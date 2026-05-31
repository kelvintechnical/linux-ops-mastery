# Lab 32b: Check Network Connectivity (Ansible) — `ansible.builtin.shell`, `wait_for`, `uri`

- **Series:** linux-ops-mastery — Networking Diagnostics
- **Trilogy:** `32a` (RHCSA) → `32b` (Ansible) → `32c` (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 playbook + native probe, Task 2 failure criteria trap-proofing)
- **Practice Directory (rotation #18):** `/media`
- **Sandbox (Tier B):** `/tmp/lab32b` with `USER=labuser_32_ping`, `GROUP=labgrp_32_ping`, `USER_HOME=/tmp/lab32b/home_labuser_32_ping`
- **Traps rehearsed this lab:** `T32-A`, `T32-B`, `T41`, `T44`

> **Section 18 boundary note (important):** There is no dedicated Ansible `ping(8)` ICMP module for host reachability tests. This lab uses `ansible.builtin.shell` for exact `ping -c` behavior and pairs it with Ansible-native probes (`ansible.builtin.wait_for` or `ansible.builtin.uri`) for idempotent connectivity checks.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "📁  PRACTICE DIR: /media"
ls -la /media 2>/dev/null || stat /media
ansible --version | head -n 1
echo "exit was: $?"
```

---

## Lab-Wide Setup — Tier B Sandbox + Playbook Path

```bash
sudo -i

export LAB_NUM=32
export LAB_SLUG=ping
export SANDBOX=/tmp/lab32b
export GROUP=labgrp_32_ping
export USER=labuser_32_ping
export USER_HOME=${SANDBOX}/home_${USER}
export PB_DIR=/root/rhcsa_journal/lab-32b/playbooks

mkdir -p "${SANDBOX}" "${USER_HOME}" "${PB_DIR}" /root/rhcsa_journal/lab-32b/task1 /root/rhcsa_journal/lab-32b/task2
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

cat > "${PB_DIR}/task1.yml" <<'EOF'
---
- name: Lab 32b Task 1 connectivity probe
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Run bounded ICMP probe with shell
      ansible.builtin.shell: ping -c 3 -W 2 127.0.0.1
      register: ping_probe
      changed_when: false

    - name: Show ping output
      ansible.builtin.debug:
        var: ping_probe.stdout_lines

    - name: Native idempotent TCP probe (Ansible equivalent pattern)
      ansible.builtin.wait_for:
        host: 127.0.0.1
        port: 22
        timeout: 2
      register: wait_probe
      ignore_errors: true
      changed_when: false

    - name: Show wait_for result
      ansible.builtin.debug:
        var: wait_probe
EOF

cat > "${PB_DIR}/task2.yml" <<'EOF'
---
- name: Lab 32b Task 2 trap-proof assertions
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Run bounded ping with strict pass/fail
      ansible.builtin.shell: ping -c 3 -W 2 127.0.0.1
      register: ping_guard
      changed_when: false
      failed_when:
        - ping_guard.rc != 0
        - "'0% packet loss' not in ping_guard.stdout"

    - name: IPv6 contrast (non-fatal)
      ansible.builtin.shell: ping -6 -c 3 -W 2 ::1
      register: ping6_guard
      changed_when: false
      ignore_errors: true

    - name: Assert IPv4 probe succeeded exactly as expected
      ansible.builtin.assert:
        that:
          - ping_guard.rc == 0
          - "'0% packet loss' in ping_guard.stdout"
        fail_msg: "Ping validation failed. Re-check T32-A/T32-B conditions."
        success_msg: "Ping validation passed with bounded safe flags."

    - name: Show outputs for journal evidence
      ansible.builtin.debug:
        msg:
          - "IPv4 rc={{ ping_guard.rc }}"
          - "IPv6 rc={{ ping6_guard.rc | default('n/a') }}"
EOF

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" "${PB_DIR}" /media
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — shell ping + Ansible-native probe

**Practice directory this task:** `/media`

### 🔁 Warm-Up

```bash
ls -la /media 2>/dev/null || stat /media
hostname -I | tee /tmp/lab32b/warmup1.txt
ansible localhost -m ansible.builtin.ping
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Run exact ICMP command behavior through Ansible (`shell` + `register`) while also using a native idempotent probe (`wait_for`/`uri`) to stay aligned with RHCE module habits.

### 🧵 WEAVE TRACE

| Re-used command | Role in task |
|---|---|
| `hostname -I` | context captured before playbook run |
| `ansible ... ping` | control-node sanity check |
| `tee` | evidence capture |
| `sudo -u "${USER}"` | writes task evidence as lab user |

### Main command block

```bash
TASKLOG=/tmp/lab32b/task1.txt
PLAY=/root/rhcsa_journal/lab-32b/playbooks/task1.yml

ansible-playbook --check --diff "${PLAY}" 2>&1 | tee "${TASKLOG}" || true
ansible-playbook "${PLAY}" 2>&1 | tee -a "${TASKLOG}"
ansible-playbook "${PLAY}" 2>&1 | tee -a "${TASKLOG}"   # idempotence rerun target

sudo -u "${USER}" bash -c 'echo "task1 ansible evidence $(date -Is)" > '"${USER_HOME}"'/task1-user-note.txt'
stat -c '%U:%G %a %n' "${USER_HOME}/task1-user-note.txt" | tee -a "${TASKLOG}"
grep -n "packet loss" "${TASKLOG}" | tee -a "${TASKLOG}" || true

echo "exit was: $?"
```

### Human-Readable Breakdown

- First run in `--check --diff` previews behavior.
- Applied run should execute bounded `ping -c 3 -W 2`.
- Third run verifies idempotent style expectations (`changed=0` for our probe tasks).

### Reading it left to right

`ansible-playbook --check --diff "${PLAY}"`

- `ansible-playbook` runs YAML task list
- `--check` simulates
- `--diff` shows intended differences
- `"${PLAY}"` points to persistent playbook path under journal tree

### The story

Connectivity automation often starts with shell parity (`ping`) but matures into declarative probes (`wait_for`/`uri`). This task teaches both without pretending there is a true ICMP Ansible module.

### Expected output

- `ping` output contains `0% packet loss` for IPv4 loopback
- `wait_for` may pass or fail depending on local SSH service state (non-fatal in this lab)
- idempotence rerun should keep changes minimal

### Switches

| Token | Meaning |
|---|---|
| `--check` | simulate without applying |
| `--diff` | show changes |
| `-c 3 -W 2` | bounded ICMP probe |
| `register` | capture task output for assertions |
| `changed_when: false` | mark probe as observational, not configuration change |

### 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | shell + register | captures exact ping output in Ansible |
| ✅ | wait_for/uri probe | Ansible-native network check pattern |
| ✅ | idempotence rerun | validates repeat-safe automation behavior |
| 🪤 | Trap risk: `T32-A` | unbounded ping causes hanging jobs |
| 🪤 | Trap risk: `T32-B` | IPv4 success does not prove IPv6 success |

### 🧹 Cleanup (task-level)

```bash
rm -f /tmp/lab32b/warmup1.txt /tmp/lab32b/task1.txt "${USER_HOME}/task1-user-note.txt"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| play hangs | ensure all ping commands include `-c` and `-W` |
| no packet-loss line | inspect registered stdout via debug output |

> **STOP — paste Task 1 play recap before Task 2.**

---

## Task 2 — `failed_when` trap-proof assertion

**Practice directory this task:** `/media`

### 🔁 Warm-Up

```bash
ls -la /media 2>/dev/null || stat /media
hostname -I | tee /tmp/lab32b/warmup2.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Encode strict pass/fail criteria so the play fails unless ping exits cleanly and reports `0% packet loss`.

### Main command block

```bash
TASKLOG=/tmp/lab32b/task2.txt
PLAY=/root/rhcsa_journal/lab-32b/playbooks/task2.yml

ansible-playbook --check --diff "${PLAY}" 2>&1 | tee "${TASKLOG}" || true
ansible-playbook "${PLAY}" 2>&1 | tee -a "${TASKLOG}"

grep -n "0% packet loss" "${TASKLOG}" | tee -a "${TASKLOG}"
grep -n "failed_when" "${PLAY}" | tee -a "${TASKLOG}"

sudo -u "${USER}" bash -c 'echo "task2 assertion evidence $(date -Is)" > '"${USER_HOME}"'/task2-user-note.txt'
stat -c '%U:%G %a %n' "${USER_HOME}/task2-user-note.txt" | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Human-Readable Breakdown

- `failed_when` enforces two conditions: `rc == 0` and output must include `0% packet loss`.
- `assert` restates these checks clearly for audit-friendly output.
- IPv6 probe remains non-fatal contrast to avoid false negatives on hosts without IPv6.

### Reading it left to right

`failed_when: [ ping_guard.rc != 0, '0% packet loss' not in ping_guard.stdout ]`

- any listed condition true => task fails
- this prevents “false green” success when ping output is degraded

### The story

Reliable automation is explicit about what success means. `rc` alone is not enough; text output checks catch partial failures and flaky diagnostics.

### Expected output

- play recap with task success on IPv4 checks
- assertion success message
- evidence lines containing `0% packet loss`

### Switches

| Token | Meaning |
|---|---|
| `failed_when` | custom failure logic |
| `ansible.builtin.assert` | explicit condition enforcement |
| `ignore_errors: true` | keep contrast checks from aborting the play |

### 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | custom failure guards | blocks silent pass conditions |
| ✅ | output-content validation | checks semantic success, not just exit code |
| ✅ | Tier B user artifact | continues user/group/file discipline |
| 🪤 | Trap risk: `T41` | always verify persisted evidence after run |
| 🪤 | Trap risk: `T44` | always perform full teardown audit |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Playbooks persisted | `ls -l /root/rhcsa_journal/lab-32b/playbooks/` | survives reboot for resume |
| Assertion evidence exists | `grep -n '0% packet loss' /tmp/lab32b/task2.txt` | confirms criteria were evaluated |

### 🧹 Cleanup (task-level)

```bash
rm -f /tmp/lab32b/warmup2.txt /tmp/lab32b/task2.txt "${USER_HOME}/task2-user-note.txt"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| assertion fails | inspect `ping_guard.stdout` and verify loopback/network stack |
| check mode noisy | expected for shell probes; use apply run for final proof |

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
