# Lab 35b: Text-Based Network Config (Ansible) — hostname + NetworkManager replacement patterns

- **Series:** linux-ops-mastery — NetworkManager and Host Identity
- **Trilogy:** [`35a`](../lab-35a-nmtui-tui-config-rhcsa/) (RHCSA TUI practice) → **`35b`** (Ansible declarative replacement) → [`35c`](../lab-35c-nmtui-tui-config-verify/) (verify capstone)
- **Section 18 boundary note (explicit):** `nmtui`, `nmtui-edit`, and `nmtui-connect` are interactive terminal UI tools and have no direct Ansible module. In automation, use `ansible.builtin.hostname` and `community.general.nmcli` instead.
- **Time Estimate:** 30-40 minutes
- **Tasks:** 2 (Task 1 = replace `nmtui-hostname` and `nmtui-edit` intents declaratively; Task 2 = add `failed_when` guard asserting hostname really applied)
- **Practice Directory (rotation #35):** `/tmp`
- **Playbooks:** `/root/rhcsa_journal/lab-35b/playbooks/`
- **Sandbox (Tier B):** `/tmp/lab35b` with `USER=labuser_35_nmtui`, `GROUP=labgrp_35_nmtui`, `USER_HOME=/tmp/lab35b/home_labuser_35_nmtui`
- **Traps rehearsed:** **T35-A** · **T35-B** · **T41** · **T44**

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
ansible --version | head -n 2
ansible localhost -m ping --connection=local
python3 -c "import importlib.util as u; print('community.general present:', bool(u.find_spec('ansible_collections.community.general')))"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T35-A T35-B T41 T44"
echo "📁  PRACTICE DIR: /tmp"
```

> **STOP — paste header output before setup.**

---

## Objective

1. Replace interactive `nmtui` intent with declarative Ansible modules.
2. Encode hostname/network state as playbook data, not keystrokes.
3. Guard against false-positive success with `failed_when` validation.

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=35
export LAB_SLUG=nmtui
export SANDBOX=/tmp/lab35b
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-35b/playbooks /root/rhcsa_journal/lab-35b/task1 /root/rhcsa_journal/lab-35b/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

ORIG_HOST="$(hostnamectl --static)"
echo "${ORIG_HOST}" > /tmp/lab35b/original-hostname.txt
```

---

## Task 1 — Declarative replacement for `nmtui-hostname` and `nmtui-edit`

### Purpose

Implement the Section 18 replacement pair explicitly:

- `ansible.builtin.hostname` for host identity
- `community.general.nmcli` for NetworkManager connection properties

### Playbook (`/root/rhcsa_journal/lab-35b/playbooks/task1.yml`)

```yaml
---
- name: "Lab 35b Task 1 - replace nmtui intent declaratively"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    target_hostname: lab35b-ansible
    conn_name: "{{ lookup('pipe', 'nmcli -t -f NAME con show --active | head -n 1') }}"

  tasks:
    - name: "Set persistent hostname (nmtui-hostname replacement)"
      ansible.builtin.hostname:
        name: "{{ target_hostname }}"
      register: hostname_set

    - name: "Apply nmcli connection settings (nmtui-edit replacement)"
      community.general.nmcli:
        conn_name: "{{ conn_name }}"
        autoconnect: true
        dns4:
          - 1.1.1.1
          - 8.8.8.8
        method4: auto
        state: present
      register: nm_profile

    - name: "Write task summary artifact"
      ansible.builtin.copy:
        dest: /tmp/lab35b/task1-summary.txt
        mode: "0644"
        content: |
          hostname_changed={{ hostname_set.changed }}
          nmcli_changed={{ nm_profile.changed }}
          connection={{ conn_name }}
          target_hostname={{ target_hostname }}
```

### Run + verify

```bash
TASKLOG=/tmp/lab35b/task1.txt
ansible-playbook /root/rhcsa_journal/lab-35b/playbooks/task1.yml 2>&1 | tee "$TASKLOG"
hostnamectl --static | tee -a "$TASKLOG"
cat /tmp/lab35b/task1-summary.txt | tee -a "$TASKLOG"
nmcli -f NAME,TYPE,AUTOCONNECT con show | tee -a "$TASKLOG"
echo "exit was: $?" | tee -a "$TASKLOG"
```

### Section 18 boundary card

| Interactive tool | Why boundary exists | Ansible replacement |
|---|---|---|
| `nmtui-hostname` | TUI-only workflow, no module API | `ansible.builtin.hostname` |
| `nmtui-edit` | TUI form fields only | `community.general.nmcli` |
| `nmtui-connect` | Interactive session chooser | `community.general.nmcli` + profile state |

### Journal write

```bash
LAB=lab-35b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab35b/task1.txt "$JDIR/evidence.txt"
cp /tmp/lab35b/task1-summary.txt "$JDIR/task1-summary.txt"
cp /root/rhcsa_journal/lab-35b/playbooks/task1.yml "$JDIR/task1.yml"
```

---

## Task 2 — `failed_when` trap gate: assert hostname applied

### Purpose

Prevent silent drift by failing the play when desired hostname and observed runtime value do not match.

### Playbook (`/root/rhcsa_journal/lab-35b/playbooks/task2.yml`)

```yaml
---
- name: "Lab 35b Task 2 - failed_when hostname assertion"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    target_hostname: lab35b-assert

  tasks:
    - name: "Set target hostname declaratively"
      ansible.builtin.hostname:
        name: "{{ target_hostname }}"
      register: host_set

    - name: "Read current static hostname"
      ansible.builtin.command:
        cmd: hostnamectl --static
      register: host_now
      changed_when: false
      failed_when: host_now.stdout.strip() != target_hostname

    - name: "Write assertion evidence"
      ansible.builtin.copy:
        dest: /tmp/lab35b/task2-assertions.txt
        mode: "0644"
        content: |
          target_hostname={{ target_hostname }}
          observed_hostname={{ host_now.stdout.strip() }}
          host_set_changed={{ host_set.changed }}
```

### Run + verify

```bash
TASKLOG=/tmp/lab35b/task2.txt
ansible-playbook /root/rhcsa_journal/lab-35b/playbooks/task2.yml 2>&1 | tee "$TASKLOG"
cat /tmp/lab35b/task2-assertions.txt | tee -a "$TASKLOG"
hostnamectl --static | tee -a "$TASKLOG"
echo "exit was: $?" | tee -a "$TASKLOG"
```

### Journal write

```bash
LAB=lab-35b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab35b/task2.txt "$JDIR/evidence.txt"
cp /tmp/lab35b/task2-assertions.txt "$JDIR/task2-assertions.txt"
cp /root/rhcsa_journal/lab-35b/playbooks/task2.yml "$JDIR/task2.yml"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

ORIG_HOST="$(cat /tmp/lab35b/original-hostname.txt 2>/dev/null)"
test -n "${ORIG_HOST}" && hostnamectl set-hostname "${ORIG_HOST}"

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 35b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"   || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}"               && echo "❌ sandbox remains"|| echo "✅ sandbox gone"
test -d "${USER_HOME}"             && echo "❌ home remains"   || echo "✅ home gone"

set -e
```

---

## Lab 35b Checklist (2 tasks + closeout)

- [ ] Task 1 replaced `nmtui` intents with `ansible.builtin.hostname` + `community.general.nmcli`
- [ ] Task 2 used `failed_when` to assert hostname application
- [ ] Section 18 boundary was explicitly documented
- [ ] Section 6 closeout ended with four `✅` audit lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
