# Lab 55b: Inspecting iptables (Ansible) - `ansible.builtin.shell`, `register`, assertions

- **Series:** linux-ops-mastery
- **Trilogy:** `55a` (RHCSA) -> `55b` (Ansible) -> `55c` (Verify)
- **Practice Directory:** `/tmp`
- **Tier B Sandbox:** `/tmp/lab55b`
- **Lab User/Group:** `labuser_55_iptables` / `labgrp_55_iptables`
- **Traps rehearsed:** `T55-A`, `T55-B`, `T41`, `T44`

This lab's practice directory is: `/tmp`

> Read-only inspection only. Do **not** add, flush, or modify any firewall rules.

---

## LAB HEADER

```bash
echo "TIME: $(date -Is)"
echo "USER: $(whoami)@$(hostname)"
echo "PRACTICE DIR: /tmp"
echo "FOCUS: ansible read-only iptables inspection"
echo "TRAPS: T55-A T55-B T41 T44"
ansible --version | head -n 2
cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release
echo "exit was: $?"
```

> STOP and confirm header output before continuing.

---

## Lab-Wide Tier B Setup (run before Task 1)

```bash
sudo -i
export LAB_NUM=55
export LAB_SLUG=iptables
export SANDBOX=/tmp/lab55b
export GROUP=labgrp_55_iptables
export USER=labuser_55_iptables
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-55b/task1 /root/rhcsa_journal/lab-55b/task2 /root/rhcsa_journal/lab-55b/playbooks
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld /tmp "${SANDBOX}" "${USER_HOME}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 - Use Ansible to gather iptables/nft inspection output

Practice directory this task: `/tmp`

### Purpose

Run read-only firewall inspections through Ansible with `register` so output is captured and reusable in later assertions.

### Main Block

```bash
export SANDBOX=/tmp/lab55b
export PLAY=/root/rhcsa_journal/lab-55b/playbooks/task1.yml

cat > "${PLAY}" <<'EOF'
---
- name: Lab55b Task1 read-only firewall inspection
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Capture iptables legacy listing (numeric, verbose)
      ansible.builtin.shell: iptables -L -n -v
      register: iptables_list
      changed_when: false

    - name: Capture iptables-save preview
      ansible.builtin.shell: iptables-save | head -n 40
      register: iptables_save_head
      changed_when: false

    - name: Capture nft ruleset preview
      ansible.builtin.shell: nft list ruleset | head -n 60
      register: nft_ruleset_head
      changed_when: false

    - name: Explain legacy module boundary
      ansible.builtin.debug:
        msg:
          - "ansible.builtin.iptables is a legacy mutation-oriented module."
          - "RHEL9 prefers firewalld/nftables backend management."
          - "This lab remains read-only, so shell inspection is used."

    - name: Show captured summary snippets
      ansible.builtin.debug:
        msg:
          - "iptables stdout first line: {{ (iptables_list.stdout_lines | default(['']))[0] }}"
          - "iptables-save first line: {{ (iptables_save_head.stdout_lines | default(['']))[0] }}"
          - "nft first line: {{ (nft_ruleset_head.stdout_lines | default(['']))[0] }}"
EOF

ansible-playbook --check --diff "${PLAY}" 2>&1 | tee "${SANDBOX}/task1-check.txt"
ansible-playbook "${PLAY}"                 2>&1 | tee "${SANDBOX}/task1-apply.txt"

sudo -u "${USER}" bash -c 'echo "Task1 ansible inspection reviewed at $(date -Is)" >> /tmp/lab55b/task1-reviewed-by-user.txt'
stat -c '%U:%G %a %n' /tmp/lab55b/task1-reviewed-by-user.txt | tee -a "${SANDBOX}/task1-apply.txt"
echo "exit was: $?"
```

### Trap focus

- `T55-B`: in automation, prefer `iptables -L -n -v` to avoid DNS lookup stalls from plain `iptables -L`.
- `T55-A`: compare with nft output so an "empty" iptables legacy view does not create a false clean-state assumption.

### Journal Write

```bash
LAB=lab-55b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab55b/task1-check.txt "${JDIR}/check.txt"
cp /tmp/lab55b/task1-apply.txt "${JDIR}/apply.txt"
cat > "${JDIR}/done.txt" <<EOF
LAB: ${LAB}
TASK: ${TASK}
DATE: $(date -Is)
USER: $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
```

---

## Task 2 - Assert `INPUT` chain appears in captured stdout

Practice directory this task: `/tmp`

### Purpose

Add a strict assertion that fails if `INPUT` is missing from `iptables -L` output, making verification explicit and machine-checkable.

### Main Block

```bash
export SANDBOX=/tmp/lab55b
export PLAY=/root/rhcsa_journal/lab-55b/playbooks/task2.yml

cat > "${PLAY}" <<'EOF'
---
- name: Lab55b Task2 assert INPUT chain visibility
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Capture iptables listing for assertion
      ansible.builtin.shell: iptables -L -n -v
      register: iptables_list
      changed_when: false

    - name: Assert INPUT chain appears in stdout
      ansible.builtin.assert:
        that:
          - "'Chain INPUT' in iptables_list.stdout"
        fail_msg: "INPUT chain missing from iptables -L -n -v output"
        success_msg: "INPUT chain present in iptables output"

    - name: Capture nft head as modern cross-check
      ansible.builtin.shell: nft list ruleset | head -n 60
      register: nft_ruleset_head
      changed_when: false

    - name: Print short verify context
      ansible.builtin.debug:
        msg:
          - "iptables INPUT assertion passed"
          - "nft first line: {{ (nft_ruleset_head.stdout_lines | default(['']))[0] }}"
EOF

ansible-playbook --check --diff "${PLAY}" 2>&1 | tee "${SANDBOX}/task2-check.txt"
ansible-playbook "${PLAY}"                 2>&1 | tee "${SANDBOX}/task2-apply.txt"

sudo -u "${USER}" bash -c 'echo "Task2 assertion reviewed at $(date -Is)" >> /tmp/lab55b/task2-reviewed-by-user.txt'
stat -c '%U:%G %a %n' /tmp/lab55b/task2-reviewed-by-user.txt | tee -a "${SANDBOX}/task2-apply.txt"
echo "exit was: $?"
```

### Journal Write

```bash
LAB=lab-55b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab55b/task2-check.txt "${JDIR}/check.txt"
cp /tmp/lab55b/task2-apply.txt "${JDIR}/apply.txt"
cat > "${JDIR}/done.txt" <<EOF
LAB: ${LAB}
TASK: ${TASK}
DATE: $(date -Is)
USER: $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "${JDIR}/notes.txt" <<EOF
TOPIC: ansible read-only iptables inspection with INPUT chain assertion
COMMANDS: ansible.builtin.shell, register, ansible.builtin.assert
TRAPS: T55-A and T55-B rehearsed
NEXT: lab-55c verify audit and destroy-restore drill
EOF
```

---

## Section 6 Closeout (after Task 2)

```bash
set +e
export SANDBOX=/tmp/lab55b
export GROUP=labgrp_55_iptables
export USER=labuser_55_iptables
export USER_HOME=${SANDBOX}/home_${USER}

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Author

Kelvin R. Tobias
