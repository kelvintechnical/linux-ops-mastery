# Lab 09b: Hard and Soft Links (Ansible) — `state=link`, `state=hard`, `force: true`

- **Series:** linux-ops-mastery — Essential Tools & File Operations
- **Trilogy:** [`09a`](../lab-09a-hard-and-soft-links-rhcsa/) → **`09b`** (Ansible — you are here) → [`09c`](../lab-09c-hard-and-soft-links-verify/)
- **Career arcs covered:** RHCE EX294 (`ansible.builtin.file: state=link`)
- **Prerequisite:** [`Lab 09a`](../lab-09a-hard-and-soft-links-rhcsa/) and Lab 00 controller
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = `state=link` + `state=hard` declarative · Task 2 = `force: true` to replace existing files; idempotence)
- **Practice Directory:** `/tmp/lab09b/`
- **Traps rehearsed:** **T17-X** (Ansible refuses to overwrite an existing regular file with a link unless `force: true`) · **T18-X** (relative `src:` is preserved as-is — same T19 trap, just declarative)

---

## LAB HEADER BLOCK

```bash
ansible --version | head -n 3
ls /root/rhcsa_journal/lab-09a/task1/done.txt 2>/dev/null && echo "✅ 09a journal" || echo "❌ 09a journal missing"
echo "exit was: $?"
```

---

## Lab-Wide Setup

```bash
sudo -i
mkdir -p /tmp/lab09b
echo "primary content" > /tmp/lab09b/primary.txt
mkdir -p /root/rhcsa_journal/lab-09b/playbooks
mkdir -p /root/rhcsa_journal/lab-09b/task1 /root/rhcsa_journal/lab-09b/task2
ls -l /tmp/lab09b
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — `state=link` and `state=hard`

### 🔁 Warm-Up

```bash
ansible-doc ansible.builtin.file | head -n 30
ls -li /tmp/lab09b/primary.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab09b/task1.txt
PB=/root/rhcsa_journal/lab-09b/playbooks/task1.yml

cat > "${PB}" << 'PLAYBOOK'
---
- name: "Lab 09b Task 1 — declarative links"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Symbolic link"
      ansible.builtin.file:
        src: /tmp/lab09b/primary.txt
        dest: /tmp/lab09b/sym.txt
        state: link
      register: sym_result

    - name: "Hard link"
      ansible.builtin.file:
        src: /tmp/lab09b/primary.txt
        dest: /tmp/lab09b/hard.txt
        state: hard
      register: hard_result

    - name: "Show results"
      ansible.builtin.debug:
        msg:
          - "sym  changed: {{ sym_result.changed }}  dest: {{ sym_result.dest }}"
          - "hard changed: {{ hard_result.changed }} dest: {{ hard_result.dest }}"
PLAYBOOK

echo "═══ Part A: --check --diff ═══"                    2>&1 | tee $TASKLOG
ansible-playbook --check --diff "${PB}"                  2>&1 | tee -a $TASKLOG

echo "═══ Part B: apply ═══"                              | tee -a $TASKLOG
ansible-playbook "${PB}"                                 2>&1 | tee -a $TASKLOG

echo "═══ Part C: verify on disk ═══"                     | tee -a $TASKLOG
ls -li /tmp/lab09b/                                      | tee -a $TASKLOG
readlink /tmp/lab09b/sym.txt                             | tee -a $TASKLOG
P_INO=$(stat -c '%i' /tmp/lab09b/primary.txt)
H_INO=$(stat -c '%i' /tmp/lab09b/hard.txt)
test "${P_INO}" = "${H_INO}" \
    && echo "✅ hard.txt shares inode with primary.txt" \
    || echo "❌ inodes differ" \
    | tee -a $TASKLOG

echo "═══ Part D: re-apply (idempotence) ═══"             | tee -a $TASKLOG
ansible-playbook "${PB}"                                 2>&1 | tee -a $TASKLOG
CHG_D=$(grep -oP 'changed=\K[0-9]+' "$TASKLOG" | tail -n 1)
test "${CHG_D}" -eq 0 && echo "✅ idempotent (D=${CHG_D})" || echo "❌ not idempotent" | tee -a $TASKLOG

echo "exit was: $?"
```

### Journal write

```bash
LAB=lab-09b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab09b/task1.txt "$JDIR/evidence.txt"
cp "${PB}" "$JDIR/task1.yml"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    state=link + state=hard via ansible.builtin.file
NEXT:     task2 — force: true
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /tmp/lab09b/task1.txt
echo "exit was: $?"
```

> **STOP — paste Part C inode-match line and Part D `✅ idempotent`.**

---

## Task 2 — `force: true` to overwrite a regular file with a link (T17-X)

### Main command block

```bash
TASKLOG=/tmp/lab09b/task2.txt
PB=/root/rhcsa_journal/lab-09b/playbooks/task2.yml

# Stage a regular file at the dest path so force: true is needed
echo "PRE-EXISTING REGULAR FILE" > /tmp/lab09b/will-be-link.txt

cat > "${PB}" << 'PLAYBOOK'
---
- name: "Lab 09b Task 2 — force: true"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Try without force (will fail / refuse)"
      ansible.builtin.file:
        src: /tmp/lab09b/primary.txt
        dest: /tmp/lab09b/will-be-link.txt
        state: link
      register: noforce_result
      ignore_errors: true

    - name: "Show no-force result"
      ansible.builtin.debug:
        msg: "no-force changed={{ noforce_result.changed | default(false) }} failed={{ noforce_result.failed | default(false) }}"

    - name: "Now with force: true"
      ansible.builtin.file:
        src: /tmp/lab09b/primary.txt
        dest: /tmp/lab09b/will-be-link.txt
        state: link
        force: true
      register: force_result

    - name: "Show force result"
      ansible.builtin.debug:
        msg: "force changed={{ force_result.changed }}"
PLAYBOOK

echo "═══ Part A: apply (no-force then force) ═══"       2>&1 | tee $TASKLOG
ansible-playbook "${PB}"                                 2>&1 | tee -a $TASKLOG

echo "═══ Part B: verify it became a symlink ═══"         | tee -a $TASKLOG
ls -l /tmp/lab09b/will-be-link.txt                       | tee -a $TASKLOG
test -L /tmp/lab09b/will-be-link.txt \
    && echo "✅ T17-X — force: true replaced regular file with symlink" \
    || echo "❌ still a regular file" \
    | tee -a $TASKLOG

echo "═══ Part C: re-apply (idempotence) ═══"             | tee -a $TASKLOG
ansible-playbook "${PB}"                                 2>&1 | tee -a $TASKLOG

echo "exit was: $?"
```

### 🧠 Concept Card

| Concept | What it does |
|---|---|
| `force: true` | Replace existing dest if it's a different type |
| Without `force`, link refuses to clobber | Idempotent + safe by default |
| **🪤 Trap Risk T17-X** | Forgetting `force: true` when migrating a regular file to a symlink. **Fix:** add `force: true` once you confirm intent. |

### Journal write

```bash
LAB=lab-09b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab09b/task2.txt "$JDIR/evidence.txt"
cp "${PB}" "$JDIR/task2.yml"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    force: true to replace regular file with symlink
TRAPS:    T17-X rehearsed
NEXT:     lab-09c
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /tmp/lab09b/task2.txt
echo "exit was: $?"
```

> **STOP — paste Part B `✅ T17-X` line.**

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
