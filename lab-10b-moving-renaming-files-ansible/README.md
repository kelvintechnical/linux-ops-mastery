# Lab 10b: Moving and Renaming Files (Ansible) — Boundary `command: mv` AND `copy: backup: true`

- **Series:** linux-ops-mastery — Essential Tools & File Operations
- **Trilogy:** [`10a`](../lab-10a-moving-renaming-files-rhcsa/) → **`10b`** (Ansible — you are here) → [`10c`](../lab-10c-moving-renaming-files-verify/)
- **Career arcs covered:** RHCE EX294 — `mv` is a **Section 18 boundary** (no honest module). Two acceptable patterns: (1) `command: mv` with `creates:`/`removes:` for idempotence, (2) `ansible.builtin.copy` with `backup: true` for atomic config replace.
- **Prerequisite:** [`Lab 10a`](../lab-10a-moving-renaming-files-rhcsa/) and Lab 00 controller
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = `command: mv` with `creates:`/`removes:` (Boundary) · Task 2 = `copy: backup: true` for atomic config replace)
- **Practice Directory:** `/tmp/lab10b/`
- **Traps rehearsed:** **T10-D** (using `command:` without `creates:`/`removes:` — task always reports `changed`) · **T10-E** (using `command: mv` for config replace when `copy:` would be safer — atomic + diff + idempotent)

---

## LAB HEADER BLOCK

```bash
ansible --version | head -n 3
ls /root/rhcsa_journal/lab-10a/task2/done.txt 2>/dev/null && echo "✅ 10a journal" || echo "❌ 10a journal missing"
echo "exit was: $?"
```

---

## Lab-Wide Setup

```bash
sudo -i
mkdir -p /tmp/lab10b/dest
mkdir -p /root/rhcsa_journal/lab-10b/playbooks
mkdir -p /root/rhcsa_journal/lab-10b/task1 /root/rhcsa_journal/lab-10b/task2

echo "v1 config" > /tmp/lab10b/dest/config.cfg
echo "report content" > /tmp/lab10b/report.txt

ls -l /tmp/lab10b/ /tmp/lab10b/dest/
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — Boundary: `command: mv` with `creates:`/`removes:`

### 🔁 Warm-Up

```bash
ansible-doc ansible.builtin.command | head -n 30
ls -l /tmp/lab10b/report.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab10b/task1.txt
PB=/root/rhcsa_journal/lab-10b/playbooks/task1.yml

cat > "${PB}" << 'PLAYBOOK'
---
- name: "Lab 10b Task 1 — Boundary mv with idempotence guards"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Move report.txt into dest/  (idempotent via creates:)"
      ansible.builtin.command:
        cmd: mv /tmp/lab10b/report.txt /tmp/lab10b/dest/report.txt
        creates: /tmp/lab10b/dest/report.txt
        removes: /tmp/lab10b/report.txt
      register: mv_result

    - name: "Show result"
      ansible.builtin.debug:
        msg:
          - "changed: {{ mv_result.changed }}"
          - "stdout:  {{ mv_result.stdout | default('(empty)') }}"
          - "skipped: {{ mv_result.skipped | default(false) }}"
PLAYBOOK

echo "═══ Part A: --check --diff ═══"                    2>&1 | tee $TASKLOG
ansible-playbook --check --diff "${PB}"                  2>&1 | tee -a $TASKLOG

echo "═══ Part B: apply ═══"                              | tee -a $TASKLOG
ansible-playbook "${PB}"                                  2>&1 | tee -a $TASKLOG
ls -l /tmp/lab10b/ /tmp/lab10b/dest/                     | tee -a $TASKLOG

echo "═══ Part C: re-apply (idempotent — creates: triggers skip) ═══" | tee -a $TASKLOG
ansible-playbook "${PB}"                                  2>&1 | tee -a $TASKLOG
CHG_C=$(grep -oP 'changed=\K[0-9]+' "$TASKLOG" | tail -n 1)
test "${CHG_C}" -eq 0 \
    && echo "✅ T10-D fix — creates: made command idempotent (changed=${CHG_C})" \
    || echo "❌ still changing — re-check creates:" \
    | tee -a $TASKLOG

echo "exit was: $?"
```

### 🧠 Concept Card

| Concept | What it does |
|---|---|
| `command:` module | Runs a binary on target — no shell expansion, no pipes |
| `creates: PATH` | Skip task if PATH exists |
| `removes: PATH` | Skip task if PATH does NOT exist |
| Combining both | Idempotent move: skip if dest exists OR src is gone |
| **🪤 Trap Risk T10-D** | `command: mv ...` without `creates:`/`removes:` — task always `changed`. **Fix:** add the guards. |

### Journal write

```bash
LAB=lab-10b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab10b/task1.txt "$JDIR/evidence.txt"
cp "${PB}" "$JDIR/task1.yml"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Boundary command: mv with creates:/removes:
TRAPS:    T10-D rehearsed
NEXT:     task2 — copy + backup atomic replace
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /tmp/lab10b/task1.txt
echo "exit was: $?"
```

> **STOP — paste Part B move evidence and Part C `✅ T10-D` line before Task 2.**

---

## Task 2 — `copy: backup: true` for atomic config replace (T10-E preferred)

### Main command block

```bash
TASKLOG=/tmp/lab10b/task2.txt
PB=/root/rhcsa_journal/lab-10b/playbooks/task2.yml

cat > "${PB}" << 'PLAYBOOK'
---
- name: "Lab 10b Task 2 — atomic config replace via copy + backup"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    new_content: |
      # === v2 config (atomic replaced) ===
      lab=10b
      replaced_at={{ ansible_date_time.iso8601 | default('now') }}

  tasks:
    - name: "Atomic config replace with backup"
      ansible.builtin.copy:
        dest: /tmp/lab10b/dest/config.cfg
        content: "{{ new_content }}"
        mode: '0644'
        owner: root
        group: root
        backup: true
      register: cfg_result

    - name: "Show result"
      ansible.builtin.debug:
        msg:
          - "changed: {{ cfg_result.changed }}"
          - "backup_file: {{ cfg_result.backup_file | default('none') }}"
PLAYBOOK

echo "═══ Part A: --check --diff ═══"                    2>&1 | tee $TASKLOG
ansible-playbook --check --diff "${PB}"                  2>&1 | tee -a $TASKLOG

echo "═══ Part B: apply ═══"                              | tee -a $TASKLOG
ansible-playbook "${PB}"                                  2>&1 | tee -a $TASKLOG
ls -l /tmp/lab10b/dest/                                  | tee -a $TASKLOG
cat /tmp/lab10b/dest/config.cfg                          | tee -a $TASKLOG

echo "═══ Part C: backup file present ═══"                | tee -a $TASKLOG
ls /tmp/lab10b/dest/config.cfg.* 2>/dev/null             | tee -a $TASKLOG
test -f /tmp/lab10b/dest/config.cfg.* \
    && echo "✅ T10-E — atomic replace produced backup" \
    || echo "❌ no backup created" \
    | tee -a $TASKLOG

echo "═══ Part D: re-apply (idempotent — gather_facts off so date stable) ═══" | tee -a $TASKLOG
ansible-playbook "${PB}"                                  2>&1 | tee -a $TASKLOG

echo "exit was: $?"
```

### 🧠 Concept Card

| Concept | What it does |
|---|---|
| `copy: content:` | Inline content; no source file needed |
| `backup: true` | Pre-replace snapshot at `<dest>.<timestamp>` |
| Atomic | `copy:` writes a tempfile then renames — same `rename(2)` atomicity as `mv` |
| **🪤 Trap Risk T10-E** | Reaching for `command: mv` when you really want declarative atomic replace. **Fix:** use `copy:` with `backup:`. |

### Journal write

```bash
LAB=lab-10b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab10b/task2.txt "$JDIR/evidence.txt"
cp "${PB}" "$JDIR/task2.yml"
ls /tmp/lab10b/dest/config.cfg.* 2>/dev/null > "$JDIR/backup-list.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Atomic config replace via copy + backup
TRAPS:    T10-E rehearsed
NEXT:     lab-10c — verify capstone
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /tmp/lab10b/task2.txt
echo "exit was: $?"
```

> **STOP — paste Part C `✅ T10-E` line.**

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
