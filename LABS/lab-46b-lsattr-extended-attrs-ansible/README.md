# Lab 46b: Identifying File Attributes (Ansible) — `ansible.builtin.shell`, `register`, `failed_when`

- **Series:** linux-ops-mastery — Permissions and Attribute Automation
- **Trilogy:** [`46a`](../lab-46a-lsattr-extended-attrs-rhcsa/) (RHCSA) → **`46b`** (Ansible boundary) → [`46c`](../lab-46c-lsattr-extended-attrs-verify/) (Verify)
- **Tasks:** 2 (Task 1 = `shell: lsattr ... | tee` with `register`; Task 2 = assert required attr via shell output)
- **Practice Directory:** `/tmp`
- **Sandbox (Tier B):** `/tmp/lab46b`, `USER=labuser_46_lsattr`, `GROUP=labgrp_46_lsattr`
- **Traps rehearsed:** `T46-A` · `T46-B` · `T41` · `T44`

> **Section 18 boundary note:** there is no first-class Ansible module that fully reproduces all `lsattr` letter semantics across filesystems. `ansible.builtin.stat` can expose limited attributes, but `lsattr` fidelity typically requires `ansible.builtin.shell` and output validation.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T46-A T46-B T41 T44"
echo "📁  PRACTICE DIR: /tmp"
ansible --version
ansible localhost -m ping --connection=local
```

> **STOP — paste output before setup.**

---

## Lab-Wide Setup — Tier B Sandbox Stack

```bash
sudo -i

export LAB_NUM=46
export LAB_SLUG=lsattr
export SANDBOX=/tmp/lab46b
export GROUP=labgrp_46_lsattr
export USER=labuser_46_lsattr
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-46b/playbooks
mkdir -p /root/rhcsa_journal/lab-46b/task1
mkdir -p /root/rhcsa_journal/lab-46b/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

touch /tmp/lab46b/attr-audit.txt
chattr +A /tmp/lab46b/attr-audit.txt 2>/dev/null || true

id "${USER}"
ls -ld /tmp "${SANDBOX}" "${USER_HOME}"
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — Boundary-safe `shell` capture with `register`

**Practice directory this task:** `/tmp`

### Purpose

Run `lsattr` from Ansible exactly as shell users do, capture output with `register`, and persist it to journal evidence.

### Main Command Block

```bash
TASKLOG=/tmp/lab46b/task1.txt
PB=/root/rhcsa_journal/lab-46b/playbooks/task1.yml

cat > "${PB}" <<'PLAYBOOK'
---
- name: Lab 46b Task 1 lsattr capture
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Capture lsattr recursive output
      ansible.builtin.shell: "lsattr -R /tmp/lab46b 2>&1 | tee /tmp/lab46b/lsattr-r.txt"
      register: lsattr_run
      changed_when: false
      failed_when: false

    - name: Optional limited stat attributes view
      ansible.builtin.stat:
        path: /tmp/lab46b/attr-audit.txt
      register: st

    - name: Print boundary reminder
      ansible.builtin.debug:
        msg:
          - "shell rc={{ lsattr_run.rc }}"
          - "stdout_lines={{ lsattr_run.stdout_lines | length }}"
          - "stat attr support can be partial; rely on lsattr output for full letter checks"
PLAYBOOK

ansible-playbook "${PB}" 2>&1 | tee "${TASKLOG}"
wc -l /tmp/lab46b/lsattr-r.txt | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal Write

```bash
LAB=lab-46b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab46b/task1.txt "$JDIR/evidence.txt"
cp /tmp/lab46b/lsattr-r.txt "$JDIR/lsattr-r.txt"
```

> **STOP — paste recap lines and one `lsattr-r.txt` sample line before Task 2.**

---

## Task 2 — Trap-proof assertion for required attr letter

**Practice directory this task:** `/tmp`

### Purpose

Assert that a specific attribute letter is present using shell output, because module-only checks are incomplete for this topic.

### Main Command Block

```bash
TASKLOG=/tmp/lab46b/task2.txt
PB=/root/rhcsa_journal/lab-46b/playbooks/task2.yml

cat > "${PB}" <<'PLAYBOOK'
---
- name: Lab 46b Task 2 attribute assertion
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Ensure test file exists and try +A
      ansible.builtin.shell: "touch /tmp/lab46b/assert-target.txt && chattr +A /tmp/lab46b/assert-target.txt 2>/dev/null || true"
      changed_when: false

    - name: Read attrs through lsattr
      ansible.builtin.shell: "lsattr /tmp/lab46b/assert-target.txt"
      register: attr_out
      changed_when: false
      failed_when: false

    - name: Assert attr output is meaningful (trap guard)
      ansible.builtin.assert:
        that:
          - attr_out.rc == 0
          - attr_out.stdout | length > 0
          - "'/tmp/lab46b/assert-target.txt' in attr_out.stdout"
        fail_msg: "T46-B/T46-A boundary hit: attr output missing or unsupported on this FS."
        success_msg: "lsattr output captured; now inspect letters (A/i/a/etc.) based on FS support."

    - name: Show attrs for human review
      ansible.builtin.debug:
        var: attr_out.stdout
PLAYBOOK

ansible-playbook "${PB}" 2>&1 | tee "${TASKLOG}"
echo "exit was: $?"
```

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | `ansible.builtin.shell` | Preserves exact `lsattr` behavior |
| ✅ | `register` | Captures stdout for assertions |
| ✅ | `assert` | Fails fast when evidence is missing |
| 🪤 `T46-A` | Ext4 vs XFS letter differences | Assert presence of output/path first, then interpret letters |
| 🪤 `T46-B` | Special-file errors | Use controlled test files and clear fail messages |

### Journal Write

```bash
LAB=lab-46b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab46b/task2.txt "$JDIR/evidence.txt"
```

---

## Lab Closeout — Section 6 Teardown

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then
    userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
    groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 46b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
echo "Cleanup complete at $(date -Is)"
echo "exit was: $?"
```

---

## Author

**Kelvin R. Tobias**
