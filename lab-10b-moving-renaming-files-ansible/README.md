# Lab 10b: Moving and Renaming Files via Ansible — Boundary patterns

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `10a` (RHCSA) → **`10b` (Ansible — you are here)** → `10c` (Verify)
- **Career arcs covered:** RHCE EX294 (idempotent command boundaries), SRE (safe file replacement), Platform (config rollout workflows)
- **Prerequisite:** Lab 10a complete, Lab 00 control node setup
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2
- **Practice Directory (rotation #10):** `/var`
- **Sandbox:** `/tmp/mv-ansible-lab`
- **Playbooks live at:** `/root/rhcsa_journal/lab-10b/playbooks/`
- **Boundary focus:** `command: mv` with `creates:` + `removes:` AND `ansible.builtin.copy` with `backup: true` for atomic replace
- **Traps rehearsed this lab:** **T10-A** (cross-fs move is not atomic rename) · **T10-B** (imperative mv can overwrite) · **T10-C** (using `command: mv` without guards is non-idempotent)

> **This lab's practice directory is: `/var`** — referenced in each task for context while writes happen in `/tmp/mv-ansible-lab`.

---

## LAB HEADER BLOCK — run this FIRST

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T10-A T10-B T10-C"
echo "📁  PRACTICE DIR: /var"
ansible --version | head -n 2
ansible -m ping localhost 2>&1 | tail -n 4
ls -ld /var /var/log
```

---

## Objective

Use the RHCE-safe boundary patterns:

1. **Move existing files** with `ansible.builtin.command: mv` guarded by `creates:` and `removes:`.
2. **Atomically replace config content** with `ansible.builtin.copy` and `backup: true`.

---

## Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i
mkdir -p /tmp/mv-ansible-lab/{src,dst}
mkdir -p /root/rhcsa_journal/lab-10b/playbooks
echo "log-data" > /tmp/mv-ansible-lab/src/app.log
echo "config-v0" > /tmp/mv-ansible-lab/dst/service.conf
ls -lR /tmp/mv-ansible-lab
```

---

## Task 1 — Boundary move with `command: mv` + `creates/removes`

**Practice directory this task:** `/var` and `/tmp/mv-ansible-lab`

### Warm-Up

```bash
ls -ld /var /var/log
ls -l /tmp/mv-ansible-lab/src /tmp/mv-ansible-lab/dst
test -f /root/rhcsa_journal/lab-10b/playbooks/task1.yml && echo "playbook present"
```

### Purpose

Run a guarded Ansible `mv` that is idempotent on rerun.

### Main command block

```bash
mkdir -p /tmp/mv-ansible-lab/task1
ansible-playbook --check --diff /root/rhcsa_journal/lab-10b/playbooks/task1.yml \
  2>&1 | tee /tmp/mv-ansible-lab/task1/check.txt

ansible-playbook /root/rhcsa_journal/lab-10b/playbooks/task1.yml \
  2>&1 | tee /tmp/mv-ansible-lab/task1/apply.txt

ansible-playbook /root/rhcsa_journal/lab-10b/playbooks/task1.yml \
  2>&1 | tee /tmp/mv-ansible-lab/task1/rerun.txt

grep -E "PLAY RECAP|changed=" /tmp/mv-ansible-lab/task1/rerun.txt
ls -l /tmp/mv-ansible-lab/src /tmp/mv-ansible-lab/dst
```

### Playbook (`task1.yml`)

```yaml
---
- name: "Lab 10b Task 1 — guarded mv boundary"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Move app.log to dst atomically on same fs (command boundary)"
      ansible.builtin.command:
        cmd: mv /tmp/mv-ansible-lab/src/app.log /tmp/mv-ansible-lab/dst/app.log
        creates: /tmp/mv-ansible-lab/dst/app.log
        removes: /tmp/mv-ansible-lab/src/app.log
      register: mv_result

    - name: "Show boundary result"
      ansible.builtin.debug:
        msg: "changed={{ mv_result.changed }} rc={{ mv_result.rc }}"
```

### Concept Card

| Concept | One-line |
|---|---|
| `command: mv` boundary | Use when no native mv module exists |
| `creates` + `removes` | Idempotence guard pair for command tasks |
| 🪤 T10-C | Missing guards causes non-idempotent behavior |

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-10b/task1
mkdir -p "$JDIR"
cp /tmp/mv-ansible-lab/task1/*.txt "$JDIR"/
```

---

## Task 2 — Atomic config replace with `copy` + backup

**Practice directory this task:** `/var` and `/tmp/mv-ansible-lab`

### Warm-Up

```bash
ls -lt /var/log 2>/dev/null | head -n 3
cat /tmp/mv-ansible-lab/dst/service.conf
test -f /root/rhcsa_journal/lab-10b/playbooks/task2.yml && echo "playbook present"
```

### Purpose

Replace config content atomically with a backup, then prove rerun idempotence.

### Main command block

```bash
mkdir -p /tmp/mv-ansible-lab/task2
ansible-playbook --check --diff /root/rhcsa_journal/lab-10b/playbooks/task2.yml \
  2>&1 | tee /tmp/mv-ansible-lab/task2/check.txt

ansible-playbook /root/rhcsa_journal/lab-10b/playbooks/task2.yml \
  2>&1 | tee /tmp/mv-ansible-lab/task2/apply.txt

ansible-playbook /root/rhcsa_journal/lab-10b/playbooks/task2.yml \
  2>&1 | tee /tmp/mv-ansible-lab/task2/rerun.txt

cat /tmp/mv-ansible-lab/dst/service.conf
ls /tmp/mv-ansible-lab/dst/service.conf*~
grep -E "PLAY RECAP|changed=" /tmp/mv-ansible-lab/task2/rerun.txt
```

### Playbook (`task2.yml`)

```yaml
---
- name: "Lab 10b Task 2 — atomic copy replace with backup"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Replace service.conf content atomically with backup"
      ansible.builtin.copy:
        content: "config-v1 (managed)\n"
        dest: /tmp/mv-ansible-lab/dst/service.conf
        owner: root
        group: root
        mode: '0644'
        backup: true
      register: copy_result

    - name: "Show copy result"
      ansible.builtin.debug:
        msg: "changed={{ copy_result.changed }} backup={{ copy_result.backup_file | default('n/a') }}"
```

### Concept Card

| Concept | One-line |
|---|---|
| `copy` atomic replace | Temp file + rename within destination fs |
| `backup: true` | Preserves previous content as timestamped file |
| 🪤 T10-B | Unprotected overwrite risk without backup/controls |
| 🪤 T10-A | Atomic rename guarantee depends on same filesystem |

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-10b/task2
mkdir -p "$JDIR"
cp /tmp/mv-ansible-lab/task2/*.txt "$JDIR"/
```

---

## Checklist

- [ ] Task 1 rerun shows `changed=0` with guarded `command: mv`
- [ ] Task 2 creates backup and rerun shows `changed=0`

---

## Related Labs

| Lab | Connection |
|---|---|
| `10a` | Hand-typed `mv` switch behavior and traps |
| `10c` | Verification of atomic/cross-fs behavior and hard-link outcomes |
