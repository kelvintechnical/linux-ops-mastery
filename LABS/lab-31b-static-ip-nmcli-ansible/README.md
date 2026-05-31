# Lab 31b: Configure a Static IP Address (Ansible) - `community.general.nmcli`

- **Series:** linux-ops-mastery
- **Trilogy:** `31a` (RHCSA) -> `31b` (Ansible) -> `31c` (Verify)
- **Practice Directory:** `/run`
- **Tier B Sandbox:** `/tmp/lab31b`
- **Lab User/Group:** `labuser_31_staticip` / `labgrp_31_staticip`
- **Test Connection:** `lab31test` only (safe profile on `lo`)
- **Traps rehearsed:** `T31-A`, `T31-B`, `T41`, `T44`

This lab's practice directory is: `/run`

---

## LAB HEADER

```bash
echo "TIME: $(date -Is)"
echo "USER: $(whoami)@$(hostname)"
echo "PRACTICE DIR: /run"
echo "TEST PROFILE: lab31test"
ansible --version | head -n 2
ansible-galaxy collection list | grep -E 'community.general' || true
nmcli con show | tee /tmp/lab31b_header_connections.txt
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
export SANDBOX=/tmp/lab31b
export GROUP=labgrp_31_staticip
export USER=labuser_31_staticip
export USER_HOME=${SANDBOX}/home_${USER}
export CON_NAME=lab31test

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-31b/task1 /root/rhcsa_journal/lab-31b/task2 /root/rhcsa_journal/lab-31b/playbooks
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
/run is runtime-only state and is rebuilt each boot. This makes it ideal
for training persistence validation and controlled networking experiments.
EOF

id "${USER}"
ls -ld /run "${SANDBOX}" "${USER_HOME}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 - Apply static profile declaratively with Ansible

Practice directory this task: `/run`

### Warm-Up

```bash
nmcli con show | head -n 10
ip addr show lo
ip route show
ls -ld /run /tmp/lab31b
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### WEAVE TRACE

- `nmcli con show` -> pre/post profile existence checks.
- `ip addr show lo` -> runtime inspection after playbook apply.
- `ip route show` -> captures kernel routing baseline.

### Purpose

Use a real FQCN module (`community.general.nmcli`) to create and configure `lab31test` idempotently, run `--check --diff` first, then apply and prove second run is unchanged.

### Main Block

```bash
export SANDBOX=/tmp/lab31b
export PLAY=/root/rhcsa_journal/lab-31b/playbooks/task1.yml

cat > "${PLAY}" <<'EOF'
---
- name: Lab31b task1 static IP profile
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Ensure test connection exists with static IPv4
      community.general.nmcli:
        conn_name: lab31test
        ifname: lo
        type: ethernet
        method4: manual
        ip4: 198.51.100.31/24
        gw4: 198.51.100.1
        dns4:
          - 1.1.1.1
          - 8.8.8.8
        autoconnect: false
        state: present
      register: nm_task1

    - name: Bring test profile up
      ansible.builtin.command: nmcli con up lab31test
      register: up_result
      changed_when: "'successfully activated' in up_result.stdout or up_result.rc == 0"

    - name: Debug module result
      ansible.builtin.debug:
        var: nm_task1
EOF

ansible-playbook --check --diff "${PLAY}" 2>&1 | tee "${SANDBOX}/task1-check.txt"
ansible-playbook "${PLAY}"                 2>&1 | tee "${SANDBOX}/task1-apply1.txt"
ansible-playbook "${PLAY}"                 2>&1 | tee "${SANDBOX}/task1-apply2.txt"

nmcli -f NAME,IPV4.METHOD,IP4.ADDRESS,IP4.GATEWAY,IP4.DNS con show lab31test \
    2>&1 | tee "${SANDBOX}/task1-verify.txt"

sudo -u "${USER}" bash -c 'echo "Task1 ansible run reviewed at $(date -Is)" >> /tmp/lab31b/task1-reviewed-by-user.txt'
stat -c '%U:%G %a %n' /tmp/lab31b/task1-reviewed-by-user.txt | tee -a "${SANDBOX}/task1-verify.txt"
echo "exit was: $?"
```

### Breakdown

- `community.general.nmcli` enforces desired profile state declaratively.
- `--check --diff` previews intended changes before mutation.
- second apply must show `changed=0` for idempotence.
- explicit `nmcli con up` addresses `T31-B` (apply runtime state).

### L->R

`ansible-playbook --check --diff /root/rhcsa_journal/lab-31b/playbooks/task1.yml`

- `ansible-playbook` execute playbook
- `--check` dry run simulation
- `--diff` show before/after differences
- `task1.yml` desired-state definition

### Story

Hand commands scale poorly. Ansible codifies the same network intent so configuration is reproducible, reviewable, and rerunnable without drift.

### Expected Output

- check mode reports planned changes.
- first apply reports changes.
- second apply reports no change (`changed=0`).

### Switches

| Token | Meaning |
|---|---|
| `--check` | simulate changes |
| `--diff` | show content differences |
| `community.general.nmcli` | NetworkManager module |
| `state: present` | ensure profile exists |
| `method4: manual` | static IPv4 mode |

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | FQCN module usage | enforces RHCE-style explicit module namespace |
| ✅ | Check mode first | validates intent before mutation |
| ✅ | Idempotence rerun | proves no repeated drift |
| ✅ | `nmcli con up` after config | applies profile now |
| 🪤 Trap Risk | `T31-A`: runtime-only `ip addr add` mistaken for persistence | use NM profile as source of truth, not transient `ip addr add` |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Profile in NM DB | `nmcli con show lab31test` | confirms saved profile |
| Runtime activation | `nmcli con up lab31test && ip addr show lo` | confirms active state |
| Idempotence | second `ansible-playbook` output | validates repeat-safe automation |

### Journal Write

```bash
LAB=lab-31b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab31b/task1-check.txt  "${JDIR}/check.txt"
cp /tmp/lab31b/task1-apply1.txt "${JDIR}/apply1.txt"
cp /tmp/lab31b/task1-apply2.txt "${JDIR}/apply2.txt"
cp /tmp/lab31b/task1-verify.txt "${JDIR}/verify.txt"
cat > "${JDIR}/done.txt" <<EOF
LAB: ${LAB}
TASK: ${TASK}
DATE: $(date -Is)
USER: $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "${JDIR}/notes.txt" <<EOF
TOPIC: community.general.nmcli static profile with check/diff and idempotence
COMMANDS: ansible-playbook --check --diff, ansible-playbook, nmcli con show
TRAPS: T31-A rehearsed
NEXT: task2 failed_when assertion for ipv4.addresses
EOF
ls -la "${JDIR}"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab31b/task1-reviewed-by-user.txt
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| module not found | install `community.general` collection |
| second run still changed | inspect mutable fields and remove non-idempotent command behavior |
| connection not active | ensure `nmcli con up lab31test` task runs successfully |

### STOP

Stop and paste Task 1 output before moving on.

---

## Task 2 - Add `failed_when` guard for `ipv4.addresses`

Practice directory this task: `/run`

### Warm-Up

```bash
nmcli -f NAME,IP4.ADDRESS,IPV4.METHOD con show lab31test
grep -n "state: present" /root/rhcsa_journal/lab-31b/playbooks/task1.yml
ls -ld /run /tmp/lab31b
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### WEAVE TRACE

- `nmcli ... con show` -> data source for assertion check.
- `grep -n` -> confirms module file context before extension.
- `ls -ld` -> evidence context in practice directory.

### Purpose

Implement a robust assertion task that fails if the connection output does not contain an IPv4 address, catching misconfiguration quickly.

### Main Block

```bash
export SANDBOX=/tmp/lab31b
export PLAY=/root/rhcsa_journal/lab-31b/playbooks/task2.yml

cat > "${PLAY}" <<'EOF'
---
- name: Lab31b task2 validation with failed_when
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Read connection details
      ansible.builtin.command: nmcli -f NAME,IP4.ADDRESS,IPV4.METHOD con show lab31test
      register: con_show
      changed_when: false

    - name: Fail when ipv4.addresses missing
      ansible.builtin.fail:
        msg: "lab31test missing ipv4.addresses in nmcli output"
      when: con_show.stdout is not regex('IP4.ADDRESS')

    - name: Debug connection output
      ansible.builtin.debug:
        var: con_show.stdout_lines
EOF

ansible-playbook --check --diff "${PLAY}" 2>&1 | tee "${SANDBOX}/task2-check.txt"
ansible-playbook "${PLAY}"                 2>&1 | tee "${SANDBOX}/task2-apply.txt"
nmcli -f NAME,IP4.ADDRESS,IPV4.METHOD con show lab31test 2>&1 | tee "${SANDBOX}/task2-verify.txt"

sudo -u "${USER}" bash -c 'echo "Task2 validation reviewed at $(date -Is)" >> /tmp/lab31b/task2-reviewed-by-user.txt'
stat -c '%U:%G %a %n' /tmp/lab31b/task2-reviewed-by-user.txt | tee -a "${SANDBOX}/task2-verify.txt"
echo "exit was: $?"
```

### Breakdown

- reads profile output with `nmcli`.
- fails fast if address field is absent.
- keeps task read-only with `changed_when: false`.

### L->R

`when: con_show.stdout is not regex('IP4.ADDRESS')`

- `when` conditional gate
- `con_show.stdout` prior command output
- `regex(...)` required marker test
- `is not` invert match to trigger fail path

### Story

Automation without assertions hides silent failure. `failed_when`-style logic converts hidden drift into immediate, actionable failures.

### Expected Output

- successful play when address field exists.
- explicit fail message if field missing.

### Switches

| Token | Meaning |
|---|---|
| `changed_when: false` | keep read-only command from counting as change |
| `when:` | conditional task execution |
| `ansible.builtin.fail` | explicit failure with custom message |
| `regex()` | pattern match in Ansible expression |

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | validation gate | blocks progression on missing static field |
| ✅ | read-only probe task | avoids false drift in output |
| ✅ | debug output lines | provides operator-facing evidence |
| 🪤 Trap Risk | `T31-B`: profile modified but not activated | enforce `con up` in setup path and verify runtime each run |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| validation playbook saved | `ls /root/rhcsa_journal/lab-31b/playbooks/task2.yml` | keeps reproducible control artifact |
| static field present | `nmcli -f IP4.ADDRESS con show lab31test` | confirms persisted address metadata |

### Journal Write

```bash
LAB=lab-31b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab31b/task2-check.txt  "${JDIR}/check.txt"
cp /tmp/lab31b/task2-apply.txt  "${JDIR}/apply.txt"
cp /tmp/lab31b/task2-verify.txt "${JDIR}/verify.txt"
cat > "${JDIR}/done.txt" <<EOF
LAB: ${LAB}
TASK: ${TASK}
DATE: $(date -Is)
USER: $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "${JDIR}/notes.txt" <<EOF
TOPIC: failed_when-style assertion for IPv4 field presence
COMMANDS: ansible.builtin.command, fail, debug, nmcli con show
TRAPS: T31-B reinforced
NEXT: lab-31c audit and destroy-restore
EOF
ls -la "${JDIR}"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab31b/task2-reviewed-by-user.txt
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| false failure on regex check | inspect exact `nmcli` output columns and adjust pattern |
| command task shows changed | keep `changed_when: false` for read operations |
| missing playbook files | re-create under `/root/rhcsa_journal/lab-31b/playbooks` |

### STOP

Stop and paste Task 2 output before final closeout.

---

## Section 6 Closeout (after Task 2)

```bash
set +e
export SANDBOX=/tmp/lab31b
export GROUP=labgrp_31_staticip
export USER=labuser_31_staticip
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
