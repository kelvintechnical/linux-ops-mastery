# Lab 38b: Configuring DNS Servers (Ansible) — declarative NM + static boundary pattern

- **Series:** linux-ops-mastery — Networking and Name Resolution
- **Trilogy:** [`38a`](../lab-38a-resolv-conf-dns-rhcsa/) (RHCSA hand-typed) → **`38b`** (Ansible) → [`38c`](../lab-38c-resolv-conf-dns-verify/) (Verify capstone)
- **Time Estimate:** 30-45 minutes
- **Tasks:** 2 (Task 1 = `community.general.nmcli` with `dns4` for `lab38test` · Task 2 = `ansible.builtin.copy` to `/etc/resolv.conf` for NM-disabled static edge case)
- **Practice Directory (rotation #38):** `/lib`
- **Playbooks:** `/root/rhcsa_journal/lab-38b/playbooks/`
- **Sandbox (Tier B):** `/tmp/lab38b` with `USER=labuser_38_resolv`, `GROUP=labgrp_38_resolv`, `USER_HOME=/tmp/lab38b/home_labuser_38_resolv`
- **Test Connection:** `lab38test` only
- **Traps rehearsed:** **T38-A** · **T38-B** · **T41** · **T44**

> **Boundary note:** use NM profile parameters when NM manages DNS. Use direct file copy only when resolver management is intentionally static/NM-disabled.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
ansible --version | head -n 2
ansible localhost -m ping --connection=local
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T38-A T38-B T41 T44"
echo "📁  PRACTICE DIR: /lib"
ls -ld /lib /etc
nmcli con show | head -n 12
```

> **STOP — paste header output before setup.**

---

## Objective

1. Automate DNS server/search configuration in NetworkManager declaratively.
2. Validate generated `/etc/resolv.conf` output after profile activation.
3. Document static-mode boundary handling with safe backup and `copy` rollback path.

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=38
export LAB_SLUG=resolv
export SANDBOX=/tmp/lab38b
export GROUP=labgrp_38_resolv
export USER=labuser_38_resolv
export USER_HOME=${SANDBOX}/home_${USER}
export CON_NAME=lab38test

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-38b/playbooks /root/rhcsa_journal/lab-38b/task1 /root/rhcsa_journal/lab-38b/task2
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

nmcli con show "${CON_NAME}" >/dev/null 2>&1 || nmcli con add type ethernet ifname lo con-name "${CON_NAME}"
cp /etc/resolv.conf /tmp/lab38b/resolv.bak

ansible-galaxy collection install community.general
id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /lib
```

---

## Task 1 — Declarative DNS with `community.general.nmcli` (`dns4`)

### Purpose

Set DNS in NM connection profile via Ansible, then activate and verify resolver output.

### Playbook (`/root/rhcsa_journal/lab-38b/playbooks/task1.yml`)

```yaml
---
- name: "Lab 38b Task 1 - declarative NM DNS"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    con_name: lab38test

  tasks:
    - name: "Ensure backup of resolv.conf exists"
      ansible.builtin.copy:
        src: /etc/resolv.conf
        remote_src: true
        dest: /tmp/lab38b/resolv.task1.bak
        mode: "0644"

    - name: "Configure DNS declaratively on test connection"
      community.general.nmcli:
        conn_name: "{{ con_name }}"
        type: ethernet
        ifname: lo
        method4: manual
        ip4: 198.51.100.38/24
        dns4:
          - 1.1.1.1
          - 8.8.8.8
        dns4_search:
          - lab38.local
          - example.internal
        autoconnect: false
        state: present

    - name: "Activate profile so NM regenerates resolv.conf"
      ansible.builtin.command: nmcli con up "{{ con_name }}"
      register: con_up
      changed_when: "'successfully activated' in (con_up.stdout | lower) or con_up.rc == 0"

    - name: "Capture resolver view"
      ansible.builtin.shell: "grep -E '^(nameserver|search)' /etc/resolv.conf"
      register: resolv_view
      changed_when: false

    - name: "Write summary"
      ansible.builtin.copy:
        dest: /tmp/lab38b/task1-summary.txt
        mode: "0644"
        content: |
          con_up_rc={{ con_up.rc }}
          resolv_lines={{ resolv_view.stdout_lines | length }}
          resolv_first={{ resolv_view.stdout_lines | first | default('none') }}
```

### Run + verify

```bash
TASKLOG=/tmp/lab38b/task1.txt
ansible-playbook /root/rhcsa_journal/lab-38b/playbooks/task1.yml 2>&1 | tee "$TASKLOG"
cat /tmp/lab38b/task1-summary.txt | tee -a "$TASKLOG"
cat /etc/resolv.conf | tee -a "$TASKLOG"
```

### Concept Card

| Concept | What it does |
|---|---|
| `community.general.nmcli` + `dns4` | Declarative DNS profile configuration under NM control |
| `nmcli con up` | Forces profile activation and resolver regeneration |
| `grep ^(nameserver\|search)` | Fast validation of effective resolver lines |
| **🪤 Trap Risk T38-A** | Direct file edits are overwritten on reconnect in NM-managed mode |
| **🪤 Trap Risk T38-B** | Keep DNS server list to practical max of 3 effective lines |

### Journal write

```bash
LAB=lab-38b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab38b/task1.txt "$JDIR/evidence.txt"
cp /tmp/lab38b/task1-summary.txt "$JDIR/task1-summary.txt"
cp /root/rhcsa_journal/lab-38b/playbooks/task1.yml "$JDIR/task1.yml"
```

---

## Task 2 — Static boundary edge: `copy` to `/etc/resolv.conf` when NM is disabled

### Purpose

Rehearse the controlled exception path: only write `/etc/resolv.conf` directly when resolver management is deliberately static.

### Playbook (`/root/rhcsa_journal/lab-38b/playbooks/task2.yml`)

```yaml
---
- name: "Lab 38b Task 2 - static resolv.conf boundary pattern"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Boundary note marker"
      ansible.builtin.copy:
        dest: /tmp/lab38b/static-boundary-note.txt
        mode: "0644"
        content: |
          This task is for NM-disabled/static mode only.
          In NM-managed mode, configure dns via profile (Task 1).

    - name: "Backup + write static resolv.conf with rollback support"
      ansible.builtin.copy:
        dest: /etc/resolv.conf
        backup: true
        mode: "0644"
        content: |
          # static-mode demo for Lab 38b Task 2
          nameserver 9.9.9.9
          nameserver 1.0.0.1
          search static.lab38.local

    - name: "Capture static resolver state"
      ansible.builtin.shell: "cat /etc/resolv.conf"
      register: static_view
      changed_when: false

    - name: "Save task summary"
      ansible.builtin.copy:
        dest: /tmp/lab38b/task2-summary.txt
        mode: "0644"
        content: |
          static_lines={{ static_view.stdout_lines | length }}
          static_first={{ static_view.stdout_lines | first | default('none') }}
```

### Run + verify

```bash
TASKLOG=/tmp/lab38b/task2.txt
ansible-playbook /root/rhcsa_journal/lab-38b/playbooks/task2.yml 2>&1 | tee "$TASKLOG"
cat /tmp/lab38b/task2-summary.txt | tee -a "$TASKLOG"
ls -1t /etc/resolv.conf.* 2>/dev/null | head -n 3 | tee -a "$TASKLOG"

# Restore baseline immediately after boundary demonstration.
cp /tmp/lab38b/resolv.bak /etc/resolv.conf
```

### Concept Card

| Concept | What it does |
|---|---|
| `ansible.builtin.copy backup: true` | Safe overwrite with timestamped rollback file |
| Static boundary mode | Manual resolver file applies only when NM no longer owns resolver state |
| Immediate restore | Prevents cross-lab resolver drift |
| **🪤 Trap Risk T44** | Forgetting rollback/cleanup leaves hidden DNS residue |

### Journal write

```bash
LAB=lab-38b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab38b/task2.txt "$JDIR/evidence.txt"
cp /tmp/lab38b/task2-summary.txt "$JDIR/task2-summary.txt"
cp /tmp/lab38b/static-boundary-note.txt "$JDIR/static-boundary-note.txt"
cp /root/rhcsa_journal/lab-38b/playbooks/task2.yml "$JDIR/task2.yml"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

test -f /tmp/lab38b/resolv.bak && cp /tmp/lab38b/resolv.bak /etc/resolv.conf
nmcli con delete lab38test 2>/dev/null || true

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 38b cleanup audit ──"
nmcli con show | grep -w lab38test >/dev/null && echo "❌ connection remains" || echo "✅ connection gone"
test -f /etc/resolv.conf && echo "✅ resolv.conf present" || echo "❌ resolv.conf missing"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"

set -e
```

---

## Lab 38b Checklist (2 tasks + closeout)

- [ ] Task 1 used `community.general.nmcli` with `dns4` and activated `lab38test`
- [ ] Task 1 verified generated `/etc/resolv.conf` lines (`nameserver` + `search`)
- [ ] Task 2 documented static boundary and used `copy backup: true` for `/etc/resolv.conf`
- [ ] `/etc/resolv.conf` was restored from backup and `lab38test` removed
- [ ] Section 6 closeout ended with cleanup audit checks

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
