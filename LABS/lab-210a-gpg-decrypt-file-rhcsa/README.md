# Lab 210a: Decrypt a GPG File (RHCSA) — `gpg --decrypt`, `gpg -d --output`

**Series:** linux-ops-mastery — GPG Encryption · **Lab 210a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (handling encrypted artifacts and reproducing files from secured sources), RHCE EX294 (the shell behavior behind `ansible.builtin.shell` gpg calls), SRE/DevOps (recovering secrets and encrypted backups in headless pipelines)  
**Prerequisite:** [Lab 209a](../lab-209a-gpg-encrypt-file-rhcsa/) (you must be able to *encrypt* before you decrypt), a RHEL/Rocky/Alma sandbox you can `sudo` on, and `gpg --version` succeeding  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Learn to recover plaintext from two kinds of GPG ciphertext — an **asymmetric** (public-key) file that needs your private key plus its passphrase, and a **symmetric** file that needs only a shared passphrase — and to do it **non-interactively** so the same command works in a script or on a headless server. By the end you can decrypt to stdout or to a named file with `-o`, force overwrites with `--batch --yes`, read the exit code to detect a wrong passphrase, and prove the recovered bytes are identical to the original with `sha256sum` and `diff`.

---

## 🧠 Concept

GPG decryption reverses encryption, but *how* it finds the key differs by mode. An **asymmetric** file was sealed to a recipient's public key, so only the matching **private key** can open it — and that private key is itself protected by a passphrase. A **symmetric** file was sealed with a passphrase alone (no keypair involved), so the same passphrase opens it. The catch on servers: GPG normally pops a graphical or curses **pinentry** prompt to ask for the passphrase, which fails when there is no terminal. `--pinentry-mode loopback` routes that prompt back through GPG itself so `--passphrase` can supply it on the command line, making decryption fully scriptable.

```
ASYMMETRIC (public-key)              SYMMETRIC (passphrase-only)
─────────────────────────────       ──────────────────────────────────
secret.txt.gpg                       secret.sym.gpg
   │ needs PRIVATE key + passphrase     │ needs SHARED passphrase only
   ▼                                    ▼
gpg -d secret.txt.gpg                gpg -d secret.sym.gpg
   └─▶ plaintext on stdout              └─▶ plaintext on stdout
   (add -o file to write a file instead of printing)
```

> **Why this matters:** Decryption that hangs on a hidden pinentry prompt is the number-one reason "it worked on my laptop" scripts freeze in CI and on remote hosts. Knowing the loopback/`--passphrase`/`--batch` trio — and checking `$?` so a wrong passphrase fails loudly instead of silently — is the difference between a recoverable secret and a 2 a.m. outage.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `gpg --decrypt` (`-d`) | Decrypt a file and print plaintext to stdout | the **anchor** — works for both asymmetric and symmetric ciphertext |
| `gpg -d --output FILE` (`-o`) | Decrypt and write plaintext to a named file instead of the screen | `-o` must precede the input file; pair with `--decrypt` |
| `--pinentry-mode loopback` | Route the passphrase prompt back through gpg so it can be scripted | required for headless/non-interactive decrypt; pairs with `--passphrase` |
| `--passphrase 'STR'` | Supply the passphrase on the command line | only honored with `--pinentry-mode loopback` (or in agent config) |
| `--batch --yes` | Never prompt; answer "yes" to overwrite questions | lets a decrypt overwrite an existing output file unattended |
| `sha256sum` / `diff` | Prove recovered plaintext is byte-identical to the original | clean `diff` = exit `0`; matching hash = lossless recovery |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** We build a throwaway workspace under `/tmp`, point GPG's keyring at a sandboxed `GNUPGHOME` so nothing touches your real keys, generate a disposable keypair, then create one plaintext and seal it **two ways** — asymmetric and symmetric — so we have real ciphertext to decrypt.

> Run this block **once** before Task 1. It defines a single sandbox root (`LAB_ROOT`) that every file in this lab lives under, so Teardown can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-210
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"

# Keep the whole keyring inside the sandbox so teardown is clean
export GNUPGHOME="$LAB_ROOT/gnupg"
mkdir -p "$GNUPGHOME"
chmod 700 "$GNUPGHOME"

# Generate a disposable keypair non-interactively
gpg --batch --pinentry-mode loopback --passphrase 'LabPass210!' \
    --quick-generate-key 'Lab 210 <lab210@example.com>' default default never

# Create the original plaintext we will later recover
echo "top secret: the vault code is 4815-1623-4208" > secret.txt

# Seal it ASYMMETRICALLY (to the recipient's public key)
gpg --batch --yes -e -r 'lab210@example.com' -o secret.txt.gpg secret.txt

# Seal it SYMMETRICALLY (passphrase only, no keypair used)
gpg --batch --yes --pinentry-mode loopback --passphrase 'LabPass210!' \
    --symmetric -o secret.sym.gpg secret.txt

ls -l "$LAB_ROOT"
echo "exit was: $?"
```

**Expected output:**

```
gpg: key A1B2C3D4E5F6 marked as ultimately trusted
gpg: directory '/tmp/lab-210/gnupg/openpgp-revocs.d' created
gpg: revocation certificate stored as '/tmp/lab-210/gnupg/openpgp-revocs.d/....rev'
total 16
drwx------. 3 root root  140 Jun 15 17:40 gnupg
-rw-r--r--. 1 root root   46 Jun 15 17:40 secret.txt
-rw-r--r--. 1 root root  478 Jun 15 17:40 secret.txt.gpg
-rw-r--r--. 1 root root  118 Jun 15 17:40 secret.sym.gpg
exit was: 0
```

---

## TASK 1 of 2 — Decrypt an asymmetric (public-key) file

**In plain English:** We open the file that was sealed to our public key by supplying the private key's passphrase non-interactively, write the result to a named file, and then prove the recovered text is byte-for-byte identical to the original.

---

### Step 1 of 2 — Decrypt `secret.txt.gpg` to a file with loopback pinentry

**In plain English:** We run a fully non-interactive decrypt — the loopback pinentry lets us hand GPG the passphrase on the command line instead of waiting for a prompt that would never appear on a headless box.

```bash
cd "$LAB_ROOT"
gpg --batch --pinentry-mode loopback --passphrase 'LabPass210!' \
    -o recovered.txt --decrypt secret.txt.gpg
echo "exit was: $?"
cat recovered.txt
```

**Expected output:**

```
gpg: encrypted with rsa3072 key, ID A1B2C3D4E5F6, created 2026-06-15
      "Lab 210 <lab210@example.com>"
exit was: 0
top secret: the vault code is 4815-1623-4208
```

**Line-by-line breakdown:**

- `gpg --batch` → Run unattended: never stop to ask interactive questions, which is exactly what a script or remote host needs.
- `--pinentry-mode loopback` → Tell GPG not to launch the external pinentry program; route the passphrase request back through GPG so it can be answered on the command line. Without this, `--passphrase` is ignored and the decrypt hangs or fails for lack of a terminal.
- `--passphrase 'LabPass210!'` → Supply the **private key's** passphrase directly (in real life you would read it from a file, env var, or secrets manager — never hard-code it).
- `-o recovered.txt --decrypt secret.txt.gpg` → `--decrypt` (the anchor) opens the ciphertext; `-o recovered.txt` writes the plaintext to a named file instead of stdout.
- `echo "exit was: $?"` → Print GPG's exit status; `0` means the passphrase was correct and decryption succeeded.

**New words in this step:**

- **pinentry** — the helper program GPG normally launches to ask for a passphrase; `loopback` mode bypasses it so the prompt can be answered programmatically.
- **loopback mode** — routing the passphrase request back through GPG itself instead of an external prompt, enabling non-interactive decryption.

---

### Step 2 of 2 — Prove the recovery is byte-identical with `diff` and `sha256sum`

**In plain English:** We compare the recovered file against the original both ways — a clean `diff` and a matching SHA-256 fingerprint — so we have objective proof that decryption lost nothing.

```bash
cd "$LAB_ROOT"
diff secret.txt recovered.txt && echo "diff MATCH (OK)"
echo "diff exit: $?"
sha256sum secret.txt recovered.txt
```

**Expected output:**

```
diff MATCH (OK)
diff exit: 0
9f3a1c2b...e7  secret.txt
9f3a1c2b...e7  recovered.txt
```

**Line-by-line breakdown:**

- `diff secret.txt recovered.txt` → Compare the original and recovered files; no output means they are identical, so the exit code is `0` and `&& echo "diff MATCH (OK)"` fires.
- `echo "diff exit: $?"` → Print `diff`'s exit status; `0` = identical, `1` = they differ (which would mean decryption was lossy or the wrong file).
- `sha256sum secret.txt recovered.txt` → Fingerprint both files; identical 64-hex hashes are the strongest "byte-for-byte equal" proof, catching even a trailing-newline difference `cat` would miss.

**New words in this step:**

- **fidelity** — whether the recovered plaintext exactly matches the original; proven here by a matching hash and a clean diff.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `gpg --decrypt` | opens ciphertext using the private key for asymmetric files | needs the private key *and* its passphrase, not just the passphrase |
| `--pinentry-mode loopback` | answers the passphrase prompt without a terminal | omit it and `--passphrase` is silently ignored |
| `-o FILE` | writes plaintext to a file instead of stdout | place `-o file` before the input filename |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `gpg: decryption failed: No secret key` | The matching private key is not in this `GNUPGHOME` | Re-run SETUP, or point `GNUPGHOME` at the keyring that holds the key |
| Command hangs or `Inappropriate ioctl for device` | Missing `--pinentry-mode loopback` on a headless host | Add `--pinentry-mode loopback` so the passphrase can be supplied non-interactively |

---

## TASK 2 of 2 — Decrypt a symmetric file and the batch/exit-code pattern

**In plain English:** We open the passphrase-only file with no private key involved, contrast stdout vs `-o`, then deliberately use a wrong passphrase to watch the exit code go non-zero — the hook a script uses to detect failure.

---

### Step 1 of 2 — Decrypt the symmetric file to stdout, then to a file

**In plain English:** We decrypt the same passphrase using nothing but `--passphrase` — there is no key lookup at all — first printing to the screen, then writing to a named file with `-o`.

```bash
cd "$LAB_ROOT"
gpg --batch --pinentry-mode loopback --passphrase 'LabPass210!' \
    -d secret.sym.gpg
gpg --batch --pinentry-mode loopback --passphrase 'LabPass210!' \
    -o recovered.sym.txt -d secret.sym.gpg
echo "exit was: $?"
diff secret.txt recovered.sym.txt && echo "symmetric MATCH (OK)"
```

**Expected output:**

```
gpg: AES256.CFB encrypted data
gpg: encrypted with 1 passphrase
top secret: the vault code is 4815-1623-4208
symmetric MATCH (OK)
exit was: 0
```

**Line-by-line breakdown:**

- first `gpg ... -d secret.sym.gpg` → Decrypt to stdout; the banner says `encrypted with 1 passphrase`, confirming **no private key was consulted** — symmetric mode unlocks purely with the shared passphrase.
- second `gpg ... -o recovered.sym.txt -d secret.sym.gpg` → Same decrypt, but `-o` writes the plaintext to a file so we can verify it instead of just viewing it.
- `echo "exit was: $?"` → Report the exit status of the file-writing decrypt; `0` confirms success.
- `diff secret.txt recovered.sym.txt && echo "symmetric MATCH (OK)"` → Prove the symmetric recovery matches the original, just as in Task 1.

**New words in this step:**

- **symmetric encryption** — one shared secret (a passphrase) both seals and opens the data; no public/private keypair is involved.

---

### Step 2 of 2 — Force overwrite with `--batch --yes`, then detect a wrong passphrase

**In plain English:** We re-decrypt over an existing output file using `--batch --yes` so it never prompts, then run it again with the *wrong* passphrase to watch the decrypt fail and `$?` go non-zero — exactly what a script tests to catch a bad secret.

```bash
cd "$LAB_ROOT"
gpg --batch --yes --pinentry-mode loopback --passphrase 'LabPass210!' \
    -o recovered.sym.txt -d secret.sym.gpg
echo "good-pass exit: $?"

gpg --batch --yes --pinentry-mode loopback --passphrase 'WRONG-pass' \
    -o recovered.sym.txt -d secret.sym.gpg
echo "bad-pass exit: $?"
```

**Expected output:**

```
gpg: AES256.CFB encrypted data
gpg: encrypted with 1 passphrase
good-pass exit: 0
gpg: AES256.CFB encrypted data
gpg: encrypted with 1 passphrase
gpg: decryption failed: Bad session key
bad-pass exit: 2
```

**Line-by-line breakdown:**

- first `gpg --batch --yes ... -o recovered.sym.txt ...` → `recovered.sym.txt` already exists from Step 1; `--batch --yes` answers the "overwrite?" question with "yes" so the decrypt completes unattended (`good-pass exit: 0`).
- `echo "good-pass exit: $?"` → Confirm the correct passphrase yields exit `0`.
- second `gpg ... --passphrase 'WRONG-pass' ...` → Same command with a wrong passphrase; GPG cannot derive the session key, prints `decryption failed: Bad session key`, and exits non-zero.
- `echo "bad-pass exit: $?"` → Print the failure code (`2`); a script keys on `if [ $? -ne 0 ]` here to abort instead of trusting a garbage output file.

**New words in this step:**

- **session key** — the per-message symmetric key GPG derives to actually scramble the data; a wrong passphrase produces the wrong session key and decryption fails.
- **exit code (`$?`)** — the numeric success/failure status of the last command; `0` = success, non-zero = failure, the hook scripts use to detect a bad passphrase.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| symmetric `-d` | opens passphrase-only ciphertext with no keypair | a missing private key is irrelevant here — only the passphrase matters |
| `--batch --yes` | overwrites the output file without prompting | without `--yes`, an existing output file aborts the unattended run |
| reading `$?` | turns a wrong passphrase into a detectable failure | GPG may still create a 0-byte output on failure — always check `$?`, not just the file |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `File 'recovered.sym.txt' exists. Overwrite? (y/N)` then hangs | Re-decrypting without `--batch --yes` | Add `--batch --yes` for unattended overwrite |
| Exit code is `0` but the file looks wrong | You trusted the output instead of the status, or a stale file | Always test `$?`; on failure delete the partial output before retrying |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Decrypt `secret.txt.gpg` to a file with loopback pinentry
- [ ] Task 1 · Step 2 — Prove the recovery is byte-identical with `diff` and `sha256sum`
- [ ] Task 2 · Step 1 — Decrypt the symmetric file to stdout, then to a file
- [ ] Task 2 · Step 2 — Force overwrite with `--batch --yes`, then detect a wrong passphrase

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. Because the entire keyring lives under `$GNUPGHOME` inside `$LAB_ROOT`, this one command removes the keys too — no `gpg --delete-secret-keys` needed.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-210
```

**Expected output:**

```
✅ Removed /tmp/lab-210 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Forgetting `--pinentry-mode loopback` | Decrypt hangs or `Inappropriate ioctl for device` | Add loopback mode so `--passphrase` is honored without a terminal |
| Putting `-o` after the input file | Plaintext lands on stdout instead of the file | Order it as `-o FILE --decrypt INPUT.gpg` |
| Trusting output without checking `$?` | A wrong passphrase leaves a 0-byte file unnoticed | Read `$?` after every decrypt and abort on non-zero |

---

## 📌 Exam Strategy

When a task hands you an encrypted file, first decide *which* secret opens it — a private key plus its passphrase (asymmetric) or a shared passphrase (symmetric) — because that dictates whether the key must be imported first. On any non-interactive box, reach for the `--batch --pinentry-mode loopback --passphrase` trio so the decrypt never stalls on a hidden prompt, and verify the result rather than assuming it.

- Memorize the order: `gpg --batch --pinentry-mode loopback --passphrase 'X' -o OUT -d IN.gpg`.
- Always confirm recovery with `diff` or `sha256sum` against a known original — a clean diff is the grader's proof.
- Check `$?` after the decrypt; a wrong passphrase exits non-zero even when an empty output file is left behind.

---

## 🔗 Related Labs

- [Lab 210b — Decrypt a GPG File (Ansible)](../lab-210b-gpg-decrypt-file-ansible/) — the same decrypt expressed as an idempotent `ansible.builtin.shell` task
- [Lab 210c — Decrypt a GPG File (Verify)](../lab-210c-gpg-decrypt-file-verify/) — prove recovery is byte-identical and a wrong passphrase fails
- [Lab 209a — Encrypt a GPG File (RHCSA)](../lab-209a-gpg-encrypt-file-rhcsa/) — the prerequisite that produces the ciphertext you decrypt here
- [Lab 211a — Share & Verify GPG Keys (RHCSA)](../lab-211a-gpg-share-keys-rhcsa/) — exporting and trusting the keys that make asymmetric decrypt possible

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
