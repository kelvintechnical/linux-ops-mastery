# Lab 211c: Share and Verify Public Keys (Verify) — `gpg --fingerprint`, `gpg --verify`, tamper test

**Series:** linux-ops-mastery — GPG Encryption · **Lab 211c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving key trust and signature validity), Security+/SRE (release-signing verification gates), DevOps (GPG trust checks in CI)  
**Prerequisite:** [Lab 211a](../lab-211a-gpg-share-verify-public-keys-rhcsa/) and [Lab 211b](../lab-211b-gpg-share-verify-public-keys-ansible/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Objective

Take the auditor's seat on the full GPG trust chain: prove the exported file is armored public key material (not a secret-key leak), prove Party B imported the same key as Party A (matching fingerprints), prove a detached signature verifies cleanly, and prove tampering is caught with a non-zero exit. These are the objective pass/fail checks that gate a signed release or encrypted handoff.

---

## 🧠 Concept

Trust verification has four gates. **Gate 1 — safe export:** `pubkey.asc` must start with `-----BEGIN PGP PUBLIC KEY BLOCK-----` and must NOT contain `PRIVATE KEY`. **Gate 2 — correct import:** fingerprints extracted from `--with-colons` on both rings must be identical 40-hex strings. **Gate 3 — good signature:** `gpg --verify` exits `0` and prints "Good signature". **Gate 4 — tamper rejection:** after altering the signed data, verify exits non-zero and prints "BAD signature". Each gate is a scriptable OK/FAIL assertion, not an impression.

```
pubkey.asc     → grep BEGIN PGP PUBLIC KEY BLOCK (OK)
               → grep PRIVATE KEY (must be FAIL/absent)
fpr_a == fpr_b → FINGERPRINT MATCH (OK)
gpg --verify   → exit 0 + "Good signature" (OK)
tamper + verify → exit != 0 + "BAD signature" (OK for the test)
```

> **Why this matters:** Shipping a release without these checks is how teams sign with the wrong key, verify against a swapped import, or miss a tampered artifact. These four gates are the minimum bar before you trust a GPG-protected handoff.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `head` / `grep` | Assert armor banner present / secret key absent | `grep -q` for silent pass/fail |
| `gpg --list-keys --with-colons` | Machine-readable records for fingerprint extraction | field 10 of `fpr` = fingerprint |
| `gpg --fingerprint` | Human-readable fingerprint for comparison | 40 hex groups = same value as field 10 |
| `gpg --verify SIG DATA` | Verify detached signature against data file | exit `0` = Good, non-zero = BAD |
| `set +e` / `set -e` | Capture expected failure exit codes | wrap the tamper test so the script continues |
| `$?` | Read verify success/failure | the verdict, not the output file's existence |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the two-party sandbox (A and B keyrings), generate Alice's key, export/import the public key, sign the message, and leave everything in place for the audit steps.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-211
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"

export GNUPGHOME_A="$LAB_ROOT/gnupg-a"
export GNUPGHOME_B="$LAB_ROOT/gnupg-b"
mkdir -p "$GNUPGHOME_A" "$GNUPGHOME_B"
chmod 700 "$GNUPGHOME_A" "$GNUPGHOME_B"

cat > "$LAB_ROOT/keyparams-a" <<'EOF'
%echo Generating Party A key for Lab 211
Key-Type: RSA
Key-Length: 3072
Subkey-Type: RSA
Subkey-Length: 3072
Name-Real: Lab 211 Alice
Name-Email: alice@lab211.local
Expire-Date: 1y
Passphrase: labpass211
%commit
%echo done
EOF

GNUPGHOME="$GNUPGHOME_A" gpg --batch --gen-key "$LAB_ROOT/keyparams-a" 2>/dev/null
echo "release artifact v1.0 — checksum: deadbeef" > message.txt
GNUPGHOME="$GNUPGHOME_A" gpg --export -a alice@lab211.local > pubkey.asc
cp pubkey.asc pubkey-received.asc
GNUPGHOME="$GNUPGHOME_B" gpg --import pubkey-received.asc 2>/dev/null
GNUPGHOME="$GNUPGHOME_A" gpg --batch --pinentry-mode loopback --passphrase 'labpass211' \
    --detach-sign -o message.txt.sig message.txt 2>/dev/null

ls -1 "$LAB_ROOT"
echo "exit was: $?"
```

**Expected output:**

```
gnupg-a
gnupg-b
keyparams-a
message.txt
message.txt.sig
pubkey-received.asc
pubkey.asc
exit was: 0
```

---

## TASK 1 of 2 — Assert safe export and matching fingerprints

**In plain English:** We prove the exported file is a public-key armored block (not a secret-key leak) and that both keyrings hold the same 40-hex fingerprint.

---

### Step 1 of 2 — Assert the export is public armor, not a secret key

**In plain English:** We check the armored export carries the public-key banner and does not contain the forbidden private-key banner.

```bash
cd "$LAB_ROOT"
head -n 1 pubkey.asc
head -n 1 pubkey.asc | grep -q 'BEGIN PGP PUBLIC KEY BLOCK' && echo "PUBLIC ARMOR (OK)" || echo "NOT PUBLIC ARMOR (FAIL)"
grep -qi 'PRIVATE KEY' pubkey.asc && echo "SECRET LEAK (FAIL)" || echo "NO SECRET KEY (OK)"
```

**Expected output:**

```
-----BEGIN PGP PUBLIC KEY BLOCK-----
PUBLIC ARMOR (OK)
NO SECRET KEY (OK)
```

**Line-by-line breakdown:**

- `head -n 1 pubkey.asc` → Show the first line; a correct public export opens with `-----BEGIN PGP PUBLIC KEY BLOCK-----`.
- `grep -q 'BEGIN PGP PUBLIC KEY BLOCK' && echo OK || echo FAIL` → Assert the public armor banner is present.
- `grep -qi 'PRIVATE KEY' pubkey.asc && echo FAIL || echo OK` → Assert the catastrophic `PRIVATE KEY` banner is **absent** — a secret-key export would contain it.

**New words in this step:**

- **public armor banner** — `-----BEGIN PGP PUBLIC KEY BLOCK-----`; proves the export is the shareable half.
- **secret-key leak check** — grepping for `PRIVATE KEY` to catch the export mistake you must never make.

---

### Step 2 of 2 — Assert fingerprints match between A and B

**In plain English:** We extract the 40-hex fingerprint from each keyring and assert they are identical — proof B imported exactly what A exported.

```bash
cd "$LAB_ROOT"
fpr_a=$(GNUPGHOME="$GNUPGHOME_A" gpg --list-keys --with-colons alice@lab211.local | awk -F: '/^fpr/ {print $10; exit}')
fpr_b=$(GNUPGHOME="$GNUPGHOME_B" gpg --list-keys --with-colons alice@lab211.local | awk -F: '/^fpr/ {print $10; exit}')
echo "A: $fpr_a"
echo "B: $fpr_b"
[ "$fpr_a" = "$fpr_b" ] && echo "FINGERPRINT MATCH (OK)" || echo "FINGERPRINT MISMATCH (FAIL)"
[[ "$fpr_a" =~ ^[A-F0-9]{40}$ ]] && echo "FINGERPRINT SHAPE (OK)" || echo "FINGERPRINT SHAPE (FAIL)"
```

**Expected output:**

```
A: AABBCCDDEEFF00112233445566778899DEADBEEF
B: AABBCCDDEEFF00112233445566778899DEADBEEF
FINGERPRINT MATCH (OK)
FINGERPRINT SHAPE (OK)
```

**Line-by-line breakdown:**

- `fpr_a` / `fpr_b` extraction → Pull field 10 from the first `fpr` record in each ring's `--with-colons` output.
- `[ "$fpr_a" = "$fpr_b" ] && echo OK || echo FAIL` → Assert the values are identical — the import trust check.
- `[[ "$fpr_a" =~ ^[A-F0-9]{40}$ ]]` → Assert the fingerprint is exactly 40 uppercase hex characters.

**New words in this step:**

- **fingerprint match** — the proof that Party B holds the same public key Party A exported.
- **shape validation** — a regex check that the fingerprint is well-formed, not truncated garbage.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| PUBLIC KEY BLOCK banner | marks a safe public export | a SECRET KEY banner means catastrophic leak |
| fingerprint equality | proves correct import | short key IDs are not enough |
| `^[A-F0-9]{40}$` | validates fingerprint shape | lowercase or partial values must fail |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `SECRET LEAK (FAIL)` | Used `--export-secret-keys` by mistake | Re-export with `--export -a` (public only) |
| `FINGERPRINT MISMATCH` | Wrong file imported | Re-export from A and re-import into B |

---

## TASK 2 of 2 — Assert Good signature, then catch tampering

**In plain English:** We verify the detached signature passes on intact data, then tamper the message and prove verification fails with a non-zero exit.

---

### Step 1 of 2 — Verify the Good signature

**In plain English:** Party B verifies the `.sig` against the untouched message and we assert exit `0` plus the "Good signature" text.

```bash
cd "$LAB_ROOT"
cp message.txt message-intact.txt
GNUPGHOME="$GNUPGHOME_B" gpg --verify message.txt.sig message-intact.txt 2>&1 | tee /tmp/lab-211/verify-good.txt
echo "good-verify exit: $?"
grep -q 'Good signature' /tmp/lab-211/verify-good.txt && echo "GOOD SIG TEXT (OK)" || echo "GOOD SIG TEXT (FAIL)"
```

**Expected output:**

```
gpg: Good signature from "Lab 211 Alice <alice@lab211.local>"
good-verify exit: 0
GOOD SIG TEXT (OK)
```

**Line-by-line breakdown:**

- `cp message.txt message-intact.txt` → Work on a copy so the tamper step in Step 2 does not destroy the intact original.
- `GNUPGHOME="$GNUPGHOME_B" gpg --verify message.txt.sig message-intact.txt` → Verify using B's ring (which holds Alice's imported public key).
- `echo "good-verify exit: $?"` → Assert exit `0`.
- `grep -q 'Good signature' ... && echo OK` → Assert the success text is present in gpg's output.

**New words in this step:**

- **Good signature** — gpg's confirmation that the `.sig` matches the data and a trusted public key.

---

### Step 2 of 2 — Tamper the message and assert BAD signature

**In plain English:** We alter the signed data and prove verification now exits non-zero and prints "BAD signature" — the tamper-detection gate.

```bash
cd "$LAB_ROOT"
echo "TAMPERED" >> message-intact.txt
set +e
GNUPGHOME="$GNUPGHOME_B" gpg --verify message.txt.sig message-intact.txt 2>&1 | tee /tmp/lab-211/verify-bad.txt
bad_rc=$?
set -e
echo "bad-verify exit: $bad_rc"
grep -q 'BAD signature' /tmp/lab-211/verify-bad.txt && echo "BAD SIG TEXT (OK)" || echo "BAD SIG TEXT (FAIL)"
[ "$bad_rc" -ne 0 ] && echo "NON-ZERO EXIT (OK)" || echo "NON-ZERO EXIT (FAIL)"
```

**Expected output:**

```
gpg: BAD signature from "Lab 211 Alice <alice@lab211.local>"
bad-verify exit: 1
BAD SIG TEXT (OK)
NON-ZERO EXIT (OK)
```

**Line-by-line breakdown:**

- `echo "TAMPERED" >> message-intact.txt` → Alter the data after signing; the signature no longer matches.
- `set +e` → Allow the expected failure to continue so we can capture `$?`.
- `gpg --verify ...` → Now reports "BAD signature" and exits non-zero.
- `grep -q 'BAD signature' ... && echo OK` → Assert the failure text is present.
- `[ "$bad_rc" -ne 0 ] && echo OK` → Assert the exit code is non-zero — automation's failure hook.

**New words in this step:**

- **tamper test** — deliberately corrupting signed data to prove verification catches the change.
- **fail-loud** — a non-zero exit plus "BAD signature" text, not a silent false pass.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `gpg --verify` on intact data | exit 0 + Good signature | needs both `.sig` and data file |
| post-sign tamper | BAD signature + non-zero exit | exit 1 here is success for the tamper test |
| `set +e` around failure | captures bad exit without aborting | restore `set -e` after capturing `$?` |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `No public key` on verify | Alice's key not in B's ring | Re-run SETUP import into `GNUPGHOME_B` |
| Good verify fails on intact copy | Message changed before Step 1 | Re-sign from a fresh `message.txt` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Assert the export is public armor, not a secret key
- [ ] Task 1 · Step 2 — Assert fingerprints match between A and B
- [ ] Task 2 · Step 1 — Verify the Good signature
- [ ] Task 2 · Step 2 — Tamper the message and assert BAD signature

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. Both keyrings and all artifacts live under `$LAB_ROOT` — this lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-211
```

**Expected output:**

```
✅ Removed /tmp/lab-211 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Skipping the PRIVATE KEY grep | A secret export passes unnoticed | Always grep for `PRIVATE KEY` and require absence |
| Trusting verify without checking exit code | BAD signature ignored | Assert `$?` and the Good/BAD text |
| Tampering the only copy of the message | Cannot re-run the Good verify | Keep an intact copy before tampering |

---

## 📌 Exam Strategy

Before trusting a GPG handoff, run all four gates: public armor (no secret banner), fingerprint match, Good signature on intact data, BAD signature after tamper. These are the same checks a grader script or release pipeline uses. Build the habit of asserting exit codes and output text, not just "the command ran."

- Gate 1: `BEGIN PGP PUBLIC KEY BLOCK` present, `PRIVATE KEY` absent.
- Gate 2: 40-hex fingerprints equal on both rings.
- Gate 3: verify exit `0` + "Good signature".
- Gate 4: tamper → exit non-zero + "BAD signature".

---

## 🔗 Related Labs

- [Lab 211a — Share and Verify Public Keys (RHCSA)](../lab-211a-gpg-share-verify-public-keys-rhcsa/) — the creator-seat lab this audits
- [Lab 211b — Share and Verify Public Keys (Ansible)](../lab-211b-gpg-share-verify-public-keys-ansible/) — the playbook whose trust chain you verify the same way
- [Lab 208c — Generate a GPG Key Pair (Verify)](../lab-208c-gpg-generate-key-pair-verify/) — the key-presence audit that precedes sharing

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
