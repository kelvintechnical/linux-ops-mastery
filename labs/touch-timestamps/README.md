# Lab 07: Creating Empty Files and Timestamps — `touch`, `stat`, `find -mtime`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Career arcs covered:** RHCSA EX200 (file creation, log rotation, ownership), RHCE EX294 (Ansible `file:` module timestamps), CKA (volume mtime probes), RHCA — RH342 (forensic time analysis)
- **Prerequisite:** Lab 06 (`ls -l`, `ls -Z`)
- **Time Estimate:** 30–45 minutes
- **Tasks:** 3 (ADHD spec)
- **Practice Directory (lab-wide rotation #07):** `/boot`
- **Sandbox:** `/tmp/touch-lab`
- **Traps rehearsed this lab:** **T07** (Wrong UUID in fstab — always copy-paste from blkid) · **T43** (Getting stuck >10 min on one task)

> **This lab's practice directory is: `/boot`** — every task references it in at least two commands.
>
> ⚠️ **Important:** we will **read** `/boot` (timestamps, blkid output, filenames) and we will **write** only inside `/tmp/touch-lab`. Never `touch` or modify files inside `/boot` — you can break the bootloader.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T07 T43"
echo "📁  PRACTICE DIR: /boot"
echo ""
echo "💡 blkid view of /boot (we read this, we do NOT edit fstab):"
blkid 2>/dev/null | grep -E "boot| /boot " || lsblk -f | head -10
```

> **STOP — paste header output before running setup.**

---

## 🎯 Objective

Create empty files with `touch`, control atime/mtime/ctime, time-travel files with `touch -d`/`-t`, inspect with `stat`, and find files by age with `find -mtime`/`-mmin`. Along the way you will read `/boot` filenames and timestamps (e.g. `vmlinuz-*`, `initramfs-*`) without touching them, and you will rehearse the **`blkid` discipline** that prevents fstab UUID typos (T07).

---

## 🧠 Concept: Linux Tracks THREE Times on Every File

| Time | Stored as | Updated when |
|---|---|---|
| **atime** | access time | The file is **read** (note: `relatime` mount option throttles this) |
| **mtime** | modification time | The file's **contents** change |
| **ctime** | change time | The **inode metadata** changes (perms, owner, link count) |
| (sometimes) **btime** | birth/creation time | The file was created — only on some filesystems (ext4 with `crtime`, XFS) |

```
touch FILE          → updates atime AND mtime (also creates if missing)
touch -a FILE       → atime only
touch -m FILE       → mtime only
touch -d "STR" FILE → set both to parsed date/time
touch -t YYMMDDHHMM FILE → set both to a specific stamp
touch -r REF FILE   → copy times from REF onto FILE
```

> **Why this matters on RHCSA:** log rotation, backup decisions, `find -mtime`, and the bootloader's incremental updates all depend on these stamps. `ls -lu` shows atime, `ls -lc` shows ctime, `ls -l` (default) shows mtime. `stat` shows all three.

---

## 🚦 Lab-Wide Setup — Run This BEFORE Task 1

```bash
sudo -i
mkdir -p /tmp/touch-lab
cd /tmp/touch-lab

cat > /tmp/touch-lab/THIS_DIRECTORY.txt <<'EOF'
/boot — Kernel, initramfs, and GRUB bootloader

The files the firmware hands control to at power-on live here: vmlinuz
(the compressed kernel), initramfs (the early root filesystem image),
System.map, config-*, and the grub2 configuration tree.

Why it exists: the bootloader runs *before* the real root filesystem is
mounted, so the kernel and its early-userspace image must be on a small,
self-contained partition that GRUB can read with simple drivers.

What lives inside it: vmlinuz-<kernel>, initramfs-<kernel>.img,
System.map-<kernel>, config-<kernel>, /boot/grub2/grub.cfg,
/boot/loader/entries/ (BLS entries), and on UEFI systems /boot/efi.

Why RHCSA cares: kernel upgrades, GRUB regeneration with
grub2-mkconfig, rd.break recovery, and the absolute rule "never let
/boot fill up to 100% — package upgrades break." The mount point is
referenced by UUID in /etc/fstab (T07 trap — copy from blkid, never type).
EOF

cat /tmp/touch-lab/THIS_DIRECTORY.txt
echo ""
echo "Snapshot of /boot (we will NOT modify any of this):"
ls -l /boot 2>/dev/null | head -n 10
echo ""
echo "blkid for /boot (T07 reminder — UUIDs are copy-paste only):"
blkid 2>/dev/null | grep -E "boot" | tee /tmp/touch-lab/boot-blkid.txt
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

# The 3 Tasks

---

## Task 1 — `touch` Basics: Create Empty Files, Update Timestamps

### a) Directory Context

**Practice directory this task:** `/boot` (read-only reference) and `/tmp/touch-lab` (sandbox).
We will compare timestamps of real `/boot` files (kernel, initramfs) against fresh files we create with `touch`.

### b) 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/touch-lab
date -Is > task01-warmup.log
ls -l /boot 2>&1 | head -n 5 | tee task01-boot-head.txt
ls -lZ /boot 2>&1 | head -n 3 | tee task01-boot-context.txt
echo "boot entries: $(ls /boot 2>/dev/null | wc -l)"
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Create empty files with `touch`, prove that `touch` on an existing file updates atime + mtime, and read all three timestamps with `stat`.

### d) Main Command Block

```bash
cd /tmp/touch-lab

touch file1.txt file2.txt file3.txt
ls -l file*.txt

stat file1.txt | tee task01-stat-before.txt

sleep 2
touch file1.txt
stat file1.txt | tee task01-stat-after.txt

echo "---"
echo "diff in timestamps (mtime should advance, ctime should advance, atime depends on mount opts):"
diff task01-stat-before.txt task01-stat-after.txt || true

echo "---"
echo "Compare to a REAL /boot file (read-only):"
stat /boot/vmlinuz-$(uname -r) 2>/dev/null | head -n 8 || stat $(ls /boot/vmlinuz-* 2>/dev/null | head -1) | head -n 8

echo "---"
echo "ls views of different times:"
ls -l  file1.txt    # mtime
ls -lu file1.txt    # atime
ls -lc file1.txt    # ctime
```

### e) Human-Readable Breakdown

- `touch file1 file2 file3` — create three empty files in one command.
- `stat FILE` — show inode, size, blocks, perms, all three times.
- `sleep 2; touch file1` — wait so the second timestamp differs, then re-touch.
- `diff` — confirm the timestamps changed.
- `stat /boot/vmlinuz-*` — read a real kernel file's stamps without modifying it.
- `ls -l` / `ls -lu` / `ls -lc` — view mtime / atime / ctime respectively.
- `|| true` — keep going if `diff` finds differences (it returns 1 when files differ, which would otherwise be treated as an error under strict scripts).

### f) Reading It Left to Right

`stat /boot/vmlinuz-$(uname -r) 2>/dev/null | head -n 8 || stat $(ls /boot/vmlinuz-* 2>/dev/null | head -1) | head -n 8`

1. `stat` — show file stats.
2. `/boot/vmlinuz-$(uname -r)` — current running kernel's image, using command substitution.
3. `2>/dev/null` — silence the error if the running kernel's image is not present (rare).
4. `|| stat $(ls /boot/vmlinuz-* | head -1)` — fallback: pick any kernel image in `/boot`.
5. `| head -n 8` — keep the top 8 lines of stat output.

### g) The Story

`touch` is one of the most-typed commands on Linux. It exists for two reasons: (1) create an empty file for a sentinel/lock/log to follow, and (2) update a file's mtime so other tools (rsync, find, make, log rotators) see it as "new." On the exam, you'll touch sentinel files like `/root/done.txt` to prove task completion. In production you'll touch log files before `chown` to pre-create them with the right ownership.

### h) Expected Output

```text
-rw-r--r--. 1 root root 0 May 27 14:02 file1.txt
-rw-r--r--. 1 root root 0 May 27 14:02 file2.txt
-rw-r--r--. 1 root root 0 May 27 14:02 file3.txt
  File: file1.txt
  Size: 0  Blocks: 0  IO Block: 4096  regular empty file
Device: ...  Inode: ...  Links: 1
Access: (0644/-rw-r--r--)  Uid: (0/root) Gid: (0/root)
Context: unconfined_u:object_r:user_tmp_t:s0
Access: 2026-05-27 14:02:01.xxx -0400
Modify: 2026-05-27 14:02:01.xxx -0400
Change: 2026-05-27 14:02:01.xxx -0400
 Birth: 2026-05-27 14:02:01.xxx -0400
... (diff shows Modify and Change advancing by 2s, Access varies by relatime)
  File: /boot/vmlinuz-5.14.0-...
  Size: 12000000+   Blocks: ...  IO Block: 4096  regular file
...
-rw-r--r--. 1 root root 0 May 27 14:02:03 file1.txt   (mtime)
-rw-r--r--. 1 root root 0 May 27 14:02:03 file1.txt   (atime)
-rw-r--r--. 1 root root 0 May 27 14:02:03 file1.txt   (ctime)
```

### i) Switches Table

| Token | Meaning |
|---|---|
| `touch FILE` | Create empty file or update atime+mtime |
| `stat FILE` | Show inode + all three times + context |
| `ls -l` | Default: shows mtime |
| `ls -lu` | Show atime instead of mtime |
| `ls -lc` | Show ctime instead of mtime |
| `sleep N` | Pause N seconds |
| `diff A B` | Compare two files line-by-line |
| `\|\| true` | Force success exit even if previous failed |
| `$(uname -r)` | Running kernel release (e.g. `5.14.0-...`) |
| `2>/dev/null` | Suppress errors |

### j) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | `touch` | Create or update atime+mtime |
|   | atime | When file was read |
|   | mtime | When contents changed |
|   | ctime | When inode metadata changed |
|   | btime | Birth time (some FS only) |
|   | `stat` | Display all four (plus SELinux ctx) |
|   | `ls -lu` / `ls -lc` | Read atime / ctime quickly |
|   | `relatime` | Default mount opt that throttles atime updates |
|   | `$(uname -r)` | Command substitution for kernel version |
| 🪤 **Trap Risk (T07)** | Wrong UUID in fstab — always copy-paste from blkid | We are reading `blkid` output for `/boot` in setup. **Never** transcribe a UUID by hand; copy-paste from `blkid` directly into vim/nano |

### k) 🧹 Cleanup

```bash
LAB=lab07
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "$JDIR/notes.txt" <<'EOF'
TOPIC:    touch basics + 4 timestamps (atime/mtime/ctime/btime)
COMMANDS: touch, stat, ls -lu, ls -lc, $(uname -r)
TRAPS:    T07 (blkid copy-paste discipline)
MISSED:   —
NEXT:     task2 — touch -d / -t / -r time manipulation
EOF
echo "Journal written: $(ls -la $JDIR)"

cd /tmp/touch-lab
rm -f file1.txt file2.txt file3.txt task01-*.txt
echo "exit was: $?"
```

### l) Troubleshoot Table

| Symptom | Fix |
|---|---|
| `touch: cannot touch '/boot/...'` | You tried to write to /boot — STOP. Sandbox is `/tmp/touch-lab` |
| atime unchanged after read | Normal with `relatime` mount option |
| `stat /boot/vmlinuz-$(uname -r)` fails | Use the fallback `ls /boot/vmlinuz-*` pattern |
| `Permission denied` on `/boot` files | You are not root — `sudo -i` first |

### m) STOP

> **STOP — paste output before Task 2.**

### n) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| Sandbox empty | `ls /tmp/touch-lab` | Just THIS_DIRECTORY.txt + boot-blkid.txt remain |
| Journal entry | `cat /root/rhcsa_journal/lab07/task1/done.txt` | Survives reboot |
| `/boot` untouched | `stat /boot/vmlinuz-$(uname -r) \| grep Modify` | Stamp should be the original install date |

---

## Task 2 — `touch -d`, `touch -t`, `touch -r`: Time Manipulation

### a) Directory Context

**Practice directory this task:** `/boot` (reference) and `/tmp/touch-lab` (sandbox).
We will copy a `/boot` file's timestamp onto a sandbox file with `touch -r`, simulating the "preserve mtime when staging an upgrade" pattern.

### b) 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/touch-lab
date -Is | tee task02-warmup.log
ls /boot 2>/dev/null | wc -l >> task02-warmup.log
cat task02-warmup.log
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Set a file's timestamp to a specific moment with `touch -d` and `touch -t`, then **copy** a reference file's timestamp onto another file with `touch -r`.

### d) Main Command Block

```bash
cd /tmp/touch-lab
touch backdated.txt
touch -d "2020-01-15 09:00:00" backdated.txt
stat backdated.txt | grep -E "Modify|Access"

touch -t 199912312359 yk2.txt
stat yk2.txt | grep -E "Modify|Access"

touch -d "now - 7 days" lastweek.txt
stat lastweek.txt | grep -E "Modify"

REF=$(ls /boot/vmlinuz-* 2>/dev/null | head -1)
echo "Using reference: $REF"
touch -r "$REF" kernel-copy.txt
echo "--- kernel reference ---"
stat "$REF" | grep -E "Modify"
echo "--- our file matches ---"
stat kernel-copy.txt | grep -E "Modify"

ls -l --time=mtime *.txt | sort -k 6,7
```

### e) Human-Readable Breakdown

- `touch -d "2020-01-15 09:00:00" FILE` — set mtime+atime to that absolute timestamp.
- `touch -t 199912312359 FILE` — same idea, but using the older `[[CC]YY]MMDDhhmm[.ss]` format (Y2K-eve example).
- `touch -d "now - 7 days" FILE` — `date` parser supports relative time.
- `touch -r REF FILE` — copy timestamps **from** `REF` **to** `FILE`. Useful when staging files that should look as old as their source.
- `ls -l --time=mtime ... | sort -k 6,7` — sort listing by month/day columns.

### f) Reading It Left to Right

`touch -r "$REF" kernel-copy.txt`

1. `touch` — the command.
2. `-r REFERENCE` — use REFERENCE's timestamps.
3. `"$REF"` — the kernel image path, quoted to survive spaces (defensive habit).
4. `kernel-copy.txt` — destination file (created if missing).

### g) The Story

`touch -r` is the unsung hero of careful sysadmin work. When you back up a config file before editing — `cp /etc/foo.conf /etc/foo.conf.bak.$(date +%F)` — the backup gets a fresh mtime, which can confuse later forensic timelines. The pro move is `cp -a` (preserves stamps) or `cp file foo.bak; touch -r file foo.bak`. The `touch -t` and `touch -d` forms let you build test fixtures: "give me files aged exactly 30, 60, and 90 days ago" for `find -mtime` rehearsal (Task 3).

### h) Expected Output

```text
Modify: 2020-01-15 09:00:00.000000000 -0500
Access: 2020-01-15 09:00:00.000000000 -0500
Modify: 1999-12-31 23:59:00.000000000 -0500
Access: 1999-12-31 23:59:00.000000000 -0500
Modify: 2026-05-20 14:05:12.xxx -0400          (7 days ago)
Using reference: /boot/vmlinuz-5.14.0-...
--- kernel reference ---
Modify: 2024-08-12 03:11:42.000000000 -0400
--- our file matches ---
Modify: 2024-08-12 03:11:42.000000000 -0400
-rw-r--r--. 1 root root 0 Dec 31  1999 yk2.txt
-rw-r--r--. 1 root root 0 Jan 15  2020 backdated.txt
-rw-r--r--. 1 root root 0 Aug 12  2024 kernel-copy.txt
-rw-r--r--. 1 root root 0 May 20 14:05 lastweek.txt
```

### i) Switches Table

| Token | Meaning |
|---|---|
| `touch -d "STRING"` | Parse human date (also relative: `-d "now - 7 days"`) |
| `touch -t YYMMDDHHMM` | Specific stamp, compact format |
| `touch -r REF FILE` | Copy timestamps from REF |
| `touch -a` | atime only |
| `touch -m` | mtime only |
| `--time=mtime/atime/ctime` | Choose which time `ls -l` shows |
| `sort -k 6,7` | Sort on columns 6 and 7 (month, day) |

### j) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | `touch -d` | Set time via human-readable date |
|   | `touch -t` | Set time via YYMMDDHHMM |
|   | `touch -r` | Copy timestamps from reference |
|   | `touch -a` | atime only |
|   | `touch -m` | mtime only |
|   | `cp -a` (preview) | Preserves timestamps and contexts (Lab 08) |
|   | Building fixtures | Use `touch -d "now - N days"` to set up `find -mtime` drills |
| 🪤 **Trap Risk (T43)** | Getting stuck >10 min | `touch -d` parsing is finicky. If a string fails, switch to `touch -t YYMMDDHHMM` and move on |

### k) 🧹 Cleanup

```bash
LAB=lab07
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "$JDIR/notes.txt" <<'EOF'
TOPIC:    touch -d / -t / -r time manipulation
COMMANDS: touch -d, touch -t, touch -r, touch -a, touch -m
TRAPS:    T43 (don't loop on date-parse failures)
MISSED:   —
NEXT:     task3 — find -mtime + stat capstone
EOF
echo "Journal written: $(ls -la $JDIR)"

cd /tmp/touch-lab
rm -f backdated.txt yk2.txt lastweek.txt kernel-copy.txt task02-warmup.log
echo "exit was: $?"
```

### l) Troubleshoot Table

| Symptom | Fix |
|---|---|
| `touch: invalid date format` | Fall back to `-t YYMMDDHHMM` (e.g. `202005271400`) |
| `Access` time did not change | The mount has `noatime`; check with `mount \| grep $(df . \| tail -1 \| awk '{print $1}')` |
| `touch -r REF` fails | `REF` doesn't exist; verify with `ls "$REF"` |
| ls sort looks wrong | Sort is alphanumeric; use `--time-style=full-iso` and sort on the right column |

### m) STOP

> **STOP — paste output before Task 3.**

### n) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| No files leaked outside sandbox | `find / -name "yk2.txt" -o -name "backdated.txt" 2>/dev/null` | Should return nothing (already cleaned) |
| Journal task2 | `cat /root/rhcsa_journal/lab07/task2/done.txt` | Reboot-proof |

---

## Task 3 — `find -mtime`, `find -mmin`, `stat` Capstone

### a) Directory Context

**Practice directory this task:** `/boot` (read-only target for `find`) and `/tmp/touch-lab` (where we build the fixture).

### b) 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/touch-lab
date -Is | tee task03-warmup.log
find /boot -maxdepth 1 -type f 2>/dev/null | wc -l >> task03-warmup.log
cat task03-warmup.log
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Build a fixture of files with known ages, then practice `find -mtime` / `-mmin` / `-newer` queries against both the fixture and read-only `/boot`.

### d) Main Command Block

```bash
cd /tmp/touch-lab
mkdir -p fixture
touch fixture/now.txt
touch -d "now - 10 minutes" fixture/10min.txt
touch -d "now - 1 hour"      fixture/1hour.txt
touch -d "now - 2 days"      fixture/2days.txt
touch -d "now - 10 days"     fixture/10days.txt
touch -d "now - 60 days"     fixture/60days.txt

ls -lh --time-style=full-iso fixture/

echo ""
echo "=== Files modified in the LAST 5 MINUTES (fixture) ==="
find fixture -type f -mmin -5

echo "=== Files modified MORE THAN 7 DAYS AGO (fixture) ==="
find fixture -type f -mtime +7

echo "=== Files modified within the LAST 24 hours (fixture) ==="
find fixture -type f -mtime -1

echo "=== Files in /boot modified MORE THAN 7 DAYS AGO ==="
find /boot -maxdepth 1 -type f -mtime +7 2>/dev/null | head -n 10

echo "=== Newer-than reference ==="
find fixture -type f -newer fixture/2days.txt

echo "=== stat capstone — full report on a fixture file ==="
stat --format='Name: %n%nSize: %s%nMode: %A (%a)%nOwner: %U:%G%nMTime: %y%nCTime: %z%nATime: %x%nBirth: %w' fixture/2days.txt

cd /tmp/touch-lab
echo "fixture line count: $(ls fixture | wc -l)"
```

### e) Human-Readable Breakdown

- `mkdir fixture; touch -d "now - N days/hours/minutes" ...` — build a known-age dataset.
- `find PATH -mmin -5` — modified less than 5 minutes ago (negative = "less than").
- `find PATH -mtime +7` — modified more than 7×24 hours ago (positive = "more than").
- `find PATH -mtime -1` — modified within the last 24 hours.
- `find PATH -newer REF` — newer than the reference file's mtime.
- `stat --format='...'` — custom output with `%n` (name), `%s` (size), `%A`/`%a` (mode), `%U:%G` (owner), `%y` (mtime), `%z` (ctime), `%x` (atime), `%w` (btime).

### f) Reading It Left to Right

`find /boot -maxdepth 1 -type f -mtime +7 2>/dev/null | head -n 10`

1. `find` — file finder.
2. `/boot` — starting directory.
3. `-maxdepth 1` — do not descend into subdirectories (e.g. `/boot/grub2`).
4. `-type f` — regular files only.
5. `-mtime +7` — mtime more than 7 days ago.
6. `2>/dev/null` — suppress permission-denied noise.
7. `| head -n 10` — keep first 10 results.

### g) The Story

This is the entire muscle memory behind log rotation and stale-file cleanup. `logrotate` does `find /var/log -mtime +30 -delete` under the hood. Backup scripts run `find /data -mtime -1 -type f | xargs rsync`. RHCSA exam: "Find all files in `/var/log` older than 30 days and save the list to `/root/old-logs.txt`." With this lab, that's two minutes of typing, not panic.

The `-mtime` numbers are tricky: `+N` = older than N days, `-N` = newer than N days, plain `N` = exactly N days ago (rounded). Same with `-mmin` for minutes.

### h) Expected Output

```text
-rw-r--r--. 1 root root 0 2026-05-27 14:10:00 ... fixture/now.txt
-rw-r--r--. 1 root root 0 2026-05-27 14:00:00 ... fixture/10min.txt
-rw-r--r--. 1 root root 0 2026-05-27 13:10:00 ... fixture/1hour.txt
-rw-r--r--. 1 root root 0 2026-05-25 14:10:00 ... fixture/2days.txt
-rw-r--r--. 1 root root 0 2026-05-17 14:10:00 ... fixture/10days.txt
-rw-r--r--. 1 root root 0 2026-03-28 14:10:00 ... fixture/60days.txt

=== Files modified in the LAST 5 MINUTES (fixture) ===
fixture/now.txt

=== Files modified MORE THAN 7 DAYS AGO (fixture) ===
fixture/10days.txt
fixture/60days.txt

=== Files modified within the LAST 24 hours (fixture) ===
fixture/now.txt
fixture/10min.txt
fixture/1hour.txt

=== Files in /boot modified MORE THAN 7 DAYS AGO ===
/boot/config-5.14.0-...
/boot/initramfs-...
/boot/symvers-...
/boot/System.map-...
/boot/vmlinuz-...

=== Newer-than reference ===
fixture/now.txt
fixture/10min.txt
fixture/1hour.txt

=== stat capstone — full report on a fixture file ===
Name: fixture/2days.txt
Size: 0
Mode: -rw-r--r-- (644)
Owner: root:root
MTime: 2026-05-25 14:10:00.000000000 -0400
CTime: 2026-05-27 14:10:01.xxx -0400
ATime: 2026-05-25 14:10:00.000000000 -0400
Birth: 2026-05-27 14:10:00.xxx -0400

fixture line count: 6
```

Note that `CTime` is "now" (we just created the file 1 second ago) but `MTime` is 2 days back (set by `touch -d`). This is the difference between **inode change** (ctime — can only ever be "now or later") and **content modify** (mtime — can be any time including past).

### i) Switches Table

| Token | Meaning |
|---|---|
| `find PATH -mtime -N` | mtime within last N days |
| `find PATH -mtime +N` | mtime older than N days |
| `find PATH -mtime N`  | mtime exactly N days ago (rounded) |
| `find PATH -mmin -N` | mtime within last N minutes |
| `find PATH -mmin +N` | mtime older than N minutes |
| `find PATH -newer REF` | newer than REF's mtime |
| `find PATH -maxdepth N` | descend at most N levels |
| `find PATH -type f` | regular files only |
| `find PATH -type d` | directories only |
| `stat --format='%n %s %y'` | custom output: name, size, mtime |
| `--time-style=full-iso` | ISO 8601 timestamps in `ls` |

### j) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | `-mtime` semantics | `-N` recent, `+N` old, `N` exactly |
|   | `-mmin` granularity | Minutes instead of days |
|   | `-newer REF` | Reference-relative query |
|   | `-maxdepth N` | Bound the recursion |
|   | `stat --format` | Custom output assembly |
|   | mtime vs ctime | Content vs inode change |
|   | btime | Birth/creation time (may not exist on all FS) |
|   | Log rotation pattern | `find /var/log -mtime +30 -delete` |
| 🪤 **Trap Risk (T07)** | Wrong UUID in fstab — always copy-paste from blkid | We read blkid for /boot in setup. If you ever transcribe a UUID by hand into fstab, the system fails to boot — recovery is 20 minutes of `rd.break` panic |
| 🪤 **Trap Risk (T43)** | Getting stuck >10 min | If a `find` query returns "wrong" results, double-check the sign of N. Spending 15 min debugging `-mtime 7` vs `-mtime +7` is the canonical example of this trap |

### k) 🧹 Cleanup

```bash
LAB=lab07
TASK=task3
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "$JDIR/notes.txt" <<'EOF'
TOPIC:    find -mtime / -mmin / -newer + stat capstone
COMMANDS: find -mtime, find -mmin, find -newer, stat --format
TRAPS:    T07 + T43 (both rehearsed)
MISSED:   —
NEXT:     Lab 08 — cp / cp -R / cp -a (/home practice dir)
EOF
echo "Journal written: $(ls -la $JDIR)"

rm -rf /tmp/touch-lab
echo "exit was: $?"
```

### l) Troubleshoot Table

| Symptom | Fix |
|---|---|
| `find -mtime +7` returns nothing | Your fixture files may not be old enough; check with `stat fixture/*` |
| `find /boot` permission denied lines | Pipe to `2>/dev/null` |
| `--time-style=full-iso` not recognized | Older `ls`; use `--time-style=long-iso` or default |
| `stat --format='%w'` shows `-` | Filesystem does not track btime (XFS without `crtime`, ext4 without `crtime`) |

### m) STOP

> **STOP — paste output before declaring Lab 07 complete.**

### n) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| Sandbox removed | `test -d /tmp/touch-lab \|\| echo CLEAN` | Confirms `rm -rf` |
| `/boot` integrity | `find /boot -maxdepth 1 -type f -newer /etc/hostname 2>/dev/null` | If THIS returns files, *someone* modified /boot during the lab — flag it |
| All 3 journal entries | `find /root/rhcsa_journal/lab07 -name done.txt \| wc -l` (expect 3) | Reboot-proof study record |
| `fstab` untouched | `stat /etc/fstab \| grep Modify` | Mtime should be the original system install date (T07 paranoia check) |

> **Reboot question:** "If we rebooted now, would the `/boot` files still be exactly as we left them?" — Answer: yes, because we never modified `/boot`. If you accidentally touched anything in `/boot`, run `rpm -Va` to detect drift before rebooting.

---

## 🪤 Trap Registry Update — End of Lab 07

| Trap ID | Category | Rehearsed? | If hit, repeat in |
|---|---|---|---|
| T07 | fstab / Mounts | ✅ | — |
| T43 | Meta / Strategy | ✅ | — |

3-lab trap window (05+06+07): **T41, T43, T01, T02, T07** = **5 unique traps** ✓

Next lab (08) traps: **T32** (setfacl default ACL on directories is a separate command) · **T31** (usermod -G without -a).

---

## 🎓 What You Now Own

1. `touch FILE` to create empty files and bump timestamps.
2. `touch -d "now - N days"` / `touch -t YYMMDDHHMM` / `touch -r REF` to set or copy stamps.
3. `stat FILE` to read all four times + perms + context.
4. `ls -l` / `-lu` / `-lc` to view mtime / atime / ctime.
5. `find -mtime ±N` and `-mmin ±N` for age queries.
6. `find -newer REF` for reference-relative queries.
7. `find -maxdepth N` to bound recursion.
8. The blkid copy-paste discipline (T07) that prevents fstab disasters.
