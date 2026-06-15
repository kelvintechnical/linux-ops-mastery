# Lab 211a: Share and Verify Public Keys (RHCSA) — `gpg --export -a`, `gpg --import`, `gpg --verify`

**Series:** linux-ops-mastery — GPG Encryption · **Lab 211a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (key distribution and signature verification), Security+/SRE (trust establishment, signed artifacts), DevOps (GPG-backed release signing workflows)  
**Prerequisite:** [Lab 208a](../lab-208a-gpg-generate-key-pair-rhcsa/) and [Lab 210a](../lab-210a-gpg-decrypt-file-rhcsa/) completed — you need to understand key generation and decryption before sharing keys  
**Time Estimate:** 30–40 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Learn to move a **public** key from one party to another safely, verify you imported the right key by matching **fingerprints** out-of-band, and prove a file's integrity with a **detached signature** — the three skills that turn GPG from a solo tool into a trust system. Along the way you will export armored public keys with `gpg --export -a`, transfer them with `scp`, import with `gpg --import`, read `gpg --fingerprint`, understand why you must never ship `gpg --export-secret-keys`, and verify with `gpg --verify` after a deliberate tamper test.

---

## 🧠 Concept

GPG trust is a chain of verifiable facts. Party A holds a keypair; Party B needs only A's **public** key to encrypt to A or verify A's signatures. The safe handoff is: export the public half (`gpg --export -a`), transfer it (`scp`), import it (`gpg --import`), then confirm the **fingerprint** on both sides matches what you verified out-of-band (phone, printed card, signed email). The **secret** key (`gpg --export-secret-keys`) must never leave A's machine — exporting it is the catastrophic mistake. Once B trusts A's public key, A can **sign** a file (`--detach-sign`) and B can **verify** (`gpg --verify`) that the file was signed by A and has not been altered.

```
Party A (GNUPGHOME_A)                    Party B (GNUPGHOME_B)
─────────────────────                    ─────────────────────
gpg --export -a alice@lab211.local       gpg --import pubkey.asc
     │                                        │
     ▼                                        ▼
pubkey.asc  ─── scp / cp ──────────────▶  gpg --fingerprint alice@lab211.local
                                               (must match A's fingerprint)

A: gpg --detach-sign message.txt           B: gpg --verify message.txt.sig message.txt
   → message.txt.sig                          → "Good signature" (or BAD after tamper)
```

> **Why this matters:** Encrypting to the wrong public key (a swapped or MITM key) is as bad as sending plaintext to the attacker. Fingerprint verification is the one step that prevents that, and detached signatures are how you prove a file was not altered in transit.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `gpg --export -a` | Export a public key in ASCII armor (safe to share) | `-a`/`--armor` makes it mailable; never export the secret half |
| `scp` | Transfer the armored key file to another host/path | `user@host:path` for remote; localhost works for practice |
| `gpg --import` | Load a public (or secret) key into a keyring | importing a public key does not grant signing/decrypt power |
| `gpg --fingerprint` | Show the 40-hex fingerprint for out-of-band verification | the only collision-resistant way to confirm you got the right key |
| `gpg --export-secret-keys` | Export the **private** key (dangerous) | almost never share this — understand it to know what NOT to do |
| `gpg --detach-sign` / `gpg --verify` | Sign a file separately / verify signature + data | `--detach-sign` produces a `.sig` sidecar; `--verify` checks both |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** We build one sandbox folder with **two** keyrings inside it — `gnupg-a` for Party A and `gnupg-b` for Party B — generate a key in A's ring, and write a short message file to sign later; both rings live under `/tmp` so one teardown wipes everything.

> Run this block **once** before Task 1. It defines a single sandbox root (`LAB_ROOT`) that every file in this lab lives under, so Teardown can wipe it in one safe command.

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

GNUPGHOME="$GNUPGHOME_A" gpg --batch --gen-key "$LAB_ROOT/keyparams-a"
echo "release artifact v1.0 — checksum: deadbeef" > "$LAB_ROOT/message.txt"

GNUPGHOME="$GNUPGHOME_A" gpg --list-keys alice@lab211.local
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
gpg: Generating Party A key for Lab 211
gpg: key A1B2C3D4E5F6 marked as ultimately trusted
gpg: done
pub   rsa3072 2026-06-15 [SCEA] [expires: 2027-06-15]
      AABBCCDDEEFF00112233445566778899DEADBEEF
uid           [ultimate] Lab 211 Alice <alice@lab211.local>
sub   rsa3072 2026-06-15 [E] [expires: 2027-06-15]
Setup complete at 2026-06-15T17:45:02-04:00
exit was: 0
```

---

## TASK 1 of 2 — Export, transfer, and import a public key

**In plain English:** We export Alice's public key from Party A's ring, transfer the armored file, import it into Party B's ring, and prove both sides see the same fingerprint — the out-of-band trust check.

---

### Step 1 of 2 — Export the armored public key and read A's fingerprint

**In plain English:** We pull Alice's public key out as printable ASCII armor and record her fingerprint — the value Party B must confirm before trusting the import.

```bash
cd "$LAB_ROOT"
GNUPGHOME="$GNUPGHOME_A" gpg --export -a alice@lab211.local > pubkey.asc
head -n 2 pubkey.asc
GNUPGHOME="$GNUPGHOME_A" gpg --fingerprint alice@lab211.local | grep -A1 '^pub'
echo "exit was: $?"
```

**Expected output:**

```
-----BEGIN PGP PUBLIC KEY BLOCK-----
pub   rsa3072 2026-06-15 [SCEA] [expires: 2027-06-15]
      AABB CCDD EEFF 0011 2233  4455 6677 8899 DEAD BEEF
exit was: 0
```

**Line-by-line breakdown:**

- `GNUPGHOME="$GNUPGHOME_A" gpg --export -a alice@lab211.local > pubkey.asc` → Export only the **public** half in ASCII armor (`-a`); this file is safe to email or `scp`. Contrast with `gpg --export-secret-keys`, which would leak the private key and must never be sent.
- `head -n 2 pubkey.asc` → Show the armor banner (`-----BEGIN PGP PUBLIC KEY BLOCK-----`) proving the export is armored text.
- `GNUPGHOME="$GNUPGHOME_A" gpg --fingerprint ...` → Print the 40-hex fingerprint Party A would read over the phone so Party B can confirm they imported the same key.

**New words in this step:**

- **public key export** — writing only the shareable half of a keypair to a file; safe to distribute.
- **`--export-secret-keys`** — exports the private key; understand it so you know never to use it for sharing.

---

### Step 2 of 2 — Transfer with `scp`, import into B's ring, match fingerprints

**In plain English:** We move the armored key to a destination path (simulating a remote handoff with `scp` to localhost), import it into Party B's keyring, and assert B's fingerprint matches A's.

```bash
cd "$LAB_ROOT"
# scp to localhost exercises the real remote form: scp file user@host:path
scp pubkey.asc localhost:"$LAB_ROOT/pubkey-received.asc" 2>/dev/null \
  || cp pubkey.asc pubkey-received.asc

GNUPGHOME="$GNUPGHOME_B" gpg --import pubkey-received.asc
fpr_a=$(GNUPGHOME="$GNUPGHOME_A" gpg --list-keys --with-colons alice@lab211.local | awk -F: '/^fpr/ {print $10; exit}')
fpr_b=$(GNUPGHOME="$GNUPGHOME_B" gpg --list-keys --with-colons alice@lab211.local | awk -F: '/^fpr/ {print $10; exit}')
echo "A fingerprint: $fpr_a"
echo "B fingerprint: $fpr_b"
[ "$fpr_a" = "$fpr_b" ] && echo "FINGERPRINT MATCH (OK)" || echo "FINGERPRINT MISMATCH (FAIL)"
```

**Expected output:**

```
gpg: key DEADBEEF marked as ultimately trusted
gpg: Total number processed: 1
A fingerprint: AABBCCDDEEFF00112233445566778899DEADBEEF
B fingerprint: AABBCCDDEEFF00112233445566778899DEADBEEF
FINGERPRINT MATCH (OK)
```

**Line-by-line breakdown:**

- `scp pubkey.asc localhost:"$LAB_ROOT/pubkey-received.asc"` → Transfer the armored key; `localhost:` uses the same `scp user@host:path` form you would use for a remote bastion. The `|| cp` fallback copies locally if `scp` to localhost is unavailable — same file, same lesson.
- `GNUPGHOME="$GNUPGHOME_B" gpg --import pubkey-received.asc` → Load the public key into Party B's ring; B can now encrypt to Alice or verify her signatures, but cannot decrypt as Alice.
- `fpr_a` / `fpr_b` extraction → Pull the 40-hex fingerprint from each ring's `--with-colons` output and compare; a match proves B imported exactly the key A exported.

**New words in this step:**

- **`gpg --import`** — adds a key from an exported file into the current `GNUPGHOME` keyring.
- **out-of-band verification** — confirming a fingerprint through a separate channel (phone, in person) so a MITM cannot swap the key unnoticed.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `gpg --export -a` | shares only the public half, armored | exporting the secret key is a catastrophic leak |
| `gpg --import` | loads a key into a keyring | importing a public key does not let you sign as that user |
| fingerprint match | proves the right key was imported | short key IDs are collision-prone — use the full fingerprint |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `FINGERPRINT MISMATCH` | Wrong file imported or corrupted transfer | Re-export from A; re-transfer and re-import |
| `scp` fails on localhost | SSH to localhost not configured | Use the `cp` fallback (same lesson, local handoff) |

---

## TASK 2 of 2 — Sign a file and verify the signature

**In plain English:** Alice signs the message with her private key, Party B verifies the detached signature with the imported public key, then we tamper the message and watch verification fail.

---

### Step 1 of 2 — Create a detached signature with `--detach-sign`

**In plain English:** We sign the message file from Party A's ring, producing a separate `.sig` sidecar that proves who signed and when, without embedding the signature inside the message.

```bash
cd "$LAB_ROOT"
GNUPGHOME="$GNUPGHOME_A" gpg --batch --pinentry-mode loopback --passphrase 'labpass211' \
    --detach-sign -o message.txt.sig message.txt
ls -l message.txt message.txt.sig
file message.txt.sig
```

**Expected output:**

```
-rw-r--r--. 1 root root  42 Jun 15 17:46 message.txt
-rw-r--r--. 1 root root 833 Jun 15 17:46 message.txt.sig
message.txt.sig: PGP signature
```

**Line-by-line breakdown:**

- `gpg --detach-sign -o message.txt.sig message.txt` → Sign `message.txt` and write the signature to a **separate** file (`message.txt.sig`); the original stays readable. Contrast with `--sign` (inline) or `--clearsign` (text-embedded).
- `--batch --pinentry-mode loopback --passphrase 'labpass211'` → Unlock Alice's private key non-interactively so the sign does not hang on a prompt.
- `file message.txt.sig` → Confirms the sidecar is a "PGP signature" blob, not plaintext.

**New words in this step:**

- **detached signature** — a `.sig` file that proves authenticity of a separate data file; both must be kept together for verification.
- **`--clearsign`** — an alternative that embeds a readable signature inside a text file (not used here, but know the variant exists).

---

### Step 2 of 2 — Verify with `gpg --verify`, then fail after tampering

**In plain English:** Party B verifies the signature against the message using the imported public key, then we alter one byte of the message and prove verification now fails with a non-zero exit.

```bash
cd "$LAB_ROOT"
GNUPGHOME="$GNUPGHOME_B" gpg --verify message.txt.sig message.txt
echo "good-sig exit: $?"
echo "TAMPERED" >> message.txt
GNUPGHOME="$GNUPGHOME_B" gpg --verify message.txt.sig message.txt
echo "bad-sig exit: $?"
```

**Expected output:**

```
gpg: Signature made Mon Jun 15 17:46:00 2026 EDT
gpg:                using RSA key AABBCCDDEEFF00112233445566778899DEADBEEF
gpg: Good signature from "Lab 211 Alice <alice@lab211.local>"
good-sig exit: 0
gpg: BAD signature from "Lab 211 Alice <alice@lab211.local>"
bad-sig exit: 1
```

**Line-by-line breakdown:**

- `GNUPGHOME="$GNUPGHOME_B" gpg --verify message.txt.sig message.txt` → Check the detached signature against the data file using B's keyring (which holds Alice's public key); "Good signature" and exit `0` mean intact and authentic.
- `echo "good-sig exit: $?"` → Capture the success code (`0`).
- `echo "TAMPERED" >> message.txt` → Alter the data after signing; the signature no longer matches the bytes.
- second `gpg --verify ...` → Now reports "BAD signature" and exits non-zero (`1`) — proof that verification catches tampering.

**New words in this step:**

- **`gpg --verify`** — checks a signature (detached or inline) against a data file and reports Good/BAD.
- **tamper detection** — any change to the signed data after signing breaks verification.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `--detach-sign` | produces a `.sig` sidecar | you must pass **both** `.sig` and data file to `--verify` |
| `gpg --verify` | proves integrity + signer identity | needs the signer's public key imported first |
| tamper → BAD signature | any post-sign change fails verify | exit `1` on BAD is expected, not a tool error |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `Can't check signature: No public key` | Alice's key not imported into B's ring | Re-run Task 1 import into `GNUPGHOME_B` |
| `BAD signature` on the first verify | Message changed before verify | Re-sign from the original `message.txt` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Export the armored public key and read A's fingerprint
- [ ] Task 1 · Step 2 — Transfer with `scp`, import into B's ring, match fingerprints
- [ ] Task 2 · Step 1 — Create a detached signature with `--detach-sign`
- [ ] Task 2 · Step 2 — Verify with `gpg --verify`, then fail after tampering

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. Both keyrings (`gnupg-a` and `gnupg-b`) live inside `$LAB_ROOT`, so one wipe removes every key and file — this lab changed **no** system state.

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
| Exporting `--export-secret-keys` | Private key leaks to the transfer file | Export with `--export -a` (public only) |
| Trusting a key without fingerprint check | MITM swaps the public key unnoticed | Compare full 40-hex fingerprints out-of-band |
| Verifying without importing first | `No public key` error | Import the signer's public key into the verifying ring |

---

## 📌 Exam Strategy

Key sharing is a three-step ritual: export the **public** key armored, transfer it, import it, then confirm the **fingerprint** matches out-of-band. Signing is `--detach-sign` + passphrase; verification is `gpg --verify` with both the `.sig` and the data file present. Never export secret keys; always test verification after a deliberate tamper so you know BAD signatures fail loudly.

- Say "export `-a` = public armor, import, fingerprint match" before you hand off a key.
- Detached sign produces a `.sig` sidecar — verification needs both files.
- A BAD signature exits non-zero; that is success for your tamper test, not an error.

---

## 🔗 Related Labs

- [Lab 211b — Share and Verify Public Keys (Ansible)](../lab-211b-gpg-share-verify-public-keys-ansible/) — the same export/import/sign/verify in playbooks
- [Lab 211c — Share and Verify Public Keys (Verify)](../lab-211c-gpg-share-verify-public-keys-verify/) — hard assertions on fingerprints and signatures
- [Lab 208a — Generate a GPG Key Pair (RHCSA)](../lab-208a-gpg-generate-key-pair-rhcsa/) — create the keypair you export here
- [Lab 210a — Decrypt a GPG File (RHCSA)](../lab-210a-gpg-decrypt-file-rhcsa/) — decryption requires the private half you never export

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
