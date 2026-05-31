# Lab 39b: Configure SSH Key-Based Authentication with Ansible (Module-First)

- **Series:** linux-ops-mastery — SSH Access and Authentication
- **Trilogy:** `39a` (RHCSA) -> `39b` (Ansible) -> `39c` (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation #39):** `/lib64`
- **Sandbox (Tier B):** `/tmp/lab39b` with `USER=labuser_39_sshkey`, `GROUP=labgrp_39_sshkey`
- **Playbooks live at:** `/root/rhcsa_journal/lab-39b/playbooks/`
- **Traps rehearsed this lab:** **T39-A** · **T39-B** · **T41** · **T44**

> **Prerequisite:** `sshd` must be active on localhost before key-auth tests.

---

## LAB HEADER BLOCK

```bash
echo "📦 OS: $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒 TIME: $(date -Is)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "📁 PRACTICE DIR: /lib64"
echo "⚠️ TRAPS: T39-A T39-B T41 T44"
ansible --version | head -n 2
ansible -m ping localhost | tail -n 4
systemctl is-active sshd 2>/dev/null || echo "sshd not active"
ls -ld /lib64
```

---

## Objective

1. Generate an SSH keypair declaratively with `ansible.builtin.user` (`generate_ssh_key: yes`).
2. Deploy the generated public key with `ansible.posix.authorized_key`.
3. Enforce strict file permissions to avoid T39-A (`.ssh` = `700`, `authorized_keys` = `600`).
4. Keep key selection explicit to avoid T39-B (never rely on unspecified defaults).

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab39b
export GROUP=labgrp_39_sshkey
export USER=labuser_39_sshkey
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-39b/playbooks
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Declarative key generation and key deployment

### Purpose

Use module-first Ansible flow to create the keypair for `labuser_39_sshkey` and install that exact key into `authorized_keys`.

### Playbook (`/root/rhcsa_journal/lab-39b/playbooks/task1.yml`)

```yaml
---
- name: "Lab 39b Task 1 - generate and deploy SSH key"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true

  vars:
    lab_user: labuser_39_sshkey
    lab_group: labgrp_39_sshkey
    lab_home: "/tmp/lab39b/home_labuser_39_sshkey"
    lab_key: "{{ lab_home }}/.ssh/lab39_ansible_ed25519"

  tasks:
    - name: "Ensure Tier B group exists"
      ansible.builtin.group:
        name: "{{ lab_group }}"
        state: present

    - name: "Ensure Tier B user exists"
      ansible.builtin.user:
        name: "{{ lab_user }}"
        group: "{{ lab_group }}"
        home: "{{ lab_home }}"
        shell: /bin/bash
        create_home: false
        state: present

    - name: "Ensure .ssh directory exists with strict permissions"
      ansible.builtin.file:
        path: "{{ lab_home }}/.ssh"
        state: directory
        owner: "{{ lab_user }}"
        group: "{{ lab_group }}"
        mode: "0700"

    - name: "Generate SSH keypair for lab user"
      ansible.builtin.user:
        name: "{{ lab_user }}"
        generate_ssh_key: true
        ssh_key_type: ed25519
        ssh_key_file: "{{ lab_key }}"

    - name: "Read generated public key"
      ansible.builtin.slurp:
        src: "{{ lab_key }}.pub"
      register: generated_pubkey

    - name: "Install generated key into authorized_keys"
      ansible.posix.authorized_key:
        user: "{{ lab_user }}"
        key: "{{ generated_pubkey.content | b64decode | trim }}"
        state: present
        path: "{{ lab_home }}/.ssh/authorized_keys"
        manage_dir: false
```

### Run and verify

```bash
ansible-playbook /root/rhcsa_journal/lab-39b/playbooks/task1.yml 2>&1 | tee /tmp/lab39b/task1-apply-1.txt
ansible-playbook /root/rhcsa_journal/lab-39b/playbooks/task1.yml 2>&1 | tee /tmp/lab39b/task1-apply-2.txt
```

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-39b/task1
cp /tmp/lab39b/task1-apply-1.txt /root/rhcsa_journal/lab-39b/task1/apply-1.txt
cp /tmp/lab39b/task1-apply-2.txt /root/rhcsa_journal/lab-39b/task1/apply-2.txt
```

---

## Task 2 — Trap guard for T39-A permissions + localhost auth check

### Purpose

Assert strict permissions and verify key login on localhost using the generated key.

### Playbook (`/root/rhcsa_journal/lab-39b/playbooks/task2.yml`)

```yaml
---
- name: "Lab 39b Task 2 - enforce T39-A guard and verify"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true

  vars:
    lab_user: labuser_39_sshkey
    lab_group: labgrp_39_sshkey
    lab_home: "/tmp/lab39b/home_labuser_39_sshkey"
    lab_key: "{{ lab_home }}/.ssh/lab39_ansible_ed25519"

  tasks:
    - name: "Enforce .ssh permission 700"
      ansible.builtin.file:
        path: "{{ lab_home }}/.ssh"
        state: directory
        owner: "{{ lab_user }}"
        group: "{{ lab_group }}"
        mode: "0700"

    - name: "Enforce private key permission 600"
      ansible.builtin.file:
        path: "{{ lab_key }}"
        owner: "{{ lab_user }}"
        group: "{{ lab_group }}"
        mode: "0600"

    - name: "Enforce authorized_keys permission 600"
      ansible.builtin.file:
        path: "{{ lab_home }}/.ssh/authorized_keys"
        owner: "{{ lab_user }}"
        group: "{{ lab_group }}"
        mode: "0600"

    - name: "Capture .ssh stat"
      ansible.builtin.stat:
        path: "{{ lab_home }}/.ssh"
      register: sshdir_stat

    - name: "Capture authorized_keys stat"
      ansible.builtin.stat:
        path: "{{ lab_home }}/.ssh/authorized_keys"
      register: authkeys_stat

    - name: "Assert trap-safe permissions"
      ansible.builtin.assert:
        that:
          - sshdir_stat.stat.mode == '0700'
          - authkeys_stat.stat.mode == '0600'
        fail_msg: "T39-A risk detected: wrong SSH permissions"
        success_msg: "T39-A avoided: SSH permissions are strict"
```

### Run and verify

```bash
ansible-playbook /root/rhcsa_journal/lab-39b/playbooks/task2.yml 2>&1 | tee /tmp/lab39b/task2-apply.txt
sudo -u "${USER}" ssh -i "${USER_HOME}/.ssh/lab39_ansible_ed25519" \
  -o PreferredAuthentications=publickey \
  -o PasswordAuthentication=no \
  -o StrictHostKeyChecking=accept-new \
  "${USER}@localhost" true 2>&1 | tee /tmp/lab39b/task2-ssh-test.txt
```

### Trap callout

- **T39-A:** mode drift on `.ssh` or `authorized_keys` breaks auth.
- **T39-B:** explicit `lab39_ansible_ed25519` avoids accidental default key confusion.

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-39b/task2
cp /tmp/lab39b/task2-apply.txt /root/rhcsa_journal/lab-39b/task2/apply.txt
cp /tmp/lab39b/task2-ssh-test.txt /root/rhcsa_journal/lab-39b/task2/ssh-test.txt
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# Delete generated keys before teardown
rm -f "${USER_HOME}/.ssh/lab39_ansible_ed25519" \
      "${USER_HOME}/.ssh/lab39_ansible_ed25519.pub" \
      "${USER_HOME}/.ssh/authorized_keys"

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 39b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 39b Checklist

- [ ] Task 1 completed (`ansible.builtin.user generate_ssh_key` + `ansible.posix.authorized_key`)
- [ ] Task 2 completed (T39-A permission assertions + localhost key auth test)
- [ ] T39-B key-selection risk explicitly mitigated with named key file
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
