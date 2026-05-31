# Lab 34a: Inspecting Listening Sockets (RHCSA) — `ss`, `lsof`, `netstat`

- **Series:** linux-ops-mastery — Network Inspection and Service Diagnostics
- **Trilogy:** `34a` (RHCSA hand-typed) -> `34b` (Ansible mirror) -> `34c` (Verify capstone)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation slot 20):** `/var/tmp`
- **Sandbox (Tier B):** `/tmp/lab34a` with `USER=labuser_34_ss`, `GROUP=labgrp_34_ss`
- **Traps rehearsed this lab:** **T34-A** (`ss` without `-n` can trigger DNS/service-name lookups and appear to hang) · **T34-B** (`ss -p` requires root for full process visibility) · **T41** · **T44**

> **This lab's topic:** inspect listening sockets with `ss -tuna`, `ss -tlnp`, `ss -s`, compare with `lsof -i`, and recognize `netstat` as legacy.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /var/tmp"
echo "⚠️  TRAP REMINDERS THIS LAB: T34-A T34-B T41 T44"
ls -ld /var/tmp
command -v ss
command -v lsof || echo "lsof missing"
command -v netstat || echo "netstat missing (net-tools may be absent)"
```

> **STOP — paste header output before setup.**

---

## Objective

1. Capture IPv4 listening sockets with `ss -tuna4` and `ss -tlnp4`.
2. Read high-level socket statistics with `ss -s`.
3. Contrast socket-centric output (`ss`) with process/file-centric output (`lsof -i :22`).
4. Keep `netstat` in your toolkit only as a legacy compatibility command.

---

## Core Reference

| Command | Meaning |
|---|---|
| `ss -tuna4` | TCP/UDP sockets, numeric output, IPv4 only, all states |
| `ss -tlnp4` | TCP listening sockets, numeric, with process info, IPv4 |
| `ss -s` | Socket summary counters |
| `lsof -i :22` | Processes that have network files open on port 22 |
| `netstat -tlnp` | Legacy equivalent view (from `net-tools`) |

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab34a
export GROUP=labgrp_34_ss
export USER=labuser_34_ss
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-34a/task1 /root/rhcsa_journal/lab-34a/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
```

> **STOP — paste `id` and `ls -ld` outputs before Task 1.**

---

## Task 1 — Capture listening sockets with `ss -tuna4` and `ss -tlnp4`

### Purpose

Build the exam reflex for socket inspection snapshots:

- Broad snapshot: `ss -tuna4`
- Focused listening view + process map: `ss -tlnp4`

### Main command block

```bash
TASKLOG=/var/tmp/lab34a-task1.txt

echo "═══ ss -tuna4 snapshot ═══"              | tee "${TASKLOG}"
ss -tuna4                                      2>&1 | tee -a "${TASKLOG}"

echo "═══ ss -tlnp4 as root (full process visibility) ═══" | tee -a "${TASKLOG}"
ss -tlnp4                                      2>&1 | tee -a "${TASKLOG}"

echo "═══ T34-B contrast: same command as non-root ═══"    | tee -a "${TASKLOG}"
sudo -u "${USER}" ss -tlnp4                    2>&1 | tee -a "${TASKLOG}" || true

echo "exit was: $?"                            | tee -a "${TASKLOG}"
```

### Trap callout

- **T34-A:** omit `-n` and `ss` may do name resolution (hosts/services), slowing output or making it look stuck.
- **T34-B:** `-p` shows process ownership reliably only as root; non-root output is incomplete by design.

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-34a/task1
cp /var/tmp/lab34a-task1.txt "${JDIR}/evidence.txt"
```

---

## Task 2 — `ss -s` summary plus `lsof -i :22` contrast

### Purpose

Understand two views of the same system:

- `ss -s`: protocol/socket summary counts
- `lsof -i :22`: which process owns the SSH endpoint

### Main command block

```bash
TASKLOG=/var/tmp/lab34a-task2.txt

echo "═══ socket summary (ss -s) ═══"          | tee "${TASKLOG}"
ss -s                                          2>&1 | tee -a "${TASKLOG}"

echo "═══ port 22 ownership (lsof -i :22) ═══" | tee -a "${TASKLOG}"
lsof -i :22                                    2>&1 | tee -a "${TASKLOG}" || true

echo "═══ legacy check (netstat -tlnp) ═══"    | tee -a "${TASKLOG}"
netstat -tlnp                                  2>&1 | tee -a "${TASKLOG}" || true

echo "exit was: $?"                            | tee -a "${TASKLOG}"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-34a/task2
cp /var/tmp/lab34a-task2.txt "${JDIR}/evidence.txt"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 34a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 34a Checklist

- [ ] Task 1 completed (`ss -tuna4` and `ss -tlnp4` captured; root vs non-root `-p` contrast recorded)
- [ ] Task 2 completed (`ss -s` summary and `lsof -i :22` contrast recorded)
- [ ] T34-A and T34-B trap notes included in evidence
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
