# Lab 32c: Check Network Connectivity (Verify) — Audit + Destroy/Restore

- **Series:** linux-ops-mastery — Networking Diagnostics
- **Trilogy:** `32a` (RHCSA) → `32b` (Ansible) → `32c` (Verify capstone)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 artifact audit, Task 2 destroy/restore drill)
- **Practice Directory (rotation #18):** `/media`
- **Sandbox (Tier B):** `/tmp/lab32c` with `USER=labuser_32_ping`, `GROUP=labgrp_32_ping`, `USER_HOME=/tmp/lab32c/home_labuser_32_ping`
- **Traps rehearsed this lab:** `T32-A`, `T32-B`, `T41`, `T44`

> This capstone is the auditor seat: no hand-waving, only evidence from `32a` and `32b` artifacts plus explicit restore proof.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📁  PRACTICE DIR: /media"
ls -la /media 2>/dev/null || stat /media
echo "📚 ARTIFACT ROOT: /root/rhcsa_journal"
echo "🕒  TIME:  $(date -Is)"
echo "exit was: $?"
```

---

## Lab-Wide Setup — Tier B Sandbox Stack

```bash
sudo -i

export LAB_NUM=32
export LAB_SLUG=ping
export SANDBOX=/tmp/lab32c
export GROUP=labgrp_32_ping
export USER=labuser_32_ping
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-32c/task1 /root/rhcsa_journal/lab-32c/task2
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /media
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — Audit `32a` + `32b` artifacts and persistence evidence

**Practice directory this task:** `/media`

### 🔁 Warm-Up

```bash
ls -la /media 2>/dev/null || stat /media
hostname -I | tee /tmp/lab32c/warmup1.txt
find /root/rhcsa_journal -maxdepth 2 -type d | sort | tail -n 10
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Audit the trilogy evidence trails from `32a` and `32b`, proving the expected commands, packet-loss checks, and playbooks exist and are readable for reboot-survivable resume.

### 🧵 WEAVE TRACE

| Re-used command | Role in task |
|---|---|
| `find` + `sort` | discovers and orders evidence paths |
| `hostname -I` | context stamp in audit transcript |
| `tee` | live + saved audit record |
| `sudo -u "${USER}"` | writes signed audit note as Tier B user |

### Main command block

```bash
TASKLOG=/tmp/lab32c/task1.txt

echo "== context ==" | tee "${TASKLOG}"
hostname -I | tee -a "${TASKLOG}"

echo "== verify 32a files ==" | tee -a "${TASKLOG}"
find /root/rhcsa_journal/lab-32a -type f 2>/dev/null | sort | tee -a "${TASKLOG}" || true

echo "== verify 32b files ==" | tee -a "${TASKLOG}"
find /root/rhcsa_journal/lab-32b -type f 2>/dev/null | sort | tee -a "${TASKLOG}" || true

echo "== packet-loss evidence grep ==" | tee -a "${TASKLOG}"
grep -Rni "packet loss" /root/rhcsa_journal/lab-32a /root/rhcsa_journal/lab-32b 2>/dev/null | tee -a "${TASKLOG}" || true

echo "== check playbooks exist ==" | tee -a "${TASKLOG}"
test -f /root/rhcsa_journal/lab-32b/playbooks/task1.yml && echo "✅ task1 playbook present" | tee -a "${TASKLOG}"
test -f /root/rhcsa_journal/lab-32b/playbooks/task2.yml && echo "✅ task2 playbook present" | tee -a "${TASKLOG}"

sudo -u "${USER}" bash -c 'echo "task1 audit signed by $(whoami) $(date -Is)" > '"${USER_HOME}"'/task1-user-note.txt'
stat -c '%U:%G %a %n' "${USER_HOME}/task1-user-note.txt" | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Human-Readable Breakdown

- `find` checks if expected journals and playbooks exist.
- `grep packet loss` confirms that connectivity results were recorded.
- `test -f` provides explicit pass/fail for required playbooks.

### Reading it left to right

`grep -Rni "packet loss" /root/rhcsa_journal/lab-32a /root/rhcsa_journal/lab-32b`

- recursive search through both prior labs
- case-insensitive numeric output with file/line context
- confirms diagnostic artifacts were captured, not just run interactively

### The story

Verification labs exist to prevent “I ran it once” confidence. Auditors need file-backed proof that survives reboot and can be inspected later without rerunning experiments.

### Expected output

- lists of files under `/root/rhcsa_journal/lab-32a` and `lab-32b`
- at least one `packet loss` evidence line
- playbook presence checks returning `✅`

### Switches

| Token | Meaning |
|---|---|
| `find -type f` | list regular files only |
| `grep -Rni` | recursive, numbered, case-insensitive search |
| `test -f` | verify file exists |

### 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | artifact-driven verification | proves state from saved outputs |
| ✅ | persistence via `/root/rhcsa_journal` | keeps evidence across reboot |
| ✅ | Tier B user audit note | ensures user/group/file discipline still practiced |
| 🪤 | Trap risk: `T41` | do not skip reboot/persistence reasoning |
| 🪤 | Trap risk: `T44` | no residue after teardown |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| 32a evidence present | `find /root/rhcsa_journal/lab-32a -type f | wc -l` | confirms prior lab artifacts persisted |
| 32b playbooks present | `ls -l /root/rhcsa_journal/lab-32b/playbooks/` | confirms reusable automation persisted |

### 🧹 Cleanup (task-level)

```bash
rm -f /tmp/lab32c/warmup1.txt /tmp/lab32c/task1.txt "${USER_HOME}/task1-user-note.txt"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| missing lab journal files | re-run prior lab tasks before continuing |
| no packet-loss entries | replay bounded ping commands and recapture evidence |

> **STOP — paste audit output before Task 2.**

---

## Task 2 — Destroy/Restore drill (wipe + re-run)

**Practice directory this task:** `/media`

### 🔁 Warm-Up

```bash
ls -la /media 2>/dev/null || stat /media
hostname -I | tee /tmp/lab32c/warmup2.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Simulate state loss by removing temporary artifacts, then restore core connectivity evidence from command reruns and prove completion with explicit checks.

### Main command block

```bash
TASKLOG=/tmp/lab32c/task2.txt

echo "== destroy step ==" | tee "${TASKLOG}"
rm -rf /tmp/lab32a /tmp/lab32b
echo "Destroyed /tmp lab artifacts from 32a/32b" | tee -a "${TASKLOG}"

echo "== restore step ==" | tee -a "${TASKLOG}"
mkdir -p /tmp/lab32a /tmp/lab32b
ping -c 3 -W 2 127.0.0.1 | tee /tmp/lab32a/restore-ping.txt | tee -a "${TASKLOG}"
timeout 10s traceroute -n -w 2 127.0.0.1 | tee /tmp/lab32a/restore-trace.txt | tee -a "${TASKLOG}" || true

ansible-playbook /root/rhcsa_journal/lab-32b/playbooks/task2.yml 2>&1 | tee -a "${TASKLOG}"

echo "== verify restore ==" | tee -a "${TASKLOG}"
test -s /tmp/lab32a/restore-ping.txt && echo "✅ ping restore artifact" | tee -a "${TASKLOG}"
test -s /tmp/lab32a/restore-trace.txt && echo "✅ traceroute restore artifact" | tee -a "${TASKLOG}"
grep -q "0% packet loss" /tmp/lab32a/restore-ping.txt && echo "✅ bounded ping validated" | tee -a "${TASKLOG}"

sudo -u "${USER}" bash -c 'echo "task2 restore complete $(date -Is)" > '"${USER_HOME}"'/task2-user-note.txt'
stat -c '%U:%G %a %n' "${USER_HOME}/task2-user-note.txt" | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Human-Readable Breakdown

- Wipe temporary lab sandboxes to emulate post-incident cleanup/state loss.
- Re-run bounded connectivity checks and regenerate artifacts.
- Re-run assertion playbook from `32b` to revalidate automation path.

### Reading it left to right

`test -s /tmp/lab32a/restore-ping.txt && echo "✅ ping restore artifact"`

- `test -s` confirms file exists and is non-empty
- `&&` prints success only when test passes

### The story

Operations maturity is measured by recovery speed after cleanup or failure. A destroy/restore drill proves commands are repeatable, not one-off lucky runs.

### Expected output

- explicit destroy log lines
- recreated ping/traceroute artifact files
- validation checks printing `✅`

### Switches

| Token | Meaning |
|---|---|
| `rm -rf` | force recursive wipe of temp lab dirs |
| `test -s` | verify non-empty files |
| `grep -q` | quiet pass/fail content test |
| `timeout 10s` | cap command runtime |

### 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | destroy/restore cycle | validates repeatability under clean state |
| ✅ | artifact verification gates | ensures outputs are actually regenerated |
| ✅ | cross-lab replay | reuses 32b playbook as regression check |
| 🪤 | Trap risk: `T32-A` | keep bounded ping flags on reruns |
| 🪤 | Trap risk: `T44` | run teardown audit before lab completion |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| restored ping artifact | `grep -n 'packet loss' /tmp/lab32a/restore-ping.txt` | confirms recreated evidence |
| ansible replay path | `test -f /root/rhcsa_journal/lab-32b/playbooks/task2.yml` | confirms restore can be repeated later |

### 🧹 Cleanup (task-level)

```bash
rm -f /tmp/lab32c/warmup2.txt /tmp/lab32c/task2.txt "${USER_HOME}/task2-user-note.txt"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| restore files empty | rerun bounded commands and inspect network stack |
| playbook fails after wipe | confirm journal playbooks still exist under `/root/rhcsa_journal` |

---

## Section 6 Lab Closeout — Bulletproof Teardown + Audit

```bash
set +e

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi

rm -rf "${SANDBOX}"

echo "── cleanup audit ──"
getent passwd "${USER}" && echo "❌ user remains" || echo "✅ user gone"
getent group  "${GROUP}" && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Author

**Kelvin R. Tobias**
