# Lab 209c: Encrypt a File with GPG (Verify) — `file`, `gpg --list-packets`, `grep`

**Series:** linux-ops-mastery — GPG Encryption · **Lab 209c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving data is actually protected before handoff), Security+/SRE (confidentiality verification), DevOps (artifact-encryption gates in CI)  
**Prerequisite:** [Lab 209a](../lab-209a-gpg-encrypt-file-rhcsa/) and [Lab 209b](../lab-209b-gpg-encrypt-file-ansible/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Objective

Take the auditor's seat: prove a file is *actually encrypted* and that each output is the kind you intended. You will assert the binary ciphertext is unreadable OpenPGP (not accidental plaintext), that the armored output really carries the `-----BEGIN PGP MESSAGE-----` banner, and — the decisive check — that `gpg --list-packets` shows a **public-key** session packet for the asymmetric file and a **symmetric** session packet for the passphrase file. These are objective, scriptable proofs of *which* encryption model produced each blob.

---

## 🧠 Concept

"Encrypted" is a claim you can verify three ways. First, **type**: `file` reads the magic bytes and reports "PGP RSA encrypted session key" (binary) or "PGP message" (armored), so you can prove the output is not plaintext that slipped through. Second, **armor**: an ASCII-armored file must begin with `-----BEGIN PGP MESSAGE-----`; grepping for that line proves the armor is present. Third, and most important, **model**: `gpg --list-packets` decodes the file's internal structure *without decrypting it*, revealing a `pubkey enc packet` (the session key was wrapped with a recipient's public key) versus a `symkey enc packet` (the session key was derived from a passphrase). The packet type is the ground truth of how the file was sealed.

```
secret.txt.gpg   → file: "PGP RSA encrypted session key"   → list-packets: :pubkey enc packet:
secret.txt.asc   → head: "-----BEGIN PGP MESSAGE-----"      → armored variant of the above
secret.sym.gpg   → file: "GPG symmetrically encrypted data" → list-packets: :symkey enc packet: (cipher 9 = AES256)
```

> **Why this matters:** Shipping a file you *think* is encrypted but is actually plaintext — or symmetric when the policy required a recipient key — is a real breach. `file` and `list-packets` turn "it should be encrypted" into proof a grader (or auditor) can re-run.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `test -s FILE` | Assert a file exists and is non-empty | `-s` is true only for a non-zero-size file |
| `file FILE` | Identify a file by its magic bytes | reports the OpenPGP type without decrypting |
| `head -n 1` | Read the first line (the armor banner) | proves `-----BEGIN PGP MESSAGE-----` is present |
| `gpg --list-packets FILE` | Decode OpenPGP structure without decrypting | needs no passphrase; reveals `pubkey` vs `symkey` packets |
| `grep -q` | Quiet match for a pass/fail assertion | exit `0` = found, `1` = not found |
| `cmp -s` | Byte-compare two files silently | proves ciphertext differs from the plaintext |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and a sandbox keyring, generate a throwaway recipient key, then seal one plaintext three ways — binary asymmetric, armored asymmetric, and symmetric — so there is real ciphertext to audit.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-209
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"

export GNUPGHOME="$LAB_ROOT/gnupg"
mkdir -p "$GNUPGHOME"
chmod 700 "$GNUPGHOME"

gpg --batch --pinentry-mode loopback --passphrase 'labpass209' \
    --quick-generate-key 'Lab 209 Recipient <recipient@lab209.local>' default default never 2>/dev/null

echo "the launch code is 0451" > secret.txt
gpg --batch --yes -e -r recipient@lab209.local -o secret.txt.gpg secret.txt
gpg --batch --yes --armor -e -r recipient@lab209.local -o secret.txt.asc secret.txt
gpg --batch --yes --pinentry-mode loopback --passphrase 'labpass209' \
    --symmetric --cipher-algo AES256 -o secret.sym.gpg secret.txt

ls -1 "$LAB_ROOT"/secret.* 
echo "exit was: $?"
```

**Expected output:**

```
/tmp/lab-209/secret.sym.gpg
/tmp/lab-209/secret.txt
/tmp/lab-209/secret.txt.asc
/tmp/lab-209/secret.txt.gpg
exit was: 0
```

---

## TASK 1 of 2 — Assert the outputs exist and are correctly typed

**In plain English:** We prove the binary ciphertext is real OpenPGP and genuinely differs from the plaintext, then prove the armored file carries the PGP message banner.

---

### Step 1 of 2 — Assert the binary `.gpg` is OpenPGP, not plaintext

**In plain English:** We confirm the file exists, that `file` sees encrypted OpenPGP data, and that its bytes are not just the original plaintext that leaked through.

```bash
cd "$LAB_ROOT"
test -s secret.txt.gpg && echo "CIPHERTEXT EXISTS (OK)" || echo "MISSING (FAIL)"
file secret.txt.gpg
file secret.txt.gpg | grep -qi 'PGP' && echo "TYPE IS OPENPGP (OK)" || echo "NOT OPENPGP (FAIL)"
cmp -s secret.txt secret.txt.gpg && echo "MATCHES PLAINTEXT (FAIL)" || echo "DIFFERS FROM PLAINTEXT (OK)"
```

**Expected output:**

```
CIPHERTEXT EXISTS (OK)
/tmp/lab-209/secret.txt.gpg: PGP RSA encrypted session key - keyid: ... RSA (Encrypt or Sign) 2048b .
TYPE IS OPENPGP (OK)
DIFFERS FROM PLAINTEXT (OK)
```

**Line-by-line breakdown:**

- `test -s secret.txt.gpg && ... || ...` → Assert the ciphertext exists and is non-empty; `-s` rejects a zero-byte file from a failed encrypt.
- `file secret.txt.gpg | grep -qi 'PGP'` → Read the magic bytes and assert they identify OpenPGP data; `-q` makes `grep` a silent pass/fail.
- `cmp -s secret.txt secret.txt.gpg` → Byte-compare against the plaintext; they must **differ**, so the `||` (OK) branch fires — proof the content was actually transformed.

**New words in this step:**

- **magic bytes** — the leading signature bytes a file format starts with, which `file` uses to identify type without trusting the extension.
- **`cmp -s`** — a silent byte-for-byte comparison; exit `0` means identical, non-zero means they differ.

---

### Step 2 of 2 — Assert the armored `.asc` carries the PGP banner

**In plain English:** We prove the armored output is text-safe by checking its first line is the `-----BEGIN PGP MESSAGE-----` banner that lets it travel through email.

```bash
cd "$LAB_ROOT"
head -n 1 secret.txt.asc
head -n 1 secret.txt.asc | grep -q 'BEGIN PGP MESSAGE' && echo "ARMOR PRESENT (OK)" || echo "NOT ARMORED (FAIL)"
file secret.txt.asc
```

**Expected output:**

```
-----BEGIN PGP MESSAGE-----
ARMOR PRESENT (OK)
/tmp/lab-209/secret.txt.asc: PGP message Public-Key Encrypted Session Key (old)
```

**Line-by-line breakdown:**

- `head -n 1 secret.txt.asc` → Print the first line; armored OpenPGP always opens with the `-----BEGIN PGP MESSAGE-----` banner.
- `... | grep -q 'BEGIN PGP MESSAGE' && echo OK || echo FAIL` → Assert the banner is present, turning "is it armored?" into a verdict.
- `file secret.txt.asc` → Confirm `file` classifies it as a PGP *message* (text-armored), distinct from the binary blob in Step 1.

**New words in this step:**

- **ASCII armor** — a printable-text wrapper around binary OpenPGP, delimited by `-----BEGIN/END PGP MESSAGE-----`.
- **armor banner** — the literal first line that proves a file is armored, not raw binary.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `file` on a `.gpg` | identifies OpenPGP by magic bytes | trust the magic bytes, not the file extension |
| `cmp -s` vs plaintext | proves the bytes actually changed | a 0-byte output can "exist" yet be useless |
| armor banner check | proves `.asc` is text-armored | armored ≠ unencrypted — it is still locked |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `MATCHES PLAINTEXT (FAIL)` | Encryption silently failed; output is empty/copy | Re-run SETUP; confirm the recipient key exists |
| `NOT ARMORED (FAIL)` | `--armor` was omitted at encryption | Re-encrypt with `--armor` to produce `.asc` |

---

## TASK 2 of 2 — Assert the encryption model via `--list-packets`

**In plain English:** We decode each ciphertext's internal packets — without decrypting — to prove the asymmetric file used a public-key session packet and the symmetric file used a passphrase-derived one.

---

### Step 1 of 2 — Prove the asymmetric file uses a `pubkey enc packet`

**In plain English:** We list the packets of the binary `.gpg` and assert the session key was wrapped with a recipient's public key — the signature of asymmetric encryption.

```bash
cd "$LAB_ROOT"
gpg --list-packets secret.txt.gpg | grep -i 'packet' | head -n 3
gpg --list-packets secret.txt.gpg | grep -qi 'pubkey enc packet' && echo "ASYMMETRIC CONFIRMED (OK)" || echo "NOT ASYMMETRIC (FAIL)"
```

**Expected output:**

```
:pubkey enc packet: version 3, algo 1, keyid A1B2C3D4E5F6A7B8
:encrypted data packet:
ASYMMETRIC CONFIRMED (OK)
```

**Line-by-line breakdown:**

- `gpg --list-packets secret.txt.gpg | grep -i 'packet' | head -n 3` → Decode the structure (no passphrase needed) and show the first few packet lines.
- `... | grep -qi 'pubkey enc packet' && echo OK || echo FAIL` → Assert a `pubkey enc packet` is present, proving the session key was protected with a public key (asymmetric), not a passphrase.

**New words in this step:**

- **packet** — one structural unit inside an OpenPGP file (session key, encrypted data, signature, etc.).
- **`pubkey enc packet`** — the packet showing the session key was wrapped with a recipient's public key (asymmetric model).

---

### Step 2 of 2 — Prove the symmetric file uses a `symkey enc packet`

**In plain English:** We list the packets of the `.sym.gpg` and assert it carries a symmetric session packet using cipher 9 (AES-256) — the signature of passphrase-only encryption.

```bash
cd "$LAB_ROOT"
gpg --list-packets secret.sym.gpg | grep -i 'packet' | head -n 3
gpg --list-packets secret.sym.gpg | grep -qi 'symkey enc packet' && echo "SYMMETRIC CONFIRMED (OK)" || echo "NOT SYMMETRIC (FAIL)"
gpg --list-packets secret.sym.gpg | grep -qi 'cipher 9' && echo "AES256 CONFIRMED (OK)" || echo "CIPHER NOT AES256 (check)"
```

**Expected output:**

```
:symkey enc packet: version 4, cipher 9, s2k 3, hash 2
:encrypted data packet:
SYMMETRIC CONFIRMED (OK)
AES256 CONFIRMED (OK)
```

**Line-by-line breakdown:**

- `gpg --list-packets secret.sym.gpg | grep -i 'packet' | head -n 3` → Decode the symmetric file's structure; the `:symkey enc packet:` line is the giveaway.
- `... | grep -qi 'symkey enc packet' && echo OK || echo FAIL` → Assert the symmetric session packet is present (no public key was used).
- `... | grep -qi 'cipher 9'` → Cipher algorithm 9 is AES-256; asserting it proves the `--cipher-algo AES256` request actually took effect.

**New words in this step:**

- **`symkey enc packet`** — the packet showing the session key was derived from a passphrase (symmetric model).
- **cipher 9** — the OpenPGP numeric ID for AES-256, visible in the symmetric packet.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `--list-packets` | reveals structure without decrypting | it never needs the passphrase — it does not decrypt |
| `pubkey enc packet` | marks asymmetric (recipient key) | absence here means it is not recipient-encrypted |
| `symkey enc packet` + cipher 9 | marks symmetric AES-256 | a different cipher number means a weaker/other algo |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `--list-packets` prompts for a passphrase | You ran a decrypt command instead | Use `--list-packets` (structure only) |
| Neither packet type matches | Audited the wrong file | Point `--list-packets` at the correct `.gpg`/`.sym.gpg` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Assert the binary `.gpg` is OpenPGP, not plaintext
- [ ] Task 1 · Step 2 — Assert the armored `.asc` carries the PGP banner
- [ ] Task 2 · Step 1 — Prove the asymmetric file uses a `pubkey enc packet`
- [ ] Task 2 · Step 2 — Prove the symmetric file uses a `symkey enc packet`

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. The keyring and ciphertext all live under `$LAB_ROOT`, so one wipe is enough — this lab changed **no** system state.

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
| Trusting the extension instead of `file` | A misnamed plaintext passes as "encrypted" | Verify type with `file` and `--list-packets` |
| Assuming armored means decrypted | Pasting `.asc` expecting readable text | The banner marks armor, not plaintext |
| Reading `--list-packets` as decryption | Expecting plaintext output | It only reveals structure; it never decrypts |

---

## 📌 Exam Strategy

Verification proves the file is protected the way the task demanded. After encrypting, run `file` to confirm the output is OpenPGP and not plaintext, check the armor banner when text output was required, and use `--list-packets` to prove asymmetric vs symmetric. Make these checks a habit before any encrypted handoff.

- `file` first — the fastest "is this actually encrypted?" check.
- `--list-packets` is the ground truth for *which* model sealed the file.
- A clean `cmp` against the plaintext proves the bytes truly changed.

---

## 🔗 Related Labs

- [Lab 209a — Encrypt a File with GPG (RHCSA)](../lab-209a-gpg-encrypt-file-rhcsa/) — the creator-seat lab this audits
- [Lab 209b — Encrypt a File with GPG (Ansible)](../lab-209b-gpg-encrypt-file-ansible/) — the playbook whose outputs you verify the same way
- [Lab 210c — Decrypt a GPG File (Verify)](../lab-210c-gpg-decrypt-file-verify/) — the reverse audit: prove recovery is byte-identical

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
