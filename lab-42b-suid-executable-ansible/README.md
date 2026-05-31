# Lab 42b: SUID Executables with Ansible (Module-First)

- **Series:** linux-ops-mastery — Privilege, Permissions, and Security Posture
- **Trilogy:** `42a` (RHCSA) -> `42b` (Ansible) -> `42c` (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation slot 42):** `/boot`
- **Sandbox (Tier B):** `/tmp/lab42b` with `USER=labuser_42_suid`, `GROUP=labgrp_42_suid`
- **Playbooks live at:** `/root/rhcsa_journal/lab-42b/playbooks/`
- **Traps rehearsed this lab:** **T42-A** · **T42-B** · **T41** · **T44**

> **This lab's topic:** declare SUID state with Ansible and audit SUID binaries safely.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /boot"
echo "⚠️  TRAP REMINDERS THIS LAB: T42-A T42-B T41 T44"
ls -ld /boot
ansible --version | head -n 2
ansible -m ping localhost | tail -n 4
```

---

## Objective

1. Use `ansible.builtin.file` to declare SUID mode (`'4755'` or symbolic `u+s`) on a lab binary.
2. Use `ansible.builtin.find` to discover SUID binaries from constrained paths and patterns.
3. Keep SUID evidence temporary and remove SUID copies at closeout.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab42b
export GROUP=labgrp_42_suid
export USER=labuser_42_suid
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-42b/playbooks /root/rhcsa_journal/lab-42b/task1 /root/rhcsa_journal/lab-42b/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Declarative SUID with `ansible.builtin.file`

### Purpose

Create a lab-owned copy of `cat`, then set owner/group/mode declaratively in Ansible.

### Playbook (`/root/rhcsa_journal/lab-42b/playbooks/task1.yml`)

```yaml
---
- name: "Lab 42b Task 1 - declarative SUID mode"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Copy cat into sandbox as lab binary"
      ansible.builtin.copy:
        src: /usr/bin/cat
        remote_src: true
        dest: /tmp/lab42b/labcat
        mode: "0755"

    - name: "Set root ownership + SUID using octal mode"
      ansible.builtin.file:
        path: /tmp/lab42b/labcat
        owner: root
        group: root
        mode: "4755"

    - name: "Verify mode and owner"
      ansible.builtin.command:
        cmd: stat -c '%A %a %U:%G %n' /tmp/lab42b/labcat
      register: labcat_stat
      changed_when: false

    - name: "Show verification line"
      ansible.builtin.debug:
        var: labcat_stat.stdout
```

### Run and verify

```bash
ansible-playbook /root/rhcsa_journal/lab-42b/playbooks/task1.yml 2>&1 | tee /tmp/lab42b/task1.txt
ls -l /tmp/lab42b/labcat | tee -a /tmp/lab42b/task1.txt
sudo -u "${USER}" /tmp/lab42b/labcat /etc/shadow | head -n 2 | tee -a /tmp/lab42b/task1.txt
```

### Journal write

```bash
cp /tmp/lab42b/task1.txt /root/rhcsa_journal/lab-42b/task1/evidence.txt
cp /root/rhcsa_journal/lab-42b/playbooks/task1.yml /root/rhcsa_journal/lab-42b/task1/task1.yml
```

---

## Task 2 — Discover SUID binaries with `ansible.builtin.find`

### Purpose

Collect SUID inventory quickly without scanning the entire filesystem blindly.

### Playbook (`/root/rhcsa_journal/lab-42b/playbooks/task2.yml`)

```yaml
---
- name: "Lab 42b Task 2 - discover SUID binaries"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Find SUID files in core binary paths"
      ansible.builtin.find:
        paths:
          - /usr/bin
          - /usr/sbin
          - /tmp/lab42b
        recurse: true
        file_type: file
        patterns:
          - "*"
        mode: "4000"
      register: suid_find

    - name: "Write concise SUID report"
      ansible.builtin.copy:
        dest: /tmp/lab42b/suid-find.txt
        mode: "0644"
        content: |
          suid_count={{ suid_find.files | length }}
          first_five={{ (suid_find.files | map(attribute='path') | list)[:5] }}

    - name: "Show report file path"
      ansible.builtin.debug:
        msg: "/tmp/lab42b/suid-find.txt"
```

### Run and verify

```bash
ansible-playbook /root/rhcsa_journal/lab-42b/playbooks/task2.yml 2>&1 | tee /tmp/lab42b/task2.txt
cat /tmp/lab42b/suid-find.txt | tee -a /tmp/lab42b/task2.txt
```

### Trap callout

- **T42-A:** `rwSr-xr-x` means SUID present but owner execute missing; fix with `chmod u+x`.
- **T42-B:** applying SUID to scripts is not a valid privilege path; only binaries honor SUID semantics on Linux.

### Journal write

```bash
cp /tmp/lab42b/task2.txt /root/rhcsa_journal/lab-42b/task2/evidence.txt
cp /tmp/lab42b/suid-find.txt /root/rhcsa_journal/lab-42b/task2/suid-find.txt
cp /root/rhcsa_journal/lab-42b/playbooks/task2.yml /root/rhcsa_journal/lab-42b/task2/task2.yml
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# Mandatory SUID cleanup first (security)
chmod 0755 /tmp/lab42b/labcat 2>/dev/null
rm -f /tmp/lab42b/labcat /tmp/lab42b/suid-find.txt /tmp/lab42b/task1.txt /tmp/lab42b/task2.txt

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 42b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -e /tmp/lab42b/labcat && echo "❌ suid labcat remains" || echo "✅ suid labcat gone"

set -e
```

---

## Lab 42b Checklist

- [ ] Task 1 completed (`ansible.builtin.file` set `mode: "4755"` on lab binary)
- [ ] Task 2 completed (`ansible.builtin.find` returned SUID inventory)
- [ ] T42-A and T42-B trap behavior explained in evidence
- [ ] All temporary SUID artifacts removed
- [ ] Section 6 closeout ended with `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
