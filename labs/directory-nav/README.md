# Lab 05: Directory Navigation - `cd`, `pwd`, `ls`

- **Series:** linux-ops-mastery - File Operations & Shell Fundamentals
- **Career arcs covered:** RHCSA EX200 path fluency, RHCE playbook path references, CKA config/log navigation, RHCA troubleshooting workflows
- **Prerequisite:** Lab 04 (`&>`, `2>&1`, `tee`, `/tmp` sandbox habits)
- **Time Estimate:** 35-50 minutes
- **Reduced task count:** 5 tasks only
- **Practice Directory (lab-wide rotation #05):** `/usr`
- **Sandbox:** `/tmp/nav-lab`

> **This lab's practice directory is: `/usr`** - every task references it at least twice.

---

## Objective

Build muscle memory for moving around Linux without losing your place. You will use `pwd`, `cd`, `ls`, absolute paths, relative paths, parent-directory shortcuts, home shortcuts, `cd -`, and practical listing flags in only five dense tasks.

---

## Concept: Linux Is One Tree

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

## Lab-Wide Setup - Run This Before Task 1

```bash
sudo -i
mkdir -p /tmp/nav-lab
cd /tmp/nav-lab

cat > /tmp/nav-lab/THIS_DIRECTORY.txt <<'EOF'
/usr - User programs, utilities, and their libraries

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

> **STOP - paste your output before Task 1.**

---

# The 5 Tasks

---

## Task 1 - Orient Yourself with `pwd`, `/usr`, and Basic Evidence Files

**Practice directory this task:** `/usr`

`/usr` holds package-managed programs, libraries, man pages, and shared data. You will use it as the anchor directory for navigation drills.

### Warm-Up - Commands from Previous Labs

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

Use `pwd` to prove your current location, list `/usr`, and save evidence that the sandbox and practice directory both exist.

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

- `cd /tmp/nav-lab` moves you into the sandbox.
- `pwd` prints the full current path.
- `ls /usr | head -n 10` lists `/usr`, then keeps the first 10 entries.
- `ls -ld /usr /tmp/nav-lab > task01-locations.txt 2>&1` records metadata for both directories and captures errors too.
- `$(ls /usr 2>/dev/null | wc -l)` counts `/usr` entries and hides any unexpected listing errors.
- `test -d` and `test -s` prove the directory and evidence file exist.

### Reading It Left to Right

`ls -ld /usr /tmp/nav-lab > task01-locations.txt 2>&1`

1. `ls` lists path metadata.
2. `-l` requests long format.
3. `-d` describes the directories themselves instead of their contents.
4. `/usr /tmp/nav-lab` are the two targets.
5. `>` sends stdout to `task01-locations.txt`.
6. `2>&1` sends stderr to the same file.

### The Story

Good admins orient first. Before editing, deleting, copying, or redirecting, run `pwd` and inspect the target. This prevents the classic mistake: running the right command in the wrong directory.

### Expected Output

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

Exact `/usr` contents vary by distribution.

### Switches Table

| Token | Meaning |
|---|---|
| `pwd` | Print working directory |
| `ls` | List directory contents |
| `ls -l` | Long listing with permissions, owner, size, and time |
| `ls -d` | List directory entry itself, not its contents |
| `head -n 10` | Show first 10 lines |
| `>` | Redirect stdout to file and truncate it |
| `2>&1` | Send stderr to stdout's current destination |
| `2>/dev/null` | Discard stderr |
| `test -d` | True if path is a directory |
| `test -s` | True if file exists and is non-empty |

### Concept Card

| Check | Concept | What it does |
|---|---|---|
|  | `pwd` | Answers "where am I?" |
|  | Absolute path | `/usr` works no matter where you stand |
|  | `ls -ld` | Directory metadata without dumping contents |
|  | `> file 2>&1` | Capture stdout and stderr together |
|  | `$(cmd)` | Command substitution; paste command output inline |
|  | `/dev/null` | Discard unwanted output |
|  | `$?` | Exit status of previous command |

### Cleanup

```bash
rm -f /tmp/nav-lab/task01-warmup.log /tmp/nav-lab/task01-warmup.copy /tmp/nav-lab/task01-locations.txt
echo "exit was: $?"
```

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `pwd` does not show `/tmp/nav-lab` | Run `cd /tmp/nav-lab` again |
| `ls: cannot access '/usr'` | You are on a damaged or nonstandard system; verify with `ls /` |
| `task01-locations.txt` is empty | Re-run the `ls -ld ... > file 2>&1` command |

> **STOP - paste your output before Task 2.**

---

## Task 2 - Move with Absolute and Relative Paths

**Practice directory this task:** `/usr`

`/usr` is ideal for this drill because `/usr/bin` is an absolute path and `bin` is a relative path once you are already inside `/usr`.

### Warm-Up - Commands from Previous Labs

```bash
cd /tmp/nav-lab
ls /usr/no-such-entry 2> task02-error.log
grep -c "No such" task02-error.log
find /usr -maxdepth 1 -type d 2>/dev/null | sort | tee task02-usr-dirs.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Practice the difference between absolute paths (`/usr/bin`) and relative paths (`bin` from inside `/usr`).

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

- `cd /usr` uses a full absolute path from root.
- `pwd` confirms the move.
- `ls -ld /usr /usr/bin` saves metadata for the parent and child directory.
- `cd bin` works only because you are currently standing in `/usr`.
- `ls -la .` lists the current directory, including dot entries.
- `tee` saves the listing while still printing it.

### Reading It Left to Right

`cd bin`

1. `cd` means change directory.
2. `bin` has no leading `/`, so it is relative.
3. Because current location is `/usr`, bash resolves it as `/usr/bin`.

`ls -la . | head -n 8 | tee /tmp/nav-lab/task02-relative.txt`

1. `ls -la .` lists current directory in long format, including hidden entries.
2. `| head -n 8` keeps the top 8 lines.
3. `| tee FILE` prints and saves those lines.

### The Story

Absolute paths are full addresses. Relative paths are directions from your current room. Both are correct, but only absolute paths are context-proof. On the exam, use absolute paths unless you intentionally set your context first.

### Expected Output

```text
/usr
/usr/bin
total ...
dr-xr-xr-x. ...
-rwxr-xr-x. ...
bin command count: 1000
```

Counts vary by system.

### Switches Table

| Token | Meaning |
|---|---|
| `cd /usr` | Move using an absolute path |
| `cd bin` | Move using a relative path |
| `ls -la` | Long listing plus hidden entries |
| `.` | Current directory |
| `tee FILE` | Print and save |
| `find -maxdepth 1` | Do not descend below the starting directory |
| `find -type d` | Match directories only |
| `sort` | Sort alphabetically |
| `grep -c` | Count matching lines |

### Concept Card

| Check | Concept | What it does |
|---|---|---|
|  | Absolute path | Starts with `/`; independent of `pwd` |
|  | Relative path | Does not start with `/`; depends on `pwd` |
|  | `.` | Current directory |
|  | `ls -la` | Long list plus hidden entries |
|  | `tee` | Save a copy without hiding output |
|  | `2>` | Capture stderr only |
|  | `find -type d` | Directory-only search |

### Cleanup

```bash
cd /tmp/nav-lab
rm -f task02-error.log task02-usr-dirs.txt task02-absolute.txt task02-relative.txt
echo "exit was: $?"
```

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `cd bin` fails | You were not in `/usr`; run `pwd`, then `cd /usr` |
| `ls -la .` floods the screen | Keep the `| head -n 8` limiter |
| Saved file missing | Confirm the destination path starts with `/tmp/nav-lab/` |

> **STOP - paste your output before Task 3.**

---

## Task 3 - Move Up with `..`, Go Home, and Toggle with `cd -`

**Practice directory this task:** `/usr`

`/usr/share/doc` gives you a safe nested path for practicing `..`, `../..`, `$HOME`, and `cd -`.

### Warm-Up - Commands from Previous Labs

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

Practice the navigation shortcuts that recover you when you are deep in a directory tree: `..`, `../..`, `~`, `$HOME`, plain `cd`, and `cd -`.

### Main Command Block

```bash
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

### Human-Readable Breakdown

- `cd /usr/share` starts in a known nested directory.
- `cd ..` moves one level up, from `/usr/share` to `/usr`.
- `cd share/doc 2>/dev/null || cd /usr/share` tries a relative path, and falls back safely if `doc` is missing.
- `cd ../..` moves two levels up.
- `cd "$HOME"` returns to your user's home.
- `cd /usr` creates an `$OLDPWD` relationship.
- `cd -` toggles back to the previous directory.

### Reading It Left to Right

`cd share/doc 2>/dev/null || cd /usr/share`

1. `cd share/doc` tries to move into a relative path.
2. `2>/dev/null` hides the error if `/usr/share/doc` is absent.
3. `||` runs the fallback only if the first `cd` failed.
4. `cd /usr/share` returns to a known good location.

### The Story

Navigation is not a straight line. Real troubleshooting means bouncing between configs, logs, and home directories. `..`, `$HOME`, and `cd -` are the shell's recovery handles.

### Expected Output

```text
/usr/share
/usr
/usr/share/doc
/usr
/root
/root
```

If you are not root, your home path may be `/home/ec2-user` or another user path. If `/usr/share/doc` is not installed, the fallback returns you to `/usr/share`.

### Switches Table

| Token | Meaning |
|---|---|
| `..` | Parent directory |
| `../..` | Two parent levels up |
| `~` | Shell shorthand for home |
| `$HOME` | Environment variable containing home path |
| `cd` | With no argument, go home |
| `cd -` | Toggle to previous directory (`$OLDPWD`) |
| `2>/dev/null` | Suppress error messages |
| `||` | Run next command only if previous failed |
| `${PIPESTATUS[@]}` | Exit status for each pipeline stage |
| `set -o pipefail` | Pipeline fails if any stage fails |

### Concept Card

| Check | Concept | What it does |
|---|---|---|
|  | `..` | Move to parent |
|  | `$HOME` | Home directory variable |
|  | `cd -` | Swap current and previous directories |
|  | `|| fallback` | Recovery path on failure |
|  | `2>/dev/null` | Silence expected errors |
|  | `pipefail` | Make pipeline failures visible |

### Cleanup

```bash
cd /tmp/nav-lab
rm -f task03-share-head.txt
echo "exit was: $?"
```

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `cd -` says `OLDPWD not set` | Run at least one normal `cd` first |
| `cd share/doc` fails | Some minimal systems do not install docs; use `/usr/share` fallback |
| You end up at `/` | You used too many `..`; run `cd /tmp/nav-lab` to reset |

> **STOP - paste your output before Task 4.**

---

## Task 4 - Read Directory Listings with `ls -a`, `ls -A`, `ls -l`, `ls -h`, and `ls -d`

**Practice directory this task:** `/usr`

`/usr` has normal directories, symlinks, large trees, and stable metadata, making it a safe place to learn `ls` flags.

### Warm-Up - Commands from Previous Labs

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

Compress the most important `ls` viewing flags into one task: hidden entries, long listings, human-readable sizes, and directory metadata.

### Main Command Block

```bash
cd /tmp/nav-lab
ls -a /usr | head -n 8
ls -A /usr | head -n 8
ls -lh /usr | head -n 8 | tee task04-usr-long.txt
ls -ld /usr /usr/bin /usr/lib64 > task04-dir-metadata.txt 2>&1
cat task04-dir-metadata.txt
echo "metadata lines: $(wc -l < task04-dir-metadata.txt)"
```

### Human-Readable Breakdown

- `ls -a /usr` shows every entry, including `.` and `..`.
- `ls -A /usr` shows hidden entries but excludes `.` and `..`.
- `ls -lh /usr` shows long format with readable sizes.
- `ls -ld /usr /usr/bin /usr/lib64` shows metadata for those directories themselves.
- `wc -l < file` counts lines without printing the filename.

### Reading It Left to Right

`ls -ld /usr /usr/bin /usr/lib64 > task04-dir-metadata.txt 2>&1`

1. `ls` lists.
2. `-l` requests metadata columns.
3. `-d` prevents expansion into directory contents.
4. The three `/usr` paths are the targets.
5. `>` saves stdout.
6. `2>&1` also saves stderr.

### The Story

Plain `ls` is for quick scans. `ls -l` is for evidence. `ls -ld` is the exam command for verifying a directory's own permissions. `ls -A` is safer than `ls -a` in scripts because it excludes `.` and `..`.

### Expected Output

```text
.
..
bin
etc
games
...
total ...
drwxr-xr-x. ...
drwxr-xr-x. ... /usr
lrwxrwxrwx. ... /usr/bin -> bin
drwxr-xr-x. ... /usr/lib64
metadata lines: 3
```

Some systems show `/usr/bin` as a real directory rather than a symlink.

### Switches Table

| Token | Meaning |
|---|---|
| `ls -a` | All entries, including `.` and `..` |
| `ls -A` | Almost all entries, excluding `.` and `..` |
| `ls -l` | Long listing |
| `ls -h` | Human-readable sizes when paired with `-l` |
| `ls -d` | Describe directory entries themselves |
| `wc -w` | Count words |
| `tr a-z A-Z` | Translate lowercase to uppercase |
| `< FILE` | Feed file into stdin |
| `chmod 644` | Owner read/write, group read, other read |

### Concept Card

| Check | Concept | What it does |
|---|---|---|
|  | `ls -a` | Shows dot entries |
|  | `ls -A` | Dotfiles without `.` and `..` |
|  | `ls -lh` | Metadata with readable sizes |
|  | `ls -ld` | Directory metadata, not contents |
|  | `< file` | Redirect stdin |
|  | `tr` | Transform text streams |

### Cleanup

```bash
rm -f /tmp/nav-lab/task04-note.txt /tmp/nav-lab/task04-note.upper /tmp/nav-lab/task04-usr-long.txt /tmp/nav-lab/task04-dir-metadata.txt
echo "exit was: $?"
```

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| You see directory contents instead of metadata | Add `-d`: `ls -ld /usr` |
| `-h` seems to do nothing | Pair it with `-l` or `-s` |
| `.` and `..` clutter output | Use `ls -A` instead of `ls -a` |

> **STOP - paste your output before Task 5.**

---

## Task 5 - Exam-Style Navigation: Find Recent and Large Files, Then Return Cleanly

**Practice directory this task:** `/usr`

This capstone combines navigation, listing, sorting, piping, counting, saving, and cleanup while repeatedly touching `/usr`.

### Warm-Up - Commands from Previous Labs

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

Complete a compact RHCSA-style task: move to `/usr`, list recent entries, list large entries, verify directory metadata, save evidence, and return to the prior directory.

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

- `pwd > task05-start.txt` saves your starting directory.
- `cd /usr` moves to the practice directory.
- `ls -ltrh | tail -n 5` shows the newest entries at the bottom and captures the final five.
- `ls -lhS | head -n 5` shows the largest entries first.
- `ls -ld /usr /usr/bin /usr/lib64 > file 2>&1` captures directory metadata plus any errors.
- `cd -` returns to the previous directory.
- Final `pwd` and `cat task05-start.txt` prove you returned cleanly.

### Reading It Left to Right

`ls -ltrh | tail -n 5 | tee /tmp/nav-lab/task05-recent.txt`

1. `ls` lists `/usr` because you are standing there.
2. `-l` long listing.
3. `-t` sort by modification time.
4. `-r` reverse the time sort, putting newest entries near the bottom.
5. `-h` human-readable sizes.
6. `| tail -n 5` keeps the last five lines.
7. `| tee FILE` displays and saves the evidence.

### The Story

This is what exam tasks feel like. They do not say "run these flags." They say "go there, identify what changed, verify permissions, and save proof." Your job is to compose the command chain.

### Expected Output

```text
/usr
drwxr-xr-x. ...
...
recent lines: 5
largest lines: 5
/tmp/nav-lab
/tmp/nav-lab
```

Exact file names and sort order vary by system.

### Switches Table

| Token | Meaning |
|---|---|
| `ls -l` | Long listing |
| `ls -t` | Sort by modification time, newest first |
| `ls -r` | Reverse sort |
| `ls -h` | Human-readable sizes |
| `ls -S` | Sort by size, largest first |
| `tail -n 5` | Last five lines |
| `head -n 5` | First five lines |
| `tee FILE` | Display and save |
| `cd -` | Return to previous directory |
| `set -o noclobber` | Prevent accidental overwrite with `>` |
| `>|` | Force overwrite under noclobber |

### Concept Card

| Check | Concept | What it does |
|---|---|---|
|  | `ls -ltrh` | Newest-at-bottom troubleshooting listing |
|  | `ls -lhS` | Largest-first disk-triage listing |
|  | `tee` | Evidence capture while still showing output |
|  | `cd -` | Clean return to previous directory |
|  | `noclobber` | Prevent accidental file overwrite |
|  | `>|` | Force overwrite intentionally |

### Cleanup

```bash
cd /tmp
rm -rf /tmp/nav-lab
rm -f /root/task05-start.txt
echo "exit was: $?"
exit
```

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `cd -` prints `OLDPWD not set` | You did not run a prior `cd`; run `cd /usr` then `cd -` |
| Recent and largest lists show fewer than 5 lines | Minimal system; use `/usr/bin` instead |
| `noclobber` blocks later labs | Run `set +o noclobber` before continuing |
| Cleanup removes the sandbox | Correct - Task 5 is the final task |

> **STOP - paste your output. Lab 05 complete.**

---

## Navigation Decision Guide

```text
Where am I?                 -> pwd
Where am I physically?      -> pwd -P
Go by full address          -> cd /absolute/path
Go nearby                   -> cd relative/path
Go up one                   -> cd ..
Go home                     -> cd, cd ~, or cd "$HOME"
Go back                     -> cd -
List visible entries        -> ls
List hidden entries         -> ls -a or ls -A
List metadata               -> ls -l
List directory itself       -> ls -ld /path
Newest at bottom            -> ls -ltrh
Largest first               -> ls -lhS
```

---

## Lab Checklist (5 Tasks Only)

- [ ] 01 Orient with `pwd`, `/usr`, and evidence files
- [ ] 02 Move with absolute and relative paths
- [ ] 03 Move up with `..`, go home, and toggle with `cd -`
- [ ] 04 Read directory listings with `ls -a`, `ls -A`, `ls -l`, `ls -h`, `ls -d`
- [ ] 05 Exam-style navigation capstone with recent files, large files, metadata, and return

---

## Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Forgetting leading `/` | `cd: usr: No such file or directory` from the wrong place | Use `cd /usr` |
| Running relative paths from the wrong directory | Command works yesterday, fails today | Run `pwd` first |
| Using `ls -l /usr` when you wanted `/usr` metadata | Dumps contents | Use `ls -ld /usr` |
| Confusing `-a` and `-A` | Scripts see `.` and `..` | Use `-A` in scripts |
| Too many `..` | You land at `/` | Reset with `cd /tmp/nav-lab` |

---

## Related Labs

| Lab | Connection |
|---|---|
| Lab 04 - Capture Both Output and Error | Uses `2>&1`, `tee`, and `/tmp` evidence files |
| Lab 06 - Listing Files and SELinux Contexts | Extends `ls -l` into `ls -Z` |
| Lab 08 - Copying Files and Directories | Requires absolute and relative path fluency |
| Lab 10 - Moving and Renaming Files | Same path rules, higher consequence |
| Lab 11 - Safe Deletion | `pwd` before `rm -rf` prevents disasters |

---

## Author

**Kelvin R. Tobias** - [kelvinintech.com](https://kelvinintech.com) - [GitHub](https://github.com/kelvintechnical) - [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
