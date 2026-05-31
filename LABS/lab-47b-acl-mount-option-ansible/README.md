# Lab 47b: Checking ACL Support with Ansible (Module-First)

- **Series:** linux-ops-mastery — Filesystems, Mount Options, and ACL Readiness
- **Trilogy:** [`47a`](../lab-47a-acl-mount-option-rhcsa/) (RHCSA) -> `47b` (Ansible) -> [`47c`](../lab-47c-acl-mount-option-verify/) (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (objective context):** `/opt` (read-only inspection only)
- **Sandbox (Tier B):** `/tmp/lab47b` with `USER=labuser_47_aclmount`, `GROUP=labgrp_47_aclmount`
- **Playbooks live at:** `/root/rhcsa_journal/lab-47b/playbooks/`
- **Traps rehearsed this lab:** **T47-A** · **T47-B** · **T41** · **T44**

> **Safety boundary:** read-only inspection lab. **Do not edit `/etc/fstab`** in this trilogy.

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /opt (read-only), /tmp/lab47b (write target)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "🕒 TIME: $(date -Is)"
echo "⚠️ TRAPS: T47-A T47-B T41 T44"
ansible --version | head -n 2
ansible -m ping localhost | tail -n 4
```

---

## Objective

1. Capture root mount metadata with Ansible and keep the run read-only.
2. Optionally model `ansible.posix.mount state=present` in check mode for inspection-only intent.
3. Assert ACL readiness from runtime mount options (`findmnt`) instead of trusting only `/etc/fstab`.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab47b
export GROUP=labgrp_47_aclmount
export USER=labuser_47_aclmount
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-47b/playbooks
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Read-only mount inspection with Ansible (`findmnt` + optional mount check-mode)

### Purpose

Capture runtime mount facts with `ansible.builtin.shell` and optionally model mount state via `ansible.posix.mount` in check mode.

### Playbook (`/root/rhcsa_journal/lab-47b/playbooks/task1.yml`)

```yaml
---
- name: "Lab 47b Task 1 - inspect root mount ACL context"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Capture root mount tuple (target/source/fstype/options)"
      ansible.builtin.shell: findmnt -n -o TARGET,SOURCE,FSTYPE,OPTIONS /
      register: root_mount_tuple
      changed_when: false

    - name: "Show mount tuple"
      ansible.builtin.debug:
        var: root_mount_tuple.stdout

    - name: "Optional ansible.posix.mount inspection (check mode only)"
      ansible.posix.mount:
        path: "/"
        src: "{{ root_mount_tuple.stdout.split()[1] }}"
        fstype: "{{ root_mount_tuple.stdout.split()[2] }}"
        opts: "{{ root_mount_tuple.stdout.split()[3] }}"
        state: present
      check_mode: true
      changed_when: false
      register: mount_present_check

    - name: "Summarize check-mode result"
      ansible.builtin.debug:
        msg:
          - "mount_check_changed={{ mount_present_check.changed }}"
          - "read_only_intent=yes (check_mode)"
```

### Run and verify

```bash
ansible-playbook /root/rhcsa_journal/lab-47b/playbooks/task1.yml --check 2>&1 | tee /opt/lab47b-task1-apply.txt
```

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-47b/task1
cp /opt/lab47b-task1-apply.txt /root/rhcsa_journal/lab-47b/task1/evidence.txt
```

---

## Task 2 — Assert ACL present in runtime options (`findmnt` shell stdout)

### Purpose

Fail fast when ACL runtime evidence is missing or misread.

### Playbook (`/root/rhcsa_journal/lab-47b/playbooks/task2.yml`)

```yaml
---
- name: "Lab 47b Task 2 - assert ACL runtime evidence"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Read root fstype"
      ansible.builtin.shell: findmnt -n -o FSTYPE /
      register: root_fstype
      changed_when: false

    - name: "Read root mount options"
      ansible.builtin.shell: findmnt -n -o OPTIONS /
      register: root_options
      changed_when: false

    - name: "Assert ACL evidence policy"
      ansible.builtin.assert:
        that:
          - "'acl' in root_options.stdout or root_fstype.stdout == 'xfs'"
        fail_msg: "ACL evidence missing from runtime options for non-xfs root."
        success_msg: "ACL readiness verified from runtime mount state."

    - name: "Read-only fstab cross-check (informational)"
      ansible.builtin.shell: awk '$1 !~ /^#/ && $2==\"/\" {print}' /etc/fstab
      register: fstab_root_line
      changed_when: false
      failed_when: false

    - name: "Show trap reminder"
      ansible.builtin.debug:
        msg:
          - "T47-B: do not rely on /etc/fstab alone; runtime findmnt state is authoritative."
          - "fstab_root_line={{ fstab_root_line.stdout | default('none') }}"
```

### Run and inspect

```bash
ansible-playbook /root/rhcsa_journal/lab-47b/playbooks/task2.yml 2>&1 | tee /opt/lab47b-task2-apply.txt
grep -E "FAILED|ASSERT|PLAY RECAP|runtime mount state" /opt/lab47b-task2-apply.txt || true
```

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-47b/task2
cp /opt/lab47b-task2-apply.txt /root/rhcsa_journal/lab-47b/task2/evidence.txt
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

echo "── Lab 47b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 47b Checklist

- [ ] Task 1 completed (`findmnt` captured via Ansible; optional `ansible.posix.mount` check-mode inspection run)
- [ ] Task 2 completed (ACL assertion evaluated from runtime `findmnt` stdout)
- [ ] Read-only `/etc/fstab` cross-check captured (no edits made)
- [ ] T47-A/T47-B plus T41/T44 notes recorded in evidence
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
