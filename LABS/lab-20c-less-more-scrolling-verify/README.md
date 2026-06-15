# Lab 20c: Scrolling Large Files (Verify) — `sed -n`, `awk NR`, `wc -l`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 20c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving you read the right lines), SRE (deterministic log slicing), DevOps (range extraction validation)  
**Prerequisite:** [Lab 20a](../lab-20a-less-more-scrolling-rhcsa/) and [Lab 20b](../lab-20b-less-more-scrolling-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `sed -n 'A,Bp'` | _Task 1 · Step 1_ |
| A2 | `grep -n` | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `awk 'NR==N'` line addressing | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | range line-count proof | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `grep -c` match count | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `grep -n | cut` line number | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Prove a range extraction or search returned exactly the right lines. You will pull a single line by number two ways (`sed -n` and `awk NR`) and confirm they agree, verify a range has the expected line count, count matches with `grep -c`, and extract the precise line number of a hit. This is how you certify a "scroll to line N" or "find pattern" operation in a script.

---

## 🧠 Concept

Verifying a read is about determinism: the same line number must yield the same content every time, and a search must return a known count at a known position. `sed -n 'Np'` and `awk 'NR==N'` both print line N; if they match, your addressing is correct. `sed -n 'A,Bp' | wc -l` proves a range has exactly B−A+1 lines. For searches, `grep -c` counts matches and `grep -n pat | cut -d: -f1` extracts the line number, which you can compare against the expected location.

```
sed -n '751p' f  == awk 'NR==751' f   → line addressing agrees
sed -n '748,752p' f | wc -l → 5        → range size correct
grep -c ERROR f → 1                    → exactly one match
grep -n ERROR f | cut -d: -f1 → 751    → match is on line 751
```

> **Why this matters:** When a playbook or script makes decisions off "line 751" or "the ERROR line," you must prove the address and the match are stable. Two independent tools agreeing is the cheap, reliable proof.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `sed -n 'Np'` | Print one line | `'A,Bp'` for a range |
| `awk 'NR==N'` | Print line N | independent of `sed` |
| `wc -l` | Count lines | proves range size |
| `grep -c` | Count matches | not line count of file |
| `grep -n | cut -d: -f1` | Line number of match | colon-delimited |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Rebuild the large log with a known ERROR position to audit.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-20
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"
seq 1 1000 | sed 's/^/line /' > big.log
sed -i '750a ERROR disk full' big.log
wc -l big.log
echo "exit was: $?"
```

**Expected output:**

```
1001 big.log
exit was: 0
```

---

## TASK 1 of 2 — Prove line addressing and range size

**In plain English:** We confirm two tools read the same line, then prove a range has the right count.

---

### Step 1 of 2 — Two tools, one line

**In plain English:** We read line 751 with `sed` and with `awk` and confirm they match.

```bash
cd "$LAB_ROOT"
S=$(sed -n '751p' big.log)
A=$(awk 'NR==751' big.log)
echo "sed:  $S"
echo "awk:  $A"
[ "$S" = "$A" ] && echo "ADDRESSING OK" || echo "MISMATCH (FAIL)"
```

**Expected output:**

```
sed:  ERROR disk full
awk:  ERROR disk full
ADDRESSING OK
```

**Line-by-line breakdown:**

- `S=$(sed -n '751p' ...)` → Read line 751 with `sed`.
- `A=$(awk 'NR==751' ...)` → Read the same line with `awk` (`NR` is the record/line number).
- `[ "$S" = "$A" ]` → Two independent tools agreeing proves the address is correct.

**New words in this step:**

- **`awk 'NR==N'`** — print the Nth line; `NR` is awk's line counter.

---

### Step 2 of 2 — Prove the range size

**In plain English:** We extract lines 748–752 and confirm the slice is exactly 5 lines.

```bash
cd "$LAB_ROOT"
N=$(sed -n '748,752p' big.log | wc -l)
echo "range lines: $N"
[ "$N" -eq 5 ] && echo "RANGE SIZE OK" || echo "WRONG SIZE (FAIL)"
```

**Expected output:**

```
range lines: 5
RANGE SIZE OK
```

**Line-by-line breakdown:**

- `sed -n '748,752p' | wc -l` → Count the lines in the extracted range.
- `[ "$N" -eq 5 ]` → 748..752 inclusive is exactly 5 lines (B−A+1).

**New words in this step:**

- **range size** — `B − A + 1` lines for an inclusive `A,B` extraction.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `sed` vs `awk` line | cross-check address | both 1-indexed |
| range count | `B-A+1` | off-by-one if exclusive assumed |
| `wc -l` | counts newlines | missing final newline undercounts |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Addressing mismatch | File changed between reads | Re-extract from same file |
| Range size off by one | Inclusive vs exclusive confusion | `A,B` is inclusive |

---

## TASK 2 of 2 — Prove the search

**In plain English:** We count matches and extract the matching line number.

---

### Step 1 of 2 — Count matches with `grep -c`

**In plain English:** We confirm there is exactly one ERROR line.

```bash
cd "$LAB_ROOT"
C=$(grep -c ERROR big.log)
echo "matches: $C"
[ "$C" -eq 1 ] && echo "COUNT OK" || echo "WRONG COUNT (FAIL)"
```

**Expected output:**

```
matches: 1
COUNT OK
```

**Line-by-line breakdown:**

- `grep -c ERROR big.log` → Count matching lines (not occurrences) — here, exactly one.
- `[ "$C" -eq 1 ]` → Assert the expected match count.

**New words in this step:**

- **`grep -c`** — count matching lines, not total file lines.

---

### Step 2 of 2 — Extract the matching line number

**In plain English:** We pull the line number of the ERROR and confirm it is where we expect.

```bash
cd "$LAB_ROOT"
LN=$(grep -n ERROR big.log | cut -d: -f1)
echo "ERROR on line: $LN"
[ "$LN" -eq 751 ] && echo "POSITION OK" || echo "WRONG POSITION (FAIL)"
```

**Expected output:**

```
ERROR on line: 751
POSITION OK
```

**Line-by-line breakdown:**

- `grep -n ERROR ...` → Output is `751:ERROR disk full`.
- `cut -d: -f1` → Take the first colon-delimited field — the line number.
- `[ "$LN" -eq 751 ]` → Confirm the match is at the expected position.

**New words in this step:**

- **`grep -n | cut`** — extract the line number from a numbered match.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `grep -c` | match-line count | not occurrence count |
| `grep -n` | prefixes `line:` | `cut -d:` to split |
| position check | assert line number | shifts if file edited |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Wrong position | File length changed | Re-derive expected line |
| `cut` gives content | Wrong delimiter/field | Use `-d: -f1` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Two tools, one line
- [ ] Task 1 · Step 2 — Prove the range size
- [ ] Task 2 · Step 1 — Count matches with `grep -c`
- [ ] Task 2 · Step 2 — Extract the matching line number
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-20
```

**Expected output:**

```
✅ Removed /tmp/lab-20 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Trusting one tool | Hidden addressing bug | Cross-check `sed` vs `awk` |
| Confusing `-c` with line count | Wrong assertion | `-c` counts matches |
| Off-by-one ranges | Wrong size | `A,B` inclusive = `B-A+1` |

---

## 📌 Exam Strategy

Verify reads deterministically: cross-check a line with two tools, prove range sizes with `wc -l`, and confirm searches with `grep -c` and the extracted line number. Determinism is what makes a scripted read trustworthy.

- `sed -n 'Np'` and `awk 'NR==N'` agreeing proves the address.
- `grep -c` for count, `grep -n | cut` for position.
- Inclusive ranges: `A,B` is `B-A+1` lines.

---

## 🔗 Related Labs

- [Lab 20a — Scrolling Large Files (RHCSA)](../lab-20a-less-more-scrolling-rhcsa/) — the `less` navigation this audits
- [Lab 20b — Scrolling Large Files (Ansible)](../lab-20b-less-more-scrolling-ansible/) — the range/search plays you verify
- [Lab 21c — Monitoring Live Log Files (Verify)](../lab-21c-tail-f-live-logs-verify/) — verifying tail captures

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
