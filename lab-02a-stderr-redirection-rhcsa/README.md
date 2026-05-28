# Lab 02a: Standard Error Redirection (RHCSA) — `2>`, `2>>`, `2>/dev/null`

- **Series:** linux-ops-mastery — Shells, Terminals & Redirection
- **Trilogy:** `02a` (RHCSA hand-typed) → ⛔ no `02b` (Section 18 boundary — `2>`/`2>/dev/null` have no honest Ansible module) → `02c` (Verify capstone — audit + persistence)
- **Career arcs covered:** RHCSA EX200 (every `find /` task that emits `Permission denied`), RHCE EX294 (Ansible `result.stderr` is the same stream `2>` captures), SRE (post-mortems read stderr — that's where the actual error message is), DevOps (CI/CD failed-build alerts), AI/MLOps (Python tracebacks land on stderr by default)
- **Prerequisite:** [`Lab 01a`](../lab-01a-stdout-redirection-rhcsa/) + [`Lab 01c`](../lab-01c-stdout-redirection-verify/) — you understand FD 1, `>`, `>>`, `wc -l`, and the Tier B sandbox stack
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = `2>` capture + `2>/dev/null` silence + `sudo -u ${USER}` weave · Task 2 = `2>>` append + order trap `2>&1` + `sudo -u ${USER}` weave)
- **Practice Directory (rotation #02):** `/var/log`
- **Sandbox (Tier B per Section 1.5):** `/tmp/lab02a` with `USER=labuser_02_stderr`, `GROUP=labgrp_02_stderr`, `USER_HOME=/tmp/lab02a/home_labuser_02_stderr`. Built in Lab-Wide Setup; torn down + audited in **Lab Closeout** after Task 2.
- **Traps rehearsed this lab:** **T02-A** (order matters — `cmd 2>&1 > file` vs `cmd > file 2>&1` do DIFFERENT things) · **T02-B** (using `2>` when you wanted `&>` — stdout still prints to terminal) · **T41** (skipping the destroy-restore drill — done in 02c) · **T44** (cleanup-left-orphan-user — Lab Closeout audit block proves no residue)

> **This lab's practice directory is: `/var/log`** — real log files produce real errors when a non-privileged process tries to read restricted subdirectories, giving us authentic stderr without inventing synthetic data.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T02-A T02-B T41"
echo "📁  PRACTICE DIR: /var/log"
echo ""
echo "💡 /var/log context (our stderr source):"
ls -ld /var/log
ls /var/log | head -n 8
echo "Shell version: $BASH_VERSION"
```

> **STOP — paste header output before running setup.**

---

## Objective

Stop letting errors disappear off the top of your terminal scrollback. By the end of this lab you can:

1. Redirect stderr (FD 2) to a file independently of stdout using `2>` and `2>>`.
2. Silence noisy `Permission denied` lines with `2>/dev/null` while keeping the clean results.
3. Understand the order trap: `cmd > file 2>&1` (both streams to file) vs `cmd 2>&1 > file` (stderr stays on screen).
4. Know that `2>/dev/null` hides the message but NOT the exit code — always check `$?`.

The capstone is the RHCSA-realistic pattern: *"Find every `.conf` file under `/etc`, suppress all errors, save the clean list to `/root/conf-files.txt`."* Every exam cycle has at least one task that reduces to this.

---

## Concept: stderr Is a Second, Independent Stream

Every Linux process has three FDs by default. Lab 01a covered FD 1 (stdout). **FD 2 is stderr.** It exists so that error messages do not tangle into the program's data output.

```
   ┌─────────────────────────────────────────────────────┐
   │   Your command (find, ls, grep, awk, ...)           │
   ├─────────────────────────────────────────────────────┤
   │   FD 0  stdin   ← keyboard                          │
   │   FD 1  stdout  → terminal (DATA output)    ◄─ `>`  │
   │   FD 2  stderr  → terminal (ERROR output)   ◄─ `2>` │
   └─────────────────────────────────────────────────────┘

   `> file`     captures FD 1 only — errors STILL hit the screen.   ← T02-B trap
   `2> file`    captures FD 2 only — data still hits the screen.
   `> f 2>&1`   correct merge — both go to `f`.                      ← Task 2
   `2>&1 > f`   order trap — stderr goes to screen, stdout to `f`.   ← T02-A
```

Both streams happen to display on the same terminal by default, which makes them *look* like one stream. They are not. `>` only redirects FD 1; FD 2 keeps going to the screen. That is the source of the bug *"my log file is empty even though the screen was full of red."*

---

## stderr Redirection Reference

| Pattern              | Effect                                                         | Use when…                                    |
|----------------------|----------------------------------------------------------------|----------------------------------------------|
| `cmd 2> file`        | stderr → file (truncate/create), stdout to screen             | Capture errors separately                    |
| `cmd 2>> file`       | stderr → file (append/create), stdout to screen               | Accumulate errors across runs                |
| `cmd 2> /dev/null`   | Discard stderr, stdout to screen                               | Silence noise like `Permission denied`       |
| `cmd > f 2>&1`       | Both FD 1 and FD 2 to `f` (correct merge order)               | Capture everything to one file               |
| `cmd 2>&1 > f`       | FD 2 → screen, FD 1 → `f` (wrong order — T02-A trap)          | Never use this unless you mean it            |
| `cmd > f1 2> f2`     | Split: stdout to `f1`, stderr to `f2`                         | Separate clean results from error log        |
| `cmd > /dev/null 2>&1` | Discard both streams                                         | Run for side effects / exit code only        |

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=02
export LAB_SLUG=stderr
export SANDBOX=/tmp/lab02a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-02a/task1
mkdir -p /root/rhcsa_journal/lab-02a/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd \
    -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id     "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /var/log
getent group  "${GROUP}"
getent passwd "${USER}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the `id` line, the three `ls -ld` lines, and both `getent` lines before Task 1. Section 1.5 sandbox stack is idempotent — re-run safe if you resume mid-lab.**

> **Why `${USER}` matters for stderr:** running `find /var/log` as root produces almost no `Permission denied` — root can read everything. The `sudo -u ${USER}` weave below makes the stderr stream *interesting* by running `find` as a non-privileged user against directories root owns.

---

## Task 1 — Capture stderr with `2>` and silence it with `2>/dev/null`

**Practice directory this task:** `/var/log` — `find /var/log` as a non-privileged user generates realistic `Permission denied` errors because some log directories are mode `0700` and owned by system accounts.

### Warm-Up

```bash
ls -ld /var/log                                        2>&1 | tee /tmp/lab02a/warmup.txt
ls /var/log | wc -l
find /var/log -maxdepth 1 -type d | head -n 5
id
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 01a: `2>&1 | tee FILE` captures the transcript — we use it in every warm-up block.

### Purpose

Run `find /var/log -name '*.log'` without redirects so you see how stderr and stdout mix on screen. Then split the streams to two separate files to prove they are independent. Finally use the RHCSA pattern: keep stdout in a file, throw stderr at `/dev/null`.

### WEAVE TRACE

| Warm-up / setup command      | Role inside Task 1                                             |
|------------------------------|----------------------------------------------------------------|
| `ls -ld /var/log`            | Pre-flight: source dir must exist before `find` runs          |
| `ls /var/log \| wc -l`       | Baseline count — helps interpret the stdout line count later  |
| `find /var/log -maxdepth 1 -type d` | Shows which subdirs could generate `Permission denied` |
| `id`                         | We're going to RUN as `${USER}` below — `id` here confirms the current EUID so the contrast is clear |
| `set -o pipefail`            | Ensures a failed `find` in a pipe chain propagates its exit code |
| `${USER}` (Tier B)           | Part D runs `find /var/log` *as* `${USER}` via `sudo -u`. That's how we actually *get* `Permission denied` lines on stderr — root would silently read every directory |

### Main command block

```bash
TASKLOG=/tmp/lab02a/task1.txt

# ── Part A: naive run — stderr and stdout mixed on screen ─────────────
echo "═══ Run 1: no redirect (streams tangled) ═══"    2>&1 | tee $TASKLOG
find /var/log -name '*.log' -type f 2>&1 | head -n 5   2>&1 | tee -a $TASKLOG
echo "(errors tangled with results above)"              | tee -a $TASKLOG

# ── Part B: split streams to separate files ───────────────────────────
echo "═══ Run 2: split capture ═══"                    2>&1 | tee -a $TASKLOG
find /var/log -name '*.log' -type f \
    >  /tmp/lab02a/log-files.txt \
    2> /tmp/lab02a/log-errors.txt

STDOUT_LINES=$(wc -l < /tmp/lab02a/log-files.txt)
STDERR_LINES=$(wc -l < /tmp/lab02a/log-errors.txt)
echo "stdout lines (real results): ${STDOUT_LINES}"    | tee -a $TASKLOG
echo "stderr lines (denied paths): ${STDERR_LINES}"    | tee -a $TASKLOG

echo "── first 3 stdout lines (log file paths) ──"     | tee -a $TASKLOG
head -n 3 /tmp/lab02a/log-files.txt                    | tee -a $TASKLOG
echo "── first 3 stderr lines (the noise) ──"          | tee -a $TASKLOG
head -n 3 /tmp/lab02a/log-errors.txt                   | tee -a $TASKLOG

# ── Part C: RHCSA clean-answer pattern ────────────────────────────────
echo "═══ Run 3: clean answer (stderr discarded) ═══"  | tee -a $TASKLOG
find /var/log -name '*.log' -type f \
    >  /tmp/lab02a/log-clean.txt \
    2> /dev/null
wc -l /tmp/lab02a/log-clean.txt                        | tee -a $TASKLOG

# ── Part D: run as ${USER} — stderr finally becomes interesting ───────
# As root, /var/log subdirs are all readable. As ${USER}, audit/ and sssd/
# are mode 0700 owned by other system accounts → Permission denied on stderr.
# This is the realistic stderr-capture scenario. Both target files are placed
# under ${USER_HOME} so ${USER} can write to them without sudo.
echo "═══ Run 4: split capture AS ${USER} ═══"         | tee -a $TASKLOG
sudo -u "${USER}" bash -c \
    'find /var/log -name "*.log" -type f \
        >  '"${USER_HOME}"'/log-files-asuser.txt \
        2> '"${USER_HOME}"'/log-errors-asuser.txt'

# Verify the user-run produced REAL stderr content (not zero lines like root would)
U_OUT=$(wc -l < "${USER_HOME}/log-files-asuser.txt")
U_ERR=$(wc -l < "${USER_HOME}/log-errors-asuser.txt")
echo "as-${USER} stdout lines: ${U_OUT}"               | tee -a $TASKLOG
echo "as-${USER} stderr lines: ${U_ERR}"               | tee -a $TASKLOG
test "${U_ERR}" -gt 0 \
    && echo "✅ stderr captured real Permission denied lines (Tier B weave worked)" \
    || echo "❌ stderr empty — sudo -u step did not actually drop privileges" \
    | tee -a $TASKLOG

# Ownership proof — both files belong to ${USER}:${GROUP}, not root
stat -c '%U:%G %a %n' "${USER_HOME}/log-files-asuser.txt"  | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${USER_HOME}/log-errors-asuser.txt" | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. Run `find` with no redirect — stderr (Permission denied) and stdout (file paths) print interleaved on the terminal. `head -n 5` cuts off both, so you lose context.
2. Run with `> stdout-file 2> stderr-file` — they are completely independent files. Count each.
3. Show first 3 lines of each so the difference is undeniable: clean paths on stdout, `Permission denied` on stderr.
4. RHCSA pattern: `> answer-file 2>/dev/null` — keep the clean answer, throw the noise away.
5. **Part D — Tier B sudo-u weave:** running `find /var/log` as the non-privileged `${USER}` is what makes stderr *non-empty*. As root, you'd see zero `Permission denied`. The check `test "${U_ERR}" -gt 0` is the literal proof that the privilege drop happened — if it failed, you'd see zero stderr lines and the `❌` branch would fire.

### Reading it left to right

- `find /var/log -name '*.log' -type f > /tmp/lab02a/log-files.txt 2> /tmp/lab02a/log-errors.txt` — the shell opens both target files (O_TRUNC) before `find` starts, then wires FD 1 to `log-files.txt` and FD 2 to `log-errors.txt`. They are independent `dup2(2)` calls; order of `>` and `2>` does NOT matter when they target different files.
- `2> /dev/null` — opens the kernel's bit-bucket for write on FD 2. Every error byte is silently accepted and discarded.
- Order of `>` and `2>` ONLY matters when one of them uses `&` to alias the other — Task 2 covers that.

### The story

In 1971, Unix had only stdin and stdout. Errors went to stdout, mixed with data. Then somebody piped the C compiler into another tool and discovered the next tool was choking on `cc: warning:` lines mixed into real output. So in Version 5 Unix (1974), Dennis Ritchie split stderr off into a separate file descriptor. The rule from that day forward:

- **FD 1 (stdout):** the program's actual answer — what you would pipe to the next command.
- **FD 2 (stderr):** diagnostics — warnings, errors, `Permission denied`. Not the answer.

`find /var/log -name '*.log'` obeys this rule: file paths go to FD 1, `Permission denied` messages go to FD 2. RHCSA tests all four combinations: capture both, capture only stdout, capture only stderr, discard stderr.

### Expected output

```text
═══ Run 1: no redirect (streams tangled) ═══
find: '/var/log/audit': Permission denied
/var/log/messages
/var/log/secure
/var/log/cron
(errors tangled with results above)
═══ Run 2: split capture ═══
stdout lines (real results): 24
stderr lines (denied paths): 3
── first 3 stdout lines (log file paths) ──
/var/log/messages
/var/log/secure
/var/log/cron
── first 3 stderr lines (the noise) ──
find: '/var/log/audit': Permission denied
find: '/var/log/private': Permission denied
find: '/var/log/sssd': Permission denied
═══ Run 3: clean answer (stderr discarded) ──
24 /tmp/lab02a/log-clean.txt
═══ Run 4: split capture AS labuser_02_stderr ═══
as-labuser_02_stderr stdout lines: 21
as-labuser_02_stderr stderr lines: 3
✅ stderr captured real Permission denied lines (Tier B weave worked)
labuser_02_stderr:labgrp_02_stderr 644 /tmp/lab02a/home_labuser_02_stderr/log-files-asuser.txt
labuser_02_stderr:labgrp_02_stderr 644 /tmp/lab02a/home_labuser_02_stderr/log-errors-asuser.txt
exit was: 0
```

### Switches

| Token                      | Meaning                                                            |
|----------------------------|--------------------------------------------------------------------|
| `2>`                       | Redirect FD 2 (stderr) — truncate-write                           |
| `2>>`                      | Redirect FD 2 — append-write                                      |
| `2> /dev/null`             | Discard stderr                                                     |
| `> f1 2> f2`               | Split streams to two different files                               |
| `find DIR -name P -type f` | Walk DIR, match name pattern P, only regular files                 |
| `wc -l < FILE`             | Line count without filename in output                              |
| `sudo -u USER bash -c '...'`| Run a redirect (or pipeline) as USER so file ownership lands there |
| `stat -c '%U:%G %a %n' F`  | Print owner:group, mode, name in one line — Tier B ownership audit |

### Concept Card

| Concept | What it does |
|---|---|
| FD 1 vs FD 2 | Two independent kernel-managed file descriptors; redirecting one doesn't touch the other |
| `2>` | Send stderr to a file (truncate) |
| `2>>` | Append stderr to a file |
| `2> /dev/null` | Discard stderr — the RHCSA `find` reflex |
| Split capture | `> out 2> err` writes to two files in one command |
| Tier B `sudo -u` weave | Running `find /var/log` as a non-privileged user is the only way to consistently generate real `Permission denied` lines on stderr |
| **🪤 Trap Risk T02-B** | `find / > /root/answer.txt` does NOT silence `Permission denied`. It only redirects FD 1; FD 2 keeps going to the screen. **Fix:** add `2>/dev/null` when you want only the clean answer. |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| stdout captured | `wc -l /tmp/lab02a/log-files.txt` > 0 | FD 1 redirect worked |
| stderr captured | `wc -l /tmp/lab02a/log-errors.txt` > 0 | FD 2 redirect worked and logged real errors |
| stderr silenced cleanly | `wc -l /tmp/lab02a/log-clean.txt` == stdout count | `2>/dev/null` didn't accidentally drop stdout |
| Task log exists | `wc -l /tmp/lab02a/task1.txt` | Transcript ready for journal |
| `${USER}` Tier B weave produced stderr | `wc -l "${USER_HOME}/log-errors-asuser.txt"` > 0 | Confirms sudo -u actually dropped privileges (root would produce 0 stderr lines) |
| User-owned outputs | `stat -c '%U:%G' "${USER_HOME}/log-files-asuser.txt"` returns `labuser_02_stderr:labgrp_02_stderr` | Files written via sudo -u land on the lab user, not root |

### Journal write

```bash
LAB=lab-02a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab02a/task1.txt                        "$JDIR/evidence.txt"
cp /tmp/lab02a/log-files.txt                    "$JDIR/log-files.txt"
cp /tmp/lab02a/log-errors.txt                   "$JDIR/log-errors.txt"
cp "${USER_HOME}/log-files-asuser.txt"          "$JDIR/log-files-asuser.txt"
cp "${USER_HOME}/log-errors-asuser.txt"         "$JDIR/log-errors-asuser.txt"

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
TOPIC:    2> captures FD 2; 2>/dev/null discards FD 2; > only redirects FD 1; sudo -u USER lets non-privileged find generate real Permission denied
COMMANDS: 2>, 2>>, 2>/dev/null, find, wc -l, sudo -u ${USER} bash -c, stat -c '%U:%G %a %n'
TRAPS:    T02-B rehearsed (plain > doesn't silence stderr)
TIER B:   log-files-asuser.txt and log-errors-asuser.txt owned by ${USER}:${GROUP}; stderr was non-empty (proof privilege drop worked)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — 2>> append, order trap 2>&1, exit-code preservation, sudo -u accumulation
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup (per-task — leaves Tier B sandbox intact)

```bash
rm -f /tmp/lab02a/log-files.txt /tmp/lab02a/log-errors.txt \
      /tmp/lab02a/log-clean.txt /tmp/lab02a/warmup.txt
rm -f "${USER_HOME}/log-files-asuser.txt" "${USER_HOME}/log-errors-asuser.txt"

getent passwd "${USER}"  >/dev/null && echo "✅ ${USER} still present"
getent group  "${GROUP}" >/dev/null && echo "✅ ${GROUP} still present"
test -d       "${SANDBOX}"          && echo "✅ ${SANDBOX} still present"

ls /tmp/lab02a
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `stderr lines: 0` (no Permission denied) | Running as root — all dirs are readable. Switch to a regular user or pick a more restricted source dir |
| `stdout lines: 0` and `stderr lines: 0` | `find` failed silently — check that `/var/log` exists and `find` is installed |
| Both files contain the same mixed content | You used `2>&1` (merged) instead of `2> file2` (separate) |
| `cannot overwrite existing file` | noclobber leaked from Lab 01a — `set +o noclobber` |

> **STOP — paste the "split capture" line counts before Task 2.**

---

## Task 2 — `2>>` append, order trap (`2>&1`), exit-code preservation

**Practice directory this task:** `/var/log` (same source) — we run `find` multiple times and accumulate the error log.

### Warm-Up

```bash
ls -la /tmp/lab02a                                     2>&1 | tee /tmp/lab02a/warmup2.txt
wc -l /tmp/lab02a/* 2>/dev/null | tail -n 3
find /var/log -maxdepth 1 -name '*.log' | wc -l
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: `2>/dev/null` combined with `wc -l` is already in your hands — the rest of this task adds `&` to the FD number.

### Purpose

Three skills:
1. **`2>>` append** — collect errors across multiple invocations into one growing log (the service-that-keeps-failing pattern).
2. **Order trap (T02-A)** — `cmd > file 2>&1` and `cmd 2>&1 > file` look identical but behave differently. Prove it by comparing line counts in the captured files.
3. **Exit-code preservation** — `2>/dev/null` does NOT mask `$?`. A failing command still exits non-zero.

### WEAVE TRACE

| Warm-up / setup command      | Role inside Task 2                                              |
|------------------------------|-----------------------------------------------------------------|
| `ls -la /tmp/lab02a`         | Proves Task 1 cleanup ran — no leftover `log-*.txt` files      |
| `wc -l /tmp/lab02a/*`        | Confirms only warmup.txt is present before the main block runs |
| `find /var/log -maxdepth 1 -name '*.log'` | Baseline: roughly how many log files exist       |
| `set -o pipefail`            | Ensures `find` failures in pipe chains surface as non-zero exit |
| `${USER}` (Tier B)           | Part D accumulates errors *across two `find` runs* as `${USER}` using `2>>` — proves append-mode persistence under a non-root identity |

### Main command block

```bash
TASKLOG=/tmp/lab02a/task2.txt

# ── Part A: 2>> append across two find runs ───────────────────────────
echo "═══ Part A: 2>> append ═══"                      2>&1 | tee $TASKLOG
find /var/log -name '*.log'  -type f >> /tmp/lab02a/all-results.txt 2>> /tmp/lab02a/all-errors.txt
find /var/log -name '*.conf' -type f >> /tmp/lab02a/all-results.txt 2>> /tmp/lab02a/all-errors.txt

R_LINES=$(wc -l < /tmp/lab02a/all-results.txt)
E_LINES=$(wc -l < /tmp/lab02a/all-errors.txt)
echo "combined results: ${R_LINES}  combined errors: ${E_LINES}" | tee -a $TASKLOG

# ── Part B: order trap — T02-A ────────────────────────────────────────
echo "═══ Part B: order trap ═══"                      | tee -a $TASKLOG

# Form A — CORRECT: redirect FD 1 first, THEN merge FD 2 into it
#   1. FD 1 → file  2. FD 2 → wherever FD 1 now goes (= file)  → BOTH in file
find /var/log -name '*.log' -type f > /tmp/lab02a/formA.txt 2>&1
A_LINES=$(wc -l < /tmp/lab02a/formA.txt)
A_ERR=$(grep -c 'Permission denied' /tmp/lab02a/formA.txt 2>/dev/null || echo 0)

# Form B — WRONG: merge FD 2 first (into terminal), THEN redirect FD 1 to file
#   1. FD 2 → terminal (still!)  2. FD 1 → file  → only stdout in file
find /var/log -name '*.log' -type f 2>&1 > /tmp/lab02a/formB.txt
B_LINES=$(wc -l < /tmp/lab02a/formB.txt)
B_ERR=$(grep -c 'Permission denied' /tmp/lab02a/formB.txt 2>/dev/null || echo 0)

echo "Form A (> file 2>&1)  lines: ${A_LINES}  'Permission denied' in file: ${A_ERR}" | tee -a $TASKLOG
echo "Form B (2>&1 > file)  lines: ${B_LINES}  'Permission denied' in file: ${B_ERR}" | tee -a $TASKLOG
echo "(Form A should have errors IN file; Form B should have errors on YOUR SCREEN)" | tee -a $TASKLOG

# ── Part C: exit-code preservation ────────────────────────────────────
echo "═══ Part C: 2>/dev/null does NOT hide exit code ═══" | tee -a $TASKLOG
find /no/such/path 2>/dev/null
echo "silenced failing find exit code: $?"               | tee -a $TASKLOG   # expect 1

find /var/log -maxdepth 0 2>/dev/null
echo "silenced succeeding find exit code: $?"            | tee -a $TASKLOG   # expect 0

# ── Part D: 2>> accumulation AS ${USER} (Tier B weave) ────────────────
# Two passes of find /var/log run as ${USER}. Each pass appends its stderr to
# the same error log. After both runs, the file should contain a non-zero
# accumulated count AND its ownership stays on ${USER}:${GROUP}.
echo "═══ Part D: 2>> accumulation AS ${USER} ═══"      | tee -a $TASKLOG

sudo -u "${USER}" bash -c '
    find /var/log -name "*.log"  -type f \
        >> '"${USER_HOME}"'/cum-results.txt \
        2>> '"${USER_HOME}"'/cum-errors.txt
    find /var/log -name "*.conf" -type f \
        >> '"${USER_HOME}"'/cum-results.txt \
        2>> '"${USER_HOME}"'/cum-errors.txt
'

CUM_OUT=$(wc -l < "${USER_HOME}/cum-results.txt")
CUM_ERR=$(wc -l < "${USER_HOME}/cum-errors.txt")
echo "accumulated as-${USER}: results=${CUM_OUT}  errors=${CUM_ERR}" | tee -a $TASKLOG
test "${CUM_ERR}" -gt 0 \
    && echo "✅ 2>> accumulated real Permission denied lines as ${USER}" \
    || echo "❌ 2>> accumulated zero stderr — sudo -u step did not run" \
    | tee -a $TASKLOG

# Ownership check — both files belong to ${USER}, not root
stat -c '%U:%G %a %n' "${USER_HOME}/cum-results.txt"   | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${USER_HOME}/cum-errors.txt"    | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. `2>>` runs `find` twice — each run appends its stderr errors to `all-errors.txt`. The file grows. This is how you build a cumulative error log from a service that's been misbehaving intermittently.
2. Form A (`> file 2>&1`): the shell processes redirections left to right. First `> file` makes FD 1 point to the file. Then `2>&1` makes FD 2 point to wherever FD 1 currently goes — which is the file. Both streams end up in the file.
3. Form B (`2>&1 > file`): the shell processes left to right. First `2>&1` makes FD 2 point to wherever FD 1 currently goes — which is **still the terminal**. Then `> file` makes FD 1 point to the file. Stderr stays on the terminal.
4. `2>/dev/null` hides the error text. `$?` still reflects the command's actual exit code.

### Reading it left to right (the order trap mechanism)

```
find ... > /tmp/lab02a/formA.txt 2>&1
         │                       │
         │                       └─ step 2: FD 2 → wherever FD 1 now goes (= file) ✅
         └─ step 1: FD 1 → file

find ... 2>&1 > /tmp/lab02a/formB.txt
         │    │
         │    └─ step 2: FD 1 → file
         └─ step 1: FD 2 → wherever FD 1 now goes (= terminal!) ❌
```

**Rule:** if you want both streams in one file, put `2>&1` **after** `>`. Or use bash shorthand `&>` (Lab 04).

### The story

The order trap (T02-A) is the most "fooled a senior engineer in production" stderr bug in Unix history. It looks symmetric — both forms have a `>` and a `2>&1`, so it feels like order can't matter. It does. The reason: `2>&1` copies *the current target of FD 1 at the moment it's parsed*, not "whatever FD 1 will eventually be." Once you've drawn the dup2 picture above once, you'll never write Form B again.

Exit-code preservation (implicitly T02-C) is the other quiet killer. People silence noisy commands with `2>/dev/null` and assume they "succeeded." The silencing hid the complaint; the exit code still tells the truth. Always check `$?` after a redirect-silenced command.

### Expected output

```text
═══ Part A: 2>> append ═══
combined results: 48  combined errors: 6
═══ Part B: order trap ═══
find: '/var/log/audit': Permission denied      ← THIS APPEARED ON YOUR SCREEN (Form B)
Form A (> file 2>&1)  lines: 27  'Permission denied' in file: 3
Form B (2>&1 > file)  lines: 24  'Permission denied' in file: 0
(Form A should have errors IN file; Form B should have errors on YOUR SCREEN)
═══ Part C: 2>/dev/null does NOT hide exit code ═══
silenced failing find exit code: 1
silenced succeeding find exit code: 0
═══ Part D: 2>> accumulation AS labuser_02_stderr ═══
accumulated as-labuser_02_stderr: results=46  errors=6
✅ 2>> accumulated real Permission denied lines as labuser_02_stderr
labuser_02_stderr:labgrp_02_stderr 644 /tmp/lab02a/home_labuser_02_stderr/cum-results.txt
labuser_02_stderr:labgrp_02_stderr 644 /tmp/lab02a/home_labuser_02_stderr/cum-errors.txt
exit was: 0
```

### Switches

| Token         | Meaning                                                                |
|---------------|------------------------------------------------------------------------|
| `2>>`         | Append-write to FD 2 target file                                       |
| `2>&1`        | Make FD 2 point wherever FD 1 **currently** points (order-sensitive)  |
| `> f 2>&1`    | Correct merge — both streams to `f`                                    |
| `2>&1 > f`    | Wrong order — FD 2 → terminal, FD 1 → `f`                             |
| `grep -c P f` | Count lines matching pattern P in file f                               |

### Concept Card

| Concept | What it does |
|---|---|
| `2>>` append | Accumulate errors across runs into one growing file |
| dup2 mental model | Each redirect is one `dup2` syscall against the **current** state of the FDs at that moment |
| `> file 2>&1` | Correct merge — FD 1 to file first, THEN FD 2 → FD 1 |
| `&>` shorthand | Bash combined-redirect equivalent to `> file 2>&1` (Lab 04) |
| Exit-code preservation | `2>/dev/null` hides text, NOT `$?` |
| **🪤 Trap Risk T02-A** | `cmd 2>&1 > file` puts stderr on screen, NOT in the file. **Fix:** always `> file 2>&1` — redirect FD 1 FIRST, then merge FD 2. |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| `2>>` accumulated errors | `wc -l /tmp/lab02a/all-errors.txt` > 0 | Two runs' errors are combined, not truncated |
| Form A merged correctly | `grep -c 'Permission denied' /tmp/lab02a/formA.txt` > 0 | Errors made it INTO the file |
| Form B did NOT merge | `grep -c 'Permission denied' /tmp/lab02a/formB.txt` returns 0 | Confirms the order trap happened |
| Exit code honest | `find /no/such/path 2>/dev/null; echo $?` returns 1 | `2>/dev/null` doesn't mask `$?` |
| Tier B `2>>` accumulation | `wc -l "${USER_HOME}/cum-errors.txt"` > 0 (two find runs combined) | Append mode works under sudo -u just like under root |
| Cumulative files owned by `${USER}` | `stat -c '%U:%G' "${USER_HOME}/cum-results.txt"` returns `labuser_02_stderr:labgrp_02_stderr` | Ownership lands where `sudo -u` says — not root |

### Journal write

```bash
LAB=lab-02a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab02a/task2.txt                "$JDIR/evidence.txt"
cp /tmp/lab02a/formA.txt                "$JDIR/formA.txt"
cp /tmp/lab02a/formB.txt                "$JDIR/formB.txt"
cp "${USER_HOME}/cum-results.txt"       "$JDIR/cum-results-asuser.txt"
cp "${USER_HOME}/cum-errors.txt"        "$JDIR/cum-errors-asuser.txt"

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
TOPIC:    2>> append; order trap (2>&1 position); exit-code preservation; sudo -u 2>> accumulation
COMMANDS: 2>>, 2>&1, > file 2>&1 (correct) vs 2>&1 > file (wrong order), sudo -u ${USER} bash -c, stat -c '%U:%G %a %n'
TRAPS:    T02-A rehearsed (Form A had errors in file; Form B had them on screen)
TIER B:   cum-results-asuser.txt and cum-errors-asuser.txt owned by ${USER}:${GROUP}; stderr non-empty after two find passes
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-02c — verify capstone: audit + persistence (destroy-restore drill, T41)
NOTE:     lab-02b is intentionally absent — Section 18 boundary lab (no honest Ansible module for 2>, 2>/dev/null)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup (per-task — leaves Tier B sandbox intact)

```bash
rm -f /tmp/lab02a/all-results.txt /tmp/lab02a/all-errors.txt \
      /tmp/lab02a/formA.txt /tmp/lab02a/formB.txt \
      /tmp/lab02a/warmup2.txt /tmp/lab02a/task2.txt
rm -f "${USER_HOME}/cum-results.txt" "${USER_HOME}/cum-errors.txt"

getent passwd "${USER}"  >/dev/null && echo "✅ ${USER} still present"
getent group  "${GROUP}" >/dev/null && echo "✅ ${GROUP} still present"
test -d       "${SANDBOX}"          && echo "✅ ${SANDBOX} still present"

ls /tmp/lab02a
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Form A and Form B look the same on disk | Running as root — all dirs are readable, so no Permission denied appears anywhere |
| Form B shows `Permission denied` IN the file | You typed `> file 2>&1` by accident — that's Form A (correct merge) |
| `exit code: 0` for failing find | Your shell collapsed the statement — make sure `find /no/such/path` is a standalone command |
| Accumulated errors count is too low | The two `find` runs hit the same restricted dirs — that's expected; the count should be double |

> **STOP — paste the Form A / Form B line counts, the "silenced failing find exit code" line, and the Part D `✅ 2>> accumulated real Permission denied lines` line before running Lab Closeout.**

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# 1) Mount layer (no-op for this lab)
awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts \
    | tac | xargs -r -n1 umount -l 2>/dev/null

# 2) User / group teardown — USER first because it owns files in ${USER_HOME}
if getent passwd "${USER}" >/dev/null 2>&1; then
    userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
    groupdel "${GROUP}"  2>/dev/null
fi

# 3) Sandbox dir
rm -rf "${SANDBOX}"

# 4) Audit
echo "── Lab 02a cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"              && echo "❌ home remains"    || echo "✅ home gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the four `✅` audit lines before moving to Lab 02c.**

---

## Lab 02a Checklist (2 tasks + closeout)

- [ ] Lab-Wide Setup — Tier B sandbox built; `id ${USER}`, both `getent` lines visible
- [ ] Task 1 — split capture (`> f1 2> f2`); RHCSA clean-answer (`2>/dev/null`); proved FD 1 ≠ FD 2; **Part D** `sudo -u ${USER}` produced non-zero stderr
- [ ] Task 2 — `2>>` accumulation; order trap (Form A has errors in file; Form B does not); exit code honest; **Part D** `${USER}` accumulated errors via `2>>`
- [ ] Lab Closeout — four `✅` audit lines; journal in `/root/rhcsa_journal/lab-02a/` survives

---

## Related Labs

| Lab | Connection |
|---|---|
| ⛔ **Lab 02b is intentionally absent** | Section 18 boundary lab — `2>` / `2>/dev/null` have no honest Ansible module. `ansible.builtin.shell` + `register: result.stderr` *captures* stderr but does not *redirect* it the way `2>` does. |
| **Lab 02c** — Verifying Stderr | Audit: file has content AND no `Permission denied` lines leaked into stdout file; destroy-restore drill against journal evidence |
| Lab 01a — Stdout Redirection | FD 1 — the stream Lab 02a extends with FD 2 |
| Lab 01c — Stdout Verify | The previous topic's verify capstone — same Tier B + destroy-restore pattern |
| Lab 04a — Combined Redirection | `&>` / `2>&1` deep dive with all edge cases |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
