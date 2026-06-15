# Lab 18c: Locate Command Documentation (Verify) — `rpm -qf`, `rpm -V`, `test -e`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 18c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving file→package mapping and doc presence), SRE (package integrity audits), DevOps (supply-chain verification)  
**Prerequisite:** [Lab 18a](../lab-18a-locate-command-docs-rhcsa/) and [Lab 18b](../lab-18b-locate-command-docs-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `rpm -qf` | _Task 1 · Step 1_ |
| A2 | `test -e` | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `rpm -V` (verify integrity) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N2 | `rpm -qf --qf` (query format) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `rpm -qd | xargs test` doc check | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `man -w` (man page path) | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Take the auditor's seat: prove a command maps to the expected package, that the package is unmodified, and that its documentation actually exists. You will resolve ownership with a custom `rpm -qf` query format, verify integrity with `rpm -V`, confirm every listed doc exists on disk, and locate the man page with `man -w`. These are the trust checks before relying on a tool or its docs.

---

## 🧠 Concept

Documentation verification has three layers. **Provenance**: `rpm -qf` confirms which package owns the binary; `--qf '%{NAME}\n'` trims the answer to just the name for clean assertions. **Integrity**: `rpm -V PKG` compares installed files against the package manifest and prints a line *only* for changed files — empty output means pristine. **Doc existence**: every path from `rpm -qd` should pass `test -e`, and `man -w cmd` prints the man page's file path, proving the docs are readable.

```
rpm -qf --qf '%{NAME}\n' $(which ls) → coreutils
rpm -V coreutils → (empty = unmodified)
rpm -qd coreutils | while read d; do test -e "$d"; done → all exist
man -w ls → /usr/share/man/man1/ls.1.gz
```

> **Why this matters:** Trusting a binary or doc that was tampered with is a security failure. `rpm -V` is the offline integrity check, and the doc-existence loop proves what you will read is actually there.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `rpm -qf` | File → package | `--qf '%{NAME}\n'` for just the name |
| `rpm -V PKG` | Verify files vs manifest | empty output = unmodified |
| `rpm -qd PKG` | List doc files | feed into existence checks |
| `test -e` | Path exists | per-doc verification |
| `man -w` | Print man page file path | proves the page is installed |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make a sandbox for notes; the audit targets the live RPM database and system docs.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-18
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"
which ls
echo "exit was: $?"
```

**Expected output:**

```
/usr/bin/ls
exit was: 0
```

---

## TASK 1 of 2 — Prove provenance and integrity

**In plain English:** We confirm the package name owning `ls` and verify the package is unmodified.

---

### Step 1 of 2 — Assert the owning package name

**In plain English:** We resolve `ls` to its package name and assert it is `coreutils`.

```bash
cd "$LAB_ROOT"
OWNER=$(rpm -qf --qf '%{NAME}\n' "$(which ls)")
echo "owner: $OWNER"
[ "$OWNER" = "coreutils" ] && echo "OWNER OK" || echo "OWNER WRONG (FAIL)"
```

**Expected output:**

```
owner: coreutils
OWNER OK
```

**Line-by-line breakdown:**

- `OWNER=$(rpm -qf --qf '%{NAME}\n' "$(which ls)")` → `--qf` formats the answer to just the package name, no version noise.
- `[ "$OWNER" = "coreutils" ]` → Assert the expected package owns the binary.

**New words in this step:**

- **`--qf` (query format)** — a template controlling exactly which RPM fields print.

---

### Step 2 of 2 — Verify integrity with `rpm -V`

**In plain English:** We check the package's files against its manifest; no output means nothing was tampered with.

```bash
cd "$LAB_ROOT"
rpm -V coreutils
[ -z "$(rpm -V coreutils)" ] && echo "PACKAGE PRISTINE (OK)" || echo "FILES MODIFIED (review)"
echo "exit was: $?"
```

**Expected output:**

```
PACKAGE PRISTINE (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `rpm -V coreutils` → Compare installed files to the manifest; it prints a line only for files that differ.
- `[ -z "$(rpm -V coreutils)" ]` → Empty output means the package is unmodified — the OK branch fires.

**New words in this step:**

- **`rpm -V`** — verify a package's installed files against its recorded checksums, sizes, and modes.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `rpm -qf --qf` | clean owner name | bare `-qf` includes version |
| `rpm -V` | integrity check | output means a file changed |
| empty `-V` | pristine | config files may legitimately show |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `rpm -V` shows lines | A file changed (often a config) | Inspect the flags; configs (`c`) are normal |
| Owner wrong | Binary not from that package | Re-check with `rpm -qf $(which cmd)` |

---

## TASK 2 of 2 — Prove the docs exist

**In plain English:** We confirm every listed doc file exists and locate the man page.

---

### Step 1 of 2 — Check every doc path exists

**In plain English:** We loop the package's doc list and assert each file is present.

```bash
cd "$LAB_ROOT"
MISSING=0
while read -r d; do
  test -e "$d" || { echo "MISSING: $d"; MISSING=$((MISSING+1)); }
done < <(rpm -qd coreutils)
[ "$MISSING" -eq 0 ] && echo "ALL DOCS PRESENT (OK)" || echo "$MISSING MISSING (FAIL)"
```

**Expected output:**

```
ALL DOCS PRESENT (OK)
```

**Line-by-line breakdown:**

- `while read -r d; do ... done < <(rpm -qd coreutils)` → Iterate every documentation path the package claims.
- `test -e "$d"` → Assert each one exists; missing files increment the counter.
- `[ "$MISSING" -eq 0 ]` → Zero missing means the docs are all installed.

**New words in this step:**

- **process substitution `<(...)`** — feed a command's output as a file to `read`.

---

### Step 2 of 2 — Locate the man page with `man -w`

**In plain English:** We print the man page's file path to prove it is installed and readable.

```bash
cd "$LAB_ROOT"
man -w ls
man -w ls | grep -q 'ls' && echo "MAN PAGE FOUND (OK)" || echo "NO MAN PAGE (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
/usr/share/man/man1/ls.1.gz
MAN PAGE FOUND (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `man -w ls` → `-w` ("where") prints the man page file path instead of opening it.
- `... | grep -q 'ls'` → Assert a path was returned, proving the page exists.

**New words in this step:**

- **`man -w`** — report the file path of a man page without displaying it.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| doc existence loop | proves docs present | `--excludedocs` installs skip docs |
| `man -w` | man page path | empty if no page exists |
| `<(...)` | feed cmd as file | bash-only, not POSIX `sh` |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `MISSING:` lines | Docs excluded at install | Reinstall without `--excludedocs` |
| `man -w` empty | No man page for that command | Try `cmd --help` instead |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Assert the owning package name
- [ ] Task 1 · Step 2 — Verify integrity with `rpm -V`
- [ ] Task 2 · Step 1 — Check every doc path exists
- [ ] Task 2 · Step 2 — Locate the man page with `man -w`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-18
```

**Expected output:**

```
✅ Removed /tmp/lab-18 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Ignoring `rpm -V` output | Tampered file unnoticed | Read every `-V` line |
| Assuming docs always exist | Loop finds missing files | Reinstall without `--excludedocs` |
| `<(...)` in `sh` | Syntax error | Run under bash |

---

## 📌 Exam Strategy

Trust-check a command in three moves: `rpm -qf` for provenance, `rpm -V` for integrity, and a doc-existence loop plus `man -w` for documentation. An empty `rpm -V` and present docs mean the tool and its manual are safe to rely on.

- Empty `rpm -V` is the "package is pristine" signal.
- `man -w` proves a page exists before you try to read it.
- Verify provenance before trusting any unfamiliar binary.

---

## 🔗 Related Labs

- [Lab 18a — Locate Command Documentation (RHCSA)](../lab-18a-locate-command-docs-rhcsa/) — the discovery this audits
- [Lab 18b — Locate Command Documentation (Ansible)](../lab-18b-locate-command-docs-ansible/) — the playbook output you verify
- [Lab 28c — Exploring Manual Pages (Verify)](../lab-28c-man-pages-verify/) — deeper man-page verification

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
