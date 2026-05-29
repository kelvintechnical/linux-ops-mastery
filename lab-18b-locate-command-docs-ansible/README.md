# Lab 18b: Locate Command Documentation (Ansible) — `ansible.builtin.find`, `ansible.builtin.shell`, `assert`

- **Series:** linux-ops-mastery — Package Intelligence & Documentation
- **Trilogy:** [`18a`](../lab-18a-locate-command-docs-rhcsa/) (RHCSA hand-typed) → **`18b`** (Ansible mirror) → [`18c`](../lab-18c-locate-command-docs-verify/) (Verify capstone)
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = discover docs with `find` + `rpm -qd` in playbook · Task 2 = `register` + `assert` + `failed_when` trap check)
- **Practice Directory (rotation #18):** `/lib64` (reference context); primary docs tree `/usr/share/doc`
- **Playbooks:** `/root/rhcsa_journal/lab-18b/playbooks/`
- **Sandbox (Tier B):** `/tmp/lab18b` with `USER=labuser_18_doclocate`, `GROUP=labgrp_18_doclocate`, `USER_HOME=/tmp/lab18b/home_labuser_18_doclocate`
- **Traps rehearsed this lab:** **T18-A** (`rpm -qd` vs `rpm -ql`) · **T18-B** (broken naming pattern) · **T41** (restore drill deferred to 18c) · **T44** (closeout audit completeness)

> **Focus:** mirror 18a logic in automation while preserving docs-only intent and trap checks.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
ansible --version
ansible localhost -m ping --connection=local
echo "📁  PRACTICE DIR: /lib64"
ls -ld /lib64 /usr/share/doc
echo "⚠️  TRAP REMINDERS THIS LAB: T18-A T18-B T41 T44"
echo "🕒  TIME: $(date -Is)"
```

> **STOP — paste header output before setup.**

---

## Objective

1. Use `ansible.builtin.find` to discover grep-related docs files.
2. Use `ansible.builtin.shell` to execute `rpm -qf` + `rpm -qd` chain.
3. Capture outputs with `register`.
4. Enforce correctness with `assert` and explicit `failed_when` guards.

---

## Concept: Why `shell` + `assert` Here

- `rpm -qf /usr/bin/grep` produces package name dynamically.
- `rpm -qd` needs that package value.
- `register` stores both outputs and return codes.
- `assert` and `failed_when` make trap violations fail fast.

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=18
export LAB_SLUG=doclocate
export SANDBOX=/tmp/lab18b
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-18b/playbooks
mkdir -p /root/rhcsa_journal/lab-18b/task1
mkdir -p /root/rhcsa_journal/lab-18b/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /usr/share/doc /lib64
```

---

## Task 1 — `ansible.builtin.find` + `ansible.builtin.shell rpm -qd`

### Warm-Up

```bash
rpm -qf /usr/bin/grep
rpm -qf /usr/bin/grep | xargs rpm -qd | head -n 10
```

### Purpose

Automate the two manual discovery methods from 18a:

1. Filesystem discovery on `/usr/share/doc`.
2. RPM metadata discovery via package owner then docs list.

### Main command block

```bash
TASKLOG=/tmp/lab18b/task1.txt
PB=/root/rhcsa_journal/lab-18b/playbooks/task1.yml

cat > "${PB}" << 'PLAYBOOK'
---
- name: "Lab 18b Task 1 - locate command docs"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Find grep-related docs under /usr/share/doc"
      ansible.builtin.find:
        paths: /usr/share/doc
        recurse: true
        file_type: file
        patterns:
          - "*grep*"
      register: grep_docs

    - name: "Resolve package owning /usr/bin/grep"
      ansible.builtin.shell: "rpm -qf /usr/bin/grep"
      register: grep_pkg
      changed_when: false

    - name: "List docs from owning package using rpm -qd"
      ansible.builtin.shell: "rpm -qd {{ grep_pkg.stdout | trim }}"
      register: grep_pkg_docs
      changed_when: false

    - name: "Write evidence file"
      ansible.builtin.copy:
        dest: /tmp/lab18b/task1-output.txt
        mode: '0644'
        content: |
          package={{ grep_pkg.stdout | trim }}
          find_hits={{ grep_docs.matched | default(0) }}
          rpm_qd_lines={{ (grep_pkg_docs.stdout_lines | default([])) | length }}
PLAYBOOK

ansible-playbook "${PB}" 2>&1 | tee "${TASKLOG}"
cat /tmp/lab18b/task1-output.txt | tee -a "${TASKLOG}"
echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Concept Card

| Concept | What it does |
|---|---|
| `ansible.builtin.find` | Tree search equivalent of shell `find` |
| `register` | Captures stdout/stdout_lines/rc for later checks |
| `ansible.builtin.shell` | Required for RPM command chain |
| **🪤 T18-A** | Must call `rpm -qd` for docs-only listing |

### Journal write

```bash
LAB=lab-18b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab18b/task1.txt        "${JDIR}/evidence.txt"
cp /tmp/lab18b/task1-output.txt "${JDIR}/task1-output.txt"
```

---

## Task 2 — `register` + `assert` + `failed_when` contains_check trap

### Warm-Up

```bash
echo "contains_check trap prep"
test -s /tmp/lab18b/task1-output.txt && echo "task1 evidence present"
```

### Purpose

Turn trap requirements into hard checks:

- Validate docs list has at least one line.
- Validate `/usr/share/doc` find hits are not zero.
- Fail if expected "grep" signal is missing in docs output (`contains_check`).

### Main command block

```bash
TASKLOG=/tmp/lab18b/task2.txt
PB=/root/rhcsa_journal/lab-18b/playbooks/task2.yml

cat > "${PB}" << 'PLAYBOOK'
---
- name: "Lab 18b Task 2 - trap checks with assert"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Get package for /usr/bin/grep"
      ansible.builtin.shell: "rpm -qf /usr/bin/grep"
      register: grep_pkg
      changed_when: false

    - name: "Get docs-only listing"
      ansible.builtin.shell: "rpm -qd {{ grep_pkg.stdout | trim }}"
      register: docs_qd
      changed_when: false
      failed_when: docs_qd.rc != 0

    - name: "Find grep-related doc files"
      ansible.builtin.find:
        paths: /usr/share/doc
        recurse: true
        file_type: file
        patterns:
          - "*grep*"
      register: docs_find

    - name: "contains_check trap guard"
      ansible.builtin.set_fact:
        contains_check: "{{ (docs_qd.stdout is search('grep')) or ((docs_find.matched | default(0)) | int > 0) }}"

    - name: "Assert trap checks"
      ansible.builtin.assert:
        that:
          - (docs_qd.stdout_lines | default([])) | length > 0
          - (docs_find.matched | default(0)) | int > 0
          - contains_check | bool
        fail_msg: "T18 trap check failed: docs were not proven discoverable"
        success_msg: "✅ docs discovery assertions passed"

    - name: "Write verification evidence"
      ansible.builtin.copy:
        dest: /tmp/lab18b/task2-assertions.txt
        mode: '0644'
        content: |
          docs_qd_count={{ (docs_qd.stdout_lines | default([])) | length }}
          docs_find_count={{ docs_find.matched | default(0) }}
          contains_check={{ contains_check }}
PLAYBOOK

ansible-playbook "${PB}" 2>&1 | tee "${TASKLOG}"
cat /tmp/lab18b/task2-assertions.txt | tee -a "${TASKLOG}"
echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Concept Card

| Concept | What it does |
|---|---|
| `failed_when` | Force explicit failure condition on shell task |
| `assert` | Stops play when proof conditions are false |
| `contains_check` | Trap flag to prove discovery signal is present |
| **🪤 T18-B** | Broken pattern would make `docs_find.matched` too low/zero |

### Journal write

```bash
LAB=lab-18b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab18b/task2.txt            "${JDIR}/evidence.txt"
cp /tmp/lab18b/task2-assertions.txt "${JDIR}/task2-assertions.txt"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 18b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"   || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}"               && echo "❌ sandbox remains"|| echo "✅ sandbox gone"
test -d "${USER_HOME}"             && echo "❌ home remains"   || echo "✅ home gone"

set -e
```

---

## Lab 18b Checklist (2 tasks + closeout)

- [ ] Task 1 used `ansible.builtin.find` on `/usr/share/doc` and `ansible.builtin.shell` for `rpm -qd`
- [ ] Task 2 used `register`, `assert`, and `failed_when` with `contains_check`
- [ ] Trap signals for T18-A and T18-B were enforced by assertions
- [ ] Section 6 closeout ended with four `✅` audit lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
