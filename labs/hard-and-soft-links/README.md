# Lab 09: Hard and Soft Links — `ln`, `ln -s`, `readlink`, `find -inum`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Career arcs covered:** RHCSA EX200 (filesystem hierarchy, systemd `mask`, /etc symlinks), RHCE EX294 (Ansible `file: state=link`), CKA (volume symlinks, `/var/log/containers/`), RHCA — RH342 (forensic inode tracking)
- **Prerequisite:** Lab 08 (`cp`, `cp -a`, `cp --preserve=context`)
- **Time Estimate:** 35–50 minutes
- **Tasks:** 3 (ADHD spec)
- **Practice Directory (lab-wide rotation #09):** `/root`
- **Sandbox:** `/tmp/link-lab`
- **Traps rehearsed this lab:** **T17** (mask vs disable confusion — masked = symlink to `/dev/null`) · **T16** (Editing unit file without daemon-reload)

> **This lab's practice directory is: `/root`** — every task references it in at least two commands.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T17 T16"
echo "📁  PRACTICE DIR: /root"
echo ""
echo "💡 /root contents (we read; we add lab-only files):"
ls -la /root 2>/dev/null | head -n 10
```

> **STOP — paste header output before running setup.**

---

## 🎯 Objective

Master both kinds of links: **hard links** (multiple names → same inode) and **soft/symbolic links** (a file containing a path). By the end you will know exactly when each one applies, how `rm` behaves on each, and you will understand the systemd `mask` trap (T17) because `systemctl mask SVC` is literally `ln -s /dev/null /etc/systemd/system/SVC`.

---

## 🧠 Concept: Two Very Different Things, Both Called "Link"

| Property | Hard link | Soft link (symlink) |
|---|---|---|
| Created with | `ln SRC LINK` | `ln -s SRC LINK` |
| Stores | A directory entry pointing to the **same inode** | A small file containing **the path string** |
| Inode | Same as source (verify with `ls -li`) | Different — its own inode |
| Across filesystems? | **No** (inodes are per-FS) | **Yes** |
| To directories? | **No** (would create cycles; only root can override and you should not) | **Yes** |
| Survives `rm` of source? | **Yes** — both names still point to the inode | **No** — symlink becomes "dangling" |
| Link count (`ls -l` column 2) | Increments | Source unchanged |
| Permissions on the link | Ignored (uses inode's mode) | `lrwxrwxrwx` always (perms come from target) |
| Identified in `ls -l` by | Nothing visible — looks like a regular file | `l` type char + `name -> target` |

```
ln    /root/orig   /root/hard-copy        # hard link — second name for same inode
ln -s /root/orig   /root/soft-copy        # soft link — file containing the path "/root/orig"

rm /root/orig
# hard-copy: still has the data (link count was 2, now 1)
# soft-copy: DANGLING — readlink works, cat does not
```

### Why this matters — the systemd `mask` insight

```
$ systemctl mask httpd
Created symlink /etc/systemd/system/httpd.service → /dev/null

$ ls -l /etc/systemd/system/httpd.service
lrwxrwxrwx. 1 root root 9 May 27 14:55 httpd.service -> /dev/null

$ systemctl unmask httpd
Removed /etc/systemd/system/httpd.service
```

`systemctl mask` is **literally a symlink to /dev/null**. systemd treats "service file is a symlink to /dev/null" as "this service is forbidden — refuse to start it even manually." Trap **T17**: people confuse `disable` (won't auto-start on boot, but `systemctl start` still works) with `mask` (cannot start at all). Knowing the symlink mechanism makes T17 unforgettable.

---

## 🚦 Lab-Wide Setup — Run This BEFORE Task 1

```bash
sudo -i
mkdir -p /tmp/link-lab
cd /tmp/link-lab

cat > /tmp/link-lab/THIS_DIRECTORY.txt <<'EOF'
/root — Home directory for the root user

/root is the root user's home directory. It is NOT /home/root because /home
can be mounted from another disk or NFS, and root must be able to log in
even when /home is unavailable.

Why it exists: keeping root's home on the root partition guarantees that
single-user mode, rd.break recovery, and emergency boots all give root a
working home directory.

What lives inside it: root's dotfiles (.bashrc, .bash_history, .ssh/),
admin scripts, and — by RHCSA convention — task output files like
/root/output.txt that grading checks. This lab uses /root/link-demo/
for that exact pattern.

Why RHCSA cares: nearly every capstone task writes a final file under
/root. Symlinks in /root/.ssh/ are a common pattern (config -> shared
config). systemctl mask creates symlinks under /etc/systemd/system/
which is conceptually adjacent to "system root configuration."
EOF

cat /tmp/link-lab/THIS_DIRECTORY.txt

mkdir -p /root/link-demo
echo "version 1.0 — original content" > /root/link-demo/original.txt

ls -ld /root /root/link-demo
ls -li /root/link-demo/original.txt
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

# The 3 Tasks

---

## Task 1 — Hard Links: Multiple Names, One Inode

### a) Directory Context

**Practice directory this task:** `/root/link-demo` (sandbox for hard link experiments).
We will create hard links, prove they share an inode, watch the link count change, and prove a hard link survives `rm` of the original.

### b) 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/link-lab
date -Is | tee task01-warmup.log
ls -li /root/link-demo/ 2>&1 | tee -a task01-warmup.log
stat --format='Inode:%i Links:%h Size:%s' /root/link-demo/original.txt | tee -a task01-warmup.log
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Create hard links, verify they share an inode, watch the link count rise and fall, and demonstrate that removing the "original" leaves the data intact via any remaining hard link.

### d) Main Command Block

```bash
cd /root/link-demo

ln original.txt hard1.txt
ln original.txt hard2.txt

echo "=== After 2 hard links: ==="
ls -li original.txt hard1.txt hard2.txt
stat --format='Name:%n Inode:%i Links:%h' original.txt hard1.txt hard2.txt

echo ""
echo "=== Modify hard1 — content visible through ALL names ==="
echo "version 2.0 — written through hard1" >> hard1.txt
cat original.txt
cat hard2.txt

echo ""
echo "=== Find all paths sharing this inode ==="
INODE=$(stat --format='%i' original.txt)
echo "Searching for inode $INODE under /root..."
find /root -inum "$INODE" 2>/dev/null

echo ""
echo "=== Remove the 'original' — data survives ==="
rm -v original.txt
ls -li hard1.txt hard2.txt
cat hard1.txt
stat --format='Name:%n Inode:%i Links:%h' hard1.txt

echo ""
echo "=== Cross-FS hard link attempt (should fail) ==="
ln hard1.txt /tmp/link-lab/hardlink-attempt.txt 2>&1 || echo "Expected fail — cross-FS hard link is impossible"
# /root and /tmp may or may not be on the same FS; if on same FS this succeeds, if separate it fails
ls -li /tmp/link-lab/hardlink-attempt.txt 2>/dev/null
```

### e) Human-Readable Breakdown

- `ln SRC LINK` (no `-s`) — create a hard link; SRC and LINK now share the same inode.
- `ls -li` — list with **inode number** in the first column.
- `stat --format='%i %h'` — print inode (%i) and hard link count (%h).
- `find /root -inum N` — find every path on `/root`'s filesystem that points to inode N. This is how forensic admins find every name for a file.
- `rm original.txt` — removes the directory entry. The inode itself only goes away when the link count hits 0.
- Cross-FS attempt fails because inodes are per-filesystem. (On many RHEL setups `/root` and `/tmp` are on the same FS, so this may actually succeed — check `df /root /tmp/link-lab`.)

### f) Reading It Left to Right

`find /root -inum "$INODE" 2>/dev/null`

1. `find` — the finder.
2. `/root` — start here.
3. `-inum N` — match inode number N (set above via `stat --format='%i'`).
4. `2>/dev/null` — suppress permission-denied noise from subdirectories.

The interesting property: this only searches `/root`'s filesystem, because inodes are scoped to a filesystem. If `/var` or `/home` were on a separate FS, you'd need to re-run `find` from there.

### g) The Story

Hard links are the original Unix file abstraction. A "file" is really an inode (data + metadata). The names you see in directories are just labels pointing at inodes. The link count tells you how many labels exist. `rm` removes one label and decrements the count; when the count hits zero, the kernel finally frees the data.

This is why `rm` is so cheap and why deleted-but-still-open files keep their disk space until every file descriptor closes. It's also why `tar` and `rsync` worry about hard links: if you have two names for the same inode, a naive copy stores the data twice unless the tool detects the hard link.

### h) Expected Output

```text
=== After 2 hard links: ===
12345678 -rw-r--r--. 3 root root 31 May 27 15:00 original.txt
12345678 -rw-r--r--. 3 root root 31 May 27 15:00 hard1.txt
12345678 -rw-r--r--. 3 root root 31 May 27 15:00 hard2.txt
Name:original.txt Inode:12345678 Links:3
Name:hard1.txt    Inode:12345678 Links:3
Name:hard2.txt    Inode:12345678 Links:3

=== Modify hard1 — content visible through ALL names ===
version 1.0 — original content
version 2.0 — written through hard1
version 1.0 — original content
version 2.0 — written through hard1

=== Find all paths sharing this inode ===
Searching for inode 12345678 under /root...
/root/link-demo/original.txt
/root/link-demo/hard1.txt
/root/link-demo/hard2.txt

=== Remove the 'original' — data survives ===
removed 'original.txt'
12345678 -rw-r--r--. 2 root root 75 May 27 15:00 hard1.txt
12345678 -rw-r--r--. 2 root root 75 May 27 15:00 hard2.txt
version 1.0 — original content
version 2.0 — written through hard1
Name:hard1.txt Inode:12345678 Links:2

=== Cross-FS hard link attempt ===
(either succeeds if /root and /tmp are same FS, OR:)
ln: failed to create hard link '/tmp/link-lab/hardlink-attempt.txt' => 'hard1.txt': Invalid cross-device link
Expected fail — cross-FS hard link is impossible
```

### i) Switches Table

| Token | Meaning |
|---|---|
| `ln SRC LINK` | Create hard link |
| `ln -v` | Verbose |
| `ls -li` | Long listing with inode column |
| `stat --format='%i'` | Inode number |
| `stat --format='%h'` | Hard link count |
| `find -inum N` | Match inode N |
| `rm -v FILE` | Verbose remove |
| `df PATH` | Show filesystem mounted at PATH (to check if two paths share an FS) |

### j) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | Hard link | Second directory entry pointing to same inode |
|   | Inode | The actual file (data + metadata) |
|   | Link count | How many names point to this inode |
|   | `ls -li` | Show inodes |
|   | `find -inum` | Find every name for an inode |
|   | `rm` semantics | Decrement link count; free inode when count = 0 |
|   | Cross-FS limit | Hard links cannot cross filesystems |
|   | No-dir rule | Hard links to directories are forbidden (no cycles) |
| 🪤 **Trap Risk (T16)** | Editing unit file without daemon-reload | If you ever `ln` a unit file into `/etc/systemd/system/`, `systemctl` won't see it until `systemctl daemon-reload`. The link is on disk but systemd's in-memory state is stale |

### k) 🧹 Cleanup

```bash
LAB=lab09
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
TOPIC:    Hard links — shared inode, link count, find -inum, rm survival
COMMANDS: ln, ls -li, stat --format='%i %h', find -inum, rm -v
TRAPS:    T16 (daemon-reload reminder)
MISSED:   —
NEXT:     task2 — soft links (ln -s), dangling links, readlink
EOF
echo "Journal written: $(ls -la $JDIR)"

cd /root/link-demo
rm -v hard1.txt hard2.txt 2>/dev/null
rm -f /tmp/link-lab/hardlink-attempt.txt
rm -f /tmp/link-lab/task01-warmup.log
ls /root/link-demo
echo "exit was: $?"
```

### l) Troubleshoot Table

| Symptom | Fix |
|---|---|
| `ln: hard link not allowed for directory` | Expected — use `ln -s` for dirs |
| `ln: Invalid cross-device link` | `/root` and `/tmp` are different FS; use `ln -s` or `cp` instead |
| Inodes differ for source and link | You used `ln -s` (soft link) — drop the `-s` for hard |
| Link count is 1 after `ln` | The link command failed silently; check with `ls -li` |

### m) STOP

> **STOP — paste output before Task 2.**

### n) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| `/root/link-demo/original.txt` re-created for Task 2 | `ls /root/link-demo` | (Task 2 needs a source — we will recreate it) |
| Journal task1 | `cat /root/rhcsa_journal/lab09/task1/done.txt` | Reboot-proof |
| No leftover hard links | `find /root -inum N` (the old inode is gone or pointing to nothing) | Confirms cleanup |

---

## Task 2 — Soft Links: Path Strings, Dangling Links, `readlink`

### a) Directory Context

**Practice directory this task:** `/root/link-demo` (sandbox) and `/root/.ssh` style scenarios.
Soft links can cross filesystems, point to directories, and **break** when the target disappears.

### b) 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/link-lab
date -Is | tee task02-warmup.log
echo "version 2.1 — new original for soft link drill" > /root/link-demo/original.txt
ls -li /root/link-demo/original.txt | tee -a task02-warmup.log
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Create symbolic links, read them with `readlink`, watch one **dangle** when its target is removed, and observe how cross-filesystem and to-directory cases work (both forbidden for hard links).

### d) Main Command Block

```bash
cd /root/link-demo

ln -s original.txt soft-relative.txt
ln -s /root/link-demo/original.txt soft-absolute.txt
ln -s /root/link-demo dir-link

echo "=== Soft links — note size (= length of target path) and 'l' type ==="
ls -l soft-relative.txt soft-absolute.txt dir-link

echo ""
echo "=== readlink — what does the symlink CONTAIN? ==="
readlink soft-relative.txt
readlink soft-absolute.txt
readlink dir-link
readlink -f soft-relative.txt   # resolved canonical path
readlink -f dir-link

echo ""
echo "=== Cross-FS soft link (always works) ==="
ln -s /root/link-demo/original.txt /tmp/link-lab/cross-fs.lnk
ls -l /tmp/link-lab/cross-fs.lnk
cat /tmp/link-lab/cross-fs.lnk

echo ""
echo "=== cat through the symlink ==="
cat soft-relative.txt
cat soft-absolute.txt
ls dir-link/

echo ""
echo "=== DANGLE the symlinks ==="
mv original.txt original.txt.moved
ls -l soft-relative.txt soft-absolute.txt
cat soft-relative.txt 2>&1 || echo "Dangling symlink — cat fails"
readlink soft-relative.txt    # still prints the (now-broken) target
readlink -f soft-relative.txt 2>/dev/null || echo "readlink -f fails: target missing"

echo ""
echo "=== Restore by recreating target ==="
mv original.txt.moved original.txt
cat soft-relative.txt
```

### e) Human-Readable Breakdown

- `ln -s SRC LINK` — create a symlink. The link is a tiny file that contains the string `SRC`.
- `ln -s original.txt soft-relative.txt` — the link contains the **relative** string `original.txt`. Resolves from the link's directory.
- `ln -s /root/link-demo/original.txt soft-absolute.txt` — the link contains the **absolute** path. Resolves from root.
- `ln -s /root/link-demo dir-link` — symlinks CAN point to directories.
- `readlink LINK` — show the path stored in the symlink (no resolution).
- `readlink -f LINK` — resolve to the canonical path on disk.
- `mv original.txt original.txt.moved` — moving the target makes both symlinks "dangle." `ls -l` may show them in red.
- Cross-FS: soft links work across filesystems because the link only stores a path string, not an inode reference.

### f) Reading It Left to Right

`ln -s /root/link-demo/original.txt soft-absolute.txt`

1. `ln` — link command.
2. `-s` — make it a soft/symbolic link (not hard).
3. `/root/link-demo/original.txt` — target path (stored as a literal string inside the link).
4. `soft-absolute.txt` — name of the new link.

The kernel never validates the target at creation. You can `ln -s /this/does/not/exist foo` and it works — the link points at a non-existent file from the start. Reading or writing through it fails.

### g) The Story

Soft links are the duct tape of Unix. Used for:

- **API compatibility**: `/usr/bin/python` → `python3.9` so scripts don't break across upgrades.
- **Versioning**: `/opt/app/current → /opt/app/v2.3.1`; atomically swap `current` to roll back.
- **Filesystem hierarchy**: on modern RHEL, `/bin → usr/bin`, `/lib → usr/lib`, etc., are all symlinks.
- **systemd masking** (T17): `/etc/systemd/system/httpd.service → /dev/null`.
- **systemd enable**: `/etc/systemd/system/multi-user.target.wants/sshd.service → /usr/lib/systemd/system/sshd.service` (this is literally what `systemctl enable` does).
- **Kubernetes**: `/var/log/containers/<pod>.log → /var/log/pods/<pod>/<container>.log`.

Dangling symlinks are not always bugs — sometimes they're placeholders for files that exist only on certain hosts (kickstart trick) or pointers to dynamic content.

### h) Expected Output

```text
=== Soft links ===
lrwxrwxrwx. 1 root root 12 May 27 15:10 soft-relative.txt -> original.txt
lrwxrwxrwx. 1 root root 30 May 27 15:10 soft-absolute.txt -> /root/link-demo/original.txt
lrwxrwxrwx. 1 root root 15 May 27 15:10 dir-link -> /root/link-demo

=== readlink ===
original.txt
/root/link-demo/original.txt
/root/link-demo
/root/link-demo/original.txt
/root/link-demo

=== Cross-FS ===
lrwxrwxrwx. 1 root root 30 May 27 15:10 /tmp/link-lab/cross-fs.lnk -> /root/link-demo/original.txt
version 2.1 — new original for soft link drill

=== cat through symlink ===
version 2.1 — new original for soft link drill
version 2.1 — new original for soft link drill
original.txt
hard1.txt        (if hard links from Task 1 are still around)
...

=== DANGLE ===
lrwxrwxrwx. 1 root root 12 May 27 15:10 soft-relative.txt -> original.txt
lrwxrwxrwx. 1 root root 30 May 27 15:10 soft-absolute.txt -> /root/link-demo/original.txt
cat: soft-relative.txt: No such file or directory
Dangling symlink — cat fails
original.txt
readlink -f fails: target missing

=== Restored ===
version 2.1 — new original for soft link drill
```

Notice: `ls -l` STILL shows the symlink itself when target is missing. `readlink` STILL prints the stored path. Only resolution-requiring operations (`cat`, `readlink -f`, `stat <link>`) fail.

### i) Switches Table

| Token | Meaning |
|---|---|
| `ln -s SRC LINK` | Create soft/symbolic link |
| `ln -sn SRC EXISTING_LINK` | Replace existing link without dereferencing |
| `ln -sf SRC LINK` | Force overwrite if LINK exists |
| `readlink LINK` | Print stored target string |
| `readlink -f LINK` | Print canonical (resolved) path |
| `realpath LINK` | Same as `readlink -f`, more strict |
| `ls -l` | Shows `l` type and `->` |
| `cat LINK` | Follows symlink to read target |

### j) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | Soft link | File containing a path string |
|   | Cross-FS works | Yes (unlike hard links) |
|   | To directories | Yes (unlike hard links) |
|   | Dangling link | Target moved or deleted — link still exists |
|   | `readlink` | Read stored path |
|   | `readlink -f` | Resolve to canonical path |
|   | `ln -sf` | Force overwrite |
|   | Relative vs absolute target | Both work; relative survives directory moves better |
| 🪤 **Trap Risk (T17)** | mask vs disable | Disabled = no auto-start, but `systemctl start` works. **Masked** = symlink to `/dev/null`, won't start AT ALL. Verify with `ls -l /etc/systemd/system/<svc>.service` — if it points to `/dev/null`, it's masked |

### k) 🧹 Cleanup

```bash
LAB=lab09
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
TOPIC:    Soft links — ln -s, cross-FS, dirs, dangling, readlink
COMMANDS: ln -s, ln -sf, readlink, readlink -f, realpath
TRAPS:    T17 (mask = symlink to /dev/null)
MISSED:   —
NEXT:     task3 — systemctl mask capstone + daemon-reload
EOF
echo "Journal written: $(ls -la $JDIR)"

cd /root/link-demo
rm -f soft-relative.txt soft-absolute.txt dir-link
rm -f /tmp/link-lab/cross-fs.lnk /tmp/link-lab/task02-warmup.log
echo "exit was: $?"
```

### l) Troubleshoot Table

| Symptom | Fix |
|---|---|
| `cat LINK` says `No such file` | Target is gone — `readlink LINK` to see what it expects |
| `ln -s` fails with "File exists" | Use `ln -sf` to overwrite |
| Symlink color is red in `ls` | Dangling — target missing or unreadable |
| `readlink -f` returns same path | LINK is not a symlink; check `ls -l` for `l` type char |

### m) STOP

> **STOP — paste output before Task 3.**

### n) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| Sandbox dir-link removed | `test -L /root/link-demo/dir-link \|\| echo CLEAN` | Confirms no stray symlinks under /root |
| `original.txt` survives | `cat /root/link-demo/original.txt` | Source for Task 3 |
| Journal task2 | `cat /root/rhcsa_journal/lab09/task2/done.txt` | Reboot-proof |

---

## Task 3 — Capstone: `systemctl mask` Is a Symlink (T17 + T16)

### a) Directory Context

**Practice directory this task:** `/etc/systemd/system/` (the canonical symlink directory) and `/root/link-demo` (where we keep our journal/evidence).
We will mask a harmless test service, prove it created a symlink to `/dev/null`, observe the daemon-reload requirement (T16), and unmask cleanly.

### b) 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/link-lab
date -Is | tee task03-warmup.log
ls -l /etc/systemd/system/ 2>&1 | head -n 10 | tee -a task03-warmup.log
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Connect everything: hard link concepts, symlink concepts, systemd's use of symlinks for `enable` and `mask`, and the `daemon-reload` requirement. Use a harmless test service (`crond` if present, or a dummy unit).

### d) Main Command Block

```bash
SVC="crond.service"
if ! systemctl list-unit-files 2>/dev/null | grep -q "^${SVC}"; then
  echo "crond not present — using systemd-tmpfiles-clean.service for the demo"
  SVC="systemd-tmpfiles-clean.service"
fi
echo "Test service: $SVC"

echo ""
echo "=== Initial state ==="
systemctl is-enabled "$SVC"
systemctl status "$SVC" --no-pager | head -n 5

echo ""
echo "=== systemctl enable creates a symlink in *.target.wants/ ==="
systemctl enable "$SVC" 2>&1 | head -n 5
find /etc/systemd/system -name "$SVC" -ls 2>/dev/null

echo ""
echo "=== systemctl mask creates a symlink to /dev/null ==="
systemctl mask "$SVC" 2>&1 | head -n 3
ls -l /etc/systemd/system/"$SVC"
readlink /etc/systemd/system/"$SVC"

echo ""
echo "=== Proof: it IS a symlink to /dev/null ==="
stat --format='Name:%n Type:%F Target:%N' /etc/systemd/system/"$SVC"

echo ""
echo "=== Try to start a masked service — fails ==="
systemctl start "$SVC" 2>&1 | head -n 3 || echo "Expected fail: masked"

echo ""
echo "=== Unmask: remove the /dev/null symlink ==="
systemctl unmask "$SVC" 2>&1 | head -n 3
ls -l /etc/systemd/system/"$SVC" 2>&1 || echo "Symlink removed"

echo ""
echo "=== Verify state is sane ==="
systemctl is-enabled "$SVC"

echo ""
echo "=== T16 demonstration: drop a custom unit, forget daemon-reload ==="
cat > /etc/systemd/system/lab09-test.service <<'EOF'
[Unit]
Description=Lab 09 test service (does nothing)

[Service]
Type=oneshot
ExecStart=/bin/true

[Install]
WantedBy=multi-user.target
EOF
echo ""
echo "Without daemon-reload — systemd does not see it yet:"
systemctl status lab09-test.service --no-pager 2>&1 | head -n 5

echo ""
echo "After daemon-reload:"
systemctl daemon-reload
systemctl status lab09-test.service --no-pager 2>&1 | head -n 5

echo ""
echo "Save evidence to /root/link-demo/:"
{
  echo "TEST SERVICE: $SVC"
  echo "Mask resolved: $(systemctl is-enabled $SVC 2>&1)"
  ls -l /etc/systemd/system/"$SVC" 2>&1 || echo "(symlink removed — unmasked)"
  echo ""
  echo "Custom unit:"
  ls -l /etc/systemd/system/lab09-test.service
} > /root/link-demo/task03-evidence.txt
cat /root/link-demo/task03-evidence.txt
```

### e) Human-Readable Breakdown

- Pick a safe test service (`crond` or `systemd-tmpfiles-clean`).
- `systemctl enable SVC` — creates a symlink in `multi-user.target.wants/`.
- `systemctl mask SVC` — creates a **second** symlink in `/etc/systemd/system/<svc>` pointing to `/dev/null`. systemd refuses to start anything pointed at `/dev/null`.
- `readlink` proves the target is `/dev/null`.
- `systemctl unmask SVC` — removes the `/dev/null` symlink.
- Drop a custom unit file. `systemctl status` reports it as "Unit not found" UNTIL `systemctl daemon-reload` (T16). After daemon-reload it shows the proper "loaded; inactive (dead)" state.
- Save evidence to `/root/link-demo/task03-evidence.txt` so the journal entry is reboot-proof.

### f) Reading It Left to Right

`find /etc/systemd/system -name "$SVC" -ls 2>/dev/null`

1. `find` — finder.
2. `/etc/systemd/system` — systemd's admin-managed unit dir.
3. `-name "$SVC"` — match the service file name.
4. `-ls` — print results in `ls -l`-style format including inode.
5. `2>/dev/null` — suppress noise.

You'll see one or more lines like:

```
12345  0 lrwxrwxrwx 1 root root 32 ... /etc/systemd/system/multi-user.target.wants/crond.service -> /usr/lib/systemd/system/crond.service
```

That arrow tells the whole story. `enable` = symlink. `mask` = symlink to `/dev/null`. systemd is built on symlinks.

### g) The Story

Every confusing systemd behavior makes sense once you understand it's symlinks underneath:

- "Why doesn't my service auto-start?" → No symlink in `*.target.wants/`. Fix: `systemctl enable`.
- "Why can't I start my service?" → Symlink to `/dev/null` in `/etc/systemd/system/`. Fix: `systemctl unmask`.
- "Why doesn't systemd see my new .service file?" → On-disk state changed; in-memory state did not. Fix: `systemctl daemon-reload` (**T16**).
- "Why is `disable` different from `mask`?" → `disable` removes the wants-symlink (auto-start gone). `mask` ADDS a /dev/null symlink (cannot start at all). **T17** in one sentence.

RHCSA grading: if a task says "Permanently prevent service X from starting," `systemctl mask` is the answer. `systemctl disable` is the wrong answer because someone could still run `systemctl start`.

### h) Expected Output

```text
Test service: crond.service

=== Initial state ===
enabled
● crond.service - Command Scheduler
   Loaded: loaded (/usr/lib/systemd/system/crond.service; enabled; vendor preset: enabled)
   Active: active (running) since ...

=== systemctl enable creates a symlink in *.target.wants/ ===
(no output if already enabled, or:)
Created symlink /etc/systemd/system/multi-user.target.wants/crond.service → /usr/lib/systemd/system/crond.service
   12345 0 lrwxrwxrwx ... /etc/systemd/system/multi-user.target.wants/crond.service -> /usr/lib/systemd/system/crond.service

=== systemctl mask creates a symlink to /dev/null ===
Created symlink /etc/systemd/system/crond.service → /dev/null.
lrwxrwxrwx. 1 root root 9 May 27 15:25 /etc/systemd/system/crond.service -> /dev/null
/dev/null

=== Proof: it IS a symlink to /dev/null ===
Name:/etc/systemd/system/crond.service Type:symbolic link Target:'/etc/systemd/system/crond.service' -> '/dev/null'

=== Try to start a masked service — fails ===
Failed to start crond.service: Unit crond.service is masked.
Expected fail: masked

=== Unmask: remove the /dev/null symlink ===
Removed /etc/systemd/system/crond.service.
ls: cannot access '/etc/systemd/system/crond.service': No such file or directory
Symlink removed

=== T16 demonstration ===
Without daemon-reload — systemd does not see it yet:
● lab09-test.service
   Loaded: not-found (Reason: Unit lab09-test.service not found.)
   Active: inactive (dead)

After daemon-reload:
● lab09-test.service - Lab 09 test service (does nothing)
   Loaded: loaded (/etc/systemd/system/lab09-test.service; disabled; vendor preset: disabled)
   Active: inactive (dead)
```

### i) Switches Table

| Token | Meaning |
|---|---|
| `systemctl enable SVC` | Symlink unit into wants dir |
| `systemctl disable SVC` | Remove wants symlink |
| `systemctl mask SVC` | Symlink unit → /dev/null in admin dir |
| `systemctl unmask SVC` | Remove the /dev/null symlink |
| `systemctl daemon-reload` | Reread unit files from disk |
| `systemctl is-enabled SVC` | State: enabled / disabled / masked / static |
| `systemctl list-unit-files \| grep SVC` | List unit + state |
| `find -ls` | Print find results in ls -l format |
| `stat --format='%F %N'` | File type + name (resolving symlinks) |

### j) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | `systemctl enable` = symlink | In `*.target.wants/` |
|   | `systemctl mask` = symlink to /dev/null | In `/etc/systemd/system/` |
|   | `systemctl is-enabled` | Shows the state |
|   | Custom unit dir | `/etc/systemd/system/` (admin); `/usr/lib/systemd/system/` (package) |
|   | Precedence | `/etc/systemd/system/` overrides `/usr/lib/` |
|   | unit file edits need reload | systemd caches the parsed unit files in memory |
| 🪤 **Trap Risk (T17)** | mask vs disable confusion | Always verify with `ls -l /etc/systemd/system/<svc>`. If it points to `/dev/null`, it's masked. `disable` does NOT create that symlink |
| 🪤 **Trap Risk (T16)** | Editing unit file without daemon-reload | After ANY change to a unit file (drop-in, edit, copy, link), run `systemctl daemon-reload`. The exam grades the **live** state, not the disk state |

### k) 🧹 Cleanup

```bash
LAB=lab09
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
TOPIC:    systemctl mask = symlink to /dev/null; daemon-reload requirement
COMMANDS: systemctl enable/disable/mask/unmask/daemon-reload, readlink, find -ls
TRAPS:    T17 + T16 (both rehearsed)
MISSED:   —
NEXT:     Lab 10 — mv (rename + move) (/var practice dir)
EOF
echo "Journal written: $(ls -la $JDIR)"

systemctl unmask "$SVC" 2>/dev/null
rm -f /etc/systemd/system/lab09-test.service
systemctl daemon-reload
rm -rf /root/link-demo
rm -rf /tmp/link-lab
echo "exit was: $?"
```

### l) Troubleshoot Table

| Symptom | Fix |
|---|---|
| `systemctl mask` says "already masked" | Already done; verify with `ls -l /etc/systemd/system/$SVC` |
| Service still running after mask | `mask` only prevents future starts; `systemctl stop` to stop now |
| `systemctl status` says "not-found" after dropping new unit | Forgot `daemon-reload` (T16) |
| `unmask` says "Removed" but `is-enabled` is wrong | Run `daemon-reload` after unmask too |

### m) STOP

> **STOP — paste output before declaring Lab 09 complete.**

### n) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| Service is unmasked | `systemctl is-enabled $SVC` (NOT "masked") | Confirms we cleaned up |
| Custom unit removed | `test -e /etc/systemd/system/lab09-test.service \|\| echo CLEAN` | No stray units |
| daemon-reload run | `systemctl daemon-reload; echo $?` (0) | systemd in-memory matches disk |
| All 3 journal entries | `find /root/rhcsa_journal/lab09 -name done.txt \| wc -l` (expect 3) | Reboot-proof |

> **Reboot question:** "If we rebooted with `$SVC` masked, would it auto-start?" — Answer: no. The mask symlink survives reboot (it's in `/etc/systemd/system/` on the root partition). systemd reads it on boot and refuses to start. That's the ENTIRE point of `mask` vs `disable`.

---

## 🪤 Trap Registry Update — End of Lab 09

| Trap ID | Category | Rehearsed? | If hit, repeat in |
|---|---|---|---|
| T17 | systemd | ✅ | — |
| T16 | systemd | ✅ | — |

3-lab trap window (07+08+09): **T07, T43, T32, T31, T17, T16** = **6 unique traps** ✓

Next lab (10) traps: **T25** (firewalld --permanent without --reload) · **T34** (cron.d file needs username field — 6 fields total).

---

## 🎓 What You Now Own

1. `ln SRC LINK` — hard link (shared inode, same FS only, no dirs).
2. `ln -s SRC LINK` — symbolic link (path string, any FS, any target).
3. `readlink` / `readlink -f` — read stored target / canonical path.
4. `find -inum N` — find every name for an inode.
5. `ls -li` — see inodes in the listing.
6. `stat --format='%i %h %F %N'` — inode, link count, type, target.
7. **systemctl enable** = symlink in `*.target.wants/`.
8. **systemctl mask** = symlink to `/dev/null`.
9. **systemctl daemon-reload** required after ANY unit file change.
10. The "verify with `ls -l`" muscle memory that defeats T17 (mask vs disable confusion).
