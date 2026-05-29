# Lab 20b: Scrolling Through Large Files via Ansible — non-interactive pager-safe patterns

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** [`20a`](../lab-20a-less-more-scrolling-rhcsa/) (RHCSA) → `20b` (Ansible) → [`20c`](../lab-20c-less-more-scrolling-verify/) (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = non-interactive evidence + pager defaults via `blockinfile`, Task 2 = T20-B trap handling)
- **Practice Directory (rotation #20):** `/etc`
- **Sandbox (Tier B):** `/tmp/lab20b` with `USER=labuser_20_pager`, `GROUP=labgrp_20_pager`
- **Traps rehearsed:** **T20-B** (interactive `less` in playbook hangs, ANSI/binary display issues) · **T41** · **T44**

> **Ansible reminder:** `less` is interactive. In playbooks, use non-interactive commands (`head`, `tail`, `awk`, `grep`) or bounded pager flags.

---

## LAB HEADER BLOCK

```bash
echo "ENV:  ${ENV:-DECLARE_ME}"
echo "TIME: $(date -Is)"
echo "USER: $(whoami)@$(hostname)"
echo "TRAPS THIS LAB: T20-B T41 T44"
echo "PRACTICE DIR: /etc"
ansible --version | head -n 2
ansible -m ping localhost 2>&1 | tail -n 3
```

---

## Objective

1. Apply pager-related defaults safely via Ansible-managed shell init.
2. Prove why interactive pagers are dangerous in automation and how to avoid playbook hangs.
3. Keep evidence artifacts for verify lab handoff.

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export LAB_NUM=20
export LAB_SLUG=pager
export SANDBOX=/tmp/lab20b
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-20b/task1 /root/rhcsa_journal/lab-20b/task2 /root/rhcsa_journal/lab-20b/playbooks
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
```

---

## Task 1 — Non-interactive file inspection + manage less defaults

### Purpose

Demonstrate the Ansible-safe alternative to interactive `less` and deploy profile defaults for human sessions.

### Playbook (`/root/rhcsa_journal/lab-20b/playbooks/task1.yml`)

```yaml
---
- name: "Lab 20b Task 1 — pager-safe inspection and defaults"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    profile_file: /etc/profile.d/lab20-less-defaults.sh
    target_file: /etc/services

  tasks:
    - name: "Collect top lines non-interactively"
      ansible.builtin.shell: "cat {{ target_file }} | head -n 20"
      register: top_lines
      changed_when: false

    - name: "Collect bottom lines non-interactively"
      ansible.builtin.shell: "tail -n 20 {{ target_file }}"
      register: bottom_lines
      changed_when: false

    - name: "Persist less defaults with marker block"
      ansible.builtin.blockinfile:
        path: "{{ profile_file }}"
        create: true
        owner: root
        group: root
        mode: '0644'
        marker: "# {mark} LAB 20 LESS DEFAULTS"
        block: |
          # safer pager defaults for long files
          alias less='less -N -S'
          export LESS='-N -S'
      register: less_defaults

    - name: "Restore SELinux context"
      ansible.builtin.command: "restorecon -v {{ profile_file }}"
      register: relabel
      changed_when: "'Relabeled' in relabel.stdout"

    - name: "Write evidence files"
      ansible.builtin.copy:
        dest: "/tmp/lab20b/task1-summary.txt"
        mode: '0644'
        content: |
          task: lab-20b task1
          profile_file: {{ profile_file }}
          top_lines_count: {{ top_lines.stdout_lines | length }}
          bottom_lines_count: {{ bottom_lines.stdout_lines | length }}
          defaults_changed: {{ less_defaults.changed }}
          relabel_changed: {{ relabel.changed }}
```

### Run + verify

```bash
mkdir -p /tmp/lab20b
ansible-playbook /root/rhcsa_journal/lab-20b/playbooks/task1.yml 2>&1 | tee /tmp/lab20b/task1.txt
ls -lZ /etc/profile.d/lab20-less-defaults.sh | tee -a /tmp/lab20b/task1.txt
cat /etc/profile.d/lab20-less-defaults.sh | tee -a /tmp/lab20b/task1.txt
cat /tmp/lab20b/task1-summary.txt | tee -a /tmp/lab20b/task1.txt
sudo -u "${USER}" bash -c "source /etc/profile.d/lab20-less-defaults.sh; alias less" | tee -a /tmp/lab20b/task1.txt
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-20b/task1
mkdir -p "${JDIR}"
cp /tmp/lab20b/task1.txt /tmp/lab20b/task1-summary.txt "${JDIR}/"
cp /etc/profile.d/lab20-less-defaults.sh "${JDIR}/lab20-less-defaults.sh"
echo "TASK1 COMPLETE $(date -Is)" > "${JDIR}/done.txt"
```

---

## Task 2 — Trap T20-B: avoid interactive pager hangs in playbooks

### Purpose

Show bad pattern and safe replacements:

- Bad: `less /etc/services` in `ansible.builtin.shell` can block waiting for TTY input.
- Better: non-interactive equivalents (`head`, `tail`, `awk`, `grep`) or bounded pager (`less -e -F` for quick exit when content fits one screen).

### Playbook (`/root/rhcsa_journal/lab-20b/playbooks/task2.yml`)

```yaml
---
- name: "Lab 20b Task 2 — trap-safe pager usage"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    ansi_file: /tmp/lab20b/ansi-demo.log

  tasks:
    - name: "Seed ANSI demo file"
      ansible.builtin.shell: |
        mkdir -p /tmp/lab20b
        printf '\033[31mERROR\033[0m line-one\nnormal line-two\n' > {{ ansi_file }}
      changed_when: true

    - name: "Document bad interactive pattern (do not execute)"
      ansible.builtin.copy:
        dest: /tmp/lab20b/task2-bad-pattern.txt
        mode: '0644'
        content: |
          BAD (hang risk): ansible.builtin.shell: less /etc/services
          WHY: less waits for interactive keystrokes.

    - name: "Safe non-interactive equivalent"
      ansible.builtin.shell: "awk 'NR<=5{print}' /etc/services"
      register: safe_preview
      changed_when: false

    - name: "Bounded pager mode (exits quickly)"
      ansible.builtin.shell: "less -e -F /etc/hosts"
      register: bounded_less
      changed_when: false

    - name: "ANSI-safe display guidance"
      ansible.builtin.copy:
        dest: /tmp/lab20b/task2-guidance.txt
        mode: '0644'
        content: |
          T20-B: If file has ANSI color escapes, use:
            less -R /tmp/lab20b/ansi-demo.log
          In automation, prefer:
            sed -r 's/\x1B\[[0-9;]*m//g' FILE | head

    - name: "Write task2 summary"
      ansible.builtin.copy:
        dest: /tmp/lab20b/task2-summary.txt
        mode: '0644'
        content: |
          safe_preview_lines: {{ safe_preview.stdout_lines | length }}
          bounded_less_rc: {{ bounded_less.rc }}
```

### Run + verify

```bash
ansible-playbook /root/rhcsa_journal/lab-20b/playbooks/task2.yml 2>&1 | tee /tmp/lab20b/task2.txt
cat /tmp/lab20b/task2-bad-pattern.txt | tee -a /tmp/lab20b/task2.txt
cat /tmp/lab20b/task2-guidance.txt | tee -a /tmp/lab20b/task2.txt
cat /tmp/lab20b/task2-summary.txt | tee -a /tmp/lab20b/task2.txt

sudo -u "${USER}" bash -c "awk 'NR<=3{print}' /etc/services > '${USER_HOME}/services-head.txt'"
stat -c '%U:%G %a %n' "${USER_HOME}/services-head.txt" | tee -a /tmp/lab20b/task2.txt
```

### Concept Card

| Pattern | Outcome |
|---|---|
| `shell: less FILE` | Hang risk in automation (interactive) |
| `shell: head/tail/awk FILE` | Safe non-interactive preview |
| `less -e -F FILE` | Pager exits at EOF / short files |
| `less -R FILE` | Preserves ANSI color escapes when viewing logs |
| **🪤 T20-B** | Interactive pager in playbook or unreadable ANSI output without `-R` |

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-20b/task2
mkdir -p "${JDIR}"
cp /tmp/lab20b/task2.txt /tmp/lab20b/task2-summary.txt /tmp/lab20b/task2-guidance.txt /tmp/lab20b/task2-bad-pattern.txt "${JDIR}/"
cp /root/rhcsa_journal/lab-20b/playbooks/task2.yml "${JDIR}/"
cp "${USER_HOME}/services-head.txt" "${JDIR}/services-head.txt"
echo "TASK2 COMPLETE $(date -Is)" > "${JDIR}/done.txt"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e
rm -f /tmp/lab20b/task1.txt /tmp/lab20b/task2.txt /tmp/lab20b/task1-summary.txt /tmp/lab20b/task2-summary.txt
rm -f /tmp/lab20b/task2-guidance.txt /tmp/lab20b/task2-bad-pattern.txt /tmp/lab20b/ansi-demo.log
rm -f "${USER_HOME}/services-head.txt"

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "---- lab-20b cleanup audit ----"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 20a** | Interactive `less`/`more` muscle memory |
| **Lab 20c** | Audit evidence + destroy-restore validation |

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
