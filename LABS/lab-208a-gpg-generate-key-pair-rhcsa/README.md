# Lab 208a: Generate a GPG Key Pair (RHCSA) — `gpg --gen-key`, `gpg --list-keys`, `gpg --list-secret-keys`

**Series:** linux-ops-mastery — GPG Encryption · **Lab 208a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (managing keys and secure file handling habits), RHCE EX294 (the shell muscle memory behind automated key generation), SRE/DevOps (signing artifacts, encrypting secrets, GnuPG-backed pass/SOPS workflows)  
**Prerequisite:** A RHEL/Rocky/Alma sandbox you can `sudo` on, with `gnupg2` installed (`gpg --version` succeeds) — no prior lab required  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Generate a real GPG key pair the way automation actually does it — unattended, from a batch parameter file — instead of clicking through the interactive wizard. By the end you can drive `gpg --batch --gen-key` with a `keyparams` file, point GnuPG at a sandboxed `GNUPGHOME` so no keys leak into your real `~/.gnupg`, list both the public and secret halves with long key IDs, and read a key's 40-hex fingerprint and machine-readable colon output the way scripts do.

---

## 🧠 Concept

A GPG **key pair** is two mathematically linked keys: a **public key** you hand out so anyone can encrypt to you or verify your signatures, and a **secret (private) key** you guard so only you can decrypt or sign. GnuPG stores both in a *keyring* directory chosen by the `GNUPGHOME` environment variable (default `~/.gnupg`). Interactively you would run `gpg --gen-key` or `gpg --full-generate-key` and answer prompts, but real automation feeds a **parameter file** to `gpg --batch --gen-key` so generation runs with zero questions. Every key has a short **key ID**, a longer **long key ID**, and a full **fingerprint** (40 hex characters) — increasingly specific names for the same key, with the fingerprint being the only one safe to trust.

```
GNUPGHOME=/tmp/lab-208/gnupg   (a sandboxed keyring, chmod 700)
        │
        ├─ pubring.kbx     ── public keys  ── gpg --list-keys
        └─ private-keys-v1.d/ ── secret keys ── gpg --list-secret-keys

key naming, least → most specific:
  short ID   A1B2C3D4
  long  ID   DEADBEEFA1B2C3D4              (gpg --keyid-format LONG)
  fingerprint DEAD BEEF 0000 1111 2222  3333 4444 5555 6666 7777  (40 hex)
```

> **Why this matters:** Generating keys by hand is fine for one laptop; every server, CI runner, and Ansible play needs *unattended* generation. The batch parameter file plus a sandboxed `GNUPGHOME` is the pattern that lets you create keys repeatably without polluting the system keyring or hanging on a passphrase prompt.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `gpg --gen-key` | Quick interactive key generation (the anchor command) | minimal prompts; fine for humans, useless for scripts |
| `gpg --full-generate-key` | Interactive generation with full control of algorithm/size/expiry | lets you pick RSA size, curve, and expiry the quick wizard hides |
| `gpg --batch --gen-key FILE` | Unattended generation from a parameter file | `--batch` answers all prompts from `FILE`; the automation form |
| `gpg --list-keys` | List public keys in the keyring (anchor) | `--keyid-format LONG` shows the 16-hex long key ID |
| `gpg --list-secret-keys` | List secret keys you hold (anchor) | proves you own the private half, not just a public copy |
| `gpg --fingerprint` / `--with-colons` | Show the 40-hex fingerprint / machine-parseable output | `--with-colons` emits stable, script-friendly fields |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** We build one throwaway sandbox folder under `/tmp` and point GnuPG at a keyring *inside* it via `GNUPGHOME`, so every key we create lives in the sandbox and Teardown wipes it in one command without ever touching your real `~/.gnupg`.

> Run this block **once** before Task 1. It defines a single sandbox root (`LAB_ROOT`) that every file in this lab lives under, so Teardown can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-208
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"

export GNUPGHOME="$LAB_ROOT/gnupg"
mkdir -p "$GNUPGHOME"
chmod 700 "$GNUPGHOME"

gpg --version | head -1
ls -ld "$GNUPGHOME"
echo "GNUPGHOME is $GNUPGHOME"
echo "exit was: $?"
```

**Expected output:**

```
gpg (GnuPG) 2.3.3
drwx------. 2 root root 6 Jun 15 17:40 /tmp/lab-208/gnupg
GNUPGHOME is /tmp/lab-208/gnupg
exit was: 0
```

---

## TASK 1 of 2 — Unattended key generation with a batch parameter file

**In plain English:** We describe the key we want in a small text file, then let `gpg --batch --gen-key` build it with no prompts, and list the public and secret halves to confirm the pair exists.

---

### Step 1 of 2 — Write a `keyparams` file and run `gpg --batch --gen-key`

**In plain English:** We create a parameter file that spells out the key type, size, owner name, email, expiry, and passphrase, then hand it to `gpg --batch --gen-key` so the whole key pair is generated unattended.

```bash
export GNUPGHOME="$LAB_ROOT/gnupg"

cat > "$LAB_ROOT/keyparams" <<'EOF'
%echo Generating a sandbox GPG key pair
Key-Type: RSA
Key-Length: 3072
Subkey-Type: RSA
Subkey-Length: 3072
Name-Real: Lab 208 User
Name-Email: lab208@example.com
Expire-Date: 1y
Passphrase: labpass208
%commit
%echo done
EOF

gpg --batch --gen-key "$LAB_ROOT/keyparams"
echo "exit was: $?"
```

**Expected output:**

```
gpg: Generating a sandbox GPG key pair
gpg: key 9F3A1C2BDEADBEEF marked as ultimately trusted
gpg: revocation certificate stored as '/tmp/lab-208/gnupg/openpgp-revocs.d/AABBCCDD...9F3A1C2BDEADBEEF.rev'
gpg: done
exit was: 0
```

**Line-by-line breakdown:**

- `export GNUPGHOME="$LAB_ROOT/gnupg"` → Re-point GnuPG at the sandbox keyring (already set in setup, repeated here so this step is safe to run on its own); without it, keys would land in your real `~/.gnupg`.
- `cat > "$LAB_ROOT/keyparams" <<'EOF' ... EOF` → A heredoc writing the parameter file; the quoted `'EOF'` means the lines are written literally with no variable expansion.
- `Key-Type: RSA` / `Key-Length: 3072` → The primary key is RSA at 3072 bits (RHEL 9's sane modern default); `Subkey-Type`/`Subkey-Length` add a matching encryption subkey.
- `Name-Real` / `Name-Email` / `Expire-Date: 1y` → The owner's user ID and an expiry one year out; `%commit` tells GnuPG to actually generate, and `Passphrase:` sets the secret-key passphrase non-interactively.
- `gpg --batch --gen-key "$LAB_ROOT/keyparams"` → `--batch` reads every answer from the file so nothing prompts; GnuPG generates the pair and stores a revocation certificate automatically.

**New words in this step:**

- **GNUPGHOME** — the environment variable that tells GnuPG which directory holds its keyrings (default `~/.gnupg`); set it to sandbox or relocate the keyring.
- **parameter file (keyparams)** — a text file of `Key:` directives that supplies every answer `gpg --gen-key` would otherwise prompt for.

---

### Step 2 of 2 — List the public and secret keys with long key IDs

**In plain English:** We list the public key, then the secret key with the long-ID format, to confirm both halves of the pair exist and to read the 16-hex long key ID we'll reference later.

```bash
gpg --list-keys
gpg --list-secret-keys --keyid-format LONG
echo "exit was: $?"
```

**Expected output:**

```
/tmp/lab-208/gnupg/pubring.kbx
------------------------------
pub   rsa3072 2026-06-15 [SCEA] [expires: 2027-06-15]
      AABBCCDDEEFF00112233445566778899DEADBEEF
uid           [ultimate] Lab 208 User <lab208@example.com>
sub   rsa3072 2026-06-15 [E] [expires: 2027-06-15]

sec   rsa3072/9F3A1C2BDEADBEEF 2026-06-15 [SCEA] [expires: 2027-06-15]
      AABBCCDDEEFF00112233445566778899DEADBEEF
uid                 [ultimate] Lab 208 User <lab208@example.com>
ssb   rsa3072/1122334455667788 2026-06-15 [E] [expires: 2027-06-15]
exit was: 0
```

**Line-by-line breakdown:**

- `gpg --list-keys` → List public keys; `pub` is the primary public key, `uid` is the owner identity, and `sub` is the encryption subkey we asked for.
- `gpg --list-secret-keys --keyid-format LONG` → List the secret keys you actually hold; `sec`/`ssb` mark the secret primary and subkey, and `--keyid-format LONG` prints the 16-hex long key ID after the `rsa3072/` prefix.
- `echo "exit was: $?"` → Confirm the listing succeeded (`0`); a non-zero here usually means `GNUPGHOME` is unset or the key never generated.

**New words in this step:**

- **long key ID** — the 16-hex-digit identifier (`--keyid-format LONG`) that names a key less ambiguously than the old 8-hex short ID.
- **subkey (`sub`/`ssb`)** — a secondary key bound to the primary; here a dedicated encryption subkey, so the primary can be reserved for signing/certification.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `gpg --batch --gen-key FILE` | unattended generation from a parameter file | forgetting `--batch` drops you into interactive prompts |
| `GNUPGHOME` | chooses which keyring directory GnuPG uses | unset = keys land in real `~/.gnupg`, not the sandbox |
| `--keyid-format LONG` | prints the 16-hex long key ID | the short 8-hex ID is collision-prone — never trust it |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `gpg: agent_genkey failed` / hangs | No entropy or pinentry trying to prompt | Use `--batch` with `Passphrase:` in the file; install `rng-tools` for entropy |
| Keys appear in `~/.gnupg`, not the sandbox | `GNUPGHOME` was not exported in this shell | `export GNUPGHOME="$LAB_ROOT/gnupg"` before running `gpg` |

---

## TASK 2 of 2 — Inspect identity, fingerprint, and machine-readable output

**In plain English:** We read the key's full 40-hex fingerprint for humans, then switch to the colon-delimited format scripts parse, extracting just the fingerprint field with `grep`/`awk`.

---

### Step 1 of 2 — Show the 40-hex fingerprint

**In plain English:** We ask GnuPG for the key's fingerprint by email so we can see the full 40-hex value — the only key name secure enough to verify a key over the phone or in print.

```bash
gpg --fingerprint lab208@example.com
echo "exit was: $?"
```

**Expected output:**

```
pub   rsa3072 2026-06-15 [SCEA] [expires: 2027-06-15]
      AABB CCDD EEFF 0011 2233  4455 6677 8899 DEAD BEEF
uid           [ultimate] Lab 208 User <lab208@example.com>
sub   rsa3072 2026-06-15 [E] [expires: 2027-06-15]
exit was: 0
```

**Line-by-line breakdown:**

- `gpg --fingerprint lab208@example.com` → Look up the key by its email and print the full fingerprint as ten space-separated 4-hex groups (40 hex digits total).
- The grouped hex on the indented line → This is the **fingerprint**, a hash of the public key; the shorter long key ID is just its last 16 hex digits, and the short ID just the last 8.
- `echo "exit was: $?"` → Confirms the lookup matched a key (`0`); a `2` typically means no key matched that user ID.

**New words in this step:**

- **fingerprint** — the full 40-hex-digit hash of a public key; the canonical, collision-resistant way to identify and verify a key.
- **key ID vs fingerprint** — the key ID is a truncated tail of the fingerprint (last 16 or 8 hex); only the full fingerprint is safe to trust.

---

### Step 2 of 2 — Machine-readable output with `--with-colons`

**In plain English:** We re-list the key in the colon-delimited format meant for programs, then pull out just the fingerprint field with `grep` and `awk` — exactly how a script captures a key's fingerprint.

```bash
gpg --list-keys --with-colons lab208@example.com
gpg --list-keys --with-colons lab208@example.com | grep '^fpr' | head -1 | awk -F: '{print $10}'
echo "exit was: $?"
```

**Expected output:**

```
tru::1:1718480400:0:3:1:5
pub:u:3072:1:99DEADBEEF001122:1718480400:1750016400::u:::scESC::::::23::0:
fpr:::::::::AABBCCDDEEFF00112233445566778899DEADBEEF:
uid:u::::1718480400::A1B2...::Lab 208 User <lab208@example.com>::::::::::0:
sub:u:3072:1:1122334455667788:1718480400:1750016400:::::e::::::23:
fpr:::::::::1111222233334444555566667777888899990000:
AABBCCDDEEFF00112233445566778899DEADBEEF
exit was: 0
```

**Line-by-line breakdown:**

- `gpg --list-keys --with-colons lab208@example.com` → Emit the key in colon-delimited records; each line is a record type (`pub`, `fpr`, `uid`, `sub`) with fixed fields, designed for parsing rather than reading.
- `... | grep '^fpr' | head -1` → Keep only fingerprint records and take the first one (the primary key's fingerprint).
- `awk -F: '{print $10}'` → Split on `:` and print field 10, which is where the 40-hex fingerprint lives in an `fpr` record — the production way to capture a fingerprint into a variable.

**New words in this step:**

- **`--with-colons`** — GnuPG's stable, machine-parseable output format; field positions are guaranteed across versions, unlike the human listing.
- **`fpr` record** — the colon-format line whose 10th field carries the full 40-hex fingerprint.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `gpg --fingerprint` | prints the human-grouped 40-hex fingerprint | verifying by short key ID instead invites collisions |
| `--with-colons` | stable machine-readable records | parsing the human listing breaks across gpg versions |
| `awk -F: '{print $10}'` on `fpr` | extracts just the fingerprint | the `fpr` field is column 10, not the last column |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `gpg: error reading key: No public key` | Wrong email/user ID or wrong `GNUPGHOME` | Match the `Name-Email` exactly; re-export `GNUPGHOME` |
| `awk` prints an empty line | Grabbed a `pub` line, not an `fpr` line | Filter with `grep '^fpr'` before `awk` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write a `keyparams` file and run `gpg --batch --gen-key`
- [ ] Task 1 · Step 2 — List the public and secret keys with long key IDs
- [ ] Task 2 · Step 1 — Show the 40-hex fingerprint
- [ ] Task 2 · Step 2 — Machine-readable output with `--with-colons`

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-208
```

Because the entire keyring lives under `$GNUPGHOME="$LAB_ROOT/gnupg"`, removing `$LAB_ROOT` deletes the keys too — this lab changed **no** system state (no services, firewall rules, SELinux booleans, or system keyring entries), so no extra reversal is needed beyond wiping the sandbox.

**Expected output:**

```
✅ Removed /tmp/lab-208 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Running `gpg` without `GNUPGHOME` set | Keys pollute your real `~/.gnupg` | Always `export GNUPGHOME="$LAB_ROOT/gnupg"` first |
| Omitting `Passphrase:` in a `--batch` file | Generation hangs waiting on pinentry | Add `Passphrase:` (or `%no-protection`) for unattended runs |
| Trusting an 8-hex short key ID | Two keys can share a short ID (collisions exist) | Verify with the full 40-hex `--fingerprint` |

---

## 📌 Exam Strategy

When a task says "create a GPG key," reach for the unattended pattern even by hand: a tiny parameter file plus `gpg --batch --gen-key` is faster and never hangs on a prompt. Keep a sandbox `GNUPGHOME` habit so test keys never contaminate a graded system keyring, and always confirm your work by listing both `--list-keys` and `--list-secret-keys`.

- Memorize the minimal `keyparams` block — `Key-Type`, `Key-Length`, `Name-Real`, `Name-Email`, `Expire-Date`, `Passphrase`, `%commit`.
- Use `--keyid-format LONG` whenever you must reference a key; the short ID is collision-prone.
- For scripts, parse `--with-colons` (the `fpr` record, field 10), never the human listing.

---

## 🔗 Related Labs

- [Lab 208a — Generate a GPG Key Pair (RHCSA)](../lab-208a-gpg-generate-key-pair-rhcsa/) — this hands-on shell version
- [Lab 208b — Generate a GPG Key Pair (Ansible)](../lab-208b-gpg-generate-key-pair-ansible/) — the same generation expressed (and bounded) in a playbook
- [Lab 208c — Generate a GPG Key Pair (Verify)](../lab-208c-gpg-generate-key-pair-verify/) — prove the pair exists with hard assertions
- [Lab 209a — Encrypt and Decrypt a File with GPG (RHCSA)](../lab-209a-gpg-encrypt-file-rhcsa/) — the next step: put this key pair to work

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
