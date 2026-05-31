# Lab 54b: NFSv4 ACL Automation Boundary (Ansible) — `ansible.builtin.command` + `dnf`

- **Series:** linux-ops-mastery — ACLs and Permissions
- **Trilogy:** [`54a`](../lab-54a-nfs4-acl-rhcsa/) (RHCSA) → **`54b` (Ansible — you are here)** → [`54c`](../lab-54c-nfs4-acl-verify/) (Verify)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = Section 18 boundary implementation, Task 2 = trap assertions and docs capture)
- **Practice Directory (rotation #54):** `/mnt`
- **Sandbox (Tier B):** `/tmp/lab54b` with `USER=labuser_54_nfs4`, `GROUP=labgrp_54_nfs4`, `USER_HOME=/tmp/lab54b/home_labuser_54_nfs4`
- **Traps rehearsed this lab:** **T54-A** (NFSv4 ACL ops need package + NFSv4 target) · **T54-B** (inheritance model differs from POSIX default ACL) · **T41** (destroy-restore in verify) · **T44** (closeout audit discipline)

> **Section 18 boundary:** there is no first-class Ansible module equivalent to `nfs4_setfacl` semantics. We use `ansible.builtin.dnf` for package install and `ansible.builtin.command` for CLI orchestration, with explicit idempotency guards (`creates:` / marker files).

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T54-A T54-B T41 T44"
echo "📁  PRACTICE DIR: /mnt"
findmnt -t nfs,nfs4 2>/dev/null || true
ansible --version 2>/dev/null | head -n 2 || true
```

---

## Objective

1. Encode NFSv4 ACL tool prep with Ansible (`ansible.builtin.dnf`).
2. Capture `nfs4_getfacl` / `nfs4_setfacl` help and package evidence through Ansible tasks.
3. Demonstrate a safe, idempotent command-based boundary for `nfs4_setfacl` syntax rehearsal when true NFSv4 targets are unavailable.
4. Prove T54-A handling (no false claims of successful ACL writes on local ext4/xfs).

---

## Lab-Wide Setup (Tier B Sandbox)

```bash
sudo -i

export LAB_NUM=54
export LAB_SLUG=nfs4
export SANDBOX=/tmp/lab54b
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-54b/task1
mkdir -p /root/rhcsa_journal/lab-54b/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Section 18 boundary implementation

**Practice directory this task:** `/mnt` for target context, `/tmp/lab54b` for generated evidence

### Files to create

`/tmp/lab54b/lab54b.yml`

```yaml
---
- name: Lab 54b NFSv4 ACL boundary
  hosts: localhost
  become: true
  gather_facts: false
  vars:
    sandbox: /tmp/lab54b
    target: /mnt/nfs/lab54-demo.txt
    marker: /tmp/lab54b/.task1.done
  tasks:
    - name: Ensure nfs4-acl-tools installed
      ansible.builtin.dnf:
        name: nfs4-acl-tools
        state: present

    - name: Capture nfs4_getfacl help
      ansible.builtin.command: nfs4_getfacl --help
      register: getfacl_help
      changed_when: false

    - name: Save nfs4_getfacl help output
      ansible.builtin.copy:
        dest: "{{ sandbox }}/nfs4_getfacl-help.txt"
        content: "{{ getfacl_help.stdout | default('') ~ '\n' }}"
        mode: "0644"

    - name: Capture nfs4_setfacl help
      ansible.builtin.command: nfs4_setfacl --help
      register: setfacl_help
      changed_when: false

    - name: Save nfs4_setfacl help output
      ansible.builtin.copy:
        dest: "{{ sandbox }}/nfs4_setfacl-help.txt"
        content: "{{ setfacl_help.stdout | default('') ~ '\n' }}"
        mode: "0644"

    - name: Capture package file list
      ansible.builtin.command: rpm -ql nfs4-acl-tools
      register: rpmql_out
      changed_when: false

    - name: Save package file list
      ansible.builtin.copy:
        dest: "{{ sandbox }}/package-filelist.txt"
        content: "{{ rpmql_out.stdout | default('') ~ '\n' }}"
        mode: "0644"

    - name: Note boundary and syntax examples
      ansible.builtin.copy:
        dest: "{{ sandbox }}/syntax-notes.txt"
        mode: "0644"
        content: |
          Section 18 boundary: no dedicated Ansible module for nfs4_setfacl semantics.
          Allow ACE example: A::labuser_54_nfs4@::rxtncy
          Deny ACE example:  D::EVERYONE@:w
          Inheritance flags: d=dir inherit, f=file inherit, i=inherit-only
          T54-A: nfs4_setfacl/nfs4_getfacl require real NFSv4 object.

    - name: Boundary marker for creates-based idempotency
      ansible.builtin.command: /usr/bin/touch {{ marker }}
      args:
        creates: "{{ marker }}"
```

### Run block

```bash
ansible-playbook /tmp/lab54b/lab54b.yml 2>&1 | tee /tmp/lab54b/task1.txt
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-54b/task1
mkdir -p "${JDIR}"
cp /tmp/lab54b/task1.txt                "${JDIR}/evidence.txt"
cp /tmp/lab54b/nfs4_getfacl-help.txt    "${JDIR}/nfs4_getfacl-help.txt"
cp /tmp/lab54b/nfs4_setfacl-help.txt    "${JDIR}/nfs4_setfacl-help.txt"
cp /tmp/lab54b/package-filelist.txt     "${JDIR}/package-filelist.txt"
cp /tmp/lab54b/syntax-notes.txt         "${JDIR}/syntax-notes.txt"
```

---

## Task 2 — Trap T54-A assertion and documentation capture

### Main command block

```bash
TASKLOG=/tmp/lab54b/task2.txt
TARGET=/mnt/nfs/lab54-demo.txt

echo "=== Trap assertion pass ==="                              | tee "${TASKLOG}"
rpm -q nfs4-acl-tools                                           | tee -a "${TASKLOG}"
test -s /tmp/lab54b/nfs4_getfacl-help.txt && echo "help captured: getfacl" | tee -a "${TASKLOG}"
test -s /tmp/lab54b/nfs4_setfacl-help.txt && echo "help captured: setfacl" | tee -a "${TASKLOG}"

if findmnt -n -o FSTYPE /mnt 2>/dev/null | grep -q '^nfs4$'; then
  echo "nfs4 mount detected at /mnt; optional live command demonstration." | tee -a "${TASKLOG}"
  mkdir -p /mnt/nfs
  touch "${TARGET}"
  nfs4_getfacl "${TARGET}" 2>&1 | tee -a "${TASKLOG}" || true
else
  echo "T54-A confirmed: /mnt is not nfs4 here; boundary mode only."       | tee -a "${TASKLOG}"
  echo "No claim of successful nfs4_setfacl write is made on local fs."    | tee -a "${TASKLOG}"
fi

echo "exit was: $?"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-54b/task2
mkdir -p "${JDIR}"
cp /tmp/lab54b/task2.txt "${JDIR}/evidence.txt"
```

---

## Lab Closeout — Section 6 Teardown

```bash
set +e
userdel -r "${USER}" 2>/dev/null
groupdel "${GROUP}" 2>/dev/null
rm -rf "${SANDBOX}"

echo "── Lab 54b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Checklist

- [ ] Task 1 implemented Section 18 boundary (`dnf` + `command`, no fake module claims)
- [ ] Task 1 includes `creates:` marker for idempotent boundary behavior
- [ ] Task 2 proves tools installed and docs/help evidence captured
- [ ] T54-A explicitly asserted when no NFSv4 mount exists
- [ ] Section 6 closeout completed and audited

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
