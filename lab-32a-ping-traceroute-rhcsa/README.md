# Lab 32a: Check Network Connectivity (RHCSA) — `ping`, `traceroute`, `mtr`, `hostname -I`

- **Series:** linux-ops-mastery — Networking Diagnostics
- **Trilogy:** `32a` (RHCSA hand-typed) → `32b` (Ansible) → `32c` (Verify capstone)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 canonical ping workflow, Task 2 traceroute contrast with timeout wrapper)
- **Practice Directory (rotation #18):** `/media`
- **Sandbox (Tier B):** `/tmp/lab32a` with `USER=labuser_32_ping`, `GROUP=labgrp_32_ping`, `USER_HOME=/tmp/lab32a/home_labuser_32_ping`
- **Traps rehearsed this lab:** `T32-A` (running `ping` without `-c` hangs scripts), `T32-B` (`ping` vs `ping -6`/`ping6` IPv6 mismatch), `T41`, `T44`

> **This lab's practice directory is: `/media`** — on hosts where `/media` is empty, use `stat /media` as the context proof and continue.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T32-A T32-B T41 T44"
echo "📁  PRACTICE DIR: /media"
ls -la /media 2>/dev/null || stat /media
echo "exit was: $?"
```

---

## Lab-Wide Setup — Tier B Sandbox Stack

```bash
sudo -i

export LAB_NUM=32
export LAB_SLUG=ping
export SANDBOX=/tmp/lab32a
export GROUP=labgrp_32_ping
export USER=labuser_32_ping
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-32a/task1 /root/rhcsa_journal/lab-32a/task2
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /media
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — `ping -c -W` loopback + IPv6 contrast

**Practice directory this task:** `/media` — use it for context checks even though diagnostics are network-focused.

### 🔁 Warm-Up

```bash
ls -la /media 2>/dev/null || stat /media
hostname -I | tee /tmp/lab32a/warmup-ip.txt
ip -o -4 addr show | tee -a /tmp/lab32a/warmup-ip.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Practice safe, bounded ICMP checks for scripts: fixed packet count (`-c`) plus deadline/wait (`-W`) and explicit IPv4/IPv6 contrast so silent IPv6 failures are visible.

### 🧵 WEAVE TRACE

| Re-used command | Role in this task |
|---|---|
| `hostname -I` | Captures local addressing context into evidence |
| `tee` | Saves command transcript while still showing terminal output |
| `ls`/`stat /media` | Confirms rotation directory requirement before diagnostics |
| `sudo -u "${USER}"` | Executes one evidence write as Tier B lab user |

### Main command block

```bash
TASKLOG=/tmp/lab32a/task1.txt

echo "== context ==" | tee "${TASKLOG}"
hostname -I | tee -a "${TASKLOG}"

echo "== ipv4 loopback ==" | tee -a "${TASKLOG}"
ping -c 3 -W 2 127.0.0.1 | tee -a "${TASKLOG}"

echo "== ipv6 loopback contrast ==" | tee -a "${TASKLOG}"
ping -c 3 ::1 | tee -a "${TASKLOG}" || true
ping -6 -c 3 -W 2 ::1 | tee -a "${TASKLOG}" || true

sudo -u "${USER}" bash -c 'echo "task1 evidence by $(whoami) $(date -Is)" > '"${USER_HOME}"'/task1-user-note.txt'
stat -c '%U:%G %a %n' "${USER_HOME}/task1-user-note.txt" | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Human-Readable Breakdown

- `ping -c 3 -W 2 127.0.0.1` sends exactly 3 packets and waits only 2 seconds per reply.
- `ping -c 3 ::1` and `ping -6 -c 3 -W 2 ::1` force the IPv6 path and show whether IPv6 is operational.
- `|| true` allows labs to continue on hosts where IPv6 loopback policy differs.

### Reading it left to right

`ping -c 3 -W 2 127.0.0.1`

- `ping` = ICMP echo tool
- `-c 3` = stop after 3 probes (prevents hang trap)
- `-W 2` = wait 2 seconds for each reply
- `127.0.0.1` = local IPv4 loopback target

### The story

On real incidents, unbounded `ping` creates stuck automation and misleading success criteria. Script-safe checks always set count/time limits and explicitly distinguish IPv4 from IPv6 behavior.

### Expected output

- `3 packets transmitted, 3 received, 0% packet loss` for `127.0.0.1`
- IPv6 line may show success or failure depending on host config
- `stat` line should show `labuser_32_ping:labgrp_32_ping`

### Switches

| Token | Meaning |
|---|---|
| `-c 3` | send three packets then stop |
| `-W 2` | per-packet reply timeout |
| `-6` | force IPv6 route family |
| `tee -a` | append transcript evidence |

### 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | bounded ping | prevents infinite run in scripts |
| ✅ | IPv4 vs IPv6 split | surfaces family-specific failures |
| ✅ | Tier B user/group write | keeps user/group/file reflex active |
| 🪤 | Trap risk: `T32-A` | never run scripted ping without `-c` |
| 🪤 | Trap risk: `T32-B` | test both `ping` and `ping -6` paths explicitly |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Evidence file as lab user | `stat -c '%U:%G %n' "${USER_HOME}/task1-user-note.txt"` | proves Tier B ownership |
| Packet-loss evidence captured | `grep -n 'packet loss' "${TASKLOG}"` | confirms reproducible results |

### 🧹 Cleanup (task-level)

```bash
rm -f /tmp/lab32a/warmup-ip.txt /tmp/lab32a/task1.txt "${USER_HOME}/task1-user-note.txt"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Command never returns | add `-c` and `-W` (T32-A) |
| IPv6 line always fails | use `ping -6` explicitly and treat as contrast signal (T32-B) |

> **STOP — paste Task 1 output before Task 2.**

---

## Task 2 — `traceroute` bounded probes with offline-safe timeout wrapper

**Practice directory this task:** `/media` (repeat rotation check).

### 🔁 Warm-Up

```bash
ls -la /media 2>/dev/null || stat /media
hostname -I | tee /tmp/lab32a/warmup2.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Use numeric traceroute and limited hops to get route evidence quickly, while tolerating offline lab hosts by wrapping internet probe in a hard timeout.

### 🧵 WEAVE TRACE

| Re-used command | Role in this task |
|---|---|
| `hostname -I` | context lines at top of route log |
| `tee` | dual output + artifact capture |
| `ls/stat /media` | keeps directory rotation active |
| `sudo -u "${USER}"` | writes secondary evidence as Tier B user |

### Main command block

```bash
TASKLOG=/tmp/lab32a/task2.txt

echo "== context ==" | tee "${TASKLOG}"
hostname -I | tee -a "${TASKLOG}"

echo "== local traceroute ==" | tee -a "${TASKLOG}"
traceroute -n -w 2 127.0.0.1 | tee -a "${TASKLOG}"

echo "== internet traceroute bounded ==" | tee -a "${TASKLOG}"
timeout 10s traceroute -m 5 8.8.8.8 | tee -a "${TASKLOG}" || true

echo "== mtr snapshot ==" | tee -a "${TASKLOG}"
timeout 10s mtr -r -c 3 127.0.0.1 | tee -a "${TASKLOG}" || true

sudo -u "${USER}" bash -c 'echo "task2 traceroute note $(date -Is)" > '"${USER_HOME}"'/task2-user-note.txt'
stat -c '%U:%G %a %n' "${USER_HOME}/task2-user-note.txt" | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Human-Readable Breakdown

- `traceroute -n -w 2 127.0.0.1` verifies local stack with numeric output and short waits.
- `timeout 10s traceroute -m 5 8.8.8.8` limits hop count and total runtime for offline-safe behavior.
- `mtr -r -c 3` gives a compact report mode sample.

### Reading it left to right

`timeout 10s traceroute -m 5 8.8.8.8`

- `timeout 10s` hard-stop wrapper for slow/unreachable routes
- `traceroute` path probe utility
- `-m 5` max five hops
- target `8.8.8.8` as external contrast

### The story

Routing checks are evidence-gathering tools, not long-running commands. Bounded probes keep troubleshooting fast and script-friendly even on disconnected training boxes.

### Expected output

- A short local route to `127.0.0.1`
- External probe may succeed or timeout/fail (acceptable in this lab)
- Tier B `stat` ownership line for task2 note

### Switches

| Token | Meaning |
|---|---|
| `-n` | show numeric hops, skip DNS lookup |
| `-w 2` | wait 2s per probe reply |
| `-m 5` | cap max hops |
| `timeout 10s` | hard stop the whole command |
| `mtr -r -c 3` | report mode with 3 cycles |

### 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | numeric traceroute | faster, deterministic output |
| ✅ | timeout wrappers | prevents hanging diagnostics |
| ✅ | mtr report snapshot | quick packet-loss/latency summary |
| 🪤 | Trap risk: `T41` | verify persistence evidence before moving on |
| 🪤 | Trap risk: `T44` | complete cleanup audit to avoid residue |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| traceroute evidence saved | `test -s /tmp/lab32a/task2.txt && wc -l /tmp/lab32a/task2.txt` | confirms artifact exists |
| user note ownership | `stat -c '%U:%G %n' "${USER_HOME}/task2-user-note.txt"` | confirms Tier B ownership path |

### 🧹 Cleanup (task-level)

```bash
rm -f /tmp/lab32a/warmup2.txt /tmp/lab32a/task2.txt "${USER_HOME}/task2-user-note.txt"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| traceroute too slow | add `-n`, reduce `-m`, keep `timeout 10s` wrapper |
| `mtr` missing | install package or keep this step as optional contrast |

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
