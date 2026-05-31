# Lab 26b: Command Mode and Insert Mode in `vi` (Ansible) — Section 18 Boundary

- **Series:** linux-ops-mastery — Text File Management
- **Trilogy:** [`26a`](../lab-26a-vi-editor-rhcsa/) → **`26b`** (Ansible boundary) → [`26c`](../lab-26c-vi-editor-verify/)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = `replace` + `lineinfile` as declarative equivalent of interactive edits · Task 2 = trap proof that `command: vi file` fails without TTY and must be replaced with modules)
- **Practice Directory (rotation #26):** `/opt`
- **Sandbox (Tier B):** `/tmp/lab26b` with `USER=labuser_26_vi`, `GROUP=labgrp_26_vi`
- **Playbooks live at:** `/root/rhcsa_journal/lab-26b/playbooks/`
- **Traps rehearsed:** **T26-A** · **T26-B** · **T41** · **T44**

> **Section 18 boundary note:** there is no honest `vi` Ansible module.  
> The declarative substitutes are `ansible.builtin.replace`, `ansible.builtin.lineinfile`, and sometimes `ansible.builtin.blockinfile`.

---

## LAB HEADER BLOCK

```bash
echo "TIME: $(date -Is)"
echo "USER: $(whoami)@$(hostname)"
echo "PRACTICE DIR: /opt"
echo "BOUNDARY: no vi module; use replace/lineinfile/blockinfile"
ansible --version | head -n 2
ansible -m ping localhost | tail -n 4
ls -ld /opt
```

---

## Objective

Translate editor intent into idempotent automation:

1. Use `replace` for whole-file pattern substitution (`:%s/foo/bar/g` equivalent).
2. Use `lineinfile` for precise single-line insertion/replacement (insert/append intent).
3. Prove why interactive editor commands (`vi`) are invalid in non-TTY Ansible runs.

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export LAB_NUM=26
export LAB_SLUG=vi
export SANDBOX=/tmp/lab26b
export GROUP=labgrp_26_vi
export USER=labuser_26_vi
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-26b/playbooks
mkdir -p /root/rhcsa_journal/lab-26b/task1 /root/rhcsa_journal/lab-26b/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — `replace` + `lineinfile`: declarative `vi`

### Purpose

Perform the same intent as:

- `:%s/foo/bar/g`
- insert or append a line

but through repeatable idempotent playbooks.

### Fixture + playbook

```bash
cat > /tmp/lab26b/app.ini <<'EOF'
mode=old
owner=ops
path=/opt/app
EOF

cat > /root/rhcsa_journal/lab-26b/playbooks/task1.yml <<'PLAYBOOK'
---
- name: "Lab 26b Task 1 - declarative vi substitutes"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Equivalent to :%s/old/new/g"
      ansible.builtin.replace:
        path: /tmp/lab26b/app.ini
        regexp: 'old'
        replace: 'new'

    - name: "Equivalent to append/new line intent"
      ansible.builtin.lineinfile:
        path: /tmp/lab26b/app.ini
        insertafter: EOF
        line: "edited_by=ansible"

    - name: "Show final content"
      ansible.builtin.command: cat /tmp/lab26b/app.ini
      register: app_view
      changed_when: false

    - name: "Print final content"
      ansible.builtin.debug:
        var: app_view.stdout_lines
PLAYBOOK

ansible-playbook --check --diff /root/rhcsa_journal/lab-26b/playbooks/task1.yml 2>&1 | tee /tmp/lab26b/task1-check.txt
ansible-playbook /root/rhcsa_journal/lab-26b/playbooks/task1.yml                    2>&1 | tee /tmp/lab26b/task1-apply1.txt
ansible-playbook /root/rhcsa_journal/lab-26b/playbooks/task1.yml                    2>&1 | tee /tmp/lab26b/task1-apply2.txt
cat /tmp/lab26b/app.ini | tee /tmp/lab26b/task1.txt
echo "task1 exit: $?"
```

### Section 18 boundary card

| Need | Use in Ansible |
|---|---|
| `:%s/foo/bar/g` style replacement | `ansible.builtin.replace` |
| single-line set/ensure | `ansible.builtin.lineinfile` |
| multi-line managed stanza | `ansible.builtin.blockinfile` |
| interactive editor session | **Boundary** (not a valid Ansible module pattern) |

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-26b/task1
mkdir -p "${JDIR}"
cp /tmp/lab26b/task1*.txt "${JDIR}/" 2>/dev/null || true
cp /tmp/lab26b/app.ini "${JDIR}/"
cp /root/rhcsa_journal/lab-26b/playbooks/task1.yml "${JDIR}/"
echo "TASK1 COMPLETE $(date -Is)" > "${JDIR}/done.txt"
ls -la "${JDIR}"
```

---

## Task 2 — Trap: `command: vi file` fails (no TTY)

### Purpose

Prove the anti-pattern and correct it:

- bad: `ansible.builtin.command: vi file`
- good: `replace` / `lineinfile`

### Main command block

```bash
cat > /tmp/lab26b/trap.txt <<'EOF'
state=old
EOF

cat > /root/rhcsa_journal/lab-26b/playbooks/task2-bad.yml <<'PLAYBOOK'
---
- name: "Lab 26b Task 2 - BAD pattern"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: "Do not do this"
      ansible.builtin.command: vi /tmp/lab26b/trap.txt
PLAYBOOK

cat > /root/rhcsa_journal/lab-26b/playbooks/task2-good.yml <<'PLAYBOOK'
---
- name: "Lab 26b Task 2 - GOOD pattern"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: "Replace old->new declaratively"
      ansible.builtin.replace:
        path: /tmp/lab26b/trap.txt
        regexp: 'old'
        replace: 'new'

    - name: "Append audit line"
      ansible.builtin.lineinfile:
        path: /tmp/lab26b/trap.txt
        insertafter: EOF
        line: "edited_by=module_not_vi"
PLAYBOOK

ansible-playbook /root/rhcsa_journal/lab-26b/playbooks/task2-bad.yml  2>&1 | tee /tmp/lab26b/task2-bad.txt || true
ansible-playbook /root/rhcsa_journal/lab-26b/playbooks/task2-good.yml 2>&1 | tee /tmp/lab26b/task2-good1.txt
ansible-playbook /root/rhcsa_journal/lab-26b/playbooks/task2-good.yml 2>&1 | tee /tmp/lab26b/task2-good2.txt

cat /tmp/lab26b/trap.txt | tee /tmp/lab26b/task2.txt

# Tier B weave
sudo -u "${USER}" bash -c 'echo "verified-by-$(whoami)" > "'"${USER_HOME}"'/task2-asuser.txt"'
stat -c '%U:%G %a %n' "${USER_HOME}/task2-asuser.txt" | tee -a /tmp/lab26b/task2.txt
echo "task2 exit: $?"
```

### Trap callouts

- **T26-A:** even outside Ansible, `vi` command mode requires `Esc` discipline.
- **T26-B:** never use raw editor writes on `/etc/passwd`; use `vipw` in Lab 27.
- **Boundary:** no TTY in normal Ansible run means `vi` is non-viable.

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-26b/task2
mkdir -p "${JDIR}"
cp /tmp/lab26b/task2*.txt "${JDIR}/" 2>/dev/null || true
cp /tmp/lab26b/trap.txt "${JDIR}/"
cp /root/rhcsa_journal/lab-26b/playbooks/task2-bad.yml "${JDIR}/"
cp /root/rhcsa_journal/lab-26b/playbooks/task2-good.yml "${JDIR}/"
cp "${USER_HOME}/task2-asuser.txt" "${JDIR}/"
echo "TASK2 COMPLETE $(date -Is)" > "${JDIR}/done.txt"
ls -la "${JDIR}"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

rm -f /tmp/lab26b/task1*.txt /tmp/lab26b/task2*.txt
rm -f /tmp/lab26b/app.ini /tmp/lab26b/trap.txt
rm -f "${USER_HOME}/task2-asuser.txt"

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "---- lab-26b cleanup audit ----"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Lab 26b Checklist

- [ ] Task 1 completed (`replace` + `lineinfile` + second idempotent run)
- [ ] Task 2 completed (proof `command: vi file` is wrong without TTY; fixed with modules)
- [ ] Section 18 boundary explicitly documented
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
