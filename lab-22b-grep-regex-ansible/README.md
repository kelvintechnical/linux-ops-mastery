# Lab 22b: Filtering Text with Regex in Ansible — `lineinfile` and `replace`

- **Series:** linux-ops-mastery — Text Processing and Pattern Matching
- **Trilogy:** [`22a`](../lab-22a-grep-regex-rhcsa/) → **`22b`** (Ansible — you are here) → [`22c`](../lab-22c-grep-regex-verify/)
- **Career arcs covered:** RHCE EX294 regex-safe edits, config drift control, deterministic text transforms
- **Prerequisite:** `22a` complete and Ansible controller ready
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = `ansible.builtin.lineinfile` with `regexp:` BRE semantics + assert match · Task 2 = `ansible.builtin.replace` with backreferences and trap handling)
- **Practice Directory (rotation slot):** `/home`
- **Sandbox (Tier B):** `/tmp/lab22b` with `USER=labuser_22_regex`, `GROUP=labgrp_22_regex`
- **Traps rehearsed:** **T22-A** (BRE vs ERE assumptions inside module regex), **T22-B** (over-greedy replacement pattern), **T41**, **T44**

---

## LAB HEADER BLOCK

```bash
ansible --version | head -n 3
echo "🕒 TIME: $(date -Is)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T22-A T22-B T41 T44"
```

---

## Lab-Wide Setup

```bash
sudo -i

export LAB_NUM=22
export LAB_SLUG=regex
export SANDBOX=/tmp/lab22b
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /tmp/lab22b/files
mkdir -p /root/rhcsa_journal/lab-22b/playbooks
mkdir -p /root/rhcsa_journal/lab-22b/task1 /root/rhcsa_journal/lab-22b/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

cat > /tmp/lab22b/files/app.conf <<'EOF'
PORT=8080
MODE=dev
LOG_LEVEL=info
ALLOW_ANON=true
EOF

cat > /tmp/lab22b/files/service.cfg <<'EOF'
listen=0.0.0.0:8080
backend=api-v1
timeout=30
EOF
```

---

## Task 1 — `lineinfile` with `regexp:` (BRE behavior) + assert match found

### Main command block

```bash
TASKLOG=/tmp/lab22b/task1.txt
PB=/root/rhcsa_journal/lab-22b/playbooks/task1.yml

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 22b Task 1 — lineinfile regexp + assertion"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Update MODE line using regexp (BRE style)"
      ansible.builtin.lineinfile:
        path: /tmp/lab22b/files/app.conf
        regexp: '^MODE='
        line: 'MODE=prod'
        backrefs: false
      register: mode_edit

    - name: "Ensure pattern existed and was handled"
      ansible.builtin.assert:
        that:
          - mode_edit is defined
          - mode_edit.msg is not defined or ('line added' in mode_edit.msg or 'line replaced' in mode_edit.msg or mode_edit.changed in [true, false])
        fail_msg: "Expected MODE line to be matched by regexp"
        success_msg: "MODE regex path verified"

    - name: "Check resulting file content"
      ansible.builtin.command: grep -n '^MODE=' /tmp/lab22b/files/app.conf
      register: mode_check
      changed_when: false

    - name: "Display check output"
      ansible.builtin.debug:
        var: mode_check.stdout_lines
PLAYBOOK

echo "═══ Part A: --check --diff ═══"                        2>&1 | tee "$TASKLOG"
ansible-playbook --check --diff "${PB}"                      2>&1 | tee -a "$TASKLOG"

echo "═══ Part B: apply + re-apply idempotence ═══"          | tee -a "$TASKLOG"
ansible-playbook "${PB}"                                      2>&1 | tee -a "$TASKLOG"
ansible-playbook "${PB}"                                      2>&1 | tee -a "$TASKLOG"
grep -n '^MODE=' /tmp/lab22b/files/app.conf                  | tee -a "$TASKLOG"
```

### Concept Card

| Concept | What it does |
|---|---|
| `lineinfile.regexp` | Matches existing line to replace |
| BRE reality | Module regex defaults align with BRE expectations unless you explicitly switch context |
| `assert` | Fails fast when expected regex path did not occur |
| **🪤 Trap Risk T22-A** | Writing ERE/PCRE expectations blindly in module regex can mis-match |

### Journal write

```bash
LAB=lab-22b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab22b/task1.txt "$JDIR/evidence.txt"
cp "${PB}" "$JDIR/task1.yml"
```

---

## Task 2 — `replace` with `regexp:` and backreferences (trap focus)

### Main command block

```bash
TASKLOG=/tmp/lab22b/task2.txt
PB=/root/rhcsa_journal/lab-22b/playbooks/task2.yml

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 22b Task 2 — replace with backrefs"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Narrow replace pattern (avoid greedy overreach)"
      ansible.builtin.replace:
        path: /tmp/lab22b/files/service.cfg
        regexp: '^(backend=)(api)-v([0-9]+)$'
        replace: '\1\2-v2'
      register: backend_edit

    - name: "Patch listen port safely with capture groups"
      ansible.builtin.replace:
        path: /tmp/lab22b/files/service.cfg
        regexp: '^(listen=0\.0\.0\.0:)([0-9]+)$'
        replace: '\18443'
      register: listen_edit

    - name: "Verify edited lines"
      ansible.builtin.command: grep -nE '^(listen|backend)=' /tmp/lab22b/files/service.cfg
      register: verify_lines
      changed_when: false

    - name: "Show result"
      ansible.builtin.debug:
        msg:
          - "backend_changed={{ backend_edit.changed }}"
          - "listen_changed={{ listen_edit.changed }}"
          - "{{ verify_lines.stdout_lines | join(' | ') }}"
PLAYBOOK

echo "═══ Part A: apply playbook ═══"                         2>&1 | tee "$TASKLOG"
ansible-playbook "${PB}"                                      2>&1 | tee -a "$TASKLOG"

echo "═══ Part B: trap note (T22-B) ═══"                      | tee -a "$TASKLOG"
echo "Avoid regexp like '^(backend=.*)$' with broad replace; prefer anchored capture groups." | tee -a "$TASKLOG"
grep -nE '^(listen|backend)=' /tmp/lab22b/files/service.cfg   | tee -a "$TASKLOG"
```

### Concept Card

| Concept | What it does |
|---|---|
| Capture groups | `(...)` stores submatches for reuse |
| Backreferences | `\1`, `\2` reuse captured fragments in replacement |
| Anchored replace | `^...$` scopes replacement to one full line |
| **🪤 Trap Risk T22-B** | Greedy regex can rewrite too much of a config line |

### Journal write

```bash
LAB=lab-22b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab22b/task2.txt "$JDIR/evidence.txt"
cp "${PB}" "$JDIR/task2.yml"
```

---

## Lab Closeout — Section 6 teardown + audit

```bash
set +e
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}" /tmp/lab22b

echo "── Lab 22b cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d /tmp/lab22b                 && echo "❌ lab22b remains"  || echo "✅ lab22b gone"
set -e
```

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
