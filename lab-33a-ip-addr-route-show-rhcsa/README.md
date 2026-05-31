# Lab 33a: Display IP and Routing Info (RHCSA)

- **Series:** linux-ops-mastery - Documentation & Networking
- **Trilogy:** `33a` (RHCSA hand-typed) -> `33b` (Ansible mirror) -> `33c` (Verify capstone)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation #33):** `/mnt`
- **Sandbox (Tier B):** `/tmp/lab33a` with `USER=labuser_33_ipshow`, `GROUP=labgrp_33_ipshow`
- **Traps rehearsed this lab:** **T33-A** (`ip addr show` vs `ip a`; avoid deprecated `ifconfig`) · **T33-B** (`ip route show` alone can miss policy routes; compare with `show table all`) · **T41** · **T44**

> **This lab's topic:** inspect local interface addressing and routing state using `ip addr show`, `ip -br addr`, `ip route show`, `ip -6 route`, and `ip link`.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /mnt"
echo "⚠️  TRAP REMINDERS THIS LAB: T33-A T33-B T41 T44"
ls -ld /mnt /tmp 2>/dev/null || true
ip -V
```

> **STOP - paste header output before setup.**

---

## Objective

Build exam-safe reflexes for quick network inspection:

1. Read interface and address state clearly with `ip -br addr show` and `ip addr show lo`.
2. Compare visible routes from default table output vs all policy tables.
3. Capture IPv4 + IPv6 route evidence to files under the sandbox for replay and verification.

---

## Core Reference

| Command | Meaning |
|---|---|
| `ip -br addr show` | Brief one-line-per-interface address view |
| `ip addr show lo` | Full detail for loopback device |
| `ip link` | Link state (UP/DOWN, MTU, flags, qdisc) |
| `ip route show` | IPv4 routes from main/default view |
| `ip route show table all` | Routes across all policy tables |
| `ip -6 route` | IPv6 routing table |

---

## Lab-Wide Setup - Tier B Sandbox

```bash
sudo -i

export LAB_NUM=33
export LAB_SLUG=ipshow
export SANDBOX=/tmp/lab33a
export GROUP=labgrp_33_ipshow
export USER=labuser_33_ipshow
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-33a/task1 /root/rhcsa_journal/lab-33a/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
```

> **STOP - paste `id` and both `ls -ld` lines before Task 1.**

---

## Task 1 - Inspect interface addressing (`ip -br`, `ip addr`, `ip link`)

### Purpose

Read both compact and detailed views of interface state and store evidence to disk:

- `ip -br addr show` gives the fast exam scan.
- `ip addr show lo` gives full structured output for one interface.
- `ip link` confirms carrier/state context around interface addresses.

### Main command block

```bash
TASKLOG=/tmp/lab33a/task1.txt

echo "=== ip -br addr show ==="                   | tee "${TASKLOG}"
ip -br addr show                                 | tee -a "${TASKLOG}"

echo "=== ip addr show lo ==="                   | tee -a "${TASKLOG}"
ip addr show lo                                  | tee -a "${TASKLOG}"

echo "=== ip link ==="                           | tee -a "${TASKLOG}"
ip link                                          | tee -a "${TASKLOG}"

cp "${TASKLOG}" /tmp/lab33a/ip-addressing-snapshot.txt
ls -l /tmp/lab33a/ip-addressing-snapshot.txt     | tee -a "${TASKLOG}"
echo "exit was: $?"                              | tee -a "${TASKLOG}"
```

### Trap callout

- **T33-A:** `ip a` is an alias shorthand, but RHCSA clarity standard is `ip addr show`; avoid `ifconfig` because it is deprecated and often absent on minimal systems.

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-33a/task1
cp /tmp/lab33a/task1.txt "${JDIR}/evidence.txt"
cp /tmp/lab33a/ip-addressing-snapshot.txt "${JDIR}/ip-addressing-snapshot.txt"
```

---

## Task 2 - Inspect routes (`ip route show`, `table all`, `ip -6 route`)

### Purpose

Capture IPv4/IPv6 routing data and compare the default route view to full policy-table output.

### Main command block

```bash
TASKLOG=/tmp/lab33a/task2.txt

echo "=== ip route show ==="                     | tee "${TASKLOG}"
ip route show                                    | tee -a "${TASKLOG}"

echo "=== ip route show table all ==="           | tee -a "${TASKLOG}"
ip route show table all                          | tee -a "${TASKLOG}"

echo "=== ip -6 route ==="                       | tee -a "${TASKLOG}"
ip -6 route                                      | tee -a "${TASKLOG}"

ip route show > /tmp/lab33a/routes-main.txt
ip route show table all > /tmp/lab33a/routes-all.txt
ip -6 route > /tmp/lab33a/routes-ipv6.txt

wc -l /tmp/lab33a/routes-main.txt /tmp/lab33a/routes-all.txt /tmp/lab33a/routes-ipv6.txt \
  | tee -a "${TASKLOG}"
echo "exit was: $?"                              | tee -a "${TASKLOG}"
```

### Trap callout

- **T33-B:** `ip route show` may omit routes from non-main policy tables; always compare with `ip route show table all` during troubleshooting.

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-33a/task2
cp /tmp/lab33a/task2.txt "${JDIR}/evidence.txt"
cp /tmp/lab33a/routes-main.txt "${JDIR}/routes-main.txt"
cp /tmp/lab33a/routes-all.txt "${JDIR}/routes-all.txt"
cp /tmp/lab33a/routes-ipv6.txt "${JDIR}/routes-ipv6.txt"
```

---

## Lab Closeout - Bulletproof Teardown (Section 6)

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 33a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 33a Checklist

- [ ] Task 1 completed (`ip -br addr show`, `ip addr show lo`, and `ip link` captured to files)
- [ ] Task 2 completed (`ip route show`, `ip route show table all`, and `ip -6 route` captured to files)
- [ ] T33-A and T33-B trap notes recorded in evidence
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
