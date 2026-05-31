# Lab 30b: Navigating `info` Pages with Ansible (Module-First)

- **Series:** linux-ops-mastery — Documentation Navigation and Discovery
- **Trilogy:** `30a` (RHCSA) -> `30b` (Ansible) -> `30c` (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation #30):** `/sys` (orientation only)
- **Sandbox (Tier B):** `/tmp/lab30b` with `USER=labuser_30_info`, `GROUP=labgrp_30_info`
- **Playbooks live at:** `/root/rhcsa_journal/lab-30b/playbooks/`
- **Traps rehearsed this lab:** **T30-A** · **T30-B** · **T41** · **T44**

> **Section 18 boundary note (explicit):** interactive key navigation (`n`, `p`, `u`, `/`, `q`) is a TTY behavior boundary and has no honest Ansible module abstraction. This b-lab is intentionally kept for trap practice: we automate package and file-state checks, and we document key navigation behavior instead of pretending to test keystrokes.

---

## LAB HEADER BLOCK

```bash
echo "📦 OS: $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒 TIME: $(date -Is)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "📁 PRACTICE DIR: /sys"
echo "⚠️ TRAPS: T30-A T30-B T41 T44"
ansible --version | head -n 2
ansible -m ping localhost | tail -n 4
ls -ld /sys /usr/share/info 2>/dev/null || true
```

---

## Objective

Translate info-page readiness and evidence capture into idempotent Ansible:

1. Install `info` package with `ansible.builtin.dnf`.
2. Assert `/usr/share/info` has entries so docs are actually present.
3. Rehearse T30-B by failing the run if expected info pages are absent.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab30b
export GROUP=labgrp_30_info
export USER=labuser_30_info
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-30b/playbooks
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Install `info` and assert `/usr/share/info` content

### Purpose

Use module-first package management and proof checks:

- `ansible.builtin.dnf` installs `info`.
- `ansible.builtin.find` and `ansible.builtin.assert` prove doc files exist.

### Playbook (`/root/rhcsa_journal/lab-30b/playbooks/task1.yml`)

```yaml
---
- name: "Lab 30b Task 1 - install info package and verify docs tree"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Install info package"
      ansible.builtin.dnf:
        name: info
        state: present

    - name: "Collect files under /usr/share/info"
      ansible.builtin.find:
        paths: /usr/share/info
        file_type: file
      register: info_tree

    - name: "Assert info docs are present"
      ansible.builtin.assert:
        that:
          - info_tree.matched | int > 0
        fail_msg: "No info pages found in /usr/share/info"
        success_msg: "Info pages found under /usr/share/info"

    - name: "Export ls invocation non-interactive evidence"
      ansible.builtin.command:
        cmd: info coreutils 'ls invocation' -o /tmp/lab30b/ls.txt
      changed_when: false
```

### Run and verify

```bash
ansible-playbook /root/rhcsa_journal/lab-30b/playbooks/task1.yml 2>&1 | tee /tmp/lab30b/task1-apply-1.txt
ansible-playbook /root/rhcsa_journal/lab-30b/playbooks/task1.yml 2>&1 | tee /tmp/lab30b/task1-apply-2.txt
ls -la /usr/share/info | tee /tmp/lab30b/task1-ls.txt
cat /tmp/lab30b/ls.txt | tee -a /tmp/lab30b/task1-ls.txt
```

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-30b/task1
cp /tmp/lab30b/task1-apply-1.txt /root/rhcsa_journal/lab-30b/task1/apply-1.txt
cp /tmp/lab30b/task1-apply-2.txt /root/rhcsa_journal/lab-30b/task1/apply-2.txt
cp /tmp/lab30b/task1-ls.txt /root/rhcsa_journal/lab-30b/task1/verify.txt
cp /tmp/lab30b/ls.txt /root/rhcsa_journal/lab-30b/task1/ls.txt
```

---

## Task 2 — Trap T30-B: fail when info pages are not installed

### Purpose

Practice explicit failure behavior instead of silent pass:

- If `info` package is absent or `/usr/share/info` has zero files, playbook must fail.
- `failed_when` is used on a count command to force visibility.

### Playbook (`/root/rhcsa_journal/lab-30b/playbooks/task2.yml`)

```yaml
---
- name: "Lab 30b Task 2 - T30-B trap guard"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Count installed info pages"
      ansible.builtin.shell: "ls -1 /usr/share/info 2>/dev/null | wc -l"
      register: info_count
      changed_when: false
      failed_when: (info_count.stdout | int) == 0

    - name: "Show trap guard result"
      ansible.builtin.debug:
        msg:
          - "info_page_count={{ info_count.stdout | trim }}"
          - "T30-B status=avoided when count > 0"
```

### Run and inspect

```bash
ansible-playbook /root/rhcsa_journal/lab-30b/playbooks/task2.yml 2>&1 | tee /tmp/lab30b/task2-apply.txt
grep -E "FAILED|info_page_count|PLAY RECAP" /tmp/lab30b/task2-apply.txt
```

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-30b/task2
cp /tmp/lab30b/task2-apply.txt /root/rhcsa_journal/lab-30b/task2/evidence.txt
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 30b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 30b Checklist

- [ ] Task 1 completed (Ansible `dnf` install + assertion on `/usr/share/info` content)
- [ ] Task 2 completed (T30-B `failed_when` guard for zero info pages)
- [ ] Section 18 boundary note documented explicitly (TTY key nav not module-testable; b-lab kept for trap practice)
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
