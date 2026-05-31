# Lab 24b: Stream Editing with `sed` Concepts in Ansible — `replace` + `lineinfile`

- **Series:** linux-ops-mastery — Text Processing & Validation
- **Trilogy:** [`24a`](../lab-24a-sed-stream-editor-rhcsa/) (RHCSA hand-typed) → **`24b`** (Ansible — you are here) → [`24c`](../lab-24c-sed-stream-editor-verify/) (Verify)
- **Prerequisite:** Lab 24a complete
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = `ansible.builtin.replace` as idempotent `sed s///g` equivalent; Task 2 = `ansible.builtin.lineinfile` with backrefs)
- **Practice Directory (rotation #24):** `/var` (reference context), writes in `/tmp/lab24b`
- **Sandbox (Tier B):** `/tmp/lab24b` with `USER=labuser_24_sed`, `GROUP=labgrp_24_sed`, `USER_HOME=/tmp/lab24b/home_labuser_24_sed`
- **Playbooks:** `/root/rhcsa_journal/lab-24b/playbooks`
- **Traps rehearsed this lab:** **T24-A** (unsafe in-place edits), **T24-B** (single replacement per line), **T41** (skip rebuild checks), **T44** (forget teardown)

> **This lab's practice directory is: `/var`** — we keep the same topic context, but Ansible writes only in Tier B sandbox paths.

---

## LAB HEADER BLOCK

```bash
echo "--- controller ---"
ansible --version | head -n 2
ansible localhost -m ping --connection=local 2>/dev/null | head -n 3
echo ""
echo "--- context ---"
ls -ld /var /tmp
echo "TRAPS: T24-A T24-B T41 T44"
echo "exit was: $?"
```

> **STOP — paste header output before setup.**

---

## Objective

Translate core `sed` workflows into idempotent Ansible primitives:

1. Replace repeated tokens across a file with `ansible.builtin.replace` (safe equivalent to `sed -i 's/old/new/g'`).
2. Replace one structured line with `ansible.builtin.lineinfile` using regex backrefs.
3. Validate idempotence with a second playbook run (`changed=0` target behavior).

---

## Concept: imperative stream edit vs declarative state

- `sed -i` says **how** to mutate text now.
- `replace` and `lineinfile` say **what** end-state must exist.
- Re-running playbooks should converge cleanly (no repeated damage, no duplicate lines).

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export LAB_NUM=24
export LAB_SLUG=sed
export SANDBOX=/tmp/lab24b
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-24b/playbooks
mkdir -p /root/rhcsa_journal/lab-24b/task1
mkdir -p /root/rhcsa_journal/lab-24b/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
echo "exit was: $?"
```

---

## Task 1 — `ansible.builtin.replace` (idempotent `sed s/old/new/g` equivalent)

**Practice directory this task:** `/tmp/lab24b`

### Warm-Up

```bash
cat > /tmp/lab24b/service.conf <<'EOF'
name=old-worker
owner=old-team
path=/var/old/cache old old
EOF
cat /tmp/lab24b/service.conf
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab24b/task1.txt
PB=/root/rhcsa_journal/lab-24b/playbooks/task1.yml

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 24b Task 1 — replace old -> new globally"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Ensure fixture exists
      ansible.builtin.copy:
        dest: /tmp/lab24b/service.conf
        mode: '0644'
        content: |
          name=old-worker
          owner=old-team
          path=/var/old/cache old old

    - name: Replace every old token
      ansible.builtin.replace:
        path: /tmp/lab24b/service.conf
        regexp: 'old'
        replace: 'new'

    - name: Show file after replacement
      ansible.builtin.command: cat /tmp/lab24b/service.conf
      register: out_file
      changed_when: false

    - name: Print result
      ansible.builtin.debug:
        var: out_file.stdout_lines
PLAYBOOK

ansible-playbook "${PB}" 2>&1 | tee "${TASKLOG}"
echo "--- second run idempotence check ---" | tee -a "${TASKLOG}"
ansible-playbook "${PB}" 2>&1 | tee -a "${TASKLOG}"
echo "--- resulting file ---" | tee -a "${TASKLOG}"
cat /tmp/lab24b/service.conf | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Notes

- `replace` catches all regex matches in file content, preventing **T24-B** drift from single-first replacement.
- Playbook re-run should converge; repeated runs should not re-corrupt content.

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-24b/task1
mkdir -p "${JDIR}"
cp /tmp/lab24b/task1.txt "${JDIR}/evidence.txt"
cp /tmp/lab24b/service.conf "${JDIR}/service.conf.after"
ls -la "${JDIR}"
echo "exit was: $?"
```

---

## Task 2 — `ansible.builtin.lineinfile` single-line replace with backrefs

**Practice directory this task:** `/tmp/lab24b`

### Warm-Up

```bash
cat > /tmp/lab24b/app.env <<'EOF'
APP_MODE=legacy
APP_PORT=8080
APP_OWNER=old-team
EOF
cat /tmp/lab24b/app.env
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab24b/task2.txt
PB=/root/rhcsa_journal/lab-24b/playbooks/task2.yml

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 24b Task 2 — lineinfile backrefs"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Ensure env file exists
      ansible.builtin.copy:
        dest: /tmp/lab24b/app.env
        mode: '0644'
        content: |
          APP_MODE=legacy
          APP_PORT=8080
          APP_OWNER=old-team

    - name: Replace owner line with backrefs
      ansible.builtin.lineinfile:
        path: /tmp/lab24b/app.env
        regexp: '^(APP_OWNER=)(.*)$'
        line: '\1new-team'
        backrefs: true

    - name: Verify app.env content
      ansible.builtin.command: cat /tmp/lab24b/app.env
      register: env_out
      changed_when: false

    - name: Print env content
      ansible.builtin.debug:
        var: env_out.stdout_lines
PLAYBOOK

ansible-playbook "${PB}" 2>&1 | tee "${TASKLOG}"
echo "--- second run idempotence check ---" | tee -a "${TASKLOG}"
ansible-playbook "${PB}" 2>&1 | tee -a "${TASKLOG}"
cat /tmp/lab24b/app.env | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-24b/task2
mkdir -p "${JDIR}"
cp /tmp/lab24b/task2.txt "${JDIR}/evidence.txt"
cp /tmp/lab24b/app.env "${JDIR}/app.env.after"
ls -la "${JDIR}"
echo "exit was: $?"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group  "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi

rm -rf "${SANDBOX}"

echo "── Lab 24b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"   || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"  || echo "✅ group gone"
test -d "${SANDBOX}"               && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"             && echo "❌ home remains"    || echo "✅ home gone"

set -e
echo "Cleanup complete at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the four `✅` audit lines.**

---

## Lab 24b Checklist (2 tasks + closeout)

- [ ] Task 1: `ansible.builtin.replace` replaced old→new; second run showed idempotent behavior
- [ ] Task 2: `ansible.builtin.lineinfile` backrefs updated one target line
- [ ] Traps rehearsed: T24-A/T24-B context verbalized, T41/T44 called out in lifecycle
- [ ] Section 6 closeout completed with four `✅` audit lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
