#!/usr/bin/env python3
"""Consolidate installed skill packages; writes require --apply."""
import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil


@dataclass
class SkillRoot:
    source_name: str
    path: Path
    kind: str
    priority: int
    include_hidden: bool = False
    enabled: bool = True


@dataclass
class SkillPackage:
    skill_id: str
    source_name: str
    source_path: Path
    kind: str
    relative_path: str
    digest: str
    priority: int


@dataclass
class Archive:
    package: SkillPackage
    destination: Path


@dataclass
class ImportPlan:
    canonical: dict
    archives: list
    packages: list


@dataclass
class ImportManifest:
    applied: bool


def digest(path):
    result = hashlib.sha256()
    for directory, dirs, files in os.walk(path, followlinks=False):
        dirs.sort()
        for name in sorted(files):
            item = Path(directory) / name
            result.update(str(item.relative_to(path)).encode())
            result.update(item.read_bytes())
    return result.hexdigest()


def default_roots():
    home = Path.home()
    roots = [SkillRoot(name, home / path, "user", priority) for name, path, priority in (
        ("Claude Code", ".claude/skills", 0), ("Hermes", ".hermes/skills", 1),
        ("Codex", ".codex/skills", 2), ("OpenCode", ".config/opencode/skills", 3),
        ("Shared skills", ".agents/skills", 4))]
    roots.append(SkillRoot("Codex", home / ".codex/skills/.system", "system", 2, True))
    # Only the enabled Superpowers installations were confirmed in the inventory.
    for path in (home / ".codex/plugins/cache/openai-curated/superpowers").glob("*/skills"):
        roots.append(SkillRoot("Codex", path, "plugin", 2))
    paths = sorted((home / ".cache/opencode/npm").glob("git-superpowers-*/*/node_modules/superpowers/skills"))
    if paths:
        roots.append(SkillRoot("OpenCode", paths[-1], "plugin", 3))
    return roots


def discover_sources(roots=None):
    packages = []
    for root in default_roots() if roots is None else roots:
        if not root.enabled or not root.path.exists():
            continue
        for directory, dirs, files in os.walk(root.path, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d != "node_modules"
                             and not (Path(directory) / d).is_symlink())
            if "SKILL.md" not in files:
                continue
            path = Path(directory)
            packages.append(SkillPackage(path.name, root.source_name, path, root.kind,
                                         str(path.relative_to(root.path)), digest(path), root.priority))
    return packages


def plan_import(packages, target_root):
    canonical = {}
    archives = []
    for package in sorted(packages, key=lambda p: (p.priority, p.kind != "user", str(p.source_path))):
        if package.skill_id not in canonical:
            canonical[package.skill_id] = package
        else:
            label = package.source_name.replace(" ", "-").lower()
            suffix = hashlib.sha256(str(package.source_path).encode()).hexdigest()[:10]
            archives.append(Archive(package, Path(target_root) / "sources" / label /
                                    f"{package.skill_id}-{suffix}"))
    return ImportPlan(canonical, archives, packages)


def apply_import(plan, target_root, apply=False):
    if not apply:
        return ImportManifest(False)
    target = Path(target_root)
    saved_manifest = target / "manifest/skill-sources.json"
    if saved_manifest.exists():
        previous = json.loads(saved_manifest.read_text())
        if set(previous["canonical"]) != set(plan.canonical):
            raise ValueError("Existing import manifest differs; use --sync-links for future skill registrations")
    destinations = {str(p.source_path): target / "skills" / sid for sid, p in plan.canonical.items()}
    destinations.update({str(a.package.source_path): a.destination for a in plan.archives})
    # Stage and verify every package before changing any source path.
    for package in plan.packages:
        dest = destinations[str(package.source_path)]
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(package.source_path, dest, symlinks=True)
        if digest(dest) != package.digest:
            raise ValueError(f"Package verification failed: {package.skill_id}")
    for package in plan.packages:
        if package.kind != "user":
            continue
        source = package.source_path
        if any(other.kind == "user" and other.source_path != source
               and other.source_path in source.parents for other in plan.packages):
            continue
        canonical = target / "skills" / package.skill_id
        if source.is_symlink():
            if source.resolve() != canonical.resolve():
                raise ValueError(f"Unexpected existing link: {source}")
            continue
        if digest(source) != package.digest:
            raise ValueError(f"Source changed during import: {source}")
        # Rename to a retained sibling backup before installing the link.
        backup = source.with_name("." + source.name + ".agent-backup")
        if backup.exists():
            raise ValueError(f"Backup already exists: {backup}")
        source.rename(backup)
        source.symlink_to(canonical, target_is_directory=True)
    manifest = {"canonical": {sid: {"source": p.source_name, "path": str(p.source_path),
                "digest": p.digest} for sid, p in plan.canonical.items()},
                "archives": [{"source": str(a.package.source_path), "destination": str(a.destination)}
                             for a in plan.archives]}
    (target / "manifest").mkdir(exist_ok=True)
    (target / "manifest/skill-sources.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return ImportManifest(True)


def register_links(canonical, roots):
    for root in roots:
        root.mkdir(parents=True, exist_ok=True)
        for package in sorted(canonical.iterdir()):
            if not (package / "SKILL.md").is_file():
                continue
            dest = root / package.name
            if dest.is_symlink():
                if dest.resolve() != package.resolve():
                    raise ValueError(f"Unexpected existing link: {dest}")
            elif not dest.exists():
                dest.symlink_to(package, target_is_directory=True)
            elif (dest / "SKILL.md").exists():
                raise ValueError(f"Unmigrated package: {dest}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=Path.home() / "Documents/Obsidian Vault/Agent")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--sync-links", action="store_true")
    args = parser.parse_args()
    if args.sync_links:
        if not args.apply:
            raise SystemExit("--sync-links requires --apply")
        home = Path.home()
        register_links(args.target / "skills", [home / ".claude/skills", home / ".codex/skills",
                                               home / ".agents/skills", home / ".config/opencode/skills"])
        print("Shared skill links synchronized")
        return
    plan = plan_import(discover_sources(), args.target)
    print(json.dumps({"packages": len(plan.packages), "unique_ids": len(plan.canonical),
                      "archive_variants": len(plan.archives), "apply": args.apply}))
    apply_import(plan, args.target, args.apply)


if __name__ == "__main__":
    main()
