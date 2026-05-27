# Lab 05: Directory Navigation — `cd`, `pwd`, `ls`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Career arcs covered:** RHCSA EX200 path fluency, RHCE playbook path references, CKA config/log navigation, RHCA troubleshooting workflows
- **Prerequisite:** Lab 04 (`&>`, `2>&1`, `tee`, `/tmp` sandbox habits)
- **Time Estimate:** 30–45 minutes
- **Tasks:** 3 (ADHD spec — exactly 3 dense tasks per `readmetemplate/cursor-adhd-lab-prompt.txt`)
- **Practice Directory (lab-wide rotation #05):** `/usr`
- **Sandbox:** `/tmp/nav-lab`
- **Traps rehearsed this lab:** **T41** (Not rebooting to test persistence after every task) · **T43** (Getting stuck >10 min on one task)

> **This lab's practice directory is: `/usr`** — every task references it in at least two commands.

---

## 🖥️ LAB HEADER BLOCK — run this FIRST and confirm or correct

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}      # BAREMETAL or AMI"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T41 T43"
echo "📁  PRACTICE DIR: /usr"
```

> **STOP — paste the header output before running setup.** If `ENV` is unset, run `export ENV=BAREMETAL` (or `AMI`) first.

---

## 🎯 Objective

Build muscle memory for moving around Linux without losing your place. By the end you will use `pwd`, `cd` (absolute / relative / parent / home / toggle), and `ls` (`-l`, `-a`, `-A`, `-h`, `-d`, `-t`, `-r`, `-S`) without thinking — in only **three dense tasks**.

---

## 🧠 Concept: Linux Is One Tree

Linux has a single root directory: `/`. Everything lives somewhere under it. There are no drive letters.

| Path Type | Example | Meaning |
|---|---|---|
| Absolute | `/usr/bin` | Starts at `/`; works from anywhere |
| Relative | `bin` | Starts from your current directory |
| Parent | `..` | One directory up |
| Current | `.` | The directory you are standing in |
| Home | `~` or `$HOME` | Your user's home directory |
| Previous | `cd -` | Swap with `$OLDPWD` |

> Exam rule: if a task gives you an absolute path, use it. If you are already in the right parent directory, a relative path is fine.

---

## 🚦 Lab-Wide Setup — Run This BEFORE Task 1

```bash
sudo -i
mkdir -p /tmp/nav-lab
cd /tmp/nav-lab

cat > /tmp/nav-lab/THIS_DIRECTORY.txt <<'EOF'
/usr — User programs, utilities, and their libraries

/usr is the largest directory on most Linux systems. It stores programs,
libraries, documentation, man pages, shared data, and package-managed content
that is not needed during the earliest boot steps.

Why it exists: the system separates the tiny early-boot root filesystem from
the larger body of installed software. On modern RHEL, many historical root
paths such as /bin and /sbin are symlinks into /usr/bin and /usr/sbin.

What lives inside it: /usr/bin commands, /usr/sbin admin tools, /usr/lib and
/usr/lib64 libraries, /usr/share documentation and data, and package-managed
application files.

Why RHCSA cares: nearly every command you type resolves to something under
/usr. You must be comfortable navigating it, listing it, and recognizing when
/bin or /sbin is actually a symlink into /usr.
EOF

cat /tmp/nav-lab/THIS_DIRECTORY.txt
echo "setup done by $(whoami) at $(date -Is) on $(hostname)"
echo "exit was: $?"
```

> **STOP — paste your output before Task 1.**

---

# The 3 Tasks

---

## Task 1 — Orient with `pwd`, Absolute Paths, and Evidence Files

### a) Directory Context

**Practice directory this task:** `/usr`
`/usr` holds package-managed programs, libraries, man pages, and shared data. It is the anchor directory for the whole lab.

### b) 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/nav-lab
date -Is > task01-warmup.log
echo "user=$(whoami) host=$(hostname) kernel=$(uname -r)" >> task01-warmup.log
ls /usr 2>/dev/null | wc -l >> task01-warmup.log
cat task01-warmup.log | tee task01-warmup.copy
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Use `pwd` to prove your current location, list `/usr`, and save evidence that the sandbox and practice directory both exist.

### d) Main Command Block

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

### e) Human-Readable Breakdown

- `cd /tmp/nav-lab` — move into the sandbox using an absolute path.
- `pwd` — print working directory; proves you are where you think you are.
- `ls /usr | head -n 10` — list the first 10 entries of `/usr`.
- `ls -ld /usr /tmp/nav-lab > task01-locations.txt 2>&1` — record metadata for both directories AND capture any errors in the same file.
- `$(ls /usr 2>/dev/null | wc -l)` — command substitution that counts `/usr` entries while silently discarding any stderr.
- `test -d` and `test -s` — quick sanity checks (directory exists, file non-empty).

### f) Reading It Left to Right

`ls -ld /usr /tmp/nav-lab > task01-locations.txt 2>&1`

1. `ls` — the list command.
2. `-l` — long format (permissions, owner, size, mtime).
3. `-d` — describe the directory entry itself, not its contents.
4. `/usr /tmp/nav-lab` — two target paths.
5. `> task01-locations.txt` — redirect stdout to the file, truncating it.
6. `2>&1` — send stderr to wherever stdout is currently going (the file).

### g) The Story

Good admins orient first. Before editing, deleting, copying, or redirecting, run `pwd` and inspect the target. This single habit prevents the classic mistake: running the right command in the wrong directory. On the RHCSA exam, every "save the output to a file" task implicitly assumes you know exactly where you are when the file is created.

### h) Expected Output

```text
/tmp/nav-lab
bin
etc
games
include
lib
lib64
...
drwxr-xr-x. ... /usr
drwxr-xr-x. ... /tmp/nav-lab
usr entries: 12
/usr exists
task01 evidence saved
```

Exact `/usr` contents and entry count vary by distribution.

### i) Switches Table

| Token | Meaning |
|---|---|
| `pwd` | Print working directory |
| `ls` | List directory contents |
| `ls -l` | Long listing |
| `ls -d` | Directory entry itself, not contents |
| `head -n 10` | Keep first 10 lines |
| `>` | Redirect stdout to file (truncate) |
| `2>&1` | Send stderr to stdout's destination |
| `2>/dev/null` | Discard stderr |
| `test -d` | True if path is a directory |
| `test -s` | True if file exists and is non-empty |
| `$(...)` | Command substitution |

### j) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | `pwd` | Answers "where am I?" |
|   | Absolute path | `/usr` works regardless of `pwd` |
|   | `ls -ld` | Directory metadata without dumping contents |
|   | `> file 2>&1` | Capture stdout and stderr together |
|   | `$(cmd)` | Run command, paste output inline |
|   | `/dev/null` | Discard unwanted output |
|   | `$?` | Exit status of previous command |
| 🪤 **Trap Risk (T43)** | Getting stuck >10 min on one task | If `pwd`, `cd`, or `ls` fails unexpectedly, do not loop — verify the FS is mounted (`mount \| grep /usr`), then move on |

### k) 🧹 Cleanup

```bash
LAB=lab05
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
TOPIC:    Directory orientation — pwd, absolute paths, /usr evidence files
COMMANDS: pwd, cd, ls -ld, head, tee, test, $()
TRAPS:    T43 (time-stuck reminder)
MISSED:   —
NEXT:     task2 — relative paths, .., $HOME, cd -
EOF
echo "Journal written: $(ls -la $JDIR)"

rm -f /tmp/nav-lab/task01-warmup.log /tmp/nav-lab/task01-warmup.copy /tmp/nav-lab/task01-locations.txt
echo "exit was: $?"
```

### l) Troubleshoot Table

| Symptom | Fix |
|---|---|
| `pwd` does not show `/tmp/nav-lab` | Run `cd /tmp/nav-lab` again |
| `ls: cannot access '/usr'` | Verify with `ls /`; on broken systems boot to rescue |
| `task01-locations.txt` is empty | Re-run `ls -ld ... > file 2>&1` — check `$?` |
| `test -s` returns 1 | The file is missing or zero-byte; check `ls -l` |

### m) STOP

> **STOP — paste your output before Task 2.**

### n) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| Sandbox directory `/tmp/nav-lab` | `test -d /tmp/nav-lab && echo OK` | Confirms the sandbox exists (note: `/tmp` is wiped on reboot — that is expected) |
| Journal entry | `cat /root/rhcsa_journal/lab05/task1/done.txt` | `/root` survives reboots; this is your durable evidence |
| `/usr` reachable | `ls -ld /usr` | Confirms practice directory mounted |

> **Reboot question:** "If we rebooted now, would the journal entry survive? Prove it." — Answer: yes, because `/root` is on the root partition. The sandbox under `/tmp` would NOT survive.

---

## Task 2 — Move with Relative Paths, `..`, `$HOME`, and `cd -`

### a) Directory Context

**Practice directory this task:** `/usr`
`/usr/share/doc` is the ideal nested path for `..`, `../..`, `~`, and `cd -` practice because it is reliably present and safe to traverse.

### b) 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/nav-lab
set -o pipefail
ls /usr/no-such-entry 2> task02-error.log
grep -c "No such" task02-error.log
find /usr -maxdepth 1 -type d 2>/dev/null | sort | tee task02-usr-dirs.txt
echo "PIPESTATUS=${PIPESTATUS[@]}"
set +o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Practice the navigation shortcuts that recover you when you are deep in a directory tree: relative paths, `..`, `../..`, `~`, `$HOME`, plain `cd`, and `cd -`.

### d) Main Command Block

```bash
cd /tmp/nav-lab
cd /usr
pwd
ls -ld /usr /usr/bin > /tmp/nav-lab/task02-absolute.txt 2>&1
cd bin
pwd
ls -la . | head -n 8 | tee /tmp/nav-lab/task02-relative.txt
echo "bin command count: $(ls /usr/bin 2>/dev/null | wc -l)"

cd /usr/share
pwd
cd ..
pwd
cd share/doc 2>/dev/null || cd /usr/share
pwd
cd ../..
pwd
cd "$HOME"
pwd
cd /usr
cd -
pwd
```

### e) Human-Readable Breakdown

- `cd /usr` then `cd bin` — absolute then relative; `bin` resolves to `/usr/bin` because you stand in `/usr`.
- `ls -la . | head -n 8 | tee FILE` — list current dir (hidden + long), keep top 8, print and save.
- `cd /usr/share` then `cd ..` — climb back to `/usr`.
- `cd share/doc 2>/dev/null || cd /usr/share` — try a relative path, fall back if missing.
- `cd ../..` — climb two levels.
- `cd "$HOME"` — return home using the env var (safer than `~` in scripts).
- `cd /usr; cd -` — `cd -` toggles back to `$OLDPWD`.

### f) Reading It Left to Right

`cd share/doc 2>/dev/null || cd /usr/share`

1. `cd share/doc` — try to enter a relative subpath.
2. `2>/dev/null` — silence the error if `doc` is missing.
3. `||` — only run the next command if the previous failed (`$? != 0`).
4. `cd /usr/share` — safe fallback to a known directory.

### g) The Story

Navigation is not a straight line. Real troubleshooting bounces between configs, logs, and home directories. `..`, `$HOME`, and `cd -` are the shell's recovery handles. The `|| fallback` pattern is the shell's safety net — every senior admin uses it to keep scripts moving when an expected path is missing.

### h) Expected Output

```text
/usr
drwxr-xr-x. ... /usr
lrwxrwxrwx. ... /usr/bin -> bin
/usr/bin
total ...
drwxr-xr-x. ...
...
bin command count: 1000
/usr/share
/usr
/usr/share/doc
/usr
/root
/root
/usr
```

If `/usr/share/doc` is not installed, the fallback puts you in `/usr/share` instead. If you are not root, `$HOME` may be `/home/ec2-user` or another path.

### i) Switches Table

| Token | Meaning |
|---|---|
| `cd /usr` | Absolute path |
| `cd bin` | Relative path (depends on `pwd`) |
| `..` | Parent directory |
| `../..` | Two parents up |
| `~` | Shell shorthand for `$HOME` |
| `$HOME` | Env var with home path |
| `cd -` | Swap with `$OLDPWD` |
| `cd` (no arg) | Same as `cd $HOME` |
| `ls -la` | Long listing including hidden entries |
| `\|\|` | Run next only if previous failed |
| `2>/dev/null` | Discard stderr |
| `set -o pipefail` | Pipeline fails if any stage fails |
| `${PIPESTATUS[@]}` | Exit status of every pipeline stage |

### j) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | Absolute path | Starts with `/`; independent of `pwd` |
|   | Relative path | Resolves from current `pwd` |
|   | `..` | Parent |
|   | `$HOME` | Portable home reference |
|   | `cd -` | Toggle previous dir |
|   | `\|\|` fallback | Recovery on failure |
|   | `pipefail` | Make pipeline failures visible |
|   | `${PIPESTATUS[@]}` | See exit code of each stage |
| 🪤 **Trap Risk (T41)** | Not rebooting to test persistence | Path muscle memory persists across reboots — but env vars (`$OLDPWD`, `$HOME`) reset on every new shell. Verify by opening a fresh login shell and re-running `cd -` |

### k) 🧹 Cleanup

```bash
LAB=lab05
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
TOPIC:    Relative paths, parent navigation, $HOME, cd -
COMMANDS: cd, .., ~, $HOME, cd -, ||, pipefail, PIPESTATUS
TRAPS:    T41 (persistence reminder)
MISSED:   —
NEXT:     task3 — ls flags + exam-style capstone
EOF
echo "Journal written: $(ls -la $JDIR)"

cd /tmp/nav-lab
rm -f task02-error.log task02-usr-dirs.txt task02-absolute.txt task02-relative.txt
echo "exit was: $?"
```

### l) Troubleshoot Table

| Symptom | Fix |
|---|---|
| `cd bin` fails | You were not in `/usr`; run `pwd`, then `cd /usr` |
| `cd -` says `OLDPWD not set` | Run at least one normal `cd` first |
| `cd ../..` lands at `/` | Reset with `cd /tmp/nav-lab` |
| `$HOME` is empty | New shell? Re-run `sudo -i` or `su -` |

### m) STOP

> **STOP — paste your output before Task 3.**

### n) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| `$OLDPWD` set | `echo "$OLDPWD"` | Confirms `cd -` will work; resets on new shell |
| `$HOME` populated | `echo "$HOME"` | Confirms `cd ~` and `cd "$HOME"` will work |
| Journal entry | `cat /root/rhcsa_journal/lab05/task2/done.txt` | Survives reboots |

> **Reboot question:** "If we rebooted now, would `cd -` still work?" — Answer: no. `$OLDPWD` is per-shell. A fresh login resets it. Path muscle memory is durable; shell env vars are not.

---

## Task 3 — `ls` Flags + Exam-Style Capstone

### a) Directory Context

**Practice directory this task:** `/usr`
`/usr` has normal directories, symlinks, varied sizes, and stable metadata — the ideal target for `ls -a`, `-A`, `-l`, `-h`, `-d`, `-t`, `-r`, and `-S`.

### b) 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/nav-lab
set -o noclobber
echo "first write $(date -Is)" > task03-noclobber.txt
echo "second write" > task03-noclobber.txt 2>/dev/null || echo "noclobber blocked overwrite"
echo "forced write $(date -Is)" >| task03-noclobber.txt
set +o noclobber
tail -n 1 task03-noclobber.txt
cat <<'EOF' > task03-note.txt
ls flags turn directory names into evidence.
EOF
chmod 644 task03-note.txt
wc -w task03-note.txt
tr a-z A-Z < task03-note.txt | tee task03-note.upper
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Compress every important `ls` flag into one task, then complete a compact RHCSA-style task: move to `/usr`, list recent entries, list large entries, verify directory metadata, save evidence, and return cleanly.

### d) Main Command Block

```bash
cd /tmp/nav-lab
ls -a /usr | head -n 8
ls -A /usr | head -n 8
ls -lh /usr | head -n 8 | tee task03-usr-long.txt
ls -ld /usr /usr/bin /usr/lib64 > task03-dir-metadata.txt 2>&1
cat task03-dir-metadata.txt
echo "metadata lines: $(wc -l < task03-dir-metadata.txt)"

pwd > task03-start.txt
cd /usr
pwd
ls -ltrh | tail -n 5 | tee /tmp/nav-lab/task03-recent.txt
ls -lhS | head -n 5 | tee /tmp/nav-lab/task03-largest.txt
ls -ld /usr /usr/bin /usr/lib64 > /tmp/nav-lab/task03-metadata.txt 2>&1
cat /tmp/nav-lab/task03-metadata.txt
echo "recent lines: $(wc -l < /tmp/nav-lab/task03-recent.txt)"
echo "largest lines: $(wc -l < /tmp/nav-lab/task03-largest.txt)"
cd -
pwd
cat /tmp/nav-lab/task03-start.txt
```

### e) Human-Readable Breakdown

- `ls -a` vs `ls -A` — both show hidden entries; `-A` excludes `.` and `..`.
- `ls -lh` — long format with human-readable sizes (`4.0K`, `1.2M`).
- `ls -ld` — describe the directory entry, not the contents.
- `ls -ltrh` — long, sort by mtime, reverse → **newest at the bottom**.
- `ls -lhS` — long, human size, sort by **size** → largest first.
- `pwd > file; cd /usr; ...; cd -` — record start, jump, do work, jump back.
- `tail -n 5` / `head -n 5` — keep just the relevant slice.

### f) Reading It Left to Right

`ls -ltrh | tail -n 5 | tee /tmp/nav-lab/task03-recent.txt`

1. `ls` — list current directory (`/usr`).
2. `-l` — long format.
3. `-t` — sort by mtime, newest first.
4. `-r` — reverse → newest at bottom.
5. `-h` — human-readable sizes.
6. `| tail -n 5` — keep the bottom 5 lines (the newest).
7. `| tee FILE` — print and save the slice.

### g) The Story

Plain `ls` is for quick scans. `ls -l` is for evidence. `ls -ld` is the exam command for verifying a directory's own permissions. `ls -A` is safer than `ls -a` in scripts because it excludes `.` and `..`. `ls -ltrh | tail` is the universal "what changed recently?" probe — admins type it dozens of times a day.

### h) Expected Output

```text
.
..
bin
etc
...
total ...
drwxr-xr-x. ...
drwxr-xr-x. ... /usr
lrwxrwxrwx. ... /usr/bin -> bin
drwxr-xr-x. ... /usr/lib64
metadata lines: 3
/usr
total ...
... (newest 5 entries)
... (largest 5 entries)
recent lines: 5
largest lines: 5
/tmp/nav-lab
/tmp/nav-lab
```

Exact entry names and sort order vary by system. On systems where `/usr/bin` is a real directory (not a symlink), the `lrwxrwxrwx` line will instead be `drwxr-xr-x`.

### i) Switches Table

| Token | Meaning |
|---|---|
| `ls -a` | All entries including `.` and `..` |
| `ls -A` | Almost all — hidden but no `.` / `..` |
| `ls -l` | Long listing |
| `ls -h` | Human-readable sizes (needs `-l` or `-s`) |
| `ls -d` | Directory entry itself |
| `ls -t` | Sort by mtime, newest first |
| `ls -r` | Reverse sort |
| `ls -S` | Sort by size, largest first |
| `head -n N` | First N lines |
| `tail -n N` | Last N lines |
| `tee FILE` | Print AND save stdout |
| `set -o noclobber` | Block `>` on existing files |
| `>\|` | Force overwrite under noclobber |
| `tr a-z A-Z` | Translate lowercase to uppercase |
| `< FILE` | Feed file into stdin |
| `chmod 644` | rw-r--r-- |
| `wc -w` | Count words |

### j) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | `ls -a` vs `-A` | Both show hidden; `-A` skips `.` and `..` |
|   | `ls -lh` | Long + readable sizes |
|   | `ls -ld` | Directory metadata, not contents |
|   | `ls -ltrh` | Recent files surfaced at the bottom |
|   | `ls -lhS` | Largest files first |
|   | `set -o noclobber` | Guard against `>` overwrites |
|   | `>\|` | Force overwrite when noclobber is on |
|   | `tee` | Capture without hiding output |
|   | `tr` | Stream translate |
|   | Exam pattern | Save start → jump → work → return |
| 🪤 **Trap Risk (T43)** | Getting stuck >10 min | If `ls -lhS` orders look wrong, do not chase it — most systems vary; skip the task, finish the lab, return later |

### k) 🧹 Cleanup

```bash
LAB=lab05
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
TOPIC:    ls flags + exam-style capstone
COMMANDS: ls -a/-A/-l/-h/-d/-t/-r/-S, noclobber, >|, tee, tr
TRAPS:    T43 (time-stuck reminder)
MISSED:   —
NEXT:     Lab 06 — Listing Files and SELinux Contexts (ls -Z, ps -eZ)
EOF
echo "Journal written: $(ls -la $JDIR)"

rm -rf /tmp/nav-lab
echo "exit was: $?"
```

### l) Troubleshoot Table

| Symptom | Fix |
|---|---|
| You see contents instead of metadata | Add `-d`: `ls -ld /usr` |
| `-h` seems to do nothing | Pair it with `-l` or `-s` |
| `.` and `..` clutter output | Use `ls -A` instead of `ls -a` |
| `>\|` rejected | Verify `set -o noclobber` was actually set |
| `cd -` shows `OLDPWD not set` | You forgot the initial `pwd > task03-start.txt; cd /usr` sequence |

### m) STOP

> **STOP — paste your output before declaring Lab 05 complete.**

### n) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| Journal for lab05 | `find /root/rhcsa_journal/lab05 -name done.txt` | Should list 3 files (task1-3) |
| All notes readable | `cat /root/rhcsa_journal/lab05/task*/notes.txt` | Reboot-proof study record |
| Sandbox removed | `test -d /tmp/nav-lab && echo LEFTOVER \|\| echo CLEAN` | Confirms `rm -rf` worked |

> **Reboot question:** "If we rebooted now, what would survive?" — Answer: everything under `/root/rhcsa_journal/`. Nothing under `/tmp`. That is exactly why journal writes go to `/root` and sandbox work goes to `/tmp`.

---

## 🪤 Trap Registry Update — End of Lab 05

| Trap ID | Category | Rehearsed? | If hit, repeat in |
|---|---|---|---|
| T41 | Meta / Strategy | ✅ | — |
| T43 | Meta / Strategy | ✅ | — |

Next lab (06) traps: **T01** (SELinux permissive instead of fixing context) · **T02** (semanage fcontext without restorecon).

---

## 🎓 What You Now Own

After this lab you can, on autopilot:

1. **Orient** with `pwd` before doing anything destructive.
2. **Reach any path** absolute or relative.
3. **Climb** with `..`, `../..`.
4. **Go home** with `cd`, `~`, `$HOME`.
5. **Toggle** with `cd -` / `$OLDPWD`.
6. **List with intent**: `-a`, `-A`, `-l`, `-h`, `-d`, `-t`, `-r`, `-S`.
7. **Save evidence** with `>`, `2>&1`, `tee`, `noclobber`, `>|`.
8. **Guard pipelines** with `pipefail` and `${PIPESTATUS[@]}`.
9. **Recover gracefully** with `cmd || fallback`.
10. **Journal** every task to `/root/rhcsa_journal/` so a reboot never costs you progress.
