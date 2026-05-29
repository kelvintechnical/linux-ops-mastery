# Lab 16a: Search for a String and Save Output (RHCSA) — `grep`, `tee`, `>`, `>>`

- **Series:** linux-ops-mastery — Shell Search and Output Capture
- **Trilogy:** `16a` (RHCSA hand-typed) → [`16b`](../lab-16b-grep-search-save-output-ansible/) (Ansible) → [`16c`](../lab-16c-grep-search-save-output-verify/) (Verify)
- **Tasks:** 2 (Task 1 = `grep ... | tee` basic save with Tier B `sudo -u` weave; Task 2 = regex + root-owned target with `sudo tee` and broken contrast)
- **Practice Directory (rotation slot):** `/sbin`
- **Sandbox (Tier B):** `/tmp/lab16a`, `USER=labuser_16_grepsave`, `GROUP=labgrp_16_grepsave`
- **Traps rehearsed this lab:** `T16-A` (greedy regex matches more than expected) · `T16-B` (`sudo cmd > file` fails for root file writes) · `T41` · `T44`

> **This lab's practice directory is: `/sbin`** — admin command namespace (usually symlinked to `/usr/sbin` on modern RHEL-family systems). We reference it directly in each task while writing artifacts only under `/tmp/lab16a`.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T16-A T16-B T41 T44"
echo "📁  PRACTICE DIR: /sbin"
```

> **STOP — paste header output before setup.**

---

## Lab-Wide Setup — Tier B Sandbox Stack

```bash
sudo -i

export LAB_NUM=16
export LAB_SLUG=grepsave
export SANDBOX=/tmp/lab16a
export GROUP=labgrp_16_grepsave
export USER=labuser_16_grepsave
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-16a/task1
mkdir -p /root/rhcsa_journal/lab-16a/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
/sbin contains administration-focused binaries (service control, system tools, low-level maintenance).
On modern systems, /sbin is commonly a symlink to /usr/sbin, but exam tasks still reference /sbin paths.
Using /sbin here builds muscle memory for admin-command search scopes while keeping writes in /tmp sandbox.
EOF

id "${USER}"
ls -ld /sbin "${SANDBOX}" "${USER_HOME}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste `id`, `ls -ld`, and final exit line before Task 1.**

---

## Task 1 — Basic save: `grep PATTERN FILE | tee output.txt`

**Practice directory this task:** `/sbin` — we search command names from `/sbin` and save matches into sandbox artifacts.

### Warm-Up

```bash
ls -ld /sbin
find /sbin -maxdepth 1 -type l -o -type f 2>/dev/null | head -5
echo "networking dns service restart" > /tmp/lab16a/source1.txt
grep -n "service" /tmp/lab16a/source1.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Capture grep matches to screen and file simultaneously using `tee`, then append an audit line with `tee -a`. Include Tier B weave by writing one search line as `${USER}` and proving ownership.

### WEAVE TRACE

| Warm-up / setup command | Role inside Task 1 |
|---|---|
| `ls -ld /sbin` | Confirms practice directory before search commands |
| `find /sbin ...` | Supplies command names to grep pipeline |
| `grep -n` | Same flag appears in main block evidence grep |
| `echo ... > file` | Seeds searchable content before tee capture |
| `id "${USER}"` (setup) | Verifies Tier B actor used in `sudo -u` write |

### Main Command Block

```bash
TASKLOG=/tmp/lab16a/task1.txt

# Build a searchable list from /sbin and local sample
ls -1 /sbin 2>/dev/null | tee /tmp/lab16a/sbin-list.txt
printf "service\nsocket\ntimer\nservice-account\n" > /tmp/lab16a/source1.txt

# Canonical pattern: grep -> tee
grep -n "service" /tmp/lab16a/source1.txt | tee /tmp/lab16a/output.txt
grep -n "sh" /tmp/lab16a/sbin-list.txt 2>/dev/null | tee -a /tmp/lab16a/output.txt

# Tier B weave: user writes one line; root verifies ownership/content
sudo -u "${USER}" bash -c 'echo "service-user-line" > '"${USER_HOME}"'/task1-user.txt'
grep -n "service" "${USER_HOME}/task1-user.txt" | tee -a /tmp/lab16a/output.txt
stat -c '%U:%G %a %n' "${USER_HOME}/task1-user.txt" | tee -a /tmp/lab16a/output.txt

# Add timestamped audit line with append-mode tee
echo "audit $(date -Is) by $(whoami)" | tee -a /tmp/lab16a/output.txt >/dev/null

wc -l /tmp/lab16a/output.txt | tee "$TASKLOG"
echo "exit was: $?"
```

### Human-Readable Breakdown

- `grep -n ... | tee output.txt` prints matches and saves the same lines.
- `tee -a` appends without truncating prior evidence.
- `/sbin` listing gives real admin-command search input.
- `sudo -u "${USER}" ...` creates a user-owned artifact for Tier B repetition.
- `stat -c '%U:%G'` proves user/group ownership actually changed.

### Reading It Left to Right

```text
grep -n "service" /tmp/lab16a/source1.txt | tee /tmp/lab16a/output.txt
│    │              │                       │
│    │              │                       └─ writes same stream to file + terminal
│    │              └─ source file
│    └─ show line numbers with each match
└─ search for matching lines
```

### The Story

RHCSA tasks often say "save the output" and learners default to only `>` redirection. `tee` is better when you must both see and preserve output for evidence. This task builds that reflex while rehearsing user/group ownership checks.

### Expected Output

```text
1:service
4:service-account
<zero or more /sbin 'sh' matches>
1:service-user-line
labuser_16_grepsave:labgrp_16_grepsave 644 /tmp/lab16a/home_labuser_16_grepsave/task1-user.txt
```

### Switches

| Token | Meaning |
|---|---|
| `grep -n` | Show matching line numbers |
| `tee` | Copy stdin to stdout and file |
| `tee -a` | Append instead of overwrite |
| `sudo -u USER` | Run command as specific user |
| `stat -c` | Custom ownership/permission output |

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | `grep pattern file` | Filters lines containing pattern |
| ✅ | `| tee file` | Saves and displays same stream |
| ✅ | `tee -a file` | Preserves earlier lines and appends |
| ✅ | Tier B `sudo -u` write | Forces user/group/file ownership practice |
| 🪤 Trap Risk | What goes wrong | How to avoid |
| ⚠️ `T16-A` | Loose pattern (like `serv.*`) can match too broadly | Start with exact text, then widen intentionally |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Match file saved | `test -s /tmp/lab16a/output.txt && wc -l /tmp/lab16a/output.txt` | Proves capture landed on disk |
| Tier B ownership | `stat -c '%U:%G' "${USER_HOME}/task1-user.txt"` | Confirms user/group weave |
| Practice dir inspected | `ls -ld /sbin` | Confirms target scope used |

### Journal Write

```bash
LAB=lab-16a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cp /tmp/lab16a/output.txt "$JDIR/output.txt"
cp /tmp/lab16a/task1.txt  "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    grep + tee capture to file while displaying output
COMMANDS: grep -n, tee, tee -a, sudo -u ${USER}, stat -c
TRAPS:    T16-A rehearsed (pattern breadth awareness)
NEXT:     task2 regex + root-owned write with sudo tee
EOF

echo "Journal written: $(ls -la "$JDIR")"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab16a/source1.txt /tmp/lab16a/sbin-list.txt /tmp/lab16a/output.txt /tmp/lab16a/task1.txt
rm -f "${USER_HOME}/task1-user.txt"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Output file is empty | Confirm source file has matching lines and rerun grep |
| No `/sbin` list produced | Use `ls -1 /sbin 2>/dev/null` and verify permissions |
| Tier B file is root-owned | Re-run write via `sudo -u "${USER}" ...` |

> **STOP — paste grep + stat evidence before Task 2.**

---

## Task 2 — Regex into root-owned file: broken `sudo grep >` vs fixed `| sudo tee`

**Practice directory this task:** `/sbin` — regex search includes `/sbin` command list to reinforce admin path targeting.

### Warm-Up

```bash
ls -ld /sbin
ls -1 /sbin 2>/dev/null | head -10 > /tmp/lab16a/sbin-mini.txt
grep -E 'sh$|ctl$' /tmp/lab16a/sbin-mini.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Use `grep -E` to capture regex matches into a root-owned file correctly with `sudo tee`, and contrast with the broken `sudo grep ... > /root/file` pattern to rehearse `T16-B`.

### WEAVE TRACE

| Warm-up / setup command | Role inside Task 2 |
|---|---|
| `ls -ld /sbin` | Verifies practice dir before search |
| `ls -1 /sbin ... > file` | Builds regex source data |
| `grep -E ...` | Same regex operator used in final capture |
| `getent passwd "${USER}"` (setup) | Confirms Tier B identity exists for contrast checks |

### Main Command Block

```bash
TASKLOG=/tmp/lab16a/task2.txt
ROOT_OUT=/root/lab16a-regex.txt

ls -1 /sbin 2>/dev/null > /tmp/lab16a/sbin-task2.txt

# T16-A rehearsal: greedy pattern catches more than intended
grep -E 's.*h' /tmp/lab16a/sbin-task2.txt | head -5 | tee /tmp/lab16a/greedy-preview.txt
grep -E 'sh$'  /tmp/lab16a/sbin-task2.txt | head -5 | tee /tmp/lab16a/precise-preview.txt

# Broken pattern (demonstration): redirect is done by current shell, not sudo process
sudo -u "${USER}" grep -E 'sh$' /tmp/lab16a/sbin-task2.txt > "${ROOT_OUT}" 2>/tmp/lab16a/broken.err || true

# Correct pattern: escalate writer via sudo tee
grep -E 'sh$|ctl$' /tmp/lab16a/sbin-task2.txt | sudo tee "${ROOT_OUT}" >/dev/null
echo "captured by $(whoami) at $(date -Is)" | sudo tee -a "${ROOT_OUT}" >/dev/null

sudo ls -l "${ROOT_OUT}" | tee "$TASKLOG"
sudo grep -cE 'sh$|ctl$' "${ROOT_OUT}" | tee -a "$TASKLOG"
sudo tail -n 1 "${ROOT_OUT}" | tee -a "$TASKLOG"
echo "exit was: $?"
```

### Human-Readable Breakdown

- `grep -E` enables extended regex alternation (`|`) and anchors (`$`).
- Broken form: `sudo grep ... > /root/file` fails because `>` happens in the non-root shell.
- Fixed form: pipe to `sudo tee /root/file`, so privileged process performs write.
- `tee -a` appends footer evidence without truncating root output.

### Reading It Left to Right

```text
grep -E 'sh$|ctl$' /tmp/lab16a/sbin-task2.txt | sudo tee /root/lab16a-regex.txt
│      │               │                        │
│      │               │                        └─ privileged writer to root-owned target
│      │               └─ input list
│      └─ extended regex: ends with sh OR ctl
└─ matcher produces selected lines
```

### The Story

Many admins memorize "add sudo in front" and still fail root-file captures because redirection belongs to the current shell, not the command. `tee` solves this by moving write responsibility into the elevated process. This is a common exam and production pitfall.

### Expected Output

```text
-rw-r--r--. 1 root root <size> <date> /root/lab16a-regex.txt
<count>
captured by root at <timestamp>
```

### Switches

| Token | Meaning |
|---|---|
| `grep -E` | Enable extended regex |
| `$` | Anchor to end of line |
| `|` (regex) | Alternation (OR) |
| `sudo tee FILE` | Write file as elevated user |
| `tee -a` | Append to existing file |

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | `grep -E` | Uses ERE syntax for richer matching |
| ✅ | Anchored match `sh$` | Reduces accidental overmatch |
| ✅ | `sudo tee` for root writes | Fixes shell-redirection privilege trap |
| ✅ | `tee -a` | Adds evidence line safely |
| 🪤 Trap Risk | What goes wrong | How to avoid |
| ⚠️ `T16-B` | `sudo cmd > /root/file` still fails write permissions | Pipe output into `sudo tee /root/file` |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Root output created | `sudo test -s /root/lab16a-regex.txt && sudo wc -l /root/lab16a-regex.txt` | Proves elevated write succeeded |
| Regex scope correct | `sudo grep -cE 'sh$|ctl$' /root/lab16a-regex.txt` | Confirms intended pattern matched |
| Trap evidence captured | `test -s /tmp/lab16a/broken.err || true` | Shows broken redirect attempt was rehearsed |

### Journal Write

```bash
LAB=lab-16a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

sudo cp /root/lab16a-regex.txt "$JDIR/lab16a-regex.txt"
cp /tmp/lab16a/task2.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    grep -E save to root-owned file using sudo tee
COMMANDS: grep -E, grep -cE, sudo tee, tee -a
TRAPS:    T16-B rehearsed (broken redirect vs sudo tee), T16-A previewed
NEXT:     lab-16b ansible shell + register + failed_when stdout length checks
EOF

echo "Journal written: $(ls -la "$JDIR")"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab16a/sbin-mini.txt /tmp/lab16a/sbin-task2.txt /tmp/lab16a/greedy-preview.txt
rm -f /tmp/lab16a/precise-preview.txt /tmp/lab16a/broken.err /tmp/lab16a/task2.txt
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `Permission denied` on `/root/lab16a-regex.txt` | Replace redirect with `... | sudo tee /root/lab16a-regex.txt` |
| Regex count too high | Tighten pattern with anchors (`$`) and explicit alternation |
| No matches | Inspect source file with `head` and adjust pattern |

> **STOP — paste root-file verification before Lab Closeout.**

---

## Lab Closeout — Section 6 Bulletproof Teardown

```bash
set +e

# 1) Container layer (no-op for this lab)
podman ps -aq --filter "name=^${CTR}$" 2>/dev/null | xargs -r podman rm -f >/dev/null 2>&1

# 2) Mount layer
awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

# 3) LVM layer (no-op for this lab)
if vgs "${VG}" >/dev/null 2>&1; then
    lvremove -fy "${VG}" 2>/dev/null
    vgremove -fy "${VG}" 2>/dev/null
    pvremove -ffy /dev/loop* 2>/dev/null
fi

# 4) Loopback layer (no-op for this lab)
losetup -j "${SANDBOX}/disk.img" 2>/dev/null | cut -d: -f1 | xargs -r losetup -d 2>/dev/null

# 5) User/group
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi

# 6) Sandbox dir
rm -rf "${SANDBOX}"

# 7) Audit
echo "── cleanup audit ──"
getent passwd "${USER}" && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" && echo "❌ group remains" || echo "✅ group gone"
vgs "${VG}" 2>/dev/null && echo "❌ VG remains" || echo "✅ vg gone"
losetup -l | grep -q "${SANDBOX}" && echo "❌ loop remains" || echo "✅ loop gone"
podman ps -a --filter "name=^${CTR}$" --format '{{.Names}}' | grep -q . && echo "❌ ctr remains" || echo "✅ ctr gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste all cleanup audit lines. Any `❌` means fix before declaring lab complete.**

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
