# Lab 40b: Standard File Permissions (Ansible) - `ansible.builtin.file` mode control

- **Series:** linux-ops-mastery - Identity, Permissions, and Access
- **Trilogy:** [`40a`](../lab-40a-chmod-standard-perms-rhcsa/) (RHCSA) -> `40b` (Ansible) -> [`40c`](../lab-40c-chmod-standard-perms-verify/) (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = declarative chmod with `ansible.builtin.file`, Task 2 = trap-proof exact octal assertions)
- **Practice Directory (rotation #40):** `/usr`
- **Sandbox (Tier B):** `/tmp/lab40b` with `USER=labuser_40_chmod`, `GROUP=labgrp_40_chmod`, `USER_HOME=/tmp/lab40b/home_labuser_40_chmod`
- **Playbooks live at:** `/root/rhcsa_journal/lab-40b/playbooks/`
- **Traps rehearsed this lab:** **T40-A** (mode notation mistakes, unquoted YAML mode values) ; **T40-B** (recursive chmod blast radius) ; **T41** ; **T44**

> **This lab's practice directory is: `/usr`**. Permission targets are staged only in `/tmp/lab40b`.

---

## LAB HEADER BLOCK

```bash
echo "📦 OS: $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒 TIME: $(date -Is)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "📁 PRACTICE DIR: /usr"
echo "⚠️ TRAPS: T40-A T40-B T41 T44"
ansible --version | head -n 2
```

---

## Objective

Move chmod work from imperative shell into declarative Ansible:

1. Enforce target mode state with `ansible.builtin.file` and quoted octal strings (`'0644'`, `'0755'`).
2. Validate exact resulting bits with both Ansible `stat` and shell `stat -c %a`.
3. Prevent T40-A by asserting exact mode strings instead of visual guessing.

---

## Lab-Wide Setup - Tier B Sandbox + playbook workspace

```bash
sudo -i

export LAB_NUM=40
export LAB_SLUG=chmod
export SANDBOX=/tmp/lab40b
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-40b/{task1,task2,playbooks}

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 - Declarative chmod with `ansible.builtin.file`

### Purpose

Declare desired permission modes for files and directories and let Ansible converge state idempotently.

### Playbook (`/root/rhcsa_journal/lab-40b/playbooks/task1.yml`)

```yaml
---
- name: "Lab 40b Task 1 - declarative file modes"
  hosts: localhost
  connection: local
  become: true
  gather_facts: false
  vars:
    sandbox: /tmp/lab40b
  tasks:
    - name: Ensure target directories exist
      ansible.builtin.file:
        path: "{{ item.path }}"
        state: directory
        mode: "{{ item.mode }}"
      loop:
        - { path: "{{ sandbox }}/bin",  mode: "0755" }
        - { path: "{{ sandbox }}/docs", mode: "0755" }
        - { path: "{{ sandbox }}/priv", mode: "0700" }

    - name: Ensure permission test files exist with target modes
      ansible.builtin.file:
        path: "{{ item.path }}"
        state: touch
        mode: "{{ item.mode }}"
      loop:
        - { path: "{{ sandbox }}/bin/run.sh",      mode: "0755" }
        - { path: "{{ sandbox }}/docs/readme.txt", mode: "0644" }
        - { path: "{{ sandbox }}/priv/secret.txt", mode: "0600" }
```

### Run and verify

```bash
set -o pipefail

ansible-playbook /root/rhcsa_journal/lab-40b/playbooks/task1.yml \
  2>&1 | tee /root/rhcsa_journal/lab-40b/task1/apply.txt

stat -c '%a %n' /tmp/lab40b/bin/run.sh /tmp/lab40b/docs/readme.txt /tmp/lab40b/priv/secret.txt \
  | tee /root/rhcsa_journal/lab-40b/task1/stat-octal.txt
```

---

## Task 2 - Trap T40-A proof with exact mode assertions

### Purpose

Prove expected octal modes exactly with `ansible.builtin.stat` + `ansible.builtin.assert` so mode notation mistakes fail fast.

### Playbook (`/root/rhcsa_journal/lab-40b/playbooks/task2.yml`)

```yaml
---
- name: "Lab 40b Task 2 - assert exact octal modes"
  hosts: localhost
  connection: local
  become: true
  gather_facts: false
  vars:
    checks:
      - { path: /tmp/lab40b/bin/run.sh,      expected: "0755" }
      - { path: /tmp/lab40b/docs/readme.txt, expected: "0644" }
      - { path: /tmp/lab40b/priv/secret.txt, expected: "0600" }
  tasks:
    - name: Read current mode for each file
      ansible.builtin.stat:
        path: "{{ item.path }}"
      loop: "{{ checks }}"
      register: mode_stats

    - name: Assert exact expected mode bits
      ansible.builtin.assert:
        that:
          - item.stat.exists
          - item.stat.mode == item.item.expected
        fail_msg: "Mode mismatch for {{ item.item.path }} expected={{ item.item.expected }} got={{ item.stat.mode }}"
        success_msg: "Mode OK for {{ item.item.path }} => {{ item.stat.mode }}"
      loop: "{{ mode_stats.results }}"
```

### Run and verify

```bash
set -o pipefail

ansible-playbook /root/rhcsa_journal/lab-40b/playbooks/task2.yml \
  2>&1 | tee /root/rhcsa_journal/lab-40b/task2/assert.txt

ls -l /tmp/lab40b/bin/run.sh /tmp/lab40b/docs/readme.txt /tmp/lab40b/priv/secret.txt \
  | tee /root/rhcsa_journal/lab-40b/task2/ls-long.txt

stat -c '%a %n' /tmp/lab40b/bin/run.sh /tmp/lab40b/docs/readme.txt /tmp/lab40b/priv/secret.txt \
  | tee /root/rhcsa_journal/lab-40b/task2/stat-final.txt
```

> **T40-A defense:** keep Ansible `mode` values quoted strings (`"0644"`, `"0755"`). This preserves exact octal intent and avoids ambiguous numeric interpretation.

---

## Lab Closeout - Section 6 Bulletproof Teardown

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group  "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}"  2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 40b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"               && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"             && echo "❌ home remains"    || echo "✅ home gone"

set -e
```

---

## Lab 40b Checklist

- [ ] Task 1 playbook converged file modes using `ansible.builtin.file`
- [ ] Declared modes used quoted octal strings (`"0644"`, `"0755"`, `"0600"`, `"0700"`)
- [ ] Task 2 assertion playbook proved exact expected mode bits
- [ ] Verification captured with both `ls -l` and `stat -c %a`
- [ ] Section 6 closeout produced four `✅` lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
