# Lab 08b: Copying Files and Directories (Ansible) — `ansible.builtin.copy`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `08a` (RHCSA) → **`08b` (Ansible)** → `08c` (Verify)
- **Prerequisite:** Lab 00 (Ansible control node) and Lab 08a
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2
- **Practice Directory (rotation #08):** `/etc/skel` (read-only source reference)
- **Sandbox:** `/tmp/cp-ansible-lab`
- **Traps rehearsed this lab:** **T08-C** (`src` resolution without `remote_src: true`) · **T08-A** (metadata drift without explicit preserve/mode) · **T08-B** (assuming recursion/archive semantics without checking module behavior)

> **This lab's practice directory is `/etc/skel`**. Source examples come from `/etc/skel`; writes go under `/tmp/cp-ansible-lab`.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /etc/skel"
echo "⚠️  TRAP REMINDERS THIS LAB: T08-A T08-B T08-C"
ansible --version | head -n 1
ansible -m ping localhost 2>&1 | tail -n 3
ls -la /etc/skel
```

---

## Objective

Use `ansible.builtin.copy` correctly with:

- `remote_src: true` for remote-local source resolution
- `mode:` and `owner:` for explicit DAC control
- `mode: preserve` to preserve source mode
- `backup: true` for safe overwrite history

---

## Setup (run once)

```bash
sudo mkdir -p /tmp/cp-ansible-lab/src /tmp/cp-ansible-lab/dst
sudo cp -a /etc/skel/. /tmp/cp-ansible-lab/src/
echo "ansible-copy-lab" | sudo tee /tmp/cp-ansible-lab/src/input.txt >/dev/null
sudo chmod 640 /tmp/cp-ansible-lab/src/input.txt
sudo mkdir -p /root/rhcsa_journal/lab-08b/playbooks
```

---

## Task 1 — `remote_src`, `mode`, and `owner`

**Practice directory this task:** `/etc/skel` (read), `/tmp/cp-ansible-lab` (write)

### Purpose

Copy a file using `ansible.builtin.copy` with explicit ownership and mode, and avoid `T08-C` by setting `remote_src: true`.

### Playbook

```yaml
---
- name: Lab 08b task1 copy with explicit DAC
  hosts: localhost
  connection: local
  become: true
  gather_facts: false
  tasks:
    - name: Ensure destination directory exists
      ansible.builtin.file:
        path: /tmp/cp-ansible-lab/dst
        state: directory
        mode: "0755"

    - name: Copy input file from remote source
      ansible.builtin.copy:
        src: /tmp/cp-ansible-lab/src/input.txt
        dest: /tmp/cp-ansible-lab/dst/input.txt
        remote_src: true
        owner: root
        group: root
        mode: "0640"
      register: copy_result

    - name: Show task result
      ansible.builtin.debug:
        msg: "changed={{ copy_result.changed }} dest={{ copy_result.dest }}"
```

### Run Block

```bash
sudo tee /root/rhcsa_journal/lab-08b/playbooks/task1.yml >/dev/null <<'EOF'
---
- name: Lab 08b task1 copy with explicit DAC
  hosts: localhost
  connection: local
  become: true
  gather_facts: false
  tasks:
    - name: Ensure destination directory exists
      ansible.builtin.file:
        path: /tmp/cp-ansible-lab/dst
        state: directory
        mode: "0755"

    - name: Copy input file from remote source
      ansible.builtin.copy:
        src: /tmp/cp-ansible-lab/src/input.txt
        dest: /tmp/cp-ansible-lab/dst/input.txt
        remote_src: true
        owner: root
        group: root
        mode: "0640"
      register: copy_result

    - name: Show task result
      ansible.builtin.debug:
        msg: "changed={{ copy_result.changed }} dest={{ copy_result.dest }}"
EOF

ansible-playbook /root/rhcsa_journal/lab-08b/playbooks/task1.yml
stat -c 'mode=%a owner=%U:%G' /tmp/cp-ansible-lab/dst/input.txt
```

### Journal Write

```bash
sudo mkdir -p /root/rhcsa_journal/lab-08b/task1
{
  echo "lab=08b task=1"
  echo "when=$(date -Is)"
  stat -c 'dst_mode=%a dst_owner=%U:%G' /tmp/cp-ansible-lab/dst/input.txt
} | sudo tee /root/rhcsa_journal/lab-08b/task1/done.txt
```

---

## Task 2 — `mode: preserve`, `backup: true`, idempotence

**Practice directory this task:** `/etc/skel` (read), `/tmp/cp-ansible-lab` (write)

### Purpose

Preserve source mode while copying and keep backups on overwrite, then prove rerun idempotence.

### Playbook

```yaml
---
- name: Lab 08b task2 preserve and backup
  hosts: localhost
  connection: local
  become: true
  gather_facts: false
  tasks:
    - name: Seed destination with old content
      ansible.builtin.copy:
        content: "old-content"
        dest: /tmp/cp-ansible-lab/dst/preserved.txt
        owner: root
        group: root
        mode: "0600"

    - name: Copy with preserve mode and backup
      ansible.builtin.copy:
        src: /tmp/cp-ansible-lab/src/input.txt
        dest: /tmp/cp-ansible-lab/dst/preserved.txt
        remote_src: true
        mode: preserve
        owner: root
        group: root
        backup: true
      register: preserve_result

    - name: Show backup file
      ansible.builtin.debug:
        msg: "changed={{ preserve_result.changed }} backup={{ preserve_result.backup_file | default('none') }}"
```

### Run Block

```bash
sudo tee /root/rhcsa_journal/lab-08b/playbooks/task2.yml >/dev/null <<'EOF'
---
- name: Lab 08b task2 preserve and backup
  hosts: localhost
  connection: local
  become: true
  gather_facts: false
  tasks:
    - name: Seed destination with old content
      ansible.builtin.copy:
        content: "old-content"
        dest: /tmp/cp-ansible-lab/dst/preserved.txt
        owner: root
        group: root
        mode: "0600"

    - name: Copy with preserve mode and backup
      ansible.builtin.copy:
        src: /tmp/cp-ansible-lab/src/input.txt
        dest: /tmp/cp-ansible-lab/dst/preserved.txt
        remote_src: true
        mode: preserve
        owner: root
        group: root
        backup: true
      register: preserve_result

    - name: Show backup file
      ansible.builtin.debug:
        msg: "changed={{ preserve_result.changed }} backup={{ preserve_result.backup_file | default('none') }}"
EOF

ansible-playbook /root/rhcsa_journal/lab-08b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-08b/playbooks/task2.yml | tee /tmp/cp-ansible-lab/rerun.log
stat -c 'src_mode=%a dst_mode=%a' /tmp/cp-ansible-lab/src/input.txt /tmp/cp-ansible-lab/dst/preserved.txt
ls -1 /tmp/cp-ansible-lab/dst/preserved.txt*
```

### Trap Calls

- **T08-C:** Missing `remote_src: true` breaks source resolution model.
- **T08-A:** If you skip preserve/explicit mode, permissions drift.
- **T08-B:** Do not assume module recursion/archive semantics without validating state.

### Journal Write

```bash
sudo mkdir -p /root/rhcsa_journal/lab-08b/task2
{
  echo "lab=08b task=2"
  echo "when=$(date -Is)"
  grep -E 'changed=[0-9]+' /tmp/cp-ansible-lab/rerun.log | tail -n 1
  stat -c 'src_mode=%a dst_mode=%a' /tmp/cp-ansible-lab/src/input.txt /tmp/cp-ansible-lab/dst/preserved.txt
} | sudo tee /root/rhcsa_journal/lab-08b/task2/done.txt
```

---

## Lab 08b Checklist

- [ ] Task 1: used `remote_src`, explicit `mode`, and explicit `owner`
- [ ] Task 2: used `mode: preserve`, `backup: true`, and rerun idempotence check

---

## Related Labs

- `08a` — RHCSA command-line copy behaviors
- `08c` — verification capstone for metadata and content fidelity
