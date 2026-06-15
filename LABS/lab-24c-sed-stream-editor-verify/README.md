# Lab 24c: Stream Editing with sed (Verify) — `grep -c`, `diff`, backup checks

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 24c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving non-interactive edits), SRE (config-edit validation), DevOps (safe-rollback verification)  
**Prerequisite:** [Lab 24a](../lab-24a-sed-stream-editor-rhcsa/) and [Lab 24b](../lab-24b-sed-stream-editor-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `grep -c` / `-q` | _Task 1 · Step 1_ |
| A2 | `diff -u` | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | new-present + old-absent proof | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `sed -n` re-derivation check | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | backup integrity (`diff` orig) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | idempotence re-edit proof | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Certify that a `sed`/`replace` edit did exactly what was asked and left a usable rollback. You will prove the new value is present and the old value is gone, re-derive the expected result independently, confirm the `.bak` backup still holds the original, and prove the edit is idempotent by re-applying it with no further change. Correct, complete, reversible, and stable — the four properties of a trustworthy edit.

---

## 🧠 Concept

A stream edit is verified on four axes. **Correctness**: the new text is present (`grep -c new` equals the expected count). **Completeness**: the old text is gone (`grep -q old` returns non-zero). **Independence**: re-running the transformation on the *original* (via the backup) reproduces the edited file (`diff` is empty) — proof the result wasn't a fluke. **Reversibility**: the `.bak` backup equals the pre-edit original, so you can roll back. Idempotence ties it together: re-applying the edit changes nothing.

```
grep -c 'Port 2222' f → 2   → new value present, right count
grep -q 'Port 22$' f || echo gone → old value absent
sed 's/.../.../ ' f.bak | diff - f → empty → transform reproducible
diff f.bak original → empty → backup is a true rollback point
```

> **Why this matters:** "The play said changed=1" isn't proof. Showing new-present, old-absent, reproducible, and reversible is what lets you trust an automated config edit in production.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `grep -c` | Count new value | exact match assertion |
| `grep -q` (inverted) | Old value absent | exit-code test |
| `sed -n` re-derive | Independent expected | reproduce the edit |
| `diff` | Compare results/backup | empty = identical |
| `.bak` check | Rollback integrity | original preserved |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Recreate an original config, a backup, and the edited result.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-24
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"
printf 'Port 22\nPort 22\nLogLevel INFO\n' > orig.conf
cp orig.conf sshd.conf
cp orig.conf sshd.conf.bak
sed -i 's/^Port 22$/Port 2222/' sshd.conf
cat sshd.conf
echo "exit was: $?"
```

**Expected output:**

```
Port 2222
Port 2222
LogLevel INFO
exit was: 0
```

---

## TASK 1 of 2 — Prove correctness and completeness

**In plain English:** We confirm the new value is present in the right count and the old value is gone.

---

### Step 1 of 2 — New present, old absent

**In plain English:** We count the new Port lines and confirm no old Port line remains.

```bash
cd "$LAB_ROOT"
C=$(grep -c '^Port 2222$' sshd.conf)
echo "new lines: $C"
[ "$C" -eq 2 ] && echo "NEW OK" || echo "NEW WRONG (FAIL)"
grep -q '^Port 22$' sshd.conf && echo "OLD REMAINS (FAIL)" || echo "OLD GONE (OK)"
```

**Expected output:**

```
new lines: 2
NEW OK
OLD GONE (OK)
```

**Line-by-line breakdown:**

- `grep -c '^Port 2222$'` → Count the edited lines; expect 2.
- `grep -q '^Port 22$' && ... || ...` → Non-zero exit (no match) proves the old value is gone.

**New words in this step:**

- **new-present/old-absent** — the paired correctness and completeness checks for an edit.

---

### Step 2 of 2 — Re-derive the expected result

**In plain English:** We apply the same transform to the backup and confirm it reproduces the edited file.

```bash
cd "$LAB_ROOT"
sed 's/^Port 22$/Port 2222/' sshd.conf.bak | diff - sshd.conf \
  && echo "TRANSFORM REPRODUCIBLE (OK)" || echo "MISMATCH (FAIL)"
```

**Expected output:**

```
TRANSFORM REPRODUCIBLE (OK)
```

**Line-by-line breakdown:**

- `sed 's/.../.../ ' sshd.conf.bak | diff - sshd.conf` → Re-apply the edit to the original and diff against the live file; empty output proves the edit is exactly the documented transform.

**New words in this step:**

- **re-derivation** — independently reproducing the edit to confirm it's deterministic.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `grep -c` new | correctness | exact count matters |
| `grep -q` old | completeness | invert the logic |
| re-derive | determinism | uses the backup |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Old value remains | Edit pattern missed it | Anchor the regex |
| Re-derive mismatch | Edit not the documented one | Reconcile the transform |

---

## TASK 2 of 2 — Prove reversibility and idempotence

**In plain English:** We confirm the backup is a true rollback and that re-editing changes nothing.

---

### Step 1 of 2 — Backup integrity

**In plain English:** We confirm the `.bak` backup is identical to the untouched original.

```bash
cd "$LAB_ROOT"
diff sshd.conf.bak orig.conf && echo "BACKUP MATCHES ORIGINAL (OK)" || echo "BACKUP CORRUPT (FAIL)"
grep -q '^Port 22$' sshd.conf.bak && echo "ROLLBACK POSSIBLE (OK)" || echo "NO ROLLBACK (FAIL)"
```

**Expected output:**

```
BACKUP MATCHES ORIGINAL (OK)
ROLLBACK POSSIBLE (OK)
```

**Line-by-line breakdown:**

- `diff sshd.conf.bak orig.conf` → Empty output proves the backup is a byte-for-byte original.
- `grep -q '^Port 22$' sshd.conf.bak` → Confirms the old value is recoverable from the backup.

**New words in this step:**

- **rollback point** — a backup that exactly preserves the pre-edit state.

---

### Step 2 of 2 — Idempotence of the edit

**In plain English:** We re-apply the same `sed` and confirm the file does not change.

```bash
cd "$LAB_ROOT"
cp sshd.conf before.txt
sed -i 's/^Port 22$/Port 2222/' sshd.conf
diff before.txt sshd.conf && echo "IDEMPOTENT (OK)" || echo "RE-EDIT CHANGED FILE (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
IDEMPOTENT (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `cp sshd.conf before.txt` → Snapshot the current state.
- `sed -i 's/^Port 22$/Port 2222/'` → Re-apply the edit; there's no `Port 22` left to change.
- `diff before.txt sshd.conf` → Empty output proves re-applying changed nothing.

**New words in this step:**

- **edit idempotence** — re-running the same edit produces no further change.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| backup `diff` | rollback proof | must equal original |
| re-edit `diff` | idempotence | empty = stable |
| `.bak` presence | safety net | bare `-i` leaves none |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Backup differs from original | Edited before backup | Back up first |
| Re-edit changes file | Pattern matches result | Make regex not re-match |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — New present, old absent
- [ ] Task 1 · Step 2 — Re-derive the expected result
- [ ] Task 2 · Step 1 — Backup integrity
- [ ] Task 2 · Step 2 — Idempotence of the edit
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-24
```

**Expected output:**

```
✅ Removed /tmp/lab-24 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Proving new only | Old value lingers | Also prove old absent |
| No backup check | Can't roll back | Verify `.bak` = original |
| Skipping idempotence | Hidden re-match bug | Re-apply and diff |

---

## 📌 Exam Strategy

Verify an edit four ways: new present (count), old absent, reproducible (re-derive from backup), and reversible (`.bak` = original) — then confirm idempotence by re-applying. This proves the edit is correct, complete, deterministic, and safe.

- Always prove the old value is gone, not just the new present.
- A `.bak` that equals the original is your rollback guarantee.
- Re-apply and `diff` to confirm idempotence.

---

## 🔗 Related Labs

- [Lab 24a — Stream Editing with sed (RHCSA)](../lab-24a-sed-stream-editor-rhcsa/) — the `sed` this audits
- [Lab 24b — Stream Editing with sed (Ansible)](../lab-24b-sed-stream-editor-ansible/) — the `replace`/`lineinfile` edits you verify
- [Lab 23c — Comparing File Differences (Verify)](../lab-23c-diff-comparing-files-verify/) — diff/cmp comparison techniques

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
