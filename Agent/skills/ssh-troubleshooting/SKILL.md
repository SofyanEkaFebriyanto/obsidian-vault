---
name: ssh-troubleshooting
description: Diagnose and fix SSH connection failures — REMOTE HOST IDENTIFICATION HAS CHANGED / known_hosts warnings, auth failures (publickey,password), config alias-vs-IP mismatches, and `sudo &&` precedence mistakes. Use whenever an ssh/scp/rsync command fails with host-key or permission errors.
tags:
  - ssh
  - known_hosts
  - host-key
  - ssh-config
  - pubkey-auth
  - remote-access
---

# SSH Troubleshooting

Fix the two most common SSH failure classes: host-key / known_hosts rejection, and authentication failure. Includes a non-obvious root cause where a mis-scoped ssh config block causes BOTH errors at once.

## Class 1 — "REMOTE HOST IDENTIFICATION HAS CHANGED"

```
@@@@@@@@@@@@@@@@@@@@@@@@@@@
@  WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!  @
@@@@@@@@@@@@@@@@@@@@@@@@@@@
Offending ... key in /home/<user>/.ssh/known_hosts:<N>
Host key verification failed.
```

This fires when the server's key no longer matches the cached one. Before blindly deleting, treat it as either (a) a legit change (server re-imaged, OS reinstalled, IP reused/reassigned, key type rotated ECDSA→ED25519) or (b) a possible MITM.

### Steps
1. **Identify the offending line** (read, don't guess the line number):
   ```bash
   sed -n '<N>p' /home/<user>/.ssh/known_hosts      # <N> = line in the error
   ```
   The line shows the cached key type (e.g. `ecdsa-sha2-nistp256`) for that host.

2. **Remove the stale entry** (auto-detects all entries for that host, keeps a `.old` backup):
   ```bash
   ssh-keygen -R <host-or-ip>
   ```

3. **Verify the NEW key is legit before trusting it.** Get the live fingerprint and compare to the one in the warning banner:
   ```bash
   ssh-keyscan -t ed25519 <ip> 2>/dev/null | ssh-keygen -lf -
   ```
   - If it matches the fingerprint in the warning → it's the real server (reinstall/key-rotation). Safe to proceed.
   - If it does NOT match and you didn't expect a change → stop, suspect MITM or wrong host.

4. **Connect again** (or accept-new to auto-add without the interactive prompt):
   ```bash
   ssh -o StrictHostKeyChecking=accept-new <user>@<ip> "hostname"
   ```

**Note:** `UserKnownHostsFile /dev/null` in a config block silently suppresses this warning — see Class 2 for why that may not be applied.

## Class 2 — Auth fails with "publickey,password" even though the key exists

Symptom: `Permission denied (publickey,password)` despite a valid local private key and the server offering `publickey`. The key is *offered* (verbose: `Offering public key: ... explicit`) but the server *rejects* it.

### Verify the key is being offered (not a client-side key problem)
```bash
ssh -v -o PreferredAuthentications=publickey <host> "echo x" 2>&1 | grep -iE "offering|can continue|denied"
```
- `Offering public key: /path/to/key ... explicit` + server still says `can continue: publickey,password` → **server rejected the key** (not a client key problem).

### Root cause A — ssh config scoped to alias, not IP (NON-OBVIOUS, both errors at once)
If `~/.ssh/config` has:
```
Host myalias
    HostName 10.0.0.5
    User ubuntu
    IdentityFile /home/.../mykey
    UserKnownHostsFile /dev/null
```
then `ssh ubuntu@10.0.0.5` (by IP) does NOT match the `Host myalias` block:
- `UserKnownHostsFile /dev/null` is skipped → the Class-1 known_hosts warning appears.
- `IdentityFile` is skipped → no key offered → auth falls back to password and is rejected.

**Fix (pick one):**
- Connect via the alias: `ssh myalias`.
- Or broaden the config block so the IP also matches, e.g. `Host myalias 10.0.0.5` or `Host myalias 10.0.0.*`.
- Always read the actual config before concluding the server is at fault:
  ```bash
  grep -iA6 "<ip-substring>" /home/<user>/.ssh/config
  ```

### Root cause B — server-side key not present
If the key is offered and rejected, the most common server-side reason is the server was re-imaged / `authorized_keys` reset → the client's public key is no longer in `~/.ssh/authorized_keys` on the server. No client-side fix exists; use out-of-band access (provider web console / VNC / reset) to re-add the pubkey:
```bash
# on the server, via console:
mkdir -p ~/.ssh && chmod 700 ~/.ssh
echo "<PASTE_CLIENT_PUBKEY>" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### Root cause C — password also rejected
Either password auth is disabled on the server (`PasswordAuthentication no`) or the password is wrong. Without working pubkey + console access, you're locked out.

## Class 3 — `sudo cmd1 && cmd2` precedence trap (not SSH per se, but hits remote installs)

```bash
sudo tar xzf f.tar.gz && mv qodercli/x /usr/local/bin/   # WRONG
```
`sudo` binds only to `tar`. `mv` runs as the normal user → `mv: cannot move ... Permission denied` on `/usr/local/bin` (root-owned, mode 755). The `&&` is a command separator, not part of `sudo`.

**Fix:**
```bash
sudo tar xzf f.tar.gz && sudo mv qodercli/x /usr/local/bin/ && sudo chmod +x /usr/local/bin/x
# or wrap the whole chain:
sudo bash -c "tar xzf f.tar.gz && mv qodercli/x /usr/local/bin/ && chmod +x /usr/local/bin/x"
```

## Harmless noise — tar "Ignoring unknown extended header keyword LIBARCHIVE.xattr.*"

When extracting a `.tar.gz` created on macOS, Linux `tar` prints many `Ignoring unknown extended header keyword 'LIBARCHIVE.xattr...'` lines. These are macOS extended-attribute metadata and are **safe to ignore** — the extract still succeeds. No action needed.

## Quick reference

| Symptom | Likely cause | Fix |
|---|---|---|
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | Cached key stale (reinstall/IP reuse) or MITM | `ssh-keygen -R <host>`; verify fingerprint via `ssh-keyscan` |
| Warning shows even with `UserKnownHostsFile /dev/null` | Config block keyed by alias, not IP | Connect via alias or broaden `Host` match |
| `Permission denied (publickey,password)`, key exists | Config not applied / key not on server | Check config scope (alias vs IP); re-add pubkey via console |
| `mv: ... Permission denied` after `sudo tar ... && mv` | sudo only covered `tar` | `sudo ... && sudo mv ...` |
| tar xattr warnings | macOS-made archive | Ignore — harmless |
