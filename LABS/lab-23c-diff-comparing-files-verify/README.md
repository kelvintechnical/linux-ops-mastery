# Lab 23c: Comparing File Differences (Verify) — `diff -q`, `cmp`, `$?`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 23c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving identity and drift), SRE (config-drift gating), DevOps (release comparison)  
**Prerequisite:** [Lab 23a](../lab-23a-diff-comparing-files-rhcsa/) and [Lab 23b](../lab-23b-diff-comparing-files-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `diff -q` + `$?` | _Task 1 · Step 1_ |
| A2 | `diff -r` | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `cmp` byte comparison | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N2 | `cmp -s` silent test | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `diff -rq` tree summary | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | counting changed files | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Prove sameness and pinpoint drift programmatically. You will gate on `diff -q`'s exit code, do a byte-exact comparison with `cmp`/`cmp -s`, summarize directory drift with `diff -rq`, and count exactly how many files changed between two trees. These are the checks behind "is this deployment identical to the baseline?"

---

## 🧠 Concept

`diff` is line-oriented; `cmp` is byte-oriented. For text equality, `diff -q a b` (exit 0 same / 1 differ) is enough, and `cmp -s a b` does the same silently at the byte level — better for binaries and for catching a trailing-newline difference `diff` might gloss over. For trees, `diff -rq d1 d2` prints one line per differing file plus "Only in" entries, which you can `grep -c` to *count* the drift. The pattern: exit codes for gating, `-q`/`-s` for quiet checks, counts for thresholds.

```
diff -q a b; echo $?         → 0 same, 1 differ
cmp -s a b && echo identical → byte-exact silent test
diff -rq d1 d2               → one line per differing/only-in file
diff -rq d1 d2 | wc -l       → number of drift entries
```

> **Why this matters:** Release gates and compliance checks need a yes/no on "identical?" and a number for "how much drifted?" `diff`/`cmp` exit codes and counts give both, scriptably.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `diff -q` | Brief, line-based | exit 0/1 |
| `cmp` | Byte comparison | reports first diff offset |
| `cmp -s` | Silent byte test | exit code only |
| `diff -rq` | Recursive summary | one line per file |
| `wc -l` | Count drift entries | threshold checks |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Rebuild file versions and trees with known differences to audit.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-23
mkdir -p "$LAB_ROOT/d1" "$LAB_ROOT/d2"
cd "$LAB_ROOT"
printf 'alpha\nbeta\n' > a.txt
printf 'alpha\nbeta\n' > a_copy.txt
printf 'alpha\nBETA\n' > b.txt
printf 'x\n' > d1/same.txt;   printf 'x\n' > d2/same.txt
printf 'p\n' > d1/diff.txt;   printf 'q\n' > d2/diff.txt
printf 'only\n' > d1/only.txt
ls d1 d2
echo "exit was: $?"
```

**Expected output:**

```
d1:
diff.txt
only.txt
same.txt

d2:
diff.txt
same.txt
exit was: 0
```

---

## TASK 1 of 2 — Prove identity

**In plain English:** We prove two identical files match and a changed file differs, by line and by byte.

---

### Step 1 of 2 — Gate on `diff -q`

**In plain English:** We confirm the copy is identical and the edited file differs, using exit codes.

```bash
cd "$LAB_ROOT"
diff -q a.txt a_copy.txt && echo "COPY IDENTICAL (OK)" || echo "COPY DIFFERS (FAIL)"
diff -q a.txt b.txt && echo "UNEXPECTED MATCH (FAIL)" || echo "EDIT DIFFERS (OK)"
```

**Expected output:**

```
COPY IDENTICAL (OK)
Files a.txt and b.txt differ
EDIT DIFFERS (OK)
```

**Line-by-line breakdown:**

- `diff -q a.txt a_copy.txt && ...` → Exit 0 (identical) triggers the OK branch.
- `diff -q a.txt b.txt && ... || ...` → Exit 1 (differ) triggers the `||` branch, which is the expected result here.

**New words in this step:**

- **exit-code gating** — branching on `diff`'s 0/1 result rather than parsing output.

---

### Step 2 of 2 — Byte-exact check with `cmp`

**In plain English:** We compare the same files at the byte level, silently.

```bash
cd "$LAB_ROOT"
cmp -s a.txt a_copy.txt && echo "BYTES IDENTICAL (OK)" || echo "BYTES DIFFER (FAIL)"
cmp a.txt b.txt || true
```

**Expected output:**

```
BYTES IDENTICAL (OK)
a.txt b.txt differ: byte 7, line 2
```

**Line-by-line breakdown:**

- `cmp -s a.txt a_copy.txt` → `-s` is silent; the exit code says identical (0) or not.
- `cmp a.txt b.txt` → Without `-s`, `cmp` reports the exact byte and line of the first difference.

**New words in this step:**

- **`cmp`** — byte-level comparison; pinpoints the first differing byte.
- **`cmp -s`** — silent mode, exit code only.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `diff -q` | line equality | misses pure-newline diffs sometimes |
| `cmp` | byte equality | reports first diff offset |
| `cmp -s` | silent | for scripting |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `diff` same but `cmp` differs | Trailing newline/byte | Trust `cmp` for exactness |
| `cmp` noisy | Missing `-s` | Add `-s` for scripts |

---

## TASK 2 of 2 — Quantify tree drift

**In plain English:** We summarize and then count the differences between two trees.

---

### Step 1 of 2 — Summarize with `diff -rq`

**In plain English:** We list every differing or only-in file between the two trees.

```bash
cd "$LAB_ROOT"
diff -rq d1 d2
echo "exit code: $?"
```

**Expected output:**

```
Files d1/diff.txt and d2/diff.txt differ
Only in d1: only.txt
exit code: 1
```

**Line-by-line breakdown:**

- `diff -rq d1 d2` → One line per differing file plus "Only in" for files unique to a tree.
- `exit code: 1` → Trees differ.

**New words in this step:**

- **`diff -rq`** — recursive brief summary, one line per drift entry.

---

### Step 2 of 2 — Count the drift

**In plain English:** We count how many files drifted and assert the expected number.

```bash
cd "$LAB_ROOT"
N=$(diff -rq d1 d2 | wc -l)
echo "drift entries: $N"
[ "$N" -eq 2 ] && echo "DRIFT COUNT OK" || echo "UNEXPECTED DRIFT (FAIL)"
```

**Expected output:**

```
drift entries: 2
DRIFT COUNT OK
```

**Line-by-line breakdown:**

- `diff -rq d1 d2 | wc -l` → Count the summary lines: one "differ" + one "Only in" = 2.
- `[ "$N" -eq 2 ]` → Assert the drift matches the expected count.

**New words in this step:**

- **drift count** — number of differing/only-in entries between two trees.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `diff -rq` | tree summary | counts "Only in" too |
| `wc -l` count | drift threshold | each entry is one line |
| exit 1 | trees differ | not an error |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Count higher than expected | Extra files present | Inspect "Only in" lines |
| No output | Trees identical | exit 0, count 0 |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Gate on `diff -q`
- [ ] Task 1 · Step 2 — Byte-exact check with `cmp`
- [ ] Task 2 · Step 1 — Summarize with `diff -rq`
- [ ] Task 2 · Step 2 — Count the drift
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-23
```

**Expected output:**

```
✅ Removed /tmp/lab-23 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Trusting `diff` for binaries | Misleading result | Use `cmp` |
| Treating exit 1 as error | Script aborts | 1 = "differ" |
| Forgetting "Only in" | Undercount drift | They count in `-rq` |

---

## 📌 Exam Strategy

Prove identity with `diff -q`/`cmp -s` exit codes, pinpoint byte differences with `cmp`, and quantify tree drift with `diff -rq | wc -l`. Exit codes and counts make comparisons scriptable and gate-able.

- `cmp -s` for byte-exact silent equality.
- `diff -rq` summarizes trees; count lines for a drift metric.
- Exit 1 means differ — handle it, don't fear it.

---

## 🔗 Related Labs

- [Lab 23a — Comparing File Differences (RHCSA)](../lab-23a-diff-comparing-files-rhcsa/) — the diff formats this audits
- [Lab 23b — Comparing File Differences (Ansible)](../lab-23b-diff-comparing-files-ansible/) — the check/diff plays you verify
- [Lab 24c — Stream Editing with sed (Verify)](../lab-24c-sed-stream-editor-verify/) — verifying edits a diff revealed

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
