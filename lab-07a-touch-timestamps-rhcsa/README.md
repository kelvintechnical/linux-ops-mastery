# Lab 07a: Creating Empty Files & Manipulating Timestamps (RHCSA) — `touch`, `stat`, `find -mtime/-mmin`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `07a` (RHCSA) → `07b` (Ansible) → `07c` (Verify)
- **Career arcs covered:** RHCSA EX200 (timestamp inspection + log-rotation triggers), RHCE EX294 (file module `modification_time:` / `access_time:`), SRE (log-rotation triggers + stale-file alerts), AI/MLOps (stale-checkpoint cleanup based on mtime)
- **Prerequisite:** Lab 06 (`ls -l`, `ls -lZ`)
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (ADHD spec — Task 1 canonical, Task 2 contrast)
- **Practice Directory (rotation #07):** `/var/log`
- **Sandbox:** `/tmp/touch-lab/`
- **Traps rehearsed this lab:** **T07** (`touch -t` format vs `touch -d` format — easy to swap; `-t` wants `[[CC]YY]MMDDhhmm[.ss]`, `-d` wants any `date -d` string) · **T08** (`-mtime +1` means strictly MORE than 1×24h ago, not "at least 1 day" — off-by-one trap)

> **This lab's practice directory is: `/var/log`** — every task references it in at least two commands. We **read** `/var/log` only (it is the real-world log-rotation target); we **write** only inside `/tmp/touch-lab/`.

---

## 🖥️ LAB HEADER BLOCK — run this FIRST

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T07 T08"
echo "📁  PRACTICE DIR: /var/log"
echo ""
echo "💡 /var/log freshest 3 files (read-only inspection target):"
ls -lt /var/log 2>/dev/null | head -4
```

> **STOP — paste header output before running setup.**

---

## 🎯 Objective

Create empty files, manipulate their three timestamps (atime/mtime/ctime), and use those timestamps to find files. By the end of this lab you can answer the grader's question "when was this file last modified vs. last read vs. last had its metadata changed?" without hesitation — because the discipline of `stat → touch → find` has become reflex, and you know exactly which switch each operation needs.

---

## 🧠 Concept: mtime vs atime vs ctime vs btime — Four Different Questions

Every regular file carries **four** timestamps. They answer different questions; mixing them up is the classic RHCSA mistake.

```
   ┌───────────────────────────────────────────────────────────────┐
   │  stat FILE  →  Access (atime)   ←  cat, less, grep, cp READ   │
   │              Modify (mtime)   ←  echo>, vi :w, sed -i WRITE   │
   │              Change (ctime)   ←  chmod, chown, mv, link, etc. │
   │              Birth  (btime)   ←  filesystem create (ext4/xfs) │
   └───────────────────────────────────────────────────────────────┘
```

Critical distinction: **ctime is NOT creation time**. The "c" stands for **change of inode**. For true creation time use `stat -c '%w'` (btime / birth) — and accept that the filesystem may print `-` if it does not support it.

`touch FILE` does two things in one syscall chain: if the file is missing it creates it (mode `0666 & ~umask`), and it sets atime + mtime to **now**. As a side effect ctime also updates — any write to the inode's timestamp fields counts as a metadata change. To bump ONLY ctime, run `chmod` with the same mode the file already has — it rewrites the inode without changing mode bits, and the kernel updates ctime alone.

> **The RHCSA failure mode (T07):** confusing the `-t` and `-d` formats of `touch`. `-t` accepts `[[CC]YY]MMDDhhmm[.ss]` (`202401151200.00`); `-d` accepts anything `date -d` parses (`"2024-01-15 12:00"`, `"yesterday"`, `"2 hours ago"`). Mix them up and the parser either errors out or silently picks the wrong year.

---

## 📚 Touch + Stat + Find Reference (everything for Tasks 1–2)

| Token | Meaning |
|---|---|
| `touch FILE` | Create if missing; update atime + mtime to now |
| `touch -t [[CC]YY]MMDDhhmm[.ss]` | Set both timestamps with numeric format |
| `touch -d 'STRING'` | Set both timestamps using a `date -d` string |
| `touch -r REF TARGET` | Copy timestamps **from** REF **to** TARGET |
| `touch -a` | Set atime only (combine with `-d` or `-t`) |
| `touch -m` | Set mtime only (combine with `-d` or `-t`) |
| `touch -c FILE` | Update only — do not create if missing |
| `stat FILE` | Full metadata dump including all timestamps |
| `stat -c '%x'` | atime, human-readable |
| `stat -c '%y'` | mtime, human-readable |
| `stat -c '%z'` | ctime, human-readable |
| `stat -c '%w'` | btime, human-readable (`-` if unsupported) |
| `stat -c '%Y'` | mtime as epoch seconds (arithmetic-friendly) |
| `find PATH -mtime -N` | Modified less than N×24h ago (newer than N days) |
| `find PATH -mtime +N` | Modified MORE than N×24h ago (older than N days) |
| `find PATH -mmin ±N` | Same convention, minutes |
| `find PATH -newer REF` | Modified after REF's mtime (no day rounding) |

> **Rule of `touch`/`stat`/`find`:** Pick the smallest tool for the question. `stat -c '%y'` for "when modified," `find -newer` for precise comparisons, `find -mtime ±N` for day-rounded sweeps.

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i
mkdir -p /tmp/touch-lab
mkdir -p /root/rhcsa_journal/lab-07a
cd /tmp/touch-lab

cat > /tmp/touch-lab/THIS_DIRECTORY.txt <<'EOF'
/tmp/touch-lab — sandbox for Lab 07a (touch + stat + find by timestamp)

/var/log is the real-world target this lab keeps referencing. We READ
/var/log to see live mtime/ctime/atime on system log files (logrotate
triggers fire when these timestamps cross thresholds). We never WRITE
to /var/log — that is the system journal's job.

We WRITE only inside /tmp/touch-lab/ because /tmp is tmpfs on most
distributions: zero risk of damaging anything real, and the sandbox
evaporates on reboot.

Three RHCSA reflexes practiced here:
  1. stat <FILE> on every file you touch (audit reflex)
  2. touch -t / -d / -r for explicit timestamp manipulation
  3. find -mtime / -mmin / -newer for timestamp-based search
EOF

echo "lab07a reference content" > /tmp/touch-lab/reference.txt
stat /tmp/touch-lab/reference.txt | head -n 8
ls -lt /var/log 2>/dev/null | head -5
echo "exit was: $?"
```

> **STOP — paste output before Task 1. Confirm `reference.txt` exists and `/var/log` listing returned at least 3 files.**

---

## Task 1 — Create files with `touch` and read all four timestamps with `stat`

**Practice directory this task:** `/var/log` (read-only inspection of real log files) · `/tmp/touch-lab/` (the safe write target).

### 🔁 Warm-Up — commands woven into Task 1

```bash
mkdir -p /tmp/touch-lab/task1
ls -la /tmp/touch-lab                               2>&1 | tee /tmp/touch-lab/task1/warmup.txt
wc -l /tmp/touch-lab/THIS_DIRECTORY.txt
test -f /tmp/touch-lab/reference.txt && echo "reference OK"
stat -c '%n mode=%a mtime=%y' /tmp/touch-lab/reference.txt
set -o pipefail
find /var/log -maxdepth 1 -type f                   2>/dev/null | wc -l
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 06: `ls -l` shows mtime by default — we now go deeper with `stat -c` to read all four timestamps explicitly.

### Purpose

Create empty files with `touch`, then read all three primary timestamps (atime, mtime, ctime) plus btime using `stat`. Demonstrate **which timestamp updates on which operation** — `touch` bumps atime+mtime (and ctime as a side effect because the inode changed), `chmod` bumps **only** ctime, `cat` bumps **only** atime.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `ls -la /tmp/touch-lab` | Baseline snapshot **before** any `touch` — proves the deltas in `op.txt` |
| `stat -c '%n mtime=%y'` | The format we will repeat per operation to track timestamp drift |
| `test -f reference.txt` | Guards the `touch -r reference.txt` call in Task 2 |
| `find /var/log -type f` | Confirms real log-files are readable for the cross-reference stat at the end |
| `2>&1 \| tee` | Captures every `stat` line into `task1/op.txt` for the journal |
| `set -o pipefail` | Catches a silent failure in the `stat ... \| tee` chain |

### Main command block

```bash
cd /tmp/touch-lab

# 1) touch to CREATE files (atime+mtime+ctime all = now; btime = now too)
touch /tmp/touch-lab/a.txt
touch /tmp/touch-lab/b.txt /tmp/touch-lab/c.txt   # multiple at once
ls -la /tmp/touch-lab/*.txt                         2>&1 | tee /tmp/touch-lab/task1/op.txt

# 2) Read all four timestamps explicitly
stat /tmp/touch-lab/a.txt                           2>&1 | tee -a /tmp/touch-lab/task1/op.txt
stat -c 'atime=%x' /tmp/touch-lab/a.txt
stat -c 'mtime=%y' /tmp/touch-lab/a.txt
stat -c 'ctime=%z' /tmp/touch-lab/a.txt
stat -c 'btime=%w' /tmp/touch-lab/a.txt             # '-' if filesystem doesn't support btime

# 3) Cross-reference: a real /var/log file
stat /var/log/messages 2>/dev/null || stat /var/log/wtmp 2>/dev/null

# 4) Demonstrate WHICH operation bumps WHICH timestamp
{
  echo "=== initial ===";                                 stat -c 'atime=%x mtime=%y ctime=%z' /tmp/touch-lab/a.txt
  sleep 1
  echo "=== after touch (bumps atime+mtime, side-effect ctime) ===";  touch /tmp/touch-lab/a.txt
  stat -c 'atime=%x mtime=%y ctime=%z' /tmp/touch-lab/a.txt
  sleep 1
  echo "=== after chmod (bumps ctime ONLY, no data write) ===";       chmod 600 /tmp/touch-lab/a.txt
  stat -c 'atime=%x mtime=%y ctime=%z' /tmp/touch-lab/a.txt
  sleep 1
  echo "=== after cat (bumps atime ONLY) ===";                        cat /tmp/touch-lab/a.txt > /dev/null
  stat -c 'atime=%x mtime=%y ctime=%z' /tmp/touch-lab/a.txt
} 2>&1 | tee /tmp/touch-lab/task1/transcript.txt

echo "exit was: $?"
```

### Human-readable breakdown

1. Three `touch` calls create three empty files. With no options, `touch` sets atime+mtime to **now** and (as a side effect of writing to the inode) bumps ctime too.
2. `stat FILE` prints the full multi-line block; `stat -c FMT FILE` prints only the requested fields — programmatic-friendly.
3. The contrast block uses `sleep 1` to make the timestamp drift visible. After each operation we re-print all three timestamps and compare to the previous line.
4. `chmod 600` (a true mode change) leaves atime+mtime alone but bumps ctime — that is the **defining proof** that ctime ≠ creation, ctime = last-inode-change.
5. `cat ... > /dev/null` reads the file (the kernel updates atime) without writing anything. On a `noatime`-mounted filesystem this step prints unchanged atime — that is also useful evidence (see troubleshoot table).

### Reading it left to right

- `touch /tmp/touch-lab/a.txt` — single-syscall create + timestamp update; mode is `0666 & ~umask`.
- `stat -c '%x'` — Access time, fractional seconds + timezone.
- `stat -c '%y'` — Modify time, same format.
- `stat -c '%z'` — Change time (inode-change, **not** creation).
- `stat -c '%w'` — Birth time; `-` if unsupported (some XFS / ext2 layouts).
- `chmod 600 FILE` — even when 600 is the existing mode, this syscall rewrites the inode → ctime updates.
- `cat FILE > /dev/null` — reads bytes; the kernel updates atime unless mounted `noatime`/`relatime` with the relatime conditions unmet.

### The story

A grader hands you a server and asks: "When was `/etc/sshd_config` last edited?" That is **mtime**. "When did its permissions change?" That is **ctime**. "When was it last read?" That is **atime**. A sloppy answer reports the wrong timestamp and loses points. The verification reflex — `stat -c '%x %y %z %w' FILE` on every file you touch — makes this automatic.

The deeper lesson is the **side-effect map**: write operations always bump mtime + ctime; metadata operations (chmod, chown, mv, ln) bump only ctime; read operations bump only atime. Memorize the map and timestamp questions become trivial.

### Expected output

```text
total 12
-rw-r--r--. 1 root root  0 May 27 15:00 a.txt
-rw-r--r--. 1 root root  0 May 27 15:00 b.txt
-rw-r--r--. 1 root root  0 May 27 15:00 c.txt
  File: /tmp/touch-lab/a.txt
  Size: 0           Blocks: 0          IO Block: 4096   regular empty file
Access: 2026-05-27 15:00:01.234567890 -0400
Modify: 2026-05-27 15:00:01.234567890 -0400
Change: 2026-05-27 15:00:01.234567890 -0400
 Birth: 2026-05-27 15:00:01.234567890 -0400
=== initial ===
atime=2026-05-27 15:00:01... mtime=2026-05-27 15:00:01... ctime=2026-05-27 15:00:01...
=== after touch (bumps atime+mtime, side-effect ctime) ===
atime=2026-05-27 15:00:02... mtime=2026-05-27 15:00:02... ctime=2026-05-27 15:00:02...
=== after chmod (bumps ctime ONLY, no data write) ===
atime=2026-05-27 15:00:02... mtime=2026-05-27 15:00:02... ctime=2026-05-27 15:00:03...
=== after cat (bumps atime ONLY) ===
atime=2026-05-27 15:00:04... mtime=2026-05-27 15:00:02... ctime=2026-05-27 15:00:03...
exit was: 0
```

> The win condition: after `chmod`, **ctime > mtime**. After `cat`, **atime > mtime** and ctime is unchanged. That is the proof of the side-effect map.

### Switches

| Token | Meaning |
|---|---|
| `touch FILE` | Create if missing; set atime + mtime to now |
| `touch FILE1 FILE2 ...` | Touch multiple files in one syscall chain |
| `stat FILE` | Full metadata block (3 timestamps + size + perms + inode) |
| `stat -c '%x'` | atime, human-readable |
| `stat -c '%y'` | mtime, human-readable |
| `stat -c '%z'` | ctime, human-readable |
| `stat -c '%w'` | btime (birth/creation), `-` if filesystem lacks it |
| `stat -c '%Y'` | mtime as epoch seconds (arithmetic-friendly) |
| `chmod MODE FILE` | Re-writes the inode → bumps ctime, leaves atime/mtime |
| `cat FILE > /dev/null` | Reads bytes → bumps atime (unless `noatime`) |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | atime | Last time the file's data was **read** |
|   | mtime | Last time the file's data was **written** |
|   | ctime | Last time the file's **inode** changed (mtime change, chmod, chown, link, mv) |
|   | btime | Filesystem creation time — `stat -c '%w'`; `-` if unsupported |
|   | Side-effect map | write→mtime+ctime · metadata→ctime · read→atime |
|   | `noatime` mount | Disables atime updates entirely — check `mount \| grep noatime` |
| 🪤 | **Trap Risk T07** | Confusing the `-t` numeric format with the `-d` string parser — covered in detail in Task 2 |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Three files created | `ls /tmp/touch-lab/*.txt \| wc -l` | Must be `>= 3` |
| Transcript captured | `wc -l /tmp/touch-lab/task1/transcript.txt` | Must be `> 0` — the side-effect map proof lives here |
| Birth time supported | `stat -c '%w' /tmp/touch-lab/a.txt \| grep -q '^[0-9]' && echo btime OK \|\| echo 'btime not supported on this fs'` | Informational — XFS+ext4 with modern features support it; older layouts do not |

> **Reboot reasoning:** `/tmp/touch-lab` is tmpfs (or tmpfiles.d-managed) and evaporates at reboot. The journal `transcript.txt` we copy to `/root/rhcsa_journal/lab-07a/` is what survives — that is the auditable evidence of the side-effect map.

### Journal write — BEFORE cleanup

```bash
LAB=lab-07a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/touch-lab/task1/op.txt          "$JDIR/op.txt"
cp /tmp/touch-lab/task1/transcript.txt  "$JDIR/transcript.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    touch creates + stat reads all four timestamps; side-effect map proven
COMMANDS: touch, stat, stat -c '%x %y %z %w', chmod, cat > /dev/null
TRAPS:    T07 reviewed (ctime ≠ creation; btime via '%w' is the real creation timestamp)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — touch -t / -d / -r / -a / -m + find -mtime/-mmin/-newer
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
# Keep the test files in /tmp/touch-lab — Task 2 reuses a.txt b.txt c.txt
rm -rf /tmp/touch-lab/task1
ls /tmp/touch-lab
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `Birth: -` in `stat` output | Filesystem (older ext4 or unsupported XFS layout) — informational, not a bug |
| atime never moves after `cat` | Mount option `noatime` or `relatime` blocking updates — `mount \| grep noatime` |
| `stat: cannot statx FILE` | File missing — re-run the `touch` step that should have created it |
| `chmod` did not bump ctime | You used `chmod` with `--reference=` against the same file; try `chmod 600 FILE` literally |

> **STOP — paste the contents of `transcript.txt` showing all four "===" sections before starting Task 2.**

---

## Task 2 — Explicit timestamps with `touch -t / -d / -r / -a / -m` + find files by age (`find -mtime / -mmin / -newer`)

**Practice directory this task:** `/var/log` (real-world target for `find -mtime -1`) · `/tmp/touch-lab/` (the safe sandbox where we backdate files).

### 🔁 Warm-Up — commands woven into Task 2

```bash
mkdir -p /tmp/touch-lab/task2
ls /tmp/touch-lab                                   2>&1 | tee /tmp/touch-lab/task2/warmup.txt
test -f /tmp/touch-lab/reference.txt && echo "reference OK for -r"
stat -c 'reference mtime=%y' /tmp/touch-lab/reference.txt
find /var/log -maxdepth 1 -type f                   2>/dev/null | wc -l
date -Is
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: the `stat -c '%y'` reflex continues — every backdate is followed by a `stat` to prove it stuck.

### Purpose

Set timestamps explicitly with the **five** `touch` switches RHCSA cares about (`-t`, `-d`, `-r`, `-a`, `-m`), then use the resulting backdated files to exercise `find -mtime`, `find -mmin`, and `find -newer`. The same backdating is what Lab 07b's Ansible `modification_time:` parameter replicates declaratively.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `stat -c 'mtime=%y'` | Verifies every `-t` / `-d` / `-r` actually stuck |
| `test -f reference.txt` | Guards the `touch -r reference.txt` call |
| `find /var/log -type f` | Real-world `find -mtime -1` target at the end of the task |
| `date -Is` | Pins the journal `notes.txt` timestamp |
| `2>&1 \| tee` | Captures the full transcript into `task2/op.txt` |
| `set -o pipefail` | Catches a silent failure in the `find ... \| tee` chain |

### Main command block

```bash
cd /tmp/touch-lab

# ── Part A: touch -t / -d / -r / -a / -m ──────────────────────────

# 1) touch -t — numeric format [[CC]YY]MMDDhhmm[.ss]
touch -t 202401151200 /tmp/touch-lab/a.txt
stat -c 'a.txt mtime=%y' /tmp/touch-lab/a.txt        # expect 2024-01-15 12:00:00

# 2) touch -d — date-string parser (anything `date -d` accepts)
touch -d '2025-06-30 09:30:00' /tmp/touch-lab/b.txt
stat -c 'b.txt mtime=%y' /tmp/touch-lab/b.txt
touch -d 'yesterday'      /tmp/touch-lab/c.txt
stat -c 'c.txt mtime=%y' /tmp/touch-lab/c.txt

# 3) touch -r — copy timestamps FROM reference TO target
touch /tmp/touch-lab/copy.txt
sleep 2
touch -r /tmp/touch-lab/reference.txt /tmp/touch-lab/copy.txt
stat -c 'ref mtime=%y' /tmp/touch-lab/reference.txt
stat -c 'cpy mtime=%y' /tmp/touch-lab/copy.txt        # must match ref exactly

# 4) touch -a (atime only) / touch -m (mtime only)
touch -a -d '2020-01-01 00:00:00' /tmp/touch-lab/a.txt
touch -m -d '2030-12-31 23:59:00' /tmp/touch-lab/a.txt
stat -c 'a.txt atime=%x mtime=%y' /tmp/touch-lab/a.txt

# ── Part B: find -mtime / -mmin / -newer ──────────────────────────

# Build three sandbox files with known ages
touch -d 'yesterday'      /tmp/touch-lab/yesterday.txt
touch -d '8 days ago'     /tmp/touch-lab/lastweek.txt
touch -d '40 days ago'    /tmp/touch-lab/lastmonth.txt
touch                     /tmp/touch-lab/now.txt
ls -lt /tmp/touch-lab/ | head

# find by DAYS (-mtime)
{
  echo "═══ touch -t / -d / -r / -a / -m ═══"
  stat -c 'a.txt atime=%x mtime=%y' /tmp/touch-lab/a.txt
  stat -c 'b.txt mtime=%y' /tmp/touch-lab/b.txt
  stat -c 'copy.txt mtime=%y' /tmp/touch-lab/copy.txt

  echo "═══ find -mtime -2  (newer than 2 days) ═══"
  find /tmp/touch-lab -maxdepth 1 -type f -mtime -2
  echo "═══ find -mtime +7  (OLDER than 7 days) ═══"
  find /tmp/touch-lab -maxdepth 1 -type f -mtime +7
  echo "═══ find -mtime +30 (older than 30 days) ═══"
  find /tmp/touch-lab -maxdepth 1 -type f -mtime +30
  echo "═══ find -mmin -5  (last 5 minutes) ═══"
  find /tmp/touch-lab -maxdepth 1 -type f -mmin -5
  echo "═══ find -newer reference.txt ═══"
  find /tmp/touch-lab -maxdepth 1 -type f -newer /tmp/touch-lab/reference.txt
  echo "═══ /var/log -mtime -1 (real-world log-rotation trigger) ═══"
  find /var/log -maxdepth 1 -type f -mtime -1 2>/dev/null | head -5
} 2>&1 | tee /tmp/touch-lab/task2/op.txt

echo "exit was: $?"
```

### Human-readable breakdown

**Part A — five touch switches.**

1. `touch -t 202401151200` — numeric `[[CC]YY]MMDDhhmm[.ss]`. Always use the full 12-digit form (`CC` century included) to avoid the century-strip trap.
2. `touch -d 'STRING'` — forgiving `date -d` parser. Accepts `'yesterday'`, `'2 hours ago'`, ISO 8601, and full `'YYYY-MM-DD HH:MM:SS'`.
3. `touch -r REF TARGET` — copies BOTH atime and mtime from REF onto TARGET. Argument order: reference first, target second. Senior reflex: `touch -r oldfile newfile` to make a brand-new file look as old as the original.
4. `touch -a -d ...` — atime ONLY. The `-m` counterpart sets mtime ONLY. Combining them lets you put atime and mtime in completely different decades on the same file (the demo here uses 2020 + 2030).

**Part B — three find switches.**

- `-mtime -N` newer than N×24h ago (modified today → `-mtime -1`).
- `-mtime +N` strictly OLDER than N×24h ago. T08 catch: `-mtime +1` means MORE than 1 full day — a file modified 36 hours ago does NOT match `+1`, only `-1` (because 36h < 48h). Use `-mtime +0` if you want "anything older than the last 24 hours."
- `-mmin ±N` same convention, minutes. Best for "what changed in the last hour."
- `-newer REF` exact precision (no day rounding). Use when `-mtime` is too coarse.

### Reading it left to right

- `touch -t 202401151200 FILE` — `-t` takes `CCYYMMDDhhmm` (or with optional `.ss`). The string `202401151200` decomposes as `2024-01-15 12:00:00`.
- `touch -d 'yesterday' FILE` — the parser handles relative phrases via `date -d`. If `date -d 'STR'` works, `touch -d 'STR'` works.
- `touch -r REFERENCE TARGET` — note the order: source comes first.
- `touch -a -d '2020-01-01 00:00:00' FILE` — `-a` restricts the update to atime; mtime is left untouched.
- `find -maxdepth 1 -type f -mtime -2` — recursion capped at one level (RHCSA noise control); `-type f` excludes directories.
- `find /var/log ... 2>/dev/null` — discards "Permission denied" noise from logdirs we cannot read.

### The story

A grader's classic question: "make `/var/www/html/old.html` appear last-modified on January 1, 2024." The manual answer is `touch -t 202401010000 /var/www/html/old.html`. One command, one verification with `stat -c '%y'`, done. The RHCE answer in Lab 07b uses `ansible.builtin.file: modification_time:` — same effect, declarative.

For `find -mtime`, the practical scenario is log rotation: "copy every `/var/log` file modified in the last 24 hours to `/root/today-logs/`." The answer is `find /var/log -maxdepth 1 -type f -mtime -1 -exec cp -p {} /root/today-logs/ \;`. Without the `-mtime` discipline you can't write that command — and log rotation, backup scripts, and forensic timeline analysis all sit on this primitive.

### Expected output

```text
═══ touch -t / -d / -r / -a / -m ═══
a.txt atime=2020-01-01 00:00:00.000000000 -0500 mtime=2030-12-31 23:59:00.000000000 -0500
b.txt mtime=2025-06-30 09:30:00.000000000 -0400
copy.txt mtime=2026-05-27 15:00:05.xxx -0400
═══ find -mtime -2  (newer than 2 days) ═══
/tmp/touch-lab/yesterday.txt
/tmp/touch-lab/now.txt
/tmp/touch-lab/reference.txt
/tmp/touch-lab/copy.txt
═══ find -mtime +7  (OLDER than 7 days) ═══
/tmp/touch-lab/lastweek.txt
/tmp/touch-lab/lastmonth.txt
═══ find -mtime +30 (older than 30 days) ═══
/tmp/touch-lab/lastmonth.txt
═══ find -mmin -5  (last 5 minutes) ═══
/tmp/touch-lab/now.txt
═══ find -newer reference.txt ═══
/tmp/touch-lab/now.txt
═══ /var/log -mtime -1 (real-world log-rotation trigger) ═══
/var/log/messages
/var/log/secure
exit was: 0
```

> Notice: `a.txt` shows atime in 2020 and mtime in 2030 — decoupled timestamps prove `-a` and `-m` work independently.

### Switches

| Token | Meaning |
|---|---|
| `touch -t [[CC]YY]MMDDhhmm[.ss]` | Numeric timestamp; use full 12 digits |
| `touch -d 'STRING'` | `date -d` parser; accepts relative phrases |
| `touch -r REF TARGET` | Copy atime + mtime from REF onto TARGET |
| `touch -a` | Atime only (combine with `-d` or `-t`) |
| `touch -m` | Mtime only (combine with `-d` or `-t`) |
| `find -mtime -N` | Modified less than N×24h ago |
| `find -mtime +N` | Modified MORE than N×24h ago (strict, off-by-one trap) |
| `find -mmin ±N` | Same convention, minutes |
| `find -newer REF` | Modified after REF's mtime (no day rounding) |
| `find -maxdepth N` | Cap recursion depth |
| `find -type f` | Restrict to regular files |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | `touch -t` format | `[[CC]YY]MMDDhhmm[.ss]` — always include the century |
|   | `touch -d` format | Any `date -d` string — "yesterday", ISO 8601, "1 hour ago" |
|   | `touch -r` direction | `touch -r SOURCE TARGET` — copies FROM source TO target |
|   | `-a` vs `-m` | Atime only vs mtime only — decouple the two fields |
|   | `-mtime` sign rule | `-N` newer than · `N` exactly · `+N` STRICTLY older than |
|   | Day rounding | `-mtime 1` = 24–48h ago; `-mtime 0` = less than 24h |
|   | `-newer` precision | Exact mtime comparison — no day rounding, use when `-mtime` is too coarse |
| 🪤 | **Trap Risk T07** | Mixing `-t` (numeric) and `-d` (string) formats — `touch -t '2024-01-15'` silently fails or picks wrong year |
| 🪤 | **Trap Risk T08** | `-mtime +1` means MORE than 1×24h, not "≥ 1 day" — a file modified 30h ago does NOT match `+1` |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| `-a`/`-m` decoupling proven | `stat -c '%x %y' /tmp/touch-lab/a.txt \| grep -q '2020.*2030' && echo OK` | The atime/mtime split is the proof of decoupled timestamps |
| `-r` copied timestamps | `diff <(stat -c '%y' /tmp/touch-lab/reference.txt) <(stat -c '%y' /tmp/touch-lab/copy.txt)` | Empty diff → mtimes match exactly |
| `find -mtime +30` finds lastmonth | `find /tmp/touch-lab -maxdepth 1 -type f -mtime +30 \| grep -c lastmonth.txt` | Must be `1` |
| Transcript captured | `wc -l /tmp/touch-lab/task2/op.txt` | Must be `> 0` |

> **Reboot reasoning:** `/tmp/touch-lab` evaporates at reboot, so the backdated files are gone — but the journal `op.txt` we copy to `/root/rhcsa_journal/lab-07a/` proves which `touch -t`/`-d` formats were exercised. The journal is the persistent record.

### Journal write — BEFORE cleanup

```bash
LAB=lab-07a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/touch-lab/task2/op.txt "$JDIR/op.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    touch -t / -d / -r / -a / -m + find -mtime / -mmin / -newer
COMMANDS: touch -t, touch -d, touch -r, touch -a, touch -m, find -mtime, find -mmin, find -newer
TRAPS:    T07 rehearsed (kept -t numeric vs -d string formats separate) · T08 rehearsed (-mtime +1 = MORE than 1 day, not ≥1)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-07b (Ansible) — replicate this with ansible.builtin.file: state=touch + modification_time:
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -rf /tmp/touch-lab
test -d /tmp/touch-lab || echo "sandbox gone — clean exit"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `touch: invalid date format` | Re-check the `-t` numeric format — `[[CC]YY]MMDDhhmm[.ss]`. Use `-d` for free-form strings. |
| `-r` says "No such file" | The reference argument is missing. Argument order is `touch -r SOURCE TARGET`. |
| `find -mtime +N` returns empty when you expect a match | Off-by-one trap (T08) — `+N` is STRICT. Try `+N-1` or `-mmin +M`. |
| `find` shows directories you don't want | Add `-type f` to restrict to regular files. |
| `touch -a` does not move atime | Mount option `noatime` blocks atime updates — `mount \| grep noatime`. |
| `find /var/log` floods with "Permission denied" | Append `2>/dev/null`, or run as root. |

> **STOP — paste the `═══ find -mtime +7 ═══` section from `op.txt` showing `lastweek.txt` AND `lastmonth.txt` before moving on to Lab 07b.**

---

## Lab 07a Checklist (2 tasks)

- [ ] Task 1 — `touch` creates files + `stat -c '%x %y %z %w'` reads all four timestamps + side-effect map proven (`chmod` bumps ctime only, `cat` bumps atime only) + journal evidence
- [ ] Task 2 — Explicit timestamps with `touch -t / -d / -r / -a / -m` + age-based search with `find -mtime / -mmin / -newer` + journal evidence

---

## 🔗 Related Labs in the Trilogy

| Lab | Connection |
|---|---|
| **Lab 07b** — Creating Files & Setting Timestamps via Ansible | The declarative form: `ansible.builtin.file: state=touch` with `modification_time:` / `access_time:` |
| **Lab 07c** — Verifying Timestamps | The auditor seat: `stat` + `find -newer` + `ls --time=atime/ctime` + persistence proof |
| Lab 06 — `ls -l`, `ls -lZ` | Prerequisite — `ls -l` shows mtime by default; this lab goes deeper |
| Lab 14a — File Searching with `find` | `find -mtime` and `-newer` are the timestamp predicates that combine with `-name`, `-size`, `-perm` |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
