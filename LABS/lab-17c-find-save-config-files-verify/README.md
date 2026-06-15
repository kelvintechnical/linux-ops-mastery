# Lab 17c: Find and Save Config Files (Verify) — `wc -l`, `grep -q`, `diff`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 17c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving a discovery list is complete and correct), SRE (inventory audits), DevOps (config compliance gates)  
**Prerequisite:** [Lab 17a](../lab-17a-find-save-config-files-rhcsa/) and [Lab 17b](../lab-17b-find-save-config-files-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `wc -l` | _Task 1 · Step 1_ |
| A2 | `grep -q` | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `comm` (set compare) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N2 | `find ... | wc -l` recount | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `stat -c %a` perm audit | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `sort -c` (is-sorted check) | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Take the auditor's seat: prove the saved config inventory is complete and the permission normalization held. You will recount with a fresh `find` and compare, set-compare the saved list against a fresh one with `comm`, audit modes with `stat`, and confirm the list is sorted. A complete, sorted, correctly-permissioned inventory is the deliverable.

---

## 🧠 Concept

Inventory verification has two halves. **Completeness**: a fresh `find ... | wc -l` should equal the saved list's line count, and `comm -3` between the saved list and a freshly generated one should be empty (no lines unique to either side). **Correctness**: `stat -c %a` proves the discovered files carry the intended mode, and `sort -c` proves the saved list is in canonical order (so diffs against it are stable). Set comparison with `comm` is stronger than a line count because it catches *which* entries differ.

```
find ... | wc -l == wc -l < saved.txt   → same count
comm -3 saved.txt fresh.txt → (empty)   → exact same set
stat -c %a file → 640                    → correct perms
sort -c saved.txt → (silent)             → already sorted
```

> **Why this matters:** A count match alone can hide a swapped entry. `comm` proves the *exact* set, and a sortedness check keeps future diffs trustworthy.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `wc -l` | Count lines | `< file` for the bare number |
| `comm -3` | Lines unique to either file | inputs must be sorted |
| `grep -q` | Presence assertion | exit 0 found |
| `stat -c %a` | Mode audit | per-file permission |
| `sort -c` | Verify a file is sorted | silent if sorted, errors if not |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Rebuild the tree, the saved sorted list, and normalized permissions so there is a real inventory to audit.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-17
mkdir -p "$LAB_ROOT/etc/app" "$LAB_ROOT/etc/svc"
cd "$LAB_ROOT"
echo a > etc/app/app.conf
echo b > etc/svc/svc.conf
chmod 640 etc/app/app.conf etc/svc/svc.conf
find etc -type f -name '*.conf' | sort > configs.txt
cat configs.txt
echo "exit was: $?"
```

**Expected output:**

```
etc/app/app.conf
etc/svc/svc.conf
exit was: 0
```

---

## TASK 1 of 2 — Prove the list is complete

**In plain English:** We recount and set-compare the saved list against a fresh discovery.

---

### Step 1 of 2 — Recount and compare totals

**In plain English:** We count the saved list and a fresh `find` and assert they match.

```bash
cd "$LAB_ROOT"
SAVED=$(wc -l < configs.txt)
FRESH=$(find etc -type f -name '*.conf' | wc -l)
echo "saved=$SAVED fresh=$FRESH"
[ "$SAVED" -eq "$FRESH" ] && echo "COUNT OK" || echo "COUNT MISMATCH (FAIL)"
```

**Expected output:**

```
saved=2 fresh=2
COUNT OK
```

**Line-by-line breakdown:**

- `SAVED=$(wc -l < configs.txt)` → Count the saved inventory lines.
- `FRESH=$(find ... | wc -l)` → Count a fresh discovery.
- `[ "$SAVED" -eq "$FRESH" ]` → Equal totals are the first completeness check.

**New words in this step:**

- **recount** — independently re-deriving a count to compare against a saved one.

---

### Step 2 of 2 — Set-compare with `comm`

**In plain English:** We prove the saved list and a fresh list contain exactly the same entries.

```bash
cd "$LAB_ROOT"
find etc -type f -name '*.conf' | sort > fresh.txt
comm -3 configs.txt fresh.txt
[ -z "$(comm -3 configs.txt fresh.txt)" ] && echo "SETS IDENTICAL (OK)" || echo "SETS DIFFER (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
SETS IDENTICAL (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `find ... | sort > fresh.txt` → Build a fresh, sorted list.
- `comm -3 configs.txt fresh.txt` → Print lines unique to either side; empty output means the sets match exactly.
- `[ -z "$(...)" ]` → Assert the comparison produced nothing — identical sets.

**New words in this step:**

- **`comm -3`** — show lines unique to each of two sorted files (suppressing the common column).

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `wc -l` recount | count completeness | count match can hide a swap |
| `comm -3` | exact set diff | inputs MUST be sorted |
| `-z` empty test | "no differences" | quote the command substitution |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `comm` shows garbage | Inputs not sorted | Sort both before `comm` |
| Count match but set differs | Swapped entries | Trust `comm` over the count |

---

## TASK 2 of 2 — Prove permissions and order

**In plain English:** We audit each file's mode and confirm the saved list is sorted.

---

### Step 1 of 2 — Audit modes with `stat`

**In plain English:** We confirm each discovered config is mode 640.

```bash
cd "$LAB_ROOT"
while read -r f; do
  M=$(stat -c %a "$f")
  [ "$M" = "640" ] && echo "$f 640 OK" || echo "$f $M WRONG (FAIL)"
done < configs.txt
echo "exit was: $?"
```

**Expected output:**

```
etc/app/app.conf 640 OK
etc/svc/svc.conf 640 OK
exit was: 0
```

**Line-by-line breakdown:**

- `while read -r f; do ... done < configs.txt` → Iterate the saved paths.
- `M=$(stat -c %a "$f")` → Read each file's octal mode.
- `[ "$M" = "640" ]` → Assert it equals the intended permission.

**New words in this step:**

- **mode audit** — checking each file's permission bits against a policy.

---

### Step 2 of 2 — Confirm the list is sorted with `sort -c`

**In plain English:** We verify the saved inventory is in sorted order so future diffs stay stable.

```bash
cd "$LAB_ROOT"
sort -c configs.txt && echo "LIST SORTED (OK)" || echo "LIST UNSORTED (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
LIST SORTED (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `sort -c configs.txt` → Check (do not rewrite) whether the file is already sorted; silent success means yes, an error line means no.
- `&& echo OK || echo FAIL` → Convert to a verdict.

**New words in this step:**

- **`sort -c`** — check mode: verify a file is sorted without changing it.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `stat -c %a` loop | per-file perms | quote `"$f"` for spaces |
| `sort -c` | is-sorted check | does not sort, only verifies |
| sorted inventory | stable diffs | unsorted lists break `comm` |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `WRONG (FAIL)` mode | Normalization missed a file | Re-run the 17b mode task |
| `sort -c` errors | List not sorted | Regenerate with `| sort` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Recount and compare totals
- [ ] Task 1 · Step 2 — Set-compare with `comm`
- [ ] Task 2 · Step 1 — Audit modes with `stat`
- [ ] Task 2 · Step 2 — Confirm the list is sorted with `sort -c`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-17
```

**Expected output:**

```
✅ Removed /tmp/lab-17 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Trusting count over set | Swapped entries unnoticed | Use `comm -3` |
| `comm` on unsorted input | Bogus output | Sort both inputs |
| Unquoted `"$f"` in loop | Breaks on spaces | Always quote |

---

## 📌 Exam Strategy

Certify a discovery list by completeness (`wc -l` + `comm`) and correctness (`stat` + `sort -c`). `comm` proves the exact set, not just a count, and a sortedness check keeps your audits repeatable.

- `comm -3` is the strongest "same set" proof.
- Always sort lists before set comparisons.
- Audit modes per file when normalization is required.

---

## 🔗 Related Labs

- [Lab 17a — Find and Save Config Files (RHCSA)](../lab-17a-find-save-config-files-rhcsa/) — the discovery this audits
- [Lab 17b — Find and Save Config Files (Ansible)](../lab-17b-find-save-config-files-ansible/) — the playbook output you verify
- [Lab 23c — Comparing File Differences (Verify)](../lab-23c-diff-comparing-files-verify/) — deeper `diff`/`comm` comparison

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
