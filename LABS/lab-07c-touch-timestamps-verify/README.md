# Lab 07c: Touch Timestamps (Verify) — `stat`, `find`, `test`

**Series:** linux-ops-mastery — Essential Tools & File Operations · **Lab 07c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving file times are exactly as required), SRE (freshness/SLA checks), DevOps (artifact age gates in CI)  
**Prerequisite:** [Lab 07a](../lab-07a-touch-timestamps-rhcsa/) and [Lab 07b](../lab-07b-touch-timestamps-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `stat -c %y` | _Task 1 · Step 1_ |
| A2 | `find -newer` | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `stat -c %Y` (epoch) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `date -d @EPOCH` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `find -printf` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `[ N -eq N ]` numeric test | Task 1 · Step 2 | _Task 1 · Step 2_ |

---

## 🎯 Objective

Take the auditor's seat: prove the timestamps from 07a/07b are exactly what was required, not approximately. You will read the modify time as a raw epoch with `stat -c %Y`, compare it to an expected epoch with a numeric test, and use `find -printf`/`-newer` to prove age-based searches return precisely the right files. Epoch math turns "looks about right" into an exact equality.

---

## 🧠 Concept

Human-readable times are easy to misread; **epoch seconds** are not. `stat -c %Y` prints the mtime as seconds since 1970, and `date -d "2026-01-01 12:00" +%s` computes the expected epoch — comparing them with `[ a -eq b ]` is an exact, timezone-safe verdict. For age searches, `find -printf '%T@ %p\n'` prints each file's mtime epoch beside its path, and `-newer ref` proves relative ordering. Epoch equality is the strongest timestamp proof there is.

```
stat -c %Y app.log         → 1767286800           (mtime epoch)
date -d "2026-01-01 12:00" +%s → 1767286800        (expected epoch)
[ 1767286800 -eq 1767286800 ] → true (MATCH)
find . -newer ref -printf '%p\n' → newer files only
```

> **Why this matters:** A grader checks the exact second, not the rendered string. Epoch comparison is how you prove a `touch` landed precisely, regardless of locale or timezone display.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `stat -c %Y` | mtime as epoch seconds | `%X` atime epoch, `%Z` ctime epoch |
| `date -d STR +%s` | Convert a date to epoch | the expected value to compare against |
| `[ a -eq b ]` | Integer equality test | `-eq/-ne/-lt/-gt` for numbers |
| `find -printf` | Custom find output | `%T@` mtime epoch, `%p` path |
| `find -newer` | Files newer than a reference | uses mtime |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Rebuild the sandbox and pin a known mtime so there is an exact value to verify.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-07
mkdir -p "$LAB_ROOT/logs"
cd "$LAB_ROOT"
echo "entry" > logs/app.log
touch -t 202601011200.00 logs/app.log
echo "ref" > logs/reference.log
touch -d "2025-12-25 09:30:00" logs/reference.log
ls -l --time-style=long-iso logs
echo "exit was: $?"
```

**Expected output:**

```
-rw-r--r--. 1 root root 6 2026-01-01 12:00 app.log
-rw-r--r--. 1 root root 4 2025-12-25 09:30 reference.log
exit was: 0
```

---

## TASK 1 of 2 — Prove the exact mtime with epoch math

**In plain English:** We read the mtime as an epoch and prove it equals the expected value to the second.

---

### Step 1 of 2 — Read the mtime epoch with `stat -c %Y`

**In plain English:** We print the raw epoch seconds of the file's mtime so we can compare it numerically.

```bash
cd "$LAB_ROOT"
ACTUAL=$(stat -c %Y logs/app.log)
echo "actual epoch: $ACTUAL"
```

**Expected output:**

```
actual epoch: 1767286800
```

**Line-by-line breakdown:**

- `ACTUAL=$(stat -c %Y logs/app.log)` → Capture the mtime as epoch seconds, free of any locale formatting.
- `echo "actual epoch: $ACTUAL"` → Show the captured value for the comparison ahead.

**New words in this step:**

- **epoch seconds** — a timestamp expressed as seconds since 1970-01-01 UTC, the unambiguous machine form.

---

### Step 2 of 2 — Compare against the expected epoch

**In plain English:** We compute what the epoch *should* be from the date string and assert the two match exactly.

```bash
cd "$LAB_ROOT"
EXPECTED=$(date -d "2026-01-01 12:00:00" +%s)
echo "expected epoch: $EXPECTED"
[ "$ACTUAL" -eq "$EXPECTED" ] && echo "MTIME EXACT MATCH (OK)" || echo "MTIME MISMATCH (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
expected epoch: 1767286800
MTIME EXACT MATCH (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `EXPECTED=$(date -d "..." +%s)` → Convert the human date to epoch seconds — the value `touch -t` should have produced.
- `[ "$ACTUAL" -eq "$EXPECTED" ]` → Integer-compare the two epochs; `-eq` is exact, so the OK branch proves a precise set.

**New words in this step:**

- **`date -d STR +%s`** — convert any date expression to epoch seconds.
- **`[ a -eq b ]`** — integer equality test, the numeric counterpart of `=`.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `stat -c %Y` | mtime epoch | timezone-independent, unlike `%y` |
| `date -d +%s` | expected epoch | DST/locale can shift human strings |
| `[ -eq ]` | integer compare | using `=` here is a string compare |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Off by 3600 | DST/timezone in the date string | Include explicit TZ or use UTC |
| `integer expression expected` | Compared with `=` | Use `-eq` for epochs |

---

## TASK 2 of 2 — Prove age searches with `find -printf`

**In plain English:** We print each file's epoch alongside its path and prove `-newer` returns exactly the newer file.

---

### Step 1 of 2 — Dump mtimes with `find -printf`

**In plain English:** We list every log file with its mtime epoch so the ordering is explicit.

```bash
cd "$LAB_ROOT"
find logs -type f -printf '%T@ %p\n' | sort -n
echo "exit was: $?"
```

**Expected output:**

```
1735137000.0000000000 logs/reference.log
1767286800.0000000000 logs/app.log
exit was: 0
```

**Line-by-line breakdown:**

- `find logs -type f -printf '%T@ %p\n'` → For each file, print its mtime epoch (`%T@`) and path (`%p`).
- `| sort -n` → Numerically sort so the oldest file is first — reference.log (Dec 2025) before app.log (Jan 2026).

**New words in this step:**

- **`-printf`** — `find`'s custom output formatter; `%T@` is the mtime epoch, `%p` the path.

---

### Step 2 of 2 — Prove `-newer` selects exactly the newer file

**In plain English:** We ask `find` which files are newer than the reference and assert only `app.log` comes back.

```bash
cd "$LAB_ROOT"
NEWER=$(find logs -type f -newer logs/reference.log -printf '%f\n')
echo "newer than reference: $NEWER"
[ "$NEWER" = "app.log" ] && echo "NEWER SET CORRECT (OK)" || echo "UNEXPECTED SET (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
newer than reference: app.log
NEWER SET CORRECT (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `NEWER=$(find ... -newer logs/reference.log -printf '%f\n')` → List filenames modified more recently than the reference.
- `[ "$NEWER" = "app.log" ]` → Assert exactly the expected file came back, proving `-newer` ordering is correct.

**New words in this step:**

- **`%f`** — the `-printf` directive for the bare filename (no directory).

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `find -printf '%T@'` | mtime epoch per file | mixes fractional seconds — sort `-n` |
| `find -newer` | relative ordering | uses mtime, not ctime |
| `%f` vs `%p` | basename vs full path | choose by what you assert |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Both files returned by `-newer` | Reference newer than expected | Re-pin reference time in SETUP |
| `-printf` not recognized | Using non-GNU find | Use GNU `find` on RHEL |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Read the mtime epoch with `stat -c %Y`
- [ ] Task 1 · Step 2 — Compare against the expected epoch
- [ ] Task 2 · Step 1 — Dump mtimes with `find -printf`
- [ ] Task 2 · Step 2 — Prove `-newer` selects exactly the newer file
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-07
```

**Expected output:**

```
✅ Removed /tmp/lab-07 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Comparing rendered strings | Locale/timezone false negatives | Compare epochs with `-eq` |
| Sorting `%T@` lexically | Wrong order | Use `sort -n` |
| Assuming `-newer` uses ctime | Wrong matches | It uses mtime |

---

## 📌 Exam Strategy

To verify a timestamp task, drop to epoch seconds: `stat -c %Y` versus `date -d "..." +%s` with `-eq` is an exact, timezone-proof check. For age searches, `find -printf` makes the ordering visible so you can prove `-newer`/`-mtime` returned the right set.

- Epoch equality beats reading rendered dates every time.
- `find -printf '%T@ %p'` is the clearest way to debug age queries.
- Always `sort -n` epoch output, never lexically.

---

## 🔗 Related Labs

- [Lab 07a — Touch Timestamps (RHCSA)](../lab-07a-touch-timestamps-rhcsa/) — the times this audits
- [Lab 07b — Touch Timestamps (Ansible)](../lab-07b-touch-timestamps-ansible/) — the playbook whose output you verify
- [Lab 14c — Searching with find (Verify)](../lab-14c-searching-with-find-verify/) — more `find` verification patterns

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
