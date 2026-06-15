# Lab 16c: Search for a String and Save Output (Verify) — `grep -c`, `diff`, `wc -l`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 16c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving saved search results are correct), SRE (alert-rule validation), DevOps (log-gate verification)  
**Prerequisite:** [Lab 16a](../lab-16a-grep-search-save-output-rhcsa/) and [Lab 16b](../lab-16b-grep-search-save-output-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `grep -c` | _Task 1 · Step 1_ |
| A2 | `wc -l` | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `diff` expected vs saved | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N2 | `grep -q` assertion | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N3 | `grep -v` (invert) | Task 2 · Step 2 | _Task 2 · Step 2_ |
| N4 | `[ N -eq N ]` count test | Task 1 · Step 1 | _Task 1 · Step 1_ |

---

## 🎯 Objective

Take the auditor's seat: prove a saved search result is exactly right. You will assert the match count equals the expected number, diff the saved file against a known-good reference, confirm a required setting is present with `grep -q`, and prove a forbidden pattern is absent with `grep -v`. Counts and a clean diff are the objective verdict.

---

## 🧠 Concept

Verifying a search is about counts and contents. `grep -c` and `wc -l` reduce "did we capture the right lines?" to a number you compare with `[ -eq ]`. `diff` proves the saved file matches a reference byte-for-byte. For policy checks, `grep -q PATTERN` asserts a required line *is* present (exit 0), while `grep -v PATTERN | grep -q .` (or a `! grep -q`) proves a forbidden line is *absent*. Together they certify both completeness and correctness.

```
grep -c ERROR app.log → 2     == expected 2     (count matches)
diff expected.txt saved.txt → (empty)           (contents match)
grep -q "PermitRootLogin no" cfg → exit 0        (required present)
! grep -q "PermitRootLogin yes" cfg → forbidden absent
```

> **Why this matters:** A captured report that is missing a line, or a config that still allows what it should forbid, fails silently. Count + diff + presence/absence checks catch all three.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `grep -c` | Count matching lines | compare with expected |
| `wc -l` | Count lines in a file | `< file` for the bare number |
| `diff` | Compare saved vs expected | empty = identical |
| `grep -q` | Quiet pass/fail | exit 0 found, 1 not |
| `grep -v` | Invert match | find lines that do NOT match |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Rebuild the log, the saved results, and a hardened config so there is real output to audit.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-16
mkdir -p "$LAB_ROOT/conf"
cd "$LAB_ROOT"
printf 'INFO start\nERROR disk full\ninfo retry\nERROR timeout\n' > app.log
grep -in error app.log > errors.txt
printf 'PermitRootLogin no\nPort 22\n' > conf/sshd_config
cat errors.txt
echo "exit was: $?"
```

**Expected output:**

```
2:ERROR disk full
4:ERROR timeout
exit was: 0
```

---

## TASK 1 of 2 — Prove the count and contents

**In plain English:** We assert the number of captured matches and diff the saved file against an expected copy.

---

### Step 1 of 2 — Assert the match count

**In plain English:** We count the saved matches and compare to the expected number.

```bash
cd "$LAB_ROOT"
COUNT=$(wc -l < errors.txt)
EXPECTED=2
echo "saved lines: $COUNT (expected $EXPECTED)"
[ "$COUNT" -eq "$EXPECTED" ] && echo "COUNT OK" || echo "COUNT WRONG (FAIL)"
```

**Expected output:**

```
saved lines: 2 (expected 2)
COUNT OK
```

**Line-by-line breakdown:**

- `COUNT=$(wc -l < errors.txt)` → Count the saved match lines as a bare number.
- `[ "$COUNT" -eq "$EXPECTED" ]` → Integer-compare to the expected count for a pass/fail.

**New words in this step:**

- **count assertion** — proving a search captured exactly the expected number of lines.

---

### Step 2 of 2 — Diff against an expected reference

**In plain English:** We build the known-good expected output and prove the saved file matches it exactly.

```bash
cd "$LAB_ROOT"
printf '2:ERROR disk full\n4:ERROR timeout\n' > expected.txt
diff -u expected.txt errors.txt && echo "CONTENT MATCH (OK)" || echo "CONTENT DIFFERS (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
CONTENT MATCH (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `printf ... > expected.txt` → Write the reference output the search should have produced.
- `diff -u expected.txt errors.txt` → Compare; no output (exit 0) fires the OK branch, proving exact match.

**New words in this step:**

- **reference comparison** — diffing actual output against a known-good expected file.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `wc -l`/`grep -c` | count verdict | `wc -l` needs `< file` for bare number |
| `diff` | content verdict | exit 1 = differ, not an error |
| `[ -eq ]` | numeric compare | use `-eq`, not `=` |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `COUNT WRONG` | Search flags differed | Re-run the exact `grep` from 16a |
| `CONTENT DIFFERS` | Line numbers/order changed | Match the exact `grep -n` output |

---

## TASK 2 of 2 — Prove presence and absence

**In plain English:** We assert a required setting is present and a forbidden one is absent.

---

### Step 1 of 2 — Assert a required line with `grep -q`

**In plain English:** We prove the hardened setting exists in the config.

```bash
cd "$LAB_ROOT"
grep -q '^PermitRootLogin no$' conf/sshd_config && echo "REQUIRED PRESENT (OK)" || echo "MISSING (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
REQUIRED PRESENT (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `grep -q '^PermitRootLogin no$' ...` → `-q` is a silent pass/fail; exit 0 means the exact required line is present.
- `&& echo OK || echo FAIL` → Convert the exit code into a verdict.

**New words in this step:**

- **`grep -q`** — quiet mode: no output, just an exit code for assertions.

---

### Step 2 of 2 — Prove a forbidden line is absent with `grep -v`

**In plain English:** We confirm the config contains no insecure `PermitRootLogin yes`.

```bash
cd "$LAB_ROOT"
! grep -q '^PermitRootLogin yes' conf/sshd_config && echo "FORBIDDEN ABSENT (OK)" || echo "INSECURE PRESENT (FAIL)"
grep -v '^#' conf/sshd_config | grep -c .
echo "exit was: $?"
```

**Expected output:**

```
FORBIDDEN ABSENT (OK)
2
exit was: 0
```

**Line-by-line breakdown:**

- `! grep -q '^PermitRootLogin yes' ...` → The `!` inverts the exit code, so "not found" becomes success — proving the insecure line is absent.
- `grep -v '^#' ... | grep -c .` → `-v` drops comment lines; counting the rest shows how many active settings remain.

**New words in this step:**

- **`grep -v`** — print (or here, filter to) lines that do NOT match the pattern.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `grep -q` | presence verdict | anchor the pattern for exactness |
| `! grep -q` | absence verdict | the `!` flips found/not-found |
| `grep -v '^#'` | drop comments | counts only active config |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `MISSING (FAIL)` | Pattern too strict | Loosen/anchor the regex correctly |
| Absence check false-passes | Forgot the `!` | Invert with `!` for absence |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Assert the match count
- [ ] Task 1 · Step 2 — Diff against an expected reference
- [ ] Task 2 · Step 1 — Assert a required line with `grep -q`
- [ ] Task 2 · Step 2 — Prove a forbidden line is absent with `grep -v`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-16
```

**Expected output:**

```
✅ Removed /tmp/lab-16 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Checking presence only | A forbidden line slips by | Also run an absence check |
| Unanchored patterns | False positives | Use `^`/`$` anchors |
| Treating `diff` rc 1 as error | Aborts a working script | rc 1 means "differ" |

---

## 📌 Exam Strategy

Verify searches by count and content, and configs by presence and absence. `wc -l`/`grep -c` give counts, `diff` proves contents, `grep -q`/`! grep -q` certify required/forbidden lines. Anchor your patterns so the verdict is exact.

- Count first, then diff — cheap to expensive.
- Use `! grep -q` to prove a forbidden setting is gone.
- Anchored regexes prevent false matches.

---

## 🔗 Related Labs

- [Lab 16a — Search and Save Output (RHCSA)](../lab-16a-grep-search-save-output-rhcsa/) — the searches this audits
- [Lab 16b — Search and Save Output (Ansible)](../lab-16b-grep-search-save-output-ansible/) — the playbook output you verify
- [Lab 22c — Filtering Text with grep and Regex (Verify)](../lab-22c-grep-regex-verify/) — deeper regex verification

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
