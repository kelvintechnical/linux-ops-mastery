# Lab 14a: Searching with `find` (RHCSA) — predicates, actions, `-print0`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `14a` (RHCSA) → `14b` (Ansible) → `14c` (Verify)
- **Career arcs covered:** RHCSA EX200 ("find every file matching X" tasks), RHCE EX294 (`ansible.builtin.find`), SRE (incident triage: "what changed in the last hour?"), DevOps (cache cleanup), AI/MLOps (checkpoint discovery)
- **Prerequisite:** Lab 13 trilogy complete
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = predicates + `-print0`, Task 2 = multi-predicate RHCSA capstone on `/etc`)
- **Practice Directory (rotation #14):** `/etc`
- **Sandbox:** `/tmp/find-lab` (writes) + `/etc` (read-only capstone target)
- **Traps rehearsed this lab:** **T14-A** (unquoted glob expanded by shell before `find` sees it) · **T14-B** (using `-exec {} \;` when `-exec {} +` is faster and usually correct)

> **This lab's practice directory is: `/etc`** — every task references it in at least two commands.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T14-A T14-B"
echo "📁  PRACTICE DIR: /etc"
echo ""
echo "💡 /etc sample (read-only context for this lab):"
find /etc -maxdepth 1 -type f -name '*.conf' 2>/dev/null | head -n 5
wc -l /etc/passwd
```

> **STOP — paste header output before setup.**

---

## Objective

Make `find` your daily reflex for "I need every file matching X." By the end you can compose multi-predicate searches, run actions per match safely with `-print0 | xargs -0`, and silence permission noise with `2>/dev/null`.

---

## Concept: `find` Walks Live — No Index, No Cache

`find` reads every directory it crawls **right now**. There is no cache. The answer reflects the kernel's view at this moment.

```
   find /etc -name '*.conf' -type f -mtime -7
       │   │    │              │       │
       │   │    │              │       └─ modified within last 7 days
       │   │    │              └─ regular files only
       │   │    └─ filename matches *.conf
       │   └─ starting directory
       └─ the command
```

Predicates are AND'd implicitly. Use `-o` for OR; use `\( ... \)` (escaped parens) to group.

> **Rule one of find:** Quote every glob pattern. The shell expands `*` before `find` ever sees it (T14-A).

---

## Reference (Tasks 1–2)

| Task | Command |
|---|---|
| Filename glob | `find PATH -name '*.conf' 2>/dev/null` |
| Case-insensitive | `find PATH -iname '*.CONF' 2>/dev/null` |
| Only files / dirs | `find PATH -type f` / `-type d` |
| Size filter | `find PATH -type f -size +1M` |
| Age filter | `find PATH -type f -mtime -7` (within 7 days) |
| Owner | `find PATH -user root` |
| Pipe-safe output | `find PATH ... -print0 \| xargs -0 cmd` |
| Per-match action | `find PATH ... -exec cmd {} \;` (slow) |
| Batched action | `find PATH ... -exec cmd {} +` (preferred — T14-B) |
| Silence errors | `... 2>/dev/null` |

---

## Lab-Wide Setup

```bash
sudo -i
mkdir -p /tmp/find-lab
cd /tmp/find-lab

cat > /tmp/find-lab/THIS_DIRECTORY.txt <<'EOF'
/etc — System-wide configuration files

Every daemon, service, and subsystem reads its config from /etc.
No binaries live here — only text files and scripts. Backing up /etc
is backing up the system's identity. RHCSA exams constantly test /etc.

What lives inside it: /etc/passwd, /etc/shadow, /etc/fstab, /etc/ssh/sshd_config,
/etc/yum.repos.d/*.repo, /etc/systemd/system/*.service, /etc/selinux/config.

Why RHCSA cares: "find every .conf file owned by root modified in the last
90 days under /etc" is a canonical exam prompt. This lab's capstone is that prompt.
EOF

cat /tmp/find-lab/THIS_DIRECTORY.txt
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

## Task 1 — Sandbox predicates + `-print0` / `-exec {} +`

**Practice directory this task:** `/etc` · we read `/etc` for context; all writes happen in `/tmp/find-lab`.

### Warm-Up

```bash
find /etc -maxdepth 1 -type f -name '*.conf' 2>/dev/null | wc -l
find /etc -maxdepth 1 -type f -name '*.conf' 2>/dev/null | head -n 3
test -d /tmp/find-lab && echo "sandbox OK"
wc -l /etc/passwd
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 13: `wc -l` counts lines — we use it to count find results before and after.

### Purpose

Build a controlled tree in `/tmp/find-lab`, then practice `-name`, `-type`, `-size`, `-mtime`, `-user`, `-print0 | xargs -0`, and the contrast between `-exec {} \;` (slow) and `-exec {} +` (fast).

### WEAVE TRACE

| Warm-up command | Role inside Task 1 |
|---|---|
| `find /etc ... \| wc -l` | Counts `/etc` conf files as a real-world baseline; repeated on sandbox |
| `find /etc ... \| head -n 3` | Shows sample paths — proves find is returning real data |
| `wc -l /etc/passwd` | Line-count primitive reused in `-exec {} + wc -l {} +` |
| `test -d /tmp/find-lab` | Guards all sandbox operations |
| `2>&1 \| tee` | Captures transcript to `task1/op.txt` |
| `set -o pipefail` | Catches silent failures in piped find chains |

### Main command block

```bash
cd /tmp/find-lab
mkdir -p /tmp/find-lab/task1 logs/2026/01 docs/new
touch logs/2026/01/{a,b,c}.log docs/new/readme.md docs/new/INDEX.TXT
dd if=/dev/zero of=big.bin bs=1M count=2 2>/dev/null
touch -d "40 days ago" old.log

BEFORE=$(find /tmp/find-lab -type f 2>/dev/null | wc -l)
echo "sandbox files before: $BEFORE"                     2>&1 | tee /tmp/find-lab/task1/op.txt

# Name searches (quote the glob — T14-A)
find /tmp/find-lab -name '*.log'                         2>&1 | tee -a /tmp/find-lab/task1/op.txt
find /tmp/find-lab -iname 'index.txt'                    2>&1 | tee -a /tmp/find-lab/task1/op.txt

# Type + size + time
find /tmp/find-lab -type f -size +1M                     2>&1 | tee -a /tmp/find-lab/task1/op.txt
find /tmp/find-lab -type f -mtime +30                    2>&1 | tee -a /tmp/find-lab/task1/op.txt

# -print0 + xargs -0 (pipe-safe)
find /tmp/find-lab -type f -print0 2>/dev/null \
  | xargs -0 ls -l | head -n 5                             2>&1 | tee -a /tmp/find-lab/task1/op.txt

# T14-B contrast: \; vs +
echo "── -exec {} \; (slow, one wc per file) ──"          | tee -a /tmp/find-lab/task1/op.txt
find /tmp/find-lab -type f -name '*.log' -exec wc -l {} \; 2>&1 | tee -a /tmp/find-lab/task1/op.txt

echo "── -exec {} + (fast, one wc for all files) ──"      | tee -a /tmp/find-lab/task1/op.txt
find /tmp/find-lab -type f -name '*.log' -exec wc -l {} + 2>&1 | tee -a /tmp/find-lab/task1/op.txt

AFTER=$(find /tmp/find-lab -type f 2>/dev/null | wc -l)
echo "sandbox files after: $AFTER"                         2>&1 | tee -a /tmp/find-lab/task1/op.txt
echo "exit was: $?"
```

### Human-readable breakdown

Build fixtures, count files, run name/type/size/time predicates, demonstrate `-print0 | xargs -0` for filenames with spaces, then contrast `-exec {} \;` (one `wc` invocation per file) vs `-exec {} +` (one `wc` invocation for all matches batched together).

### Reading it left to right

- `-name '*.log'` — glob match; MUST be quoted or shell expands `*`.
- `-type f` — regular files only (`d`=directory, `l`=symlink).
- `-size +1M` — larger than 1 MiB; `+` means greater, `-` means less.
- `-mtime +30` — modified MORE than 30 days ago (`-30` = within last 30 days).
- `-print0` — null-terminated paths; pair with `xargs -0`.
- `-exec wc -l {} \;` — `\;` ends the `-exec`; one invocation per `{}`.
- `-exec wc -l {} +` — `+` batches all matches into one `wc` call up to ARG_MAX.

### The story

`-exec {} +` is the modern default. On a match set of 1,000 files, `\;` starts 1,000 processes; `+` starts one. The speed difference is dramatic. Reserve `\;` for when the command cannot accept multiple arguments (rare).

### Expected output

```text
sandbox files before: 6
/tmp/find-lab/logs/2026/01/a.log
/tmp/find-lab/logs/2026/01/b.log
...
/tmp/find-lab/docs/new/INDEX.TXT
/tmp/find-lab/big.bin
/tmp/find-lab/old.log
── -exec {} \; (slow, one wc per file) ──
0 /tmp/find-lab/logs/2026/01/a.log
0 /tmp/find-lab/logs/2026/01/b.log
...
── -exec {} + (fast, one wc for all files) ──
0 /tmp/find-lab/logs/2026/01/a.log
0 /tmp/find-lab/logs/2026/01/b.log
0 total
sandbox files after: 6
exit was: 0
```

### Concept Card

| Concept | What it does |
|---|---|
| Live traversal | No index — reflects current filesystem state |
| Quoted globs | Prevents shell expansion before find runs (T14-A) |
| `-print0 \| xargs -0` | Safe pipeline for filenames with spaces/newlines |
| `-exec {} +` | Batched action — preferred over `\;` (T14-B) |
| `2>/dev/null` | Silences permission-denied noise on system paths |
| **🪤 Trap Risk T14-A** | Unquoted `*.log` → shell expands → `find: paths must precede expression` |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Sandbox built | `find /tmp/find-lab -type f \| wc -l` | Structural proof |
| Journal evidence | `wc -l /root/rhcsa_journal/lab-14a/task1/op.txt` | Audit trail |

### Journal write

```bash
LAB=lab-14a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/find-lab/task1/op.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    find predicates + -print0 + exec contrast
COMMANDS: find -name -type -size -mtime, -print0, xargs -0, -exec {} + vs \\;
TRAPS:    T14-A T14-B rehearsed
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — multi-predicate capstone on /etc
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup

```bash
rm -rf /tmp/find-lab/task1
echo "exit was: $?"
```

> **STOP — paste Task 1 evidence before Task 2.**

---

## Task 2 — RHCSA capstone: multi-predicate `find` on `/etc`

**Practice directory this task:** `/etc` · the capstone runs entirely against `/etc` and writes results to `/root/`.

### Warm-Up

```bash
find /etc -type f -name '*.conf' -user root 2>/dev/null | wc -l
find /etc -type f -name '*.conf' -user root -mtime -90 2>/dev/null | wc -l
test -f /etc/passwd && echo "/etc readable"
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Execute the canonical exam prompt: find every file under `/etc` owned by `root`, ending in `.conf`, modified within 90 days, larger than 100 bytes. Save human-readable list to `/root/conf-list.txt` and null-terminated copy to `/root/conf-list.txt0`.

### WEAVE TRACE

| Warm-up command | Role inside Task 2 |
|---|---|
| `find /etc ... \| wc -l` | Progressive predicate narrowing — shows how each filter reduces the set |
| `2>&1 \| tee` | Captures the full find output to evidence file |
| `wc -l` on output | Counts matches — cross-check against null-list count |
| `test -f /etc/passwd` | Guards that `/etc` is accessible before the capstone |
| `set -o pipefail` | Ensures tee/wc chain reports failures |
| `$(date -Is)` | Stamps journal |

### Main command block

```bash
mkdir -p /tmp/find-lab/task2

# Human-readable list
find /etc \
  -type f \
  -name '*.conf' \
  -user root \
  -mtime -90 \
  -size +100c \
  2>/dev/null \
  | tee /root/conf-list.txt \
  | wc -l                                                2>&1 | tee /tmp/find-lab/task2/op.txt

# Null-terminated copy (scripting-safe)
find /etc \
  -type f \
  -name '*.conf' \
  -user root \
  -mtime -90 \
  -size +100c \
  -print0 2>/dev/null \
  > /root/conf-list.txt0

# Verify both outputs
wc -l /root/conf-list.txt
ls -l /root/conf-list.txt0
test -s /root/conf-list.txt && echo "VERIFY: text list non-empty"
tr '\0' '\n' < /root/conf-list.txt0 | grep -c . \
  | awk '{print "null-list count: "$1}'                    2>&1 | tee -a /tmp/find-lab/task2/op.txt
head -n 5 /root/conf-list.txt                            2>&1 | tee -a /tmp/find-lab/task2/op.txt
echo "exit was: $?"
```

### Human-readable breakdown

Five predicates AND'd together. First run pipes through `tee` to save `/root/conf-list.txt` and count with `wc -l`. Second run uses `-print0` redirected to `/root/conf-list.txt0`. Verify both files exist and counts agree.

### The story

Memorize the spine: `find /path -type f -name PAT -user USER -mtime -N -size +Nc 2>/dev/null | tee /out`. Adjust predicates per question. The null-terminated copy (`-print0`) is the scripting-safe variant — counts must match the newline-separated list.

### Expected output

```text
185
185 /root/conf-list.txt
-rw-r--r--. 1 root root 7402 ... /root/conf-list.txt0
VERIFY: text list non-empty
null-list count: 185
/etc/dnf/dnf.conf
/etc/ssh/sshd_config.d/50-redhat.conf
...
exit was: 0
```

### Concept Card

| Concept | What it does |
|---|---|
| Implicit AND | Predicates chained with spaces are AND'd |
| `-print0` vs default `-print` | Null vs newline termination — use `-print0` for pipelines |
| `tee` + redirect | Human list via tee; null list via `>` |
| Count cross-check | `wc -l` must equal `tr '\0' '\n' \| grep -c .` |
| **🪤 Trap Risk** | Counts disagree → a path contains a newline — that's why `-print0` exists |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Text list | `test -s /root/conf-list.txt` | Survives in `/root/` (not `/tmp/`) |
| Null list | `test -s /root/conf-list.txt0` | Scripting-safe artifact |
| Counts agree | Compare `wc -l` vs null-list count | Integrity check |

### Journal write

```bash
LAB=lab-14a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/find-lab/task2/op.txt "$JDIR/evidence.txt"
cp /root/conf-list.txt "$JDIR/conf-list.txt" 2>/dev/null || true

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Multi-predicate find capstone on /etc
COMMANDS: find -type -name -user -mtime -size, -print0, tee, tr, wc -l
TRAPS:    T14-A (quoted '*.conf' throughout)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-14b — ansible.builtin.find for the same predicates
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup

```bash
rm -rf /tmp/find-lab
rm -f /root/conf-list.txt /root/conf-list.txt0
echo "exit was: $?"
```

> **STOP — paste the `wc -l` count and first 5 lines of conf-list.txt before Lab 14b.**

---

## Lab 14a Checklist (2 tasks)

- [ ] Task 1 — Sandbox predicates + `-print0` + `-exec {} +` vs `\;` contrast
- [ ] Task 2 — Multi-predicate capstone on `/etc` → `/root/conf-list.txt` + null-terminated copy

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 14b** — find via Ansible | `ansible.builtin.find` — same predicates declaratively |
| **Lab 14c** — Verifying find results | Diff declared baseline vs live find output |
| Lab 15 — locate | The index-backed fast alternative (stale but instant) |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
