# Lab 25b: Extracting Columns with `awk` (Ansible) — `shell` + `register` and `lineinfile` regex patterns

- **Series:** linux-ops-mastery — Text Processing and Parsing
- **Trilogy:** [`25a`](../lab-25a-awk-columns-rhcsa/) → **`25b`** (Ansible) → [`25c`](../lab-25c-awk-columns-verify/)
- **Prerequisite:** Lab 25a complete and Ansible control node ready
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = run `awk` via `ansible.builtin.shell` + `register` and mirror filter with `lineinfile` · Task 2 = regex update with awk-style FS behavior trap)
- **Practice Directory (rotation slot):** `/tmp`
- **Playbooks:** `/root/rhcsa_journal/lab-25b/playbooks/`
- **Sandbox (Tier B):** `/tmp/lab25b` with `USER=labuser_25_awk`, `GROUP=labgrp_25_awk`
- **Traps rehearsed:** **T25-A** (wrong separator assumptions) · **T25-B** (single vs double quotes for expansion) · **T41** (skip restore re-apply) · **T44** (orphan cleanup leftovers)

---

## LAB HEADER BLOCK

```bash
ansible --version | head -n 3
ansible localhost -m ping --connection=local 2>/dev/null \
  && echo "✅ localhost reachable" \
  || echo "❌ localhost ping failed"
ls /root/rhcsa_journal/lab-25a/task1/done.txt /root/rhcsa_journal/lab-25a/task2/done.txt 2>/dev/null \
  && echo "✅ 25a journal present" \
  || echo "❌ 25a journal missing"
echo "⚠️ TRAPS: T25-A T25-B T41 T44"
echo "exit was: $?"
```

---

## Objective

Translate the 25a column-extraction skill into Ansible workflows:

1. Use `ansible.builtin.shell` to execute `awk` exactly and capture output with `register`.
2. Convert filtered results into managed files.
3. Use `lineinfile` regex patterns that correctly model field boundaries.
4. Avoid quoting mistakes that alter expansion semantics.

---

## Lab-Wide Setup (Tier B + playbook area)

```bash
sudo -i

export LAB_NUM=25
export LAB_SLUG=awk
export SANDBOX=/tmp/lab25b
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-25b/playbooks
mkdir -p /root/rhcsa_journal/lab-25b/task1 /root/rhcsa_journal/lab-25b/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

cat > /tmp/lab25b/passwd-sample.txt <<'EOF'
root:x:0:0:root:/root:/bin/bash
nobody:x:65534:65534:nobody:/:
student1:x:1001:1001:Student One:/home/student1:/bin/bash
student2:x:2002:2002:Student Two:/home/student2:/bin/zsh
EOF

echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — `ansible.builtin.shell` awk + `register` OR `lineinfile` mirror

### Warm-Up

```bash
ansible-doc ansible.builtin.shell | rg 'executable|stdin|cmd' -n
ansible-doc ansible.builtin.lineinfile | rg 'regexp|line|backrefs' -n
ls -l /tmp/lab25b/passwd-sample.txt
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab25b/task1.txt
PB=/root/rhcsa_journal/lab-25b/playbooks/task1.yml

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 25b Task 1 — awk columns via shell + register"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Run required awk #1"
      ansible.builtin.shell: "awk -F: '{print $1}' /etc/passwd | head"
      register: awk_users
      changed_when: false

    - name: "Run required awk #2"
      ansible.builtin.shell: "awk -F: '$3>1000 {print $1}' /etc/passwd"
      register: awk_uid_gt_1000
      changed_when: false

    - name: "Persist registered outputs"
      ansible.builtin.copy:
        dest: /tmp/lab25b/awk-task1-output.txt
        mode: '0644'
        content: |
          === awk -F: '{print $1}' /etc/passwd | head ===
          {{ awk_users.stdout }}
          === awk -F: '$3>1000 {print $1}' /etc/passwd ===
          {{ awk_uid_gt_1000.stdout }}

    - name: "lineinfile mirror of awk-style UID filter"
      ansible.builtin.lineinfile:
        path: /tmp/lab25b/passwd-filtered.txt
        create: true
        mode: '0644'
        regexp: '^([^:]*:){2}(1[0-9]{3,}|[2-9][0-9]{3,}):'
        line: '\g<0> # uid-gt-1000'
        backrefs: true
PLAYBOOK

echo "═══ Part A: apply playbook ═══"                             2>&1 | tee $TASKLOG
ansible-playbook "${PB}"                                          2>&1 | tee -a $TASKLOG

echo "═══ Part B: verify artifacts ═══"                           | tee -a $TASKLOG
cat /tmp/lab25b/awk-task1-output.txt                              | tee -a $TASKLOG
cp /tmp/lab25b/passwd-sample.txt /tmp/lab25b/passwd-filtered.txt
ansible-playbook "${PB}"                                           2>&1 | tee -a $TASKLOG
cat /tmp/lab25b/passwd-filtered.txt                                | tee -a $TASKLOG
echo "exit was: $?"
```

### Concept Card

| Concept | What it does |
|---|---|
| `shell` + `register` | Captures command output for later tasks |
| `changed_when: false` | Marks pure read commands as non-mutating |
| `lineinfile` + `backrefs` | Rewrites matched content with regex captures |
| **🪤 Trap Risk T25-A** | Regex or awk without colon-aware logic targets wrong field |

### Journal write

```bash
LAB=lab-25b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab25b/task1.txt "$JDIR/evidence.txt"
cp "${PB}" "$JDIR/task1.yml"
cp /tmp/lab25b/awk-task1-output.txt "$JDIR/awk-task1-output.txt"
```

---

## Task 2 — Replace with awk-style FS regex pattern (trap rehearsal)

### Main command block

```bash
TASKLOG=/tmp/lab25b/task2.txt
PB=/root/rhcsa_journal/lab-25b/playbooks/task2.yml

cat > "${PB}" <<'PLAYBOOK'
---
- name: "Lab 25b Task 2 — regex correction for colon fields"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    sample: /tmp/lab25b/passwd-sample.txt
    result: /tmp/lab25b/passwd-regex-fix.txt

  tasks:
    - name: "Reset result from sample"
      ansible.builtin.copy:
        src: "{{ sample }}"
        dest: "{{ result }}"
        remote_src: true
        mode: '0644'

    - name: "BAD pattern (trap demo): whitespace-oriented split idea"
      ansible.builtin.lineinfile:
        path: "{{ result }}"
        regexp: '^\S+\s+\S+\s+[1-9][0-9]{3,}\s+'
        line: '# bad-regex-hit'
      failed_when: false

    - name: "GOOD pattern: third colon-delimited field >1000 shape"
      ansible.builtin.lineinfile:
        path: "{{ result }}"
        regexp: '^([^:]*:){2}(1[0-9]{3,}|[2-9][0-9]{3,}):'
        line: 'UID_GT_1000_MATCH'
PLAYBOOK

echo "═══ Part A: apply regex-fix playbook ═══"                    2>&1 | tee $TASKLOG
ansible-playbook "${PB}"                                            2>&1 | tee -a $TASKLOG

echo "═══ Part B: show result + quoting trap proof (T25-B) ═══"    | tee -a $TASKLOG
cat /tmp/lab25b/passwd-regex-fix.txt                                | tee -a $TASKLOG
ansible localhost -m ansible.builtin.shell -a 'echo ${USER}' --connection=local 2>&1 | tee -a $TASKLOG
ansible localhost -m ansible.builtin.shell -a "echo ${USER}" --connection=local 2>&1 | tee -a $TASKLOG

echo "═══ Part C: Tier B sudo -u weave ═══"                        | tee -a $TASKLOG
sudo -u "${USER}" -H bash -c 'echo "task2-owned-by-$(whoami)" > "'"${USER_HOME}"'/task2-asuser.txt"'
stat -c '%U:%G %a %n' "${USER_HOME}/task2-asuser.txt"               | tee -a $TASKLOG
cat "${USER_HOME}/task2-asuser.txt"                                 | tee -a $TASKLOG
echo "exit was: $?"
```

### Concept Card

| Concept | What it does |
|---|---|
| Bad whitespace regex | Fails on `/etc/passwd` style records |
| Colon-aware regex | Mirrors `awk -F:` field indexing behavior |
| Shell quoting in Ansible ad-hoc | Single quotes keep `${USER}` literal |
| **🪤 Trap Risk T25-B** | Wrong quote type causes unexpected expansion |

### Journal write

```bash
LAB=lab-25b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab25b/task2.txt "$JDIR/evidence.txt"
cp "${PB}" "$JDIR/task2.yml"
cp /tmp/lab25b/passwd-regex-fix.txt "$JDIR/passwd-regex-fix.txt"
cp "${USER_HOME}/task2-asuser.txt" "$JDIR/task2-asuser.txt"
```

---

## Lab Closeout — Section 6 Bulletproof Teardown

```bash
set +e
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}" /tmp/lab25b/passwd-*.txt /tmp/lab25b/awk-task1-output.txt /tmp/lab25b/task1.txt /tmp/lab25b/task2.txt

echo "── Lab 25b cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Lab 25b Checklist

- [ ] Task 1 complete: `shell` + `register` outputs captured and stored
- [ ] Task 2 complete: regex trap and corrected colon-field pattern validated
- [ ] Tier B ownership proof captured for `${USER}:${GROUP}`
- [ ] Section 6 closeout completed (no orphan user/group/sandbox)

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
