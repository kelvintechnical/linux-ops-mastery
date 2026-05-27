# Lab 09: Hard and Soft Links — `ln`, `ln -s`, `readlink`, `find -inum`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Career arcs covered:** RHCSA EX200 (symlinks in `/etc`, systemd `mask` = link to `/dev/null`, alternatives), RHCE EX294 (`ansible.builtin.file: state=link`, `state=hard`), CKA (`/var/log/containers/` symlinks, kubelet volume links), RHCA — RH342 (forensic inode tracking with `find -inum`)
- **Prerequisite:** Lab 00 (Ansible control node) + Lab 08 (`cp`, `cp -a`)
- **Time Estimate:** 35–50 minutes
- **Tasks:** 5 (ADHD 3-1-1 spec — 3 RHCSA + 1 Ansible + 1 Verification capstone)
- **Practice Directory (lab-wide rotation #09):** `/var/log` (real symlinks live here — `/var/log/journal` etc)
- **Sandbox:** `/srv/link-lab`
- **Traps rehearsed this lab:** **T17** (`systemctl mask` = symlink to `/dev/null` — `disable` is different) · **T18** (`ln` (no `-s`) creates a HARD link — fails across filesystems and on directories) · **T19** (Dangling symlinks return success from `ls -l` but `cat` fails with "No such file" — use `test -e` not `test -L`)

> **This lab's practice directory is: `/var/log`** — we read its real symlinks. The sandbox is `/srv/link-lab` where we create, break, and inspect links.

---

## 🖥️ LAB HEADER BLOCK — run this FIRST

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
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

Build, inspect, and break both kinds of Linux links. By the end you will:

- Make a **hard link** with `ln` and see its inode is identical to the original
- Make a **soft link** (symlink) with `ln -s` and see it has its own inode that points at a path
- Break a hard link's "source" and observe the data persists (hard links are equal partners)
- Break a soft link's target and observe the symlink dangles (`ls -l` shows it, `cat` fails)
- Use `find -inum` to find every hard link to a given inode
- Replicate with `ansible.builtin.file: state=link` and `state=hard`

---

## 🛠️ Setup — run once before Task 1

```bash
sudo mkdir -p /srv/link-lab
echo "original content" | sudo tee /srv/link-lab/data.txt
sudo mkdir -p /root/rhcsa_journal/lab09
ls -li /srv/link-lab/
```

---

## Task 1 — Soft Links: `ln -s`, `readlink`, Symlink Behavior

**Practice directory this task:** `/var/log` (real symlinks), `/srv/link-lab` (write)

### 🔁 Warm-Up — Commands from Previous Labs

```bash
sudo mkdir -p /root/rhcsa_journal/lab09/task1
date -Is | sudo tee /root/rhcsa_journal/lab09/task1/start.txt
ls -li /srv/link-lab/data.txt | sudo tee -a /root/rhcsa_journal/lab09/task1/start.txt
ls -l /etc/localtime | sudo tee -a /root/rhcsa_journal/lab09/task1/start.txt
echo "exit was: $?"
```

### Purpose

Create a symbolic link with `ln -s`, observe that it has its own inode and shows up as `l` in `ls -l` column 1, follow the link with `readlink`, and observe the size column = number of bytes in the target path string.

### Main Command Block

```bash
# Create the symlink: ln -s TARGET LINKNAME
sudo ln -s /srv/link-lab/data.txt /srv/link-lab/soft-link

# Inspect
ls -li /srv/link-lab/
# data.txt:   ` ... 12345 -rw-r--r--  1 root root  17 ... data.txt `
# soft-link:  ` ... 12346 lrwxrwxrwx  1 root root  22 ... soft-link -> /srv/link-lab/data.txt `

# Note: inode of soft-link != inode of data.txt; size of soft-link = 22 (bytes of target path)

# Follow the symlink
readlink /srv/link-lab/soft-link
readlink -f /srv/link-lab/soft-link    # canonical absolute path (follows chain)

# Reading the symlink reads the target's content
cat /srv/link-lab/soft-link
[ "$(cat /srv/link-lab/soft-link)" = "$(cat /srv/link-lab/data.txt)" ] && echo "contents identical"

# Real-world example
ls -l /etc/localtime
readlink /etc/localtime

# Capture
{
  echo "=== inodes (should differ) ==="; ls -li /srv/link-lab/data.txt /srv/link-lab/soft-link
  echo "=== readlink ==="; readlink /srv/link-lab/soft-link
  echo "=== readlink -f ==="; readlink -f /srv/link-lab/soft-link
  echo "=== /etc/localtime example ==="; ls -l /etc/localtime; readlink /etc/localtime
} 2>&1 | sudo tee /root/rhcsa_journal/lab09/task1/transcript.txt
```

### Human-Readable Breakdown

A symlink is a tiny file whose **content is a path**. The kernel notices "this file is a symlink" and substitutes the target whenever something tries to open it. Key properties:

- Has its **own inode** — `ls -li` shows two different numbers
- Column 1 of `ls -l` is `l` (lowercase L)
- The "size" column = byte length of the path string (`/srv/link-lab/data.txt` = 22 chars = 22 bytes)
- Mode column is always `lrwxrwxrwx` — mode is ignored, the target's mode is what matters
- Can point ACROSS filesystems
- Can point at DIRECTORIES
- Can DANGLE (target removed → link still exists, but reading it errors with `ENOENT`)

`readlink` prints the literal target string. `readlink -f` (or `realpath`) follows the chain to the canonical absolute path.

### Reading It Left to Right

`ln -s TARGET LINK`

- `ln` — link tool
- `-s` — soft (symbolic) link; without `-s` you get a hard link
- `TARGET` — what the link points at (can be relative or absolute)
- `LINK` — the name of the new symlink

`lrwxrwxrwx`

- `l` — symbolic link
- `rwxrwxrwx` — the symlink's mode (always all-rwx; ignored by kernel)

### The Story

Every RHEL admin uses symlinks daily without naming them — `/etc/localtime` is a symlink to `/usr/share/zoneinfo/America/New_York`, `/usr/lib/systemd/system/multi-user.target.wants/sshd.service` is a symlink to `/usr/lib/systemd/system/sshd.service`, and `systemctl mask SERVICE` creates a symlink from `/etc/systemd/system/SERVICE` to `/dev/null` (T17). Reading these structures fluently is RHCSA-grade.

### Expected Output

```
$ ls -li /srv/link-lab/
total 4
12345 -rw-r--r--. 1 root root 17 May 27 15:01 data.txt
12346 lrwxrwxrwx. 1 root root 22 May 27 15:02 soft-link -> /srv/link-lab/data.txt
^^^^^                                                ^^^^^
different inode                                      ls -l shows the arrow

$ readlink /srv/link-lab/soft-link
/srv/link-lab/data.txt

$ readlink -f /srv/link-lab/soft-link
/srv/link-lab/data.txt
```

### Switches Table

| Switch | Meaning | Why it matters |
|---|---|---|
| `ln -s TARGET LINK` | Create symbolic link | The base case |
| `ln -sf` | Force; replace LINK if it exists | Re-pointing a symlink |
| `ln -snf` | `-s -n -f` — don't follow LINK if it's a dir | Required when LINK is itself a symlink to a dir |
| `readlink PATH` | Print literal target | Quick "what does this link point to?" |
| `readlink -f PATH` | Canonical absolute path (follow chain) | Useful for scripts |
| `realpath PATH` | Equivalent to `readlink -f` | Some prefer this name |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| Symlink | Tiny file whose content is a path |
| Own inode | Yes — different from target |
| Cross-filesystem | Yes — can link across `/`, `/home`, `/var` |
| Directory target | Yes — `ln -s /var /tmp/var-link` works |
| Dangling | Yes — target removed, link remains but reads fail |
| `readlink -f` | Resolve the full chain |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| **T17** | `systemctl mask` creates a symlink to `/dev/null`; unmask = remove symlink. Easy to confuse with `disable` | Use `systemctl list-unit-files` to see what's masked; `mask` → linked to /dev/null |
| **T19** | A dangling symlink looks fine in `ls -l` but `cat` errors | Use `test -e` (exists, follows symlinks) instead of `test -L` (is a symlink) for "is the data there?" |

### 🔁 Persistence Check

```bash
test -L /srv/link-lab/soft-link && echo "is a symlink"
test -e /srv/link-lab/soft-link && echo "target reachable"
[ "$(cat /srv/link-lab/soft-link)" = "$(cat /srv/link-lab/data.txt)" ] && echo "content matches"
```

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab09/task1/done.txt > /dev/null <<EOF
lab=09 task=1
when=$(date -Is)
practice_dir=/var/log
data_inode=$(stat -c '%i' /srv/link-lab/data.txt)
softlink_inode=$(stat -c '%i' /srv/link-lab/soft-link)
target=$(readlink /srv/link-lab/soft-link)
EOF
cat /root/rhcsa_journal/lab09/task1/done.txt
```

### 🧹 Cleanup

Leave the symlink — Task 3 breaks it deliberately.

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `ln: failed to create symbolic link: File exists` | LINK name already exists — use `-f` to force, or pick a new name |
| `readlink` returns nothing | Argument is not a symlink — check `ls -l` |
| Reading symlink errors with `ENOENT` | Target was removed — symlink dangles (T19) |

> **STOP — confirm two different inodes in done.txt before Task 2.**

---

## Task 2 — Hard Links: `ln`, Inode Equality, Link Count

**Practice directory this task:** `/srv/link-lab` (write)

### 🔁 Warm-Up — Commands from Previous Labs

```bash
sudo mkdir -p /root/rhcsa_journal/lab09/task2
date -Is | sudo tee /root/rhcsa_journal/lab09/task2/start.txt
ls -li /srv/link-lab/data.txt | sudo tee -a /root/rhcsa_journal/lab09/task2/start.txt
echo "exit was: $?"
```

### Purpose

Create a hard link with `ln` (no `-s`), observe the inode is **identical** to the source, watch the link count (`stat -c '%h'`) jump from 1 to 2, then find all hard links to that inode with `find -inum`.

### Main Command Block

```bash
# Before: data.txt link count is 1
stat -c 'inode=%i links=%h' /srv/link-lab/data.txt

# Create the hard link
sudo ln /srv/link-lab/data.txt /srv/link-lab/hard-link

# After: link count is 2 on BOTH names (they're the same inode)
stat -c 'inode=%i links=%h' /srv/link-lab/data.txt
stat -c 'inode=%i links=%h' /srv/link-lab/hard-link

# Confirm same inode
ls -li /srv/link-lab/data.txt /srv/link-lab/hard-link

# Find all paths pointing at that inode
inode=$(stat -c '%i' /srv/link-lab/data.txt)
sudo find /srv/link-lab -inum $inode

# Make a second hard link, link count becomes 3
sudo ln /srv/link-lab/data.txt /srv/link-lab/hard-link-2
stat -c 'links=%h' /srv/link-lab/data.txt

# Modifying through ANY hard link affects ALL (because they ARE the same file)
sudo sh -c 'echo "added line" >> /srv/link-lab/hard-link'
cat /srv/link-lab/data.txt
cat /srv/link-lab/hard-link-2

# Try to hard-link a directory — fails (T18)
sudo ln /srv/link-lab /srv/link-lab-dir-link 2>&1 | head -1

# Try to hard-link across filesystems — fails (T18)
sudo ln /srv/link-lab/data.txt /tmp/cross-fs-hard 2>&1 | head -1   # may work if /tmp is on same fs; if not, EXDEV

# Capture
{
  echo "=== before ==="; stat -c 'inode=%i links=%h' /srv/link-lab/data.txt
  echo "=== after first hard link ==="
  sudo ln -f /srv/link-lab/data.txt /srv/link-lab/hard-link
  ls -li /srv/link-lab/data.txt /srv/link-lab/hard-link
  echo "=== link count after two hard links ==="
  sudo ln -f /srv/link-lab/data.txt /srv/link-lab/hard-link-2
  stat -c 'inode=%i links=%h' /srv/link-lab/data.txt
  echo "=== find -inum ==="
  sudo find /srv/link-lab -inum $(stat -c '%i' /srv/link-lab/data.txt)
} 2>&1 | sudo tee /root/rhcsa_journal/lab09/task2/transcript.txt
```

### Human-Readable Breakdown

A hard link is a second **name** for the same inode. The inode is the data; the filename is just a label pointing at it. Key properties:

- **Same inode** — `ls -li` shows identical numbers
- Column 1 of `ls -l` is `-` (regular file), NOT `l`
- The "size" matches because there is one set of data bytes
- Link count (`stat -c '%h'`) = number of hard links to this inode
- Cannot cross filesystems (each filesystem has its own inode table)
- Cannot hard-link a directory on most filesystems (would create loops)
- All hard links are **equal partners** — there's no "original" — `rm` of any one decrements the link count by 1; data is freed only when count hits 0

`find -inum N` searches by inode number — the canonical way to find all hard links to a given file.

### Reading It Left to Right

`ln TARGET LINK`

- `ln` — link tool
- (no `-s`) — hard link
- `TARGET` — existing file (the inode you want to alias)
- `LINK` — new filename pointing at the same inode

`stat -c '%h' FILE`

- `stat` — file metadata
- `-c '%h'` — hard link count

`find /srv/link-lab -inum 12345`

- `find` — search
- `/srv/link-lab` — start path
- `-inum 12345` — match by inode number

### The Story

A grader: "find all paths in `/var/log` that share an inode with `/var/log/messages`." Answer: `find /var/log -inum $(stat -c '%i' /var/log/messages)`. Real systems use hard links for things like log rotation snapshots, `make install` pseudo-installs, and rsync's `--link-dest=` incremental backups.

### Expected Output

```
$ stat -c 'inode=%i links=%h' /srv/link-lab/data.txt
inode=12345 links=1

$ sudo ln /srv/link-lab/data.txt /srv/link-lab/hard-link
$ ls -li /srv/link-lab/data.txt /srv/link-lab/hard-link
12345 -rw-r--r--. 2 root root 17 May 27 15:01 /srv/link-lab/data.txt
12345 -rw-r--r--. 2 root root 17 May 27 15:01 /srv/link-lab/hard-link
^^^^^               ^^
same inode         link count: 2

$ sudo find /srv/link-lab -inum 12345
/srv/link-lab/data.txt
/srv/link-lab/hard-link
/srv/link-lab/hard-link-2
```

When you try to hard-link a directory:

```
ln: /srv/link-lab: hard link not allowed for directory
```

### Switches Table

| Switch | Meaning | Why it matters |
|---|---|---|
| `ln TARGET LINK` | Create hard link | Same inode, different name |
| `ln -f` | Force | Replace LINK if it exists |
| `find -inum N` | Find by inode | Locate all hard links |
| `stat -c '%i'` | Inode number | Programmatic compare |
| `stat -c '%h'` | Hard link count | Detect aliasing |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| Hard link | Second filename for the same inode (= same file) |
| Same inode | `stat -c %i` matches; `ls -li` shows same number |
| Link count | `stat -c %h` = number of hard links |
| `find -inum N` | Find all paths pointing at inode N |
| Cross-fs forbidden | Each filesystem has its own inode table |
| Directories forbidden | Would create cycles |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| **T18** | `ln` (no `-s`) fails across filesystems with `EXDEV` | Use `ln -s` for cross-fs; check with `df` if confused |
| **T18-b** | `ln` of a directory fails with `EPERM` | Only `ln -s` works for directories |
| Aliasing surprise | `rm data.txt` doesn't free space because `hard-link` still references the inode | Check link count with `stat -c %h` before assuming `rm` frees data |

### 🔁 Persistence Check

```bash
[ "$(stat -c '%i' /srv/link-lab/data.txt)" = "$(stat -c '%i' /srv/link-lab/hard-link)" ] && echo "same inode"
[ "$(stat -c '%h' /srv/link-lab/data.txt)" -ge 2 ] && echo "link count >= 2"
sudo find /srv/link-lab -inum "$(stat -c '%i' /srv/link-lab/data.txt)" | wc -l
```

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab09/task2/done.txt > /dev/null <<EOF
lab=09 task=2
when=$(date -Is)
inode=$(stat -c '%i' /srv/link-lab/data.txt)
link_count=$(stat -c '%h' /srv/link-lab/data.txt)
found_paths=$(sudo find /srv/link-lab -inum "$(stat -c '%i' /srv/link-lab/data.txt)" | wc -l)
EOF
cat /root/rhcsa_journal/lab09/task2/done.txt
```

### 🧹 Cleanup

Leave hard links; Task 3 deletes the original and observes what happens.

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `ln: failed to create hard link 'X' => 'Y': Invalid cross-device link` | EXDEV — `/srv` and `/tmp` on different filesystems; use `ln -s` |
| `ln: 'X': hard link not allowed for directory` | Use `ln -s` for directories |

> **STOP — confirm `link_count >= 2` in done.txt before Task 3.**

---

## Task 3 — Break the Source: Hard Link Survives, Symlink Dangles

**Practice directory this task:** `/srv/link-lab` (write)

### 🔁 Warm-Up — Commands from Previous Labs

```bash
sudo mkdir -p /root/rhcsa_journal/lab09/task3
date -Is | sudo tee /root/rhcsa_journal/lab09/task3/start.txt
ls -li /srv/link-lab/ | sudo tee -a /root/rhcsa_journal/lab09/task3/start.txt
echo "exit was: $?"
```

### Purpose

Remove the original `data.txt`. Watch the hard link continue to read normally (it's the same inode — equal partner). Watch the symlink dangle (target is gone, `ls -l` still shows the link, but `cat` errors).

### Main Command Block

```bash
# Before delete
ls -li /srv/link-lab/
cat /srv/link-lab/data.txt
cat /srv/link-lab/hard-link
cat /srv/link-lab/soft-link

# Remove the "original" filename
sudo rm /srv/link-lab/data.txt

# After delete
ls -li /srv/link-lab/

echo "=== try the hard link (should WORK) ==="
cat /srv/link-lab/hard-link            # works
stat -c 'links=%h' /srv/link-lab/hard-link

echo "=== try the soft link (should DANGLE) ==="
ls -l /srv/link-lab/soft-link          # ls shows it but in red (dangling)
cat /srv/link-lab/soft-link 2>&1 || echo "(read failed — symlink dangles)"
test -e /srv/link-lab/soft-link && echo "target exists" || echo "TARGET MISSING (symlink dangles)"
test -L /srv/link-lab/soft-link && echo "still a symlink"
readlink /srv/link-lab/soft-link        # still returns the (now-missing) target string

# Repair: restore via hard link
sudo ln /srv/link-lab/hard-link /srv/link-lab/data.txt
ls -li /srv/link-lab/

# Capture
{
  echo "=== after rm of data.txt ===";   ls -li /srv/link-lab/
  echo "=== hard-link cat ==="; cat /srv/link-lab/hard-link
  echo "=== soft-link cat ==="; cat /srv/link-lab/soft-link 2>&1 || echo "(dangling)"
  echo "=== test -e on dangling ==="
  test -e /srv/link-lab/soft-link && echo "exists" || echo "MISSING"
  test -L /srv/link-lab/soft-link && echo "is symlink"
  echo "=== repaired via hard link ==="
  sudo ln /srv/link-lab/hard-link /srv/link-lab/data.txt 2>/dev/null
  ls -li /srv/link-lab/
} 2>&1 | sudo tee /root/rhcsa_journal/lab09/task3/transcript.txt
```

### Human-Readable Breakdown

When you `rm /srv/link-lab/data.txt`, the kernel:

1. Decrements the link count on inode 12345 (the underlying data)
2. Frees the data ONLY when the count hits 0

Since `hard-link` and `hard-link-2` still reference inode 12345, the count drops to 2 (or 1 if only one hard link remained) — NOT to 0. The data is intact. You can keep reading it through the other names.

The **symlink** is independent. It still exists as its own inode (`12346`). Its content is the path string `/srv/link-lab/data.txt`. When you try to read the symlink, the kernel looks up that path... and finds `ENOENT`. The symlink itself is fine; its target is gone. `ls -l` still shows the link (often in red). `test -L` returns true (it IS a symlink). `test -e` returns false (the *target* doesn't exist). That's the difference between "is this a symlink?" and "is its target reachable?"

### Reading It Left to Right

`rm /srv/link-lab/data.txt`

- `rm` — remove
- decrements link count on the inode; frees data when count = 0

`test -L PATH` and `test -e PATH`

- `test` — condition test
- `-L` — is PATH a symlink? (does NOT follow)
- `-e` — does the file PATH refers to exist? (FOLLOWS symlinks)

### The Story

A grader's nasty question: "the file `/data/config.yml` was deleted; symlink `/etc/myservice/config.yml -> /data/config.yml` now dangles. Recover the file." If you had a hard link to `/data/config.yml` elsewhere (say in `/backup/`), you could restore by `ln /backup/config.yml /data/config.yml` — the data was never freed, the link count never hit 0. That's the operational value of hard links: redundant names protect against accidental `rm` of a single name.

### Expected Output

```
$ sudo rm /srv/link-lab/data.txt
$ ls -li /srv/link-lab/
total 8
12345 -rw-r--r--. 2 root root 28 May 27 15:05 hard-link
12345 -rw-r--r--. 2 root root 28 May 27 15:05 hard-link-2
12346 lrwxrwxrwx. 1 root root 22 May 27 15:02 soft-link -> /srv/link-lab/data.txt
                                                                                  ^
                                                                                  (red in terminal: dangling)

$ cat /srv/link-lab/hard-link
original content
added line

$ cat /srv/link-lab/soft-link
cat: /srv/link-lab/soft-link: No such file or directory

$ test -e /srv/link-lab/soft-link && echo "exists" || echo "MISSING"
MISSING
```

### Switches Table

| Switch | Meaning | Why it matters |
|---|---|---|
| `rm FILE` | Remove (decrement link count) | Frees data when count hits 0 |
| `test -L PATH` | Is PATH a symlink? | Does NOT follow |
| `test -e PATH` | Does PATH's target exist? | FOLLOWS symlinks |
| `test -f PATH` | Is PATH a regular file? | Follows symlinks; false for dangling |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| Hard link delete | Decrements link count; data freed only when count = 0 |
| Symlink dangle | `ls -l` still shows it; reading errors with ENOENT |
| `test -L` | Is symlink (no follow) |
| `test -e` | Target exists (follow) |
| Recovery | Restore via remaining hard link with `ln` |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| **T19** | `test -L symlink` returns true even when dangling; script proceeds; later `cat` fails | Use `test -e` to check the data, `test -L` to check link-ness |
| Symlink rot | Service starts before its symlink target file exists | Use `test -e` in scripts; treat dangling as a hard failure |

### 🔁 Persistence Check

```bash
test -e /srv/link-lab/hard-link && echo "hard-link reachable"
test -e /srv/link-lab/soft-link && echo "soft-link target reachable" || echo "soft-link DANGLES (expected)"
test -L /srv/link-lab/soft-link && echo "soft-link still a symlink"
[ "$(stat -c '%i' /srv/link-lab/hard-link)" = "$(stat -c '%i' /srv/link-lab/data.txt)" ] && echo "data.txt restored via hard link"
```

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab09/task3/done.txt > /dev/null <<EOF
lab=09 task=3
when=$(date -Is)
hard_link_survived=$(test -e /srv/link-lab/hard-link && echo yes || echo no)
soft_link_dangled=$(test ! -e /srv/link-lab/soft-link -a -L /srv/link-lab/soft-link && echo yes || echo no)
recovered_via_hard_link=$(test -e /srv/link-lab/data.txt && echo yes || echo no)
EOF
cat /root/rhcsa_journal/lab09/task3/done.txt
```

### 🧹 Cleanup

Leave the lab; Task 4 makes new links via Ansible.

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `hard-link` content also gone after `rm data.txt` | Link count must have hit 0 — confirm with `stat -c '%h'` BEFORE rm |
| `ls -l` doesn't show dangling symlinks in red | `--color=auto` may be disabled; `ls -l --color=always` to force |

> **STOP — confirm `hard_link_survived=yes` and `soft_link_dangled=yes` in done.txt before Task 4.**

---

## Task 4 — Ansible: `state=link` and `state=hard` via `ansible.builtin.file`

**Practice directory this task:** `/srv/link-lab`

### 🔁 Warm-Up — Commands from Previous Labs

```bash
sudo mkdir -p /root/rhcsa_journal/lab09/task4/playbooks
date -Is | sudo tee /root/rhcsa_journal/lab09/task4/start.txt
ansible --version | head -1 | sudo tee -a /root/rhcsa_journal/lab09/task4/start.txt
echo "exit was: $?"
```

If `ansible --version` fails — **Lab 00**.

### Purpose

Replicate Task 1 + Task 2 with `ansible.builtin.file`. Use `state: link` for symlinks (with `src:` = target), `state: hard` for hard links. Prove idempotence on re-run.

### Main Command Block

Ensure we have an origin file (Task 3 may have left `data.txt` restored via hard link; if not, recreate):

```bash
test -e /srv/link-lab/data.txt || (echo "ansible origin" | sudo tee /srv/link-lab/data.txt)
```

Write the playbook:

```bash
sudo tee /root/rhcsa_journal/lab09/task4/playbooks/links.yml > /dev/null <<'EOF'
---
- name: Lab 09 Task 4 — create symlink and hard link via ansible.builtin.file
  hosts: localhost
  become: true
  gather_facts: false

  vars:
    origin: /srv/link-lab/data.txt
    soft: /srv/link-lab/ansible-soft
    hard: /srv/link-lab/ansible-hard

  tasks:
    - name: Ensure origin file exists (idempotent guard)
      ansible.builtin.copy:
        content: "ansible origin\n"
        dest: "{{ origin }}"
        owner: root
        group: root
        mode: '0644'
        force: false

    - name: Create soft (symbolic) link
      ansible.builtin.file:
        src: "{{ origin }}"
        dest: "{{ soft }}"
        state: link
        force: true
      register: soft_result

    - name: Create hard link
      ansible.builtin.file:
        src: "{{ origin }}"
        dest: "{{ hard }}"
        state: hard
        force: true
      register: hard_result

    - name: Show results
      ansible.builtin.debug:
        msg:
          - "soft changed: {{ soft_result.changed }}"
          - "hard changed: {{ hard_result.changed }}"
EOF
```

Check-mode first:

```bash
ansible-playbook --check --diff /root/rhcsa_journal/lab09/task4/playbooks/links.yml \
  2>&1 | sudo tee /root/rhcsa_journal/lab09/task4/check.log
```

Apply:

```bash
ansible-playbook /root/rhcsa_journal/lab09/task4/playbooks/links.yml \
  2>&1 | sudo tee /root/rhcsa_journal/lab09/task4/apply.log
```

Idempotence proof:

```bash
ansible-playbook /root/rhcsa_journal/lab09/task4/playbooks/links.yml \
  2>&1 | sudo tee /root/rhcsa_journal/lab09/task4/rerun.log
grep '^localhost' /root/rhcsa_journal/lab09/task4/rerun.log
```

### Human-Readable Breakdown

`ansible.builtin.file` is the same module we used in Lab 07 — but now with `state: link` and `state: hard`. The arguments:

| Argument | For symlink | For hard link |
|---|---|---|
| `src:` | Target path the link points at | Existing file to hard-link |
| `dest:` | The link name | The new hard-link name |
| `state: link` | Symlink | — |
| `state: hard` | — | Hard link |
| `force: true` | Replace dest if it exists (file, dir, or other link) | Same |

`force: true` is what makes the playbook idempotent: without it, if `dest` already exists as something else, the task fails. With it, the module replaces. On the second run, the link already exists with the correct `src:` — module detects this and returns `changed=False`.

`state: hard` requires `src:` to exist; if it doesn't, the module errors. That's why the first task in the play uses `force: false` on the origin file — to ensure it exists without overwriting if it already does.

### Reading It Left to Right

```yaml
ansible.builtin.file:
  src: /srv/link-lab/data.txt
  dest: /srv/link-lab/ansible-soft
  state: link
  force: true
```

- `src:` — target (what the link points at)
- `dest:` — link name (the file being created)
- `state: link` — symbolic link
- `force: true` — replace if dest already exists

```yaml
ansible.builtin.file:
  src: /srv/link-lab/data.txt
  dest: /srv/link-lab/ansible-hard
  state: hard
  force: true
```

- `state: hard` — hard link
- Otherwise identical syntax

### The Story

A grader: "Create `/etc/myservice/config -> /opt/myservice/etc/config` as a symlink, owned by root, idempotent." Ansible answer is exactly the playbook above (paths swapped). Second run = `changed=0`. Real-world Ansible roles use `state: link` constantly — for systemd target/wants links, alternatives, and config drop-ins.

### Expected Output

First apply:

```
TASK [Ensure origin file exists] ***
ok: [localhost]

TASK [Create soft (symbolic) link] ***
changed: [localhost]

TASK [Create hard link] ***
changed: [localhost]

PLAY RECAP ***
localhost : ok=4 changed=2 unreachable=0 failed=0
```

Idempotence rerun:

```
TASK [Create soft (symbolic) link] ***
ok: [localhost]                    <-- NOT changed; symlink already points at the right src

TASK [Create hard link] ***
ok: [localhost]                    <-- NOT changed; hard link already exists

PLAY RECAP ***
localhost : ok=4 changed=0 unreachable=0 failed=0
```

### Switches Table

| Switch / Key | Meaning | Why it matters |
|---|---|---|
| `state: link` | Symbolic link | Equivalent to `ln -s` |
| `state: hard` | Hard link | Equivalent to `ln` |
| `force: true` | Replace dest if it exists | Idempotence helper |
| `src:` | Target path | Required for both link states |
| `dest:` | Link name | Required |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| `ansible.builtin.file: state=link` | RHCE answer for `ln -s` |
| `ansible.builtin.file: state=hard` | RHCE answer for `ln` (no `-s`) |
| `force: true` | Replace existing dest — enables idempotence |
| Idempotence | Module checks current state of dest; only changes if mismatched |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| **Wrapping `command: ln -s` instead of using `ansible.builtin.file: state=link`** | RHCE cardinal sin | Use the module |
| Forgetting `force: true` | Existing dest causes task failure | Always `force: true` for re-applicable link tasks |
| `state: hard` to non-existent src | Module errors | Ensure src exists first (use a dependent task) |

### 🔁 Persistence Check

```bash
test -L /srv/link-lab/ansible-soft && echo "ansible-soft is symlink"
[ "$(readlink /srv/link-lab/ansible-soft)" = "/srv/link-lab/data.txt" ] && echo "symlink target correct"
[ "$(stat -c '%i' /srv/link-lab/ansible-hard)" = "$(stat -c '%i' /srv/link-lab/data.txt)" ] && echo "hard link same inode"
grep -c 'changed=0' /root/rhcsa_journal/lab09/task4/rerun.log
```

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab09/task4/done.txt > /dev/null <<EOF
lab=09 task=4
when=$(date -Is)
playbook=/root/rhcsa_journal/lab09/task4/playbooks/links.yml
soft_target=$(readlink /srv/link-lab/ansible-soft)
hard_inode_match=$([ "$(stat -c '%i' /srv/link-lab/ansible-hard)" = "$(stat -c '%i' /srv/link-lab/data.txt)" ] && echo yes || echo no)
idempotent_rerun_changed_0=$(grep -c 'changed=0' /root/rhcsa_journal/lab09/task4/rerun.log)
EOF
cat /root/rhcsa_journal/lab09/task4/done.txt
```

### 🧹 Cleanup

Leave links; Task 5 verifies them.

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `src 'X' is not readable` | Origin file doesn't exist; check `ls -l` of the src path |
| Second run shows `changed=1` | Dest exists but mismatched — re-check `readlink` and `stat -c %i` |

> **STOP — confirm `hard_inode_match=yes` in done.txt before Task 5.**

---

## Task 5 — RHCSA Verification Capstone: Prove the Links Behave Correctly

**Practice directory this task:** `/srv/link-lab`

### 🔁 Warm-Up — Commands from Previous Labs

```bash
sudo mkdir -p /root/rhcsa_journal/lab09/task5
date -Is | sudo tee /root/rhcsa_journal/lab09/task5/start.txt
echo "exit was: $?"
```

### Purpose

Use **only** RHCSA inspection commands to prove:

1. `ansible-soft` is a symlink whose target is `/srv/link-lab/data.txt`
2. `ansible-hard` shares an inode with `/srv/link-lab/data.txt`
3. `find -inum` shows both `data.txt` and `ansible-hard` (and any other hard links)
4. Reading either link yields identical content

### Main Command Block

Three+ RHCSA inspection commands:

```bash
# 1) Symlink inspection
ls -li /srv/link-lab/ansible-soft
readlink /srv/link-lab/ansible-soft
test -L /srv/link-lab/ansible-soft && echo "is symlink"
test -e /srv/link-lab/ansible-soft && echo "target reachable"

# 2) Hard-link inspection
ls -li /srv/link-lab/ansible-hard /srv/link-lab/data.txt
stat -c 'inode=%i links=%h' /srv/link-lab/ansible-hard

# 3) find -inum cross-check
inode=$(stat -c '%i' /srv/link-lab/data.txt)
sudo find /srv/link-lab -inum "$inode"

# 4) Content compare
diff <(cat /srv/link-lab/ansible-soft) <(cat /srv/link-lab/data.txt) && echo "SOFT_CONTENT_MATCH"
diff <(cat /srv/link-lab/ansible-hard) <(cat /srv/link-lab/data.txt) && echo "HARD_CONTENT_MATCH"

# Capture
{
  echo "=== symlink ==="
  ls -li /srv/link-lab/ansible-soft
  readlink /srv/link-lab/ansible-soft
  echo "=== hard link inode match ==="
  ls -li /srv/link-lab/ansible-hard /srv/link-lab/data.txt
  echo "=== find -inum ==="
  sudo find /srv/link-lab -inum "$(stat -c '%i' /srv/link-lab/data.txt)"
  echo "=== content compare ==="
  diff <(cat /srv/link-lab/ansible-soft) <(cat /srv/link-lab/data.txt) && echo "SOFT_CONTENT_MATCH"
  diff <(cat /srv/link-lab/ansible-hard) <(cat /srv/link-lab/data.txt) && echo "HARD_CONTENT_MATCH"
} 2>&1 | sudo tee /root/rhcsa_journal/lab09/task5/evidence.txt
```

### Human-Readable Breakdown

The audit:

- `ls -li` — show inode + type-bit + link count + symlink arrow
- `readlink` — show literal symlink target
- `test -L` and `test -e` — symlink-ness and reachability (catches T19)
- `stat -c '%i'` — inode number for compare
- `find -inum N` — find all hard links to inode N

Together they prove: "the symlink points at the right path; the hard link shares the right inode; the link count agrees; content is identical."

### Reading It Left to Right

`diff <(cat A) <(cat B)`

- `diff` — diff
- `<(cmd)` — process substitution; runs `cmd` and gives a fake filename
- `cat A` / `cat B` — both files
- Result: diff is silent (clean exit) when the two files have identical contents

`find /srv/link-lab -inum "$inode"`

- `find` — search
- `-inum N` — match by inode number; finds all hard links to that inode

### The Story

You hand a grader `evidence.txt` and it reads: "`ansible-soft` is a symlink to `data.txt` (readlink), `ansible-hard` shares the same inode as `data.txt` (find -inum), and reading any of them yields identical content (diff)." That's the auditor's full link report.

### Expected Output

```
=== symlink ===
12350 lrwxrwxrwx. 1 root root 22 May 27 15:08 /srv/link-lab/ansible-soft -> /srv/link-lab/data.txt
/srv/link-lab/data.txt

=== hard link inode match ===
12345 -rw-r--r--. 3 root root 28 May 27 15:05 /srv/link-lab/ansible-hard
12345 -rw-r--r--. 3 root root 28 May 27 15:05 /srv/link-lab/data.txt

=== find -inum ===
/srv/link-lab/data.txt
/srv/link-lab/hard-link
/srv/link-lab/ansible-hard

=== content compare ===
SOFT_CONTENT_MATCH
HARD_CONTENT_MATCH
```

### Switches Table

| Switch | Meaning | Why it matters |
|---|---|---|
| `ls -li` | Long listing with inode column | Side-by-side inode compare |
| `readlink PATH` | Print symlink target | Symlink content |
| `test -L` | Is symlink (no follow) | Symlink-ness |
| `test -e` | Target reachable (follow) | Catches T19 dangling |
| `find -inum N` | All paths with inode N | Find all hard links |
| `diff <(cat A) <(cat B)` | Compare two file contents | Quick content check |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| Audit triangle | `ls -li` + `readlink` + `find -inum` |
| Reboot reasoning | `/srv/` persists; inode numbers may change on relabel but link relationships do not |
| Auditor reflex | ≥3 RHCSA inspection commands; check both symlinks AND hard links |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| **Trusting `ansible-playbook`'s changed=1 without inspecting state** | Whole point of the verification capstone | Verify with `ls -li`, `readlink`, `find -inum` |
| **T19 again** | `test -L` returns true but data unreachable | Always pair `-L` with `-e` |

### 🔁 Persistence Check (Reboot Reasoning)

```bash
echo "REBOOT REASONING:"                                                                | sudo tee /root/rhcsa_journal/lab09/task5/reboot.txt
echo "1. /srv/ persists; inode numbers persist; link relationships persist."           | sudo tee -a /root/rhcsa_journal/lab09/task5/reboot.txt
echo "2. Symlink content (the target PATH string) is stored in the symlink inode."     | sudo tee -a /root/rhcsa_journal/lab09/task5/reboot.txt
echo "3. Hard links survive because they ARE the file — same inode, same data."        | sudo tee -a /root/rhcsa_journal/lab09/task5/reboot.txt
test -L /srv/link-lab/ansible-soft && echo "soft link persists"                        | sudo tee -a /root/rhcsa_journal/lab09/task5/reboot.txt
test -e /srv/link-lab/ansible-hard && echo "hard link persists"                        | sudo tee -a /root/rhcsa_journal/lab09/task5/reboot.txt
test -f /root/rhcsa_journal/lab09/task4/playbooks/links.yml && echo "playbook persists" | sudo tee -a /root/rhcsa_journal/lab09/task5/reboot.txt
```

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab09/task5/done.txt > /dev/null <<EOF
lab=09 task=5
when=$(date -Is)
evidence=/root/rhcsa_journal/lab09/task5/evidence.txt
reboot=/root/rhcsa_journal/lab09/task5/reboot.txt
soft_match=$(grep -c '^SOFT_CONTENT_MATCH$' /root/rhcsa_journal/lab09/task5/evidence.txt)
hard_match=$(grep -c '^HARD_CONTENT_MATCH$' /root/rhcsa_journal/lab09/task5/evidence.txt)
status=lab09-complete
EOF
cat /root/rhcsa_journal/lab09/task5/done.txt
```

### 🧹 Cleanup (No Regression)

```bash
# Remove the entire sandbox
sudo rm -rf /srv/link-lab
ls -d /srv/link-lab 2>&1 | grep -q "No such" && echo "sandbox cleaned"

# Journal stays
ls /root/rhcsa_journal/lab09/
```

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `SOFT_CONTENT_MATCH` missing | Symlink points at wrong path — re-run Task 4 |
| `HARD_CONTENT_MATCH` missing | Hard link not pointing at the same inode — re-run Task 4 with correct `src:` |
| `find -inum` returns only the origin | Hard links not created; re-run Task 4 |

> **STOP — record `status=lab09-complete` in done.txt. Lab 09 is finished.**

---

## ✅ Lab 09 Complete When

```bash
ls /root/rhcsa_journal/lab09/task{1,2,3,4,5}/done.txt
grep -l 'lab09-complete' /root/rhcsa_journal/lab09/task5/done.txt
test -f /root/rhcsa_journal/lab09/task4/playbooks/links.yml
grep -cE '(SOFT|HARD)_CONTENT_MATCH' /root/rhcsa_journal/lab09/task5/evidence.txt
```

All four must succeed. You can build, inspect, break, and replicate both link kinds in shell and Ansible.
