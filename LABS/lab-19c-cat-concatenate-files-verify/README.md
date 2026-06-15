# Lab 19c: Concatenating Files with cat (Verify) — `wc -l`, `sha256sum`, `cat -A`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 19c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving a concatenation is ordered and clean), SRE (config-assembly validation), DevOps (artifact integrity)  
**Prerequisite:** [Lab 19a](../lab-19a-cat-concatenate-files-rhcsa/) and [Lab 19b](../lab-19b-cat-concatenate-files-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `cat -A` | _Task 2 · Step 1_ |
| A2 | `sha256sum` | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `head` / `tail` line checks | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `sha256sum` reassembly proof | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `grep -P '\r'` CRLF detection | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `file` line-ending report | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Take the auditor's seat: prove a concatenated file is correctly ordered and free of hidden corruption. You will check the first and last lines came from the right fragments, prove the combined file equals a fresh concatenation by hash, then hunt for CRLF and other invisible characters that would break a parser. Order plus a matching hash plus clean line endings equals a trustworthy assembled file.

---

## 🧠 Concept

Concatenation verification has two questions. **Order/content**: `head -1`/`tail -1` confirm the boundaries came from the right fragments, and a `sha256sum` of the combined file versus a fresh `cat parts/*` proves nothing was reordered or dropped. **Cleanliness**: assembled files often inherit a stray CRLF or trailing whitespace from one fragment; `grep -P '\r'` finds carriage returns and `cat -A` shows tabs/EOLs, while `file` reports "with CRLF line terminators" when Windows endings sneak in.

```
head -1 combined.txt → header line   (first fragment)
tail -1 combined.txt → footer line   (last fragment)
sha256sum combined == sha256sum <(cat parts/*) → identical
grep -Pc '\r' combined.txt → 0       (no CRLF)
```

> **Why this matters:** A drop-in config assembled out of order, or carrying one CRLF fragment, fails in ways that are maddening to debug. Hash + order + line-ending checks catch all three before deploy.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `head -1` / `tail -1` | First / last line | boundary fragment check |
| `sha256sum` | Content fingerprint | combined vs fresh concat |
| `grep -P '\r'` | Detect carriage returns | `-c` counts, `-P` Perl regex |
| `cat -A` | Show non-printing chars | `^M$` = CRLF |
| `file` | Report line-ending type | flags "CRLF line terminators" |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Rebuild the fragments and a combined file so there is a real assembly to audit.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-19
mkdir -p "$LAB_ROOT/parts"
cd "$LAB_ROOT"
printf 'header line\n' > parts/01-header.txt
printf 'body line\n'   > parts/02-body.txt
printf 'footer line\n' > parts/03-footer.txt
cat parts/*.txt > combined.txt
cat combined.txt
echo "exit was: $?"
```

**Expected output:**

```
header line
body line
footer line
exit was: 0
```

---

## TASK 1 of 2 — Prove order and content

**In plain English:** We check the boundary lines and prove the combined file matches a fresh concatenation.

---

### Step 1 of 2 — Check the first and last lines

**In plain English:** We confirm the assembly starts with the header fragment and ends with the footer fragment.

```bash
cd "$LAB_ROOT"
head -1 combined.txt
tail -1 combined.txt
[ "$(head -1 combined.txt)" = "header line" ] && [ "$(tail -1 combined.txt)" = "footer line" ] && echo "ORDER OK" || echo "ORDER WRONG (FAIL)"
```

**Expected output:**

```
header line
footer line
ORDER OK
```

**Line-by-line breakdown:**

- `head -1` / `tail -1` → Show the first and last lines — the boundaries of the concatenation.
- the combined `[ ... ] && [ ... ]` test → Assert both boundaries came from the expected fragments.

**New words in this step:**

- **boundary check** — verifying the first/last lines came from the correct fragments.

---

### Step 2 of 2 — Prove equality with `sha256sum`

**In plain English:** We hash the combined file and a fresh concatenation and prove they are identical.

```bash
cd "$LAB_ROOT"
A=$(sha256sum combined.txt | awk '{print $1}')
B=$(cat parts/*.txt | sha256sum | awk '{print $1}')
echo "$A"; echo "$B"
[ "$A" = "$B" ] && echo "CONCAT MATCHES (OK)" || echo "MISMATCH (FAIL)"
```

**Expected output:**

```
2f1d...  (64 hex)
2f1d...  (same hash)
CONCAT MATCHES (OK)
```

**Line-by-line breakdown:**

- `A=$(sha256sum combined.txt ...)` → Fingerprint the saved combined file.
- `B=$(cat parts/*.txt | sha256sum ...)` → Fingerprint a fresh concatenation in the same order.
- `[ "$A" = "$B" ]` → Equal hashes prove the assembly is byte-identical to a fresh `cat`.

**New words in this step:**

- **reassembly proof** — confirming a saved combination equals a freshly built one.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `head`/`tail -1` | boundary fragments | empty file gives empty output |
| `sha256sum` | content/order proof | order changes flip the hash |
| fresh concat | reference | glob order must match |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `ORDER WRONG` | Fragments unsorted | Zero-pad fragment names |
| Hash mismatch | Reordered/dropped fragment | Re-assemble in sorted order |

---

## TASK 2 of 2 — Prove the file is clean

**In plain English:** We hunt for CRLF and confirm the line-ending type.

---

### Step 1 of 2 — Detect carriage returns with `grep -P`

**In plain English:** We count any CRLF in the combined file; zero is clean.

```bash
cd "$LAB_ROOT"
CR=$(grep -Pc '\r' combined.txt || true)
echo "CR lines: $CR"
[ "$CR" -eq 0 ] && echo "NO CRLF (OK)" || echo "CRLF FOUND (FAIL)"
cat -A combined.txt | tail -1
```

**Expected output:**

```
CR lines: 0
NO CRLF (OK)
footer line$
```

**Line-by-line breakdown:**

- `CR=$(grep -Pc '\r' combined.txt || true)` → Count lines containing a carriage return; `-P` enables `\r`, `|| true` keeps the script alive when the count is zero (grep rc 1).
- `[ "$CR" -eq 0 ]` → Zero CRLF means Unix-clean.
- `cat -A combined.txt | tail -1` → Show the last line's endings; `$` with no `^M` confirms LF-only.

**New words in this step:**

- **CRLF** — the Windows two-byte line ending (`\r\n`) that breaks many Linux parsers.

---

### Step 2 of 2 — Confirm line-ending type with `file`

**In plain English:** We ask `file` to report the line-ending style of the combined file.

```bash
cd "$LAB_ROOT"
file combined.txt
file combined.txt | grep -q 'CRLF' && echo "HAS CRLF (FAIL)" || echo "UNIX ENDINGS (OK)"
echo "exit was: $?"
```

**Expected output:**

```
combined.txt: ASCII text
UNIX ENDINGS (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `file combined.txt` → Classify the file; it appends "with CRLF line terminators" if Windows endings are present.
- `... | grep -q 'CRLF'` → Invert the logic: finding CRLF is a failure, absence is the OK branch.

**New words in this step:**

- **`file` line-ending report** — `file` notes "CRLF line terminators" when a text file has Windows endings.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `grep -P '\r'` | finds CRLF | needs `-P` (PCRE) for `\r` |
| `cat -A` | shows `^M$` | quick visual CRLF check |
| `file` | reports endings | only flags when CRLF present |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `CRLF FOUND` | A fragment had Windows endings | `dos2unix` or `sed 's/\r$//'` |
| `grep -P` error | Non-PCRE grep | Use GNU grep with `-P` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Check the first and last lines
- [ ] Task 1 · Step 2 — Prove equality with `sha256sum`
- [ ] Task 2 · Step 1 — Detect carriage returns with `grep -P`
- [ ] Task 2 · Step 2 — Confirm line-ending type with `file`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-19
```

**Expected output:**

```
✅ Removed /tmp/lab-19 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Checking content but not order | Reordered assembly slips by | Hash against a fresh concat |
| Ignoring CRLF | Parser fails mysteriously | Detect with `grep -P '\r'`/`file` |
| `grep '\r'` without `-P` | No matches found | Use `-P` for escape sequences |

---

## 📌 Exam Strategy

Certify an assembled file by order (boundary lines), content (hash vs fresh concat), and cleanliness (no CRLF). These checks catch the three ways concatenations go wrong: misordered, incomplete, or whitespace-polluted.

- Hash against a fresh `cat parts/*` to prove order and completeness.
- `file` instantly flags CRLF contamination.
- `cat -A` is the quick visual whitespace audit.

---

## 🔗 Related Labs

- [Lab 19a — Concatenating Files (RHCSA)](../lab-19a-cat-concatenate-files-rhcsa/) — the `cat` this audits
- [Lab 19b — Concatenating Files (Ansible)](../lab-19b-cat-concatenate-files-ansible/) — the `assemble` output you verify
- [Lab 23c — Comparing File Differences (Verify)](../lab-23c-diff-comparing-files-verify/) — deeper content comparison with `diff`

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
