# Lab 39c: Configure SSH and Key-Based Auth (Verify) — prove key auth

**Series:** linux-ops-mastery — Networking · **Lab 39c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (evidence-based SSH checks), SRE (access & permission audits)  
**Prerequisite:** [Lab 39b](../lab-39b-ssh-key-auth-ansible/) completed  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `ssh-keygen -lf` fingerprint | _Task 1 · Step 1_ |
| A2 | `stat -c %a` permissions | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | fingerprint match (priv vs pub) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | strict-permission assertion | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `ssh BatchMode` auth proof | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `sshd -T` config audit | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Prove SSH key authentication is correct and secure. You will confirm the private and public keys are a matching pair (same fingerprint), assert the strict permissions SSH demands, prove a passwordless login actually works with `BatchMode`, and audit the effective `sshd` policy with `sshd -T`. These are the objective checks behind a working, hardened SSH setup.

> **Setup note:** Re-create the sandbox key and authorize it (as in Lab 39a) before these checks if a prior teardown removed them.

---

## 🧠 Concept

Key-auth verification has four pillars. **Pairing**: `ssh-keygen -lf` on the private and public keys must yield the *same fingerprint* — that proves they belong together. **Permissions**: `~/.ssh` must be `700`, the private key and `authorized_keys` `600`; SSH silently ignores keys with looser modes, so `stat -c %a` checks are essential. **Functional proof**: `ssh -i KEY -o BatchMode=yes ... true` succeeds *only* if the key authenticates (BatchMode forbids password fallback), giving a true pass/fail. **Policy audit**: `sshd -T` prints the effective server config, so you can assert `pubkeyauthentication yes` (and, when hardening, `passwordauthentication no`). Each is extract-then-assert — the complete proof that key auth is enabled, secure, and working.

```
ssh-keygen -lf KEY  ==  ssh-keygen -lf KEY.pub   → matching pair
stat -c %a ~/.ssh / KEY / authorized_keys         → 700 / 600 / 600
ssh -i KEY -o BatchMode=yes user@localhost true   → passwordless works
sshd -T | grep pubkeyauthentication               → policy allows keys
```

> **Why this matters:** "Keys are set up" needs proof: the pair matches, permissions are strict, login works without a password, and the server policy permits keys. Missing any one silently breaks or weakens access.

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `ssh-keygen -lf` | Fingerprint | match priv/pub |
| `stat -c %a` | Permission mode | 700/600 |
| `ssh -o BatchMode=yes` | No password fallback | true auth test |
| `sshd -T` | Effective config | needs root |
| `grep pubkeyauthentication` | Policy check | yes/no |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make the sandbox and ensure a key exists and is authorized.

> Run this block **once** before Task 1. It re-creates and authorizes the key if needed.

```bash
export LAB_ROOT=/tmp/lab-39
mkdir -p "$LAB_ROOT"
mkdir -p ~/.ssh && chmod 700 ~/.ssh
[ -f "$LAB_ROOT/lab_key" ] || ssh-keygen -t ed25519 -f "$LAB_ROOT/lab_key" -N '' -C lab-39c >/dev/null
grep -q lab-39c ~/.ssh/authorized_keys 2>/dev/null || \
  { echo "# LAB-39 VERIFY"; cat "$LAB_ROOT/lab_key.pub"; } >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys "$LAB_ROOT/lab_key"
echo "ready"
echo "exit was: $?"
```

**Expected output:**

```
ready
exit was: 0
```

---

## TASK 1 of 2 — Prove pairing and permissions

**In plain English:** We confirm the keys match and have strict permissions.

---

### Step 1 of 2 — Assert the keys are a matching pair

**In plain English:** We compare the private and public key fingerprints.

```bash
FP_PRIV=$(ssh-keygen -lf "$LAB_ROOT/lab_key" | awk '{print $2}')
FP_PUB=$(ssh-keygen -lf "$LAB_ROOT/lab_key.pub" | awk '{print $2}')
echo "priv: $FP_PRIV"
echo "pub:  $FP_PUB"
[ "$FP_PRIV" = "$FP_PUB" ] && echo "PASS: keys are a matching pair" || echo "FAIL: mismatched keys"
```

**Expected output:**

```
priv: SHA256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
pub:  SHA256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PASS: keys are a matching pair
```

**Line-by-line breakdown:**

- `ssh-keygen -lf KEY` / `KEY.pub` → Each prints the key's fingerprint; the private key's fingerprint is derived from its public half.
- `[ "$FP_PRIV" = "$FP_PUB" ]` → Identical fingerprints prove they're one pair.

**New words in this step:**

- **fingerprint match** — identical hashes confirm a private/public pairing.

---

### Step 2 of 2 — Assert strict permissions

**In plain English:** We require `700` on `~/.ssh` and `600` on the key and authorized_keys.

```bash
DIR=$(stat -c %a ~/.ssh)
KEY=$(stat -c %a "$LAB_ROOT/lab_key")
AK=$(stat -c %a ~/.ssh/authorized_keys)
echo "~/.ssh=$DIR key=$KEY authorized_keys=$AK"
[ "$DIR" = "700" ] && [ "$KEY" = "600" ] && [ "$AK" = "600" ] \
  && echo "PASS: permissions strict" || echo "FAIL: loosen perms will break key auth"
```

**Expected output:**

```
~/.ssh=700 key=600 authorized_keys=600
PASS: permissions strict
```

**Line-by-line breakdown:**

- `stat -c %a` → The numeric mode of each path.
- The combined test enforces SSH's requirement: `700` dir, `600` private key and `authorized_keys`.

**New words in this step:**

- **strict-permission assertion** — proving modes SSH won't reject.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| fingerprint | identify key | priv == pub |
| `stat -c %a` | mode | 700/600 |
| strict perms | SSH requirement | loose = ignored |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Fingerprint mismatch | Wrong `.pub` | Regenerate the pair |
| Perm FAIL | Too open | `chmod 700/600` |

---

## TASK 2 of 2 — Prove login and policy

**In plain English:** We prove passwordless login works and audit the server policy.

---

### Step 1 of 2 — Prove passwordless login

**In plain English:** We log in with the key in BatchMode, which forbids password fallback.

```bash
if ssh -i "$LAB_ROOT/lab_key" -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
     "$USER@localhost" true 2>/dev/null; then
  echo "PASS: key authentication works (no password)"
else
  echo "FAIL: key login failed (check perms/authorized_keys/sshd)"
fi
```

**Expected output:**

```
PASS: key authentication works (no password)
```

**Line-by-line breakdown:**

- `ssh -i lab_key -o BatchMode=yes ... true` → Run a no-op over SSH; BatchMode means no password prompt, so success proves the *key* authenticated.
- The `if` branches on SSH's exit code — a clean functional pass/fail.

> Requires a local `sshd`. If localhost SSH is unavailable, the pairing/permission/policy checks still validate the setup.

**New words in this step:**

- **BatchMode proof** — non-interactive login success that can only come from key auth.

---

### Step 2 of 2 — Audit the effective `sshd` policy

**In plain English:** We read the running server config and confirm key auth is enabled.

```bash
sudo sshd -T 2>/dev/null | grep -E '^(pubkeyauthentication|passwordauthentication|permitrootlogin)'
echo "---"
sudo sshd -T 2>/dev/null | grep -q '^pubkeyauthentication yes' \
  && echo "PASS: pubkey auth enabled" || echo "FAIL: pubkey auth disabled"
```

**Expected output:**

```
permitrootlogin prohibit-password
pubkeyauthentication yes
passwordauthentication yes
---
PASS: pubkey auth enabled
```

**Line-by-line breakdown:**

- `sshd -T` → Dumps the *effective* configuration (after all includes/matches) — the real policy.
- `grep -q '^pubkeyauthentication yes'` → Confirms the server accepts key auth; for hardening you'd also want `passwordauthentication no`.

**New words in this step:**

- **`sshd -T`** — print the resolved, effective SSH server configuration.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| BatchMode | no prompt | proves key auth |
| `sshd -T` | effective config | not just the file |
| pubkey/password | policy | harden = password no |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Login FAIL | Perms/policy | Fix modes; enable pubkey |
| `sshd -T` denied | Not root | Use `sudo` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Assert the keys are a matching pair
- [ ] Task 1 · Step 2 — Assert strict permissions
- [ ] Task 2 · Step 1 — Prove passwordless login
- [ ] Task 2 · Step 2 — Audit the effective `sshd` policy
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — authorized key removed + sandbox cleared

---

## 🧹 Teardown

**In plain English:** Remove the verify key from `authorized_keys` and clear the sandbox.

> Removes the marked key this lab may have added. `lab_teardown.sh` clears the sandbox root.

```bash
sed -i '/# LAB-39 VERIFY/,+1d' ~/.ssh/authorized_keys 2>/dev/null || true
sed -i '/lab-39c/d' ~/.ssh/authorized_keys 2>/dev/null || true
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-39
```

**Expected output:**

```
✅ Removed /tmp/lab-39 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Skipping BatchMode | Password masks failure | Use `BatchMode=yes` |
| Reading config file only | Misses effective policy | Use `sshd -T` |
| Loose perms | Silent key rejection | `700`/`600` |

---

## 📌 Exam Strategy

Prove four things: pair match (fingerprints), strict perms (`stat -c %a`), passwordless login (`BatchMode`), and policy (`sshd -T`). BatchMode is the decisive functional test; `sshd -T` is the authoritative policy source.

- Matching fingerprints = valid pair.
- `700`/`600` or SSH ignores the key.
- `BatchMode=yes` proves key (not password) auth.

---

## 🔗 Related Labs

- [Lab 39a — Configure SSH and Key-Based Auth (RHCSA)](../lab-39a-ssh-key-auth-rhcsa/) — the setup these checks verify
- [Lab 39b — Configure SSH and Key-Based Auth (Ansible)](../lab-39b-ssh-key-auth-ansible/) — declarative key management
- [Lab 34c — Inspecting Listening Sockets (Verify)](../lab-34c-ss-listening-sockets-verify/) — confirm sshd is listening and exposed correctly

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
