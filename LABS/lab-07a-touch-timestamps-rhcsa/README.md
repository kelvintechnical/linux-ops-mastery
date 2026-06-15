# Lab 07a: Touch Timestamps (RHCSA) — `touch`, `stat`

**Series:** linux-ops-mastery — Essential Tools & File Operations · **Lab 07a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (setting/reading file times, `find` by age), SRE (log rotation and freshness checks), DevOps (build-artifact timestamp control)  
**Prerequisite:** [Lab 06c](../lab-06c-listing-files-selinux-verify/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `touch` | _Task 1 · Step 1_ |
| A2 | `stat` | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `touch -t` / `touch -d` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `stat -c %x/%y/%z` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `touch -r` / `touch -a` / `touch -m` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `find -mtime` / `-mmin` / `-newer` | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Take full control of the three timestamps every file carries and learn to find files by age. You will create a file, force a specific access/modify time with `touch -t`/`-d`, read all three times with `stat`, copy one file's times onto another with `touch -r`, and locate files by modification age with `find -mtime`/`-mmin`/`-newer` — the exact toolkit for log hygiene and "find what changed since" tasks.

---

## 🧠 Concept

Every file has three times: **atime** (last read), **mtime** (last content change), and **ctime** (last inode/metadata change — not creatable by `touch`). `touch` updates atime and mtime to *now* by default, or to a chosen moment with `-t [[CC]YY]MMDDhhmm[.ss]` or the friendlier `-d "string"`. `-a` touches only atime, `-m` only mtime, and `-r FILE` copies another file's times. `stat` reads them: `%x` atime, `%y` mtime, `%z` ctime. `find` then searches by mtime in days (`-mtime`), minutes (`-mmin`), or relative to another file (`-newer`).

```
touch -t 202601011200 f   → set atime+mtime to 2026-01-01 12:00
stat -c '%x|%y|%z' f      → atime | mtime | ctime
touch -r ref f            → copy ref's atime+mtime onto f
find . -mmin -5           → files modified in the last 5 minutes
```

> **Why this matters:** Log rotation, backup freshness, and "what changed in the last hour" incident triage all hinge on reading and setting times correctly. `ctime` cannot be forced — knowing that prevents a classic exam misstep.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `touch` | Create a file or bump its times to now | no flag = set atime+mtime to now |
| `touch -t` / `-d` | Set a specific time | `-t CCYYMMDDhhmm.ss`; `-d "2026-01-01 12:00"` |
| `touch -a` / `-m` / `-r` | Set atime only / mtime only / copy from ref | `-r FILE` mirrors another file's times |
| `stat -c` | Print chosen metadata | `%x` atime, `%y` mtime, `%z` ctime |
| `find -mtime/-mmin/-newer` | Find by age | `-N` newer than, `+N` older than, `-newer F` |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build a sandbox with a couple of files so we have something to time-stamp and search.

> Run this block **once** before Task 1. It defines a single sandbox root
> (`LAB_ROOT`) that every file in this lab lives under, so the Teardown
> section can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-07
mkdir -p "$LAB_ROOT/logs"
cd "$LAB_ROOT"
echo "entry" > logs/app.log
echo "ref"   > logs/reference.log
ls -l logs
echo "exit was: $?"
```

**Expected output:**

```
-rw-r--r--. 1 root root 6 Jun 15 18:30 app.log
-rw-r--r--. 1 root root 4 Jun 15 18:30 reference.log
exit was: 0
```

---

## TASK 1 of 2 — Set and read timestamps

**In plain English:** We force a known time onto a file with `touch -t`, then read all three timestamps back with `stat`.

---

### Step 1 of 2 — Force a specific time with `touch -t` and `-d`

**In plain English:** We set one file's access and modify times to a fixed point in the past two different ways.

```bash
cd "$LAB_ROOT"
touch -t 202601011200.00 logs/app.log
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

**Line-by-line breakdown:**

- `touch -t 202601011200.00 logs/app.log` → Set atime+mtime to `2026-01-01 12:00:00`; `-t` takes the compact `CCYYMMDDhhmm.ss` form.
- `touch -d "2025-12-25 09:30:00" logs/reference.log` → Same idea with a human-readable date string via `-d`.
- `ls -l --time-style=long-iso logs` → Show the mtimes in ISO format to confirm both stuck.

**New words in this step:**

- **mtime** — the last time a file's *contents* changed; what `ls -l` shows by default.
- **`-t` time format** — `CCYYMMDDhhmm.ss`, e.g. `202601011200.00`.

---

### Step 2 of 2 — Read all three times with `stat`

**In plain English:** We print the access, modify, and change times of a file using `stat` format codes.

```bash
cd "$LAB_ROOT"
stat -c 'atime=%x' logs/app.log
stat -c 'mtime=%y' logs/app.log
stat -c 'ctime=%z' logs/app.log
echo "exit was: $?"
```

**Expected output:**

```
atime=2026-01-01 12:00:00.000000000 -0500
mtime=2026-01-01 12:00:00.000000000 -0500
ctime=2026-06-15 18:31:02.000000000 -0400
```

**Line-by-line breakdown:**

- `stat -c 'atime=%x'` → `%x` is the human-readable access time.
- `stat -c 'mtime=%y'` → `%y` is the modify time (matches what we set).
- `stat -c 'ctime=%z'` → `%z` is the change time; note it is *now*, because `touch` updated the inode — `ctime` cannot be set to the past.

**New words in this step:**

- **atime / ctime** — last read time; and last inode/metadata change time (uncontrollable by `touch`).

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `touch -t`/`-d` | set atime+mtime | cannot set `ctime` — it tracks inode changes |
| `stat %x/%y/%z` | read a/m/c times | `%z` is ctime, not "creation" time |
| default `touch` | sets times to now | also creates the file if missing |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `invalid date format` | Wrong `-t` layout | Use `CCYYMMDDhhmm.ss` exactly |
| `ctime` won't go back | `ctime` is inode-tracked | Accept it; only a/mtime are settable |

---

## TASK 2 of 2 — Mirror times and find by age

**In plain English:** We copy one file's times onto another with `touch -r`, then locate files by modification age with `find`.

---

### Step 1 of 2 — Copy times with `touch -r`, set one with `-a`/`-m`

**In plain English:** We mirror the reference file's timestamps onto a new file, then bump only the mtime of another.

```bash
cd "$LAB_ROOT"
touch newfile.log
touch -r logs/reference.log newfile.log
touch -m -d "2026-02-02 02:02:02" logs/app.log
stat -c '%y %n' newfile.log logs/app.log
echo "exit was: $?"
```

**Expected output:**

```
2025-12-25 09:30:00.000000000 -0500 newfile.log
2026-02-02 02:02:02.000000000 -0500 logs/app.log
```

**Line-by-line breakdown:**

- `touch -r logs/reference.log newfile.log` → Copy reference.log's atime+mtime onto newfile.log; `-r` means "reference."
- `touch -m -d "..." logs/app.log` → `-m` changes only the mtime to the given date, leaving atime alone.
- `stat -c '%y %n' ...` → Print the mtime and name of both files to confirm.

**New words in this step:**

- **`touch -r`** — set a file's times to match a reference file's times.

---

### Step 2 of 2 — Find files by age with `find`

**In plain English:** We search for files modified recently with `-mmin`, older than a threshold with `-mtime`, and newer than a reference with `-newer`.

```bash
cd "$LAB_ROOT"
touch fresh.log
find . -mmin -5 -type f
find . -mtime +30 -type f
find . -newer logs/reference.log -type f
echo "exit was: $?"
```

**Expected output:**

```
./fresh.log
./logs/reference.log
./fresh.log
./logs/app.log
exit was: 0
```

**Line-by-line breakdown:**

- `find . -mmin -5 -type f` → Files whose mtime is within the last 5 minutes; `-5` means "less than 5 ago."
- `find . -mtime +30 -type f` → Files older than 30 days; `+30` means "more than 30 days ago" (reference.log at Dec 25 qualifies).
- `find . -newer logs/reference.log -type f` → Files modified more recently than reference.log.

**New words in this step:**

- **`-mmin`/`-mtime`** — find by modify age in minutes / days; `-N` = within, `+N` = older than.
- **`-newer`** — compare mtime against another file rather than a fixed age.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `touch -r` | mirror times | copies a+m, not ctime |
| `find -mtime +N` | older than N days | `+N`/`-N`/`N` are three different windows |
| `find -newer` | relative to a file | uses mtime, not ctime |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `find` returns nothing | Wrong sign on `-mtime` | `+N` older, `-N` newer, `N` exact day |
| `-newer` matches too much | Reference file is very old | Pick a recent reference |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Force a specific time with `touch -t` and `-d`
- [ ] Task 1 · Step 2 — Read all three times with `stat`
- [ ] Task 2 · Step 1 — Copy times with `touch -r`, set one with `-a`/`-m`
- [ ] Task 2 · Step 2 — Find files by age with `find`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

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
| Expecting to set `ctime` | `%z` stays "now" | Only atime/mtime are settable |
| Wrong `-mtime` sign | `find` misses files | `+N` older, `-N` within, `N` that exact day |
| Confusing `%z` with creation | Misreads ctime | `%z` is metadata-change time, not birth |

---

## 📌 Exam Strategy

Timestamp tasks show up as "make this file look modified at TIME" or "find files changed in the last N." Use `touch -d`/`-t` to set, `stat -c %y` to confirm, and `find -mmin`/`-mtime`/`-newer` to locate. Remember `ctime` is off-limits to `touch`.

- `touch -d "natural language"` is faster than the `-t` digit string.
- `find -newer ref` beats guessing day counts when you have a reference file.
- Confirm every set with `stat` before moving on.

---

## 🔗 Related Labs

- [Lab 07b — Touch Timestamps (Ansible)](../lab-07b-touch-timestamps-ansible/) — `ansible.builtin.file` with `modification_time`/`access_time`
- [Lab 07c — Touch Timestamps (Verify)](../lab-07c-touch-timestamps-verify/) — prove the times with `stat` and `find`
- [Lab 14a — Searching with find (RHCSA)](../lab-14a-searching-with-find-rhcsa/) — deeper `find` predicates

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
