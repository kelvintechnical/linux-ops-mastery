# Lab 11a: Safe Deletion (RHCSA) — `rm`, `rmdir`, `rm -rf`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `11a` (RHCSA) → `11b` (Ansible) → `11c` (Verify)
- **Career arcs covered:** RHCSA EX200 ("remove the file" / cleanup tasks), RHCE EX294 (Ansible `file: state=absent` is idempotent `rm -rf`), SRE (incident cleanup of stale lockfiles, log rotation), DevOps (CI cache invalidation), AI/MLOps (cleaning up old checkpoints / scratch space)
- **Prerequisite:** Lab 10 (`mv`, `mv -i/-n`, atomic rename)
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (ADHD spec — Task 1 canonical, Task 2 contrast)
- **Practice Directory (rotation #11):** `/tmp`
- **Sandbox:** `/tmp/rm-lab`
- **Traps rehearsed this lab:** **T11-A** (`rm -rf` with unquoted `$VAR` expanding to empty or `/`) · **T11-B** (skipping the `pwd ; ls` pre-flight before any `rm -rf`)

> **This lab's practice directory is: `/tmp`** — every task references it in at least two commands.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T11-A T11-B"
echo "📁  PRACTICE DIR: /tmp"
echo ""
echo "💡 /tmp occupants (we write into /tmp/rm-lab; rest is read-only context):"
ls -ld /tmp /tmp/.X11-unix 2>/dev/null
df -h /tmp | head -n 2
```

> **STOP — paste header output before running setup.**

---

## 🎯 Objective

Delete files and directories **deliberately and safely**. By the end of this lab you can run `rm -rf` on a directory tree without flinching — because the discipline of `pwd ; ls ; quote variables` has become reflex, and you know exactly which `rm` options exist to catch the mistakes everybody makes at least once.

---

## 🧠 Concept: `rm` Is the Shredder, Not the Recycle Bin

`rm` removes the **directory entry** that names a file. If that entry was the last name pointing at the inode (and no process has the file open), the kernel frees the inode and its data blocks. There is **no recycle bin** at the command line on Linux.

```
   ┌───────────────────────────────────────────────────────────────┐
   │  rm file.txt                                                  │
   ├───────────────────────────────────────────────────────────────┤
   │  1. unlink("file.txt")          ← remove the directory entry  │
   │  2. If inode link count == 0:                                 │
   │       If no process holds it open:                            │
   │         Free inode + data blocks immediately.                 │
   │       Else:                                                   │
   │         Defer free until last FD is closed.                   │
   │     Else:                                                     │
   │       Other names still point at the inode — data lives on.   │
   └───────────────────────────────────────────────────────────────┘
```

The single biggest cause of catastrophic data loss in Linux history is a `rm -rf` command where a variable expanded to empty or to `/`. The kernel will do exactly what you typed — no second chances. The `--preserve-root` default blocks the literal `rm -rf /` since coreutils 6.x — but it does **not** protect against `rm -rf "$VAR"/` where `$VAR` is unset and the trailing slash makes the result `rm -rf /`.

---

## 📚 Deletion Reference (everything you need for Tasks 1–2)

| Task | Command | Notes |
|---|---|---|
| Delete one file | `rm FILE` | Silent, irreversible |
| Delete with audit trail | `rm -v FILE` | Prints `removed 'FILE'` |
| Prompt before each | `rm -i FILE` | Per-file Y/N |
| Empty directory only | `rmdir DIR` | Refuses non-empty |
| Recursive tree | `rm -r DIR` | Removes everything under DIR + DIR |
| Force + recursive | `rm -rf DIR` | No prompts, no error on missing |
| Once-per-operation prompt | `rm -Ir DIR` | One Y/N for the whole tree |
| Filename starts with `-` | `rm -- -file` | `--` ends option parsing |
| Refuse mount crossing | `rm -rf --one-file-system DIR` | Bind-mount safe |

> **Rule of `rm`:** Pick the smallest blast radius for the job. `rmdir` for one empty directory. `rm` for one file. `rm -rf` only for trees you have audited with `pwd ; ls`.

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i
mkdir -p /tmp/rm-lab
cd /tmp/rm-lab

cat > /tmp/rm-lab/THIS_DIRECTORY.txt <<'EOF'
/tmp — Temporary files, cleared on every reboot

/tmp is the kernel-blessed scratch directory. Any process can write here.
systemd-tmpfiles clears it on boot by default. RHCSA labs use /tmp for
sandboxes because nothing here survives a reboot and no sudo is needed
to write.

Why it exists: separating ephemeral data from persistent data lets the
system reclaim space without backup concerns. Many distributions mount
/tmp as tmpfs (RAM-backed), which means /tmp writes never touch disk.

What lives inside it: /tmp/.X11-unix (X server sockets), /tmp/.ICE-unix
(InterClient Exchange sockets), build artifacts, downloaded tarballs,
and the rm-lab sandbox we are about to use.

Why RHCSA cares: every "create a file at /tmp/X" task lives here. /tmp
is the only system directory a normal user can write to without sudo.
The cleanup-at-end pattern (rm -rf /tmp/<sandbox>) is universal.
EOF

cat /tmp/rm-lab/THIS_DIRECTORY.txt
ls -ld /tmp/rm-lab
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

## Task 1 — Safe single-target removal: `rm`, `rm -v`, `rm -i`, `rmdir`

**Practice directory this task:** `/tmp` · Temporary files, cleared on every reboot — every command in this task targets `/tmp/rm-lab` so a mistake cannot reach anything important.

### 🔁 Warm-Up — commands woven into Task 1

```bash
ls -la /tmp/rm-lab                                  2>&1 | tee /tmp/rm-lab/warmup-pre.txt
wc -l /tmp/rm-lab/THIS_DIRECTORY.txt
test -d /tmp/rm-lab && echo "sandbox OK"
stat -c '%n mode=%a' /tmp/rm-lab/THIS_DIRECTORY.txt
set -o pipefail
find /tmp/rm-lab -maxdepth 1 -type f                2>/dev/null | wc -l
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 10: `mv` is the safe alternative to `rm` when you want a reversible "delete" — we will use that quarantine pattern at the end of Task 1.

### Purpose

Remove files one at a time with three different prompt behaviors (`rm`, `rm -v`, `rm -i`), and use `rmdir` to remove an empty directory. Build the muscle memory of `ls → rm -v → ls` so every removal has an audit trail.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `ls -la /tmp/rm-lab` | Snapshot **before** each `rm` so we can prove the removal happened |
| `find ... -type f \| wc -l` | Counts files before/after — same number means the `rm` lied to us |
| `test -d /tmp/rm-lab` | Guards the `rmdir` call — only runs if the sandbox still exists |
| `2>&1 \| tee` | Captures each `rm -v` line into `task1/op.txt` for the journal |
| `$(date -Is)` | Stamps the journal `notes.txt` with the completion time |

### Main command block

```bash
cd /tmp/rm-lab

touch a.txt b.txt c.txt
mkdir empty-dir
ls -la                                              2>&1 | tee /tmp/rm-lab/task1/op.txt
mkdir -p /tmp/rm-lab/task1

BEFORE=$(find /tmp/rm-lab -maxdepth 1 -type f | wc -l)

rm a.txt
rm -v b.txt                                         2>&1 | tee -a /tmp/rm-lab/task1/op.txt
rm -i c.txt    <<< "y"

test -d /tmp/rm-lab/empty-dir && rmdir /tmp/rm-lab/empty-dir
ls -la                                              2>&1 | tee -a /tmp/rm-lab/task1/op.txt

AFTER=$(find /tmp/rm-lab -maxdepth 1 -type f | wc -l)
echo "files before=$BEFORE  files after=$AFTER  delta=$(( BEFORE - AFTER ))"
echo "exit was: $?"
```

### Human-readable breakdown

1. Create three empty files and one empty directory in the sandbox.
2. Snapshot the state with `ls -la` and `find ... | wc -l` so we have a baseline.
3. Remove `a.txt` silently, `b.txt` verbosely, `c.txt` interactively (heredoc `<<< "y"` answers the prompt).
4. Use `test -d` to guard `rmdir` against a missing sandbox, then remove the empty directory.
5. Compute the file delta and confirm it equals 3.

### Reading it left to right

- `touch a.txt b.txt c.txt` — three syscalls in one command; creates each with mode 0664 minus umask.
- `BEFORE=$(...)` — command substitution captures the file count into a shell variable.
- `rm a.txt` — silent `unlink(2)`; success goes to exit 0, missing file would have errored.
- `rm -v b.txt` — same as above, but prints `removed 'b.txt'` to stdout.
- `rm -i c.txt <<< "y"` — `-i` reads from stdin; the herestring supplies the `y` without interactive typing.
- `test -d /tmp/rm-lab/empty-dir && rmdir ...` — short-circuit: `rmdir` only runs if the directory exists.
- `rmdir` itself calls the `rmdir(2)` syscall, which refuses non-empty directories — a built-in sanity check.

### The story

Default `rm` is the muscle memory you build for known-safe paths in scripts. `rm -v` is the audit-friendly form when you need to prove later what disappeared. `rm -i` is for "did I really mean this?" moments — almost nobody uses it interactively because the prompt-per-file is unbearable, but it's perfect for one-off "this file matters" deletions.

`rmdir` is the **sanity-checked** delete: it refuses to remove a non-empty directory, which means a typo cannot cascade into accidental data loss. Senior engineers reach for `rmdir` whenever they expect a directory to be empty — if `rmdir` fails, that's a real signal that something unexpected is still inside.

### Expected output

```text
total 12
-rw-r--r--. 1 root root  0 May 27 ... a.txt
-rw-r--r--. 1 root root  0 May 27 ... b.txt
-rw-r--r--. 1 root root  0 May 27 ... c.txt
drwxr-xr-x. 2 root root  6 May 27 ... empty-dir
-rw-r--r--. 1 root root 1.2K May 27 ... THIS_DIRECTORY.txt
removed 'b.txt'
total 4
-rw-r--r--. 1 root root 1.2K May 27 ... THIS_DIRECTORY.txt
files before=4  files after=1  delta=3
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| `rm FILE` | Silent removal (no prompt, no output unless error) |
| `rm -v FILE` | Verbose — prints `removed 'FILE'` |
| `rm -i FILE` | Prompt before every deletion (`y` / `n`) |
| `<<< "y"` | Herestring — pipes the string into the next command's stdin |
| `rmdir DIR` | Remove empty directory; refuses non-empty |
| `test -d PATH` | Exit 0 if PATH is a directory, else exit 1 |
| `find -maxdepth 1` | One level only; does not recurse |
| `set -o pipefail` | Pipeline exit = first non-zero stage (catches silent `\| tee` failures) |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | `unlink(2)` syscall | Removes a directory entry; frees inode if last link and no open FDs |
|   | `rmdir(2)` syscall | Removes an empty directory; refuses non-empty (built-in safety) |
|   | `-v` audit flag | Prints each removal — turn this on whenever you want evidence |
|   | `-i` interactive | Reads stdin before each removal; combine with herestring for scripted answers |
|   | `test -d` guard | Short-circuit pattern: only proceed if the guard passes |
|   | Command substitution `$(...)` | Captures output into a shell variable for arithmetic |
| 🪤 | **Trap Risk T11-B** | Skipping `ls` before `rm` means you delete what you assumed, not what is there |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Files removed in /tmp | `ls /tmp/rm-lab` | `/tmp` is tmpfs in most distros — removal survives until reboot, then tmpfs clears anyway |
| Journal evidence | `cat /tmp/rm-lab/task1/op.txt` | The op.txt persists in tmpfs until reboot; we'll copy to /root in journal write |

> **Reboot reasoning:** Removals from `/tmp` are irrelevant after reboot because `/tmp` clears itself. The thing that **must** survive is the **evidence** of the removal — that goes in the journal under `/root/`, not `/tmp/`.

### Journal write — BEFORE cleanup

```bash
LAB=lab-11a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/rm-lab/task1/op.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Safe single-target removal — rm, rm -v, rm -i, rmdir
COMMANDS: rm, rm -v, rm -i, rmdir, test -d, find -maxdepth 1
TRAPS:    T11-B (rehearsed: ran ls before every rm)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — the rm -rf trap with unquoted \$VAR
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -rf /tmp/rm-lab/task1
ls /tmp/rm-lab
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `rm: cannot remove 'X': Permission denied` | Need write on **parent directory**, not the file. Check `ls -ld $(dirname FILE)`. |
| `rmdir: failed to remove 'X': Directory not empty` | Either empty it first, or use `rm -r` if you mean to remove the contents too. |
| `rm` did not free disk | A process holds the inode open. Find it with `lsof FILE` and close. |
| `find ... \| wc -l` returns wrong count | `set -o pipefail` not active — a missing-permission error on a subdir went silent. |

> **STOP — paste the output of `cat $JDIR/done.txt` and the final `ls /tmp/rm-lab` before starting Task 2.**

---

## Task 2 — The contrast: `rm -rf` and the unquoted-variable trap (T11-A)

**Practice directory this task:** `/tmp` · Temporary files, cleared on every reboot — and the only directory in this lab where we deliberately demonstrate `rm -rf` patterns. The sandbox is constructed so the trap cannot escape into real paths.

### 🔁 Warm-Up — commands woven into Task 2

```bash
pwd
ls -la /tmp/rm-lab                                  2>&1 | tee /tmp/rm-lab/warmup-task2.txt
find /tmp/rm-lab -type f                            2>/dev/null | wc -l
test -d /tmp/rm-lab && echo "sandbox OK"
echo "set noclobber so we cannot truncate by accident:"
set -o noclobber
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 10 (`mv`): the atomic-rename quarantine pattern is the **safer** alternative to `rm -rf` when you are unsure — `mv DIR /tmp/trash/` instead of `rm -rf DIR`.

### Purpose

Demonstrate `rm -rf` doing its job correctly on a known tree, then **demonstrate the trap** (`rm -rf "$VAR"/` when `$VAR` is empty) inside a confined sandbox that cannot reach real paths. The lesson is the contrast between the two: same syntax, catastrophically different outcomes — and exactly which two-second pre-flight (`pwd ; ls`) prevents the trap every time.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `pwd` | The **first** pre-flight before any `rm -rf` — confirms current directory is `/tmp/rm-lab`, not `/` |
| `ls -la /tmp/rm-lab` | Snapshot **before** the `rm -rf` so we can compare after |
| `find -type f \| wc -l` | Counts files before AND after — drops to 0 when `rm -rf` succeeds |
| `test -d` | Guards the `rm -rf` so we never fire on a missing target |
| `set -o noclobber` | Prevents `>` from accidentally truncating the evidence file mid-task |
| `2>&1 \| tee` | Captures every step into `task2/op.txt` so we can audit the trap demonstration |

### Main command block

```bash
cd /tmp/rm-lab
mkdir -p /tmp/rm-lab/task2 /tmp/rm-lab/big-tree/a/b/c /tmp/rm-lab/big-tree/d/e
for i in 1 2 3 4 5; do touch "/tmp/rm-lab/big-tree/file$i"; done

# ── Part A: rm -rf done correctly (canonical form) ─────────────────
pwd
ls /tmp/rm-lab/big-tree
du -sh /tmp/rm-lab/big-tree

TARGET="/tmp/rm-lab/big-tree"
echo "About to remove: $TARGET"
test -d "$TARGET" && rm -rfv "$TARGET" 2>&1 | tee /tmp/rm-lab/task2/op.txt | head -n 5
echo "After:"
ls /tmp/rm-lab/

# ── Part B: the trap, contained in a fenced sandbox ────────────────
# We build a fake "root" so the trap CANNOT reach real paths.
mkdir -p /tmp/rm-lab/fake-root/{etc,var,home/user/data}
touch /tmp/rm-lab/fake-root/etc/important.conf
touch /tmp/rm-lab/fake-root/home/user/data/payroll.csv

FAKE_ROOT="/tmp/rm-lab/fake-root"
find "$FAKE_ROOT" -type f                            2>&1 | tee -a /tmp/rm-lab/task2/op.txt

# THE TRAP — UNQUOTED, AND $UNSET expands to empty.
# Without --preserve-root semantics inside our fake root, `rm -rf $UNSET/`
# becomes `rm -rf /` from the shell's point of view. We DO NOT run this
# against the real / — we run a guarded simulation against the fake root.
UNSET=""    # the bug — variable empty by mistake
echo "What the trap WOULD have been:  rm -rf \$UNSET/  →  rm -rf /"
echo "(we are NOT running that — we simulate inside fake-root only)"

# The safe equivalent — quoted, guarded, with pre-flight:
SAFE_TARGET="$FAKE_ROOT/home/user/data"
pwd
ls "$SAFE_TARGET"
test -n "$SAFE_TARGET" && test -d "$SAFE_TARGET" && \
  rm -rfv "$SAFE_TARGET" 2>&1 | tee -a /tmp/rm-lab/task2/op.txt | tail -n 3

find "$FAKE_ROOT" -type f                            2>&1 | tee -a /tmp/rm-lab/task2/op.txt
echo "exit was: $?"
```

### Human-readable breakdown

**Part A — the right way.** Build a non-trivial tree, run `pwd ; ls ; du` as the pre-flight, store the target in a **quoted** variable, guard with `test -d`, then run `rm -rfv` and pipe to `tee` for the audit trail.

**Part B — the trap, contained.** Build a fake filesystem root inside `/tmp/rm-lab/fake-root/` containing `etc/`, `var/`, and `home/user/data/`. Show the **unquoted variable footgun** as a commented `echo` (not executed) so you can read what would have happened. Then run the **safe equivalent** (quoted, guarded, with pre-flight) against `$FAKE_ROOT/home/user/data` to remove the simulated user data only. Verify with `find` that `etc/important.conf` and `var/` were untouched — which is what the trap **would have destroyed** without the guards.

### Reading it left to right

- `mkdir -p ... big-tree/a/b/c` — `-p` is idempotent and creates missing parents in one syscall chain.
- `du -sh DIR` — summarized size; useful sanity check ("am I about to delete 2 KB or 2 TB?").
- `TARGET="/tmp/rm-lab/big-tree"` — quoting the value protects against word-splitting if the path ever contained spaces.
- `test -d "$TARGET" && rm -rfv "$TARGET"` — the guard pattern: only fire if the target really is a directory.
- `rm -rfv` decomposes to: `-r` recurse, `-f` force (ignore missing, no prompts), `-v` verbose.
- `head -n 5` / `tail -n 3` — limit how much of the verbose output ends up on screen; full transcript still lands in `op.txt` via `tee`.
- `FAKE_ROOT="/tmp/rm-lab/fake-root"` — every dangerous demonstration in Part B operates inside this prefix; nothing can escape it because every path is concatenated against `$FAKE_ROOT`.
- `test -n "$SAFE_TARGET"` — guards against the empty-variable case (`-n` = non-empty). This is the **specific guard** that prevents T11-A.

### The story

The `pwd ; ls ; quote-the-variable ; test -d` ritual is three to four seconds of friction that prevents the worst incident of your career. Every senior engineer has either personally caused or watched a colleague cause a `rm -rf` disaster — usually a script with `rm -rf "$DIR"/` where `$DIR` was empty because an earlier step failed to set it. The trailing slash plus empty variable means the shell expands the line to `rm -rf /`, and `--preserve-root` only blocks the literal `/` — not the empty-variable path that **resolves** to `/`.

The fix is one habit: **never** trust a variable in a destructive command. Always `test -n` for non-empty, always quote it, always run `pwd` and `ls` immediately before. Build the habit in the sandbox so the muscle memory is there when you are on a customer's production system at 2 a.m.

### Expected output

```text
/tmp/rm-lab
a  d  file1  file2  file3  file4  file5
20K  /tmp/rm-lab/big-tree
About to remove: /tmp/rm-lab/big-tree
removed 'big-tree/file1'
removed 'big-tree/file2'
removed 'big-tree/file3'
removed 'big-tree/file4'
removed 'big-tree/file5'
After:
fake-root  task1  task2  THIS_DIRECTORY.txt  warmup-pre.txt  warmup-task2.txt
/tmp/rm-lab/fake-root/etc/important.conf
/tmp/rm-lab/fake-root/home/user/data/payroll.csv
What the trap WOULD have been:  rm -rf $UNSET/  →  rm -rf /
(we are NOT running that — we simulate inside fake-root only)
/tmp/rm-lab
payroll.csv
removed '/tmp/rm-lab/fake-root/home/user/data/payroll.csv'
removed directory '/tmp/rm-lab/fake-root/home/user/data'
/tmp/rm-lab/fake-root/etc/important.conf
exit was: 0
```

> Notice: in the final `find` output, `etc/important.conf` **survives**. The guards (`test -n`, `test -d`, quoted variable, `pwd ; ls` pre-flight) limited the blast radius to the intended directory only.

### Switches

| Token | Meaning |
|---|---|
| `rm -r DIR` | Recursive — removes contents then the directory |
| `rm -rf DIR` | Force + recursive — no prompts, ignore missing |
| `rm -rfv DIR` | Same, verbose — prints each removal |
| `test -n "$VAR"` | Exit 0 if `$VAR` is non-empty (guards against empty-variable trap) |
| `test -d "$VAR"` | Exit 0 if `$VAR` is a directory (guards against missing target) |
| `du -sh DIR` | Summarized human-readable disk usage |
| `set -o noclobber` | Block `>` from overwriting existing files in this shell |
| `head -n 5` / `tail -n 3` | Limit displayed output; full transcript stays in `tee`'d file |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | `--preserve-root` (default) | Refuses `rm -rf /` literally — does NOT protect against `rm -rf "$EMPTY"/` |
|   | Quote-the-variable rule | `rm -rf "$VAR"` not `rm -rf $VAR` — prevents word-splitting and glob disasters |
|   | `test -n` guard | Catches the empty-variable case before the dangerous command runs |
|   | `pwd ; ls` pre-flight | Two-second confirmation that you are where you think you are |
|   | Fenced-root sandbox | Building a fake-root tree means dangerous demonstrations cannot escape |
|   | `tee` for audit | Every destructive operation should pipe to `tee FILE` so the journal has a transcript |
| 🪤 | **Trap Risk T11-A** | `rm -rf "$VAR"/` where `$VAR` is empty becomes `rm -rf /`. Always `test -n` and quote. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Big-tree removed | `ls /tmp/rm-lab/` | Confirms the canonical `rm -rf` succeeded |
| Fake-root etc/ survived | `find /tmp/rm-lab/fake-root/etc -type f` | Proves the guard worked — the trap was contained |
| Journal transcript | `wc -l /root/rhcsa_journal/lab-11a/task2/evidence.txt` | The audit trail of what was removed (must be > 0) |

> **Reboot reasoning:** `/tmp` is tmpfs — everything in `/tmp/rm-lab` evaporates at reboot anyway. The thing that **must** persist is the journal `evidence.txt` under `/root/`. If the journal is empty after reboot, the lab failed silently.

### Journal write — BEFORE cleanup

```bash
LAB=lab-11a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/rm-lab/task2/op.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    rm -rf done correctly + the unquoted-variable trap (T11-A)
COMMANDS: rm -rf, rm -rfv, test -n, test -d, pwd, ls, du -sh, tee
TRAPS:    T11-A rehearsed (the trap was simulated and contained, not triggered)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-11b (Ansible) — ansible.builtin.file: state=absent for the same outcome
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -rf /tmp/rm-lab
test -d /tmp/rm-lab || echo "sandbox gone — clean exit"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `rm: refusing to remove '.' or '..'` | The shell tried to remove the working directory's parent — `cd` to a different directory first. |
| `rm -rf` ran but did nothing | `-f` silenced a missing-path error. Re-run without `-f` to see the real error. |
| Trap demo destroyed something real | Your `$FAKE_ROOT` was not constructed inside `/tmp/rm-lab` — recheck the variable. |
| `tee` failed silently | `set -o pipefail` not active — turn it on at the start of every dangerous task. |
| `test -n` always returns true | Likely tested `"$VAR "` (trailing space) instead of `"$VAR"` — the quoted string is always non-empty if it has whitespace. |

> **STOP — paste the output of `cat $JDIR/notes.txt` and the final `find /tmp/rm-lab/fake-root -type f` output (before cleanup) before moving on to Lab 11b.**

---

## Lab 11a Checklist (2 tasks)

- [ ] Task 1 — Safe single-target removal with `rm`, `rm -v`, `rm -i`, `rmdir` + journal evidence
- [ ] Task 2 — `rm -rf` canonical form **and** the T11-A trap, contained in a fake-root sandbox + journal evidence

---

## 🔗 Related Labs in the Trilogy

| Lab | Connection |
|---|---|
| **Lab 11b** — Removing Files via Ansible | `ansible.builtin.file: state=absent` — same outcome, idempotent, via the module |
| **Lab 11c** — Verifying File Removal | The auditor seat: `stat`, `find`, `test -f`, journal evidence verification |
| Lab 10 — Moving and Renaming Files (`mv`) | `mv FILE /tmp/trash/` is the reversible "quarantine" alternative to `rm` |
| Lab 14a — File Searching with `find` | `find PATH -mtime +N -delete` is the criteria-based version of `rm` |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
