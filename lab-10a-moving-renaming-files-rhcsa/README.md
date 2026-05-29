# Lab 10a: Moving & Renaming Files (RHCSA) — `mv`, atomic rename, cross-fs copy+remove

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `10a` (RHCSA) → `10b` (Ansible) → `10c` (Verify)
- **Career arcs covered:** RHCSA EX200 (`mv` for log rotation, config staging, package upgrades), RHCE EX294 (atomic config replace), SRE (incident rollback via backup file), DevOps (blue-green config swap)
- **Prerequisite:** Lab 09 (`ln`, `ln -s`, `readlink`)
- **Time Estimate:** 35–50 minutes
- **Tasks:** 2 (ADHD spec — Task 1 canonical mv, Task 2 cross-fs contrast)
- **Practice Directory (rotation #10):** `/var`
- **Sandbox:** `/tmp/mv-lab/` (plus a loop-mounted ext4 image at `/tmp/mv-lab/mnt2/`)
- **Traps rehearsed this lab:** **T10-A** (`mv -t TARGET SRC1 SRC2 ...` — `-t` flips arg order so target comes FIRST; easy to confuse with regular `mv SRC DST`) · **T10-B** (assuming `mv` always preserves inode — true only within same fs) · **T10-C** (`mv` over existing file silently overwrites unless `-i`/`-n` — destroys data)

> **This lab's practice directory is: `/var`** — real `mv` happens during log rotation, package upgrades, and config staging there. The sandbox is `/tmp/mv-lab/` where we actually move and rename without risk.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T10-A T10-B T10-C"
echo "📁  PRACTICE DIR: /var"
echo ""
echo "💡 Log rotation example (read-only — real mv happens here on real systems):"
ls -lt /var/log/messages* 2>/dev/null | head -3 || ls -lt /var/log/ 2>/dev/null | head -3
```

> **STOP — paste header output before running setup.**

---

## 🎯 Objective

Rename and move files **deliberately and safely**. By the end of this lab you can:

- Rename a file in place with `mv old new` and prove the inode did NOT change
- Move files between directories on the **same filesystem** (atomic — just a dirent rewrite)
- Move files **across filesystems** and prove the inode DID change (it's `cp -p` + `rm` under the hood)
- Use `-i` (interactive), `-n` (no-clobber), `-b` (backup), `-u` (update if newer), `-t` (target-first batch)
- Understand why hard links survive same-fs `mv` but break across filesystems

---

## 🧠 Concept: `mv` Is a `rename(2)` Syscall — Until It Has to Cross a Filesystem

`mv` calls the kernel's `rename(2)` system call. On a **single filesystem** this is just a directory-entry rewrite — the inode (and the data blocks it points at) does not move. The operation finishes in microseconds and is atomic: it either completes fully or not at all. mtime is preserved (no data was written); ctime is updated (the inode metadata changed because its parent-directory entry changed).

```
   ┌───────────────────────────────────────────────────────────────────┐
   │  Same-filesystem mv (atomic rename — the common case)             │
   ├───────────────────────────────────────────────────────────────────┤
   │  1. rename("/srv/old.txt", "/srv/new.txt")                        │
   │  2. Kernel rewrites the directory entry — same inode number       │
   │  3. mtime preserved, ctime bumped, data blocks untouched          │
   │  4. Hard links pointing at the inode STILL work                   │
   └───────────────────────────────────────────────────────────────────┘

   ┌───────────────────────────────────────────────────────────────────┐
   │  Cross-filesystem mv (NOT atomic — falls back to cp + rm)         │
   ├───────────────────────────────────────────────────────────────────┤
   │  1. rename() returns EXDEV (cross-device link not permitted)      │
   │  2. mv falls back to: cp -p SRC DST  (copy with metadata)         │
   │  3. ...then:           rm SRC                                     │
   │  4. NEW inode on destination filesystem                           │
   │  5. Hard links to SRC are now broken (different inode)            │
   │  6. Interrupt between steps 2 and 3 = both files exist briefly    │
   └───────────────────────────────────────────────────────────────────┘
```

That's the kernel-level reason same-fs `mv` is instant on a 50 GB file and cross-fs `mv` takes wall-clock minutes — the latter is literally copying every byte.

> **Three trap families to rehearse:** silent overwrite (T10-C — `mv` destroys the destination by default), inode misconception (T10-B — only same-fs preserves the inode), and `-t` arg order (T10-A — target comes FIRST after `-t`, easy to swap when scripting).

---

## 📚 `mv` Reference (everything you need for Tasks 1–2)

| Switch | Meaning | Why it matters |
|---|---|---|
| `mv SRC DST` | Move/rename — destructive by default | Base case |
| `-i` | Interactive — prompt before overwrite | T10-C antidote (ad-hoc) |
| `-n` | No-clobber — skip silently if DST exists | Idempotent without prompts |
| `-b` | Backup overwritten dst as `dst~` | Safety net for configs |
| `-u` | Update only — move if SRC newer than DST | rsync-like behavior |
| `-v` | Verbose — print each move | Script audit trail |
| `-t DIR SRC1 SRC2 ...` | Target-directory-first form | T10-A — target comes FIRST after `-t` |
| `-S SUFFIX` | Override backup suffix (default `~`) | Match company convention |
| `--no-target-directory` | Treat DST as a regular file, never a directory | Avoid `mv DIR/ DST/` ambiguity |
| `stat -c '%i' FILE` | Print inode number | Proves same-fs vs cross-fs |
| `df --output=source PATH` | Print the device holding PATH | Detect filesystem boundary |

> **Rule of `mv`:** Default `mv` is **destructive**. Always reach for `-i`, `-n`, or `-b` when the destination might already exist — and always check `df -T` before assuming a `mv` is going to be instant.

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i

# Sandbox on root filesystem (will be where same-fs renames happen)
mkdir -p /tmp/mv-lab/{src,archive}
mkdir -p /root/rhcsa_journal/lab-10a

# Fixture files
echo "config v1"  > /tmp/mv-lab/src/config.txt
echo "logfile A"  > /tmp/mv-lab/src/app.log
echo "logfile B"  > /tmp/mv-lab/src/access.log

# Build a loop-mounted ext4 image so we have a REAL second filesystem
# for the cross-fs demonstration in Task 2.
dd if=/dev/zero of=/tmp/mv-lab/img.ext4 bs=1M count=10 status=none
mkfs.ext4 -q /tmp/mv-lab/img.ext4
mkdir -p /tmp/mv-lab/mnt2
mount -o loop /tmp/mv-lab/img.ext4 /tmp/mv-lab/mnt2

# Confirm two filesystems are visible
df -hT /tmp/mv-lab /tmp/mv-lab/mnt2
ls -liR /tmp/mv-lab/
echo "exit was: $?"
```

> **STOP — confirm `df -hT` shows two DIFFERENT `Source` columns (one for `/` containing `/tmp/mv-lab`, one for `/dev/loopN` mounted at `/tmp/mv-lab/mnt2`) before Task 1. If both report the same source, the loop mount did not succeed.**

---

## Task 1 — Same-filesystem `mv`: rename in place, move into a directory, and the four guard switches

**Practice directory this task:** `/var` (read-only context for log rotation) · `/tmp/mv-lab/` (write). Every `mv` in this task stays on a single filesystem so we can prove the **inode does not change** — that's the atomic-rename contract.

### 🔁 Warm-Up — commands woven into Task 1

```bash
mkdir -p /tmp/mv-lab/task1
date -Is                                            2>&1 | tee /tmp/mv-lab/task1/warmup-pre.txt
ls -li /tmp/mv-lab/src/                             2>&1 | tee -a /tmp/mv-lab/task1/warmup-pre.txt
stat -c '%n inode=%i' /tmp/mv-lab/src/config.txt
test -d /tmp/mv-lab/src && echo "sandbox OK"
ls -lt /var/log/ 2>/dev/null | head -3
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 09: hard links survive same-fs operations — we will exercise that again at the end of this task by `ln`ing the file, then `mv`ing it, then checking that the link still resolves.

### Purpose

Rename `config.txt` to `config.txt.old`, move `app.log` into `/tmp/mv-lab/archive/`, and demonstrate the four guard switches (`-i`, `-n`, `-b`, `-u`) on overwrite collisions. Then prove with `stat -c '%i'` that **none of these operations changed the inode** — they were directory-entry rewrites only.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `ls -li /tmp/mv-lab/src/` | Snapshot **before** the moves so we have a baseline of inode numbers |
| `stat -c '%n inode=%i'` | Captured for each file before move; compared after to prove inode preservation |
| `test -d /tmp/mv-lab/src` | Guards each `mv` — we only fire if the sandbox source dir really exists |
| `2>&1 \| tee` | Captures the entire transcript into `task1/op.txt` for journal evidence |
| `set -o pipefail` | Catches a silent failure in any `mv ... | tee` chain |
| `$(date -Is)` | Stamps the journal `notes.txt` and the warmup pre-snapshot |

### Main command block

```bash
cd /tmp/mv-lab
mkdir -p /tmp/mv-lab/task1

# ── Part A: rename in place — same fs → inode unchanged ─────────────
ls -li /tmp/mv-lab/src/                             2>&1 | tee /tmp/mv-lab/task1/op.txt
inode_before=$(stat -c '%i' /tmp/mv-lab/src/config.txt)

mv -v /tmp/mv-lab/src/config.txt /tmp/mv-lab/src/config.txt.old \
                                                    2>&1 | tee -a /tmp/mv-lab/task1/op.txt
ls -li /tmp/mv-lab/src/                             2>&1 | tee -a /tmp/mv-lab/task1/op.txt

inode_after=$(stat -c '%i' /tmp/mv-lab/src/config.txt.old)
echo "before=$inode_before  after=$inode_after"     2>&1 | tee -a /tmp/mv-lab/task1/op.txt
[ "$inode_before" = "$inode_after" ] && \
  echo "INODE_PRESERVED — same-fs mv is just a dirent rewrite" \
                                                    2>&1 | tee -a /tmp/mv-lab/task1/op.txt

# ── Part B: move into another directory + move+rename in one go ─────
mv -v /tmp/mv-lab/src/app.log /tmp/mv-lab/archive/  2>&1 | tee -a /tmp/mv-lab/task1/op.txt
mv -v /tmp/mv-lab/src/access.log /tmp/mv-lab/archive/access-$(date +%Y%m%d).log \
                                                    2>&1 | tee -a /tmp/mv-lab/task1/op.txt
ls -liR /tmp/mv-lab/src /tmp/mv-lab/archive         2>&1 | tee -a /tmp/mv-lab/task1/op.txt

# ── Part C: the four guard switches on a fresh overwrite collision ──
echo "VERSION 1"        > /tmp/mv-lab/src/v1.txt
echo "VERSION 2"        > /tmp/mv-lab/src/v2.txt
echo "VERSION 3"        > /tmp/mv-lab/src/v3.txt
echo "EXISTING TARGET"  > /tmp/mv-lab/archive/target.txt

# (default) silent overwrite — T10-C in action
mv -v /tmp/mv-lab/src/v1.txt /tmp/mv-lab/archive/target.txt \
                                                    2>&1 | tee -a /tmp/mv-lab/task1/op.txt
cat /tmp/mv-lab/archive/target.txt                  2>&1 | tee -a /tmp/mv-lab/task1/op.txt

# Restore target and try -n (no-clobber)
echo "EXISTING TARGET" > /tmp/mv-lab/archive/target.txt
mv -nv /tmp/mv-lab/src/v2.txt /tmp/mv-lab/archive/target.txt \
                                                    2>&1 | tee -a /tmp/mv-lab/task1/op.txt
cat /tmp/mv-lab/archive/target.txt                  2>&1 | tee -a /tmp/mv-lab/task1/op.txt
ls /tmp/mv-lab/src/v2.txt                           2>&1 | tee -a /tmp/mv-lab/task1/op.txt

# Restore target and try -b (backup overwritten dst as target.txt~)
echo "EXISTING TARGET" > /tmp/mv-lab/archive/target.txt
mv -bv /tmp/mv-lab/src/v2.txt /tmp/mv-lab/archive/target.txt \
                                                    2>&1 | tee -a /tmp/mv-lab/task1/op.txt
ls /tmp/mv-lab/archive/                             2>&1 | tee -a /tmp/mv-lab/task1/op.txt
cat /tmp/mv-lab/archive/target.txt                  2>&1 | tee -a /tmp/mv-lab/task1/op.txt
cat /tmp/mv-lab/archive/target.txt~                 2>&1 | tee -a /tmp/mv-lab/task1/op.txt

# Restore target and try -i (interactive; answer "n" so the move is refused)
echo "EXISTING TARGET" > /tmp/mv-lab/archive/target.txt
echo n | mv -iv /tmp/mv-lab/src/v3.txt /tmp/mv-lab/archive/target.txt \
                                                    2>&1 | tee -a /tmp/mv-lab/task1/op.txt
cat /tmp/mv-lab/archive/target.txt                  2>&1 | tee -a /tmp/mv-lab/task1/op.txt

# ── Part D: -u (update if newer) and -t (target-first batch — T10-A) ─
echo "OLD" > /tmp/mv-lab/src/staged.txt
echo "EVEN OLDER" > /tmp/mv-lab/archive/staged.txt
touch -d '1 hour ago' /tmp/mv-lab/archive/staged.txt
mv -uv /tmp/mv-lab/src/staged.txt /tmp/mv-lab/archive/staged.txt \
                                                    2>&1 | tee -a /tmp/mv-lab/task1/op.txt

# -t batch form: target comes FIRST after -t (T10-A rehearsal)
touch /tmp/mv-lab/src/{batch1.txt,batch2.txt,batch3.txt}
mv -vt /tmp/mv-lab/archive/ \
       /tmp/mv-lab/src/batch1.txt \
       /tmp/mv-lab/src/batch2.txt \
       /tmp/mv-lab/src/batch3.txt                   2>&1 | tee -a /tmp/mv-lab/task1/op.txt
ls /tmp/mv-lab/archive/                             2>&1 | tee -a /tmp/mv-lab/task1/op.txt

# ── Part E: hard-link survival across same-fs mv ────────────────────
echo "linkable" > /tmp/mv-lab/src/link-src.txt
ln /tmp/mv-lab/src/link-src.txt /tmp/mv-lab/src/link-hard.txt
ls -li /tmp/mv-lab/src/link-src.txt /tmp/mv-lab/src/link-hard.txt \
                                                    2>&1 | tee -a /tmp/mv-lab/task1/op.txt
mv -v /tmp/mv-lab/src/link-src.txt /tmp/mv-lab/archive/link-src-moved.txt \
                                                    2>&1 | tee -a /tmp/mv-lab/task1/op.txt
# Hard link should STILL share the same inode after same-fs mv
ls -li /tmp/mv-lab/archive/link-src-moved.txt /tmp/mv-lab/src/link-hard.txt \
                                                    2>&1 | tee -a /tmp/mv-lab/task1/op.txt

echo "exit was: $?"
```

### Human-readable breakdown

1. **Part A** captures the inode of `config.txt`, renames it in place to `config.txt.old`, then proves with `stat -c '%i'` that the inode is unchanged. That's the atomic-rename contract.
2. **Part B** exercises the "move into a directory" form (`mv FILE DIR/`) and the "move + rename in one operation" form (`mv FILE DIR/new-name`). Both are same-fs operations so both preserve their inodes.
3. **Part C** rehearses all four guard switches against the same `target.txt` collision — default (destroys data, T10-C), `-n` (silent skip), `-b` (backup as `target.txt~`), `-i` (prompt; we answer `n`). Reading the captured `op.txt` is the audit trail of which switch did what.
4. **Part D** demonstrates `-u` (move only if source is newer than destination — we force the destination to be older with `touch -d`) and the `-t` target-first batch form. The `-t` form is the **specific rehearsal for T10-A**: when you write `mv -t DIR SRC1 SRC2 SRC3`, the DIR comes FIRST, which feels backwards compared to regular `mv SRC DST`. Burning this into muscle memory now prevents the script-driven version from going sideways.
5. **Part E** proves the hard-link survival property: create a hard link, move the original, and verify both names still point at the same inode. This works **because** same-fs `mv` does not change the inode — it's just a directory-entry rewrite. We rebuild this contrast in Task 2 where cross-fs `mv` breaks the link.

### Reading it left to right

- `inode_before=$(stat -c '%i' FILE)` — command substitution captures the inode number into a shell variable.
- `mv -v SRC DST` — `-v` prints `renamed 'SRC' -> 'DST'` to stdout so the transcript has audit lines.
- `[ "$inode_before" = "$inode_after" ] && echo ...` — string equality test in a short-circuit; only prints if the inode survived.
- `mv -nv SRC DST` — `-n` is no-clobber + `-v` is verbose. The two switches combine; the order doesn't matter.
- `mv -bv SRC DST` — `-b` backs up DST as `DST~` before overwriting. The backup suffix is `~` unless overridden with `-S`.
- `echo n | mv -iv SRC DST` — pipes `n` into mv's prompt; the move is refused. Useful for testing what `-i` does in a script.
- `touch -d '1 hour ago' FILE` — sets the mtime to one hour in the past so `mv -u SRC FILE` will trigger (SRC is newer).
- `mv -vt DIR SRC1 SRC2 ...` — `-t` flips the order: target FIRST, then any number of sources. This is the **T10-A rehearsal**.
- `ln SRC DST` — hard link (no `-s` = not symbolic). DST and SRC share the same inode.

### The story

A grader: "rotate `/var/log/myapp.log` to `/var/log/myapp.log.1` and start a fresh log file, preserving the old log's mtime." The hand-typed answer is `mv /var/log/myapp.log /var/log/myapp.log.1 && touch /var/log/myapp.log`. The `mv` is instant because `/var/log/` is a single directory on the root filesystem — no bytes were copied, just a directory-entry rewrite. The mtime of the rotated log is exactly what it was a millisecond before the `mv`. That's RHCSA log-rotation 101, and it works the way it works because of `rename(2)`.

The four guard switches are the **why** of "never trust default `mv` against an existing destination." On a clean system, none of `-i`, `-n`, `-b`, or `-u` are necessary — the destination is empty. But the grader's exam scenario always has *something* already at the destination, and the default `mv` will overwrite it silently. The `-b` switch is the senior-engineer answer for production configs because it leaves a `target.txt~` you can restore from. The `-i` switch is for interactive use. The `-n` switch is for idempotent scripts. The `-u` switch is for sync-like workflows. Each has a place.

### Expected output

```text
total 12
12340 -rw-r--r--. 1 root root 11 May 28 ... access.log
12341 -rw-r--r--. 1 root root 11 May 28 ... app.log
12342 -rw-r--r--. 1 root root 11 May 28 ... config.txt
renamed '/tmp/mv-lab/src/config.txt' -> '/tmp/mv-lab/src/config.txt.old'
12340 -rw-r--r--. 1 root root 11 May 28 ... access.log
12341 -rw-r--r--. 1 root root 11 May 28 ... app.log
12342 -rw-r--r--. 1 root root 11 May 28 ... config.txt.old
before=12342  after=12342
INODE_PRESERVED — same-fs mv is just a dirent rewrite

renamed '/tmp/mv-lab/src/app.log' -> '/tmp/mv-lab/archive/app.log'
renamed '/tmp/mv-lab/src/access.log' -> '/tmp/mv-lab/archive/access-20260528.log'

# Default mv: data destroyed (T10-C)
renamed '/tmp/mv-lab/src/v1.txt' -> '/tmp/mv-lab/archive/target.txt'
VERSION 1                                        ← "EXISTING TARGET" gone forever

# mv -n: silent skip, SRC stays in place
EXISTING TARGET                                  ← untouched
/tmp/mv-lab/src/v2.txt                            ← still there

# mv -b: backup left as target.txt~
target.txt  target.txt~  access-20260528.log  app.log
VERSION 2                                        ← new content
EXISTING TARGET                                  ← old content in target.txt~

# mv -i answered "n": destination preserved
EXISTING TARGET

# -u: SRC was newer than DST, move proceeded
renamed '/tmp/mv-lab/src/staged.txt' -> '/tmp/mv-lab/archive/staged.txt'

# -t: target first, three sources after (T10-A rehearsal)
renamed '/tmp/mv-lab/src/batch1.txt' -> '/tmp/mv-lab/archive/batch1.txt'
renamed '/tmp/mv-lab/src/batch2.txt' -> '/tmp/mv-lab/archive/batch2.txt'
renamed '/tmp/mv-lab/src/batch3.txt' -> '/tmp/mv-lab/archive/batch3.txt'

# Hard link survives same-fs mv (both names share inode after move)
98765 -rw-r--r--. 2 root root  9 May 28 ... /tmp/mv-lab/archive/link-src-moved.txt
98765 -rw-r--r--. 2 root root  9 May 28 ... /tmp/mv-lab/src/link-hard.txt
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| `mv SRC DST` | Move/rename — silent overwrite by default (T10-C) |
| `mv -v` | Verbose — prints `renamed 'SRC' -> 'DST'` |
| `mv -i` | Prompt before overwrite — answer y/n on stdin |
| `mv -n` | No-clobber — silently skip if DST exists |
| `mv -b` | Backup overwritten DST as `DST~` |
| `mv -u` | Update — only move if SRC mtime > DST mtime |
| `mv -t DIR SRC1 SRC2 ...` | Target-first batch — DIR comes FIRST (T10-A) |
| `mv --no-target-directory` | Force DST to be treated as a file, not a directory |
| `stat -c '%i' FILE` | Print only the inode number |
| `touch -d 'TIME' FILE` | Override mtime — useful for `-u` testing |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | `rename(2)` syscall | Same-fs `mv` is one syscall — atomic, instant, inode preserved |
|   | mtime preservation | Same-fs `mv` does not touch data — mtime survives |
|   | ctime update | Same-fs `mv` updates ctime because the parent-directory field of the inode changed |
|   | `dst` is a directory | `mv` moves SRC INTO it as `dst/$(basename SRC)` |
|   | `dst` is a file | `mv` OVERWRITES it (default), unless `-i`/`-n`/`-b` |
|   | `mv -i` vs `-n` | Mutually exclusive — last one on the command line wins |
|   | Hard links same-fs | Survive `mv` — both names still point at the same inode |
| 🪤 | **Trap Risk T10-A** | `mv -t DIR SRC1 SRC2 ...` — target FIRST after `-t`; opposite of `mv SRC DST` |
| 🪤 | **Trap Risk T10-C** | Default `mv` silently overwrites an existing dst — gone is gone |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Rename inode preserved | `stat -c '%i' /tmp/mv-lab/src/config.txt.old` (compare to `$inode_before`) | Proves same-fs mv was a dirent rewrite, not a copy |
| Backup file present | `ls /tmp/mv-lab/archive/target.txt~` | Proves `-b` actually created the safety net |
| Hard link survived | `stat -c '%i' /tmp/mv-lab/archive/link-src-moved.txt /tmp/mv-lab/src/link-hard.txt` | Both inodes must match — same-fs mv kept the link alive |
| Transcript captured | `wc -l /tmp/mv-lab/task1/op.txt` | The audit evidence (must be > 0) |

> **Reboot reasoning:** `/tmp/mv-lab/` is on `/` (the root filesystem) — survives reboot in most layouts unless `tmp.mount` is enabled. The **journal** under `/root/rhcsa_journal/` always survives. We copy `op.txt` into the journal in the next step so the evidence is safe regardless of `/tmp/` lifetime.

### Journal write — BEFORE cleanup

```bash
LAB=lab-10a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/mv-lab/task1/op.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Same-fs mv — atomic rename, four guard switches, -t batch, hard-link survival
COMMANDS: mv, mv -v/-i/-n/-b/-u/-t, stat -c '%i', ln, touch -d
TRAPS:    T10-A (rehearsed -t target-first), T10-C (rehearsed default-overwrite + -b safety net)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — cross-fs mv (inode CHANGES; hard links BREAK)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -rf /tmp/mv-lab/task1
ls /tmp/mv-lab/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Inode changed after a "rename" | You crossed a filesystem boundary — likely a bind mount or a tmpfs subdirectory. Check `df -T SRC DST`. |
| `mv -i` did not prompt | Either no overwrite happened (DST was missing), or distro alias `mv='mv -i'` interaction with piped input. Use `/usr/bin/mv -i`. |
| `mv -b` left no backup | DST did not exist before — `-b` only acts on overwrite. |
| `mv -u` overwrote anyway | DST mtime was older than SRC mtime — that is the intended behavior. Inspect with `stat -c '%y' SRC DST`. |
| Hard link inodes differ | You either crossed filesystems or used `ln -s` (symbolic, not hard). Re-check with `ls -li`. |

> **STOP — paste the `INODE_PRESERVED` line and the `cat $JDIR/done.txt` output before Task 2.**

---

## Task 2 — Cross-filesystem `mv`: inode CHANGES, hard links BREAK, the operation is NOT atomic

**Practice directory this task:** `/tmp/mv-lab/` (source — root filesystem) → `/tmp/mv-lab/mnt2/` (destination — loop-mounted ext4 filesystem). The loop mount is a **real** second filesystem with its own inode table, so cross-fs `mv` behavior manifests cleanly.

### 🔁 Warm-Up — commands woven into Task 2

```bash
mkdir -p /tmp/mv-lab/task2
pwd
df -hT /tmp/mv-lab /tmp/mv-lab/mnt2                 2>&1 | tee /tmp/mv-lab/task2/warmup-pre.txt
mount | grep mnt2                                   2>&1 | tee -a /tmp/mv-lab/task2/warmup-pre.txt
test -d /tmp/mv-lab/mnt2 && echo "mnt2 OK"
ls -la /tmp/mv-lab/                                 2>&1 | tee -a /tmp/mv-lab/task2/warmup-pre.txt
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: `stat -c '%i'` was our atomic-rename proof. Same command now — but the inode WILL change, which is the kernel's way of telling us the operation was `cp -p` + `rm` under the hood, not `rename(2)`.

### Purpose

Move a file from `/tmp/mv-lab/` (root filesystem) into `/tmp/mv-lab/mnt2/` (loop-mounted ext4). Observe with `stat -c '%i'` that the inode CHANGED. Then move a hard-linked file across the filesystem boundary and demonstrate that the hard-link relationship is **broken** — because the destination is a brand-new inode on a different filesystem, the original link no longer reaches it.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `df -hT /tmp/mv-lab /tmp/mv-lab/mnt2` | Confirms TWO filesystems (different `Source` columns) so the cross-fs demo is honest |
| `mount \| grep mnt2` | Verifies the loop mount is active before we try to move into it |
| `test -d /tmp/mv-lab/mnt2` | Guards each cross-fs `mv` — refuses to run if the mount went away |
| `ls -la /tmp/mv-lab/` | Pre-snapshot for the journal evidence |
| `pwd` | Tracks current working dir — defensive habit before any `mv` |
| `2>&1 \| tee` | Captures the full cross-fs transcript into `task2/op.txt` |

### Main command block

```bash
cd /tmp/mv-lab
mkdir -p /tmp/mv-lab/task2

# ── Part A: prove the two filesystems are distinct ─────────────────
df --output=source,fstype,target /tmp/mv-lab /tmp/mv-lab/mnt2 \
                                                    2>&1 | tee /tmp/mv-lab/task2/op.txt

# Build source file on the root filesystem
echo "cross-fs payload" > /tmp/mv-lab/src/crossfs.txt
inode_src=$(stat -c '%i' /tmp/mv-lab/src/crossfs.txt)
fs_src=$(df --output=source /tmp/mv-lab/src/crossfs.txt | tail -1)
echo "SRC:  fs=$fs_src  inode=$inode_src"           2>&1 | tee -a /tmp/mv-lab/task2/op.txt

# ── Part B: mv across the boundary ─────────────────────────────────
mv -v /tmp/mv-lab/src/crossfs.txt /tmp/mv-lab/mnt2/crossfs.txt \
                                                    2>&1 | tee -a /tmp/mv-lab/task2/op.txt
inode_dst=$(stat -c '%i' /tmp/mv-lab/mnt2/crossfs.txt)
fs_dst=$(df --output=source /tmp/mv-lab/mnt2/crossfs.txt | tail -1)
echo "DST:  fs=$fs_dst  inode=$inode_dst"           2>&1 | tee -a /tmp/mv-lab/task2/op.txt

if [ "$fs_src" != "$fs_dst" ]; then
  echo "ACROSS_FILESYSTEMS"                         2>&1 | tee -a /tmp/mv-lab/task2/op.txt
  [ "$inode_src" != "$inode_dst" ] && \
    echo "INODE_CHANGED — cross-fs mv was cp -p + rm" \
                                                    2>&1 | tee -a /tmp/mv-lab/task2/op.txt
else
  echo "Same fs — mount didn't take; troubleshoot first" \
                                                    2>&1 | tee -a /tmp/mv-lab/task2/op.txt
fi

# mtime preserved (mv calls cp -p internally for cross-fs)
stat -c 'mtime=%y' /tmp/mv-lab/mnt2/crossfs.txt     2>&1 | tee -a /tmp/mv-lab/task2/op.txt

# ── Part C: cross-fs mv is NOT atomic — time a larger file ─────────
dd if=/dev/zero of=/tmp/mv-lab/src/big.bin bs=1M count=5 status=none
ls -lh /tmp/mv-lab/src/big.bin                      2>&1 | tee -a /tmp/mv-lab/task2/op.txt

# A same-fs mv finishes instantly; a cross-fs mv has to copy bytes.
{ time mv -v /tmp/mv-lab/src/big.bin /tmp/mv-lab/mnt2/big.bin ; } \
                                                    2>&1 | tee -a /tmp/mv-lab/task2/op.txt
ls -lh /tmp/mv-lab/mnt2/big.bin                     2>&1 | tee -a /tmp/mv-lab/task2/op.txt

# ── Part D: hard-link relationship BREAKS across filesystems ───────
echo "linked payload" > /tmp/mv-lab/src/hl-src.txt
ln /tmp/mv-lab/src/hl-src.txt /tmp/mv-lab/src/hl-twin.txt
echo "BEFORE cross-fs mv — both names share inode:" 2>&1 | tee -a /tmp/mv-lab/task2/op.txt
ls -li /tmp/mv-lab/src/hl-src.txt /tmp/mv-lab/src/hl-twin.txt \
                                                    2>&1 | tee -a /tmp/mv-lab/task2/op.txt
# Link count column (the "2") confirms the inode has two names

mv -v /tmp/mv-lab/src/hl-src.txt /tmp/mv-lab/mnt2/hl-src.txt \
                                                    2>&1 | tee -a /tmp/mv-lab/task2/op.txt

echo "AFTER cross-fs mv — link is broken (different inodes, different fs):" \
                                                    2>&1 | tee -a /tmp/mv-lab/task2/op.txt
ls -li /tmp/mv-lab/mnt2/hl-src.txt /tmp/mv-lab/src/hl-twin.txt \
                                                    2>&1 | tee -a /tmp/mv-lab/task2/op.txt
# Link count drops back to 1 on hl-twin.txt; the moved file is a brand-new inode

twin_inode=$(stat -c '%i' /tmp/mv-lab/src/hl-twin.txt)
moved_inode=$(stat -c '%i' /tmp/mv-lab/mnt2/hl-src.txt)
[ "$twin_inode" != "$moved_inode" ] && \
  echo "HARD_LINK_BROKEN — cross-fs mv minted a new inode" \
                                                    2>&1 | tee -a /tmp/mv-lab/task2/op.txt

echo "exit was: $?"
```

### Human-readable breakdown

1. **Part A** uses `df --output=source,fstype,target` to prove `/tmp/mv-lab` and `/tmp/mv-lab/mnt2` are on different filesystems (different `Source` columns — one is the root device, one is `/dev/loopN`). Then we capture the source file's inode and filesystem identity for later comparison.
2. **Part B** runs the cross-fs `mv` and proves with `stat -c '%i'` that the destination inode is **different** from the source inode. That's how you read the kernel: same number = `rename(2)` succeeded; different number = `rename()` returned EXDEV and `mv` fell back to `cp -p` + `rm`.
3. **Part C** times a 5 MB cross-fs `mv` with `time` to make the **wall-clock cost** of the copy visible. On a same-fs rename, this would finish in microseconds. On the loop mount, you'll see real seconds of wall time even for a small file — because `mv` is literally copying the bytes through the kernel.
4. **Part D** is the hard-link contrast. Create a hard link with `ln` (no `-s`). Both names show the same inode and a link count of 2. After cross-fs `mv`, the moved name is a **brand new inode** on the destination filesystem, and the original twin file's link count drops back to 1. The hard-link relationship is gone — even though both files have the same content, they are independent inodes from this point on.

### Reading it left to right

- `df --output=source,fstype,target PATH` — only the columns we care about; `source` shows the device backing PATH.
- `inode_src=$(stat -c '%i' FILE)` — capture the inode number for later comparison.
- `mv -v SRC DST` — same `mv -v` as Task 1; the kernel does completely different work but the user-facing syntax is unchanged.
- `[ "$inode_src" != "$inode_dst" ]` — string inequality; true means the inode changed, which is the cross-fs signature.
- `{ time mv ... ; }` — the braces group `mv` so `time` can wrap it and `tee` can capture the timing output.
- `ln SRC DST` — hard link (NOT `-s`). Both names share the same inode; link count goes from 1 to 2.
- `ls -li FILE` — shows the inode number in column 1 and the link count in column 3 (after permissions). Watch both before and after to see the link break.

### The story

Two interview questions everyone gets eventually:

1. *"Why is `mv` slow on this 80 GB file but instant on this 80 KB file?"* — Wrong question. The size doesn't matter. What matters is whether the source and destination are on the same filesystem. Same-fs `mv` is `rename(2)` — instant for any size. Cross-fs `mv` is `cp -p` + `rm` — wall-clock time proportional to size.
2. *"We have a backup script that hard-links to save space, and after one `mv` the duplicates ballooned. Why?"* — Because someone moved a file to a different filesystem. Hard links can't span filesystems (the kernel won't let you `ln SRC DST` if they're on different mount points, and `mv` across filesystems creates a NEW inode that the old hard link can't reach). The fix is `cp --reflink=auto` on a CoW filesystem, or `rsync --link-dest` if you're rebuilding the backup tree.

The lesson: `mv` looks like one command in the shell, but it's two completely different operations under the hood. The kernel's `EXDEV` errno is the signal — when `rename(2)` returns it, `mv` quietly falls back to copy + delete, and several invariants you rely on (atomicity, inode preservation, hard-link survival) silently break. The cure is `df -T` before any `mv` you care about — and `cp --reflink` or `rsync` for the cases where you needed inode preservation.

### Expected output

```text
Filesystem     Type Mounted on
/dev/sda3      xfs  /
/dev/loop0     ext4 /tmp/mv-lab/mnt2
SRC:  fs=/dev/sda3  inode=12345
renamed '/tmp/mv-lab/src/crossfs.txt' -> '/tmp/mv-lab/mnt2/crossfs.txt'
DST:  fs=/dev/loop0  inode=12
ACROSS_FILESYSTEMS
INODE_CHANGED — cross-fs mv was cp -p + rm
mtime=2026-05-28 20:01:12.345678901 -0400
-rw-r--r--. 1 root root 5.0M May 28 ... big.bin
renamed '/tmp/mv-lab/src/big.bin' -> '/tmp/mv-lab/mnt2/big.bin'

real    0m0.124s
user    0m0.001s
sys     0m0.062s

BEFORE cross-fs mv — both names share inode:
98765 -rw-r--r--. 2 root root 15 May 28 ... hl-src.txt
98765 -rw-r--r--. 2 root root 15 May 28 ... hl-twin.txt
renamed '/tmp/mv-lab/src/hl-src.txt' -> '/tmp/mv-lab/mnt2/hl-src.txt'
AFTER cross-fs mv — link is broken (different inodes, different fs):
   13 -rw-r--r--. 1 root root 15 May 28 ... /tmp/mv-lab/mnt2/hl-src.txt
98765 -rw-r--r--. 1 root root 15 May 28 ... /tmp/mv-lab/src/hl-twin.txt
HARD_LINK_BROKEN — cross-fs mv minted a new inode
exit was: 0
```

> Note: the `time` output for cross-fs mv of 5 MB shows ~100 ms of wall time on a loop-mounted ext4. The exact number varies, but it is **always non-trivial** — and on a same-fs rename it would be tens of microseconds.

### Switches

| Token | Meaning |
|---|---|
| `df --output=source,fstype,target` | Show only device, filesystem type, and mount point |
| `mkfs.ext4 IMG.ext4` | Format a regular file as ext4 — usable via loop mount |
| `mount -o loop IMG MNT` | Mount a file as a block device; kernel binds a loop device automatically |
| `time CMD` | Wrap CMD and print real/user/sys wall-clock breakdown |
| `dd if=/dev/zero of=FILE bs=1M count=N` | Generate an N-MB file of zeros |
| `ln SRC DST` | Hard link — same inode, two names, link count +1 |
| `ls -li FILE` | Long listing with inode in column 1 |
| `stat -c '%y' FILE` | Print mtime |
| `umount MNT` | Detach a loop mount before cleanup |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | `rename(2)` EXDEV | The errno for "cross-device link" — triggers `mv`'s cp+rm fallback |
|   | Cross-fs `mv` is `cp -p` + `rm` | NOT atomic; wall-clock cost proportional to file size |
|   | Inode tables are per-filesystem | Same number on different filesystems means nothing; never compare across fs |
|   | mtime preserved across fs | `cp -p` keeps mtime; that's why post-mv stat still shows the original |
|   | ctime always bumps | Every inode change updates ctime — even same-fs mv |
|   | Hard links don't cross | Within a fs they survive `mv`; across a fs they break (different inode) |
| 🪤 | **Trap Risk T10-B** | Assuming `mv` always preserves the inode. Only true within a single filesystem. |
| 🪤 | **Trap Risk T10-A** | `mv -t DIR SRC1 SRC2 ...` — target FIRST after `-t`. Easy to mis-script. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Cross-fs move happened | `test -f /tmp/mv-lab/mnt2/crossfs.txt && test ! -f /tmp/mv-lab/src/crossfs.txt` | Both conditions must be true — SRC gone, DST present |
| Inode actually changed | `stat -c '%i' /tmp/mv-lab/mnt2/crossfs.txt` (must differ from `$inode_src`) | The kernel's proof that this was cp+rm, not rename |
| Hard link broken | `ls -li /tmp/mv-lab/src/hl-twin.txt /tmp/mv-lab/mnt2/hl-src.txt` | Different inodes, different filesystems |
| Transcript captured | `wc -l /root/rhcsa_journal/lab-10a/task2/evidence.txt` | The audit trail (must be > 0) |

> **Reboot reasoning:** The loop mount itself does NOT survive a reboot unless persisted in `/etc/fstab` — and that is a deliberate choice for this lab. The data we moved is intact inside `/tmp/mv-lab/img.ext4` (the backing file persists; only the mount needs to be re-established). The cross-fs mv evidence in the journal under `/root/` always survives. We umount and clean the image in the final cleanup step.

### Journal write — BEFORE cleanup

```bash
LAB=lab-10a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/mv-lab/task2/op.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Cross-fs mv — cp -p + rm under the hood, new inode, broken hard links
COMMANDS: df --output=source,fstype, mkfs.ext4, mount -o loop, stat -c '%i', ln, time mv
TRAPS:    T10-B rehearsed (inode CHANGES across fs; do not assume preservation)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-10b (Ansible) — command: mv boundary + copy: backup: true atomic replace
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
# Detach the loop mount and remove the backing image
umount /tmp/mv-lab/mnt2 2>/dev/null
rm -f  /tmp/mv-lab/img.ext4
rm -rf /tmp/mv-lab
test -d /tmp/mv-lab || echo "sandbox gone — clean exit"
mount | grep mnt2 || echo "loop mount detached"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `df -T` shows both paths on the same source | Loop mount did not take. Re-run `mount -o loop /tmp/mv-lab/img.ext4 /tmp/mv-lab/mnt2` and check `dmesg \| tail`. |
| `mkfs.ext4` complains about block size | The backing file is too small. Bump `count=10` in `dd` to `count=20`. |
| `mv` to mnt2 returns "Read-only file system" | The loop mount was made read-only somehow. Remount with `mount -o remount,rw`. |
| `time mv` shows zero wall time | You are actually on a same-fs target. Re-verify `df --output=source` on both paths. |
| Hard link inodes still match after cross-fs mv | You wrote to a bind mount, not a separate filesystem. Bind mounts share the underlying inode table. |
| `umount` says "target is busy" | Some shell is `cd`'d into `/tmp/mv-lab/mnt2`. `cd /` first, then retry. |

> **STOP — paste the `INODE_CHANGED` and `HARD_LINK_BROKEN` lines, and the `cat $JDIR/done.txt` output before moving to Lab 10b.**

---

## Lab 10a Checklist (2 tasks)

- [ ] Task 1 — Same-fs `mv`: rename in place, move into a directory, the four guard switches (`-i`/`-n`/`-b`/`-u`), `-t` target-first batch, hard-link survival + journal evidence
- [ ] Task 2 — Cross-fs `mv` on a loop-mounted ext4: inode CHANGES, hard links BREAK, wall-clock cost is non-zero + journal evidence

---

## 🔗 Related Labs in the Trilogy

| Lab | Connection |
|---|---|
| **Lab 10b** — Moving & Atomic Config Replace via Ansible | `command: mv` boundary with `creates:`/`removes:`, plus `ansible.builtin.copy` with `backup: true` for atomic replace |
| **Lab 10c** — Verifying Moves & Atomic Replace | The auditor seat: `stat -c '%n %i'`, `test -e SRC`, `test -e DST`, `ls -la DST.backup~*`, simulated-reboot rollback |
| **Lab 11a** — Safe Deletion (RHCSA) | `mv DIR /tmp/trash/` is the reversible "quarantine" alternative to `rm` |
| Lab 09 — Hard and Soft Links | The `ln` foundation — hard links survive same-fs mv, break across fs |
| Lab 14a — File Searching with `find` | `find PATH -mtime +N -exec mv -t /archive {} +` is the criteria-based batch-move pattern |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
