# Lab 03a: Pipe Text Streams (RHCSA) — `|`, `less`, `grep`, `tee`, `wc -l`

- **Series:** linux-ops-mastery — Shells, Terminals & Redirection
- **Trilogy:** `03a` (RHCSA hand-typed) → ⛔ no `03b` (Section 18 boundary — `|`/`tee` have no honest Ansible module) → `03c` (Verify capstone — audit + persistence)
- **Career arcs covered:** RHCSA EX200 (every "filter and count" task), RHCE EX294 (Ansible `shell:` + `register:` exposes `stdout_lines` — the pipeline result), SRE (alerting pipelines, log grep-and-count), DevOps (CI build summaries), AI/MLOps (dataset inspection: `wc -l`, `head`, `tail`, `grep` patterns)
- **Prerequisite:** [`Lab 01a`](../lab-01a-stdout-redirection-rhcsa/) + [`Lab 01c`](../lab-01c-stdout-redirection-verify/) (stdout + Tier B) · [`Lab 02a`](../lab-02a-stderr-redirection-rhcsa/) + [`Lab 02c`](../lab-02c-stderr-redirection-verify/) (stderr + Tier B)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = `|`, `grep`, `wc -l`, `less` basics + `sudo -u ${USER}` weave · Task 2 = `tee`, `set -o pipefail`, T03-A proof + `sudo -u ${USER}` weave)
- **Practice Directory (rotation #03):** `/etc`
- **Sandbox (Tier B per Section 1.5):** `/tmp/lab03a` with `USER=labuser_03_pipe`, `GROUP=labgrp_03_pipe`, `USER_HOME=/tmp/lab03a/home_labuser_03_pipe`. Built in Lab-Wide Setup; torn down + audited in **Lab Closeout** after Task 2.
- **Traps rehearsed this lab:** **T03-A** (`false | true` returns 0 without `set -o pipefail` — upstream failures are silent) · **T03-B** (forgetting `set -o pipefail` in scripts — default behavior masks broken pipes) · **T41** (skipping the destroy-restore drill — done in 03c) · **T44** (cleanup-left-orphan-user — Lab Closeout audit block proves no residue)

> **This lab's practice directory is: `/etc`** — every task reads config files from `/etc` as the pipeline source: rich, structured text, predictable line counts, universally present on every Linux host.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T03-A T03-B T41"
echo "📁  PRACTICE DIR: /etc"
echo ""
echo "💡 /etc context (our pipe source):"
ls -ld /etc
ls /etc | wc -l
echo "Shell version: $BASH_VERSION"
```

> **STOP — paste header output before running setup.**

---

## Objective

Make pipe chains a reflex. By the end of this lab you can:

1. Connect the stdout of any command to the stdin of the next using `|`.
2. Filter text with `grep`, count lines with `wc -l`, page through output with `less`.
3. Split a pipe so output goes to BOTH a file and the next command using `tee`.
4. Detect and prevent silent upstream failures with `set -o pipefail` (T03-A and T03-B).

The capstone pattern: *"Find all files in `/etc` that contain 'root', count them, and save the filtered list to a file."* Every RHCSA exam has a variation of this.

---

## Concept: A Pipe Connects FD 1 of One Command to FD 0 of Another

A pipe (`|`) is a kernel-managed in-memory buffer. The shell connects the **stdout (FD 1)** of the left command to the **stdin (FD 0)** of the right command. Both commands run concurrently; the right command reads as the left writes.

```
   cmd1       |        cmd2       |        cmd3
   ─────────────────────────────────────────────
   FD 1 ─────► FD 0   FD 1 ─────► FD 0   FD 1 ─► terminal
   (stdout)  (stdin)  (stdout)  (stdin)  (stdout)

   Each `|` creates one kernel pipe buffer.
   cmd1 writes into it; cmd2 reads from it.
   cmd3 writes its stdout to the terminal (or the next `|`).
```

**Key facts:**
- Each command runs in its own subshell.
- By default, the pipeline exit code is the exit code of the **last** command — even if earlier commands failed. This is T03-A.
- `set -o pipefail` changes this: the pipeline returns the exit code of the **rightmost** command that exited non-zero.

---

## Pipe Reference

| Operator / Command       | What it does                                                    |
|--------------------------|-----------------------------------------------------------------|
| `cmd1 \| cmd2`           | Connect FD 1 of cmd1 to FD 0 of cmd2                           |
| `grep PATTERN`           | Print only lines matching PATTERN                               |
| `grep -v PATTERN`        | Print only lines NOT matching PATTERN                           |
| `grep -c PATTERN`        | Print count of matching lines (no actual lines)                 |
| `grep -i PATTERN`        | Case-insensitive match                                          |
| `wc -l`                  | Count newlines from stdin                                       |
| `less`                   | Page through stdin; `q` to quit, `/` to search                 |
| `head -n N`              | First N lines from stdin                                        |
| `tail -n N`              | Last N lines from stdin                                         |
| `tee FILE`               | Write stdin to FILE and also pass it to stdout (wye fitting)    |
| `tee -a FILE`            | Append to FILE instead of overwriting                           |
| `set -o pipefail`        | Pipeline returns exit of rightmost non-zero command             |
| `set +o pipefail`        | Restore default (exit of last command)                          |

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=03
export LAB_SLUG=pipe
export SANDBOX=/tmp/lab03a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-03a/task1
mkdir -p /root/rhcsa_journal/lab-03a/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd \
    -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id     "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /etc
getent group  "${GROUP}"
getent passwd "${USER}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the `id`, three `ls -ld`, and both `getent` lines before Task 1. Section 1.5 sandbox is idempotent.**

> **Why `${USER}` matters for pipes:** running pipelines as a non-privileged user is how you discover `Permission denied` lines that need filtering with `grep -v` or silencing with `2>/dev/null`. Root sees no permission errors; `${USER}` sees the real exam scenario.

---

## Task 1 — Pipe basics: `|`, `grep`, `wc -l`, `less`

**Practice directory this task:** `/etc` — we read from `/etc/passwd`, `/etc/services`, and the directory listing as pipeline sources.

### Warm-Up

```bash
wc -l /etc/passwd                                      2>&1 | tee /tmp/lab03a/warmup.txt
ls /etc | wc -l
cat /etc/passwd | head -n 3
grep 'root' /etc/passwd
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 02a: `2>&1 | tee FILE` is the standard transcript capture. `set -o pipefail` is now our default at the start of every warm-up.

### Purpose

Build five progressively longer pipe chains, reading from `/etc` files. After each chain, verify the line count and inspect the first/last few results. Prove that `less` is just another pipe stage. Prove that `grep` can be stacked multiple times.

### WEAVE TRACE

| Warm-up / setup command   | Role inside Task 1                                             |
|---------------------------|----------------------------------------------------------------|
| `wc -l /etc/passwd`       | Baseline: full passwd line count; we'll `grep` to a subset   |
| `ls /etc \| wc -l`        | Another baseline; we'll filter this listing in the main block |
| `cat /etc/passwd \| head -n 3` | Proves the pipe: cat writes, head reads                 |
| `grep 'root' /etc/passwd` | Single-filter example we extend in the main block            |
| `set -o pipefail`         | The default from here on — Task 2 demonstrates WHY            |
| `${USER}` (Tier B)        | Part D runs the canonical `grep \| tee` pipeline *as* `${USER}` writing into `${USER_HOME}` — proves the file lands on the lab user without root touching it |

### Main command block

```bash
TASKLOG=/tmp/lab03a/task1.txt

# ── Chain 1: single filter + count ────────────────────────────────────
echo "═══ Chain 1: grep nologin users ═══"              2>&1 | tee $TASKLOG
grep 'nologin' /etc/passwd | wc -l                     2>&1 | tee -a $TASKLOG

# ── Chain 2: filter with multiple greps stacked ───────────────────────
echo "═══ Chain 2: /etc files containing 'root' ═══"    | tee -a $TASKLOG
grep -rl 'root' /etc 2>/dev/null | wc -l               2>&1 | tee -a $TASKLOG

# ── Chain 3: ls /etc filtered and counted ────────────────────────────
echo "═══ Chain 3: /etc entries matching '.conf' ═══"   | tee -a $TASKLOG
ls /etc | grep '\.conf$'                               2>&1 | tee -a $TASKLOG
ls /etc | grep '\.conf$' | wc -l                       2>&1 | tee -a $TASKLOG

# ── Chain 4: save to file using tee (preview then read from file) ─────
echo "═══ Chain 4: chain into tee — save AND display ═══" | tee -a $TASKLOG
grep 'nologin' /etc/passwd | tee /tmp/lab03a/nologin-users.txt | wc -l
echo "file also written:"                              | tee -a $TASKLOG
wc -l /tmp/lab03a/nologin-users.txt                    | tee -a $TASKLOG
head -n 3 /tmp/lab03a/nologin-users.txt                | tee -a $TASKLOG

# ── Chain 5: less (pipe to pager) ────────────────────────────────────
echo "═══ Chain 5: pipe to less (interactive) ═══"      | tee -a $TASKLOG
echo "(run this manually to try less interactively)"    | tee -a $TASKLOG
echo "  cat /etc/services | less"                       | tee -a $TASKLOG
echo "(in less: j/k or arrows to scroll; /ssh to search; q to quit)" | tee -a $TASKLOG
# Non-interactive version to keep the script runnable:
cat /etc/services | head -n 5                          | tee -a $TASKLOG

# ── Chain 6: pipe + tee AS ${USER} (Tier B weave) ─────────────────────
# The whole pipeline runs as ${USER}. The tee target lands under ${USER_HOME}
# so the file ownership is the proof — not just an echo statement claiming
# the right thing happened.
echo "═══ Chain 6: grep | tee | wc -l AS ${USER} ═══"   | tee -a $TASKLOG
sudo -u "${USER}" bash -c \
    'grep "nologin" /etc/passwd \
        | tee '"${USER_HOME}"'/nologin-asuser.txt \
        | wc -l'

# Verify ownership lands on ${USER}:${GROUP}
stat -c '%U:%G %a %n' "${USER_HOME}/nologin-asuser.txt"  | tee -a $TASKLOG
U_LINES=$(wc -l < "${USER_HOME}/nologin-asuser.txt")
echo "as-${USER} nologin lines: ${U_LINES}"             | tee -a $TASKLOG
test "${U_LINES}" -gt 0 \
    && echo "✅ pipeline ran as ${USER}, file owned by ${USER}:${GROUP}" \
    || echo "❌ Tier B pipeline produced empty output" \
    | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. **Chain 1** — `grep 'nologin' /etc/passwd | wc -l`: grep filters to only matching lines; wc -l counts them. This is the most common RHCSA counting pattern.
2. **Chain 2** — `grep -rl 'root' /etc 2>/dev/null | wc -l`: `-r` recursive, `-l` filenames only. The `2>/dev/null` suppresses `Permission denied` from subdirs we can't read (Lab 02a in action).
3. **Chain 3** — two versions of the same chain: first with `tee -a $TASKLOG` to see the filenames, then with `| wc -l` to count them. This demonstrates that you can add or swap the last stage.
4. **Chain 4** — `tee` is the "wye fitting": the water (data) flows through it AND a copy branches off into the file. The downstream command (`wc -l`) sees the same data as if there were no tee.
5. **Chain 5** — `less` is just another command that reads from stdin. `cat /etc/services | less` pages through the file.
6. **Chain 6 — Tier B `sudo -u` weave.** Same `grep | tee | wc -l` pipeline as Chain 4, but the whole thing runs as `${USER}`. The `tee` target sits under `${USER_HOME}` so the file ownership is `${USER}:${GROUP}` automatically. `stat` confirms; `wc -l > 0` proves the pipeline produced real output.

### Reading it left to right

```
grep 'nologin' /etc/passwd   |   tee /tmp/lab03a/nologin-users.txt   |   wc -l
│                             │   │                                    │   │
│                             │   │                                    │   └─ count the lines
│                             │   │                                    └─ pipe to wc
│                             │   └─ file copy branches off here
│                             └─ pipe connects grep's FD 1 to tee's FD 0
└─ grep filters /etc/passwd and writes matches to FD 1
```

### The story

Doug McIlroy invented the pipe in 1972 after years of watching Bell Labs programmers write monolithic tools that did everything. His insight: a small tool that does one thing perfectly, connected to another small tool that does one thing perfectly, is more powerful than any combined tool. The `|` character is the Unix philosophy embodied in a single keystroke.

`tee` gets its name from the plumbing T-fitting that splits a pipe into two branches. Same data in, two destinations out. It's the solution to "I want to save the output AND pass it to the next stage" — which is exactly what RHCSA lab-verification looks like: you need the data in a file AND a count on screen.

### Expected output

```text
═══ Chain 1: grep nologin users ═══
24
═══ Chain 2: /etc files containing 'root' ═══
47
═══ Chain 3: /etc entries matching '.conf' ═══
adjtime.conf
chrony.conf
dnsmasq.conf
...
8
═══ Chain 4: chain into tee — save AND display ═══
24
file also written:
24 /tmp/lab03a/nologin-users.txt
bin:x:1:1:bin:/bin:/sbin/nologin
daemon:x:2:2:daemon:/sbin:/sbin/nologin
adm:x:3:4:adm:/var/adm:/sbin/nologin
═══ Chain 6: grep | tee | wc -l AS labuser_03_pipe ═══
24
labuser_03_pipe:labgrp_03_pipe 644 /tmp/lab03a/home_labuser_03_pipe/nologin-asuser.txt
as-labuser_03_pipe nologin lines: 24
✅ pipeline ran as labuser_03_pipe, file owned by labuser_03_pipe:labgrp_03_pipe
```

### Switches

| Token               | Meaning                                                      |
|---------------------|--------------------------------------------------------------|
| `\|`                | Connect stdout of left to stdin of right                     |
| `grep PATTERN`      | Print lines matching PATTERN                                 |
| `grep -c`           | Count matching lines (no output text, just a number)         |
| `grep -v`           | Invert match — print lines NOT matching                      |
| `grep -rl`          | Recursive search; print only filenames                       |
| `wc -l`             | Count newlines (one per line of input)                       |
| `tee FILE`          | Write to FILE and pass unchanged to stdout                   |
| `tee -a FILE`       | Append to FILE instead of truncating                         |
| `less`              | Interactive pager; q=quit, /=search, n=next match            |
| `sudo -u USER bash -c '...\|...'` | Run a whole pipeline as USER so the tee target file lands on USER |
| `stat -c '%U:%G %a %n' FILE` | Print owner:group, mode, name — Tier B ownership reflex     |

### Concept Card

| Concept | What it does |
|---|---|
| Pipe (`\|`) | Kernel buffer connecting FD 1 of left to FD 0 of right |
| Concurrency | Both sides of `\|` run simultaneously; left produces, right consumes |
| Chain length | Any number of `\|` stages; each is one process |
| `tee` (wye fitting) | Duplicate the stream — file copy AND pass-through simultaneously |
| `grep \| wc -l` vs `grep -c` | Same count result; `grep \| wc -l` also passes lines to further stages |
| Tier B `sudo -u` pipeline | Running `grep \| tee \| wc -l` as `${USER}` lands the tee target on the lab user — pipeline + ownership in one shot |
| **🪤 Trap Risk T03-A** | Default: `false \| true` returns 0 (last command's exit code). Pipeline failure is invisible. **Fix:** `set -o pipefail` in every script. Demonstrated in Task 2. |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| nologin-users file written | `wc -l /tmp/lab03a/nologin-users.txt` matches Chain 1 count | `tee` wrote the file |
| `grep` filter works | `head -n 3 /tmp/lab03a/nologin-users.txt` shows nologin entries | Content is correct, not just count |
| Task log exists | `wc -l /tmp/lab03a/task1.txt` | Evidence ready for journal |
| Tier B pipeline produced output | `wc -l "${USER_HOME}/nologin-asuser.txt"` returns 24 | `sudo -u ${USER}` pipeline ran end-to-end |
| `${USER}` owns the tee target | `stat -c '%U:%G' "${USER_HOME}/nologin-asuser.txt"` returns `labuser_03_pipe:labgrp_03_pipe` | Sudo -u dropped privileges; tee wrote as USER |

> **Reboot note:** `/tmp` is tmpfs. Journal copies survive reboot; `/tmp/lab03a/` does not.

### Journal write

```bash
LAB=lab-03a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab03a/task1.txt              "$JDIR/evidence.txt"
cp /tmp/lab03a/nologin-users.txt      "$JDIR/nologin-users.txt"
cp "${USER_HOME}/nologin-asuser.txt"  "$JDIR/nologin-asuser.txt"

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
TOPIC:    | connects FD 1 to FD 0; tee splits to file+downstream; grep+wc -l = count pattern; sudo -u USER pipeline lands ownership on USER
COMMANDS: |, grep, wc -l, tee, tee -a, head, tail, less, sudo -u ${USER} bash -c, stat -c '%U:%G %a %n'
TRAPS:    T03-A preview (pipefail not yet set — Task 2 demonstrates it)
TIER B:   nologin-asuser.txt owned by ${USER}:${GROUP}; 24-line pipeline output through tee
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — tee -a append, set -o pipefail, T03-A false|true proof + sudo -u pipefail proof
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup (per-task — leaves Tier B sandbox intact)

```bash
rm -f /tmp/lab03a/nologin-users.txt /tmp/lab03a/warmup.txt /tmp/lab03a/task1.txt
rm -f "${USER_HOME}/nologin-asuser.txt"

getent passwd "${USER}"  >/dev/null && echo "✅ ${USER} still present"
getent group  "${GROUP}" >/dev/null && echo "✅ ${GROUP} still present"
test -d       "${SANDBOX}"          && echo "✅ ${SANDBOX} still present"

ls /tmp/lab03a
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `wc -l` shows 0 from a pipe | The upstream command produced no output — test it without the `\|` first |
| `tee` overwrote a file you wanted to keep | Use `tee -a` instead of `tee` |
| `less` exits immediately | `less` needs a TTY — in a script it won't wait. Use it interactively only |
| `grep -rl` takes forever | Add `-maxdepth N` before `-rl` or constrain the search directory |

> **STOP — paste the `wc -l` output from Chains 1 and 4 before Task 2.**

---

## Task 2 — `tee -a`, `set -o pipefail`, and the silent-failure trap (T03-A)

**Practice directory this task:** `/etc` (same source) — we build append-mode tee chains and then prove that pipelines can silently swallow upstream failures.

### Warm-Up

```bash
ls -la /tmp/lab03a                                     2>&1 | tee /tmp/lab03a/warmup2.txt
cat /etc/os-release | head -n 4
ls /etc | grep -c '\.d$'
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: `set -o pipefail` is already on — Task 2 demonstrates what happens without it.

### Purpose

Three skills:
1. **`tee -a`** — append mode: build a cumulative log across multiple pipeline runs.
2. **T03-A demonstration** — run `false | true` without pipefail → exit 0. Then run it WITH pipefail → exit 1. The contrast is the lesson.
3. **T03-B reminder** — scripts default to no pipefail. Put `set -o pipefail` at the top of every script that uses pipes in conditional logic.

### WEAVE TRACE

| Warm-up / setup command | Role inside Task 2                                              |
|-------------------------|-----------------------------------------------------------------|
| `ls -la /tmp/lab03a`    | Confirms Task 1 cleanup ran — no leftover files                |
| `cat /etc/os-release \| head -n 4` | Shows a simple pipeline that will grow in the main block |
| `ls /etc \| grep -c '\.d$'` | Counts `.d` directories in `/etc` — used as a baseline below |
| `set -o pipefail`       | On by default this task; we explicitly toggle it for the T03-A demo |
| `${USER}` (Tier B)      | Part D runs the `false \| true` pipefail demo *as* `${USER}` and proves the exit-code behavior is identical under sudo -u (no shell-mode difference) |

### Main command block

```bash
TASKLOG=/tmp/lab03a/task2.txt

# ── Part A: tee -a builds a cumulative report ─────────────────────────
echo "═══ Part A: tee -a cumulative report ═══"         2>&1 | tee $TASKLOG
echo "=== Report Pass 1 ===" | tee    /tmp/lab03a/report.txt | tee -a $TASKLOG
cat /etc/os-release | head -n 4 | tee -a /tmp/lab03a/report.txt | tee -a $TASKLOG
echo "=== Report Pass 2 ===" | tee -a /tmp/lab03a/report.txt | tee -a $TASKLOG
ls /etc | grep '\.d$' | tee -a /tmp/lab03a/report.txt | wc -l | tee -a $TASKLOG
wc -l /tmp/lab03a/report.txt                           | tee -a $TASKLOG
head -3 /tmp/lab03a/report.txt                         | tee -a $TASKLOG

# ── Part B: T03-A demonstration — pipefail OFF ────────────────────────
echo "═══ Part B: T03-A — false|true without pipefail ═══" | tee -a $TASKLOG
set +o pipefail
false | true
echo "false|true exit code WITHOUT pipefail: $?"        | tee -a $TASKLOG   # expect 0

# T03-A demonstration with a realistic broken-find chain
find /no/such/path | wc -l 2>/dev/null
echo "broken-find|wc-l exit code WITHOUT pipefail: $?"  | tee -a $TASKLOG   # expect 0

# ── Part C: set -o pipefail — fix the silent failure ─────────────────
echo "═══ Part C: WITH pipefail ═══"                    | tee -a $TASKLOG
set -o pipefail
false | true 2>/dev/null
echo "false|true exit code WITH pipefail: $?"           | tee -a $TASKLOG   # expect 1

find /no/such/path | wc -l 2>/dev/null
echo "broken-find|wc-l exit code WITH pipefail: $?"     | tee -a $TASKLOG   # expect 1

# Reset for the rest of the session
set -o pipefail   # leave it ON — good default
echo "═══ pipefail status now: ON (good default) ═══"   | tee -a $TASKLOG

# ── Part D: pipefail under sudo -u (Tier B weave) ─────────────────────
# Run the same false|true and broken-find pipelines AS ${USER} to prove
# pipefail behaves identically across identities. The output also lands
# in ${USER_HOME} so ownership of the evidence file is ${USER}:${GROUP}.
echo "═══ Part D: pipefail under sudo -u ${USER} ═══"   | tee -a $TASKLOG

sudo -u "${USER}" bash -c '
    set +o pipefail
    false | true
    EC_OFF=$?
    set -o pipefail
    false | true
    EC_ON=$?
    {
        echo "as-$(whoami) WITHOUT pipefail: $EC_OFF"
        echo "as-$(whoami) WITH    pipefail: $EC_ON"
    } > '"${USER_HOME}"'/pipefail-asuser.txt
'

cat "${USER_HOME}/pipefail-asuser.txt"                  | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${USER_HOME}/pipefail-asuser.txt" | tee -a $TASKLOG

# Sanity: as ${USER}, EC_OFF must be 0 and EC_ON must be 1 — same as root
grep -q 'WITHOUT pipefail: 0' "${USER_HOME}/pipefail-asuser.txt" \
    && grep -q 'WITH    pipefail: 1' "${USER_HOME}/pipefail-asuser.txt" \
    && echo "✅ pipefail behavior identical under sudo -u ${USER}" \
    || echo "❌ pipefail behavior diverged under sudo -u" \
    | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. **Part A** — `tee` without `-a` creates a new file on the first pass. `tee -a` on the second pass appends. If you use `tee` (without `-a`) twice, the second run wipes what the first wrote — exactly the `>` vs `>>` lesson applied to pipes.
2. **Part B** — `set +o pipefail` (turn it OFF). `false | true` exits 0 because `true` is the last command and it exits 0. The pipeline "succeeded" even though `false` explicitly failed. This is the silent killer in scripts.
3. **Part C** — `set -o pipefail` (turn it ON). Now `false | true` exits 1 because `false` was the rightmost non-zero exit in the pipeline. `find /no/such/path | wc -l` also exits 1.

### Reading it left to right

```
grep 'nologin' /etc/passwd   |   tee -a /tmp/lab03a/report.txt   |   wc -l
│                             │   │                                │   │
│                             │   │                                │   └─ count lines, print to terminal
│                             │   │                                └─ pipe to wc
│                             │   └─ APPEND copy to report.txt (don't wipe prior content)
│                             └─ pipe (FD 1 of grep → FD 0 of tee)
└─ grep filters /etc/passwd
```

### The story

T03-A is the reason sysadmins wake up at 2 AM. A nightly backup script has:
```bash
find /data | gzip > /backup/data.tar.gz
echo "Backup complete"
```
`find` fails because `/data` was unmounted. The `gzip` receives EOF immediately and creates an empty `.tar.gz`. The exit code of `gzip` is 0. The script prints "Backup complete." The on-call engineer sees a green dashboard and goes back to sleep. Three weeks later, someone tries to restore from the backup. It's empty.

One line at the top of the script — `set -o pipefail` — would have made the script exit non-zero at `find | gzip`, triggered the alerting, and prevented the incident.

T03-B is the companion: scripts don't inherit `set -o pipefail` from the interactive shell. You must explicitly set it at the top of each script or it defaults to off.

### Expected output

```text
═══ Part A: tee -a cumulative report ═══
=== Report Pass 1 ===
NAME="Red Hat Enterprise Linux"
VERSION="9.4 (Plow)"
ID="rhel"
ID_LIKE="fedora"
=== Report Pass 2 ===
4
10 /tmp/lab03a/report.txt
=== Report Pass 1 ===
NAME="Red Hat Enterprise Linux"
VERSION="9.4 (Plow)"
═══ Part B: T03-A — false|true without pipefail ═══
false|true exit code WITHOUT pipefail: 0
broken-find|wc-l exit code WITHOUT pipefail: 0
═══ Part C: WITH pipefail ═══
false|true exit code WITH pipefail: 1
broken-find|wc-l exit code WITH pipefail: 1
═══ pipefail status now: ON (good default) ═══
═══ Part D: pipefail under sudo -u labuser_03_pipe ═══
as-labuser_03_pipe WITHOUT pipefail: 0
as-labuser_03_pipe WITH    pipefail: 1
labuser_03_pipe:labgrp_03_pipe 644 /tmp/lab03a/home_labuser_03_pipe/pipefail-asuser.txt
✅ pipefail behavior identical under sudo -u labuser_03_pipe
exit was: 0
```

### Switches

| Token               | Meaning                                                            |
|---------------------|--------------------------------------------------------------------|
| `tee FILE`          | Write stdin to FILE (truncate) and pass to stdout                  |
| `tee -a FILE`       | Write stdin to FILE (append) and pass to stdout                    |
| `set -o pipefail`   | Pipeline exit = rightmost non-zero command's exit                  |
| `set +o pipefail`   | Pipeline exit = last command's exit (default, dangerous in scripts)|
| `false`             | Always exits 1 — no output                                        |
| `true`              | Always exits 0 — no output                                        |

### Concept Card

| Concept | What it does |
|---|---|
| `tee -a` | Append mode — same as `>>` but inside a pipe chain |
| Default pipe exit code | Exit code of the **last** command, regardless of upstream failures |
| `set -o pipefail` | Exit code of the **rightmost non-zero** command in the pipeline |
| Why this matters | Without pipefail, a broken pipeline can report success |
| Script default | `set -o pipefail` is OFF by default — you must set it explicitly |
| **🪤 Trap Risk T03-A** | `false \| true` returns 0 without `set -o pipefail`. Upstream failure is invisible. **Fix:** `set -o pipefail` at the top of every script that uses pipes in `if`/`while` conditions. |
| **🪤 Trap Risk T03-B** | Interactive shell's `set -o pipefail` is NOT inherited by scripts. Each script must set it independently. |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Report built with tee -a | `wc -l /tmp/lab03a/report.txt` > 0 | File has cumulative content from both passes |
| Pass 2 appended (not replaced) | `grep -c '===' /tmp/lab03a/report.txt` returns 2 | Two header lines = two passes |
| T03-A demonstrated | `grep 'WITHOUT pipefail: 0' /tmp/lab03a/task2.txt` | Silent-success proof captured |
| T03-B corrected | `grep 'WITH pipefail: 1' /tmp/lab03a/task2.txt` | Correction also captured |
| Tier B pipefail proof under `${USER}` | `cat "${USER_HOME}/pipefail-asuser.txt"` shows EC_OFF=0 / EC_ON=1 | Pipefail is a shell option, not a privilege option |
| User-owned pipefail evidence | `stat -c '%U:%G' "${USER_HOME}/pipefail-asuser.txt"` returns `labuser_03_pipe:labgrp_03_pipe` | Sudo -u landed evidence ownership |

### Journal write

```bash
LAB=lab-03a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab03a/task2.txt              "$JDIR/evidence.txt"
cp /tmp/lab03a/report.txt             "$JDIR/report.txt"
cp "${USER_HOME}/pipefail-asuser.txt" "$JDIR/pipefail-asuser.txt"

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
TOPIC:    tee vs tee -a; set -o pipefail; T03-A false|true=0 without pipefail; sudo -u USER reproduces pipefail behavior identically
COMMANDS: tee, tee -a, set -o pipefail, set +o pipefail, false, true, sudo -u ${USER} bash -c, stat -c '%U:%G %a %n'
TRAPS:    T03-A and T03-B rehearsed (proved 0 without pipefail, 1 with pipefail)
TIER B:   pipefail-asuser.txt owned by ${USER}:${GROUP}; EC_OFF=0, EC_ON=1 confirmed under sudo -u
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-03c — verify capstone: audit pipefail evidence + destroy-restore of nologin/report (T41)
NOTE:     lab-03b is intentionally absent — Section 18 boundary lab (no honest Ansible module for |, tee, pipefail)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup (per-task — leaves Tier B sandbox intact)

```bash
rm -f /tmp/lab03a/report.txt /tmp/lab03a/warmup2.txt /tmp/lab03a/task2.txt
rm -f "${USER_HOME}/pipefail-asuser.txt"

getent passwd "${USER}"  >/dev/null && echo "✅ ${USER} still present"
getent group  "${GROUP}" >/dev/null && echo "✅ ${GROUP} still present"
test -d       "${SANDBOX}"          && echo "✅ ${SANDBOX} still present"

ls /tmp/lab03a
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `false \| true` exit code is 1 even without pipefail | You forgot `set +o pipefail` — the default was already ON from the warm-up |
| `false \| true` exit code is 0 even WITH pipefail | Check the order: `false \| true` — `true` is last; pipefail makes `false`'s exit code propagate only if it's non-zero |
| `tee -a` created a new file | You used `tee` (without `-a`) on the second run — always `tee -a` for append mode |
| Report shows only one `===` header | Second pass used `tee` instead of `tee -a` and overwrote the first pass |

> **STOP — paste the `false|true` exit codes WITH and WITHOUT pipefail, plus the Part D `✅ pipefail behavior identical under sudo -u ${USER}` line, before running Lab Closeout.**

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# 1) Mount layer (no-op)
awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts \
    | tac | xargs -r -n1 umount -l 2>/dev/null

# 2) User / group teardown
if getent passwd "${USER}" >/dev/null 2>&1; then
    userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
    groupdel "${GROUP}"  2>/dev/null
fi

# 3) Sandbox dir
rm -rf "${SANDBOX}"

# 4) Audit
echo "── Lab 03a cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"              && echo "❌ home remains"    || echo "✅ home gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the four `✅` audit lines before moving to Lab 03c.**

---

## Lab 03a Checklist (2 tasks + closeout)

- [ ] Lab-Wide Setup — Tier B sandbox built; `id ${USER}`, both `getent` lines visible
- [ ] Task 1 — Five pipe chains from `/etc`; `tee` splits to file+downstream; `grep \| wc -l` count pattern; **Chain 6** `sudo -u ${USER}` pipeline produces 24-line user-owned file
- [ ] Task 2 — `tee -a` appends; `false\|true` exits 0 without pipefail; exits 1 with pipefail (T03-A/B); **Part D** pipefail behavior identical under `sudo -u ${USER}`
- [ ] Lab Closeout — four `✅` audit lines; journal in `/root/rhcsa_journal/lab-03a/` survives

---

## Related Labs

| Lab | Connection |
|---|---|
| ⛔ **Lab 03b is intentionally absent** | Section 18 boundary lab — `\|`, `tee`, `set -o pipefail` have no honest Ansible module. `ansible.builtin.shell` with `executable: /bin/bash` can *use* pipefail but is not the same operation. |
| **Lab 03c** — Verifying Pipes | Audit: file has correct content AND correct line count AND correct filter; destroy-restore drill for pipeline evidence |
| Lab 01a — Stdout Redirection | FD 1 redirection that pipes build on |
| Lab 01c — Stdout Verify | Same audit + destroy-restore pattern, FD 1 source artifacts |
| Lab 02a — Stderr Redirection | `2>/dev/null` used in chains when pipeline sources generate Permission denied |
| Lab 02c — Stderr Verify | Stream-separation audit; same Tier B + verify pattern |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
