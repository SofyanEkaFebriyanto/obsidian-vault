# Qoder Farm — PAT farming + Pro Trial claim (qoder.com)

Repo: https://github.com/fazulfi/qoder-farm
Harvests Qoder PAT (`pt-*`) and claims Pro Trial (300 credits + 800 Qwen3.8-Max calls).

## Distinction: two scripts, two jobs
- `qoder_claim_trial.py` — creates NEW accounts via GSuite SSO + Camoufox + proxy, then claims trial. Needs a supply of Google accounts (`gsuite.txt`, `email|password` per line). This is the mass-farm path and requires the account supply itself (the abuse bottleneck).
- `qoder_injector.py` — claims Pro Trial for PATs you ALREADY own (no new accounts, no browser). Eligibility -> claim `canClaim=true` activities (incl. `qwen38_800_invoke`) -> verify plan/quota. Use this for already-minted PATs.

## CLI install (standalone binary)
```bash
curl -L -o qodercli.tar.gz "https://download.qoder.com/qoderwake/releases/0.2.5/qoderwake_0.2.5_linux_amd64.tar.gz"
sudo tar xzf qodercli.tar.gz && sudo mv qodercli/qodercli-wake /usr/local/bin/
sudo chmod +x /usr/local/bin/qodercli-wake
qodercli-wake --version   # expect output, e.g. 1.1.8
```
tar `LIBARCHIVE.xattr.*` warnings = harmless macOS metadata, ignore.

## PITFALL: scripts hardcode CLI path /tmp/qodercli/qodercli-wake
`check_qoder_quota.py`, `verify_800.sh`, `qoder_injector.py` all call `CLI=/tmp/qodercli/qodercli-wake`,
but the install above puts the binary at `/usr/local/bin/qodercli-wake`. Symlink once:
```bash
sudo mkdir -p /tmp/qodercli
sudo ln -sf /usr/local/bin/qodercli-wake /tmp/qodercli/qodercli-wake
```

## WARNING: `--list-models` showing Qwen3.8-Max is NOT proof the trial is active
README claims "model appears = trial active" — FALSE. With a Free plan, `--list-models` still lists
Qwen3.8-Max, but a real query returns a paywall instead of an answer:
```bash
QODER_PERSONAL_ACCESS_TOKEN="pt-..." qodercli-wake --model Qwen3.8-Max -p "Ketik hanya: HIJUKI_OK"
# Free plan output (BLOCKED):  {"pricingUrl":"https://qoder.com/pricing?client=qoder"}
```
Real proof = actual inference returns the prompt text, OR the openapi plan check below shows `personal_professional_trial`.

## Verify plan/quota (authoritative)
`check_qoder_quota.py` expects a JSON ARRAY `[{email, pat}]` with key `pat` (NOT jsonl with `pat_token`).
Convert a jsonl (`{"email":..,"pat_token":..}`) to the expected shape:
```bash
python3 - <<'EOF'
import json
out=[{"email":json.loads(l)["email"],"pat":json.loads(l).get("pat_token","")}
      for l in open("qoder-creator/data/accounts.jsonl") if l.strip()]
json.dump(out, open("pats_full.json","w"), indent=2)
EOF
# one-PAT direct version:
echo '[{"email":"a@b.id","pat":"pt-..."}]' > /tmp/one_pat.json
python3 check_qoder_quota.py /tmp/one_pat.json
# needs: pip install pycryptodome  (script uses `Crypto`)
```
Expected ACTIVE output: `plan=personal_professional_trial userType=...trial quota=300/300`
Free/blocked output: `plan=Free userType=personal_standard quota=0.0/0.0`

## Claim trial for an owned PAT
```bash
echo 'pt-...' > /tmp/one_pat.txt
python3 qoder_injector.py /tmp/one_pat.txt   # uses the /tmp/qodercli symlink
python3 check_qoder_quota.py /tmp/one_pat.json   # re-verify -> should now show trial
```

## Proxy requirement
Farmer aborts without proxy (`QODER_NO_PROXY=0` is mandatory in .env). Pool format: one
`http://user:pass@host:port` per line in `proxies_residential.txt`; health-check via
`filter_proxy.py proxies_residential.txt proxies_ok.txt 200` -> use `proxies_ok.txt`.
Cheap residential PAYG that fits ~Rp 15k budget: DataImpulse $1/GB.

## Production farm (new accounts)
```bash
source .venv/bin/activate
python -m playwright install chromium && python -m camoufox fetch
QODER_PROXY_POOL=proxies_ok.txt QODER_NO_PROXY=0 QODER_DELAY=15 \
  python3 qoder_device_pat.py 20 gsuite.txt
```
