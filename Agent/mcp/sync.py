#!/usr/bin/env python3
"""Merge the shared MCP catalog into user configs. Defaults to dry-run."""
import argparse
import copy
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import tomllib
import yaml

CLIENTS = ("claude", "hermes", "codex", "opencode")


def sanitize_server(raw):
    command = raw.get("command")
    result = {}
    if raw.get("url"):
        result["url"] = raw["url"]
    elif command:
        result["command"] = command[0] if isinstance(command, list) else command
        result["args"] = command[1:] if isinstance(command, list) else raw.get("args", [])
    for key in ("cwd",):
        if key in raw:
            result[key] = raw[key]
    env = raw.get("env", raw.get("environment", {}))
    if env:
        result["env"] = {key: ({"env": key} if re.search(r"TOKEN|KEY|SECRET|PASSWORD|PASSWD|(?:^|_)PASS(?:$|_)", key, re.I)
                                else value) for key, value in env.items()}
    if raw.get("headers") or raw.get("http_headers"):
        headers = raw.get("headers", raw.get("http_headers", {}))
        result["headers"] = {key: {"env": "MCP_" + re.sub(r"\W", "_", key).upper()} for key in headers}
    if "startup_timeout_sec" in raw:
        result["startup_seconds"] = raw["startup_timeout_sec"]
    if "connect_timeout" in raw:
        result["startup_seconds"] = raw["connect_timeout"]
    if "tool_timeout_sec" in raw:
        result["execution_seconds"] = raw["tool_timeout_sec"]
    return result


def adapt(server, client):
    remote = "url" in server
    if client == "opencode":
        result = {"type": "remote", "url": server["url"]} if remote else {
            "type": "local", "command": [server["command"], *server.get("args", [])]}
    elif client == "claude":
        result = {"type": "http", "url": server["url"]} if remote else {
            "type": "stdio", "command": server["command"], "args": server.get("args", [])}
    else:
        result = {"url": server["url"]} if remote else {
            "command": server["command"], "args": server.get("args", [])}
    for key in ("cwd",):
        if key in server and client != "claude":
            result[key] = server[key]
    env = {}
    inherited = []
    for key, value in server.get("env", {}).items():
        if isinstance(value, dict):
            name = value["env"]
            if client == "codex":
                if name != key:
                    raise ValueError("Codex environment aliases are unsupported; use the server variable name")
                inherited.append(name)
                continue
            value = "{env:" + name + "}" if client == "opencode" else "${" + name + "}"
        env[key] = value
    if env:
        result["environment" if client == "opencode" else "env"] = env
    if inherited:
        result["env_vars"] = inherited
    startup = server.get("startup_seconds")
    execution = server.get("execution_seconds")
    if client == "codex":
        if startup: result["startup_timeout_sec"] = startup
        if execution: result["tool_timeout_sec"] = execution
    elif client == "hermes":
        if startup: result["connect_timeout"] = startup
    elif client == "opencode":
        timeouts = {}
        if startup: timeouts["startup"] = int(startup * 1000)
        if execution: timeouts["execution"] = int(execution * 1000)
        if timeouts: result["timeout"] = timeouts
    elif execution:
        result["timeout"] = int(execution * 1000)
    if remote and server.get("headers"):
        result["headers" if client != "codex" else "env_http_headers"] = {
            key: (value["env"] if client == "codex" else
                  "{env:" + value["env"] + "}" if client == "opencode" else
                  "${" + value["env"] + "}") for key, value in server["headers"].items()}
    return result


def merge_servers(original, client, servers, previously_managed=()):
    merged = copy.deepcopy(original)
    if client == "opencode":
        current = merged.setdefault("mcp", {}).setdefault("servers", {})
    else:
        current = merged.setdefault("mcpServers" if client == "claude" else "mcp_servers", {})
    for name in set(previously_managed) - set(servers):
        current.pop(name, None)
    transport_keys = {"type", "command", "args", "url", "env", "environment", "headers", "http_headers", "env_vars"}
    for name, desired in servers.items():
        existing = current.get(name, {})
        entry = {k: copy.deepcopy(v) for k, v in existing.items() if k not in transport_keys}
        entry.update(copy.deepcopy(desired))
        # Auth values and client-local process environment never enter the catalog.
        for key in ("env", "environment", "headers", "http_headers", "oauth", "bearer_token_env_var"):
            if key in existing:
                if isinstance(existing[key], dict) and isinstance(entry.get(key), dict):
                    for field, value in existing[key].items():
                        if field not in entry[key] or re.search(r"TOKEN|KEY|SECRET|PASSWORD|PASSWD|(?:^|_)PASS(?:$|_)", field, re.I):
                            entry[key][field] = value
                else:
                    entry[key] = existing[key]
        current[name] = entry
    return merged


def update_toml(text, servers):
    lines = text.splitlines(keepends=True)
    output = []
    skipping = False
    for line in lines:
        if re.match(r"^\s*\[", line):
            skipping = bool(re.match(r"^\s*\[mcp_servers(?:\.|\])", line))
        if not skipping:
            output.append(line)
    rendered = "".join(output).rstrip() + "\n\n"
    def value(v):
        if isinstance(v, dict):
            return "{ " + ", ".join(json.dumps(k) + " = " + value(x) for k, x in v.items()) + " }"
        if isinstance(v, list):
            return "[" + ", ".join(value(x) for x in v) + "]"
        return json.dumps(v)
    for name, entry in servers.items():
        rendered += "[mcp_servers." + json.dumps(name) + "]\n"
        rendered += "".join(json.dumps(key) + " = " + value(v) + "\n" for key, v in entry.items() if v is not None)
        rendered += "\n"
    tomllib.loads(rendered)
    return rendered


def config_paths():
    home = Path.home()
    return {"claude": home / ".claude.json", "hermes": home / ".hermes/config.yaml",
            "codex": home / ".codex/config.toml", "opencode": home / ".config/opencode/opencode.jsonc"}


def read_config(path):
    text = path.read_text()
    if path.suffix == ".toml": return tomllib.loads(text)
    if path.suffix in (".yaml", ".yml"): return yaml.safe_load(text)
    # Fail closed for JSONC extensions requiring a richer parser.
    return json.loads(text)


def load_catalog(path):
    catalog = yaml.safe_load(Path(path).read_text())
    if not isinstance(catalog.get("servers"), dict) or not catalog["servers"]:
        raise ValueError("Catalog must contain named servers")
    for name, server in catalog["servers"].items():
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", name): raise ValueError("Invalid server name")
        for definition in [server["default"], *server.get("clients", {}).values()]:
            for field, val in definition.get("env", {}).items():
                sensitive = re.search(r"TOKEN|KEY|SECRET|PASSWORD|PASSWD|(?:^|_)PASS(?:$|_)", field, re.I)
                if sensitive and not (isinstance(val, dict) and set(val) == {"env"}):
                    raise ValueError("Secret environment values must use references")
            for val in definition.get("headers", {}).values():
                if not (isinstance(val, dict) and set(val) == {"env"}):
                    raise ValueError("Headers must use environment references")
        for client in CLIENTS:
            adapt(server.get("clients", {}).get(client, server["default"]), client)
    return catalog


def plan_sync(catalog, configs, previously_managed=()):
    result = {}
    for client, original in configs.items():
        servers = {name: adapt(entry.get("clients", {}).get(client, entry["default"]), client)
                   for name, entry in catalog["servers"].items()}
        result[client] = merge_servers(original, client, servers, previously_managed)
    return result


def apply_sync(plan, paths, dry_run=True):
    backup = Path.home() / ".local/state/agent-vault/backups" / datetime.now().strftime("%Y%m%d-%H%M%S")
    for client, merged in plan.items():
        path = paths[client]
        if read_config(path) == merged: continue
        if dry_run: continue
        backup.mkdir(parents=True, exist_ok=True, mode=0o700)
        backup.chmod(0o700)
        saved = backup / (client + path.suffix)
        shutil.copy2(path, saved)
        saved.chmod(0o600)
        if client == "codex":
            text = update_toml(path.read_text(), merged["mcp_servers"])
        elif client == "hermes":
            text = yaml.safe_dump(merged, sort_keys=False, allow_unicode=True)
        else:
            text = json.dumps(merged, indent=2, ensure_ascii=False) + "\n"
        temp = path.with_name(path.name + ".agent-tmp")
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream: stream.write(text)
        read_config(temp) if client not in ("codex", "hermes") else None
        temp.replace(path)
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    catalog = load_catalog(Path(__file__).with_name("catalog.yaml"))
    paths = config_paths()
    original = {client: read_config(path) for client, path in paths.items()}
    state = Path.home() / ".local/state/agent-vault/managed-mcp.json"
    previous = json.loads(state.read_text()) if state.exists() else []
    plan = plan_sync(catalog, original, previous)
    drift = [client for client in CLIENTS if plan[client] != original[client]]
    print(json.dumps({"servers": sorted(catalog["servers"]), "drift": drift, "apply": args.apply}))
    if args.apply:
        print("Backup directory:", apply_sync(plan, paths, dry_run=False))
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(json.dumps(sorted(catalog["servers"])) + "\n")
    if args.check and drift: raise SystemExit(1)


if __name__ == "__main__":
    main()
