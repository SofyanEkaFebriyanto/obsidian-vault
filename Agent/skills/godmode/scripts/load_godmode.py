"""
Loader for G0DM0D3 scripts. Handles the exec-scoping issues.

Usage in execute_code:
    exec(open(os.path.expanduser(
        os.path.join(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")), "skills/security/godmode/scripts/load_godmode.py")
    )).read())
    
    # Now all functions are available:
    # - auto_jailbreak(), undo_jailbreak()
    # - race_models(), race_godmode_classic()
    # - generate_variants(), obfuscate_query(), detect_triggers()
    # - score_response(), is_refusal(), count_hedges()
    # - escalate_encoding()
"""

import os, sys
from pathlib import Path

_gm_home = Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))


def _gm_find_scripts_dir():
    """Locate the godmode scripts dir.

    NOTE 1: when this loader is exec()'d by a caller, __file__ belongs to the
    CALLER, not to this file — so it must be validated, never trusted blindly.
    NOTE 2: skills do NOT live under a HERMES_HOME that has been overridden for
    config isolation, so ~/.hermes is always searched as an independent root.
    """
    roots = [
        _gm_home,
        Path.home() / ".hermes",
        Path(os.getenv("HERMES_PROFILE_DIR", "")),
    ]
    candidates = []
    try:
        candidates.append(Path(__file__).resolve().parent)
    except NameError:
        pass
    for root in roots:
        if not root:
            continue
        candidates.append(root / "skills" / "security" / "godmode" / "scripts")
        candidates.append(root / "skills" / "red-teaming" / "godmode" / "scripts")
    for c in candidates:
        if c and (c / "parseltongue.py").is_file():
            return c
    return candidates[0] if candidates else Path.cwd()


_gm_scripts_dir = _gm_find_scripts_dir()

_gm_old_argv = sys.argv
sys.argv = ["_godmode_loader"]

def _gm_load(path):
    ns = dict(globals())
    ns["__name__"] = "_godmode_module"
    ns["__file__"] = str(path)
    exec(compile(open(path).read(), str(path), 'exec'), ns)
    return ns

for _gm_script in ["parseltongue.py", "godmode_race.py", "auto_jailbreak.py"]:
    _gm_path = _gm_scripts_dir / _gm_script
    if _gm_path.exists():
        _gm_ns = _gm_load(_gm_path)
        for _gm_k, _gm_v in _gm_ns.items():
            if not _gm_k.startswith('_gm_') and (callable(_gm_v) or _gm_k.isupper()):
                globals()[_gm_k] = _gm_v

sys.argv = _gm_old_argv

# Cleanup loader vars
for _gm_cleanup in ['_gm_scripts_dir', '_gm_old_argv', '_gm_load', '_gm_ns', '_gm_k',
                     '_gm_v', '_gm_script', '_gm_path', '_gm_cleanup']:
    globals().pop(_gm_cleanup, None)
