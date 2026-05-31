# Lab 39c: Verify SSH Key-Based Authentication — audit + destroy/restore

- **Series:** linux-ops-mastery — SSH Access and Authentication
- **Trilogy:** `39a` (RHCSA) -> `39b` (Ansible) -> `39c` (Verify — you are here)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = audit + verify, Task 2 = destroy-restore drill)
- **Practice Directory (rotation #39):** `/lib64`
- **Sandbox (Tier B):** `/tmp/lab39c` with `USER=labuser_39_sshkey`, `GROUP=labgrp_39_sshkey`
- **Traps rehearsed this lab:** **T39-A** · **T39-B** · **T41** · **T44**

> **Prerequisite:** `sshd` must be active on localhost for key-auth verification.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /lib64"
echo "⚠️  TRAP REMINDERS THIS LAB: T39-A T39-B T41 T44"
ls -ld /lib64
systemctl is-active sshd 2>/dev/null || echo "sshd not active"
```

> **STOP — paste header output before setup.**

---

## Objective

1. Audit Tier B account, SSH directory permissions, and key-auth behavior.
2. Prove `ssh -i KEY USER@localhost true` works with strict permission checks.
3. Run a destroy-restore drill to remove keys and recover state with playbook automation.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab39c
export GROUP=labgrp_39_sshkey
export USER=labuser_39_sshkey
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}/.ssh" /root/rhcsa_journal/lab-39c/task1 /root/rhcsa_journal/lab-39c/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
chmod 700 "${USER_HOME}/.ssh"
```

---

## Task 1 — Audit account state and verify SSH key login

### Purpose

Perform verification-seat checks: account exists, permissions are strict, and key auth succeeds for the Tier B user on localhost.

### Main command block

```bash
TASKLOG=/tmp/lab39c/task1.txt

# Build a verify key for this lab
sudo -u "${USER}" ssh-keygen -t ed25519 -f "${USER_HOME}/.ssh/lab39_verify_ed25519" -N '' 2>&1 | tee "${TASKLOG}"
sudo -u "${USER}" bash -c 'cat "'"${USER_HOME}"'/.ssh/lab39_verify_ed25519.pub" >> "'"${USER_HOME}"'/.ssh/authorized_keys"'

chmod 700 "${USER_HOME}/.ssh"
chmod 600 "${USER_HOME}/.ssh/lab39_verify_ed25519"
chmod 600 "${USER_HOME}/.ssh/authorized_keys"
chown -R "${USER}:${GROUP}" "${USER_HOME}/.ssh"

echo "═══ identity + permission audit ═══" | tee -a "${TASKLOG}"
getent passwd "${USER}"                     | tee -a "${TASKLOG}"
stat -c '%a %U:%G %n' "${USER_HOME}/.ssh"  | tee -a "${TASKLOG}"
stat -c '%a %U:%G %n' "${USER_HOME}/.ssh/authorized_keys" | tee -a "${TASKLOG}"

echo "═══ localhost key-auth test ═══" | tee -a "${TASKLOG}"
sudo -u "${USER}" ssh -i "${USER_HOME}/.ssh/lab39_verify_ed25519" \
  -o PreferredAuthentications=publickey \
  -o PasswordAuthentication=no \
  -o StrictHostKeyChecking=accept-new \
  "${USER}@localhost" true 2>&1 | tee -a "${TASKLOG}"

echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-39c/task1
cp /tmp/lab39c/task1.txt "${JDIR}/audit.txt"
```

---

## Task 2 — Destroy-restore drill (remove keys, regenerate via playbook)

### Purpose

Practice T41 resilience by deleting key material, proving login fails, then restoring key auth from a reproducible playbook.

### Playbook (`/root/rhcsa_journal/lab-39c/task2-restore.yml`)

```yaml
---
- name: "Lab 39c Task 2 - restore SSH key auth"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true

  vars:
    lab_user: labuser_39_sshkey
    lab_group: labgrp_39_sshkey
    lab_home: "/tmp/lab39c/home_labuser_39_sshkey"
    lab_key: "{{ lab_home }}/.ssh/lab39_verify_ed25519"

  tasks:
    - name: "Ensure .ssh exists with 700"
      ansible.builtin.file:
        path: "{{ lab_home }}/.ssh"
        state: directory
        owner: "{{ lab_user }}"
        group: "{{ lab_group }}"
        mode: "0700"

    - name: "Generate replacement keypair"
      ansible.builtin.user:
        name: "{{ lab_user }}"
        generate_ssh_key: true
        ssh_key_type: ed25519
        ssh_key_file: "{{ lab_key }}"

    - name: "Read restored public key"
      ansible.builtin.slurp:
        src: "{{ lab_key }}.pub"
      register: restored_pubkey

    - name: "Install restored authorized key"
      ansible.posix.authorized_key:
        user: "{{ lab_user }}"
        key: "{{ restored_pubkey.content | b64decode | trim }}"
        state: present
        path: "{{ lab_home }}/.ssh/authorized_keys"
        manage_dir: false

    - name: "Enforce strict file permissions"
      ansible.builtin.file:
        path: "{{ item.path }}"
        owner: "{{ lab_user }}"
        group: "{{ lab_group }}"
        mode: "{{ item.mode }}"
      loop:
        - { path: "{{ lab_key }}", mode: "0600" }
        - { path: "{{ lab_home }}/.ssh/authorized_keys", mode: "0600" }
```

### Main command block

```bash
TASKLOG=/tmp/lab39c/task2.txt

echo "═══ DESTROY phase ═══" | tee "${TASKLOG}"
rm -f "${USER_HOME}/.ssh/lab39_verify_ed25519" \
      "${USER_HOME}/.ssh/lab39_verify_ed25519.pub" \
      "${USER_HOME}/.ssh/authorized_keys"

sudo -u "${USER}" ssh -i "${USER_HOME}/.ssh/lab39_verify_ed25519" \
  -o PreferredAuthentications=publickey \
  -o PasswordAuthentication=no \
  "${USER}@localhost" true 2>&1 | tee -a "${TASKLOG}" || true

echo "═══ RESTORE phase ═══" | tee -a "${TASKLOG}"
ansible-playbook /root/rhcsa_journal/lab-39c/task2-restore.yml 2>&1 | tee -a "${TASKLOG}"

sudo -u "${USER}" ssh -i "${USER_HOME}/.ssh/lab39_verify_ed25519" \
  -o PreferredAuthentications=publickey \
  -o PasswordAuthentication=no \
  -o StrictHostKeyChecking=accept-new \
  "${USER}@localhost" true 2>&1 | tee -a "${TASKLOG}"

stat -c '%a %U:%G %n' "${USER_HOME}/.ssh" | tee -a "${TASKLOG}"
stat -c '%a %U:%G %n' "${USER_HOME}/.ssh/authorized_keys" | tee -a "${TASKLOG}"
echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Trap callout

- **T39-A:** restore must re-enforce `700`/`600` permissions, not only recreate files.
- **T39-B:** verify uses explicit `-i "${USER_HOME}/.ssh/lab39_verify_ed25519"` each run.

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-39c/task2
cp /tmp/lab39c/task2.txt "${JDIR}/destroy-restore.txt"
cp /root/rhcsa_journal/lab-39c/task2-restore.yml "${JDIR}/task2-restore.yml"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# Explicit key cleanup
rm -f "${USER_HOME}/.ssh/lab39_verify_ed25519" \
      "${USER_HOME}/.ssh/lab39_verify_ed25519.pub" \
      "${USER_HOME}/.ssh/authorized_keys"

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 39c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 39c Checklist

- [ ] Task 1 completed (account + perms audited, localhost key-auth verified)
- [ ] Task 2 completed (destroy-restore drill executed and key auth recovered)
- [ ] T39-A and T39-B controls validated after restore
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
