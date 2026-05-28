# Lab 01a: Standard Output Redirection (RHCSA) — `>`, `>>`, `cat`

- **Series:** linux-ops-mastery — Shells, Terminals & Redirection
- **Trilogy:** `01a` (RHCSA hand-typed) → ⛔ no `01b` (Section 18 boundary — `>`/`>>` has no honest Ansible module) → `01c` (Verify capstone — audit + persistence)
- **Career arcs covered:** RHCSA EX200 (every "save the output to…" task), RHCE EX294 (Ansible `shell:` + `register:` mirrors `>` semantics), SRE (incident-evidence capture without losing prior log lines), DevOps (CI/CD artifact files), AI/MLOps (training-script stdout → experiment log)
- **Prerequisite:** Basic shell familiarity — you can `ls`, `pwd`, `cat`, and you know what a file path is
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = `>` and `>>` basics + `sudo -u ${USER}` weave · Task 2 = multi-source report + T01-B trap proof + `sudo -u ${USER}` weave)
- **Practice Directory (rotation #01):** `/tmp`
- **Sandbox (Tier B per Section 1.5):** `/tmp/lab01a` with `USER=labuser_01_stdout`, `GROUP=labgrp_01_stdout`, `USER_HOME=/tmp/lab01a/home_labuser_01_stdout`. Built in Lab-Wide Setup; torn down + audited in **Lab Closeout** after Task 2.
- **Traps rehearsed this lab:** **T01-A** (`>` truncates BEFORE the command runs — pre-existing content lost) · **T01-B** (unquoted space in redirect target corrupts command parsing) · **T41** (skipping the destroy-restore drill — done in 01c) · **T44** (cleanup-left-orphan-user — Lab Closeout audit block proves no residue)

> **This lab's practice directory is: `/tmp`** — every task writes artifacts here, mirrors real sysadmin capture patterns (`/tmp` is the canonical "safe scratch space" on exam VMs).

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T01-A T01-B T41"
echo "📁  PRACTICE DIR: /tmp"
echo ""
echo "💡 /tmp context (our write target):"
ls -ld /tmp
df -h /tmp 2>/dev/null | tail -n 1
echo "Shell version: $BASH_VERSION"
```

> **STOP — paste header output before running setup.**

---

## Objective

Make output redirection a reflex. By the end of this lab you can:

1. Send the stdout of any command to a file with `>` (overwrite/create) or `>>` (append).
2. Read it back with `cat` and confirm what landed on disk matches what was on screen.
3. Build a multi-source composite file by mixing `>` and `>>` in the correct order.
4. Survive the two traps that cost exam points: **truncate-before-run** (T01-A) and **unquoted space in redirect target** (T01-B).

Every RHCSA task that says *"save the output of X to /root/Y"* reduces to a `>` or `>>` decision plus a `cat` verification. You will own both.

---

## Concept: stdout Is a Stream, Not a Screen

When a command "prints to the screen," what actually happens is the kernel writes bytes to **file descriptor 1** of the process. The terminal happens to be connected to FD 1 by default, but FD 1 is a *handle* — point it at a file and the bytes land in the file instead.

```
   ┌─────────────────────────────────────────────────────┐
   │   Your command (ls, ps, cat, date, hostname, ...)   │
   ├─────────────────────────────────────────────────────┤
   │   FD 0  stdin   ← keyboard (default)                │
   │   FD 1  stdout  → terminal  (default) ◄─ retarget   │
   │   FD 2  stderr  → terminal  (default)               │
   └─────────────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────────┐
        │                           │
   `> file`                    `>> file`
   open O_TRUNC then write      seek to EOF then write
   destroys existing content    preserves existing content
   creates file if missing      creates file if missing
```

The shell sets up the redirection **before** the command starts. That means `cmd > existing.txt` empties `existing.txt` first, then runs `cmd`. If `cmd` fails immediately, you've lost the file's content for nothing. This is **trap T01-A** and it costs exam points every year.

---

## Redirection Reference

| Operator / Command | What it does                                          | Use when…                           |
|--------------------|-------------------------------------------------------|--------------------------------------|
| `cmd > file`       | Redirect stdout — overwrite (or create) target file   | First write of a fresh artifact      |
| `cmd >> file`      | Redirect stdout — append (or create) target file      | Adding to logs, notes, reports       |
| `cmd > /dev/null`  | Discard stdout                                        | Suppress noisy output                |
| `set -o noclobber` | Refuse `>` on existing files (safety net)             | Scripts touching production files    |
| `cat FILE`         | Print file contents to stdout                         | Verify what `>` / `>>` wrote         |
| `wc -l FILE`       | Count newlines in a file                              | Verify append didn't truncate        |
| `wc -l < FILE`     | Count lines; filename absent from output              | Clean count for variable capture     |

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

Per the ADHD prompt's Section 1.5, every lab builds a sandbox dir + a local group + a local user under `/tmp` so the user/group/file/directory reflex compounds across every objective on the exam. The block is **idempotent** — the `getent` guards make it safe to re-run if you resume mid-lab.

```bash
sudo -i

export LAB_NUM=01
export LAB_SLUG=stdout
export SANDBOX=/tmp/lab01a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-01a/task1
mkdir -p /root/rhcsa_journal/lab-01a/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd \
    -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id     "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
getent group  "${GROUP}"
getent passwd "${USER}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the `id` line, the two `ls -ld` lines, and both `getent` lines before Task 1. If `${USER}` already exists from a prior run, the `getent` guard makes the create a no-op — that is correct, not a bug.**

> **Why under `/tmp`, not `/home`?** Section 1.5's `useradd -M` forbids `/home/<name>`. The user's `$HOME` lives under the sandbox so `userdel -r ${USER}` in **Lab Closeout** is guaranteed to clean it up. Putting it in `/home` would leak the home dir if `userdel` runs without `-r`.

---

## Task 1 — Truncate-write with `>`, append with `>>`

**Practice directory this task:** `/tmp/lab01a` — we create and verify files here, mirroring exam-day "save output to /root/answer.txt" tasks.

### Warm-Up

```bash
echo "hello from stdout"                               2>&1 | tee /tmp/lab01a/warmup.txt
date
hostname
ls /tmp/lab01a
cat /etc/hostname
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from setup: `mkdir -p` underlies every journal write in this series.

### Purpose

Use `>` to create a fresh capture file, verify it with `cat` and `wc -l`, then use `>>` to append lines to the same file without losing prior content. Prove the count grows with each append. Then prove `>` starts over from zero (Task 1's capstone moment).

### WEAVE TRACE

| Warm-up / setup command  | Role inside Task 1                                                   |
|--------------------------|----------------------------------------------------------------------|
| `echo "hello ..."`       | Same `echo` command we'll redirect in the main block                 |
| `date`                   | Date output is one source we'll capture into the report file         |
| `hostname`               | Hostname output is the second source we'll capture                   |
| `ls /tmp/lab01a`         | Pre-flight: confirms sandbox exists before any `>` writes            |
| `cat /etc/hostname`      | Shows `cat` reading a file — mirrors the post-write verification     |
| `set -o pipefail`        | Defensive habit; ensures a failed sub-command in a pipe is visible   |
| `${USER}` / `${GROUP}` (from Lab-Wide Setup) | Part D writes a file *as* `${USER}` via `sudo -u`; we verify ownership with `stat -c '%U:%G'` — exercises Tier B (user/group/file/dir) instead of just printing the user's name |

### Main command block

```bash
TASKLOG=/tmp/lab01a/task1.txt

# ── Part A: > creates file, >> appends ───────────────────────────────
echo "Line 1: first write" > /tmp/lab01a/output.txt

echo "after first >"
wc -l /tmp/lab01a/output.txt                           2>&1 | tee $TASKLOG

echo "Line 2: first append"  >> /tmp/lab01a/output.txt
echo "Line 3: second append" >> /tmp/lab01a/output.txt

echo "after two >>s"
cat /tmp/lab01a/output.txt                             2>&1 | tee -a $TASKLOG
wc -l /tmp/lab01a/output.txt                           2>&1 | tee -a $TASKLOG

# ── Part B: > resets (T01-A demonstration) ───────────────────────────
echo "Line overwrites everything" > /tmp/lab01a/output.txt
echo "after second >"
cat /tmp/lab01a/output.txt                             2>&1 | tee -a $TASKLOG
wc -l /tmp/lab01a/output.txt                           2>&1 | tee -a $TASKLOG

# ── Part C: noclobber safety net ─────────────────────────────────────
set -o noclobber
echo "protected" > /tmp/lab01a/precious.txt
echo "will fail" > /tmp/lab01a/precious.txt 2>&1 | head -n 1 | tee -a $TASKLOG || true
set +o noclobber
cat /tmp/lab01a/precious.txt                           2>&1 | tee -a $TASKLOG

# ── Part D: write a file AS ${USER} via sudo -u (Tier B weave) ────────
# Real work as the lab user — proves ${USER}/${GROUP}/${USER_HOME} all wire
# up correctly. The file ownership is the verification, not the echo output.
sudo -u "${USER}" bash -c \
    'echo "owned-by-$(whoami)-at-$(date -Is)" > '"${USER_HOME}"'/task1-asuser.txt'

# Verify ownership lands on ${USER}:${GROUP}, not root:root
stat -c '%U:%G %a %n' "${USER_HOME}/task1-asuser.txt"  | tee -a $TASKLOG
cat                  "${USER_HOME}/task1-asuser.txt"  | tee -a $TASKLOG

# Cross-check: root cannot pretend to be ${USER}'s file owner without sudo -u
echo "wrote-as-$(whoami)" > "${SANDBOX}/task1-asroot.txt"
stat -c '%U:%G %a %n' "${SANDBOX}/task1-asroot.txt"    | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

- `echo "Line 1: first write"` — generates a one-line string on stdout
- `> /tmp/lab01a/output.txt` — shell opens the file with `O_TRUNC` (truncate) first, then runs `echo`. New file created with one line.
- `>> /tmp/lab01a/output.txt` — shell opens the file with `O_APPEND`, seeks to EOF, writes. Existing lines untouched.
- `wc -l` counts newlines — 1 after first write, 3 after two appends, 1 after the overwrite.
- `set -o noclobber` — shell refuses `>` on existing files, prints "cannot overwrite existing file". Use `>|` to override explicitly.
- `sudo -u "${USER}" bash -c '... > FILE'` — runs the entire redirected shell as `${USER}` so the file lands under `${USER}:${GROUP}`. `stat -c '%U:%G'` prints the owner+group as proof. Compare the user-owned file (`task1-asuser.txt`) to the root-owned one (`task1-asroot.txt`) — that contrast IS the Tier B lesson.

### Reading it left to right

```
echo "Line 1: first write"   >   /tmp/lab01a/output.txt
│                             │   │
│                             │   └─ destination file (opened O_TRUNC before echo runs)
│                             └─ redirect stdout (FD 1)
└─ command that writes to stdout
```

### The story

`>` and `>>` are not "shell tricks." They are the original design of how a Unix program talks to the outside world, dating to 1969. Ken Thompson's insight: every program writes to FD 1; the **shell** decides what FD 1 is connected to. That single design decision created redirection, pipes, `tee`, and the entire composable-tools philosophy.

The reason RHCSA tests this so heavily: every grader script reads files, not screens. If your answer scrolled past instead of landing in `/root/answer.txt`, you scored zero on a question you understood perfectly. Reflex matters more than knowledge here.

### Expected output

After Part A first `>` (`wc -l`):
```
1 /tmp/lab01a/output.txt
```

After Part A two `>>`s (`cat`):
```
Line 1: first write
Line 2: first append
Line 3: second append
```

After Part B second `>` (`cat`):
```
Line overwrites everything
```

Part C (noclobber):
```
bash: /tmp/lab01a/precious.txt: cannot overwrite existing file
protected
```

Part D (Tier B sudo -u weave):
```
labuser_01_stdout:labgrp_01_stdout 644 /tmp/lab01a/home_labuser_01_stdout/task1-asuser.txt
owned-by-labuser_01_stdout-at-2026-05-28T08:54:13-04:00
root:root 644 /tmp/lab01a/task1-asroot.txt
```

### Switches

| Token            | Meaning                                                          |
|------------------|------------------------------------------------------------------|
| `>`              | Redirect stdout — truncate-write (or create)                     |
| `>>`             | Redirect stdout — append-write (or create)                       |
| `wc -l`          | Count newlines                                                   |
| `wc -l < FILE`   | Count without filename in output                                  |
| `set -o noclobber`| Refuse `>` on existing files                                    |
| `set +o noclobber`| Allow `>` to clobber again                                      |
| `2>&1 \| tee`    | Capture + display (standard lab transcript pattern)              |
| `sudo -u USER bash -c '...'` | Run a whole quoted shell pipeline as USER — required when `>` redirect must apply with that user's identity |
| `stat -c '%U:%G %a %n' FILE` | Print owner, group, mode, and name in one line — the Tier B verification reflex |

### Concept Card

| Concept | What it does |
|---|---|
| `>` | Open-truncate-write FD 1; **destroys existing content** |
| `>>` | Open-append-write FD 1; **preserves existing content** |
| Both create file if missing | No error if the file doesn't exist yet |
| noclobber + `>` | Shell refuses the overwrite — safe script default |
| `2>&1 \| tee FILE` | Transcript pattern: shows on screen AND saves to file |
| `sudo -u "${USER}" bash -c '... > FILE'` | Tier B weave: run the redirect as the lab user; ownership lands on `${USER}:${GROUP}` |
| `stat -c '%U:%G %a %n' FILE` | Print owner/group/mode/name — the canonical Tier B ownership check |
| **🪤 Trap Risk T01-A** | `cmd > existing.txt` empties the file BEFORE `cmd` runs. If `cmd` crashes, original data is gone. **Fix:** `ls -l FILE` first; use `>>` if file has content you need. |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| > overwrites (Part B) | `wc -l /tmp/lab01a/output.txt` returns 1 | Proves truncate happened |
| >> appended (Part A) | `cat` showed 3 lines before Part B | Proves append preserved earlier lines |
| noclobber blocked clobber | `cat /tmp/lab01a/precious.txt` returns "protected" | Proves safety net works |
| Task log written | `wc -l /tmp/lab01a/task1.txt` | Evidence file exists |
| `${USER}` owns the sudo-u file | `stat -c '%U:%G' "${USER_HOME}/task1-asuser.txt"` returns `labuser_01_stdout:labgrp_01_stdout` | Proves Tier B sandbox actually wired up — Lab Closeout depends on it |
| Root-owned contrast file | `stat -c '%U:%G' /tmp/lab01a/task1-asroot.txt` returns `root:root` | Catches the "I forgot the sudo -u" mistake at the point of contrast |

> **Reboot note:** `/tmp` is RAM-backed on most RHEL 9 hosts (`tmpfs`). Files here do NOT survive reboot. The journal write below copies artifacts to `/root/rhcsa_journal/` which IS on the root partition and survives reboot.

### Journal write

```bash
LAB=lab-01a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab01a/task1.txt              "$JDIR/evidence.txt"
cp "${USER_HOME}/task1-asuser.txt"    "$JDIR/task1-asuser.txt"
cp /tmp/lab01a/task1-asroot.txt       "$JDIR/task1-asroot.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
LAB_USER: ${USER}
LAB_GROUP: ${GROUP}
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    > overwrites (O_TRUNC); >> appends (O_APPEND); both create if missing; sudo -u places ownership on the lab user
COMMANDS: >, >>, wc -l, cat, set -o noclobber, sudo -u ${USER} bash -c, stat -c '%U:%G %a %n'
TRAPS:    T01-A rehearsed (Part B: second > reset file to 1 line)
TIER B:   task1-asuser.txt owned by ${USER}:${GROUP}; task1-asroot.txt owned by root:root
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — multi-source report + T01-B filename trap + sudo -u report append
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup (per-task — leaves Tier B sandbox intact)

```bash
# Per-task cleanup removes ONLY the files Task 1 created.
# The Tier B sandbox/user/group must survive into Task 2 — Lab Closeout
# (after Task 2) runs the bulletproof Section 6 teardown with the audit block.
rm -f /tmp/lab01a/output.txt /tmp/lab01a/precious.txt /tmp/lab01a/warmup.txt \
      /tmp/lab01a/task1-asroot.txt
rm -f "${USER_HOME}/task1-asuser.txt"

# Sanity-check that ${USER}/${GROUP}/${SANDBOX} still exist for Task 2
getent passwd "${USER}"   >/dev/null && echo "✅ ${USER} still present"
getent group  "${GROUP}"  >/dev/null && echo "✅ ${GROUP} still present"
test -d       "${SANDBOX}"           && echo "✅ ${SANDBOX} still present"

ls /tmp/lab01a
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `wc -l` shows 0 after `>` | The command before `>` failed — check the command independently |
| `>>` seems to reset the file | You typed `>` instead of `>>` — T01-A happened |
| `cannot overwrite` after turning off noclobber | You turned it off as `set -o noclobber` — use `set +o noclobber` (`+` disables, `-` enables) |
| Line count is off by 1 | Some commands (like `printf`) don't emit a trailing newline; `echo` always does |

> **STOP — paste the `wc -l` and `cat` outputs before Task 2.**

---

## Task 2 — Multi-source report file (the exam pattern)

**Practice directory this task:** `/tmp/lab01a` — we build a composite system report, the pattern used in real exam "capture diagnostic output" tasks.

### Warm-Up

```bash
ls -la /tmp/lab01a                                     2>&1 | tee /tmp/lab01a/warmup2.txt
hostname
date
uptime
id
uname -r
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: the `2>&1 | tee` transcript pattern — now standard for every warm-up block.

### Purpose

Build a composite system report by using `>` once (header, clean start) then `>>` for every subsequent source. Verify header and footer survive with `head -1` and `tail -1`. Demonstrate T01-B (unquoted space in redirect target corrupts the command). Finalize the report with a line count and hand the evidence to the journal.

### WEAVE TRACE

| Warm-up / setup command | Role inside Task 2                                                  |
|-----------------|---------------------------------------------------------------------|
| `ls -la /tmp/lab01a` | Pre-flight: confirms sandbox exists and task1 cleanup ran     |
| `hostname`      | First data source captured into the report via `>>`                 |
| `date`          | Second source — timestamps the report                               |
| `uptime`        | Third source — load/runtime context                                 |
| `id`            | Fourth source — documents who ran the report                        |
| `uname -r`      | Fifth source — kernel version for system context                    |
| `${USER}` (Tier B) | Part D appends a "signed" line into `report.txt` *as* `${USER}` via `sudo -u`, then `stat`/`getfacl` proves the section the lab user wrote vs the ones root wrote — real Tier B work inside the report itself |

### Main command block

```bash
TASKLOG=/tmp/lab01a/task2.txt

# ── Part A: multi-source report ──────────────────────────────────────
echo "=== System Report ===" > /tmp/lab01a/report.txt               # ONLY `>` in the whole block

echo "--- Hostname ---"    >> /tmp/lab01a/report.txt
hostname                   >> /tmp/lab01a/report.txt
echo "--- Date ---"        >> /tmp/lab01a/report.txt
date                       >> /tmp/lab01a/report.txt
echo "--- Uptime ---"      >> /tmp/lab01a/report.txt
uptime                     >> /tmp/lab01a/report.txt
echo "--- User ---"        >> /tmp/lab01a/report.txt
id                         >> /tmp/lab01a/report.txt
echo "--- Kernel ---"      >> /tmp/lab01a/report.txt
uname -r                   >> /tmp/lab01a/report.txt
echo "=== End Report ===" >> /tmp/lab01a/report.txt

cat /tmp/lab01a/report.txt                             2>&1 | tee $TASKLOG
wc -l /tmp/lab01a/report.txt                           2>&1 | tee -a $TASKLOG
head -1 /tmp/lab01a/report.txt                         | tee -a $TASKLOG
tail -1 /tmp/lab01a/report.txt                         | tee -a $TASKLOG

# ── Part B: T01-B — unquoted space in target name ────────────────────
echo "=== T01-B demo ===" | tee -a $TASKLOG
# BAD: bash sees `echo "test" > my` with `file.txt` as arg to echo
echo "test" > /tmp/lab01a/my file.txt 2>&1 | tee -a $TASKLOG || true
ls -la /tmp/lab01a/my* 2>&1 | tee -a $TASKLOG || echo "(no files created)" | tee -a $TASKLOG

# GOOD: quote the path
echo "test" > "/tmp/lab01a/my file.txt"
cat "/tmp/lab01a/my file.txt" | tee -a $TASKLOG
rm -f /tmp/lab01a/my* "/tmp/lab01a/my file.txt" 2>/dev/null

# ── Part C: ${USER} signs the report (Tier B weave) ───────────────────
# Give ${USER} write permission on the report, then append a "signed" line
# AS that user. We then prove the appended line is the ONLY line whose
# write was attributable to ${USER} — every other section was written as root.
chown root:"${GROUP}" /tmp/lab01a/report.txt
chmod 0664           /tmp/lab01a/report.txt        # group can write

sudo -u "${USER}" bash -c \
    'echo "--- Signed by $(whoami) at $(date -Is) ---" >> /tmp/lab01a/report.txt'

# Verify: file group is now ${GROUP}; last line shows the lab user signed it
stat -c '%U:%G %a %n' /tmp/lab01a/report.txt           | tee -a $TASKLOG
tail -n 1 /tmp/lab01a/report.txt                       | tee -a $TASKLOG
grep -c "Signed by ${USER}" /tmp/lab01a/report.txt     | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. `>` once at the top creates a clean, empty report file with the header line.
2. Each `>>` appends exactly one section header and one data line — position in the final file matches the order of calls.
3. `wc -l` confirms the expected line count (12 lines: header + 5 sections × 2 lines each + footer).
4. `head -1` and `tail -1` confirm the report boundaries survived all the appends.
5. T01-B: `echo "test" > my file.txt` — bash parses this as `echo "test" > my` with `file.txt` as an extra argument to `echo`. Result depends on the shell — usually creates a file named `my` containing `test file.txt`. The fix: always quote paths with spaces, or prefer underscores.

### Reading it left to right

```
hostname   >>   /tmp/lab01a/report.txt
│          │    │
│          │    └─ destination (existing file — append to EOF)
│          └─ redirect stdout (FD 1), append mode
└─ command whose stdout is one line (hostname output)
```

### The story

The multi-source report is the canonical exam pattern. A grading script will `cat /root/answer.txt` — if the header is missing (because you used `>>` first), or the footer is missing (because a later `>` wiped everything), you lose points. The rule is simple: one `>` at the top establishes the clean file; every subsequent source uses `>>`.

T01-B exists because shell word-splitting on unquoted strings is one of the most consistent sources of subtle bugs. `echo "test" > my file.txt` looks like it redirects to a two-word filename, but the shell processes word-splitting AFTER the redirect operator, not before. The result is confusing. The professional habit: never use spaces in filenames when you control the naming.

### Expected output

```text
=== System Report ===
--- Hostname ---
yourhost.example.com
--- Date ---
Tue May 27 10:23:45 UTC 2026
--- Uptime ---
 10:23:45 up 2 days,  3:11,  1 user,  load average: 0.00, 0.01
--- User ---
uid=0(root) gid=0(root) groups=0(root)
--- Kernel ---
5.14.0-427.el9.x86_64
=== End Report ===
12 /tmp/lab01a/report.txt
=== System Report ===
=== End Report ===
```

### Switches

| Pattern          | Meaning                                              |
|------------------|------------------------------------------------------|
| `> file`         | Overwrite — use exactly once, for the header         |
| `>> file`        | Append — use for every subsequent write              |
| `head -1 file`   | Confirm header is still first line                   |
| `tail -1 file`   | Confirm footer is still last line                    |
| `wc -l file`     | Count lines — verify no truncation happened          |

### Concept Card

| Concept | What it does |
|---|---|
| Multi-source report pattern | `>` once (header) → `>>` for everything else |
| Order = final file order | Lines appear in file in the exact order `>>` was called |
| Exam reflex: `>` means "fresh start" | Use before any sequence of `>>` calls |
| Exam reflex: `>>` means "add to" | Never wipes what's already there |
| **🪤 Trap Risk T01-B** | `echo "text" > my file.txt` is parsed as `echo "text" > my` with `file.txt` as an arg. **Fix:** quote paths: `echo "text" > "my file.txt"`. |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Report header present | `head -1 /tmp/lab01a/report.txt` returns `=== System Report ===` | First line must be the header |
| Report footer present | `tail -1 /tmp/lab01a/report.txt` returns `=== End Report ===` | No accidental `>` wiped the file |
| Line count correct | `wc -l /tmp/lab01a/report.txt` returns 13 | 12 root sections + 1 `${USER}`-signed line |
| Report group ownership | `stat -c '%G' /tmp/lab01a/report.txt` returns `labgrp_01_stdout` | Proves the chown that enabled the Tier B append |
| `${USER}` signed exactly once | `grep -c "Signed by ${USER}" /tmp/lab01a/report.txt` returns 1 | Confirms `sudo -u ${USER}` actually ran the append (vs root pretending) |
| Journal evidence | `ls /root/rhcsa_journal/lab-01a/task2/` | Files survive `/tmp` tmpfs reboot |

### Journal write

```bash
LAB=lab-01a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab01a/task2.txt  "$JDIR/evidence.txt"
cp /tmp/lab01a/report.txt "$JDIR/report.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Multi-source report pattern — > once (header), >> for all subsequent sources; ${USER} signs via sudo -u append
COMMANDS: >, >>, head -1, tail -1, wc -l, cat, chown root:${GROUP}, chmod 0664, sudo -u ${USER} bash -c '>> file', stat -c '%U:%G %a %n'
TRAPS:    T01-B rehearsed (unquoted space in redirect target)
TIER B:   report.txt is root:${GROUP} 0664; last line was appended by ${USER}; grep -c "Signed by" returns 1
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-01c — verify capstone: audit + persistence (destroy-restore drill, T41)
NOTE:     lab-01b is intentionally absent — Section 18 boundary lab (no honest Ansible module for >, >>, cat)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup (per-task — leaves Tier B sandbox intact)

```bash
# Final per-task cleanup before Lab Closeout. Removes only Task 2 files;
# user/group/sandbox stay so Lab Closeout can audit + tear them down.
rm -f /tmp/lab01a/report.txt /tmp/lab01a/warmup2.txt /tmp/lab01a/task2.txt

# Sanity-check the Tier B stack is still in place for Lab Closeout to audit
getent passwd "${USER}"  >/dev/null && echo "✅ ${USER} still present"
getent group  "${GROUP}" >/dev/null && echo "✅ ${GROUP} still present"
test -d       "${SANDBOX}"          && echo "✅ ${SANDBOX} still present"

ls /tmp/lab01a
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Report has only 1 line (just the header) | You used `>` for each section instead of `>>` — every `>` wiped the previous content |
| `head -1` shows wrong line | You used `>>` for the header too — the header was appended to a file that already had stale content |
| Line count is wrong | One of the commands (hostname, date, etc.) produced more than one line — inspect with `CMD \| wc -l` |
| T01-B: `ls -la /tmp/lab01a/my*` shows unexpected files | Expected — the demo creates or tries to create files in the wrong location |

> **STOP — paste the `cat report.txt`, `wc -l`, `head -1`, `tail -1`, the `stat -c '%U:%G'`, and the `grep -c "Signed by ${USER}"` outputs before running Lab Closeout.**

---

## Lab Closeout — Bulletproof Teardown (Section 6)

Runs after Task 2 only. This block tears down the Tier B sandbox the lab built in Lab-Wide Setup and **audits** that nothing was left behind. It's partial-failure tolerant — every step is guarded so a missing artifact doesn't abort the rest of the teardown.

```bash
set +e                          # tolerate partial failures inside cleanup

# 1) Mount layer — unmount anything we put under ${SANDBOX} (no-op here)
awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts \
    | tac | xargs -r -n1 umount -l 2>/dev/null

# 2) User / group (USER first because it owns files in ${USER_HOME})
if getent passwd "${USER}" >/dev/null 2>&1; then
    userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
    groupdel "${GROUP}"  2>/dev/null
fi

# 3) Sandbox dir — the safety net
rm -rf "${SANDBOX}"

# 4) Audit — prove nothing was left behind
echo "── Lab 01a cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"              && echo "❌ home remains"    || echo "✅ home gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the four `✅` audit lines before declaring Lab 01a complete. A single `❌` is a Section 8 mistake: investigate, fix, then re-run the audit.**

The journal in `/root/rhcsa_journal/lab-01a/` survives this teardown — only the `/tmp` Tier B stack is removed. Resume from there for Lab 01c.

---

## Lab 01a Checklist (2 tasks + closeout)

- [ ] Lab-Wide Setup — Tier B sandbox built; `id ${USER}`, both `getent` lines visible
- [ ] Task 1 — `>` creates file, `>>` appends; `wc -l` grows from 1→3; second `>` resets to 1; **Part D**: file written by `sudo -u ${USER}` is owned by `${USER}:${GROUP}`
- [ ] Task 2 — Multi-source report; `head -1` and `tail -1` confirm header/footer; T01-B demonstrated; **Part C**: `${USER}`-signed line appended via `sudo -u`; `grep -c` returns 1
- [ ] Lab Closeout — Section 6 teardown ran; four `✅` audit lines visible; journal in `/root/rhcsa_journal/lab-01a/` survives

---

## Related Labs

| Lab | Connection |
|---|---|
| ⛔ **Lab 01b is intentionally absent** | Section 18 boundary lab — `>`/`>>`/`cat` have no honest Ansible module. `ansible.builtin.copy` is not the same operation. The boundary is expressed by the absence, per Section 15. |
| **Lab 01c** — Verifying Stdout | Auditor seat: replays Lab 01a behavior, proves file contents, runs the destroy-restore drill (T41), validates the journal evidence written here |
| Lab 02a — Stderr Redirection RHCSA | The second stream; `2>` / `2>/dev/null` / order-of-operations |
| Lab 03a — Pipe Text Streams RHCSA | Connects stdout of one command to stdin of another |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
