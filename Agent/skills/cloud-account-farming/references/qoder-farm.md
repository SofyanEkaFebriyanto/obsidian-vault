# Qoder Farm — setup, CLI install, and Pro-Trial claim

Repo: `https://github.com/fazulfi/qoder-farm`. Qoder = Alibaba Qwen coding agent.
Goal: mass-produce Qoder PATs (`pt-*`, 64-char) via Google SSO device flow, then claim
Pro Trial (300 credits + 800 free Qwen3.8-Max calls) — free, instead of paying Rp800-1000/PAT.

## Two distinct components — don't conflate them

1. **`qodercli-wake`** — Qoder's standalone CLI binary (download separately). Used ONLY to
   log in with a PAT and claim/verify the Pro Trial. Independent of the farm repo scripts.
2. **Python farm scripts** in the repo (`qoder_device_pat.py`, `qoder_claim_trial.py`,
   `inject_qoder_pat.py`, `check_qoder_quota.py`) — the actual mass-farming pipeline
   (Camoufox anti-detect + Google SSO + proxies + GSuite accounts).

If you already HAVE a PAT (e.g. from `qoder-creator/data/accounts.jsonl`), you only need
the CLI to claim the trial — you do NOT need to run the full farm.

## Install the CLI binary (verified working)

```bash
curl -L -o qodercli.tar.gz \
  "https://download.qoder.com/qoderwake/releases/0.2.5/qoderwake_0.2.5_linux_amd64.tar.gz"
sudo tar xzf qodercli.tar.gz && sudo mv qodercli/qodercli-wake /usr/local/bin/ && sudo chmod +x /usr/local/bin/qodercli-wake
qodercli-wake --version      # expect: 1.1.8 (or newer)
```

**Pitfall — `sudo &&` precedence:** `sudo tar ... && mv ...` runs `mv` as the normal user
→ `Permission denied` on `/usr/local/bin`. Put `sudo` before BOTH commands (or wrap in
`sudo bash -c "..."`). See ssh-troubleshooting Class 3.

**Harmless noise:** `tar: Ignoring unknown extended header keyword 'LIBARCHIVE.xattr.*'`
is macOS archive metadata — ignore it; extract succeeds.

## Claim Pro Trial with an existing PAT

```bash
# PAT must be the FULL 64-char token — truncating → "invalid token format" reject
QODER_PERSONAL_ACCESS_TOKEN="pt-...<full>" qodercli-wake --list-models
# Qwen3.8-Max in output = trial active
```

Verify quota (needs repo + deps):
```bash
pip install -r requirements.txt
python3 check_qoder_quota.py <accounts-file>.jsonl
# → userType=personal_professional_trial, userQuota 300/300
```

## Full farm pipeline (from README Quickstart)

```bash
git clone https://github.com/fazulfi/qoder-farm && cd qoder-farm
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
python -m camoufox fetch
cp .env.example .env
printf 'email@domain.id|password\n' > gsuite.txt     # GSuite accounts
python3 filter_proxy.py proxies_residential.txt proxies_ok.txt 200   # health-check pool
QODER_PROXY_POOL=proxies_ok.txt QODER_NO_PROXY=0 QODER_DELAY=15 \
  python3 qoder_device_pat.py 20 gsuite.txt
```

Key env vars: `QODER_PROXY_POOL` (pool path), `QODER_NO_PROXY=0` (MUST be 0 — farming
without proxy is aborted, anti-IP-leak), `QODER_DELAY` (anti-throttle), `QODER_SKIP_EXISTING`,
`QODER_RETRY`, `QODER_CONCURRENCY` (start 1, raise if VPS strong).

## Secrets hygiene
PATs, `gsuite.txt`, `proxies*.txt`, `.env` are gitignored — never commit. PAT = credential;
treat like a password. `accounts.jsonl` from `qoder-creator` already holds `email|password|pat_token|pat_valid`.

## Gotchas captured
- CLI `qodercli-wake` ≠ farm scripts — install verifies independently (`which` + `--version`).
- PAT MUST be full 64-char to claim; truncate = reject.
- After `sudo tar`, the extracted `qodercli/` dir is root-owned → clean up with `sudo rm -rf qodercli qodercli.tar.gz`.
- Server-side `authorized_keys` reset after reimage causes SSH publickey rejection (see ssh-troubleshooting).
