# Lab 05c: Directory Navigation (Verify) — `readlink -f`, `pwd -P`, `test`

**Series:** linux-ops-mastery — Essential Tools & File Operations · **Lab 05c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving you operated in the right path), SRE (path correctness in incident scripts), DevOps (canonical-path checks in CI)  
**Prerequisite:** [Lab 05a](../lab-05a-directory-navigation-rhcsa/) and [Lab 05b](../lab-05b-directory-navigation-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `pwd -P` | _Task 1 · Step 1_ |
| A2 | `cd` | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `readlink -f` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N2 | `test -L` / `test -d` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `realpath` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `[ a = b ]` string test | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Take the auditor's seat: prove the logical-vs-physical path story from 05a is real, not a feeling. You will assert a symlink is a symlink, resolve it to its canonical target with `readlink -f` and `realpath`, and prove that standing inside the symlink yields a different `pwd -P` than the path you typed. The verdict is a clean string comparison — pass or fail.

---

## 🧠 Concept

Verification of navigation is about *canonical paths*. A symlink (`test -L` true) points at a real directory; `readlink -f` and `realpath` both collapse every symlink in a path to the single real location. When you `cd` through a symlink, `pwd -L` echoes what you typed while `pwd -P` reports the canonical target. Comparing the two with `[ a = b ]` turns "are these the same place?" into a scriptable yes/no — exactly what a grader needs.

```
test -L link_dir    → true (it is a symlink)
readlink -f link_dir → /tmp/lab-05/real_dir   (canonical target)
cd link_dir ; pwd -L → /tmp/lab-05/link_dir   (logical)
cd link_dir ; pwd -P → /tmp/lab-05/real_dir   (physical = canonical)
```

> **Why this matters:** Scripts that compute output paths from `pwd` write to the wrong place when a symlink is in play. Asserting canonical paths catches that class of bug before it corrupts data.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `test -L PATH` | True if PATH is a symlink | pairs with `&&`/`||` for a verdict |
| `test -d PATH` | True if PATH is a directory | follows symlinks by default |
| `readlink -f PATH` | Print the canonical resolved path | `-f` resolves every component |
| `realpath PATH` | Print the absolute canonical path | errors if a component is missing |
| `pwd -P` | Physical CWD (symlinks resolved) | compare against `pwd -L` |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Rebuild the sandbox with a real directory and a symlink to it so there is a known structure to audit.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-05
mkdir -p "$LAB_ROOT/real_dir/sub"
ln -sfn "$LAB_ROOT/real_dir" "$LAB_ROOT/link_dir"
ls -l "$LAB_ROOT"
echo "exit was: $?"
```

**Expected output:**

```
drwxr-xr-x. 3 root root 17 Jun 15 18:20 real_dir
lrwxrwxrwx. 1 root root 18 Jun 15 18:20 link_dir -> /tmp/lab-05/real_dir
exit was: 0
```

---

## TASK 1 of 2 — Assert the symlink and resolve it

**In plain English:** We prove `link_dir` is genuinely a symlink pointing at a real directory, then resolve it to its canonical target.

---

### Step 1 of 2 — Assert link type with `test -L` / `test -d`

**In plain English:** We confirm `link_dir` is a symlink and that it leads to a real directory.

```bash
cd "$LAB_ROOT"
test -L link_dir && echo "IS A SYMLINK (OK)" || echo "NOT A SYMLINK (FAIL)"
test -d link_dir && echo "RESOLVES TO A DIR (OK)" || echo "NOT A DIR (FAIL)"
```

**Expected output:**

```
IS A SYMLINK (OK)
RESOLVES TO A DIR (OK)
```

**Line-by-line breakdown:**

- `test -L link_dir && ... || ...` → `-L` is true only for a symlink; the OK branch fires, proving it is a link, not a copy.
- `test -d link_dir && ... || ...` → `-d` follows the link; OK proves the target is a real directory.

**New words in this step:**

- **`test -L`** — the file test that is true only for a symbolic link.

---

### Step 2 of 2 — Resolve the canonical target with `readlink -f`

**In plain English:** We print the real path the symlink points at, collapsing every link in the chain.

```bash
readlink -f "$LAB_ROOT/link_dir"
readlink -f "$LAB_ROOT/link_dir" | grep -q '/real_dir$' && echo "TARGET OK" || echo "TARGET WRONG (FAIL)"
```

**Expected output:**

```
/tmp/lab-05/real_dir
TARGET OK
```

**Line-by-line breakdown:**

- `readlink -f "$LAB_ROOT/link_dir"` → Resolve the symlink to its canonical path; `-f` follows the whole chain.
- `... | grep -q '/real_dir$'` → Assert the canonical path ends in `real_dir`, turning resolution into a verdict.

**New words in this step:**

- **`readlink -f`** — prints the fully-resolved canonical path of a symlink or file.
- **canonical path** — the single, symlink-free absolute path to a file.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `test -L` | true for symlinks | `test -e` is true for both link and target |
| `test -d` on a link | follows the link | a dangling link makes `-d` false |
| `readlink -f` | canonical resolution | `readlink` without `-f` shows only one hop |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `NOT A SYMLINK (FAIL)` | `link_dir` is a real dir/copy | Recreate it with `ln -sfn` |
| `readlink` prints nothing | Path is not a link | Point it at the symlink, not the target |

---

## TASK 2 of 2 — Prove logical ≠ physical inside the link

**In plain English:** We stand inside the symlink and prove `pwd -P` differs from `pwd -L`, then assert the physical path equals the canonical target.

---

### Step 1 of 2 — Capture both paths with `realpath`

**In plain English:** We `cd` into the symlink, record the logical and physical CWDs, and compute the canonical target with `realpath`.

```bash
cd "$LAB_ROOT/link_dir"
LOGICAL=$(pwd -L)
PHYSICAL=$(pwd -P)
CANON=$(realpath "$LAB_ROOT/link_dir")
echo "logical:  $LOGICAL"
echo "physical: $PHYSICAL"
echo "canon:    $CANON"
```

**Expected output:**

```
logical:  /tmp/lab-05/link_dir
physical: /tmp/lab-05/real_dir
canon:    /tmp/lab-05/real_dir
```

**Line-by-line breakdown:**

- `cd "$LAB_ROOT/link_dir"` → Enter via the symlink so logical and physical diverge.
- `LOGICAL=$(pwd -L)` / `PHYSICAL=$(pwd -P)` → Capture both views into variables for comparison.
- `CANON=$(realpath ...)` → Compute the canonical target independently of the CWD.

**New words in this step:**

- **`realpath`** — resolves a path to its absolute canonical form, erroring if a component is missing.

---

### Step 2 of 2 — Assert the relationship with a string test

**In plain English:** We compare the captured paths to prove the logical path differs from the physical one, and that the physical path matches the canonical target.

```bash
[ "$LOGICAL" != "$PHYSICAL" ] && echo "LOGICAL != PHYSICAL (OK)" || echo "PATHS EQUAL (FAIL)"
[ "$PHYSICAL" = "$CANON" ] && echo "PHYSICAL = CANON (OK)" || echo "MISMATCH (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
LOGICAL != PHYSICAL (OK)
PHYSICAL = CANON (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `[ "$LOGICAL" != "$PHYSICAL" ]` → Assert the typed path and the real path differ — the symlink trap, proven numerically.
- `[ "$PHYSICAL" = "$CANON" ]` → Assert the physical CWD equals the canonical target, confirming `pwd -P` is trustworthy.

**New words in this step:**

- **string test `[ a = b ]`** — a shell comparison returning exit 0 (true) or 1 (false) for use in `&&`/`||`.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `pwd -L` vs `-P` | logical vs physical CWD | scripts default to `-L` and misfire |
| `realpath` | canonical target | fails on a non-existent component |
| `[ a = b ]` | string equality verdict | use `=`, not `==`, for POSIX `sh` |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `PATHS EQUAL (FAIL)` | You `cd`'d into the real dir | Enter via `link_dir` instead |
| `realpath: No such file` | Component missing | Re-run SETUP to recreate the tree |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Assert link type with `test -L` / `test -d`
- [ ] Task 1 · Step 2 — Resolve the canonical target with `readlink -f`
- [ ] Task 2 · Step 1 — Capture both paths with `realpath`
- [ ] Task 2 · Step 2 — Assert the relationship with a string test
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-05
```

**Expected output:**

```
✅ Removed /tmp/lab-05 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Using `pwd` and trusting it inside a link | Output written to the real dir unexpectedly | Use `pwd -P` for the true location |
| `readlink` without `-f` | Only one hop resolved | Use `-f` for the full canonical path |
| Comparing with `==` in `sh` | Portability error | Use `=` in POSIX test |

---

## 📌 Exam Strategy

Verification of navigation means proving you operated in the intended directory. After any `cd` that might cross a symlink, run `pwd -P` and compare against the canonical target with `realpath`. Make path assertions part of your scripts so a stray symlink never silently redirects your writes.

- `readlink -f`/`realpath` are interchangeable for canonical paths — know both.
- A `[ "$a" = "$b" ]` test is the cleanest pass/fail in a script.
- When in doubt about "where am I really," `pwd -P` is the answer.

---

## 🔗 Related Labs

- [Lab 05a — Directory Navigation (RHCSA)](../lab-05a-directory-navigation-rhcsa/) — the navigation this audits
- [Lab 05b — Directory Navigation (Ansible)](../lab-05b-directory-navigation-ansible/) — `chdir:` as the Ansible `cd`
- [Lab 09c — Hard and Soft Links (Verify)](../lab-09c-hard-and-soft-links-verify/) — deeper link auditing with `inode` and `readlink`

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
