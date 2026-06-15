# Lab 39a: Configure SSH and Key-Based Auth (RHCSA) — `ssh-keygen`, `ssh-copy-id`

**Series:** linux-ops-mastery — Networking · **Lab 39a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (SSH key-based auth), SRE/DevOps (passwordless automation, secure access)  
**Prerequisite:** [Lab 38c](../lab-38c-resolv-conf-dns-verify/) completed  
**Time Estimate:** 30–40 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `chmod`/permissions | _Task 1 · Step 2_ |
| A2 | `ssh user@host` | _Task 2 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `ssh-keygen -t ed25519 -f` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | key permissions (700/600) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `authorized_keys` / `ssh-copy-id` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `ssh -i` key auth test | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Set up SSH key-based authentication end to end. You'll generate a modern key pair with `ssh-keygen` (into a sandbox), set the strict permissions SSH requires, install the public key into `authorized_keys` (the mechanism behind `ssh-copy-id`), and log in with the key using `ssh -i` against localhost. This is the foundation of passwordless, secure, automatable access.

> **Safety note:** Keys live in the sandbox `/tmp/lab-39`. We authorize the key only for *your own* account against `localhost`, with a marker, and remove it in Teardown. No remote hosts or system credentials are touched.

---

## 🧠 Concept

SSH key auth replaces passwords with a **key pair**: a private key you keep secret and a public key you place on servers. `ssh-keygen -t ed25519` creates a modern, compact pair (use `-t rsa -b 4096` only for legacy hosts); `-f PATH` sets the output file, `-N ''` an empty passphrase (for automation), and `-C "comment"` a label. The client proves possession of the private key; the server checks the matching public key listed in `~/.ssh/authorized_keys`. **Permissions are strict and non-negotiable**: `~/.ssh` must be `700`, `authorized_keys` and the private key `600` — SSH refuses keys with loose permissions. `ssh-copy-id user@host` automates appending your public key to the remote `authorized_keys` (over an initial password login); manually it's just appending the `.pub` contents. To log in with a specific key: `ssh -i /path/to/key user@host`. Hardening lives in `/etc/ssh/sshd_config` (`PasswordAuthentication no`, `PermitRootLogin prohibit-password`).

```
ssh-keygen -t ed25519 -f KEY -N '' -C "label"   → create pair (KEY, KEY.pub)
chmod 700 ~/.ssh ; chmod 600 authorized_keys      → required perms
ssh-copy-id -i KEY.pub user@host                  → install public key
cat KEY.pub >> ~/.ssh/authorized_keys             → the manual equivalent
ssh -i KEY user@host                              → log in with the key
```

> **Why this matters:** Key-based auth is more secure than passwords and is required for any automation (Ansible, CI, backups). RHCSA expects you to generate keys, install them, and verify passwordless login — and to get the permissions right, the #1 reason keys "don't work".

---

## 📚 Command Reference

| Command | Purpose | Notes |
|---|---|---|
| `ssh-keygen -t ed25519` | Create key pair | modern default |
| `-f PATH` | Output file | key + `.pub` |
| `-N ''` | Empty passphrase | for automation |
| `-C "label"` | Comment | identify the key |
| `ssh-copy-id` | Install public key | over password login |
| `ssh -i KEY` | Use a specific key | explicit identity |
| `ssh-keygen -lf` | Show fingerprint | verify a key |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Create the sandbox and ensure your `~/.ssh` exists with correct permissions.

> Run this block **once** before Task 1.

```bash
export LAB_ROOT=/tmp/lab-39
mkdir -p "$LAB_ROOT"
mkdir -p ~/.ssh && chmod 700 ~/.ssh
cp -a ~/.ssh/authorized_keys "$LAB_ROOT/authorized_keys.backup" 2>/dev/null || touch "$LAB_ROOT/authorized_keys.backup"
echo "ready"
echo "exit was: $?"
```

**Expected output:**

```
ready
exit was: 0
```

---

## TASK 1 of 2 — Generate a key pair

**In plain English:** We create an ed25519 pair and set its permissions.

---

### Step 1 of 2 — Create the key pair

**In plain English:** We generate a modern key pair into the sandbox with a label.

```bash
ssh-keygen -t ed25519 -f "$LAB_ROOT/lab_key" -N '' -C "lab-39@$(hostname)"
ls -l "$LAB_ROOT"/lab_key*
echo "exit was: $?"
```

**Expected output:**

```
Generating public/private ed25519 key pair.
Your identification has been saved in /tmp/lab-39/lab_key
Your public key has been saved in /tmp/lab-39/lab_key.pub
...
-rw------- 1 user user  ... lab_key
-rw-r--r-- 1 user user  ... lab_key.pub
exit was: 0
```

**Line-by-line breakdown:**

- `ssh-keygen -t ed25519 -f .../lab_key -N '' -C "..."` → Create an ed25519 pair; `-N ''` no passphrase (automation), `-C` a label.
- `ls -l lab_key*` → Two files: the private `lab_key` (mode 600) and public `lab_key.pub` (644).

**New words in this step:**

- **key pair** — private key (secret) + public key (shareable).

---

### Step 2 of 2 — Verify and fix permissions

**In plain English:** We confirm the private key is locked down and show its fingerprint.

```bash
chmod 600 "$LAB_ROOT/lab_key"
ssh-keygen -lf "$LAB_ROOT/lab_key.pub"
stat -c '%a %n' "$LAB_ROOT/lab_key"
echo "exit was: $?"
```

**Expected output:**

```
256 SHA256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx lab-39@host (ED25519)
600 /tmp/lab-39/lab_key
exit was: 0
```

**Line-by-line breakdown:**

- `chmod 600 lab_key` → Private keys must be readable only by you, or SSH rejects them.
- `ssh-keygen -lf lab_key.pub` → Prints the key's fingerprint and type — how you identify/verify a key.
- `stat -c '%a %n'` → Confirms mode `600`.

**New words in this step:**

- **fingerprint** — a short hash uniquely identifying a key.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `-t ed25519` | modern key | rsa only for legacy |
| `-N ''` | no passphrase | automation only |
| 600 perms | lock private key | SSH refuses loose |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| "bad permissions" | Key too open | `chmod 600` |
| Passphrase prompt | `-N ''` omitted | Regenerate or use agent |

---

## TASK 2 of 2 — Install the key and log in

**In plain English:** We authorize the public key, then log in with the private key.

---

### Step 1 of 2 — Install the public key

**In plain English:** We add the public key to `authorized_keys` (what `ssh-copy-id` does).

```bash
# The manual equivalent of: ssh-copy-id -i "$LAB_ROOT/lab_key.pub" "$USER@localhost"
{ echo "# LAB-39 KEY"; cat "$LAB_ROOT/lab_key.pub"; } >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
grep -c 'lab-39@' ~/.ssh/authorized_keys
echo "exit was: $?"
```

**Expected output:**

```
1
exit was: 0
```

**Line-by-line breakdown:**

- `cat lab_key.pub >> ~/.ssh/authorized_keys` → Appends the public key — exactly what `ssh-copy-id` automates over an initial login.
- `chmod 600 ~/.ssh/authorized_keys` → Required permission, or the server ignores the file.
- `grep -c 'lab-39@'` → Confirms our key is now authorized (count 1).

**New words in this step:**

- **`authorized_keys`** — the file listing public keys allowed to log into an account.

---

### Step 2 of 2 — Log in with the key

**In plain English:** We SSH to localhost using the private key, non-interactively.

```bash
ssh -i "$LAB_ROOT/lab_key" -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
  "$USER@localhost" 'echo key-login-ok; whoami'
echo "exit was: $?"
```

**Expected output:**

```
key-login-ok
user
exit was: 0
```

**Line-by-line breakdown:**

- `ssh -i lab_key ...` → Authenticate with our private key explicitly.
- `-o BatchMode=yes` → Fail rather than prompt for a password — proves the key (not a password) worked.
- `-o StrictHostKeyChecking=accept-new` → Accept localhost's host key on first contact without prompting.

> Requires `sshd` running locally. If `ssh localhost` is blocked, the install in Step 1 is still the exam-relevant action.

**New words in this step:**

- **BatchMode** — non-interactive; no password fallback, so success means the key worked.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `authorized_keys` | allowed keys | needs 600 |
| `ssh-copy-id` | installs pubkey | over password first |
| `ssh -i` | pick a key | explicit identity |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Still asks password | Perms/wrong key | Fix 700/600, check `.pub` |
| Permission denied | Key not authorized | Append correct `.pub` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Create the key pair
- [ ] Task 1 · Step 2 — Verify and fix permissions
- [ ] Task 2 · Step 1 — Install the public key
- [ ] Task 2 · Step 2 — Log in with the key
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — authorized key removed + sandbox cleared

---

## 🧹 Teardown

**In plain English:** Remove the authorized lab key and clear the sandbox.

> This lab added one line to your `authorized_keys`; the marked key is removed here (a backup is in the sandbox).

```bash
# Remove the lab key line(s) we added:
sed -i '/# LAB-39 KEY/,+1d' ~/.ssh/authorized_keys 2>/dev/null || true
sed -i '/lab-39@/d' ~/.ssh/authorized_keys 2>/dev/null || true
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
| Loose permissions | Key ignored | `700` dir, `600` files |
| Copying private key | Security risk | Only the `.pub` goes on servers |
| Passphrase in automation | Hangs on prompt | `-N ''` or ssh-agent |

---

## 📌 Exam Strategy

Generate (`ssh-keygen -t ed25519`), install (`ssh-copy-id` / append `.pub` to `authorized_keys`), verify (`ssh -i ... BatchMode=yes`). Permissions are the #1 failure: `~/.ssh` 700, keys/authorized_keys 600. Only the public key leaves your machine.

- `ssh-keygen -t ed25519 -f -N '' -C` for a clean automation key.
- `authorized_keys` 600, `~/.ssh` 700 — always.
- `ssh -i` + BatchMode proves key auth (not password) works.

---

## 🔗 Related Labs

- [Lab 39b — Configure SSH and Key-Based Auth (Ansible)](../lab-39b-ssh-key-auth-ansible/) — manage keys and `authorized_key` declaratively
- [Lab 39c — Configure SSH and Key-Based Auth (Verify)](../lab-39c-ssh-key-auth-verify/) — prove key auth and permissions
- [Lab 34a — Inspecting Listening Sockets (RHCSA)](../lab-34a-ss-listening-sockets-rhcsa/) — confirm sshd is listening

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
