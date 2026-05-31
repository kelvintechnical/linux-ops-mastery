# Lab 37b: Configuring Local Host Resolution (Ansible) — `lineinfile` + `blockinfile`

- **Series:** linux-ops-mastery — Networking Name Resolution Fundamentals
- **Trilogy:** [`37a`](../lab-37a-etc-hosts-resolution-rhcsa/) (RHCSA hand-typed) → **`37b`** (Ansible — you are here) → [`37c`](../lab-37c-etc-hosts-resolution-verify/) (Verify capstone)
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = idempotent single-line entry via `lineinfile`, Task 2 = managed multi-line block via `blockinfile`)
- **Practice Directory (rotation #37):** `/sbin`
- **Playbooks:** `/root/rhcsa_journal/lab-37b/playbooks/`
- **Sandbox (Tier B):** `/tmp/lab37b` with `USER=labuser_37_hosts`, `GROUP=labgrp_37_hosts`, `USER_HOME=/tmp/lab37b/home_labuser_37_hosts`
- **Traps rehearsed this lab:** **T37-A** (no backup before `/etc/hosts` change) · **T37-B** (`hosts:` order misunderstood in verification) · **T41** (skip destroy-restore drill in verify lab) · **T44** (residual users/groups/sandbox)

> **This lab's practice directory is: `/sbin`** — operational focus remains system administration while automation writes `/etc/hosts` safely.

---

## LAB HEADER BLOCK

```bash
ansible --version
ansible localhost -m ping --connection=local
echo "PATH: $PATH"
ls -ld /sbin /etc/hosts /etc/nsswitch.conf
grep '^hosts:' /etc/nsswitch.conf
```

---

## Objective

Express safe `/etc/hosts` editing declaratively:

1. Use `ansible.builtin.lineinfile` with `backup: true` and regex-backed idempotence for a single mapping.
2. Use `ansible.builtin.blockinfile` with explicit markers for managed multi-line entries.
3. Verify behavior with `getent hosts`.

---

## Lab-Wide Setup — Tier B + Journal Paths

```bash
sudo -i

export LAB_NUM=37
export LAB_SLUG=hosts
export SANDBOX=/tmp/lab37b
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-37b/playbooks
mkdir -p /root/rhcsa_journal/lab-37b/task1
mkdir -p /root/rhcsa_journal/lab-37b/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — `lineinfile` with backup + idempotent regex

### Purpose

Manage one host mapping safely, preserving rollback via module backup and preventing duplicate lines.

### Main command block

```bash
PB=/root/rhcsa_journal/lab-37b/playbooks/task1.yml
TASKLOG=/tmp/lab37b/task1.txt

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 37b Task 1 — lineinfile for /etc/hosts"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Ensure lab37test.local mapping is present idempotently
      ansible.builtin.lineinfile:
        path: /etc/hosts
        regexp: '^\s*10\.99\.99\.99\s+lab37test\.local(\s|$)'
        line: '10.99.99.99 lab37test.local'
        state: present
        backup: true
      register: hosts_line

    - name: Show lineinfile outcome
      ansible.builtin.debug:
        msg:
          - "changed={{ hosts_line.changed }}"
          - "backup_file={{ hosts_line.backup | default('none') }}"
PLAYBOOK

ansible-playbook "${PB}" | tee "$TASKLOG"
ansible-playbook "${PB}" | tee -a "$TASKLOG"   # idempotence re-run

getent hosts lab37test.local | tee -a "$TASKLOG"
grep '^10.99.99.99 lab37test.local' /etc/hosts | tee -a "$TASKLOG"
```

### Expected result

- First run may show `changed=1`; second run should show no additional change.
- `getent hosts lab37test.local` resolves to `10.99.99.99`.

---

## Task 2 — `blockinfile` for managed multi-line entries

### Purpose

Declare a controlled hosts block with markers so future automation can update/remove it safely.

### Main command block

```bash
PB=/root/rhcsa_journal/lab-37b/playbooks/task2.yml
TASKLOG=/tmp/lab37b/task2.txt

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 37b Task 2 — blockinfile for /etc/hosts"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Manage lab37 hosts block with marker
      ansible.builtin.blockinfile:
        path: /etc/hosts
        marker: "# {mark} ANSIBLE MANAGED BLOCK LAB37"
        backup: true
        block: |
          10.99.99.100 lab37node1.local
          10.99.99.101 lab37node2.local
      register: hosts_block

    - name: Show blockinfile outcome
      ansible.builtin.debug:
        msg: "changed={{ hosts_block.changed }}"
PLAYBOOK

ansible-playbook "${PB}" | tee "$TASKLOG"

getent hosts lab37node1.local | tee -a "$TASKLOG"
getent hosts lab37node2.local | tee -a "$TASKLOG"
grep '^hosts:' /etc/nsswitch.conf | tee -a "$TASKLOG"

cp /tmp/lab37b/task1.txt /root/rhcsa_journal/lab-37b/task1/evidence.txt
cp /tmp/lab37b/task2.txt /root/rhcsa_journal/lab-37b/task2/evidence.txt
```

### Expected result

- Managed marker block exists in `/etc/hosts`.
- `getent hosts` resolves both block entries.
- You can explain whether `hosts: files dns` or `hosts: dns files` gets checked first (**T37-B**).

---

## Lab Closeout — Section 6 Bulletproof Teardown

```bash
set +e

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group  "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}"  2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 37b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"               && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"             && echo "❌ home remains"    || echo "✅ home gone"

set -e
```

---

## Lab 37b Checklist

- [ ] Used `lineinfile` with `backup: true` and regex idempotence (**T37-A defense**)
- [ ] Verified single-line mapping via `getent hosts`
- [ ] Used `blockinfile` with marker for multi-line entries
- [ ] Verified `hosts:` order awareness in `/etc/nsswitch.conf` (**T37-B**)
- [ ] Ran Section 6 closeout audit with four `✅` lines (**T44**)

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
