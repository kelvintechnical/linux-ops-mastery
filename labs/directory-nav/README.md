# Lab 05: Directory Navigation — `cd`, `pwd`, `ls`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Permanent standard:** every lab is exactly **5 tasks**. If a topic needs more, split it into another 5-task lab.
- **Practice Directory (rotation #05):** `/usr`
- **Sandbox:** `/tmp/nav-lab`
- **Journal:** `/root/rhcsa_journal/lab05/`
- **Traps rehearsed:** **T41** not reboot-testing persistence, **T42** live fix without persistent record, **T43** stuck longer than 10 minutes.

> **This lab's practice directory is: `/usr`** — every task references `/usr` in at least two commands.

---

## Objective

Build muscle memory for `pwd`, `cd`, and `ls` through five dense tasks. You will practice absolute paths, relative paths, parent navigation, home navigation, `cd -`, long listings, SELinux context previews, evidence capture, persistence checks, and reboot-safe journal entries.

---

## Lab Header Block

Run this first and confirm or correct the environment values before Task 1.

```bash
sudo -i
echo "ENV:   ${ENV:-DECLARE_BAREMETAL_OR_AMI}"
echo "DISK:  $(lsblk | awk '$6=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "NIC:   $(ip -o addr show | awk '$2!="lo"{print $2}' | sort -u | tr -d ':' | paste -sd, -)"
echo "SE:    $(getenforce 2>/dev/null || echo unavailable)"
echo "OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "TIME:  $(date -Is)"
echo "USER:  $(whoami)@$(hostname)"
echo "TRAPS: T41 T42 T43"
echo "PRACTICE DIR: /usr"
```

> **STOP — paste the header output before setup.** If you are on an AMI and SELinux is disabled, note it now; later SELinux labs must be practiced on Rocky/RHEL with SELinux enforcing.

---

## Lab-Wide Setup

```bash
sudo -i
mkdir -p /tmp/nav-lab /root/rhcsa_journal/lab05
cd /tmp/nav-lab

cat > /tmp/nav-lab/THIS_DIRECTORY.txt <<'EOF'
/usr — User programs, utilities, and their libraries

/usr is the largest directory on most Linux systems. It holds programs,
libraries, documentation, man pages, and shared data installed by the package
manager but not needed for the earliest boot steps.

Why it exists: Linux separates the small early-boot root filesystem from the
larger body of installed software. On modern RHEL, historical paths such as
/bin and /sbin are usually symlinks into /usr/bin and /usr/sbin.

What lives inside it: /usr/bin commands, /usr/sbin admin tools, /usr/lib and
/usr/lib64 libraries, /usr/share documentation and data, and application files.

Why RHCSA cares: nearly every command you type resolves under /usr. You must
be comfortable navigating it, listing it, and recognizing symlinked legacy
paths before troubleshooting permissions, packages, services, or SELinux.
EOF

cat /tmp/nav-lab/THIS_DIRECTORY.txt
echo "setup done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste setup output before Task 1.**

---

# The 5 Tasks

---

## Task 1 — Orient Yourself with `pwd` and `/usr`

**Practice directory this task:** `/usr`

`/usr` stores package-managed commands and libraries. This task proves where you are, verifies `/usr`, and saves evidence.

### 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/nav-lab
date -Is > task01-warmup.log
echo "user=$(whoami) host=$(hostname) kernel=$(uname -r)" >> task01-warmup.log
ls /usr 2>/dev/null | wc -l >> task01-warmup.log
cat task01-warmup.log | tee task01-warmup.copy
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Use `pwd` to identify your current directory, list `/usr`, and capture directory metadata with stdout and stderr saved together.

### Main Command Block

```bash
cd /tmp/nav-lab
pwd
ls /usr | head -n 10
ls -ld /usr /tmp/nav-lab > task01-locations.txt 2>&1
cat task01-locations.txt
echo "usr entries: $(ls /usr 2>/dev/null | wc -l)"
test -d /usr && echo "/usr exists"
test -s task01-locations.txt && echo "task01 evidence saved"
```

### Human-Readable Breakdown

- `cd /tmp/nav-lab` moves into the sandbox.
- `pwd` prints your current directory.
- `ls /usr | head -n 10` lists the practice directory and limits the output.
- `ls -ld /usr /tmp/nav-lab > task01-locations.txt 2>&1` saves metadata for both directories and captures any error in the same file.
- `$(ls /usr 2>/dev/null | wc -l)` counts `/usr` entries while discarding unexpected errors.
- `test -d` and `test -s` prove the directory exists and the evidence file is non-empty.

### Reading It Left to Right

`ls -ld /usr /tmp/nav-lab > task01-locations.txt 2>&1`

1. `ls` lists files or directories.
2. `-l` means long listing.
3. `-d` means show the directory entry itself, not its contents.
4. `/usr /tmp/nav-lab` are the targets.
5. `>` writes stdout to the file.
6. `2>&1` sends stderr to the same destination as stdout.

### The Story

Every safe command line starts with orientation. `pwd` tells you where you stand; `ls -ld` tells you what the target is. This habit prevents running the right command in the wrong directory.

### Expected Output

```text
/tmp/nav-lab
bin
etc
lib
lib64
share
...
drwxr-xr-x. ... /usr
drwxr-xr-x. ... /tmp/nav-lab
usr entries: 12
/usr exists
task01 evidence saved
```

### Switches Table

| Token | Meaning |
|---|---|
| `pwd` | Print working directory |
| `ls -l` | Long listing with permissions, owner, size, and time |
| `ls -d` | Show directory entry itself |
| `head -n 10` | Show first 10 lines |
| `>` | Redirect stdout and truncate target file |
| `2>&1` | Send stderr to stdout's current destination |
| `2>/dev/null` | Discard stderr |
| `test -d` | True if path is a directory |
| `test -s` | True if file is non-empty |
| `tee` | Show output and save a copy |

### 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|  | `pwd` | Answers “where am I?” |
|  | Absolute path | `/usr` works from anywhere |
|  | `ls -ld` | Directory metadata without listing children |
|  | `> file 2>&1` | Capture stdout and stderr together |
|  | `$(cmd)` | Paste command output inline |
|  | `$?` | Exit status of the previous command |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| T42 | You save evidence only in `/tmp` and assume it survives reboot | Write the journal under `/root/rhcsa_journal/lab05/` before cleanup |

### 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| Sandbox exists now | `test -d /tmp/nav-lab && echo OK` | confirms current lab workspace |
| Journal root exists | `test -d /root/rhcsa_journal/lab05 && echo OK` | confirms reboot-safe progress location |
| `/tmp` persistence | `ls /tmp/nav-lab` after reboot | expected to fail; `/tmp` is temporary |

```bash
test -d /tmp/nav-lab && echo "sandbox=OK"
test -d /root/rhcsa_journal/lab05 && echo "journal=OK"
```

### 📓 Journal Write — Before Cleanup

```bash
LAB=lab05
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cat > "$JDIR/done.txt" <<EOF
LAB:    lab05
TASK:   task1
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Orient with pwd, /usr, and evidence files
COMMANDS: pwd, ls /usr, ls -ld, tee, test -d, test -s
TRAPS:    T42
MISSED:   none
NEXT:     task2 — absolute vs relative paths
EOF
ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /tmp/nav-lab/task01-warmup.log /tmp/nav-lab/task01-warmup.copy /tmp/nav-lab/task01-locations.txt
echo "exit was: $?"
```

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `pwd` is not `/tmp/nav-lab` | Run `cd /tmp/nav-lab` |
| Evidence file is empty | Re-run `ls -ld ... > task01-locations.txt 2>&1` |
| Journal write fails | Run `sudo -i`; `/root` requires root |

> **STOP — paste output before Task 2.**

---

## Task 2 — Absolute vs Relative Paths

**Practice directory this task:** `/usr`

`/usr/bin` is an absolute path. `bin` is the same destination only when you already stand in `/usr`.

### 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/nav-lab
ls /usr/no-such-entry 2> task02-error.log
grep -c "No such" task02-error.log
find /usr -maxdepth 1 -type d 2>/dev/null | sort | tee task02-usr-dirs.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Prove the difference between a path that starts at root and a path that depends on your current directory.

### Main Command Block

```bash
cd /tmp/nav-lab
cd /usr
pwd
ls -ld /usr /usr/bin > /tmp/nav-lab/task02-absolute.txt 2>&1
cd bin
pwd
ls -la . | head -n 8 | tee /tmp/nav-lab/task02-relative.txt
echo "bin command count: $(ls /usr/bin 2>/dev/null | wc -l)"
```

### Human-Readable Breakdown

- `cd /usr` works from anywhere because it is absolute.
- `cd bin` works only because you are already inside `/usr`.
- `ls -la .` lists the current directory with hidden entries and long metadata.
- `tee` displays the sample and saves it.
- The final `echo` counts entries in `/usr/bin` using command substitution.

### Reading It Left to Right

`cd bin`

1. `cd` changes directory.
2. `bin` has no leading `/`, so it is relative.
3. Bash resolves it as `/usr/bin` because the current directory is `/usr`.

### The Story

Absolute paths are full addresses. Relative paths are directions from the room you are standing in. RHCSA tasks usually give absolute paths because they are unambiguous.

### Expected Output

```text
/usr
/usr/bin
total ...
-rwxr-xr-x. ...
bin command count: 1000
```

### Switches Table

| Token | Meaning |
|---|---|
| `cd /usr` | Move with an absolute path |
| `cd bin` | Move with a relative path |
| `ls -la` | Long listing plus hidden entries |
| `.` | Current directory |
| `find -maxdepth 1` | Do not descend below the start directory |
| `find -type d` | Match directories only |
| `grep -c` | Count matching lines |
| `sort` | Sort output |
| `tee` | Print and save |

### 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|  | Absolute path | Starts with `/`; independent of `pwd` |
|  | Relative path | No leading `/`; depends on `pwd` |
|  | `.` | Current directory |
|  | `tee` | Saves evidence while output remains visible |
|  | `grep -c` | Produces a count, not matching text |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| T43 | You type `cd bin` from the wrong directory and waste time | Run `pwd` before every relative `cd` until it is automatic |

### 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| Current location | `pwd` | confirms relative navigation result |
| `$OLDPWD` exists | `echo "$OLDPWD"` | confirms `cd -` can work later |
| Evidence file exists | `test -s /tmp/nav-lab/task02-relative.txt && echo OK` | confirms `tee` saved output |

```bash
pwd
echo "OLDPWD=$OLDPWD"
test -s /tmp/nav-lab/task02-relative.txt && echo "task02 evidence=OK"
```

### 📓 Journal Write — Before Cleanup

```bash
LAB=lab05
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cat > "$JDIR/done.txt" <<EOF
LAB:    lab05
TASK:   task2
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Absolute vs relative paths from /usr
COMMANDS: cd /usr, cd bin, pwd, ls -ld, ls -la, find -maxdepth 1 -type d
TRAPS:    T43
MISSED:   none
NEXT:     task3 — parent, home, and cd - navigation
EOF
ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
cd /tmp/nav-lab
rm -f task02-error.log task02-usr-dirs.txt task02-absolute.txt task02-relative.txt
echo "exit was: $?"
```

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `cd bin` fails | Run `pwd`; if not `/usr`, run `cd /usr` first |
| Saved file missing | Check that the path begins with `/tmp/nav-lab/` |
| `OLDPWD` empty | You have not changed directories enough in this shell yet |

> **STOP — paste output before Task 3.**

---

## Task 3 — Parent, Home, and `cd -`

**Practice directory this task:** `/usr`

`/usr/share` gives a safe nested path for `..`, `$HOME`, and `cd -` drills.

### 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/nav-lab
set -o pipefail
ls /usr/share 2>&1 | head -n 5 | tee task03-share-head.txt
echo "PIPESTATUS=${PIPESTATUS[@]}"
set +o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Practice recovery navigation: up one level, home, and back to the previous directory.

### Main Command Block

```bash
cd /usr/share
pwd
cd ..
pwd
cd share/doc 2>/dev/null || cd /usr/share
pwd
cd "$HOME"
pwd
cd /usr
cd -
pwd
```

### Human-Readable Breakdown

- `cd /usr/share` moves to a known nested location.
- `cd ..` moves to the parent (`/usr`).
- `cd share/doc 2>/dev/null || cd /usr/share` tries a relative directory and falls back if docs are absent.
- `cd "$HOME"` returns home.
- `cd /usr` sets up the previous-directory toggle.
- `cd -` swaps back to `$OLDPWD`.

### Reading It Left to Right

`cd share/doc 2>/dev/null || cd /usr/share`

1. Try the relative destination.
2. Hide expected errors.
3. If it fails, run the fallback command.

### The Story

Navigation is not linear during troubleshooting. You bounce between configs, logs, and home. `..`, `$HOME`, and `cd -` are the recovery handles.

### Expected Output

```text
/usr/share
/usr
/usr/share/doc
/root
/usr
/usr
```

If `/usr/share/doc` is absent, the third path may be `/usr/share`.

### Switches Table

| Token | Meaning |
|---|---|
| `..` | Parent directory |
| `$HOME` | Home-directory environment variable |
| `cd -` | Swap to previous directory |
| `2>/dev/null` | Discard expected errors |
| `||` | Run fallback only on failure |
| `set -o pipefail` | Pipeline fails if any stage fails |
| `${PIPESTATUS[@]}` | Exit codes for every pipeline stage |

### 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|  | `..` | Move up one level |
|  | `$HOME` | Stable home path within this session |
|  | `cd -` | Toggle current and previous directories |
|  | `|| fallback` | Recover from expected failure |
|  | `pipefail` | Makes hidden pipe failure visible |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| T41 | You assume `$OLDPWD` survives logout or reboot | It does not; only the journal survives |

### 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| `$HOME` value | `echo "$HOME"` | confirms home shortcut target |
| `$OLDPWD` value | `echo "$OLDPWD"` | confirms `cd -` target for this shell |
| Reboot survival | Start a fresh shell and echo `$OLDPWD` | expected to be empty; shell state is volatile |

```bash
echo "HOME=$HOME"
echo "OLDPWD=$OLDPWD"
echo "PWD=$PWD"
```

### 📓 Journal Write — Before Cleanup

```bash
LAB=lab05
TASK=task3
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cat > "$JDIR/done.txt" <<EOF
LAB:    lab05
TASK:   task3
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Parent navigation, HOME, and cd -
COMMANDS: cd .., cd \$HOME, cd -, pipefail, PIPESTATUS
TRAPS:    T41
MISSED:   none
NEXT:     task4 — ls flags and SELinux context preview
EOF
ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
cd /tmp/nav-lab
rm -f task03-share-head.txt
echo "exit was: $?"
```

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `cd -` says `OLDPWD not set` | Run one normal `cd` first |
| You land at `/` unexpectedly | Too many `..`; reset with `cd /tmp/nav-lab` |
| `${PIPESTATUS[@]}` prints one value only | You are not checking immediately after the pipeline |

> **STOP — paste output before Task 4.**

---

## Task 4 — Read Listings with `ls -a`, `-A`, `-l`, `-h`, `-d`, `-Z`

**Practice directory this task:** `/usr`

`/usr` contains directories, symlinks, and SELinux-labeled files, making it safe for listing practice.

### 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/nav-lab
cat > task04-note.txt <<'EOF'
Listing flags turn directory names into evidence.
EOF
chmod 644 task04-note.txt
wc -w task04-note.txt
tr a-z A-Z < task04-note.txt | tee task04-note.upper
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Learn the core `ls` flags used for file inspection and introduce SELinux context output.

### Main Command Block

```bash
cd /tmp/nav-lab
ls -a /usr | head -n 8
ls -A /usr | head -n 8
ls -lh /usr | head -n 8 | tee task04-usr-long.txt
ls -ld /usr /usr/bin /usr/lib64 > task04-dir-metadata.txt 2>&1
ls -lZ /usr/bin/ls 2>/dev/null | tee task04-usr-context.txt
cat task04-dir-metadata.txt
echo "metadata lines: $(wc -l < task04-dir-metadata.txt)"
```

### Human-Readable Breakdown

- `ls -a` includes `.` and `..`.
- `ls -A` includes hidden entries but excludes `.` and `..`.
- `ls -lh` shows metadata with readable sizes.
- `ls -ld` shows the directory entries themselves.
- `ls -lZ` adds SELinux context.
- `wc -l < file` returns a pure line count.

### Reading It Left to Right

`ls -ld /usr /usr/bin /usr/lib64 > task04-dir-metadata.txt 2>&1`

1. `ls` lists.
2. `-l` long format.
3. `-d` directory entries only.
4. Three `/usr` paths are targets.
5. `>` saves stdout.
6. `2>&1` saves stderr with it.

### The Story

`ls -ld` is the RHCSA verification habit for directory permissions. `ls -Z` is the preview of SELinux reality: DAC permissions can look perfect while SELinux blocks the service.

### Expected Output

```text
.
..
bin
lib
lib64
share
...
drwxr-xr-x. ... /usr
... system_u:object_r:bin_t:s0 /usr/bin/ls
metadata lines: 3
```

### Switches Table

| Token | Meaning |
|---|---|
| `ls -a` | All entries, including `.` and `..` |
| `ls -A` | Almost all entries, excluding `.` and `..` |
| `ls -l` | Long listing |
| `ls -h` | Human-readable sizes |
| `ls -d` | Directory entries themselves |
| `ls -Z` | SELinux context |
| `< file` | Send file to stdin |
| `chmod 644` | Owner read/write; group/other read |
| `tr a-z A-Z` | Translate lowercase to uppercase |

### 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|  | `ls -A` | Dotfiles without `.` and `..` |
|  | `ls -lh` | Readable size metadata |
|  | `ls -ld` | Verify a directory itself |
|  | `ls -Z` | Show SELinux context |
|  | `tr` | Transform text streams |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| T42 | You see `?` in `ls -Z` and assume SELinux is fine | Run `getenforce`; use Rocky/RHEL enforcing for SELinux labs |

### 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| `/usr` metadata | `ls -ld /usr` | survives reboot on root filesystem |
| SELinux visibility | `ls -Z /usr/bin/ls` | confirms context output exists |
| SELinux mode | `getenforce` | confirms enforcing/permissive/disabled state |

```bash
ls -ld /usr /usr/bin /usr/lib64
getenforce 2>/dev/null || echo "SELinux tool unavailable"
ls -Z /usr/bin/ls 2>/dev/null || echo "SELinux context unavailable"
```

### 📓 Journal Write — Before Cleanup

```bash
LAB=lab05
TASK=task4
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cat > "$JDIR/done.txt" <<EOF
LAB:    lab05
TASK:   task4
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "$JDIR/notes.txt" <<EOF
TOPIC:    ls -a, ls -A, ls -l, ls -h, ls -d, ls -Z
COMMANDS: ls -a, ls -A, ls -lh, ls -ld, ls -lZ, getenforce, tr
TRAPS:    T42
MISSED:   none
NEXT:     task5 — capstone with recent, large, and return
EOF
ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /tmp/nav-lab/task04-note.txt /tmp/nav-lab/task04-note.upper /tmp/nav-lab/task04-usr-long.txt /tmp/nav-lab/task04-dir-metadata.txt /tmp/nav-lab/task04-usr-context.txt
echo "exit was: $?"
```

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| Directory contents flood screen | Add `-d`: `ls -ld /usr` |
| `-h` does nothing | Pair with `-l` or `-s` |
| `ls -Z` shows `?` | Check `getenforce`; SELinux may be disabled |

> **STOP — paste output before Task 5.**

---

## Task 5 — Exam Capstone: Recent, Large, Return Cleanly

**Practice directory this task:** `/usr`

Combine navigation, listing, sorting, evidence capture, metadata verification, and cleanup.

### 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/nav-lab
set -o noclobber
echo "first write $(date -Is)" > task05-noclobber.txt
echo "second write" > task05-noclobber.txt 2>/dev/null || echo "noclobber blocked overwrite"
echo "forced write $(date -Is)" >| task05-noclobber.txt
set +o noclobber
tail -n 1 task05-noclobber.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Complete an RHCSA-style navigation scenario: go to `/usr`, identify recent entries, identify large entries, verify metadata, save proof, and return.

### Main Command Block

```bash
cd /tmp/nav-lab
pwd > task05-start.txt
cd /usr
pwd
ls -ltrh | tail -n 5 | tee /tmp/nav-lab/task05-recent.txt
ls -lhS | head -n 5 | tee /tmp/nav-lab/task05-largest.txt
ls -ld /usr /usr/bin /usr/lib64 > /tmp/nav-lab/task05-metadata.txt 2>&1
cat /tmp/nav-lab/task05-metadata.txt
echo "recent lines: $(wc -l < /tmp/nav-lab/task05-recent.txt)"
echo "largest lines: $(wc -l < /tmp/nav-lab/task05-largest.txt)"
cd -
pwd
cat /tmp/nav-lab/task05-start.txt
```

### Human-Readable Breakdown

- `pwd > task05-start.txt` saves the starting point.
- `cd /usr` enters the practice directory.
- `ls -ltrh | tail -n 5` shows the newest entries at the bottom.
- `ls -lhS | head -n 5` shows largest entries first.
- `ls -ld ... > file 2>&1` captures metadata and errors.
- `cd -` returns to the previous directory.

### Reading It Left to Right

`ls -ltrh | tail -n 5 | tee /tmp/nav-lab/task05-recent.txt`

1. `ls` lists current directory (`/usr`).
2. `-l` long format.
3. `-t` sort by modification time.
4. `-r` reverse the sort, putting newest near the bottom.
5. `-h` readable sizes.
6. `| tail -n 5` keeps the last five lines.
7. `| tee FILE` displays and saves the evidence.

### The Story

This is what exam tasks feel like: navigate, inspect, verify, save proof, return cleanly. `ls -ltrh | tail` is also the first production troubleshooting move when asking “what changed recently?”

### Expected Output

```text
/usr
... five recent rows ...
... five largest rows ...
drwxr-xr-x. ... /usr
recent lines: 5
largest lines: 5
/tmp/nav-lab
/tmp/nav-lab
```

### Switches Table

| Token | Meaning |
|---|---|
| `ls -l` | Long listing |
| `ls -t` | Sort by modification time |
| `ls -r` | Reverse sort |
| `ls -h` | Human-readable sizes |
| `ls -S` | Sort by size, largest first |
| `tail -n 5` | Last five lines |
| `head -n 5` | First five lines |
| `tee` | Display and save |
| `cd -` | Return to previous directory |
| `set -o noclobber` | Prevent accidental overwrite |
| `>|` | Force overwrite under noclobber |

### 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|  | `ls -ltrh` | Newest-at-bottom troubleshooting listing |
|  | `ls -lhS` | Largest-first disk triage listing |
|  | `tee` | Evidence capture while still showing output |
|  | `cd -` | Clean return to previous directory |
|  | `noclobber` | Prevent accidental overwrite |
|  | `>|` | Intentional forced overwrite |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| T43 | You restart the whole capstone after one typo | Fix the failing line only; do not restart unless state is corrupted |

### 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| Lab journal | `find /root/rhcsa_journal/lab05 -name done.txt | sort` | proves all completed tasks are resumable |
| Notes files | `find /root/rhcsa_journal/lab05 -name notes.txt | sort` | human-readable resume context |
| Sandbox cleanup | `test -d /tmp/nav-lab || echo sandbox gone` | confirms temporary files are gone |

```bash
find /root/rhcsa_journal/lab05 -name done.txt | sort
find /root/rhcsa_journal/lab05 -name notes.txt | sort
```

### 📓 Journal Write — Before Cleanup

```bash
LAB=lab05
TASK=task5
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cat > "$JDIR/done.txt" <<EOF
LAB:    lab05
TASK:   task5
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Capstone — recent files, large files, metadata, return cleanly
COMMANDS: pwd, cd /usr, ls -ltrh, ls -lhS, ls -ld, tee, wc -l, cd -
TRAPS:    T43
MISSED:   none
NEXT:     lab06 — ls -l, ls -Z, SELinux contexts
EOF
find /root/rhcsa_journal/lab05 -name done.txt | sort
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
cd /tmp
rm -rf /tmp/nav-lab
echo "exit was: $?"
exit
```

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `cd -` prints `OLDPWD not set` | Run a normal `cd` first |
| Recent/largest output has fewer than five rows | Use `/usr/bin` instead on minimal installs |
| `noclobber` blocks later work | Run `set +o noclobber` |

> **STOP — paste output. Lab 05 complete.**

---

## Checklist (5 Tasks — Permanent)

- [ ] Task 1 — orient with `pwd`, `/usr`, evidence files
- [ ] Task 2 — absolute vs relative paths
- [ ] Task 3 — parent, home, and `cd -`
- [ ] Task 4 — `ls -a`, `-A`, `-l`, `-h`, `-d`, `-Z`
- [ ] Task 5 — recent, large, metadata, return capstone

---

## Trap Rotation

| Trap | Rehearsed where |
|---|---|
| T41 | Task 3 — shell state does not persist |
| T42 | Tasks 1 and 4 — `/tmp` and SELinux assumptions |
| T43 | Tasks 2 and 5 — context mistakes and over-restarting |

Next lab should rotate into SELinux traps: T01, T02, and T03.

---

## Resume Command

```bash
find /root/rhcsa_journal -name done.txt | sort | tail -5
```

---

## Related Labs

| Lab | Connection |
|---|---|
| Lab 04 — Capture Both Output and Error | Uses `2>&1`, `tee`, and evidence files |
| Lab 06 — Listing Files and SELinux Contexts | Extends `ls -l` into `ls -Z` |
| Lab 08 — Copying Files and Directories | Requires absolute and relative path fluency |
| Lab 10 — Moving and Renaming Files | Same path rules, higher consequence |
| Lab 11 — Safe Deletion | `pwd` before `rm -rf` prevents disasters |

---

## Author

**Kelvin R. Tobias** — [kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical)
