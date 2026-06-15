# Lab 18a: Locate Command Documentation (RHCSA) — `rpm -qf`, `rpm -qd`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 18a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (finding which package owns a file and where its docs live), RHCE EX294 (package provenance), SRE/DevOps (auditing installed software)  
**Prerequisite:** [Lab 17c](../lab-17c-find-save-config-files-verify/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `find /usr/share/doc` | _Task 2 · Step 2_ |
| A2 | `>` (save output) | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `rpm -qf` (which package owns a file) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `rpm -ql` (list package files) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `rpm -qd` (package documentation) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `rpm -qi` (package info) | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

When you find a binary but do not know its package or where to read about it, RPM answers. You will discover which package owns a command with `rpm -qf`, list that package's files with `rpm -ql`, read its bundled documentation paths with `rpm -qd`, and confirm those docs exist under `/usr/share/doc`. This is the offline "where are the docs?" workflow for an exam box with no internet.

---

## 🧠 Concept

Every file installed from an RPM is tracked in the RPM database. `rpm -qf PATH` reverse-maps a file to its owning package. `rpm -ql PKG` lists all files a package installed; `rpm -qd PKG` lists just the documentation files (man pages, READMEs, licenses under `/usr/share/doc/PKG`); `rpm -qi PKG` prints metadata (version, summary, license). Combined, they let you go from "what is this command?" to "read its docs" without leaving the shell.

```
rpm -qf $(which ls)   → coreutils-9.x
rpm -ql coreutils     → /usr/bin/ls, /usr/bin/cp, ...
rpm -qd coreutils     → /usr/share/man/man1/ls.1.gz, ...
rpm -qi coreutils     → Name, Version, License, Summary
```

> **Why this matters:** On a locked-down exam box, `rpm -qd` and `/usr/share/doc` are your only documentation. Knowing how to trace a command to its package and its docs is a core RHCSA self-rescue skill.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `rpm -qf PATH` | Which package owns a file | feed it `$(which cmd)` |
| `rpm -ql PKG` | List all files in a package | `-l` = list |
| `rpm -qd PKG` | List a package's doc files | `-d` = documentation |
| `rpm -qi PKG` | Package metadata | name, version, license, summary |
| `find /usr/share/doc` | Browse on-disk docs | per-package doc directories |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make a sandbox to save our findings into; the data we query lives in the system RPM database.

> Run this block **once** before Task 1. It defines a single sandbox root
> (`LAB_ROOT`) that every file in this lab lives under, so the Teardown
> section can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-18
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"
which ls cp
echo "exit was: $?"
```

**Expected output:**

```
/usr/bin/ls
/usr/bin/cp
exit was: 0
```

---

## TASK 1 of 2 — Trace a command to its package

**In plain English:** We find which package owns `ls`, then list that package's files.

---

### Step 1 of 2 — Find the owning package with `rpm -qf`

**In plain English:** We resolve the `ls` binary's full path and ask RPM which package installed it.

```bash
cd "$LAB_ROOT"
rpm -qf "$(which ls)"
rpm -qf "$(which ls)" > owner.txt
cat owner.txt
echo "exit was: $?"
```

**Expected output:**

```
coreutils-9.0-...el9.x86_64
coreutils-9.0-...el9.x86_64
exit was: 0
```

**Line-by-line breakdown:**

- `rpm -qf "$(which ls)"` → `which ls` gives the path; `rpm -qf` reverse-maps that file to its owning package.
- `... > owner.txt` → Save the answer for later reference.

**New words in this step:**

- **`rpm -qf`** — query which package owns (provides) a given file.

---

### Step 2 of 2 — List the package's files with `rpm -ql`

**In plain English:** We list every file the owning package installed and save the binaries.

```bash
cd "$LAB_ROOT"
rpm -ql coreutils | grep '/bin/' | head -n 5
rpm -ql coreutils > coreutils-files.txt
wc -l coreutils-files.txt
echo "exit was: $?"
```

**Expected output:**

```
/usr/bin/[
/usr/bin/b2sum
/usr/bin/base32
/usr/bin/base64
/usr/bin/basename
... coreutils-files.txt
exit was: 0
```

**Line-by-line breakdown:**

- `rpm -ql coreutils | grep '/bin/' | head -n 5` → List the package's files, filter to binaries, show a few.
- `rpm -ql coreutils > coreutils-files.txt` → Save the full file list; `wc -l` shows how many files the package owns.

**New words in this step:**

- **`rpm -ql`** — list all files contained in a package.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `rpm -qf` | file → package | needs a real path (`$(which)`) |
| `rpm -ql` | package → files | huge for big packages — filter it |
| `which` | resolve a binary path | misses shell builtins |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `file ... not owned by any package` | Not from an RPM | It was built/copied manually |
| `which: no ls` | Unusual PATH | Use the full `/usr/bin/ls` |

---

## TASK 2 of 2 — Find and read the documentation

**In plain English:** We list a package's docs with `rpm -qd`, read its metadata, and confirm the docs exist on disk.

---

### Step 1 of 2 — List docs with `rpm -qd` and info with `rpm -qi`

**In plain English:** We show the documentation files a package ships and its metadata summary.

```bash
cd "$LAB_ROOT"
rpm -qd coreutils | head -n 5
rpm -qi coreutils | grep -E '^(Name|Version|License|Summary)'
echo "exit was: $?"
```

**Expected output:**

```
/usr/share/man/man1/ls.1.gz
/usr/share/man/man1/cp.1.gz
...
Name        : coreutils
Version     : 9.0
License     : GPLv3+
Summary     : A set of basic GNU tools ...
exit was: 0
```

**Line-by-line breakdown:**

- `rpm -qd coreutils | head -n 5` → `-d` lists only documentation files (man pages, READMEs); show a few.
- `rpm -qi coreutils | grep -E '^(Name|Version|License|Summary)'` → Print key metadata fields.

**New words in this step:**

- **`rpm -qd`** — list a package's documentation files.
- **`rpm -qi`** — print a package's metadata (info).

---

### Step 2 of 2 — Confirm docs on disk with `find /usr/share/doc`

**In plain English:** We browse the package's documentation directory under `/usr/share/doc`.

```bash
cd "$LAB_ROOT"
find /usr/share/doc -maxdepth 1 -type d -name 'coreutils*'
ls /usr/share/doc/coreutils* 2>/dev/null | head -n 5
echo "exit was: $?"
```

**Expected output:**

```
/usr/share/doc/coreutils
README
THANKS
...
exit was: 0
```

**Line-by-line breakdown:**

- `find /usr/share/doc -maxdepth 1 -type d -name 'coreutils*'` → Locate the package's doc directory.
- `ls /usr/share/doc/coreutils* 2>/dev/null | head -n 5` → List a few of the docs inside; `2>/dev/null` hides noise if the dir is absent.

**New words in this step:**

- **`/usr/share/doc`** — the standard tree where packages drop READMEs, changelogs, and licenses.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `rpm -qd` | doc files only | some minimal packages ship none |
| `rpm -qi` | metadata | license/version live here |
| `/usr/share/doc` | on-disk docs | not every package populates it |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `rpm -qd` empty | Package ships no docs | Try `man cmd` or `rpm -ql | grep doc` |
| No `/usr/share/doc/PKG` | `nodocs` install option | Reinstall without `--excludedocs` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Find the owning package with `rpm -qf`
- [ ] Task 1 · Step 2 — List the package's files with `rpm -ql`
- [ ] Task 2 · Step 1 — List docs with `rpm -qd` and info with `rpm -qi`
- [ ] Task 2 · Step 2 — Confirm docs on disk with `find /usr/share/doc`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab only queried the RPM database — it changed **no** system state.

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
| `rpm -qf ls` (no path) | "not owned" / wrong | Use `$(which ls)` full path |
| Expecting docs for every pkg | Empty `rpm -qd` | Fall back to `man`/`--help` |
| Confusing `-qi` and `-qd` | Wrong output | `-i` info, `-d` docs |

---

## 📌 Exam Strategy

When you cannot recall a command, trace it: `rpm -qf $(which cmd)` for the package, `rpm -qd` for its docs, then read `/usr/share/doc/PKG` or its man page. This offline chain works on any exam box with no network.

- `rpm -qf $(which cmd)` is the canonical "what package is this?" combo.
- `rpm -qd` points straight at the docs to read.
- `/usr/share/doc` is your offline library.

---

## 🔗 Related Labs

- [Lab 18b — Locate Command Documentation (Ansible)](../lab-18b-locate-command-docs-ansible/) — `package_facts` and `rpm -q*` via Ansible
- [Lab 18c — Locate Command Documentation (Verify)](../lab-18c-locate-command-docs-verify/) — prove ownership and doc presence
- [Lab 28a — Exploring Manual Pages (RHCSA)](../lab-28a-man-pages-rhcsa/) — reading the man pages you just located

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
