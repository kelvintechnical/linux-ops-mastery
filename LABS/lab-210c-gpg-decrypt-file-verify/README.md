# Lab 210c: Decrypt a GPG File (Verify) — `sha256sum`, `diff`, exit-code assertions

**Series:** linux-ops-mastery — GPG Encryption · **Lab 210c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving recovered data is intact), SRE (restore verification), DevOps (decrypt gates and failure detection in CI)  
**Prerequisite:** [Lab 210a](../lab-210a-gpg-decrypt-file-rhcsa/) and [Lab 210b](../lab-210b-gpg-decrypt-file-ansible/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Objective

Take the auditor's seat: prove that decryption recovered the *exact* original and that a *wrong* passphrase fails loudly. You will decrypt both an asymmetric and a symmetric file non-interactively, then assert byte-for-byte fidelity with `sha256sum` and `diff`, and finally run a deliberate wrong-passphrase decrypt to confirm the exit code goes non-zero — the hook automation must trust instead of a possibly-empty output file.

---

## 🧠 Concept

A decrypt is "good" only if two things hold: the recovered plaintext is **byte-identical** to the original, and a **bad passphrase is detectable**. Fidelity is proven with a hash (`sha256sum`) — identical bytes share a fingerprint, and even a trailing-newline difference flips it — backed up by a clean `diff`. Failure detection matters because GnuPG can exit non-zero *and* still leave a zero-byte output file; trusting the file's existence would hide the failure, so you test the **exit code** (`$?`) instead. Because a non-zero exit would normally abort a script under `set -e`, you temporarily relax that (`set +e`) around the expected-failure check so you can capture and assert on the code.

```
GOOD decrypt:  gpg ... -d file  → recovered == original  (sha256 match, diff clean, $?=0)
BAD passphrase: gpg ... -d file → "Bad session key"      ($? != 0, even if a stub file exists)
```

> **Why this matters:** "It decrypted" is not enough — automation needs proof the plaintext is whole and a guarantee that a wrong key fails instead of silently producing garbage. Hashes and exit codes are that proof.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `gpg --decrypt` (`-d`) | Recover plaintext (the anchor) | pair with loopback pinentry for non-interactive runs |
| `sha256sum` | Byte-exact fingerprint of a file | identical files share a hash; any change flips it |
| `diff` | Show whether two files differ | clean diff = exit `0`; differences = exit `1` |
| `set +e` / `set -e` | Allow / forbid a non-zero exit to continue | wrap an expected-failure check so it does not abort |
| `$?` | The exit code of the last command | the real success/failure signal, not the output file |
| `awk '{print $1}'` | Keep just the hash from `sha256sum` output | strips the filename column for comparison |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and a sandbox keyring, generate a disposable keypair, and seal one plaintext two ways (asymmetric and symmetric) so there is real ciphertext to decrypt and audit.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-210
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"

export GNUPGHOME="$LAB_ROOT/gnupg"
mkdir -p "$GNUPGHOME"
chmod 700 "$GNUPGHOME"

gpg --batch --pinentry-mode loopback --passphrase 'LabPass210!' \
    --quick-generate-key 'Lab 210 <lab210@example.com>' default default never 2>/dev/null

echo "top secret: the vault code is 4815-1623-4208" > secret.txt
gpg --batch --yes -e -r 'lab210@example.com' -o secret.txt.gpg secret.txt
gpg --batch --yes --pinentry-mode loopback --passphrase 'LabPass210!' \
    --symmetric -o secret.sym.gpg secret.txt

ls -1 "$LAB_ROOT"/secret.*
echo "exit was: $?"
```

**Expected output:**

```
/tmp/lab-210/secret.sym.gpg
/tmp/lab-210/secret.txt
/tmp/lab-210/secret.txt.gpg
exit was: 0
```

---

## TASK 1 of 2 — Prove the asymmetric recovery is byte-identical

**In plain English:** We decrypt the public-key file non-interactively, then prove the recovered plaintext exactly matches the original with both a clean `diff` and a matching SHA-256 hash.

---

### Step 1 of 2 — Decrypt and check the exit code

**In plain English:** We run a fully non-interactive decrypt and assert it exits `0`, the first sign the passphrase and key were correct.

```bash
cd "$LAB_ROOT"
gpg --batch --pinentry-mode loopback --passphrase 'LabPass210!' \
    -o recovered.txt --decrypt secret.txt.gpg 2>/dev/null
rc=$?
echo "decrypt exit code: $rc"
[ "$rc" -eq 0 ] && echo "DECRYPT SUCCEEDED (OK)" || echo "DECRYPT FAILED (FAIL)"
```

**Expected output:**

```
decrypt exit code: 0
DECRYPT SUCCEEDED (OK)
```

**Line-by-line breakdown:**

- `gpg --batch --pinentry-mode loopback --passphrase 'LabPass210!' -o recovered.txt --decrypt secret.txt.gpg` → Decrypt the asymmetric file with the private key's passphrase, writing the plaintext to `recovered.txt`; `2>/dev/null` hides the informational banner.
- `rc=$?` → Capture the exit code immediately, before any other command overwrites `$?`.
- `[ "$rc" -eq 0 ] && echo OK || echo FAIL` → Assert success as a verdict; `0` means the key and passphrase were correct.

**New words in this step:**

- **exit code (`$?`)** — the numeric success/failure status of the last command; `0` = success.
- **capturing `$?`** — saving the code into a variable right away, since the next command resets it.

---

### Step 2 of 2 — Prove byte-identity with `sha256sum` and `diff`

**In plain English:** We fingerprint the original and recovered files and assert the hashes match, backed by a clean `diff` — objective proof decryption lost nothing.

```bash
cd "$LAB_ROOT"
orig=$(sha256sum secret.txt    | awk '{print $1}')
rec=$( sha256sum recovered.txt | awk '{print $1}')
echo "orig: $orig"
echo "rec:  $rec"
[ "$orig" = "$rec" ] && echo "HASH MATCH (OK)" || echo "HASH MISMATCH (FAIL)"
diff secret.txt recovered.txt && echo "DIFF CLEAN (OK)"
```

**Expected output:**

```
orig: 9f3a1c2b...e7
rec:  9f3a1c2b...e7
HASH MATCH (OK)
DIFF CLEAN (OK)
```

**Line-by-line breakdown:**

- `orig=$(sha256sum secret.txt | awk '{print $1}')` → Fingerprint the original and keep only the hash (field 1), dropping the filename.
- `rec=$(sha256sum recovered.txt | awk '{print $1}')` → Fingerprint the recovered file the same way.
- `[ "$orig" = "$rec" ] && echo OK || echo FAIL` → Assert the two hashes are identical — the strongest "byte-for-byte equal" proof.
- `diff secret.txt recovered.txt && echo "DIFF CLEAN (OK)"` → A clean diff (no output, exit `0`) confirms the same result a second way.

**New words in this step:**

- **fidelity** — whether the recovered plaintext exactly matches the original, proven by a matching hash and clean diff.
- **hash comparison** — comparing two `sha256sum` values to prove identity without reading the contents.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| capture `$?` after decrypt | turns success into a verdict | the next command overwrites `$?` — capture immediately |
| `sha256sum` match | proves byte-for-byte recovery | `cat` can miss a trailing-newline a hash catches |
| clean `diff` | second proof of identity | exit `1` means "differ," not a tool error |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `HASH MISMATCH (FAIL)` | Wrong key/passphrase or corrupt ciphertext | Re-run SETUP; confirm the right `GNUPGHOME` |
| `No secret key` | Private key not in this keyring | Re-generate in SETUP or import the secret key |

---

## TASK 2 of 2 — Prove failures are detectable

**In plain English:** We confirm the symmetric file also recovers cleanly, then deliberately use a wrong passphrase to prove the decrypt exits non-zero — so automation can catch a bad secret.

---

### Step 1 of 2 — Decrypt the symmetric file and confirm the match

**In plain English:** We open the passphrase-only file with no key involved and assert the recovered text matches the original.

```bash
cd "$LAB_ROOT"
gpg --batch --yes --pinentry-mode loopback --passphrase 'LabPass210!' \
    -o recovered.sym.txt -d secret.sym.gpg 2>/dev/null
echo "symmetric decrypt exit: $?"
diff secret.txt recovered.sym.txt && echo "SYMMETRIC MATCH (OK)" || echo "SYMMETRIC MISMATCH (FAIL)"
```

**Expected output:**

```
symmetric decrypt exit: 0
SYMMETRIC MATCH (OK)
```

**Line-by-line breakdown:**

- `gpg ... -d secret.sym.gpg` → Decrypt the symmetric file using only the shared passphrase; no private key is consulted.
- `echo "symmetric decrypt exit: $?"` → Show the exit code (`0` = success) right after the command.
- `diff secret.txt recovered.sym.txt && echo OK || echo FAIL` → Assert the symmetric recovery is byte-identical to the original.

**New words in this step:**

- **symmetric recovery** — recovering plaintext with only the shared passphrase, no keypair involved.

---

### Step 2 of 2 — Assert a wrong passphrase fails loudly

**In plain English:** We run the decrypt again with a deliberately wrong passphrase and assert the exit code is non-zero — proving a bad secret is caught instead of silently producing garbage.

```bash
cd "$LAB_ROOT"
set +e
gpg --batch --yes --pinentry-mode loopback --passphrase 'WRONG-pass' \
    -o /tmp/lab-210/should_not_trust.txt -d secret.sym.gpg 2>/dev/null
bad_rc=$?
set -e
echo "wrong-pass exit code: $bad_rc"
[ "$bad_rc" -ne 0 ] && echo "BAD PASSPHRASE REJECTED (OK)" || echo "BAD PASSPHRASE ACCEPTED (FAIL)"
```

**Expected output:**

```
wrong-pass exit code: 2
BAD PASSPHRASE REJECTED (OK)
```

**Line-by-line breakdown:**

- `set +e` → Temporarily allow a non-zero exit to continue, since we *expect* this command to fail and want to capture its code rather than abort.
- `gpg ... --passphrase 'WRONG-pass' ... -d secret.sym.gpg` → Attempt the decrypt with the wrong passphrase; GnuPG cannot derive the session key and exits non-zero.
- `bad_rc=$?` then `set -e` → Capture the failure code, then restore strict error handling.
- `[ "$bad_rc" -ne 0 ] && echo OK || echo FAIL` → Assert the code is non-zero — the verdict that a bad passphrase is detectable, which is the whole point.

**New words in this step:**

- **`set +e` / `set -e`** — toggle whether a non-zero exit aborts the script; relax it around an expected failure, then restore it.
- **fail-loud** — designing a check so a wrong input produces a clear non-zero exit rather than a silent bad result.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| symmetric `-d` | recovers with the passphrase only | no key needed — a missing key is irrelevant |
| `set +e` around a failure | lets you capture the bad exit code | forgetting `set -e` after leaves the shell lax |
| `$? != 0` on wrong pass | proves failure is detectable | gpg may leave a stub file — trust `$?`, not the file |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Wrong-pass decrypt exits `0` | You reused the correct passphrase | Use a clearly wrong value to test rejection |
| Script aborts before the check | `set -e` still active on the failing line | Wrap the expected failure in `set +e` / `set -e` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Decrypt and check the exit code
- [ ] Task 1 · Step 2 — Prove byte-identity with `sha256sum` and `diff`
- [ ] Task 2 · Step 1 — Decrypt the symmetric file and confirm the match
- [ ] Task 2 · Step 2 — Assert a wrong passphrase fails loudly

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. The keyring, ciphertext, and recovered files all live under `$LAB_ROOT`, so one wipe is enough — this lab changed **no** system state.

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
| Trusting the output file over `$?` | A wrong passphrase leaves a stub unnoticed | Capture and assert the exit code |
| Comparing with `cat` instead of a hash | A trailing-newline difference slips by | Use `sha256sum` for byte-exact proof |
| Letting `set -e` abort the failure test | Script dies before the assertion runs | Wrap it in `set +e` / `set -e` |

---

## 📌 Exam Strategy

Verification proves a decrypt both succeeded and is trustworthy. After recovering plaintext, confirm exit `0`, then prove byte-identity with `sha256sum`/`diff`. For robustness, prove the negative too: a wrong passphrase must exit non-zero. These are the same checks a grader script runs against your work.

- Capture `$?` immediately after every decrypt and assert on it.
- Use a matching `sha256sum` (and clean `diff`) as the fidelity proof.
- Test the wrong-passphrase path under `set +e` so failure is provably detectable.

---

## 🔗 Related Labs

- [Lab 210a — Decrypt a GPG File (RHCSA)](../lab-210a-gpg-decrypt-file-rhcsa/) — the creator-seat lab this audits
- [Lab 210b — Decrypt a GPG File (Ansible)](../lab-210b-gpg-decrypt-file-ansible/) — the playbook whose recovery you verify the same way
- [Lab 211a — Share and Verify Public Keys (RHCSA)](../lab-211a-gpg-share-verify-public-keys-rhcsa/) — the next step: trust the keys that make asymmetric decrypt possible

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
