# Lab 21c: Monitoring Live Logs (Verify) — `tail -n`, `wc -l`, `grep -c`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 21c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving a tail captured the right lines), SRE (log-snapshot validation), DevOps (alert-rule testing)  
**Prerequisite:** [Lab 21a](../lab-21a-tail-f-live-logs-rhcsa/) and [Lab 21b](../lab-21b-tail-f-live-logs-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `tail -n N` | _Task 1 · Step 1_ |
| A2 | `grep -c` | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `tail -n | wc -l` count proof | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `tail` vs `awk` last-line check | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `grep -c` on a snapshot | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `diff` snapshot vs expectation | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Prove a log snapshot captured exactly what it should. You will confirm `tail -n N` returns N lines, that the captured last line really is the file's last line, count the alerts in the snapshot with `grep -c`, and diff a snapshot against an expected window. These checks validate the monitoring logic a playbook depends on.

---

## 🧠 Concept

A monitoring snapshot is only trustworthy if it captured the right window. Two things to verify: **size** — `tail -n N | wc -l` should equal N (or the file length if shorter); and **content** — the snapshot's last line must equal the file's actual last line (`tail -1` vs `awk 'END{print}'`). For alerting, `grep -c PATTERN` on the snapshot must match the known number of events, and a `diff` between the snapshot and an expected window catches drift exactly.

```
tail -n 10 f | wc -l → 10            → window size correct
tail -1 f == awk 'END{print}' f      → last line agrees
grep -c ERROR snapshot → 1           → alert count correct
diff snapshot expected → (empty)     → snapshot matches expectation
```

> **Why this matters:** If a remediation play fires on "ERROR in the last 20 lines," you must prove that window is the right size and that your match count is correct — otherwise you alert on the wrong data.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `tail -n N | wc -l` | Window size | equals N or file length |
| `tail -1` | Last line | compare with `awk END` |
| `awk 'END{print}'` | Last line, independently | cross-check |
| `grep -c` | Count alerts | match lines, not occurrences |
| `diff` | Snapshot vs expected | empty = identical |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Rebuild the log with a known last line and one alert.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-21
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"
seq 1 49 | sed 's/^/event /' > app.log
echo "ERROR disk pressure" >> app.log
echo "event 50" >> app.log
wc -l app.log
echo "exit was: $?"
```

**Expected output:**

```
51 app.log
exit was: 0
```

---

## TASK 1 of 2 — Prove the window

**In plain English:** We confirm the snapshot is the right size and ends on the right line.

---

### Step 1 of 2 — Prove the window size

**In plain English:** We capture 10 lines and confirm we got exactly 10.

```bash
cd "$LAB_ROOT"
N=$(tail -n 10 app.log | wc -l)
echo "window: $N"
[ "$N" -eq 10 ] && echo "WINDOW SIZE OK" || echo "WRONG SIZE (FAIL)"
```

**Expected output:**

```
window: 10
WINDOW SIZE OK
```

**Line-by-line breakdown:**

- `tail -n 10 app.log | wc -l` → Count the snapshot's lines.
- `[ "$N" -eq 10 ]` → A 10-line request on a 51-line file must yield exactly 10.

**New words in this step:**

- **window size** — the number of lines a snapshot is supposed to capture.

---

### Step 2 of 2 — Prove the last line

**In plain English:** We confirm the snapshot's last line is the file's true last line, using two tools.

```bash
cd "$LAB_ROOT"
T=$(tail -1 app.log)
A=$(awk 'END{print}' app.log)
echo "tail: $T"
echo "awk:  $A"
[ "$T" = "$A" ] && echo "LAST LINE OK" || echo "MISMATCH (FAIL)"
```

**Expected output:**

```
tail: event 50
awk:  event 50
LAST LINE OK
```

**Line-by-line breakdown:**

- `tail -1` / `awk 'END{print}'` → Get the last line two independent ways.
- `[ "$T" = "$A" ]` → Agreement proves the tail truly captured the file's end.

**New words in this step:**

- **`awk 'END{print}'`** — print the final line; `END` runs after the last record.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `tail -n | wc -l` | size proof | short files yield fewer |
| `tail -1` vs `awk END` | last-line cross-check | both must agree |
| snapshot end | newest event | not necessarily an alert |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Window < N | File shorter than N | Expected for short logs |
| Last lines differ | File changed mid-check | Re-snapshot |

---

## TASK 2 of 2 — Prove the alert detection

**In plain English:** We count alerts in a snapshot and diff it against an expected window.

---

### Step 1 of 2 — Count alerts with `grep -c`

**In plain English:** We snapshot the tail and confirm exactly one ERROR is present.

```bash
cd "$LAB_ROOT"
tail -n 20 app.log > snap.txt
C=$(grep -c ERROR snap.txt)
echo "alerts: $C"
[ "$C" -eq 1 ] && echo "ALERT COUNT OK" || echo "WRONG COUNT (FAIL)"
```

**Expected output:**

```
alerts: 1
ALERT COUNT OK
```

**Line-by-line breakdown:**

- `tail -n 20 app.log > snap.txt` → Save a snapshot to a file.
- `grep -c ERROR snap.txt` → Count alert lines in the snapshot.
- `[ "$C" -eq 1 ]` → Assert the known alert count.

**New words in this step:**

- **alert count** — number of matching events inside the captured window.

---

### Step 2 of 2 — Diff against an expected window

**In plain English:** We build the expected last-20 window directly and confirm the snapshot matches it.

```bash
cd "$LAB_ROOT"
tail -n 20 app.log > expected.txt
diff snap.txt expected.txt && echo "SNAPSHOT MATCHES (OK)" || echo "DRIFT (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
SNAPSHOT MATCHES (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `tail -n 20 app.log > expected.txt` → Independently build the expected window.
- `diff snap.txt expected.txt` → No output (exit 0) means the snapshot is exactly the expected window.

**New words in this step:**

- **drift check** — diffing a captured snapshot against a freshly computed expectation.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `grep -c` | alert count | counts lines, not hits |
| `diff` | exact comparison | empty output = identical |
| snapshot vs expected | drift detection | rebuild expected the same way |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Wrong alert count | Window too small/large | Match `tail -n` to the rule |
| `diff` shows changes | File grew mid-test | Snapshot both at once |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Prove the window size
- [ ] Task 1 · Step 2 — Prove the last line
- [ ] Task 2 · Step 1 — Count alerts with `grep -c`
- [ ] Task 2 · Step 2 — Diff against an expected window
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-21
```

**Expected output:**

```
✅ Removed /tmp/lab-21 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Trusting tail size blindly | Short file fools you | Compare to file length |
| One last-line tool only | Hidden capture bug | Cross-check `tail` vs `awk` |
| Mismatched windows | False drift | Build expected identically |

---

## 📌 Exam Strategy

Validate monitoring logic by proving window size, last-line agreement, alert count, and snapshot-versus-expected equality. If these hold, the play that reacts to the tail is acting on correct data.

- `tail -n N | wc -l` proves the window captured N lines.
- Cross-check the last line with `awk 'END{print}'`.
- `diff` a snapshot against a freshly built window to detect drift.

---

## 🔗 Related Labs

- [Lab 21a — Monitoring Live Logs (RHCSA)](../lab-21a-tail-f-live-logs-rhcsa/) — the `tail -f` this audits
- [Lab 21b — Monitoring Live Logs (Ansible)](../lab-21b-tail-f-live-logs-ansible/) — the snapshot plays you verify
- [Lab 22c — Filtering with grep and Regex (Verify)](../lab-22c-grep-regex-verify/) — deeper match validation

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
