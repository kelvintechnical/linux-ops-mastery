# Lab 26c: Verifying `vi` Edits (Capstone) — Audit + Destroy-Restore

- **Series:** linux-ops-mastery — Text File Management
- **Trilogy:** [`26a`](../lab-26a-vi-editor-rhcsa/) → [`26b`](../lab-26b-vi-editor-ansible/) → **`26c`**
- **Time Estimate:** 20-30 minutes
- **Tasks:** 2 (Task 1 = audit 26a substitutions using backup-vs-current `diff` evidence · Task 2 = destroy-restore drill for reproducible recovery)
- **Practice Directory (rotation #26):** `/opt`
- **Sandbox (Tier B):** `/tmp/lab26c` with `USER=labuser_26_vi`, `GROUP=labgrp_26_vi`
- **Traps rehearsed:** **T26-A** · **T26-B** · **T41** · **T44**

---

## LAB HEADER BLOCK

```bash
echo "TIME: $(date -Is)"
echo "USER: $(whoami)@$(hostname)"
echo "PRACTICE DIR: /opt"
ls -ld /opt
ls -la /root/rhcsa_journal/lab-26a/ /root/rhcsa_journal/lab-26b/ 2>/dev/null || true
```

---

## Objective

Move into auditor mode:

1. Validate that 26a edits are exactly what was intended (backup vs edited).
2. Rehearse failure recovery by destroying sandbox artifacts and restoring from known-good commands/playbooks.

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export LAB_NUM=26
export LAB_SLUG=vi
export SANDBOX=/tmp/lab26c
export GROUP=labgrp_26_vi
export USER=labuser_26_vi
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-26c/task1 /root/rhcsa_journal/lab-26c/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Audit 26a edits via `diff` against backup

### Purpose

Confirm change intent from Lab 26a:

- original backup exists
- edited file exists
- diff shows only expected `old -> new` substitutions

### Main command block

```bash
TASKLOG=/tmp/lab26c/task1.txt
J26A=/root/rhcsa_journal/lab-26a/task1

echo "=== verify required artifacts ==="                | tee "${TASKLOG}"
for f in "${J26A}/app.conf" "${J26A}/app.conf.bak" "${J26A}/evidence.txt"; do
  test -s "$f" && echo "✅ $f" || echo "❌ $f missing"
done                                                   | tee -a "${TASKLOG}"

echo "=== diff backup vs edited ==="                   | tee -a "${TASKLOG}"
diff -u "${J26A}/app.conf.bak" "${J26A}/app.conf"     | tee -a "${TASKLOG}"

echo "=== grep verification ==="                       | tee -a "${TASKLOG}"
grep -n 'new' "${J26A}/app.conf"                      | tee -a "${TASKLOG}"
grep -n 'old' "${J26A}/app.conf"                      | tee -a "${TASKLOG}" || true

cat <<'EOF' | tee -a "${TASKLOG}"
Audit notes:
- T26-A control: check no literal ':wq' ended up in edited artifacts.
- T26-B control: no direct edits against /etc/passwd in 26a evidence.
EOF

echo "task1 exit: $?"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-26c/task1
mkdir -p "${JDIR}"
cp /tmp/lab26c/task1.txt "${JDIR}/evidence.txt"
echo "TASK1 COMPLETE $(date -Is)" > "${JDIR}/done.txt"
ls -la "${JDIR}"
```

---

## Task 2 — Destroy-restore drill (T41)

### Purpose

Deliberately remove working files and restore them using documented patterns:

- 26a non-interactive `vi -c` sequence
- 26b declarative Ansible module sequence

### Main command block

```bash
TASKLOG=/tmp/lab26c/task2.txt

echo "=== Part A: seed files ==="                                  | tee "${TASKLOG}"
mkdir -p /tmp/lab26c/restore
cat > /tmp/lab26c/restore/base.txt <<'EOF'
color=old
mode=old
EOF
cp -a /tmp/lab26c/restore/base.txt /tmp/lab26c/restore/base.txt.bak
ls -l /tmp/lab26c/restore | tee -a "${TASKLOG}"

echo "=== Part B: destroy ==="                                     | tee -a "${TASKLOG}"
rm -rf /tmp/lab26c/restore
test ! -d /tmp/lab26c/restore && echo "✅ destroyed" || echo "❌ destroy failed" | tee -a "${TASKLOG}"

echo "=== Part C: restore RHCSA pattern (vi -c) ==="              | tee -a "${TASKLOG}"
mkdir -p /tmp/lab26c/restore
cat > /tmp/lab26c/restore/base.txt <<'EOF'
color=old
mode=old
EOF
cp -a /tmp/lab26c/restore/base.txt /tmp/lab26c/restore/base.txt.bak
vi -c ':1,$s/old/new/g' -c ':wq' /tmp/lab26c/restore/base.txt
diff -u /tmp/lab26c/restore/base.txt.bak /tmp/lab26c/restore/base.txt | tee -a "${TASKLOG}"

echo "=== Part D: restore Ansible pattern (replace + lineinfile) ===" | tee -a "${TASKLOG}"
cat > /root/rhcsa_journal/lab-26c/task2-restore.yml <<'PLAYBOOK'
---
- name: "Lab 26c restore"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: "Ensure state token"
      ansible.builtin.replace:
        path: /tmp/lab26c/restore/base.txt
        regexp: 'new'
        replace: 'new'
    - name: "Append restore marker"
      ansible.builtin.lineinfile:
        path: /tmp/lab26c/restore/base.txt
        insertafter: EOF
        line: "restored_by=ansible"
PLAYBOOK

ansible-playbook /root/rhcsa_journal/lab-26c/task2-restore.yml      | tee -a "${TASKLOG}"
cat /tmp/lab26c/restore/base.txt                                     | tee -a "${TASKLOG}"

# Tier B weave
sudo -u "${USER}" bash -c 'echo "destroy-restore-verified $(date -Is)" > "'"${USER_HOME}"'/task2-asuser.txt"'
stat -c '%U:%G %a %n' "${USER_HOME}/task2-asuser.txt"               | tee -a "${TASKLOG}"

echo "task2 exit: $?"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-26c/task2
mkdir -p "${JDIR}"
cp /tmp/lab26c/task2.txt "${JDIR}/evidence.txt"
cp /root/rhcsa_journal/lab-26c/task2-restore.yml "${JDIR}/"
cp "${USER_HOME}/task2-asuser.txt" "${JDIR}/"
echo "TASK2 COMPLETE $(date -Is)" > "${JDIR}/done.txt"
ls -la "${JDIR}"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

rm -f /tmp/lab26c/task1.txt /tmp/lab26c/task2.txt
rm -rf /tmp/lab26c/restore
rm -f /root/rhcsa_journal/lab-26c/task2-restore.yml
rm -f "${USER_HOME}/task2-asuser.txt"

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "---- lab-26c cleanup audit ----"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Lab 26c Checklist

- [ ] Task 1 completed (26a backup-vs-edited `diff` audit captured)
- [ ] Task 2 completed (destroy-restore drill with both `vi -c` and Ansible module restore)
- [ ] T41/T44 controls rehearsed in verification context
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
