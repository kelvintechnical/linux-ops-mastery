# Lab 23a: Comparing File Differences (RHCSA) — `diff`, `diff -u`, `diff -r`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 23a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (comparing configs and files), RHCE EX294 (reading `--diff` output), SRE/DevOps (config drift review)  
**Prerequisite:** [Lab 22c](../lab-22c-grep-regex-verify/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | comparing files (`cmp`/hash) | _Task 1 · Step 1_ |
| A2 | redirect to save (`>`) | _Task 2 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `diff` (normal format) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `diff -u` (unified) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `diff -r` (recursive) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `diff` exit codes + `-q` | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

See exactly what changed between two files or two directory trees. You will read `diff`'s normal format, switch to the universal unified format (`-u`) used by patches and `git`, compare whole directories recursively (`-r`), and use `diff`'s exit code and `-q` for scripting. By the end you can answer "what changed?" precisely and machine-checkably.

---

## 🧠 Concept

`diff A B` reports the edits that turn A into B. The **normal** format uses `<`/`>` with change commands (`a`dd, `c`hange, `d`elete). The **unified** format (`-u`) is the modern standard: a `@@` hunk header plus `-`/`+` lines showing context — exactly what `git diff`, `patch`, and Ansible's `--diff` emit. `diff -r dirA dirB` compares trees recursively, listing per-file diffs and "Only in" entries. The **exit code** is the scripting key: `0` identical, `1` differences, `2` trouble; `-q` ("brief") prints just "Files differ" for fast checks.

```
diff a.txt b.txt        → normal format (< old, > new)
diff -u a.txt b.txt     → unified (-/+ with @@ context)
diff -r dir1 dir2       → recursive tree comparison
diff -q a.txt b.txt     → "Files a and b differ" (or nothing)
echo $?                 → 0 same, 1 differ, 2 error
```

> **Why this matters:** Config drift is everywhere. Unified diff is the lingua franca of changes; the exit code lets scripts and playbooks gate on "did anything change?"

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `diff` | Show differences | normal `<`/`>` format |
| `diff -u` | Unified format | `-/+`, `@@` hunks |
| `diff -r` | Recurse directories | with `-q` for summary |
| `diff -q` | Brief (differ or not) | scripting |
| `diff -y` | Side-by-side | `--suppress-common-lines` |
| `$?` | Exit code | 0/1/2 |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build a sandbox with two versions of a file and two directory trees.

> Run this block **once** before Task 1. It defines a single sandbox root
> (`LAB_ROOT`) that every file in this lab lives under, so the Teardown
> section can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-23
mkdir -p "$LAB_ROOT/d1" "$LAB_ROOT/d2"
cd "$LAB_ROOT"
printf 'alpha\nbeta\ngamma\n'   > old.txt
printf 'alpha\nBETA\ngamma\ndelta\n' > new.txt
printf 'same\n' > d1/keep.txt
printf 'same\n' > d2/keep.txt
printf 'only-in-d1\n' > d1/extra.txt
printf 'v1\n' > d1/changed.txt
printf 'v2\n' > d2/changed.txt
ls d1 d2
echo "exit was: $?"
```

**Expected output:**

```
d1:
changed.txt
extra.txt
keep.txt

d2:
changed.txt
keep.txt
exit was: 0
```

---

## TASK 1 of 2 — Normal and unified diffs

**In plain English:** We compare two file versions in normal format, then in unified format.

---

### Step 1 of 2 — Compare with normal `diff`

**In plain English:** We diff the old and new file versions and read the `<`/`>` output.

```bash
cd "$LAB_ROOT"
diff old.txt new.txt
echo "exit code: $?"
```

**Expected output:**

```
2c2
< beta
---
> BETA
3a4
> delta
exit code: 1
```

**Line-by-line breakdown:**

- `2c2` → Line 2 *changed*; `<` shows the old line, `>` the new.
- `3a4` → After line 3, *add* line 4 (`delta`).
- `exit code: 1` → `diff` returns 1 when files differ.

**New words in this step:**

- **`diff`** — report the edits (a/c/d) that turn the first file into the second.
- **exit code 1** — files differ (0 = same, 2 = error).

---

### Step 2 of 2 — Unified format with `-u`

**In plain English:** We produce the unified diff used by patches and version control.

```bash
cd "$LAB_ROOT"
diff -u old.txt new.txt
echo "exit code: $?"
```

**Expected output:**

```
--- old.txt	2024-...
+++ new.txt	2024-...
@@ -1,3 +1,4 @@
 alpha
-beta
+BETA
 gamma
+delta
exit code: 1
```

**Line-by-line breakdown:**

- `@@ -1,3 +1,4 @@` → Hunk header: lines 1–3 of old map to 1–4 of new.
- `-beta` / `+BETA` → The removed and added lines; unchanged lines have a leading space.
- This is exactly the format `git diff` and `patch` consume.

**New words in this step:**

- **unified diff (`-u`)** — `-`/`+` change lines with `@@` context; the standard patch format.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| normal `c`/`a`/`d` | change/add/delete | `<` old, `>` new |
| `-u` unified | patch format | `-`/`+` not `<`/`>` |
| exit code | 0/1/2 | 1 means "differ", not error |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Whole file shows as changed | CRLF vs LF | Normalize line endings first |
| Confusing `<`/`>` | Normal format | Use `-u` for clarity |

---

## TASK 2 of 2 — Recursive and scriptable diffs

**In plain English:** We compare whole directory trees, then use the brief mode and exit code.

---

### Step 1 of 2 — Recurse with `diff -r`

**In plain English:** We compare the two directory trees and read both file diffs and "Only in" notices.

```bash
cd "$LAB_ROOT"
diff -r d1 d2
echo "exit code: $?"
```

**Expected output:**

```
diff -r d1/changed.txt d2/changed.txt
1c1
< v1
---
> v2
Only in d1: extra.txt
exit code: 1
```

**Line-by-line breakdown:**

- `diff -r d1 d2` → Walk both trees; for each file present in both, show the diff.
- `Only in d1: extra.txt` → A file present in one tree but not the other.

**New words in this step:**

- **`diff -r`** — recursively compare two directory trees.

---

### Step 2 of 2 — Brief mode and exit code

**In plain English:** We use `-q` for a one-line answer and read the exit code for scripting.

```bash
cd "$LAB_ROOT"
diff -q old.txt new.txt
diff -q d1/keep.txt d2/keep.txt && echo "keep.txt identical"
diff -q old.txt new.txt > /tmp/lab-23/diff-summary.txt; echo "saved rc: $?"
```

**Expected output:**

```
Files old.txt and new.txt differ
keep.txt identical
saved rc: 1
```

**Line-by-line breakdown:**

- `diff -q old.txt new.txt` → Brief mode: just states they differ, no detail.
- `diff -q ... && echo "identical"` → Exit 0 (identical) triggers the `&&` branch.
- `> diff-summary.txt; echo "saved rc: $?"` → Save the summary and capture the exit code for a script.

**New words in this step:**

- **`diff -q`** — brief mode: report only whether files differ.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `-r` | recurse trees | shows "Only in" too |
| `-q` | brief | no hunk detail |
| `$?` gating | 0 same / 1 differ | scriptable |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Too much output | Full recursive diff | Add `-q` for summary |
| Script treats 1 as failure | Misread exit code | 1 = "differ", handle explicitly |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Compare with normal `diff`
- [ ] Task 1 · Step 2 — Unified format with `-u`
- [ ] Task 2 · Step 1 — Recurse with `diff -r`
- [ ] Task 2 · Step 2 — Brief mode and exit code
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

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
| Treating exit 1 as error | Script aborts on a normal diff | Handle 1 = "differ" |
| Reading normal format | Confusing `<`/`>` | Prefer `-u` |
| CRLF noise | Everything "changed" | Normalize endings |

---

## 📌 Exam Strategy

Use `diff -u` to read and share changes, `diff -r` to compare trees, and `diff -q`/`$?` to script "did it change?" Remember exit 1 means *differences*, not failure — the single most common scripting mistake with `diff`.

- `-u` is the universal patch format (git, patch, Ansible).
- `-r` plus `-q` summarizes tree drift fast.
- Exit code: 0 identical, 1 differ, 2 error.

---

## 🔗 Related Labs

- [Lab 23b — Comparing File Differences (Ansible)](../lab-23b-diff-comparing-files-ansible/) — `--check --diff` preview mode
- [Lab 23c — Comparing File Differences (Verify)](../lab-23c-diff-comparing-files-verify/) — prove identity and drift
- [Lab 24a — Stream Editing with sed (RHCSA)](../lab-24a-sed-stream-editor-rhcsa/) — apply the changes a diff describes

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
