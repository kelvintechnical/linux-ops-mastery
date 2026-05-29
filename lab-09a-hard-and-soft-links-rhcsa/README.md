# Lab 09a: Hard & Soft Links (RHCSA) — `ln`, `ln -s`, `readlink -f`, inode counting

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** **`09a` (RHCSA — you are here)** → `09b` (Ansible) → `09c` (Verify)
- **Career arcs covered:** RHCSA EX200 (`ln` / `ln -s`, inode inspection, dangling symlink diagnosis), RHCE EX294 (foundation for `ansible.builtin.file: state=link`), SRE (atomic release promotion via `ln -sfn`), DevOps (blue-green deployments via symlink swap)
- **Prerequisite:** Lab 08 (`cp`, `cp -a`)
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = hard links, Task 2 = soft/symbolic links)
- **Practice Directory (lab-wide rotation #09):** `/var/log`
- **Sandbox:** `/tmp/links-lab/`
- **Traps rehearsed this lab:** **T17** (hard link across filesystems → `Invalid cross-device link`) · **T18** (`ln -s` with a **relative** source path — resolves relative to the **link's location**, not your cwd; the #1 broken-symlink cause) · **T19** (`rm SYMLINK/` with a trailing slash can delete the **target directory's contents** on some shells — modern `rm` refuses, but muscle memory should still be `rm SYMLINK` without `/`)

> **This lab's practice directory is: `/var/log`** — we read its real symlinks (`/var/log/journal` etc.). The sandbox is `/tmp/links-lab/` where we create, break, and inspect links.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T17 T18 T19"
echo "📁  PRACTICE DIR: /var/log"
echo ""
echo "💡 Real symlinks in /var/log (read-only):"
find /var/log -maxdepth 2 -type l 2>/dev/null | head -5
ls -l /etc/localtime    # famous real-world symlink
```

> **STOP — paste header output before running setup.**

---

## 🎯 Objective

Build and inspect both kinds of Linux links by hand — the RHCSA way. By the end of this lab you can create a hard link and prove it shares an inode, create a symbolic link and follow it with `readlink -f`, demonstrate that removing one hard-link name does not free the data, and spot a dangling symlink before a service restart surprises you.

---

## 🧠 Concept: Inode vs Name — Hard Link = Same Inode, Soft Link = Path String

Every file on disk is an **inode** (metadata + data blocks). A **filename** is just a directory entry pointing at an inode.

```
   HARD LINK (ln SRC DST)              SOFT LINK (ln -s SRC DST)
   ┌─────────┐  ┌─────────┐           ┌─────────┐         ┌─────────┐
   │ data.txt│  │hard-link│           │soft-link│ ──────► │ data.txt│
   └────┬────┘  └────┬────┘           └────┬────┘  path  └────┬────┘
        │            │                     │   string          │
        └─────┬──────┘                     own inode             own inode
              │                                                  (different)
         SAME inode #12345
         link count = 2
```

- **Hard link:** second **name** for the same inode. Same filesystem only. All names are equal partners — `rm` of any one decrements the link count; data is freed only when count hits 0.
- **Soft (symbolic) link:** tiny file with its **own inode** whose content is a path string. Can cross filesystems, can point at directories, can **dangle** when the target is removed.

`readlink PATH` prints the literal target string. `readlink -f PATH` follows the chain to the canonical absolute path — the form scripts and auditors trust.

---

## 📚 Link Reference (everything you need for Tasks 1–2)

| Task | Command | Notes |
|---|---|---|
| Hard link | `ln SRC DST` | Same inode, same fs only |
| Hard link force | `ln -f SRC DST` | Replace DST if it exists |
| Soft link | `ln -s TARGET LINK` | Separate inode; TARGET can be relative or absolute |
| Atomic symlink swap | `ln -sfn NEW TARGET` | Canonical "promote new release" pattern |
| Inode number | `stat -c '%i' FILE` | Programmatic compare |
| Link count | `stat -c '%h' FILE` | Number of hard links to this inode |
| Follow symlink | `readlink PATH` | Literal target string |
| Canonical path | `readlink -f PATH` | Resolves chains to absolute path |
| Reverse lookup | `find DIR -inum N` | All hard-link names for inode N |
| Is symlink? | `test -L PATH` | Does NOT follow |
| Target exists? | `test -e PATH` | FOLLOWS symlinks |

> **Rule of links:** Use `ln` (no `-s`) for redundant names on the **same filesystem**. Use `ln -s` for cross-fs pointers, directory aliases, and release-promotion symlinks.

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i
mkdir -p /tmp/links-lab
echo "original content" | tee /tmp/links-lab/data.txt
mkdir -p /root/rhcsa_journal/lab-09a
ls -li /tmp/links-lab/
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

## Task 1 — Hard Links: `ln`, inode equality, link count, `find -inum`

**Practice directory this task:** `/var/log` (read-only context for real symlinks), `/tmp/links-lab` (write)

### 🔁 Warm-Up — commands woven into Task 1

```bash
mkdir -p /root/rhcsa_journal/lab-09a/task1
date -Is | tee /root/rhcsa_journal/lab-09a/task1/start.txt
ls -li /tmp/links-lab/data.txt | tee -a /root/rhcsa_journal/lab-09a/task1/start.txt
stat -c 'inode=%i links=%h' /tmp/links-lab/data.txt | tee -a /root/rhcsa_journal/lab-09a/task1/start.txt
find /var/log -maxdepth 2 -type l 2>/dev/null | head -3
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 08: `cp -a` preserves inode on same filesystem — hard links are the manual way to create a second name for an existing inode without copying bytes.

### Purpose

Create a hard link with `ln` (no `-s`), prove both names share the same inode via `ls -li` and `stat -c '%i %h'`, remove the "original" name and observe the data persists through the remaining hard link, then reverse-lookup all names with `find -inum`.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `ls -li` | Side-by-side inode column — the visual proof hard links match |
| `stat -c 'inode=%i links=%h'` | Programmatic link-count baseline before and after `ln` |
| `find /var/log -type l` | Read-only contrast: symlinks in practice dir vs hard links we build |
| `2>&1 \| tee` | Captures the full transcript into `task1/transcript.txt` |
| `$(date -Is)` | Stamps journal `done.txt` |

### Main command block

```bash
cd /tmp/links-lab

# Before: data.txt link count is 1
stat -c 'inode=%i links=%h' /tmp/links-lab/data.txt

# Create the hard link
ln /tmp/links-lab/data.txt /tmp/links-lab/hard-link

# After: link count is 2 on BOTH names (they're the same inode)
stat -c 'inode=%i links=%h' /tmp/links-lab/data.txt
stat -c 'inode=%i links=%h' /tmp/links-lab/hard-link

# Confirm same inode
ls -li /tmp/links-lab/data.txt /tmp/links-lab/hard-link

# Find all paths pointing at that inode
inode=$(stat -c '%i' /tmp/links-lab/data.txt)
find /tmp/links-lab -inum $inode

# Make a second hard link, link count becomes 3
ln /tmp/links-lab/data.txt /tmp/links-lab/hard-link-2
stat -c 'links=%h' /tmp/links-lab/data.txt

# Modifying through ANY hard link affects ALL (because they ARE the same file)
sh -c 'echo "added line" >> /tmp/links-lab/hard-link'
cat /tmp/links-lab/data.txt
cat /tmp/links-lab/hard-link-2

# Remove the "original" filename — data survives via remaining hard links
rm /tmp/links-lab/data.txt
echo "=== after rm data.txt ==="
ls -li /tmp/links-lab/
cat /tmp/links-lab/hard-link            # works — same inode still alive
stat -c 'links=%h' /tmp/links-lab/hard-link

# Restore the original name via remaining hard link
ln /tmp/links-lab/hard-link /tmp/links-lab/data.txt
ls -li /tmp/links-lab/

# Try to hard-link a directory — fails (T18 variant)
ln /tmp/links-lab /tmp/links-lab-dir-link 2>&1 | head -1

# Try to hard-link across filesystems — fails (T17)
ln /tmp/links-lab/data.txt /tmp/cross-fs-hard 2>&1 | head -1   # EXDEV if /tmp is separate fs

# Capture
{
  echo "=== inode match ==="; ls -li /tmp/links-lab/data.txt /tmp/links-lab/hard-link
  echo "=== link count ==="; stat -c 'inode=%i links=%h' /tmp/links-lab/data.txt
  echo "=== find -inum ==="
  find /tmp/links-lab -inum $(stat -c '%i' /tmp/links-lab/data.txt)
} 2>&1 | tee /root/rhcsa_journal/lab-09a/task1/transcript.txt

echo "exit was: $?"
```

### Human-readable breakdown

1. `stat -c '%h'` before `ln` shows link count **1** — one name points at the inode.
2. `ln SRC DST` creates a second directory entry pointing at the **same inode** — no bytes copied.
3. `ls -li` shows identical inode numbers in column 1; column 2 (link count) jumps to 2, then 3.
4. `rm data.txt` decrements the link count but does **not** free data while `hard-link` still references the inode.
5. `find -inum N` is the canonical reverse lookup — "show me every filename for this inode."
6. Cross-filesystem and directory hard links fail — that's T17 in action.

### Reading it left to right

- `ln TARGET LINK` — link tool, no `-s` = hard link; TARGET must exist; LINK is the new alias.
- `stat -c '%i'` — inode number; `%h` — hard link count.
- `find /tmp/links-lab -inum 12345` — search by inode; finds all hard-link siblings.
- `rm FILE` — removes one name; decrements link count; frees inode only when count = 0.

### The story

A grader: "find all paths in `/var/log` that share an inode with `/var/log/messages`." Answer: `find /var/log -inum $(stat -c '%i' /var/log/messages)`. Hard links protect against accidental `rm` of a single name — if you had a hard link elsewhere, the data was never freed. That's the operational value senior admins reach for when a "source" file disappears but a backup hard link still holds the inode alive.

### Expected output

```text
inode=12345 links=1

12345 -rw-r--r--. 2 root root 17 May 27 15:01 /tmp/links-lab/data.txt
12345 -rw-r--r--. 2 root root 17 May 27 15:01 /tmp/links-lab/hard-link
^^^^^               ^^
same inode         link count: 2

/tmp/links-lab/data.txt
/tmp/links-lab/hard-link
/tmp/links-lab/hard-link-2

=== after rm data.txt ===
12345 -rw-r--r--. 2 root root 28 May 27 15:05 hard-link
12345 -rw-r--r--. 2 root root 28 May 27 15:05 hard-link-2

ln: /tmp/links-lab: hard link not allowed for directory
ln: failed to create hard link '/tmp/cross-fs-hard' => '/tmp/links-lab/data.txt': Invalid cross-device link
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| `ln TARGET LINK` | Create hard link — same inode, different name |
| `ln -f` | Force — replace LINK if it exists |
| `stat -c '%i'` | Inode number |
| `stat -c '%h'` | Hard link count |
| `find -inum N` | Find all paths with inode N |
| `ls -li` | Long listing with inode column |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | Hard link | Second filename for the same inode (= same file) |
|   | Same inode | `stat -c %i` matches; `ls -li` shows same number |
|   | Link count | `stat -c %h` = number of hard links |
|   | `find -inum N` | Find all paths pointing at inode N |
|   | Cross-fs forbidden | Each filesystem has its own inode table |
|   | Directories forbidden | Would create cycles — use `ln -s` instead |
| 🪤 | **Trap Risk T17** | `ln` (no `-s`) fails across filesystems with `Invalid cross-device link` — use `ln -s` for cross-fs |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Hard links share inode | `[ "$(stat -c '%i' /tmp/links-lab/data.txt)" = "$(stat -c '%i' /tmp/links-lab/hard-link)" ] && echo OK` | Core RHCSA proof |
| Link count ≥ 2 | `[ "$(stat -c '%h' /tmp/links-lab/data.txt)" -ge 2 ] && echo OK` | Confirms aliasing |
| Reverse lookup | `find /tmp/links-lab -inum "$(stat -c '%i' /tmp/links-lab/data.txt)"` | Finds all sibling names |

> **Reboot reasoning:** `/tmp/links-lab/` is tmpfs on most systems — hard links evaporate at reboot. The **journal transcript** under `/root/rhcsa_journal/lab-09a/` is what survives.

### Journal write — BEFORE cleanup

```bash
LAB=lab-09a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /root/rhcsa_journal/lab-09a/task1/transcript.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
inode=$(stat -c '%i' /tmp/links-lab/data.txt)
link_count=$(stat -c '%h' /tmp/links-lab/data.txt)
found_paths=$(find /tmp/links-lab -inum "$(stat -c '%i' /tmp/links-lab/data.txt)" | wc -l)
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Hard links — ln, inode equality, link count, find -inum
COMMANDS: ln, ls -li, stat -c '%i %h', find -inum, rm
TRAPS:    T17 rehearsed (cross-device hard link fails)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — soft/symbolic links, readlink -f, dangling symlinks, ln -sfn
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

Leave hard links in place — Task 2 adds symlinks alongside them.

### Troubleshoot

| Symptom | Fix |
|---|---|
| `Invalid cross-device link` | EXDEV — different filesystems; use `ln -s` (T17) |
| `hard link not allowed for directory` | Only `ln -s` works for directories |
| `hard-link` content gone after `rm data.txt` | Link count must have hit 0 — check `stat -c '%h'` BEFORE rm |
| Inodes don't match | You created a copy with `cp`, not a link with `ln` |

> **STOP — confirm `link_count >= 2` in done.txt before Task 2.**

---

## Task 2 — Soft Links: `ln -s`, `readlink -f`, dangling symlinks, `ln -sfn`

**Practice directory this task:** `/var/log` (real symlinks), `/tmp/links-lab` (write)

### 🔁 Warm-Up — commands woven into Task 2

```bash
mkdir -p /root/rhcsa_journal/lab-09a/task2
date -Is | tee /root/rhcsa_journal/lab-09a/task2/start.txt
ls -li /tmp/links-lab/ | tee -a /root/rhcsa_journal/lab-09a/task2/start.txt
ls -l /etc/localtime | tee -a /root/rhcsa_journal/lab-09a/task2/start.txt
readlink /etc/localtime
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: hard links share an inode; symlinks will show **different** inodes in `ls -li`.

### Purpose

Create a symbolic link with `ln -s`, contrast `readlink` vs `readlink -f`, use `test -L` vs `test -e` to distinguish symlink-ness from target reachability, deliberately break a symlink (dangle it), demonstrate the T18 relative-path trap, and perform an atomic symlink update with `ln -sfn`.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `ls -l /etc/localtime` | Real-world symlink example from practice dir rotation |
| `readlink /etc/localtime` | Shows literal target string before we build our own |
| `ls -li /tmp/links-lab/` | Baseline inode column — symlinks will differ from data.txt |
| `2>&1 \| tee` | Full transcript in `task2/transcript.txt` |
| `$(date -Is)` | Journal timestamp |

### Main command block

```bash
cd /tmp/links-lab

# Create the symlink: ln -s TARGET LINKNAME (absolute path — safe form)
ln -s /tmp/links-lab/data.txt /tmp/links-lab/soft-link

# Inspect — note: inode of soft-link != inode of data.txt
ls -li /tmp/links-lab/
# soft-link:  lrwxrwxrwx ... soft-link -> /tmp/links-lab/data.txt

# Follow the symlink
readlink /tmp/links-lab/soft-link
readlink -f /tmp/links-lab/soft-link    # canonical absolute path (follows chain)

# Reading the symlink reads the target's content
cat /tmp/links-lab/soft-link
[ "$(cat /tmp/links-lab/soft-link)" = "$(cat /tmp/links-lab/data.txt)" ] && echo "contents identical"

# test -L (is symlink) vs test -e (target exists)
test -L /tmp/links-lab/soft-link && echo "is a symlink"
test -e /tmp/links-lab/soft-link && echo "target reachable"

# ── T18: relative path trap ──
mkdir -p /tmp/links-lab/subdir
ln -s data.txt /tmp/links-lab/subdir/broken-relative    # WRONG if cwd != subdir
readlink /tmp/links-lab/subdir/broken-relative
cat /tmp/links-lab/subdir/broken-relative 2>&1 || echo "(broken — relative resolved from LINK dir, not cwd)"

# Fix: relative path must be relative to the LINK's directory
ln -sf ../data.txt /tmp/links-lab/subdir/good-relative
readlink -f /tmp/links-lab/subdir/good-relative

# ── Dangling symlink demonstration ──
mv /tmp/links-lab/data.txt /tmp/links-lab/data.txt.bak
ls -l /tmp/links-lab/soft-link          # ls shows it (often in red: dangling)
cat /tmp/links-lab/soft-link 2>&1 || echo "(read failed — symlink dangles)"
test -L /tmp/links-lab/soft-link && echo "still a symlink"
test -e /tmp/links-lab/soft-link && echo "target exists" || echo "TARGET MISSING (symlink dangles)"
readlink /tmp/links-lab/soft-link        # still returns the (now-missing) target string

# Restore target
mv /tmp/links-lab/data.txt.bak /tmp/links-lab/data.txt
test -e /tmp/links-lab/soft-link && echo "target reachable again"

# ── Atomic "promote new release" pattern (ln -sfn) ──
mkdir -p /tmp/links-lab/releases/v1 /tmp/links-lab/releases/v2
echo "release v1" > /tmp/links-lab/releases/v1/app.conf
echo "release v2" > /tmp/links-lab/releases/v2/app.conf
ln -sfn /tmp/links-lab/releases/v1/app.conf /tmp/links-lab/current
readlink -f /tmp/links-lab/current
cat /tmp/links-lab/current

# Promote v2 — atomic swap
ln -sfn /tmp/links-lab/releases/v2/app.conf /tmp/links-lab/current
readlink -f /tmp/links-lab/current
cat /tmp/links-lab/current

# ── T19 reminder: rm SYMLINK/ vs rm SYMLINK ──
mkdir -p /tmp/links-lab/target-dir
echo "precious" > /tmp/links-lab/target-dir/important.txt
ln -s /tmp/links-lab/target-dir /tmp/links-lab/dir-link
echo "SAFE:   rm /tmp/links-lab/dir-link        # removes the symlink only"
echo "TRAP:   rm /tmp/links-lab/dir-link/       # may delete TARGET dir contents (T19)"
# Do NOT run the trap line — modern rm refuses with trailing slash on symlink-to-dir

# Capture
{
  echo "=== inodes (should differ) ==="; ls -li /tmp/links-lab/data.txt /tmp/links-lab/soft-link
  echo "=== readlink ==="; readlink /tmp/links-lab/soft-link
  echo "=== readlink -f ==="; readlink -f /tmp/links-lab/soft-link
  echo "=== dangling test ==="
  mv /tmp/links-lab/data.txt /tmp/links-lab/data.txt.bak
  test -L /tmp/links-lab/soft-link && echo "is symlink"
  test -e /tmp/links-lab/soft-link && echo "exists" || echo "MISSING"
  mv /tmp/links-lab/data.txt.bak /tmp/links-lab/data.txt
  echo "=== atomic promote ==="; readlink -f /tmp/links-lab/current
} 2>&1 | tee /root/rhcsa_journal/lab-09a/task2/transcript.txt

echo "exit was: $?"
```

### Human-readable breakdown

1. `ln -s TARGET LINK` creates a tiny file whose content is a path — own inode, `l` in `ls -l` column 1.
2. `readlink` prints the stored path; `readlink -f` resolves chains to the canonical absolute destination.
3. `test -L` answers "is this a symlink?" (no follow). `test -e` answers "does the target exist?" (follows) — the pair catches T19 dangling cases.
4. T18: a relative `TARGET` resolves from the **link's directory**, not your shell cwd — the #1 cause of broken symlinks in the wild.
5. `ln -sfn NEW LINK` atomically repoints a symlink — the blue-green / release-promotion pattern DevOps teams use daily.

### Reading it left to right

- `ln -s TARGET LINK` — `-s` = soft/symbolic; TARGET can be relative or absolute; LINK is the new symlink name.
- `lrwxrwxrwx` — `l` = symlink; mode is ignored; target's mode is what matters.
- `readlink -f PATH` — follow chain; equivalent to `realpath`.
- `ln -sfn NEW LINK` — `-s` soft, `-f` force replace, `-n` don't dereference LINK if it's a symlink to a dir.

### The story

Every RHEL admin uses symlinks daily — `/etc/localtime`, systemd `.wants/` links, `alternatives`. The release-promotion pattern (`current -> releases/v2/app.conf`) is how Nginx, Tomcat, and Kubernetes deployments swap versions without renaming directories. Reading `readlink -f` output fluently is RHCSA-grade; writing relative symlinks correctly (T18) separates juniors from seniors.

### Expected output

```text
12345 -rw-r--r--. 1 root root 28 ... data.txt
12346 lrwxrwxrwx. 1 root root 22 ... soft-link -> /tmp/links-lab/data.txt
^^^^^                                                ^^^^^
different inode                                      ls -l shows the arrow

/tmp/links-lab/data.txt
/tmp/links-lab/data.txt
contents identical
is a symlink
target reachable
(broken — relative resolved from LINK dir, not cwd)
/tmp/links-lab/data.txt
TARGET MISSING (symlink dangles)
/tmp/links-lab/releases/v2/app.conf
release v2
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| `ln -s TARGET LINK` | Create symbolic link |
| `ln -sf` | Force; replace LINK if it exists |
| `ln -snf` | `-s -n -f` — atomic repoint; required when LINK is symlink-to-dir |
| `readlink PATH` | Print literal target |
| `readlink -f PATH` | Canonical absolute path (follow chain) |
| `test -L PATH` | Is symlink (no follow) |
| `test -e PATH` | Target exists (follow) |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | Symlink | Tiny file whose content is a path |
|   | Own inode | Yes — different from target |
|   | Cross-filesystem | Yes — can link across `/`, `/home`, `/var` |
|   | Dangling | Target removed; `ls -l` still shows link; `cat` errors |
|   | `readlink -f` | Resolve the full chain — trust this over `ls` arrow alone |
|   | `ln -sfn` | Atomic release promotion |
| 🪤 | **Trap Risk T18** | Relative source resolves from LINK location, not cwd — #1 broken-symlink cause |
| 🪤 | **Trap Risk T19** | `rm SYMLINK/` may delete target dir contents — always `rm SYMLINK` without `/` |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Symlink exists | `test -L /tmp/links-lab/soft-link && echo OK` | Confirms link created |
| Target correct | `[ "$(readlink /tmp/links-lab/soft-link)" = "/tmp/links-lab/data.txt" ] && echo OK` | Points at right path |
| Release promoted | `readlink -f /tmp/links-lab/current` | Must show v2 after promote |
| Different inodes | `[ "$(stat -c '%i' /tmp/links-lab/data.txt)" != "$(stat -c '%i' /tmp/links-lab/soft-link)" ] && echo OK` | Proves soft ≠ hard |

> **Reboot reasoning:** `/tmp/links-lab/` clears on reboot. Hard links and symlinks created here are ephemeral. Lab 09b will recreate links declaratively via Ansible — that's the persistence path.

### Journal write — BEFORE cleanup

```bash
LAB=lab-09a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /root/rhcsa_journal/lab-09a/task2/transcript.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
data_inode=$(stat -c '%i' /tmp/links-lab/data.txt)
softlink_inode=$(stat -c '%i' /tmp/links-lab/soft-link)
target=$(readlink /tmp/links-lab/soft-link)
current=$(readlink -f /tmp/links-lab/current)
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Soft links — ln -s, readlink -f, test -L/-e, dangling, ln -sfn
COMMANDS: ln -s, readlink, readlink -f, test -L, test -e, ln -sfn
TRAPS:    T18 (relative path), T19 (rm SYMLINK/ trailing slash)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-09b — ansible.builtin.file state=link / state=hard
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
# Keep sandbox for Lab 09b — drop task transcripts only
rm -rf /root/rhcsa_journal/lab-09a/task1/start.txt /root/rhcsa_journal/lab-09a/task2/start.txt
ls /tmp/links-lab/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `ln: failed to create symbolic link: File exists` | LINK name already exists — use `-f` to force |
| `readlink` returns nothing | Argument is not a symlink — check `ls -l` |
| Reading symlink errors with `ENOENT` | Target removed — symlink dangles (T19) |
| Relative symlink broken | Path resolves from link dir, not cwd (T18) — use absolute or fix relative path |
| `ln -sfn` didn't repoint | Missing `-n` when LINK is symlink-to-dir |

> **STOP — paste `readlink -f /tmp/links-lab/current` showing v2 before Lab 09b.**

---

## Lab 09a Checklist (2 tasks)

- [ ] Task 1 — Hard links with `ln`, inode match via `ls -li` / `stat -c '%h'`, survive `rm` of one name, `find -inum` reverse lookup + journal evidence
- [ ] Task 2 — Soft links with `ln -s`, `readlink -f`, `test -L`/`test -e`, dangling demo, T18 relative-path trap, atomic `ln -sfn` promote + journal evidence

---

## 🔗 Related Labs in the Trilogy

| Lab | Connection |
|---|---|
| **Lab 09b** — Managing Links via Ansible | `ansible.builtin.file: state=link` / `state=hard` — declarative form of what you typed here |
| **Lab 09c** — Verifying Links | The auditor seat: prove links behave correctly with RHCSA inspection commands |
| Lab 08 — Copying Files (`cp`, `cp -a`) | Prerequisite — `cp -a` preserves metadata; hard links alias without copying |
| Lab 11a — Safe Deletion (`rm`) | Removing a hard-link name decrements count; removing a symlink removes only the link inode |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
