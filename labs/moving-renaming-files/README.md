# Lab 10: Moving and Renaming Files — `mv`, `mv -i`, `mv -n`, atomic renames

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Career arcs covered:** RHCSA EX200 (log rotation, fstab safety, config staging), RHCE EX294 (Ansible atomic file replace), CKA (ConfigMap atomic swaps), RHCA — RH358 (atomic file update patterns)
- **Prerequisite:** Lab 09 (`ln`, `ln -s`, `readlink`)
- **Time Estimate:** 35–50 minutes
- **Tasks:** 3 (ADHD spec)
- **Practice Directory (lab-wide rotation #10):** `/var`
- **Sandbox:** `/tmp/mv-lab`
- **Traps rehearsed this lab:** **T25** (firewalld `--permanent` without `--reload`) · **T34** (`/etc/cron.d/` needs username field — 6 fields; user crontab is 5)

> **This lab's practice directory is: `/var`** — every task references it in at least two commands.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T25 T34"
echo "📁  PRACTICE DIR: /var"
echo ""
echo "💡 /var occupants (we read; we use /tmp/mv-lab for writes):"
ls -ld /var /var/log /var/spool /var/lib 2>/dev/null
df -h /var | head -n 2
```

> **STOP — paste header output before running setup.**

---

## 🎯 Objective

Rename and move files safely. By the end you will use `mv`, `mv -i`, `mv -n`, `mv -v`, and the **atomic rename pattern** (`write tmpfile; mv tmpfile final`) that every well-engineered Linux service uses to swap configs without dropping requests.

---

## 🧠 Concept: `mv` Is Not One Operation

`mv` does **two different things** depending on the source and destination paths:

| Case | What actually happens at the syscall level |
|---|---|
| Source and dest on the **same filesystem** | `rename(2)` — an atomic directory entry update. **Inode unchanged, mtime unchanged, content unchanged.** |
| Source and dest on **different filesystems** | `cp -a + rm` — copy contents, copy metadata, then delete the source. **New inode. Not atomic.** |

```
# Same FS — atomic rename, instant, zero data copied
mv /var/log/messages.tmp /var/log/messages

# Cross FS — copy + delete, NOT atomic, can leave half-state
mv /tmp/big.iso /mnt/usb/big.iso
```

**Atomic rename is the production-grade pattern for swapping configs:**

```bash
# Bad — readers might see a half-written file
echo "$NEW_CONFIG" > /etc/nginx/nginx.conf

# Good — write to a tmpfile on the SAME directory, then atomic rename
echo "$NEW_CONFIG" > /etc/nginx/nginx.conf.new
mv /etc/nginx/nginx.conf.new /etc/nginx/nginx.conf   # atomic
```

The tmpfile MUST be on the same filesystem as the final destination, or `mv` falls back to copy+delete (not atomic). Always use the same directory.

---

## 🚦 Lab-Wide Setup — Run This BEFORE Task 1

```bash
sudo -i
mkdir -p /tmp/mv-lab
cd /tmp/mv-lab

cat > /tmp/mv-lab/THIS_DIRECTORY.txt <<'EOF'
/var — Variable data: logs, mail, databases, spools

/var holds data that grows and changes over time. /var/log has system
logs. /var/spool has print and mail queues. /var/lib has package manager
databases. /var/cache has package and DNS caches.

Why it exists: separating static configuration (/etc) and static binaries
(/usr) from data-that-grows means /var can be put on its own partition or
LV. Filling /var (logs filling /var/log; rpm DB in /var/lib/rpm) is a
common production outage cause.

What lives inside it: /var/log/messages, /var/log/secure, /var/log/audit,
/var/spool/cron, /var/spool/at, /var/spool/postfix, /var/lib/rpm (the rpm
database), /var/lib/systemd, /var/cache/dnf.

Why RHCSA cares: log rotation, fstab persistence checks on /var mounts,
cron files in /var/spool/cron (single-user crontabs), and the rpm DB. The
"mv from .new to final" pattern that log rotators and config managers
use is foundational to safe administration.
EOF

cat /tmp/mv-lab/THIS_DIRECTORY.txt
echo ""
echo "Build fixture files:"
echo "v1: original config" > /tmp/mv-lab/app.conf
echo "v2: improved config" > /tmp/mv-lab/app.conf.new
mkdir -p /tmp/mv-lab/archive /tmp/mv-lab/staging
for f in log1 log2 log3 log4 log5; do
  echo "$f content $(date -Is)" > /tmp/mv-lab/$f.log
done
ls -l /tmp/mv-lab/
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

# The 3 Tasks

---

## Task 1 — Rename in Place: `mv FROM TO` (Same Directory)

### a) Directory Context

**Practice directory this task:** `/var` (read-only reference for `/var/log` naming conventions) and `/tmp/mv-lab` (sandbox).
Renaming is just `mv` with both arguments in the same directory.

### b) 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/mv-lab
date -Is | tee task01-warmup.log
ls /var/log 2>/dev/null | head -n 5 | tee -a task01-warmup.log
ls -l /var/log/messages /var/log/secure 2>&1 | tee -a task01-warmup.log
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Rename files in place, prove the inode is preserved (atomic rename on same FS), and use `mv` to add date stamps the way real log rotation scripts do.

### d) Main Command Block

```bash
cd /tmp/mv-lab

echo "=== Before — note the inode ==="
ls -li log1.log

INODE_BEFORE=$(stat --format='%i' log1.log)
echo "Inode before: $INODE_BEFORE"

mv log1.log log1.log.$(date +%F)
ls -li log1.log.* 2>/dev/null

INODE_AFTER=$(stat --format='%i' log1.log.* 2>/dev/null | head -1)
echo "Inode after:  $INODE_AFTER"
if [ "$INODE_BEFORE" = "$INODE_AFTER" ]; then
  echo "✓ Same inode — atomic rename succeeded"
else
  echo "✗ Inode changed — was this a cross-FS move?"
fi

echo ""
echo "=== Rename multiple files via brace expansion + loop ==="
for f in log2 log3; do
  mv -v "$f.log" "$f.log.$(date +%F)"
done

echo ""
echo "=== Show /var/log naming convention for context ==="
ls /var/log/messages* 2>/dev/null | head -n 5
ls /var/log/secure* 2>/dev/null | head -n 5

echo ""
echo "=== Result ==="
ls -l /tmp/mv-lab/
```

### e) Human-Readable Breakdown

- `mv log1.log log1.log.$(date +%F)` — renames `log1.log` to `log1.log.2026-05-27` (or whatever today is).
- `stat --format='%i'` — extract inode number.
- The inode comparison **proves** the rename was an atomic `rename(2)` syscall, not a copy+delete.
- The `for` loop renames `log2.log` and `log3.log` similarly. This is the building block of log rotation.
- `/var/log/messages-20260520` style names exist because of this exact pattern, run by `logrotate` nightly.

### f) Reading It Left to Right

`mv log1.log log1.log.$(date +%F)`

1. `mv` — move/rename command.
2. `log1.log` — source path.
3. `log1.log.$(date +%F)` — destination path. `$(date +%F)` expands to today in ISO format like `2026-05-27`. Resulting filename: `log1.log.2026-05-27`.

Because source and destination are both in `/tmp/mv-lab/`, the kernel does a `rename(2)` syscall: just update the directory entry to point at the same inode under a new name. Zero bytes copied. The mtime of the file does not change.

### g) The Story

`mv` is one of the safest operations in Linux — when it's same-FS. The directory entry update is atomic from the perspective of any other process: at no point does a reader see the file under both names or neither name. This is why `logrotate` works without dropping log lines, why config managers do `write tmpfile; mv tmpfile final`, and why `mv` is the official way to "publish" a new version of a file.

Cross-FS, `mv` is just `cp -a + rm`. That is not atomic. A reader could see the partial copy. The fix is to **stage the file on the same FS first**, then do the final `mv` in one move.

### h) Expected Output

```text
=== Before — note the inode ===
12345678 -rw-r--r--. 1 root root 36 May 27 15:40 log1.log
Inode before: 12345678

12345678 -rw-r--r--. 1 root root 36 May 27 15:40 log1.log.2026-05-27
Inode after:  12345678
✓ Same inode — atomic rename succeeded

=== Rename multiple files ===
renamed 'log2.log' -> 'log2.log.2026-05-27'
renamed 'log3.log' -> 'log3.log.2026-05-27'

=== /var/log naming convention ===
/var/log/messages
/var/log/messages-20260520
/var/log/messages-20260513
...
/var/log/secure
/var/log/secure-20260520
...

=== Result ===
-rw-r--r--. 1 root root  36 May 27 15:40 log1.log.2026-05-27
-rw-r--r--. 1 root root  36 May 27 15:40 log2.log.2026-05-27
-rw-r--r--. 1 root root  36 May 27 15:40 log3.log.2026-05-27
-rw-r--r--. 1 root root  36 May 27 15:40 log4.log
-rw-r--r--. 1 root root  36 May 27 15:40 log5.log
-rw-r--r--. 1 root root  21 May 27 15:40 app.conf
-rw-r--r--. 1 root root  21 May 27 15:40 app.conf.new
drwxr-xr-x. 2 root root   6 May 27 15:40 archive
drwxr-xr-x. 2 root root   6 May 27 15:40 staging
-rw-r--r--. 1 root root 250 May 27 15:40 task01-warmup.log
-rw-r--r--. 1 root root 700 May 27 15:40 THIS_DIRECTORY.txt
```

### i) Switches Table

| Token | Meaning |
|---|---|
| `mv SRC DST` | Rename/move |
| `mv -v` | Verbose |
| `mv -i` | Interactive (prompt before overwrite) |
| `mv -n` | No-clobber |
| `mv -f` | Force (default for root with non-tty) |
| `mv -u` | Update only (move only if newer) |
| `$(date +%F)` | ISO date: 2026-05-27 |
| `$(date +%F_%T)` | ISO datetime: 2026-05-27_15:40:00 |
| `$(date +%s)` | Unix epoch seconds |
| `for f in ...; do ...; done` | Shell loop |
| `stat --format='%i'` | Inode number |

### j) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | `mv` same-FS | Atomic `rename(2)` — inode preserved |
|   | `mv` cross-FS | `cp -a + rm` — NOT atomic |
|   | Inode check | `stat --format='%i'` before and after |
|   | Date suffix pattern | `$(date +%F)` for log rotation |
|   | `for f in LIST; do ...; done` | Bulk operations |
|   | `mtime` unchanged | Rename does not bump mtime |
|   | `ctime` changes | The inode metadata DID change (name update) |
| 🪤 **Trap Risk (T34)** | `/etc/cron.d/` needs username (6 fields); user crontab is 5 | Not directly mv, but if you rename a personal `crontab.txt` and `cp` it into `/etc/cron.d/`, your old format is wrong. `/etc/cron.d/` lines need `MIN HOUR DOM MON DOW USER COMMAND` |

### k) 🧹 Cleanup

```bash
LAB=lab10
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
TOPIC:    mv same-FS atomic rename; inode preservation; date-stamp pattern
COMMANDS: mv, mv -v, stat --format='%i', $(date +%F), for loops
TRAPS:    T34 (cron.d 6-field vs user crontab 5-field)
MISSED:   —
NEXT:     task2 — mv across directories + -i/-n safety
EOF
echo "Journal written: $(ls -la $JDIR)"

cd /tmp/mv-lab
rm -f task01-warmup.log log1.log.* log2.log.* log3.log.*
echo "exit was: $?"
```

### l) Troubleshoot Table

| Symptom | Fix |
|---|---|
| `mv: cannot stat 'log1.log'` | File already renamed; check `ls` |
| Inode changed after rename | Source and dest were on different filesystems; check with `df source dest` |
| `mtime` advanced | You used `cp + rm`, not `mv` |
| Date suffix is empty | `$(date +%F)` returned empty — check `which date` and `$PATH` |

### m) STOP

> **STOP — paste output before Task 2.**

### n) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| Date-stamped files in sandbox | `ls /tmp/mv-lab/` | Sandbox state matches expectations |
| `/var/log` untouched | `ls -ld /var/log` | We did not write to /var |
| Journal task1 | `cat /root/rhcsa_journal/lab10/task1/done.txt` | Reboot-proof |

---

## Task 2 — Move Across Directories: `mv -i`, `mv -n`, `mv -u`

### a) Directory Context

**Practice directory this task:** `/var` (we will read `/var/log` and `/var/spool` paths as references) and `/tmp/mv-lab` (sandbox).
Moving between directories is one `mv` call; the safety flags (`-i`, `-n`, `-u`) control what happens on collision.

### b) 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/mv-lab
date -Is | tee task02-warmup.log
ls -ld /var/log /var/spool /var/lib 2>/dev/null | tee -a task02-warmup.log
df -h /var /tmp 2>/dev/null | tee -a task02-warmup.log
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Move files between directories, observe collision handling with `-i` / `-n` / `-u`, and see how `mv` behaves when source and destination might be on different filesystems.

### d) Main Command Block

```bash
cd /tmp/mv-lab

echo "=== Move log4 and log5 into archive/ ==="
mv -v log4.log log5.log archive/
ls -l archive/

echo ""
echo "=== Create a collision: archive/log4.log already exists ==="
echo "second copy of log4" > log4.log
ls -l log4.log archive/log4.log

echo ""
echo "=== mv -n (no-clobber): does NOT overwrite ==="
mv -nv log4.log archive/log4.log
ls -l log4.log archive/log4.log
echo "(Note: log4.log still exists locally — mv -n refused to overwrite)"

echo ""
echo "=== mv -i (interactive): asks; we feed 'no' ==="
echo "n" | mv -iv log4.log archive/log4.log
ls -l log4.log archive/log4.log

echo ""
echo "=== mv -u (update): move only if source is newer ==="
sleep 1
touch log4.log
echo "newer source content" > log4.log
mv -uv log4.log archive/log4.log
cat archive/log4.log

echo ""
echo "=== Cross-FS move detection ==="
df --output=source /tmp/mv-lab /var 2>/dev/null
echo ""
echo "Inode of staging/log5-stage.log before cross-FS test:"
echo "staged content" > staging/log5-stage.log
INODE_BEFORE=$(stat --format='%i' staging/log5-stage.log)
echo "Inode: $INODE_BEFORE"

# Try moving to /var/tmp (often a different FS in production)
mv -v staging/log5-stage.log /var/tmp/lab10-test.log 2>&1 || echo "Move failed — perms or FS issue"
ls -l /var/tmp/lab10-test.log 2>/dev/null
INODE_AFTER=$(stat --format='%i' /var/tmp/lab10-test.log 2>/dev/null)
echo "Inode after: ${INODE_AFTER:-N/A}"
if [ -n "$INODE_AFTER" ] && [ "$INODE_BEFORE" = "$INODE_AFTER" ]; then
  echo "✓ Same inode — same FS, atomic"
else
  echo "↪ Different inode (or different FS) — cp+rm under the hood"
fi
```

### e) Human-Readable Breakdown

- `mv log4.log log5.log archive/` — move multiple files into a directory in one command. Trailing `/` clarifies intent.
- `mv -n` — refuse to overwrite. The file stays in source if destination exists.
- `mv -i` — prompt before overwrite. `echo "n" | mv -i ...` simulates answering "no."
- `mv -u` — only move if source is newer than destination (uses mtime).
- `df --output=source PATH` — show which device backs a path. Comparing two paths reveals if they're on the same filesystem.
- Cross-FS test moves a sandbox file to `/var/tmp` which on RHEL is usually the same FS as `/tmp` (both root), but in production with `/var` on its own LV they would differ.

### f) Reading It Left to Right

`mv -v log4.log log5.log archive/`

1. `mv` — move.
2. `-v` — verbose; print each rename.
3. `log4.log log5.log` — two source files.
4. `archive/` — destination DIRECTORY (trailing `/` makes intent explicit).

When the last arg is a directory and there are multiple sources, `mv` moves each source INTO the directory. The trailing slash also catches the common mistake of moving INTO a file that doesn't exist as a directory — `mv x y z notadir/` fails clearly instead of overwriting `notadir` with `z`.

### g) The Story

The combination of `mv -i`, `-n`, and `-u` covers nearly every real-world "do not lose data" scenario:

- **`-i`** — for interactive shell work. Default for root in many distros via `alias mv='mv -i'`.
- **`-n`** — for scripts that must NEVER overwrite. (E.g. "deposit incoming file if not already there; otherwise leave it alone.")
- **`-u`** — for sync scripts where "newer wins" is the rule.

The cross-FS check teaches the most important real-world rule: **when staging configs, always write to a temp file in the SAME directory as the final location**. Don't write to `/tmp/foo.conf` and then `mv /tmp/foo.conf /etc/foo.conf` — that's cross-FS on most systems, NOT atomic, can be observed half-written. Instead: `vi /etc/foo.conf.new; mv /etc/foo.conf.new /etc/foo.conf`.

### h) Expected Output

```text
=== Move log4 and log5 into archive/ ===
renamed 'log4.log' -> 'archive/log4.log'
renamed 'log5.log' -> 'archive/log5.log'

=== Collision created ===
-rw-r--r--. ... log4.log
-rw-r--r--. ... archive/log4.log

=== mv -n: does NOT overwrite ===
mv: not replacing 'archive/log4.log'
-rw-r--r--. ... log4.log
-rw-r--r--. ... archive/log4.log
(Note: log4.log still exists locally — mv -n refused to overwrite)

=== mv -i: asks; we fed 'no' ===
mv: overwrite 'archive/log4.log'? mv: not overwriting 'archive/log4.log'
-rw-r--r--. ... log4.log
-rw-r--r--. ... archive/log4.log

=== mv -u: move only if source newer ===
renamed 'log4.log' -> 'archive/log4.log'
newer source content

=== Cross-FS move detection ===
Filesystem
/dev/mapper/rhel-root        (or similar)
/dev/mapper/rhel-root

Inode of staging/log5-stage.log before cross-FS test:
Inode: 87654321
renamed 'staging/log5-stage.log' -> '/var/tmp/lab10-test.log'
-rw-r--r--. ... /var/tmp/lab10-test.log
Inode after: 87654321
✓ Same inode — same FS, atomic
```

If `/var` is on a separate LV/partition (production setup), the second inode would differ, signaling that `mv` fell back to `cp -a + rm`.

### i) Switches Table

| Token | Meaning |
|---|---|
| `mv -v` | Verbose |
| `mv -i` | Interactive (prompt) |
| `mv -n` | No-clobber (skip if exists) |
| `mv -u` | Update only (newer wins) |
| `mv -t DIR FILES` | Move FILES into DIR (target-first) |
| `mv -T` | Treat dest as a non-dir (no "into dir" expansion) |
| `df --output=source PATH` | Print just the device column |
| `echo "n" \| mv -i` | Feed "no" to an interactive prompt |
| Trailing `/` on dir | Defensive habit — fails clearly if dest is wrong type |

### j) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | `mv -n` | Refuses to overwrite |
|   | `mv -i` | Prompts before overwrite |
|   | `mv -u` | "Newer wins" — uses mtime |
|   | `mv -t DIR FILES` | Target-first form (xargs-friendly) |
|   | Trailing `/` defense | Catches mistyped destinations |
|   | Same-FS = atomic | Inode preserved |
|   | Cross-FS = cp+rm | Not atomic |
|   | `df --output=source` | Compare devices for two paths |
| 🪤 **Trap Risk (T25)** | firewalld `--permanent` without `--reload` | If you `mv` a new firewalld zone file into `/etc/firewalld/zones/`, the rule is on disk but NOT active until `firewall-cmd --reload`. Always pair file changes with `--reload` |

### k) 🧹 Cleanup

```bash
LAB=lab10
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
TOPIC:    mv across dirs; -i/-n/-u safety; cross-FS detection
COMMANDS: mv -i, mv -n, mv -u, mv -t, df --output=source
TRAPS:    T25 (--reload after file-based firewalld changes)
MISSED:   —
NEXT:     task3 — atomic rename capstone (write .new + mv)
EOF
echo "Journal written: $(ls -la $JDIR)"

rm -f /var/tmp/lab10-test.log
cd /tmp/mv-lab
rm -f task02-warmup.log
rm -rf archive staging
echo "exit was: $?"
```

### l) Troubleshoot Table

| Symptom | Fix |
|---|---|
| `mv -n` overwrote anyway | You used `-f` after `-n`; later flags win |
| `mv` complains "destination not a directory" | Trailing `/` defense saved you; create the dir or pick a file name |
| `mv -u` did nothing | Source mtime is OLDER than dest; `touch SOURCE` to bump it |
| Inode changed but you expected atomic | `df --output=source SRC DST` to confirm same FS |

### m) STOP

> **STOP — paste output before Task 3.**

### n) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| `/var/tmp/lab10-test.log` removed | `test -e /var/tmp/lab10-test.log \|\| echo CLEAN` | No leftover under /var |
| Sandbox sub-dirs removed | `ls /tmp/mv-lab` | Sanity |
| Journal task2 | `cat /root/rhcsa_journal/lab10/task2/done.txt` | Reboot-proof |

---

## Task 3 — The Atomic Rename Capstone (Write `.new`, `mv` Into Place)

### a) Directory Context

**Practice directory this task:** `/var/spool/cron` (we will *carefully* simulate a cron-file swap, then revert) and `/tmp/mv-lab` (sandbox).
This is the canonical atomic-publish pattern used by `logrotate`, `nginx -s reload`, `dnf`, etcd, and almost every well-designed Linux tool.

### b) 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/mv-lab
date -Is | tee task03-warmup.log
ls -ld /var/spool/cron 2>&1 | tee -a task03-warmup.log
ls /etc/cron.d/ 2>&1 | head -n 5 | tee -a task03-warmup.log
ls /var/log/messages* 2>&1 | head -n 5 | tee -a task03-warmup.log
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Use the atomic rename pattern to swap a config file safely, deliberately introduce a `/etc/cron.d/` file (6-field T34 rehearsal), reload the affected service, and revert cleanly.

### d) Main Command Block

```bash
cd /tmp/mv-lab

echo "=== STEP 1 — Current app.conf ==="
cat app.conf

echo ""
echo "=== STEP 2 — Atomic rename pattern: write .new in SAME dir, then mv ==="
ls -li app.conf
INODE_BEFORE=$(stat --format='%i' app.conf)
cp -a app.conf.new app.conf.staged
mv -v app.conf.staged app.conf
ls -li app.conf
INODE_AFTER=$(stat --format='%i' app.conf)
echo "Inode before: $INODE_BEFORE / after: $INODE_AFTER (different — content actually swapped)"
cat app.conf

echo ""
echo "=== STEP 3 — T34 rehearsal: /etc/cron.d/ vs user crontab format ==="
echo ""
echo "❌ WRONG (5-field, user crontab format) for /etc/cron.d/:"
cat > /tmp/mv-lab/cron-wrong.txt <<'EOF'
*/5 * * * * /usr/local/bin/sync.sh
EOF
cat /tmp/mv-lab/cron-wrong.txt

echo ""
echo "✅ RIGHT (6-field with USER) for /etc/cron.d/:"
cat > /tmp/mv-lab/cron-right.txt <<'EOF'
*/5 * * * * root /usr/local/bin/sync.sh
EOF
cat /tmp/mv-lab/cron-right.txt

echo ""
echo "=== STEP 4 — Atomic-install the cron file (and revert) ==="
mv -v /tmp/mv-lab/cron-right.txt /etc/cron.d/lab10-test
ls -l /etc/cron.d/lab10-test
cat /etc/cron.d/lab10-test

echo ""
echo "Verify cron picked it up (cron re-reads /etc/cron.d/ on file mtime change):"
systemctl status crond --no-pager 2>&1 | head -n 5 || systemctl status cron --no-pager 2>&1 | head -n 5

echo ""
echo "=== STEP 5 — Revert: atomic rename to .bak, remove ==="
mv -v /etc/cron.d/lab10-test /etc/cron.d/lab10-test.bak
rm -f /etc/cron.d/lab10-test.bak
ls /etc/cron.d/ | grep lab10 || echo "Clean — no lab10 artifacts left"

echo ""
echo "=== STEP 6 — T25 rehearsal: --permanent + --reload paired pattern ==="
echo ""
echo "If we had added a firewall rule:"
echo "  firewall-cmd --permanent --add-port=8443/tcp   ← rule written to /etc/firewalld/zones/"
echo "  firewall-cmd --reload                           ← apply it (T25!)"
echo ""
echo "Demonstrate the read side (no modification):"
firewall-cmd --list-all 2>/dev/null | head -n 5 || echo "firewalld not running (fine for this demo)"

echo ""
echo "=== Final evidence ==="
{
  echo "LAB 10 TASK 3 EVIDENCE"
  echo "Atomic rename succeeded:"
  ls -l /tmp/mv-lab/app.conf
  cat /tmp/mv-lab/app.conf
  echo ""
  echo "/etc/cron.d/ cleaned: $(ls /etc/cron.d/ | grep -c lab10) lab10 files (expect 0)"
} > /root/lab10-evidence.txt
cat /root/lab10-evidence.txt
```

### e) Human-Readable Breakdown

- **STEP 1**: Show current contents of `app.conf`.
- **STEP 2 (atomic rename)**: `cp -a app.conf.new app.conf.staged` (stage on same FS, preserve metadata). Then `mv app.conf.staged app.conf` — atomic, no reader sees a half-written file. The inode changes because we're replacing one inode with another, but at no point is there a missing or partial file.
- **STEP 3 (T34)**: Show the difference between **user crontab format** (5 fields: min hour dom mon dow → command) and **/etc/cron.d/ format** (6 fields: min hour dom mon dow **USER** → command). Skipping the user field on `/etc/cron.d/` is the classic mistake.
- **STEP 4**: Install the 6-field cron file atomically. cron daemon notices the mtime change and re-reads.
- **STEP 5**: Revert by renaming to `.bak` first (so the live cron file is gone in one atomic step), then removing the backup.
- **STEP 6 (T25)**: Verbal/read-only demo of the firewalld pattern: changing files under `/etc/firewalld/` (or `--permanent` flag) needs a `--reload` to take effect. Same pattern, different daemon.

### f) Reading It Left to Right

`mv -v /tmp/mv-lab/cron-right.txt /etc/cron.d/lab10-test`

1. `mv` — move command.
2. `-v` — verbose.
3. `/tmp/mv-lab/cron-right.txt` — source (sandbox).
4. `/etc/cron.d/lab10-test` — destination.

Note: `/tmp` and `/etc` may be on the same filesystem (root) or different ones depending on the install. If same FS, this is an atomic rename. If different, it's `cp -a + rm`. **For production cron file installs, you would stage in `/etc/cron.d/.lab10-test.tmp` (same dir) and rename within `/etc/cron.d/`.** For this lab we use the simpler form because we control the test.

### g) The Story

Atomic rename is the single most important multi-process safety pattern in Unix. Without it:

- **logrotate** couldn't safely rotate a log while syslog is writing to it.
- **nginx reload** couldn't swap configs without dropping connections.
- **rpm/dnf** couldn't replace executables that are currently running.
- **kubectl apply ConfigMap** couldn't atomically swap a pod's config.
- **etcd** couldn't durably commit a transaction.

The pattern is always the same:

```
1. Write new content to a temp file IN THE SAME DIRECTORY as the final destination.
2. fsync(tmpfile) — make sure the bytes are on disk.
3. rename(tmpfile, finalfile) — atomic.
4. fsync(directory) — make sure the rename is on disk.
```

`mv` does step 3 for you. Steps 2 and 4 require `sync` or `fsync(1)` in shell scripts when durability matters (e.g., before reporting "success" to a user).

### h) Expected Output

```text
=== STEP 1 — Current app.conf ===
v1: original config

=== STEP 2 — Atomic rename pattern ===
12345678 -rw-r--r--. 1 root root 22 May 27 15:50 app.conf
renamed 'app.conf.staged' -> 'app.conf'
99887766 -rw-r--r--. 1 root root 22 May 27 15:50 app.conf
Inode before: 12345678 / after: 99887766 (different — content actually swapped)
v2: improved config

=== STEP 3 — T34 rehearsal ===
❌ WRONG (5-field, user crontab format) for /etc/cron.d/:
*/5 * * * * /usr/local/bin/sync.sh
✅ RIGHT (6-field with USER) for /etc/cron.d/:
*/5 * * * * root /usr/local/bin/sync.sh

=== STEP 4 — Atomic-install the cron file ===
renamed '/tmp/mv-lab/cron-right.txt' -> '/etc/cron.d/lab10-test'
-rw-r--r--. 1 root root ... /etc/cron.d/lab10-test
*/5 * * * * root /usr/local/bin/sync.sh

● crond.service - Command Scheduler
   Loaded: loaded (/usr/lib/systemd/system/crond.service; enabled; vendor preset: enabled)
   Active: active (running) since ...

=== STEP 5 — Revert ===
renamed '/etc/cron.d/lab10-test' -> '/etc/cron.d/lab10-test.bak'
Clean — no lab10 artifacts left

=== STEP 6 — T25 rehearsal ===
If we had added a firewall rule:
  firewall-cmd --permanent --add-port=8443/tcp
  firewall-cmd --reload
public (default, active)
  target: default
  icmp-block-inversion: no
  ...

=== Final evidence ===
LAB 10 TASK 3 EVIDENCE
Atomic rename succeeded:
-rw-r--r--. 1 root root 22 May 27 15:50 /tmp/mv-lab/app.conf
v2: improved config

/etc/cron.d/ cleaned: 0 lab10 files (expect 0)
```

### i) Switches Table

| Token | Meaning |
|---|---|
| `mv (atomic on same FS)` | `rename(2)` syscall |
| Atomic-publish pattern | write `.new` in same dir → `mv .new final` |
| `/etc/cron.d/` line | `MIN HOUR DOM MON DOW USER COMMAND` (6 fields) |
| User crontab line | `MIN HOUR DOM MON DOW COMMAND` (5 fields) |
| `firewall-cmd --permanent` | Writes to `/etc/firewalld/zones/*.xml` |
| `firewall-cmd --reload` | Re-reads on-disk state into runtime |
| `firewall-cmd --list-all` | Show current ACTIVE rules |
| `systemctl status SVC` | Show daemon state |

### j) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | Atomic rename pattern | Write `.new` in same dir → mv into place |
|   | Same-FS staging | Required for true atomicity |
|   | fsync / sync | Optional for durability beyond rename |
|   | `/etc/cron.d/` 6 fields | min hour dom mon dow USER command |
|   | User crontab 5 fields | min hour dom mon dow command |
|   | crond auto-reread | Notices mtime change in `/etc/cron.d/` |
|   | firewalld 2-step | `--permanent` writes file; `--reload` applies |
| 🪤 **Trap Risk (T34)** | `/etc/cron.d/` needs USER field | Forgetting the username field makes the cron line silently fail. Always verify with `tail -1 /var/log/cron` after install |
| 🪤 **Trap Risk (T25)** | firewalld `--permanent` without `--reload` | The rule is in `/etc/firewalld/zones/*.xml` but not active until reload. ALWAYS pair them: `firewall-cmd --permanent ...; firewall-cmd --reload` |

### k) 🧹 Cleanup

```bash
LAB=lab10
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
TOPIC:    Atomic rename capstone; /etc/cron.d/ format; firewalld 2-step
COMMANDS: mv (atomic), cp -a stage, cron.d 6-field, firewall-cmd --permanent + --reload
TRAPS:    T34 + T25 (both rehearsed)
MISSED:   —
NEXT:     Module 1 complete (labs 01-10) — review for RHCSA file-ops fluency
EOF
echo "Journal written: $(ls -la $JDIR)"

rm -f /etc/cron.d/lab10-test /etc/cron.d/lab10-test.bak
rm -f /root/lab10-evidence.txt
rm -rf /tmp/mv-lab
echo "exit was: $?"
```

### l) Troubleshoot Table

| Symptom | Fix |
|---|---|
| Reader sees half-written file | You staged on a different FS — restage in same dir |
| cron didn't pick up the file | Wait 1 min, then check `journalctl -u crond \| tail`; verify 6-field format |
| `firewall-cmd: command not found` | firewalld not installed — the demo is informational; skip the live command |
| `/etc/cron.d/lab10-test` already exists | Earlier run didn't clean; `rm -f /etc/cron.d/lab10-test*` and retry |

### m) STOP

> **STOP — paste output before declaring Lab 10 complete.**

### n) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| No leftover cron files | `ls /etc/cron.d/ \| grep lab10 \|\| echo CLEAN` | Confirms revert |
| No leftover evidence in /root | `test -e /root/lab10-evidence.txt \|\| echo CLEAN` | Confirms cleanup |
| Sandbox removed | `test -d /tmp/mv-lab \|\| echo CLEAN` | Confirms `rm -rf` |
| All 3 journal entries | `find /root/rhcsa_journal/lab10 -name done.txt \| wc -l` (expect 3) | Reboot-proof |
| All 6 lab journal trees | `ls /root/rhcsa_journal/ \| wc -l` (expect ≥6: lab05..lab10) | Full Module 1 record |

> **Reboot question:** "If we rebooted with `/etc/cron.d/lab10-test` still installed, would the cron job survive?" — Answer: yes. `/etc/cron.d/` is on the root partition; crond starts and reads it on every boot. **That is exactly why we always clean up after labs**: leftover cron files run forever until you notice.

---

## 🪤 Trap Registry Update — End of Lab 10

| Trap ID | Category | Rehearsed? | If hit, repeat in |
|---|---|---|---|
| T25 | firewalld | ✅ | — |
| T34 | Cron / Scheduling | ✅ | — |

3-lab trap window (08+09+10): **T32, T31, T17, T16, T25, T34** = **6 unique traps** ✓

**Module 1 trap totals (labs 05-10):**
T41, T43, T01, T02, T07, T32, T31, T17, T16, T25, T34 — **11 unique traps** rehearsed across 6 labs.

Categories covered: Meta×2, SELinux×2, fstab×1, Permissions×2, systemd×2, firewalld×1, cron×1 = 7 of 13 trap categories.
**Still missing in this Module:** LVM (T11–T14), Boot Recovery (T18–T20), Networking (T21–T24), autofs (T28–T30), Containers (T36–T38), Repos/DNF (T39–T40). Schedule these for Modules 5–7.

---

## 🎓 What You Now Own

1. `mv FROM TO` — rename in place (same dir).
2. `mv FILE DIR/` — move file into directory.
3. `mv -i` — interactive overwrite prompts.
4. `mv -n` — never overwrite.
5. `mv -u` — newer wins.
6. `mv -t DIR FILES` — target-first form for xargs.
7. The **atomic rename pattern**: write `.new` in same dir → `mv .new final`.
8. Same-FS = atomic; cross-FS = cp+rm (NOT atomic) — verify with `df --output=source`.
9. `/etc/cron.d/` 6-field format (T34) vs user crontab 5-field.
10. `firewall-cmd --permanent` + `--reload` paired pattern (T25).
11. Inode tracking with `stat --format='%i'` to prove what `mv` actually did.

---

## 🏁 Module 1 Complete (Labs 01–10)

You now have muscle memory for:

- stdout/stderr/pipes/tee (Labs 1–4)
- pwd/cd/ls navigation (Lab 5)
- ls -l, ls -Z, SELinux contexts, semanage+restorecon (Lab 6)
- touch, timestamps, stat, find -mtime (Lab 7)
- cp, cp -p, cp -a, --preserve=context (Lab 8)
- ln, ln -s, readlink, find -inum, systemctl mask (Lab 9)
- mv, atomic rename, /etc/cron.d/ format, firewalld 2-step (Lab 10)

Next: **Module 2 — Documentation & Networking** (Labs 11–27 in the global numbering; man/whatis/apropos, nmcli, hosts, DNS, SSH).
