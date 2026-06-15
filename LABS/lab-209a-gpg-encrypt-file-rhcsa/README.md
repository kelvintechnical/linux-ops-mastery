# Lab 209a: Encrypt a File with GPG (RHCSA) — `gpg -e -r`, `--armor`

**Series:** linux-ops-mastery — GPG Encryption · **Lab 209a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (protecting files at rest, secure handoff of data), Security+/SRE (data confidentiality, key vs passphrase encryption), DevOps (encrypting secrets and artifacts before storage)  
**Prerequisite:** [Lab 208a](../lab-208a-gpg-generate-key-rhcsa/) (generating a GPG key) helps, but this lab creates its own throwaway recipient key in SETUP — you only need a RHEL/Rocky/Alma sandbox with `gpg` installed  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Learn the two ways GPG encrypts a file so the contents are unreadable to anyone but the intended reader: **asymmetric** (public-key) encryption *to a recipient* with `gpg -e -r`, and **symmetric** (passphrase-only) encryption with `gpg --symmetric`. Along the way you will produce both raw binary OpenPGP output and human-mailable ASCII-armored output with `--armor`, name your output files cleanly with `--output`, pin a strong cipher with `--cipher-algo AES256`, and learn to *read* a ciphertext file with `file` and `gpg --list-packets` so you can tell a public-key-encrypted file from a passphrase-encrypted one at a glance.

---

## 🧠 Concept

Encryption turns readable plaintext into ciphertext that only the right key (or passphrase) can reverse. GPG offers two models. **Asymmetric** encryption uses a recipient's *public* key to lock the file — only the matching *private* key can open it, so you can encrypt to someone without sharing any secret first (`gpg -e -r recipient`). **Symmetric** encryption uses a single shared *passphrase* to both lock and unlock — simpler, but everyone who can decrypt must already know that passphrase (`gpg --symmetric`). By default GPG writes compact **binary** ciphertext (`.gpg`); add `--armor` and it wraps that binary in printable ASCII (`.asc`) with a `-----BEGIN PGP MESSAGE-----` header so it survives email and copy-paste.

```
PLAINTEXT  secret.txt
   │
   ├── gpg -e -r recipient ───────────▶ secret.txt.gpg   (binary, public-key locked)
   │                                       └─ only the recipient's PRIVATE key opens it
   │
   ├── gpg --armor -e -r recipient ──▶ secret.txt.asc   (ASCII-armored, mailable)
   │                                       └─ -----BEGIN PGP MESSAGE-----
   │
   └── gpg --symmetric --cipher-algo AES256 ─▶ secret.sym.gpg  (passphrase locked)
                                           └─ anyone with the PASSPHRASE opens it
```

> **Why this matters:** Encrypting a file before it leaves your control is the single most common "protect this data" task in real ops — backups, credential handoffs, audit evidence. Knowing *which* model to reach for (recipient key vs shared passphrase) and being able to prove what a `.gpg` blob actually is keeps you from shipping the wrong thing to the wrong person.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `gpg --recipient --encrypt` | Asymmetric encrypt to a named recipient's public key | `--recipient`/`-r` selects the key; output is binary `.gpg` by default |
| `gpg -e -r` | Short form of the above (`-e` = `--encrypt`, `-r` = `--recipient`) | the everyday muscle-memory form |
| `gpg --armor` (`-a`) | Wrap binary ciphertext in printable ASCII | produces `.asc` with a `-----BEGIN PGP MESSAGE-----` header |
| `gpg --output` (`-o`) | Name the output file explicitly | without it gpg picks `<input>.gpg`/`.asc` or writes to stdout |
| `gpg --symmetric` (`-c`) | Passphrase-only encryption, no keys needed | pair with `--cipher-algo AES256` to pin a strong cipher |
| `gpg --list-packets` | Decode a ciphertext's internal structure | shows `pubkey enc packet` vs `symkey enc packet` — proof of which model was used |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** We build one throwaway sandbox folder, point GPG at a private keyring *inside* it, then generate a disposable recipient key non-interactively so we have someone to encrypt to — all under `/tmp` so a single teardown wipes the keys too.

> Run this block **once** before Task 1. It defines a single sandbox root (`LAB_ROOT`) that every file in this lab lives under, so Teardown can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-209
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"

# Keep the whole keyring inside the sandbox so teardown is clean.
export GNUPGHOME="$LAB_ROOT/gnupg"
mkdir -p "$GNUPGHOME"
chmod 700 "$GNUPGHOME"

# Non-interactive (batch) generation of a throwaway RECIPIENT key.
cat > "$LAB_ROOT/keyparams" <<'EOF'
%echo Generating throwaway Lab 209 recipient key
Key-Type: RSA
Key-Length: 2048
Subkey-Type: RSA
Subkey-Length: 2048
Name-Real: Lab 209 Recipient
Name-Email: recipient@lab209.local
Expire-Date: 0
Passphrase: labpass209
%commit
%echo done
EOF

gpg --batch --pinentry-mode loopback --gen-key "$LAB_ROOT/keyparams"
gpg --list-keys recipient@lab209.local
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
gpg: Generating throwaway Lab 209 recipient key
gpg: key A1B2C3D4E5F6A7B8 marked as ultimately trusted
gpg: done
pub   rsa2048 2026-06-15 [SCEAR]
      9F3A1C2B5D7E0F8A6B4C2D1E0F9A8B7C6D5E4F3A
uid           [ultimate] Lab 209 Recipient <recipient@lab209.local>
sub   rsa2048 2026-06-15 [SEA]
Setup complete at 2026-06-15T17:40:02-04:00
exit was: 0
```

---

## TASK 1 of 2 — Asymmetric (public-key) encryption to a recipient

**In plain English:** We encrypt a file to the recipient's public key two ways — once as raw binary and once as ASCII-armored text — and prove what each output actually is.

---

### Step 1 of 2 — Encrypt to a recipient, producing binary `.gpg`

**In plain English:** We write a short plaintext, lock it to the recipient's public key with `gpg -e -r`, and confirm the result is unreadable binary OpenPGP data.

```bash
echo "the launch code is 0451" > "$LAB_ROOT/secret.txt"
gpg -e -r recipient@lab209.local -o "$LAB_ROOT/secret.txt.gpg" "$LAB_ROOT/secret.txt"
file "$LAB_ROOT/secret.txt.gpg"
echo "exit was: $?"
```

**Expected output:**

```
/tmp/lab-209/secret.txt.gpg: PGP RSA encrypted session key - keyid: ... RSA (Encrypt or Sign) 2048b .
exit was: 0
```

**Line-by-line breakdown:**

- `echo "the launch code is 0451" > "$LAB_ROOT/secret.txt"` → Create the plaintext we will protect; this is the readable file that must never leave the box unencrypted.
- `gpg -e -r recipient@lab209.local -o "$LAB_ROOT/secret.txt.gpg" "$LAB_ROOT/secret.txt"` → `-e` (encrypt) `-r` (recipient) locks the file to that public key; `-o` names the output. Only the recipient's private key can reverse it.
- `file "$LAB_ROOT/secret.txt.gpg"` → Ask `file` what the output is; it reports a PGP RSA encrypted session key — i.e. raw binary OpenPGP, not text you could read or paste.

**New words in this step:**

- **asymmetric encryption** — a scheme using a public key to lock and a separate private key to unlock, so no shared secret is needed in advance.
- **`.gpg`** — the conventional extension for *binary* OpenPGP ciphertext.

---

### Step 2 of 2 — Produce ASCII-armored output with `--armor`

**In plain English:** We encrypt the same file again but add `--armor` so the ciphertext comes out as printable text you could safely paste into an email, then peek at its header to see the armor.

```bash
gpg --armor -e -r recipient@lab209.local -o "$LAB_ROOT/secret.txt.asc" "$LAB_ROOT/secret.txt"
head -n 2 "$LAB_ROOT/secret.txt.asc"
file "$LAB_ROOT/secret.txt.asc"
echo "exit was: $?"
```

**Expected output:**

```
-----BEGIN PGP MESSAGE-----

/tmp/lab-209/secret.txt.asc: PGP message Public-Key Encrypted Session Key (old)
exit was: 0
```

**Line-by-line breakdown:**

- `gpg --armor -e -r ... -o "$LAB_ROOT/secret.txt.asc" ...` → Same recipient encryption as Step 1, but `--armor` (`-a`) wraps the binary in printable ASCII; the `.asc` extension signals "armored."
- `head -n 2 "$LAB_ROOT/secret.txt.asc"` → Show the first two lines; the `-----BEGIN PGP MESSAGE-----` banner is the armor header that lets the blob survive email and copy-paste.
- `file "$LAB_ROOT/secret.txt.asc"` → Confirm `file` now sees it as a PGP *message* (text-armored), contrasting with the raw binary of Step 1.

**New words in this step:**

- **ASCII armor** — a printable-text wrapper around binary OpenPGP data, marked by `-----BEGIN PGP MESSAGE-----`.
- **`.asc`** — the conventional extension for *armored* (ASCII) OpenPGP output.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `gpg -e -r recipient` | encrypts to a public key (asymmetric) | the recipient key must be in your keyring first, or gpg errors |
| `--armor` (`-a`) | wraps ciphertext in printable ASCII | armored ≠ unencrypted — it is still locked, just text-safe |
| `--output` (`-o`) | names the output file | omit it and gpg may write to stdout or auto-name `<file>.gpg` |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `No public key` / `unusable public key` | The recipient key is missing or untrusted in this keyring | Re-run SETUP; confirm with `gpg --list-keys recipient@lab209.local` |
| Output went to the terminal as garbage | You forgot `-o` and gpg wrote binary to stdout | Add `-o file.gpg` (or `--armor` for text) and re-run |

---

## TASK 2 of 2 — Symmetric (passphrase-only) encryption — no keys needed

**In plain English:** We encrypt the same file with only a shared passphrase (no recipient key at all), then crack open both ciphertexts with `gpg --list-packets` to see, packet by packet, how the two models differ.

---

### Step 1 of 2 — Encrypt with a passphrase using `--symmetric` + AES256

**In plain English:** We lock the file with a single passphrase and pin the strong AES-256 cipher, running gpg non-interactively so no password prompt pops up.

```bash
gpg --batch --pinentry-mode loopback --passphrase 'labpass209' \
    --symmetric --cipher-algo AES256 \
    -o "$LAB_ROOT/secret.sym.gpg" "$LAB_ROOT/secret.txt"
file "$LAB_ROOT/secret.sym.gpg"
echo "exit was: $?"
```

**Expected output:**

```
/tmp/lab-209/secret.sym.gpg: GPG symmetrically encrypted data (AES256 cipher)
exit was: 0
```

**Line-by-line breakdown:**

- `gpg --batch --pinentry-mode loopback --passphrase 'labpass209'` → Run non-interactively: `--batch` suppresses prompts, `--pinentry-mode loopback` lets gpg take the passphrase from the command line, and `--passphrase` supplies it.
- `--symmetric --cipher-algo AES256` → `--symmetric` (`-c`) encrypts with a shared passphrase instead of a key; `--cipher-algo AES256` pins the cipher to AES-256 rather than gpg's default.
- `-o "$LAB_ROOT/secret.sym.gpg" "$LAB_ROOT/secret.txt"` → Name the output and give the plaintext input. No recipient, no keyring needed.
- `file "$LAB_ROOT/secret.sym.gpg"` → `file` reports "GPG symmetrically encrypted data (AES256 cipher)" — proof the passphrase model, not a public key, was used.

**New words in this step:**

- **symmetric encryption** — one shared secret (a passphrase) both locks and unlocks the data.
- **`--cipher-algo AES256`** — the option that forces a specific, strong symmetric cipher (AES with a 256-bit key).

---

### Step 2 of 2 — Inspect and contrast with `gpg --list-packets`

**In plain English:** We decode the internal structure of both the symmetric and the asymmetric ciphertext to see the different "session key" packets that prove which model each file uses.

```bash
gpg --list-packets "$LAB_ROOT/secret.sym.gpg" | grep -i "packet" | head -n 3
echo "--- vs the asymmetric file ---"
gpg --list-packets "$LAB_ROOT/secret.txt.gpg" | grep -i "packet" | head -n 3
echo "exit was: $?"
```

**Expected output:**

```
:symkey enc packet: version 4, cipher 9, s2k 3, hash 2
:encrypted data packet:
--- vs the asymmetric file ---
:pubkey enc packet: version 3, algo 1, keyid A1B2C3D4E5F6A7B8
:encrypted data packet:
exit was: 0
```

**Line-by-line breakdown:**

- `gpg --list-packets "$LAB_ROOT/secret.sym.gpg"` → Decode the symmetric file; the `:symkey enc packet:` line shows the session key was protected by a *passphrase-derived* key (note `cipher 9` = AES256).
- `gpg --list-packets "$LAB_ROOT/secret.txt.gpg"` → Decode the asymmetric file; the `:pubkey enc packet:` with a `keyid` shows the session key was wrapped with the recipient's *public key* instead.
- `grep -i "packet" | head -n 3` → Trim the verbose output down to the few packet lines that tell the story; the contrast (`symkey` vs `pubkey`) is the whole lesson.

**New words in this step:**

- **packet** — one structural unit inside an OpenPGP file (session key, encrypted data, signature, etc.).
- **session key** — the random per-message key that actually encrypts the data; GPG then protects *it* with either a passphrase (symmetric) or the recipient's public key (asymmetric).

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `gpg --symmetric` (`-c`) | passphrase-only encryption, no keyring | anyone with the passphrase can decrypt — distribution is the weak point |
| `--cipher-algo AES256` | pins a strong symmetric cipher | omitting it falls back to gpg's default, which may be weaker/older |
| `gpg --list-packets` | reveals `symkey` vs `pubkey` enc packets | it does NOT decrypt — it only shows structure, no passphrase needed |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `Inappropriate ioctl for device` / hangs on a prompt | No loopback pinentry, so gpg tried to open a GUI/tty prompt | Add `--batch --pinentry-mode loopback --passphrase '...'` |
| `--list-packets` asks for a passphrase | You ran a command that decrypts instead of listing | Use `--list-packets` (structure only); it never needs the passphrase |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Encrypt to a recipient, producing binary `.gpg`
- [ ] Task 1 · Step 2 — Produce ASCII-armored output with `--armor`
- [ ] Task 2 · Step 1 — Encrypt with a passphrase using `--symmetric` + AES256
- [ ] Task 2 · Step 2 — Inspect and contrast with `gpg --list-packets`

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. Because the GPG keyring (`GNUPGHOME`) lives *inside* `$LAB_ROOT`, removing the root also wipes the throwaway recipient key — no separate key cleanup is needed.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-209
```

**Expected output:**

```
✅ Removed /tmp/lab-209 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Encrypting to a key that is not in your keyring | `No public key` error, nothing written | Import/generate the recipient key first; verify with `gpg --list-keys` |
| Thinking `--armor` means "not encrypted" | Pasting the `.asc` assuming it is readable | Armor is just a text wrapper; the contents are still locked |
| Forgetting `--cipher-algo` on symmetric encryption | Weaker/older default cipher used | Always pin `--cipher-algo AES256` for predictable strength |

---

## 📌 Exam Strategy

When a task says "encrypt this file for *so-and-so*," that is asymmetric — `gpg -e -r recipient`, and make sure their public key is imported first. When it says "protect this file with a passphrase," that is symmetric — `gpg -c --cipher-algo AES256`. Add `--armor` only when the output must travel as text (email, a config field), and always name the output with `-o` so you control the filename.

- Say "`-e -r` = encrypt to a recipient, `-c` = symmetric passphrase" before you type — it picks the right model instantly.
- Use `file` and `gpg --list-packets` to *prove* what a ciphertext is rather than guessing from the extension.
- For non-interactive work, `--batch --pinentry-mode loopback --passphrase '...'` is the reliable trio that avoids prompt hangs.

---

## 🔗 Related Labs

- [Lab 209b — Encrypt a File with GPG (Ansible)](../lab-209b-gpg-encrypt-file-ansible/) — the same encryption expressed in an idempotent playbook
- [Lab 209c — Encrypt a File with GPG (Verify)](../lab-209c-gpg-encrypt-file-verify/) — prove the `.gpg`/`.asc`/`.sym.gpg` files are real, armored, and packet-correct
- [Lab 208a — Generate a GPG Key (RHCSA)](../lab-208a-gpg-generate-key-rhcsa/) — create the keypair that makes recipient encryption possible
- [Lab 210a — Decrypt a File with GPG (RHCSA)](../lab-210a-gpg-decrypt-file-rhcsa/) — the reverse trip: turning these ciphertexts back into plaintext

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
