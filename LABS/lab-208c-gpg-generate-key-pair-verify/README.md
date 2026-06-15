# Lab 208c: Generate a GPG Key Pair (Verify) — `gpg --list-keys`, `--with-colons`, `grep`/`awk`

**Series:** linux-ops-mastery — GPG Encryption · **Lab 208c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving key material is present and correct), SRE (post-provision verification), DevOps (key-presence gates in CI pipelines)  
**Prerequisite:** [Lab 208a](../lab-208a-gpg-generate-key-pair-rhcsa/) and [Lab 208b](../lab-208b-gpg-generate-key-pair-ansible/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Objective

Take the auditor's seat: instead of *generating* a key, you *prove* one exists and is well-formed using hard evidence. You will assert that both the public and secret halves are present, that the user ID matches what you asked for, that the fingerprint is exactly 40 hexadecimal characters, and that the key carries a real expiry date — turning "I think I made a key" into objective, scriptable pass/fail checks built from `gpg --with-colons`, `grep -c`, `awk -F:`, and a bash regex test.

---

## 🧠 Concept

Verification replaces memory with proof. A GPG key pair is "good" only if four facts hold: the **public** key is in the keyring (`pub`), you hold the **secret** half (`sec`), the **fingerprint** is a 40-hex hash, and the key has an **expiry** so it cannot live forever. The human `--list-keys` output is fine to eyeball, but a grader script reads the stable `--with-colons` format: each line is a typed record (`pub`, `sec`, `fpr`, `uid`) with fixed colon-separated fields. Field 10 of an `fpr` record is the fingerprint; field 7 of a `pub` record is the expiry timestamp. Asserting on those fields — not on the pretty output — is how you build checks that never break across gpg versions.

```
gpg --list-keys              → human view (eyeball)
gpg --list-secret-keys       → proves you hold the PRIVATE half
gpg --with-colons:
   pub:...:<expiry-epoch>:...   ← field 7 = expiry (empty = never)
   fpr:::::::::<40-hex>:        ← field 10 = fingerprint
```

> **Why this matters:** "The key generated fine" is worth zero points if you cannot prove it. A presence check, a 40-hex fingerprint assertion, and an expiry check are the same evidence a grader script (or your future automation) uses to gate the next step — encrypting to a key that does not exist fails loudly here, not in production.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `gpg --list-keys` | List public keys; exit code signals presence | non-zero exit when the user ID is not found |
| `gpg --list-secret-keys` | Prove you hold the private half, not just a public copy | `sec`/`ssb` lines confirm secret material |
| `gpg --with-colons` | Stable machine-readable records for scripting | field positions are guaranteed across versions |
| `grep -c` | Count matching lines (presence as a number) | `-c` prints the count; `0` means absent |
| `awk -F:` | Split colon records and print a chosen field | `'/^fpr/ {print $10}'` extracts the fingerprint |
| `[[ "$x" =~ ^[A-F0-9]{40}$ ]]` | Assert a string is exactly 40 hex chars | a bash regex test — the fingerprint sanity check |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox, point GnuPG at a keyring inside it, and generate the same key 208a/208b make so there is something real to audit — all under `/tmp` so one teardown wipes it.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-208
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"

export GNUPGHOME="$LAB_ROOT/gnupg"
mkdir -p "$GNUPGHOME"
chmod 700 "$GNUPGHOME"

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

gpg --batch --gen-key "$LAB_ROOT/keyparams" 2>/dev/null
gpg --list-keys lab208@example.com >/dev/null && echo "key ready (OK)"
echo "exit was: $?"
```

**Expected output:**

```
key ready (OK)
exit was: 0
```

---

## TASK 1 of 2 — Assert both halves of the pair exist

**In plain English:** We prove the public key is present and the user ID matches, then prove we actually hold the secret half — the two checks that confirm a *pair*, not just a stray public key.

---

### Step 1 of 2 — Assert the public key is present and the UID matches

**In plain English:** We look up the key by email and turn "is it there?" into a counted, pass/fail assertion instead of trusting our eyes.

```bash
cd "$LAB_ROOT"
gpg --list-keys lab208@example.com >/dev/null 2>&1 && echo "PUBLIC KEY PRESENT (OK)" || echo "PUBLIC KEY MISSING (FAIL)"
uid_count=$(gpg --list-keys --with-colons lab208@example.com | grep -c '^uid')
echo "uid records: $uid_count"
gpg --list-keys --with-colons lab208@example.com | grep '^uid' | awk -F: '{print $10}'
```

**Expected output:**

```
PUBLIC KEY PRESENT (OK)
uid records: 1
Lab 208 User <lab208@example.com>
```

**Line-by-line breakdown:**

- `gpg --list-keys lab208@example.com >/dev/null 2>&1 && echo ... || echo ...` → Look up the key silently; a `0` exit fires the OK branch, a non-zero fires FAIL — presence as a verdict, not a guess.
- `uid_count=$(... | grep -c '^uid')` → Count the `uid` records in machine output; `1` confirms exactly one identity is attached.
- `... | grep '^uid' | awk -F: '{print $10}'` → Print field 10 of the `uid` record, the human-readable user ID, to confirm it matches what we generated.

**New words in this step:**

- **assertion** — a check that prints a clear pass/fail (OK/FAIL) so verification is objective, not impressionistic.
- **`uid` record** — the `--with-colons` line whose field 10 holds the key's `Name-Real <email>` identity.

---

### Step 2 of 2 — Prove you hold the secret (private) half

**In plain English:** A public key alone is not a pair — we confirm the matching secret key is in the keyring, which is what lets you ever decrypt or sign.

```bash
cd "$LAB_ROOT"
gpg --list-secret-keys lab208@example.com >/dev/null 2>&1 && echo "SECRET KEY PRESENT (OK)" || echo "SECRET KEY MISSING (FAIL)"
sec_count=$(gpg --list-secret-keys --with-colons lab208@example.com | grep -c '^sec')
echo "sec records: $sec_count"
```

**Expected output:**

```
SECRET KEY PRESENT (OK)
sec records: 1
```

**Line-by-line breakdown:**

- `gpg --list-secret-keys ... && echo OK || echo FAIL` → Assert the private half exists; without it you have only a public copy and could never decrypt or sign.
- `sec_count=$(... | grep -c '^sec')` → Count `sec` (secret primary) records; `1` confirms you hold the private key, completing the proof of a real pair.

**New words in this step:**

- **secret key (`sec`)** — the private half of the pair; its presence is what distinguishes "I own this key" from "I imported someone's public key."

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `--list-keys` exit code | non-zero when the UID is absent | trust the exit code, not just on-screen text |
| `grep -c '^uid'` | counts identities on the key | `0` means the key (or UID) is missing |
| `--list-secret-keys` | proves the private half is present | a public-only key cannot decrypt or sign |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `PUBLIC KEY MISSING (FAIL)` | Wrong `GNUPGHOME` or key never generated | Re-export `GNUPGHOME`; re-run SETUP |
| `SECRET KEY MISSING` but public present | Imported a public key without the private half | Generate locally, or import with `--import-secret-keys` |

---

## TASK 2 of 2 — Assert the fingerprint and expiry are well-formed

**In plain English:** We extract the fingerprint and prove it is exactly 40 hex characters, then prove the key carries a real expiry date rather than living forever.

---

### Step 1 of 2 — Extract and validate the 40-hex fingerprint

**In plain English:** We pull the fingerprint from machine output and run a regex test that passes only if it is precisely 40 uppercase hex digits — the shape every valid fingerprint must have.

```bash
cd "$LAB_ROOT"
fpr=$(gpg --list-keys --with-colons lab208@example.com | awk -F: '/^fpr/ {print $10; exit}')
echo "fingerprint: $fpr"
echo "length: ${#fpr}"
[[ "$fpr" =~ ^[A-F0-9]{40}$ ]] && echo "FINGERPRINT VALID (OK)" || echo "FINGERPRINT MALFORMED (FAIL)"
```

**Expected output:**

```
fingerprint: AABBCCDDEEFF00112233445566778899DEADBEEF
length: 40
FINGERPRINT VALID (OK)
```

**Line-by-line breakdown:**

- `fpr=$(... | awk -F: '/^fpr/ {print $10; exit}')` → Capture the first `fpr` record's field 10 (the primary key fingerprint) into a variable; `exit` stops at the first match so subkey fingerprints are ignored.
- `echo "length: ${#fpr}"` → Print the string length; `${#var}` is bash's length operator, and a valid fingerprint is exactly `40`.
- `[[ "$fpr" =~ ^[A-F0-9]{40}$ ]] && echo OK || echo FAIL` → A regex assertion: pass only if the value is exactly 40 uppercase-hex characters — catching truncation or stray whitespace.

**New words in this step:**

- **`${#var}`** — bash syntax for the character length of a variable's value.
- **regex anchors `^`/`$`** — force the pattern to match the *entire* string, so "40 hex somewhere inside" cannot pass by accident.

---

### Step 2 of 2 — Prove the key has a real expiry date

**In plain English:** A key with no expiry is a security smell; we read the expiry field from machine output and assert it is set, not empty.

```bash
cd "$LAB_ROOT"
expiry=$(gpg --list-keys --with-colons lab208@example.com | awk -F: '/^pub/ {print $7; exit}')
echo "expiry epoch: $expiry"
if [ -n "$expiry" ] && [ "$expiry" -gt 0 ] 2>/dev/null; then
  echo "EXPIRY SET (OK) — $(date -d "@$expiry" +%F)"
else
  echo "NO EXPIRY (FAIL) — key never expires"
fi
```

**Expected output:**

```
expiry epoch: 1750000000
EXPIRY SET (OK) — 2027-06-15
```

**Line-by-line breakdown:**

- `expiry=$(... | awk -F: '/^pub/ {print $7; exit}')` → Read field 7 of the `pub` record, the expiry as a Unix epoch timestamp; an empty value means "never expires."
- `if [ -n "$expiry" ] && [ "$expiry" -gt 0 ] ...` → Assert the field is non-empty and a positive number — both must hold for a real expiry.
- `date -d "@$expiry" +%F` → Convert the epoch to a human `YYYY-MM-DD` date so the OK message shows the actual expiry day.

**New words in this step:**

- **epoch timestamp** — seconds since 1970-01-01 UTC; GnuPG stores expiry this way in colon output.
- **key expiry** — a built-in end date after which the key is no longer valid, limiting the damage of a lost key.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `fpr` field 10 | the 40-hex fingerprint | parsing the human listing breaks across gpg versions |
| `^[A-F0-9]{40}$` regex | validates fingerprint shape | a lowercase or 8/16-hex value is not the full fingerprint |
| `pub` field 7 | expiry epoch (empty = never) | "no expiry" passes naive checks but fails the policy |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `length: 0` / fingerprint empty | Grabbed a non-`fpr` line or wrong key | Filter `/^fpr/` and capture field 10 |
| `NO EXPIRY (FAIL)` | `Expire-Date: 0` was used at generation | Regenerate with a real `Expire-Date` (e.g. `1y`) |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Assert the public key is present and the UID matches
- [ ] Task 1 · Step 2 — Prove you hold the secret (private) half
- [ ] Task 2 · Step 1 — Extract and validate the 40-hex fingerprint
- [ ] Task 2 · Step 2 — Prove the key has a real expiry date

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. The keyring lives under `$GNUPGHOME` inside `$LAB_ROOT`, so this one command removes the generated key too — this lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-208
```

**Expected output:**

```
✅ Removed /tmp/lab-208 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Eyeballing `--list-keys` instead of asserting | A missing secret key slips through | Assert exit codes and counts, not appearances |
| Validating the fingerprint without anchors | A partial/garbage value passes | Use `^...{40}$` so the whole string must match |
| Accepting a key with no expiry | "Forever" keys pass naive checks | Read `pub` field 7 and require a positive epoch |

---

## 📌 Exam Strategy

Verification is what turns "I generated a key" into "I can prove it." After any key task, assert presence of both halves, validate the fingerprint's shape, and confirm an expiry — using `--with-colons` so your checks are stable. Build the habit of gating the next step (encryption) on these proofs so a missing key fails here, cheaply, instead of mid-task.

- Use exit codes (`&& echo OK || echo FAIL`) for presence — never trust the screen alone.
- Parse `--with-colons` fields (`fpr` → 10, `pub` expiry → 7), not the human listing.
- Anchor regex checks with `^`/`$` so "close enough" can never pass.

---

## 🔗 Related Labs

- [Lab 208a — Generate a GPG Key Pair (RHCSA)](../lab-208a-gpg-generate-key-pair-rhcsa/) — the creator-seat lab this audits
- [Lab 208b — Generate a GPG Key Pair (Ansible)](../lab-208b-gpg-generate-key-pair-ansible/) — the playbook whose key you verify the same way
- [Lab 209c — Encrypt a File with GPG (Verify)](../lab-209c-gpg-encrypt-file-verify/) — the next audit: prove the ciphertext this key produces is real

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
