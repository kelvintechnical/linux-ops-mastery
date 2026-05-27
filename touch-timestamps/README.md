# Lab 07: Creating Empty Files and Timestamps — `touch`, `stat`, `find -mtime`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Career arcs covered:** RHCSA EX200 (file creation, log rotation triggers, sentinel files), RHCE EX294 (`ansible.builtin.file: state=touch`, `modification_time:`, `access_time:`), CKA (sentinel files for liveness probes), RHCA — RH342 (forensic mtime/ctime/atime analysis)
- **Prerequisite:** Lab 00 (Ansible control node) + Lab 06 (`ls -l`, `ls -lZ`)
- **Time Estimate:** 30–45 minutes
- **Tasks:** 5 (ADHD 3-1-1 spec — 3 RHCSA + 1 Ansible + 1 Verification capstone)
- **Practice Directory (lab-wide rotation #07):** `/var/log`
- **Sandbox:** `/tmp/touch-lab`
- **Traps rehearsed this lab:** **T07** (Confusing `ctime` (inode change) with `mtime` (data change) — ctime updates on `chmod`/`chown`, mtime only on data writes) · **T08** (`touch -t` requires `[[CC]YY]MMDDhhmm[.ss]` — wrong format silently picks current year/century)

> **This lab's practice directory is: `/var/log`** — every task references it in at least two commands. We **read** `/var/log` only; we **write** only inside `/tmp/touch-lab`.

---

## 🖥️ LAB HEADER BLOCK — run this FIRST

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T07 T08"
echo "📁  PRACTICE DIR: /var/log"
echo ""
echo "💡 /var/log freshest 3 files:"
ls -lt /var/log 2>/dev/null | head -4
```

> **STOP — paste header output before running setup.**

---

## 🎯 Objective

Create empty files, manipulate their three timestamps (atime/mtime/ctime), and use those timestamps to find files. By the end you will:

- Know which timestamp updates on each operation (`cat` reads atime, `vi` writes mtime, `chmod` writes ctime)
- Use `touch -t`, `touch -d`, `touch -r`, `touch -a`, `touch -m` like a senior admin
- Run `find -mtime`, `find -mmin`, `find -newer` to locate files by age
- Write an Ansible playbook that uses `ansible.builtin.file: state=touch` with explicit `modification_time:`
- Verify with `stat -c '%y %x %z'` that the timestamps match what your playbook claimed

---

## 🛠️ Setup — run once before Task 1

```bash
mkdir -p /tmp/touch-lab
sudo mkdir -p /root/rhcsa_journal/lab07
cd /tmp/touch-lab
echo "lab07 reference content" > reference.txt
stat reference.txt
ls -l /var/log | head -5
```

---

## Task 1 — `touch` to Create + Read Timestamps with `stat`

**Practice directory this task:** `/var/log` (read), `/tmp/touch-lab` (write)

### 🔁 Warm-Up — Commands from Previous Labs

```bash
sudo mkdir -p /root/rhcsa_journal/lab07/task1
cd /tmp/touch-lab
date -Is | sudo tee /root/rhcsa_journal/lab07/task1/start.txt
ls -lZ reference.txt | sudo tee -a /root/rhcsa_journal/lab07/task1/start.txt
echo "exit was: $?"
```

### Purpose

Create empty files with `touch`, then read all three timestamps (atime, mtime, ctime) using `stat`. Show that re-running `touch` updates mtime/atime but NOT ctime — until you `chmod`, which updates ctime alone.

### Main Command Block

```bash
touch /tmp/touch-lab/a.txt
touch /tmp/touch-lab/b.txt /tmp/touch-lab/c.txt   # multiple at once

# Read all three timestamps
stat /tmp/touch-lab/a.txt
stat -c 'atime=%x' /tmp/touch-lab/a.txt
stat -c 'mtime=%y' /tmp/touch-lab/a.txt
stat -c 'ctime=%z' /tmp/touch-lab/a.txt

# Read a real file's age
stat /var/log/messages 2>/dev/null || stat /var/log/wtmp

# Demonstrate what changes each timestamp
sleep 1
touch /tmp/touch-lab/a.txt          # bumps atime + mtime (NOT ctime alone — but ctime also bumps because metadata changed)
stat -c 'mtime=%y ctime=%z' /tmp/touch-lab/a.txt

sleep 1
chmod 600 /tmp/touch-lab/a.txt      # bumps ctime ONLY (no data write)
stat -c 'mtime=%y ctime=%z' /tmp/touch-lab/a.txt

sleep 1
cat /tmp/touch-lab/a.txt > /dev/null  # bumps atime
stat -c 'atime=%x mtime=%y ctime=%z' /tmp/touch-lab/a.txt

# Capture
{
  echo "=== initial ===";    stat /tmp/touch-lab/a.txt
  echo "=== after touch ==="; touch /tmp/touch-lab/a.txt; stat -c 'mtime=%y ctime=%z' /tmp/touch-lab/a.txt
  echo "=== after chmod ==="; chmod 644 /tmp/touch-lab/a.txt; stat -c 'mtime=%y ctime=%z' /tmp/touch-lab/a.txt
  echo "=== after cat ===";   cat /tmp/touch-lab/a.txt > /dev/null; stat -c 'atime=%x mtime=%y ctime=%z' /tmp/touch-lab/a.txt
} 2>&1 | sudo tee /root/rhcsa_journal/lab07/task1/transcript.txt
```

### Human-Readable Breakdown

A file has **three** timestamps:

| Name | What it tracks | What updates it |
|---|---|---|
| **atime** (access) | Last read | `cat`, `less`, `grep`, `cp` of the file |
| **mtime** (modify) | Last write to data | `echo > file`, `vi :w`, `sed -i` |
| **ctime** (change) | Last metadata change | mtime change + `chmod`, `chown`, `mv`, rename, link |

Critical distinction: **ctime is not creation time**. There is also `btime` / `crtime` (birth time) on some filesystems (`stat -c '%w'` — `-` if unsupported). The "c" in ctime stands for "change" (of inode), not "creation."

`touch` with no args creates the file if it doesn't exist AND updates both atime and mtime to **now**. `chmod` doesn't touch atime/mtime but does bump ctime because the inode (permissions field) changed.

### Reading It Left to Right

`stat -c 'atime=%x mtime=%y ctime=%z' FILE`

- `stat` — file metadata
- `-c FMT` — custom format
- `%x` — atime, human-readable
- `%y` — mtime, human-readable
- `%z` — ctime, human-readable

`touch /tmp/touch-lab/a.txt /tmp/touch-lab/b.txt`

- `touch` — create or update timestamps
- Two paths — `touch` accepts many; each is touched in turn

### The Story

A grader asks: "When was this config file last edited?" — that's mtime. "When did its permissions last change?" — that's ctime. "When was it last read?" — that's atime. Mixing those up is a classic RHCSA mistake; the question literally asks "modified," meaning mtime, but a sloppy answer reports ctime. This task burns the distinction in.

### Expected Output

```
$ stat /tmp/touch-lab/a.txt
  File: /tmp/touch-lab/a.txt
  Size: 0           Blocks: 0          IO Block: 4096   regular empty file
Access: 2026-05-27 15:00:01.234567890 -0400
Modify: 2026-05-27 15:00:01.234567890 -0400
Change: 2026-05-27 15:00:01.234567890 -0400
 Birth: 2026-05-27 15:00:01.234567890 -0400
```

After `chmod 600`:

```
mtime=2026-05-27 15:00:02.xxx -0400 ctime=2026-05-27 15:00:03.xxx -0400
```

Notice ctime > mtime — that's the proof of "ctime bumps on chmod, mtime does not."

### Switches Table

| Switch | Meaning | Why it matters |
|---|---|---|
| `touch FILE` | Create if missing, update atime+mtime to now | The base case |
| `stat FILE` | Print all metadata including all 3 timestamps | RHCSA primary inspection |
| `stat -c %x` | atime | Programmatic compare |
| `stat -c %y` | mtime | Programmatic compare |
| `stat -c %z` | ctime | Programmatic compare |
| `stat -c %w` | btime (creation) | `-` if filesystem doesn't support it |
| `stat -c %Y` | mtime as epoch seconds | Easy arithmetic in scripts |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| atime | Last read |
| mtime | Last data write |
| ctime | Last metadata change (NOT creation) |
| btime/crtime | Actual creation time (filesystem-dependent) |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| **T07** | Confusing ctime with "creation time" | The "c" is **change** of inode; for true creation, use `stat -c '%w'` (btime) |
| Atime drift | Frequent `cat` of a file changes atime — kernel may be mounted with `noatime` and atime won't update | Check `mount \| grep noatime` if atime never moves |

### 🔁 Persistence Check

```bash
test -f /tmp/touch-lab/a.txt && echo "a.txt ok"
test -f /tmp/touch-lab/b.txt && echo "b.txt ok"
test -f /tmp/touch-lab/c.txt && echo "c.txt ok"
grep -c 'mtime=' /root/rhcsa_journal/lab07/task1/transcript.txt
```

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab07/task1/done.txt > /dev/null <<EOF
lab=07 task=1
when=$(date -Is)
practice_dir=/var/log
sandbox=/tmp/touch-lab
files_created=3
transcript=/root/rhcsa_journal/lab07/task1/transcript.txt
EOF
cat /root/rhcsa_journal/lab07/task1/done.txt
```

### 🧹 Cleanup

Leave files in `/tmp/touch-lab` — Task 2 modifies them.

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `Birth: -` in stat output | Filesystem is ext4 with `lazy_itable_init` or XFS without crtime — not a bug |
| Atime never updates | Mount option `noatime` or `relatime` — `mount \| grep /tmp` to verify |

> **STOP — confirm 3 timestamps visible in transcript before Task 2.**

---

## Task 2 — Set Explicit Timestamps with `touch -t`, `touch -d`, `touch -r`

**Practice directory this task:** `/var/log` (read), `/tmp/touch-lab` (write)

### 🔁 Warm-Up — Commands from Previous Labs

```bash
sudo mkdir -p /root/rhcsa_journal/lab07/task2
date -Is | sudo tee /root/rhcsa_journal/lab07/task2/start.txt
stat -c 'mtime=%y' /tmp/touch-lab/a.txt | sudo tee -a /root/rhcsa_journal/lab07/task2/start.txt
echo "exit was: $?"
```

### Purpose

Set timestamps explicitly: backdate a file, sync timestamps from a reference file, set only atime, set only mtime. These are the operations Ansible's `modification_time:` parameter replicates in Task 4.

### Main Command Block

```bash
# touch -t — set both atime+mtime to specific time
# Format: [[CC]YY]MMDDhhmm[.ss]
touch -t 202401151200 /tmp/touch-lab/a.txt
stat -c 'mtime=%y' /tmp/touch-lab/a.txt
# expect: 2024-01-15 12:00:00...

# touch -d — set with a human-readable date string (more forgiving)
touch -d '2025-06-30 09:30:00' /tmp/touch-lab/b.txt
stat -c 'mtime=%y' /tmp/touch-lab/b.txt

# touch -d also accepts relative phrases
touch -d 'yesterday' /tmp/touch-lab/c.txt
stat -c 'mtime=%y' /tmp/touch-lab/c.txt

# touch -r — copy timestamps from another file
touch /tmp/touch-lab/reference.txt
sleep 2
touch /tmp/touch-lab/copy.txt
touch -r /tmp/touch-lab/reference.txt /tmp/touch-lab/copy.txt
stat -c 'ref=%y' /tmp/touch-lab/reference.txt
stat -c 'cpy=%y' /tmp/touch-lab/copy.txt
# expect: ref == cpy

# touch -a — atime only; -m — mtime only
touch -a -d '2020-01-01 00:00:00' /tmp/touch-lab/a.txt
stat -c 'atime=%x mtime=%y' /tmp/touch-lab/a.txt
touch -m -d '2030-12-31 23:59:00' /tmp/touch-lab/a.txt
stat -c 'atime=%x mtime=%y' /tmp/touch-lab/a.txt

# Capture
{
  echo "=== touch -t (backdate to Jan 15 2024) ==="
  touch -t 202401151200 /tmp/touch-lab/a.txt
  stat -c 'mtime=%y' /tmp/touch-lab/a.txt
  echo "=== touch -d (June 30 2025) ==="
  touch -d '2025-06-30 09:30:00' /tmp/touch-lab/b.txt
  stat -c 'mtime=%y' /tmp/touch-lab/b.txt
  echo "=== touch -r (copy from ref) ==="
  touch -r /tmp/touch-lab/reference.txt /tmp/touch-lab/copy.txt
  stat -c 'ref=%y' /tmp/touch-lab/reference.txt
  stat -c 'cpy=%y' /tmp/touch-lab/copy.txt
  echo "=== touch -a / -m split ==="
  touch -a -d '2020-01-01 00:00:00' /tmp/touch-lab/a.txt
  touch -m -d '2030-12-31 23:59:00' /tmp/touch-lab/a.txt
  stat -c 'atime=%x mtime=%y' /tmp/touch-lab/a.txt
} 2>&1 | sudo tee /root/rhcsa_journal/lab07/task2/transcript.txt
```

### Human-Readable Breakdown

`touch -t 202401151200` says "set atime AND mtime to January 15, 2024, 12:00:00 (no seconds)." The format is `[[CC]YY]MMDDhhmm[.ss]` — easy to miss the century: `2401151200` (no century, 2-digit year) means **24-01-15 12:00** which most touches interpret as **2024**, but a malformed string like `20240115` (no time) gets parsed in a surprising way (often current time). Stick with the full 12-digit `[CC]YYMMDDhhmm` to avoid T08.

`touch -d 'STRING'` is more forgiving — it parses anything `date -d` parses: `'2025-06-30'`, `'yesterday'`, `'last week'`, `'2 hours ago'`, ISO 8601 strings, etc.

`touch -r REFERENCE TARGET` copies both atime and mtime from REFERENCE to TARGET. Useful for "make this new file look as old as the existing one."

`touch -a` sets atime only. `touch -m` sets mtime only. Combine with `-d` or `-t`. RHCSA forensic question: "set this file's mtime to last Tuesday without changing atime" → `touch -m -d 'last Tuesday' file`.

### Reading It Left to Right

`touch -t 202401151200 FILE`

- `touch` — create/update
- `-t TIMESPEC` — explicit time, format `[[CC]YY]MMDDhhmm[.ss]`
- `202401151200` — CCYYMMDDhhmm → 2024-01-15 12:00
- `FILE` — target

`touch -r REF TARGET`

- `touch` — create/update
- `-r REF` — use REF's timestamps as the source
- `TARGET` — file to update

### The Story

A common exam-style question: "make `/var/www/html/old.html` appear last-modified on January 1, 2024." Manual answer: `touch -t 202401010000 /var/www/html/old.html`. Done in one command. The RHCE answer in Task 4 will use `ansible.builtin.file: modification_time:` — same effect, declarative shape.

### Expected Output

```
=== touch -t (backdate to Jan 15 2024) ===
mtime=2024-01-15 12:00:00.000000000 -0500

=== touch -d (June 30 2025) ===
mtime=2025-06-30 09:30:00.000000000 -0400

=== touch -r (copy from ref) ===
ref=2026-05-27 15:00:05.xxx -0400
cpy=2026-05-27 15:00:05.xxx -0400

=== touch -a / -m split ===
atime=2020-01-01 00:00:00.000000000 -0500 mtime=2030-12-31 23:59:00.000000000 -0500
```

### Switches Table

| Switch | Meaning | Why it matters |
|---|---|---|
| `-t [[CC]YY]MMDDhhmm[.ss]` | Set timestamp by numeric format | RHCSA classic; T08 is the format trap |
| `-d 'STRING'` | Set by parseable date string | Forgiving; uses `date -d` parser |
| `-r REF` | Use another file's timestamps | "Match this file's age" |
| `-a` | Set atime only | Combine with `-d` or `-t` |
| `-m` | Set mtime only | Combine with `-d` or `-t` |
| `-c` | Don't create if missing | Only update existing files |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| `-t` format | `[[CC]YY]MMDDhhmm[.ss]` — use the full 12-digit form |
| `-d` parser | Any `date -d` string: "yesterday", ISO 8601, "1 hour ago" |
| `-r REF` | Copy timestamps from REF |
| `-a` / `-m` | Atime only / mtime only |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| **T08** | `touch -t 20240115` (no hhmm) silently picks current time | Always include hhmm — `20240115` alone is not a valid `-t` string |
| Century-strip | `touch -t 2401151200` — `24` parsed as year 1924 on some systems | Always include CC — `202401151200` |
| `-r` direction | `touch -r src dst` — order is `r SOURCE TARGET` (not the other way) | Read the man page; remember "r" is reference-from |

### 🔁 Persistence Check

```bash
stat -c '%y' /tmp/touch-lab/a.txt | grep -c '2030-12-31'   # we set mtime to Dec 31 2030
stat -c '%x' /tmp/touch-lab/a.txt | grep -c '2020-01-01'   # we set atime to Jan 1 2020
```

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab07/task2/done.txt > /dev/null <<EOF
lab=07 task=2
when=$(date -Is)
a_mtime=$(stat -c '%y' /tmp/touch-lab/a.txt)
a_atime=$(stat -c '%x' /tmp/touch-lab/a.txt)
b_mtime=$(stat -c '%y' /tmp/touch-lab/b.txt)
EOF
cat /root/rhcsa_journal/lab07/task2/done.txt
```

### 🧹 Cleanup

Leave files; Task 3 uses them.

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `touch: invalid date format` | Re-check the `-t` format; use `-d` instead |
| `-r` says "No such file" | `-r` takes the reference path as its argument — `touch -r REF TARGET` |

> **STOP — confirm mtime/atime are decoupled in done.txt before Task 3.**

---

## Task 3 — `find -mtime`, `find -mmin`, `find -newer`: Use Timestamps to Find Files

**Practice directory this task:** `/var/log` (real-world target), `/tmp/touch-lab` (sandbox)

### 🔁 Warm-Up — Commands from Previous Labs

```bash
sudo mkdir -p /root/rhcsa_journal/lab07/task3
date -Is | sudo tee /root/rhcsa_journal/lab07/task3/start.txt
ls -lt /var/log | head -3 | sudo tee -a /root/rhcsa_journal/lab07/task3/start.txt
echo "exit was: $?"
```

### Purpose

Use `find` to locate files by age. `-mtime N` = exactly N days old. `-mtime +N` = older than N. `-mtime -N` = newer than N. `-mmin` = minutes. `-newer FILE` = newer than FILE's mtime.

### Main Command Block

```bash
# Make 3 sandbox files with known ages
touch -d 'yesterday'      /tmp/touch-lab/yesterday.txt
touch -d '8 days ago'     /tmp/touch-lab/lastweek.txt
touch -d '40 days ago'    /tmp/touch-lab/lastmonth.txt
ls -lt /tmp/touch-lab/ | head

# find by age (days)
find /tmp/touch-lab -type f -mtime -2     # newer than 2 days ago
find /tmp/touch-lab -type f -mtime +7     # older than 7 days
find /tmp/touch-lab -type f -mtime +30    # older than 30 days

# find by minutes
find /tmp/touch-lab -type f -mmin -5      # modified in last 5 minutes
find /tmp/touch-lab -type f -mmin +60     # older than 1 hour

# find newer than a reference file
touch /tmp/touch-lab/now.txt
find /tmp/touch-lab -type f -newer /tmp/touch-lab/lastweek.txt

# Real-world: find log files modified in the last day
find /var/log -maxdepth 1 -type f -mtime -1 2>/dev/null

# Capture
{
  echo "=== -mtime -2 (last 2 days) ===";   find /tmp/touch-lab -type f -mtime -2
  echo "=== -mtime +7 (older than 7 d) ==="; find /tmp/touch-lab -type f -mtime +7
  echo "=== -mtime +30 ===";                find /tmp/touch-lab -type f -mtime +30
  echo "=== -newer lastweek ===";           find /tmp/touch-lab -type f -newer /tmp/touch-lab/lastweek.txt
  echo "=== /var/log -mtime -1 ===";        find /var/log -maxdepth 1 -type f -mtime -1 2>/dev/null | head -5
} 2>&1 | sudo tee /root/rhcsa_journal/lab07/task3/transcript.txt
```

### Human-Readable Breakdown

`find -mtime N` is **"exactly N 24-hour periods ago, rounded toward zero."** That means `-mtime 0` is "less than 24 hours old," `-mtime 1` is "between 24 and 48 hours old," etc. The sign matters:

- `-mtime -N` — modified less than N days ago (newer than N days)
- `-mtime N`  — modified exactly between N and N+1 days ago
- `-mtime +N` — modified MORE than N days ago (older than N days)

That sign convention applies to `-mmin` (minutes), `-atime` (atime in days), `-amin` (atime in minutes), `-ctime`, `-cmin` identically.

`-newer FILE` compares mtime against FILE's mtime — no day-rounding. More precise for "newer than this specific build."

### Reading It Left to Right

`find /tmp/touch-lab -type f -mtime -2`

- `find` — recursive file search
- `/tmp/touch-lab` — starting path
- `-type f` — only regular files (not dirs, not links)
- `-mtime -2` — mtime less than 2 days ago

`find /var/log -maxdepth 1 -type f -mtime -1 2>/dev/null`

- `-maxdepth 1` — don't descend into subdirs (RHCSA-grade noise control)
- `2>/dev/null` — discard permission-denied errors

### The Story

A grader's question: "find all files in `/var/log` modified in the last 24 hours and copy them to `/root/today-logs/`." The answer is `find /var/log -type f -mtime -1 -exec cp {} /root/today-logs/ \;`. You can't write that without owning `-mtime`. Backup scripts, log rotation, and forensic investigation all sit on this primitive.

### Expected Output

```
=== -mtime -2 (last 2 days) ===
/tmp/touch-lab/yesterday.txt
/tmp/touch-lab/now.txt

=== -mtime +7 (older than 7 d) ===
/tmp/touch-lab/lastweek.txt
/tmp/touch-lab/lastmonth.txt

=== -mtime +30 ===
/tmp/touch-lab/lastmonth.txt

=== -newer lastweek ===
/tmp/touch-lab/yesterday.txt
/tmp/touch-lab/now.txt
```

### Switches Table

| Switch | Meaning | Why it matters |
|---|---|---|
| `-mtime N` | exactly N days | rarely used directly; `+N`/`-N` more common |
| `-mtime +N` | older than N days | "find files older than 7 days" → `-mtime +7` |
| `-mtime -N` | newer than N days | "modified today" → `-mtime -1` |
| `-mmin ±N` | minutes equivalent | "in the last 5 minutes" → `-mmin -5` |
| `-newer FILE` | newer than FILE's mtime | exact, no day-rounding |
| `-type f` | files only | excludes directories |
| `-maxdepth N` | don't descend past depth N | noise control |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| `-mtime` sign | `-N` newer than, `N` exactly, `+N` older than |
| `-mmin` | same convention, minutes |
| `-newer FILE` | precise newer-than comparison |
| Day rounding | `-mtime 0` = less than 24h, `-mtime 1` = 24–48h |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| Sign confusion | Writing `-mtime 7` expecting "older than 7 days" (it means exactly between 7 and 8) | Use `+7` for "older," `-7` for "newer" |
| Forgot `-type f` | Get directories in your results | Always specify `-type f` when you want files |

### 🔁 Persistence Check

```bash
grep -c '^/tmp/touch-lab' /root/rhcsa_journal/lab07/task3/transcript.txt
grep -c 'lastmonth.txt'   /root/rhcsa_journal/lab07/task3/transcript.txt
```

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab07/task3/done.txt > /dev/null <<EOF
lab=07 task=3
when=$(date -Is)
found_today=$(find /tmp/touch-lab -type f -mtime -2 | wc -l)
found_old=$(find /tmp/touch-lab -type f -mtime +30 | wc -l)
EOF
cat /root/rhcsa_journal/lab07/task3/done.txt
```

### 🧹 Cleanup

Leave sandbox; Task 4 reuses some filenames.

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `find: paths must precede expression` | Path argument went in the wrong spot — `find PATH -EXPR`, not `find -EXPR PATH` |
| Empty results when files exist | `-mtime N` (no sign) is exactly N — try `-N` or `+N` |

> **STOP — confirm `lastmonth.txt` appears in the `+30` results before Task 4.**

---

## Task 4 — Ansible: `ansible.builtin.file: state=touch` with Explicit Timestamps

**Practice directory this task:** `/tmp/touch-lab` (sandbox)

### 🔁 Warm-Up — Commands from Previous Labs

```bash
sudo mkdir -p /root/rhcsa_journal/lab07/task4/playbooks
date -Is | sudo tee /root/rhcsa_journal/lab07/task4/start.txt
ansible --version | head -1 | sudo tee -a /root/rhcsa_journal/lab07/task4/start.txt
ansible-galaxy collection list | grep ansible.posix | sudo tee -a /root/rhcsa_journal/lab07/task4/start.txt
echo "exit was: $?"
```

If `ansible --version` fails — **Lab 00**.

### Purpose

Replicate Tasks 1–2 with `ansible.builtin.file: state=touch`. Set explicit `modification_time:` and `access_time:`, then run the playbook twice to prove idempotence. Use `mode:`, `owner:`, `group:` on the same call to show how Ansible bundles touch + chmod + chown into one declarative module call.

### Main Command Block

Write the playbook:

```bash
sudo tee /root/rhcsa_journal/lab07/task4/playbooks/touch.yml > /dev/null <<'EOF'
---
- name: Lab 07 Task 4 — create + timestamp files via ansible.builtin.file
  hosts: localhost
  become: true
  gather_facts: false

  vars:
    sandbox: /tmp/touch-lab
    target_mtime: "202401151200.00"   # 2024-01-15 12:00:00 — touch -t format
    target_atime: "202001010000.00"   # 2020-01-01 00:00:00

  tasks:
    - name: Ensure sandbox directory exists
      ansible.builtin.file:
        path: "{{ sandbox }}"
        state: directory
        mode: '0755'

    - name: Touch a.txt with mode + ownership + explicit timestamps
      ansible.builtin.file:
        path: "{{ sandbox }}/ansible-a.txt"
        state: touch
        owner: root
        group: root
        mode: '0644'
        modification_time: "{{ target_mtime }}"
        access_time: "{{ target_atime }}"
      register: touch_a

    - name: Touch b.txt with just state=touch (timestamps = now)
      ansible.builtin.file:
        path: "{{ sandbox }}/ansible-b.txt"
        state: touch
        mode: '0600'
      register: touch_b

    - name: Show register results
      ansible.builtin.debug:
        msg:
          - "a.txt changed: {{ touch_a.changed }}"
          - "b.txt changed: {{ touch_b.changed }}"
EOF
```

Check-mode first:

```bash
ansible-playbook --check --diff /root/rhcsa_journal/lab07/task4/playbooks/touch.yml \
  2>&1 | sudo tee /root/rhcsa_journal/lab07/task4/check.log
```

Apply:

```bash
ansible-playbook /root/rhcsa_journal/lab07/task4/playbooks/touch.yml \
  2>&1 | sudo tee /root/rhcsa_journal/lab07/task4/apply.log
```

**Idempotence note for `state: touch`**: `state: touch` ALWAYS sets timestamps to **now** UNLESS you supply `modification_time:` and `access_time:` (with `modification_time_format:` and `access_time_format:` defaulting to `%Y%m%d%H%M.%S`). With explicit times, the second run is idempotent. Without them, EVERY run is `changed=1` — because mtime moves forward each time.

Idempotence rerun (expect `changed=1` on `b.txt` task, `changed=0` on `a.txt` task — because b uses default "now"):

```bash
ansible-playbook /root/rhcsa_journal/lab07/task4/playbooks/touch.yml \
  2>&1 | sudo tee /root/rhcsa_journal/lab07/task4/rerun.log
grep '^localhost' /root/rhcsa_journal/lab07/task4/rerun.log
```

### Human-Readable Breakdown

`ansible.builtin.file:` is the Ansible "everything about a file's metadata" module. `state: touch` is one of its valid states (the others: `file`, `directory`, `link`, `hard`, `absent`).

`modification_time: "202401151200.00"` corresponds to the manual `touch -t 202401151200`. The default `modification_time_format:` is `%Y%m%d%H%M.%S` — exactly the `touch -t` format. If you want a different shape (e.g., `2024-01-15T12:00:00`), set `modification_time_format: "%Y-%m-%dT%H:%M:%S"`.

`access_time:` is the same idea for atime.

When you do NOT set `modification_time:` and `access_time:`, the module sets them to "now" — which makes the task non-idempotent (every run = new "now" = changed). That's a deliberate Ansible design: `state: touch` is for "I want this file to exist and have a freshly-bumped mtime," which is intentionally NOT idempotent.

### Reading It Left to Right

```yaml
ansible.builtin.file:
  path: "{{ sandbox }}/ansible-a.txt"
  state: touch
  owner: root
  group: root
  mode: '0644'
  modification_time: "{{ target_mtime }}"
  access_time: "{{ target_atime }}"
```

- `ansible.builtin.file:` — FQCN of the file module
- `path:` — absolute path to the target
- `state: touch` — create if missing + update timestamps
- `owner:`, `group:` — DAC ownership
- `mode: '0644'` — octal mode (quoted, always)
- `modification_time: "202401151200.00"` — `touch -t` formatted string
- `access_time:` — same for atime

### The Story

A grader's RHCE question: "create `/srv/sentinel.flag` with mode 0600, owned by root, with a modification time of January 1, 2025." The Ansible answer is exactly the playbook above (path swapped). Three operations (create + chmod + touch -t) collapse into one `ansible.builtin.file:` call. That's the RHCE shape.

### Expected Output

First apply:

```
TASK [Ensure sandbox directory exists] ***
ok: [localhost]

TASK [Touch a.txt with mode + ownership + explicit timestamps] ***
changed: [localhost]

TASK [Touch b.txt with just state=touch] ***
changed: [localhost]

PLAY RECAP ***
localhost : ok=4 changed=2 unreachable=0 failed=0
```

Idempotence rerun:

```
TASK [Touch a.txt ...] ***
ok: [localhost]                    <-- not changed, because timestamps are explicit

TASK [Touch b.txt ...] ***
changed: [localhost]               <-- changed, because state:touch with no explicit time = now

PLAY RECAP ***
localhost : ok=4 changed=1 unreachable=0 failed=0
```

That `changed=1` on b is **not a bug** — it's the documented behavior of `state: touch` with default times. Note it; understand it.

### Switches Table

| Switch / Key | Meaning | Why it matters |
|---|---|---|
| `ansible.builtin.file:` | FQCN of the file module | RHCE answer for touch/chmod/chown |
| `state: touch` | Create + bump timestamps | Equivalent to `touch FILE` |
| `state: file` | Ensure exists with given attrs (does NOT create empty file) | Use when file already exists |
| `state: directory` | Make a directory | Equivalent to `mkdir -p` |
| `state: absent` | Remove | Equivalent to `rm` / `rm -rf` |
| `modification_time:` | mtime as `touch -t` formatted string | Idempotent touch |
| `access_time:` | atime, same format | Idempotent touch |
| `modification_time_format:` | strftime format override | If you want ISO 8601 etc |
| `mode:` | Octal mode, quoted | Quote it: `'0644'` |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| `ansible.builtin.file: state=touch` | Equivalent to `touch FILE` + chmod + chown in one call |
| `modification_time:` | Equivalent to `touch -t` — idempotent when explicit |
| Default time = "now" | `state: touch` without explicit times = NOT idempotent (deliberate) |
| `state: file` vs `state: touch` | `file` doesn't create; `touch` creates if missing |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| **Wrapping `command: touch` instead of using `ansible.builtin.file`** | RHCE cardinal sin | Use the module |
| `mode: 0644` (unquoted) | YAML parses as decimal 644 = octal 1204 — silent wrong mode | Always quote: `mode: '0644'` |
| Forgetting explicit `modification_time:` and complaining about non-idempotence | `state: touch` defaults to "now" — that's the spec | Pass explicit `modification_time:` for idempotence |

### 🔁 Persistence Check

```bash
test -f /tmp/touch-lab/ansible-a.txt && echo "a.txt ok"
test -f /tmp/touch-lab/ansible-b.txt && echo "b.txt ok"
stat -c '%y' /tmp/touch-lab/ansible-a.txt | grep -c '2024-01-15'
stat -c '%a' /tmp/touch-lab/ansible-a.txt | grep -c '644'
```

All four must return success.

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab07/task4/done.txt > /dev/null <<EOF
lab=07 task=4
when=$(date -Is)
playbook=/root/rhcsa_journal/lab07/task4/playbooks/touch.yml
a_mtime=$(stat -c '%y' /tmp/touch-lab/ansible-a.txt)
a_atime=$(stat -c '%x' /tmp/touch-lab/ansible-a.txt)
a_mode=$(stat -c '%a' /tmp/touch-lab/ansible-a.txt)
b_mode=$(stat -c '%a' /tmp/touch-lab/ansible-b.txt)
EOF
cat /root/rhcsa_journal/lab07/task4/done.txt
```

### 🧹 Cleanup

Leave files; Task 5 verifies them and cleans together.

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `couldn't resolve module 'ansible.builtin.file'` | `ansible-core` broken — reinstall |
| Timestamps not what you set | Check `modification_time_format:` — default is `%Y%m%d%H%M.%S`, not ISO 8601 |
| `mode` shows `0744` after `mode: 0644` | YAML stripped the leading 0 — quote the mode string |

> **STOP — confirm a.txt mtime is 2024-01-15 before Task 5.**

---

## Task 5 — RHCSA Verification Capstone: Prove Timestamps Are Persistent and Correct

**Practice directory this task:** `/var/log` (real-world reference) + `/tmp/touch-lab` (sandbox)

### 🔁 Warm-Up — Commands from Previous Labs

```bash
sudo mkdir -p /root/rhcsa_journal/lab07/task5
date -Is | sudo tee /root/rhcsa_journal/lab07/task5/start.txt
echo "exit was: $?"
```

### Purpose

Use **only** RHCSA inspection commands (`stat`, `ls`, `find`, `getfacl`) to prove:

1. The files Ansible created exist
2. Their timestamps match what the playbook claimed
3. The mode + owner match the playbook

### Main Command Block

Three+ RHCSA inspection commands:

```bash
# 1) Existence and metadata
ls -l /tmp/touch-lab/ansible-a.txt /tmp/touch-lab/ansible-b.txt
stat /tmp/touch-lab/ansible-a.txt

# 2) Programmatic timestamp check
mtime_a=$(stat -c '%y' /tmp/touch-lab/ansible-a.txt | cut -d' ' -f1)
atime_a=$(stat -c '%x' /tmp/touch-lab/ansible-a.txt | cut -d' ' -f1)
echo "ansible-a.txt mtime date: $mtime_a (expected 2024-01-15)"
echo "ansible-a.txt atime date: $atime_a (expected 2020-01-01)"
[ "$mtime_a" = "2024-01-15" ] && echo "MTIME_MATCH" || echo "MTIME_MISMATCH"
[ "$atime_a" = "2020-01-01" ] && echo "ATIME_MATCH" || echo "ATIME_MISMATCH"

# 3) Mode + owner check
mode_a=$(stat -c '%a' /tmp/touch-lab/ansible-a.txt)
owner_a=$(stat -c '%U:%G' /tmp/touch-lab/ansible-a.txt)
echo "mode=$mode_a (expected 644)"
echo "owner=$owner_a (expected root:root)"

# 4) find -mtime sanity — file is well in the past
find /tmp/touch-lab -name 'ansible-a.txt' -mtime +365   # older than a year ago

# Capture combined evidence
{
  echo "=== ls -l ===";          ls -l /tmp/touch-lab/ansible-a.txt /tmp/touch-lab/ansible-b.txt
  echo "=== stat ===";           stat /tmp/touch-lab/ansible-a.txt
  echo "=== timestamps ==="
  mtime_a=$(stat -c '%y' /tmp/touch-lab/ansible-a.txt | cut -d' ' -f1)
  atime_a=$(stat -c '%x' /tmp/touch-lab/ansible-a.txt | cut -d' ' -f1)
  echo "mtime=$mtime_a atime=$atime_a"
  [ "$mtime_a" = "2024-01-15" ] && [ "$atime_a" = "2020-01-01" ] && echo "MATCH" || echo "MISMATCH"
  echo "=== mode + owner ==="
  echo "mode=$(stat -c '%a' /tmp/touch-lab/ansible-a.txt) owner=$(stat -c '%U:%G' /tmp/touch-lab/ansible-a.txt)"
  echo "=== older-than-365d ==="; find /tmp/touch-lab -name 'ansible-a.txt' -mtime +365
} 2>&1 | sudo tee /root/rhcsa_journal/lab07/task5/evidence.txt
```

### Human-Readable Breakdown

The capstone is the auditor seat. You do NOT run `ansible-playbook` — you ask the filesystem directly. `stat` prints all three timestamps; `cut -d' ' -f1` keeps only the YYYY-MM-DD portion so we can do a string equality test. `find -mtime +365` confirms the file looks "older than a year" — a sanity check that the mtime really is in 2024.

This is the RHCSA-grade auditor's path for any "did the playbook actually work?" question. Always at least three commands (`ls`, `stat`, `find`) plus the equality test.

### Reading It Left to Right

`stat -c '%y' FILE | cut -d' ' -f1`

- `stat -c '%y'` — mtime, human-readable form (`2024-01-15 12:00:00.000000000 -0500`)
- `|` — pipe to next command
- `cut -d' ' -f1` — split on space, keep field 1 → `2024-01-15`

`find /tmp/touch-lab -name 'ansible-a.txt' -mtime +365`

- `find` — search
- `/tmp/touch-lab` — start path
- `-name 'ansible-a.txt'` — match by name
- `-mtime +365` — mtime older than 365 days ago

### The Story

You hand a grader `evidence.txt` and it reads: "the file exists, its mtime is exactly 2024-01-15, its atime is exactly 2020-01-01, its mode is 644, its owner is root:root, and `find -mtime +365` confirms it's older than a year." That answers every plausible follow-up question.

### Expected Output

```
=== ls -l ===
-rw-r--r--. 1 root root 0 Jan 15  2024 /tmp/touch-lab/ansible-a.txt
-rw-------. 1 root root 0 May 27 15:01 /tmp/touch-lab/ansible-b.txt

=== timestamps ===
mtime=2024-01-15 atime=2020-01-01
MATCH

=== mode + owner ===
mode=644 owner=root:root

=== older-than-365d ===
/tmp/touch-lab/ansible-a.txt
```

### Switches Table

| Switch | Meaning | Why it matters |
|---|---|---|
| `stat -c '%y'` | mtime human-readable | RHCSA primary timestamp check |
| `stat -c '%x'` | atime | Same |
| `stat -c '%a'` | mode | Mode check |
| `stat -c '%U:%G'` | owner:group | Ownership check |
| `cut -d' ' -f1` | Split on space, keep field 1 | Strip time to get YYYY-MM-DD |
| `find -mtime +365` | Older than 365 days | Sanity check |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| Verification triangle | `ls -l`, `stat`, `find` |
| Reboot reasoning | `/tmp/` is wiped on reboot — for true persistence use `/var/` or `/root/`; this lab uses `/tmp/` deliberately for fast cleanup |
| Auditor reflex | Confirm with 3+ RHCSA commands AND a programmatic equality test |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| **Trusting `changed=1` from ansible-playbook** | Whole point of the verification capstone | Verify with `stat`, `ls`, `find` |
| Locale drift | `stat` output in non-en_US locale formats differently | Set `LC_ALL=C stat` for stable scripted compares |

### 🔁 Persistence Check (Reboot Reasoning)

```bash
echo "REBOOT REASONING:"                                                                          | sudo tee /root/rhcsa_journal/lab07/task5/reboot.txt
echo "1. /tmp/touch-lab is on tmpfs OR a tmpfiles.d-managed dir — wiped on reboot."              | sudo tee -a /root/rhcsa_journal/lab07/task5/reboot.txt
echo "2. For TRUE persistence we would put files in /var/lib/ or /root/."                        | sudo tee -a /root/rhcsa_journal/lab07/task5/reboot.txt
echo "3. The Ansible playbook itself IS persistent — it lives in /root/rhcsa_journal/."          | sudo tee -a /root/rhcsa_journal/lab07/task5/reboot.txt
test -f /root/rhcsa_journal/lab07/task4/playbooks/touch.yml && echo "playbook persists"          | sudo tee -a /root/rhcsa_journal/lab07/task5/reboot.txt
df /tmp 2>/dev/null | tail -1                                                                    | sudo tee -a /root/rhcsa_journal/lab07/task5/reboot.txt
```

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab07/task5/done.txt > /dev/null <<EOF
lab=07 task=5
when=$(date -Is)
evidence=/root/rhcsa_journal/lab07/task5/evidence.txt
reboot=/root/rhcsa_journal/lab07/task5/reboot.txt
match=$(grep -c '^MATCH$' /root/rhcsa_journal/lab07/task5/evidence.txt)
status=lab07-complete
EOF
cat /root/rhcsa_journal/lab07/task5/done.txt
```

### 🧹 Cleanup

```bash
# Remove the sandbox; playbook + journal stay
sudo rm -rf /tmp/touch-lab
ls -d /tmp/touch-lab 2>&1 | grep -q "No such" && echo "sandbox cleaned"

# Journal stays
ls /root/rhcsa_journal/lab07/
```

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `MISMATCH` in evidence.txt | Re-run Task 4 — `modification_time:` likely had wrong format |
| `find -mtime +365` returns nothing | Either mtime was reset by a subsequent `touch`, or `+365` is too coarse — try `+30` |

> **STOP — record `status=lab07-complete` in done.txt. Lab 07 is finished.**

---

## Lab 07 Complete When

```bash
ls /root/rhcsa_journal/lab07/task{1,2,3,4,5}/done.txt
grep -l 'lab07-complete' /root/rhcsa_journal/lab07/task5/done.txt
test -f /root/rhcsa_journal/lab07/task4/playbooks/touch.yml
grep -c 'MATCH' /root/rhcsa_journal/lab07/task5/evidence.txt
```

All four must succeed. You can now create files, control their three timestamps from the shell, do the same declaratively with Ansible, and audit the result with RHCSA-grade `stat`/`ls`/`find`.
