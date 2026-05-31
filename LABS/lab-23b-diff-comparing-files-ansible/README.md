# Lab 23b: Comparing File Differences (Ansible) - `ansible.builtin.copy`, `ansible.builtin.template`, `--check --diff`

- **Series:** linux-ops-mastery - File Inspection and Verification
- **Trilogy:** `23a` (RHCSA) -> **`23b` (Ansible - you are here)** -> `23c` (Verify)
- **Career arcs covered:** RHCE EX294 (module-first diffs and backups), SRE (safe config rollout with rollback path), DevOps (idempotent preview before apply)
- **Prerequisite:** Lab 00 (Ansible control node), Lab 23a (shell `diff` baseline)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 copy+backup diff proof, Task 2 template `--check --diff` preview + register parsing)
- **Practice Directory (rotation #23):** `/root`
- **Sandbox (Tier B):** `/tmp/lab23b` with `USER=labuser_23_diff`, `GROUP=labgrp_23_diff`
- **Playbooks path:** `/root/rhcsa_journal/lab-23b/playbooks/`
- **Traps rehearsed this lab:** **T23-A** (misread `diff` exit code), **T23-B** (`diff -r` and symlink surprises during verify), **T41** (skip restore drill), **T44** (cleanup residue)

> **This lab's practice directory is `/root`**. Playbooks and journal artifacts persist in `/root/rhcsa_journal/lab-23b/`.

---

## LAB HEADER BLOCK

```bash
echo "ENV:   ${ENV:-DECLARE_ME}"
echo "OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "TIME:  $(date -Is)"
echo "USER:  $(whoami)@$(hostname)"
echo "PRACTICE DIR: /root"
echo "TRAP REMINDERS THIS LAB: T23-A T23-B T41 T44"
ansible --version | head -n 2
ansible -m ping localhost 2>&1 | tail -n 4
```

> **STOP - if Ansible ping does not return `pong`, return to Lab 00 first.**

---

## Objective

Translate shell diff habits into Ansible workflows:

1. Use `ansible.builtin.copy` with `backup: true`, then verify old/new content with shell `diff`.
2. Use `ansible.builtin.template` with `--check --diff` to preview unified changes safely.
3. Capture and parse `register` output so your playbook reports exactly what changed.

---

## Concept: Ansible `--diff` is preview, shell `diff` is proof

- `--check --diff` tells you what the module *would* change.
- Shell `diff` on resulting files proves what actually changed on disk.
- In real ops, use both: preview before apply, proof after apply.

---

## Quick Reference

| Tool | Use |
|---|---|
| `ansible.builtin.copy` | Deploy byte-identical file with ownership/mode controls |
| `backup: true` | Preserve prior destination as timestamped backup |
| `ansible.builtin.template` | Render Jinja2 and deploy managed config |
| `ansible-playbook --check --diff` | Show unified diff without writing |
| `register:` + `debug` | Emit `changed`, `dest`, `backup_file` for audit |
| `diff -u old new` | Post-apply verification in shell |

---

## Lab-Wide Setup - Tier B Sandbox Stack

```bash
sudo -i

export LAB_NUM=23
export LAB_SLUG=diff
export SANDBOX=/tmp/lab23b
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" "${SANDBOX}/templates" /root/rhcsa_journal/lab-23b/playbooks
mkdir -p /root/rhcsa_journal/lab-23b/task1 /root/rhcsa_journal/lab-23b/task2
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

# Seed files for copy/template tasks
cat > "${SANDBOX}/sshd_config.managed" <<'EOF'
Port 22
PermitRootLogin prohibit-password
PasswordAuthentication yes
EOF

cat > "${SANDBOX}/templates/sshd_config.j2" <<'EOF'
Port {{ ssh_port }}
PermitRootLogin {{ permit_root_login }}
PasswordAuthentication {{ password_auth }}
# managed_by=ansible
EOF
```

---

## Task 1 - `ansible.builtin.copy` with `backup: true`, then shell `diff`

**Practice directory this task:** `/root` + `/tmp/lab23b`

### Purpose

Prove that backup rotation happened and compare the backup against the new destination using `diff -u`.

### Playbook: `task1-copy.yml`

```yaml
---
- name: "Lab 23b Task 1 copy with backup"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    src_file: "/tmp/lab23b/sshd_config.managed"
    dest_file: "/tmp/lab23b/sshd_config.deploy"
  tasks:
    - name: "Seed destination so backup has something to rotate"
      ansible.builtin.copy:
        content: |
          Port 22
          PermitRootLogin yes
          PasswordAuthentication yes
        dest: "{{ dest_file }}"
        mode: '0600'

    - name: "Deploy managed file with backup enabled"
      ansible.builtin.copy:
        src: "{{ src_file }}"
        dest: "{{ dest_file }}"
        remote_src: true
        owner: root
        group: root
        mode: '0600'
        backup: true
      register: copy_result

    - name: "Show copy result fields"
      ansible.builtin.debug:
        msg:
          - "changed={{ copy_result.changed }}"
          - "dest={{ copy_result.dest }}"
          - "backup={{ copy_result.backup_file | default('none') }}"
```

### Main command block

```bash
cat > /root/rhcsa_journal/lab-23b/playbooks/task1-copy.yml <<'YAML'
---
- name: "Lab 23b Task 1 copy with backup"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    src_file: "/tmp/lab23b/sshd_config.managed"
    dest_file: "/tmp/lab23b/sshd_config.deploy"
  tasks:
    - name: "Seed destination so backup has something to rotate"
      ansible.builtin.copy:
        content: |
          Port 22
          PermitRootLogin yes
          PasswordAuthentication yes
        dest: "{{ dest_file }}"
        mode: '0600'
    - name: "Deploy managed file with backup enabled"
      ansible.builtin.copy:
        src: "{{ src_file }}"
        dest: "{{ dest_file }}"
        remote_src: true
        owner: root
        group: root
        mode: '0600'
        backup: true
      register: copy_result
    - name: "Show copy result fields"
      ansible.builtin.debug:
        msg:
          - "changed={{ copy_result.changed }}"
          - "dest={{ copy_result.dest }}"
          - "backup={{ copy_result.backup_file | default('none') }}"
YAML

ansible-playbook /root/rhcsa_journal/lab-23b/playbooks/task1-copy.yml \
  2>&1 | tee /tmp/lab23b/task1.txt

BACKUP_FILE=$(awk -F'backup=' '/backup=/{print $2}' /tmp/lab23b/task1.txt | tail -n1)
echo "backup file: ${BACKUP_FILE}" | tee -a /tmp/lab23b/task1.txt

if [ -n "${BACKUP_FILE}" ] && [ -f "${BACKUP_FILE}" ]; then
  diff -u "${BACKUP_FILE}" /tmp/lab23b/sshd_config.deploy | tee -a /tmp/lab23b/task1.txt
  echo "diff exit: ${PIPESTATUS[0]}" | tee -a /tmp/lab23b/task1.txt
fi
```

### Journal write

```bash
cp /tmp/lab23b/task1.txt /root/rhcsa_journal/lab-23b/task1/evidence.txt
```

---

## Task 2 - `ansible.builtin.template` with `--check --diff`, register and parse

**Practice directory this task:** `/root` + `/tmp/lab23b`

### Purpose

Preview unified diff safely before changing files, then parse registered results to prove changed/no-changed states.

### Playbook: `task2-template.yml`

```yaml
---
- name: "Lab 23b Task 2 template diff preview"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    dest_file: "/tmp/lab23b/sshd_config.templated"
    ssh_port: 2222
    permit_root_login: "no"
    password_auth: "no"
  tasks:
    - name: "Render template to destination"
      ansible.builtin.template:
        src: "/tmp/lab23b/templates/sshd_config.j2"
        dest: "{{ dest_file }}"
        owner: root
        group: root
        mode: '0600'
        backup: true
      register: tpl_result

    - name: "Parse register values for audit"
      ansible.builtin.debug:
        msg:
          - "changed={{ tpl_result.changed }}"
          - "dest={{ tpl_result.dest }}"
          - "checksum={{ tpl_result.checksum | default('none') }}"
          - "backup={{ tpl_result.backup_file | default('none') }}"
```

### Main command block

```bash
cat > /root/rhcsa_journal/lab-23b/playbooks/task2-template.yml <<'YAML'
---
- name: "Lab 23b Task 2 template diff preview"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    dest_file: "/tmp/lab23b/sshd_config.templated"
    ssh_port: 2222
    permit_root_login: "no"
    password_auth: "no"
  tasks:
    - name: "Render template to destination"
      ansible.builtin.template:
        src: "/tmp/lab23b/templates/sshd_config.j2"
        dest: "{{ dest_file }}"
        owner: root
        group: root
        mode: '0600'
        backup: true
      register: tpl_result
    - name: "Parse register values for audit"
      ansible.builtin.debug:
        msg:
          - "changed={{ tpl_result.changed }}"
          - "dest={{ tpl_result.dest }}"
          - "checksum={{ tpl_result.checksum | default('none') }}"
          - "backup={{ tpl_result.backup_file | default('none') }}"
YAML

ansible-playbook --check --diff /root/rhcsa_journal/lab-23b/playbooks/task2-template.yml \
  2>&1 | tee /tmp/lab23b/task2-check-diff.txt

ansible-playbook /root/rhcsa_journal/lab-23b/playbooks/task2-template.yml \
  2>&1 | tee /tmp/lab23b/task2-apply.txt

awk '/changed=/{print}' /tmp/lab23b/task2-apply.txt | tee /tmp/lab23b/task2.txt
awk '/backup=|checksum=|dest=/{print}' /tmp/lab23b/task2-apply.txt | tee -a /tmp/lab23b/task2.txt
```

### Journal write

```bash
cp /tmp/lab23b/task2-check-diff.txt /root/rhcsa_journal/lab-23b/task2/check-diff.txt
cp /tmp/lab23b/task2-apply.txt /root/rhcsa_journal/lab-23b/task2/apply.txt
cp /tmp/lab23b/task2.txt /root/rhcsa_journal/lab-23b/task2/evidence.txt
```

---

## Lab Closeout - Bulletproof Teardown (Section 6)

```bash
set +e
awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null
getent passwd "${USER}" >/dev/null 2>&1 && userdel -r "${USER}" 2>/dev/null
getent group "${GROUP}" >/dev/null 2>&1 && groupdel "${GROUP}" 2>/dev/null
rm -rf "${SANDBOX}"

echo "-- Lab 23b cleanup audit --"
getent passwd "${USER}" >/dev/null && echo "FAIL user remains" || echo "OK user gone"
getent group "${GROUP}" >/dev/null && echo "FAIL group remains" || echo "OK group gone"
test -d "${SANDBOX}" && echo "FAIL sandbox remains" || echo "OK sandbox gone"
test -d "${USER_HOME}" && echo "FAIL home remains" || echo "OK home gone"
set -e
```

---

## Lab 23b Checklist

- [ ] Tier B setup completed in `/tmp/lab23b`
- [ ] Task 1 used `ansible.builtin.copy` with `backup: true`
- [ ] Task 1 compared backup file vs deployed file with shell `diff -u`
- [ ] Task 2 ran `ansible-playbook --check --diff` and reviewed unified output
- [ ] Task 2 parsed registered result fields (`changed`, `dest`, `checksum`, `backup`)
- [ ] Section 6 closeout returned four `OK` audit lines

---

## Related Labs

| Lab | Connection |
|---|---|
| `23a` | Hand-typed `diff` foundations this lab automates |
| `23c` | Auditor replay + destroy-restore proof |
| `00a/00b` | Required Ansible control node and module fluency |

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
