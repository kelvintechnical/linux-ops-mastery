# Lab 31a: Configure a Static IP Address (RHCSA) - nmcli

- **Series:** linux-ops-mastery
- **Trilogy:** `31a` (RHCSA hand-typed) -> `31b` (Ansible) -> `31c` (Verify)
- **Practice Directory:** `/run`
- **Tier B Sandbox:** `/tmp/lab31a`
- **Lab User/Group:** `labuser_31_staticip` / `labgrp_31_staticip`
- **Test Connection:** `lab31test` only (never modify real management NIC)
- **Traps rehearsed:** `T31-A`, `T31-B`, `T41`, `T44`

This lab's practice directory is: `/run`

---

## LAB HEADER

```bash
echo "ENV CHECK"
echo "TIME: $(date -Is)"
echo "USER: $(whoami)@$(hostname)"
echo "PRACTICE DIR: /run"
echo "TEST CONNECTION: lab31test"
ip -br link | tee /tmp/lab31a_header_links.txt
nmcli con show | tee /tmp/lab31a_header_connections.txt
echo "TRAPS: T31-A T31-B T41 T44"
echo "exit was: $?"
```

> STOP and confirm header output before continuing.

---

## Lab-Wide Tier B Setup (run before Task 1)

```bash
sudo -i
export LAB_NUM=31
export LAB_SLUG=staticip
export SANDBOX=/tmp/lab31a
export GROUP=labgrp_31_staticip
export USER=labuser_31_staticip
export USER_HOME=${SANDBOX}/home_${USER}
export CON_NAME=lab31test

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-31a/task1 /root/rhcsa_journal/lab-31a/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
/run is tmpfs runtime state rebuilt on boot. It stores pid files, sockets,
and transient daemon metadata. Practicing here trains safe handling of
runtime-only data and reinforces reboot-persistence checks.
EOF

id "${USER}"
ls -ld /run "${SANDBOX}" "${USER_HOME}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 - Build Static IPv4 Profile with `nmcli con add/mod`

Practice directory this task: `/run`

### Warm-Up

```bash
pwd
ls -ld /run
ip -br addr show
nmcli con show | head -n 10
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### WEAVE TRACE

- `ip -br addr show` -> baseline before static config.
- `nmcli con show` -> verifies profile creation and persistence fields.
- `ls -ld /run` -> confirms runtime target context before evidence writes.

### Purpose

Create a safe test-only NetworkManager profile (`lab31test`) on loopback, set static IPv4 fields with `nmcli con mod`, and capture evidence with `tee` without touching real interfaces.

### Main Block

```bash
export SANDBOX=/tmp/lab31a
export CON_NAME=lab31test
export TEST_IP=198.51.100.31/24
export TEST_GW=198.51.100.1
export TEST_DNS="1.1.1.1 8.8.8.8"

nmcli con delete "${CON_NAME}" 2>/dev/null || true
nmcli con add type ethernet ifname lo con-name "${CON_NAME}" 2>&1 | tee "${SANDBOX}/task1.txt"

nmcli con mod "${CON_NAME}" ipv4.addresses "${TEST_IP}"      2>&1 | tee -a "${SANDBOX}/task1.txt"
nmcli con mod "${CON_NAME}" ipv4.gateway  "${TEST_GW}"       2>&1 | tee -a "${SANDBOX}/task1.txt"
nmcli con mod "${CON_NAME}" ipv4.dns      "${TEST_DNS}"      2>&1 | tee -a "${SANDBOX}/task1.txt"
nmcli con mod "${CON_NAME}" ipv4.method   manual             2>&1 | tee -a "${SANDBOX}/task1.txt"
nmcli con mod "${CON_NAME}" connection.autoconnect no        2>&1 | tee -a "${SANDBOX}/task1.txt"
nmcli con up  "${CON_NAME}"                                  2>&1 | tee -a "${SANDBOX}/task1.txt"

nmcli -f NAME,TYPE,DEVICE,IP4.ADDRESS,IP4.GATEWAY,IP4.DNS,IPV4.METHOD con show "${CON_NAME}" \
    2>&1 | tee -a "${SANDBOX}/task1.txt"

sudo -u "${USER}" bash -c 'echo "Task1 evidence reviewed at $(date -Is)" >> /tmp/lab31a/task1-reviewed-by-user.txt'
stat -c '%U:%G %a %n' /tmp/lab31a/task1-reviewed-by-user.txt | tee -a "${SANDBOX}/task1.txt"
echo "exit was: $?"
```

### Breakdown

- `nmcli con add ... ifname lo` creates a test profile on loopback to avoid production impact.
- `nmcli con mod` writes persistent profile settings in NetworkManager config.
- `nmcli con up` is required so modified values become active now (`T31-B`).
- `tee` captures transcript for verification and journal evidence.

### L->R

`nmcli con mod lab31test ipv4.addresses 198.51.100.31/24`

- `nmcli` NetworkManager CLI
- `con mod` edit connection profile fields
- `lab31test` target profile
- `ipv4.addresses` static address property
- `198.51.100.31/24` CIDR address and prefix

### Story

Real outages happen when admins edit the wrong connection or forget activation. Using a dedicated test profile plus `con up` builds safe muscle memory and isolates risk.

### Expected Output

- `nmcli con add` prints successful connection creation.
- `nmcli con up lab31test` reports activated connection.
- `nmcli con show lab31test` shows manual method, static IP, gateway, and DNS.

### Switches

| Token | Meaning |
|---|---|
| `con add` | create a new NetworkManager profile |
| `type ethernet` | ethernet profile type |
| `ifname lo` | bind to loopback device for safe lab |
| `con-name` | explicit profile name |
| `con mod` | update profile settings |
| `con up` | apply profile now |
| `-f` | select display fields in `nmcli con show` |

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | `nmcli con mod` | persists static IPv4 settings in profile |
| ✅ | `nmcli con up` | applies profile changes at runtime |
| ✅ | `ipv4.method manual` | prevents silent DHCP fallback |
| ✅ | `tee -a` | preserves evidence transcript |
| 🪤 Trap Risk | `T31-B`: forgot `nmcli con up` | profile changed but active state unchanged; always run `con up` then verify |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Static profile fields | `nmcli con show lab31test` | proves profile stores static values |
| Active runtime state | `nmcli con up lab31test && ip addr show lo` | confirms applied now |
| Reboot-safe profile | `nmcli -f NAME,IPV4.METHOD con show lab31test` | confirms manual method persists |

### Journal Write

```bash
LAB=lab-31a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab31a/task1.txt "${JDIR}/evidence.txt"
cat > "${JDIR}/done.txt" <<EOF
LAB: ${LAB}
TASK: ${TASK}
DATE: $(date -Is)
USER: $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "${JDIR}/notes.txt" <<EOF
TOPIC: nmcli con add/mod static IPv4 on test profile
COMMANDS: nmcli con add, con mod, con up, nmcli con show
TRAPS: T31-B rehearsed
NEXT: task2 capture ip addr/ip route and teardown
EOF
ls -la "${JDIR}"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab31a/task1-reviewed-by-user.txt
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `con up` fails | verify `ifname lo` exists and connection name is exact |
| IP values missing in show output | rerun `con mod ...` and confirm `ipv4.method manual` |
| File ownership wrong | use `sudo -u "${USER}"` for Tier B evidence write |

### STOP

Stop and paste Task 1 output before moving on.

---

## Task 2 - Capture `ip addr` and `ip route`, then teardown test profile

Practice directory this task: `/run`

### Warm-Up

```bash
ip addr show lo
ip route show
nmcli con show lab31test
find /run -maxdepth 1 -type d | head -n 5
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### WEAVE TRACE

- `ip addr show lo` -> compare before/after activation.
- `ip route show` -> validates route view from kernel table.
- `nmcli con show lab31test` -> persistent profile audit before destroy.

### Purpose

Collect runtime networking evidence (`ip addr`, `ip route`) for the test profile and perform controlled teardown with `nmcli con delete lab31test`.

### Main Block

```bash
export SANDBOX=/tmp/lab31a
export CON_NAME=lab31test

ip addr show lo     2>&1 | tee "${SANDBOX}/task2.txt"
ip route show       2>&1 | tee -a "${SANDBOX}/task2.txt"
nmcli con show "${CON_NAME}" 2>&1 | tee -a "${SANDBOX}/task2.txt"

sudo -u "${USER}" bash -c 'echo "Task2 audit reviewed at $(date -Is)" >> /tmp/lab31a/task2-reviewed-by-user.txt'
stat -c '%U:%G %a %n' /tmp/lab31a/task2-reviewed-by-user.txt | tee -a "${SANDBOX}/task2.txt"

nmcli con delete "${CON_NAME}" 2>&1 | tee -a "${SANDBOX}/task2.txt"
nmcli con show | grep -w "${CON_NAME}" 2>&1 | tee -a "${SANDBOX}/task2.txt" || true
echo "exit was: $?"
```

### Breakdown

- `ip addr show lo` confirms interface addresses visible to kernel.
- `ip route show` captures route table state at runtime.
- `nmcli con delete` removes test profile cleanly so no persistent residue remains.

### L->R

`ip route show`

- `ip` iproute2 command
- `route` route table object
- `show` display current entries

### Story

Static configuration is incomplete without verification and cleanup. Operators must both prove state and restore baseline to avoid cross-lab contamination (`T44`).

### Expected Output

- address lines for loopback in `ip addr show lo`
- route table lines in `ip route show`
- no `lab31test` profile after deletion

### Switches

| Token | Meaning |
|---|---|
| `addr show` | display interface addresses |
| `route show` | display route table |
| `con delete` | remove NM profile |
| `grep -w` | exact-word match for connection name |

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | `ip addr` | runtime interface inspection |
| ✅ | `ip route` | runtime route inspection |
| ✅ | `nmcli con delete` | removes persistent profile |
| 🪤 Trap Risk | `T44`: forgetting teardown | leaves dirty state for next lab; always verify deletion |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Test profile removed | `nmcli con show | grep -w lab31test || true` | proves no residue persists |
| Evidence captured | `wc -l /tmp/lab31a/task2.txt` | verifies audit transcript exists |

### Journal Write

```bash
LAB=lab-31a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab31a/task2.txt "${JDIR}/evidence.txt"
cat > "${JDIR}/done.txt" <<EOF
LAB: ${LAB}
TASK: ${TASK}
DATE: $(date -Is)
USER: $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "${JDIR}/notes.txt" <<EOF
TOPIC: ip addr/ip route verification plus connection teardown
COMMANDS: ip addr show, ip route show, nmcli con delete
TRAPS: T44 rehearsed
NEXT: lab-31b ansible implementation
EOF
ls -la "${JDIR}"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab31a/task2-reviewed-by-user.txt
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `lab31test` still listed | run `nmcli con delete lab31test` again and recheck |
| no route lines shown | expected minimal output on isolated test setup; capture command output anyway |
| journal missing files | recreate `JDIR` then rerun copy/write block |

### STOP

Stop and paste Task 2 output before final closeout.

---

## Section 6 Closeout (after Task 2)

```bash
set +e
export SANDBOX=/tmp/lab31a
export GROUP=labgrp_31_staticip
export USER=labuser_31_staticip
export USER_HOME=${SANDBOX}/home_${USER}
export CON_NAME=lab31test

nmcli con delete "${CON_NAME}" 2>/dev/null || true
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
nmcli con show | grep -w "${CON_NAME}" >/dev/null && echo "❌ connection remains" || echo "✅ connection gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Author

Kelvin R. Tobias
