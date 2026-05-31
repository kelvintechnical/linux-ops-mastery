# Lab 48b: Viewing ACLs via Ansible — query + assert

- **Series:** linux-ops-mastery — Permissions, Special Bits, and ACLs
- **Trilogy:** `48a` (RHCSA) → `48b` (Ansible) → `48c` (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (objective context):** `/srv` (inspection context), `/tmp/lab48b` (safe automation sandbox)
- **Sandbox (Tier B):** `/tmp/lab48b` with `USER=labuser_48_getfacl`, `GROUP=labgrp_48_getfacl`
- **Playbooks live at:** `/root/rhcsa_journal/lab-48b/playbooks/`
- **Traps rehearsed:** **T48-A** (`ls -l` `+` missing means no extended ACL) · **T48-B** (`getfacl` non-recursive unless `-R`) · **T41** (destroy-restore drill appears in 48c) · **T44** (cleanup audit)

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /srv (read), /tmp/lab48b (write)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "🕒 TIME: $(date -Is)"
echo "⚠️ TRAPS: T48-A T48-B T41 T44"
ansible --version | head -n 2
ansible -m ping localhost 2>&1 | tail -n 4
```

> **STOP — paste output before setup.**

---

## Objective

Build an auditor-grade Ansible ACL query flow:

1. Query ACLs with automation (`ansible.posix.acl state=query` or `ansible.builtin.shell: getfacl ...` + `register`).
2. Assert specific ACL entries are present in stdout.
3. Capture machine-verifiable evidence for later restore drills.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export LAB_NUM=48
export LAB_SLUG=getfacl
export SANDBOX=/tmp/lab48b
export GROUP=labgrp_48_getfacl
export USER=labuser_48_getfacl
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}/task1" "${SANDBOX}/task2" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-48b/task1
mkdir -p /root/rhcsa_journal/lab-48b/task2
mkdir -p /root/rhcsa_journal/lab-48b/playbooks

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

touch /tmp/lab48b/acl-target
setfacl -m u:${USER}:rw /tmp/lab48b/acl-target
```

---

## Task 1 — Query ACLs with Ansible and register output

### Purpose

Use Ansible to collect ACL state in a way that can be asserted and audited.

### Main command block

```bash
TASKLOG=/tmp/lab48b/task1/task1.txt
PLAY=/root/rhcsa_journal/lab-48b/playbooks/task1.yml

cat > "${PLAY}" <<'EOF'
---
- name: Lab 48b Task 1 - query ACL data
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Query ACL via shell fallback (portable)
      ansible.builtin.shell: getfacl --absolute-names /tmp/lab48b/acl-target
      register: acl_query
      changed_when: false

    - name: Show query stdout
      ansible.builtin.debug:
        var: acl_query.stdout_lines
EOF

ansible-playbook "${PLAY}" 2>&1 | tee "${TASKLOG}"
ls -l /tmp/lab48b/acl-target | tee -a "${TASKLOG}"
echo "exit was: $?"
```

> Optional variant for environments with `ansible.posix.acl` query support:
>
> - `ansible.posix.acl: path=/tmp/lab48b/acl-target state=query`

### Expected checks

- Playbook succeeds with `changed=0` for pure query flow.
- Registered stdout includes ACL header and at least one `user:` ACL line.
- `ls -l` shows `+` marker on target file.

### Journal write

```bash
cp /tmp/lab48b/task1/task1.txt /root/rhcsa_journal/lab-48b/task1/evidence.txt
cat > /root/rhcsa_journal/lab-48b/task1/done.txt <<EOF
LAB: lab-48b
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 — Assert required ACL entry exists in stdout

### Purpose

Fail fast if the expected ACL grant is missing, using declarative assertions.

### Main command block

```bash
TASKLOG=/tmp/lab48b/task2/task2.txt
PLAY=/root/rhcsa_journal/lab-48b/playbooks/task2.yml

cat > "${PLAY}" <<'EOF'
---
- name: Lab 48b Task 2 - assert ACL entry exists
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    acl_path: /tmp/lab48b/acl-target
    acl_user: labuser_48_getfacl
  tasks:
    - name: Query ACL text
      ansible.builtin.shell: getfacl --absolute-names {{ acl_path }}
      register: acl_query
      changed_when: false

    - name: Assert specific ACL entry is present
      ansible.builtin.assert:
        that:
          - "'user:' ~ acl_user ~ ':rw-' in acl_query.stdout"
        fail_msg: "Expected ACL entry missing for {{ acl_user }}"
        success_msg: "ACL entry found for {{ acl_user }}"

    - name: Query recursively to rehearse T48-B
      ansible.builtin.shell: getfacl -R /tmp/lab48b
      register: acl_recursive
      changed_when: false

    - name: Show recursive line count
      ansible.builtin.debug:
        msg: "Recursive ACL lines: {{ acl_recursive.stdout_lines | length }}"
EOF

ansible-playbook "${PLAY}" 2>&1 | tee "${TASKLOG}"
echo "exit was: $?"
```

### Expected checks

- `assert` passes with success message for `${USER}` ACL entry.
- Recursive query completes and prints line-count debug output.

### Journal write

```bash
cp /tmp/lab48b/task2/task2.txt /root/rhcsa_journal/lab-48b/task2/evidence.txt
cat > /root/rhcsa_journal/lab-48b/task2/done.txt <<EOF
LAB: lab-48b
TASK: task2
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Lab Closeout — Section 6 Teardown

```bash
set +e
userdel -r "${USER}" 2>/dev/null
groupdel "${GROUP}" 2>/dev/null
rm -rf "${SANDBOX}"

echo "── Lab 48b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Author

**Kelvin R. Tobias**
