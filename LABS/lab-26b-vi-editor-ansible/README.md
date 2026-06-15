# Lab 26b: Editing Files (Ansible) — `blockinfile`, `lineinfile` instead of vi

**Series:** linux-ops-mastery — Text Editors · **Lab 26b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (declarative file edits — the automation answer to vi), RHCSA EX200 (the edits vi would make), DevOps (managed config blocks)  
**Prerequisite:** [Lab 26a](../lab-26a-vi-editor-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `lineinfile` single line | _Task 1 · Step 1_ |
| A2 | `:%s///g` mental model | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | the interactive-editor boundary | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `ansible.builtin.blockinfile` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N3 | `marker:` managed block | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `insertafter:` / `insertbefore:` | Task 1 · Step 1 | _Task 1 · Step 1_ |

---

## 🎯 Objective

There is no "vi module" — automation edits *declaratively*. You will make the single-line edits vi would do with `ansible.builtin.lineinfile` (placed precisely with `insertafter:`), and manage a multi-line region as one idempotent unit with `ansible.builtin.blockinfile` and its `marker:`. These are the tools that replace opening a file and typing.

---

## 🧠 Concept

Interactive editors can't be automated — a play can't "press `i` and type." Instead Ansible declares the *desired content*. `ansible.builtin.lineinfile` ensures a single line exists (optionally positioned with `insertafter:`/`insertbefore:` regexes), the declarative version of vi's insert. `ansible.builtin.blockinfile` manages a whole multi-line region wrapped in auto-generated `marker:` comments (`# BEGIN ANSIBLE MANAGED BLOCK` … `# END …`); on re-run it updates only that block and reports `changed=0` when unchanged. The marker is what makes a block idempotent and safe to re-manage — Ansible knows exactly which lines it owns.

```
VI (26a)                             ANSIBLE (26b)
─────────────────────────────       ──────────────────────────────────────
o, type a line, Esc, :wq             lineinfile: line='...' insertafter='^...'
edit a multi-line section            blockinfile: block=|... marker='# {mark} APP'
```

> **Why this matters:** RHCE config management is declarative. `blockinfile` lets you own a managed region of a shared file (e.g. an `/etc/hosts` block) without clobbering the rest — the idempotent replacement for hand-editing in vi.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.lineinfile` | Ensure one line | `insertafter:`, `regexp:` |
| `insertafter:` / `insertbefore:` | Position the line | regex anchor |
| `ansible.builtin.blockinfile` | Manage a region | `block:`, `marker:` |
| `marker:` | Delimit managed block | `{mark}` placeholder |
| `backup: true` | Keep a backup | before editing |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and playbook folder with a config to edit.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-26
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-26b/playbooks
cat > "$LAB_ROOT/app.conf" <<'EOF'
[main]
name = demo
[network]
EOF
cat "$LAB_ROOT/app.conf"
echo "exit was: $?"
```

**Expected output:**

```
[main]
name = demo
[network]
exit was: 0
```

---

## TASK 1 of 2 — Insert a positioned line

**In plain English:** We add a line right after a section header, idempotently.

---

### Step 1 of 2 — Write the lineinfile playbook

**In plain English:** We create `task1.yml`, which inserts `port = 8080` right after the `[network]` header.

```yaml
---
- name: "Lab 26b Task 1 — insert a positioned line"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    conf: /tmp/lab-26/app.conf
  tasks:
    - name: "Ensure port line exists under [network]"
      ansible.builtin.lineinfile:
        path: "{{ conf }}"
        line: 'port = 8080'
        insertafter: '^\[network\]'
        backup: true
      register: line_result

    - name: "Show whether anything changed"
      ansible.builtin.debug:
        msg: "changed: {{ line_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `line: 'port = 8080'` → The line to guarantee exists — the declarative insert.
- `insertafter: '^\[network\]'` → Position it right after the `[network]` header, like moving the cursor there in vi.

**New words in this step:**

- **`insertafter:`** — place the managed line after a regex-matched anchor.

---

### Step 2 of 2 — Run it twice and watch `changed=0`

**In plain English:** We run the play twice; the line is inserted once and then already present.

```bash
ansible-playbook /root/rhcsa_journal/lab-26b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-26b/playbooks/task1.yml
cat /tmp/lab-26/app.conf
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
[main]
name = demo
[network]
port = 8080
exit was: 0
```

**Line-by-line breakdown:**

- two runs → `changed=1` then `changed=0`: the line exists after the first run.
- `cat app.conf` → The port line sits directly under `[network]`.

**New words in this step:**

- **declarative insert** — guaranteeing a line's presence rather than typing it.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `lineinfile` | one canonical line | anchor to avoid dupes |
| `insertafter:` | position | regex must match |
| idempotent | re-run `changed=0` | line already present |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Line appended at EOF | `insertafter` regex missed | Fix the anchor regex |
| Duplicate lines | No `regexp:` to match existing | Add `regexp:` |

---

## TASK 2 of 2 — Manage a multi-line block

**In plain English:** We own a multi-line region with `blockinfile` and prove it's idempotent.

---

### Step 1 of 2 — Write the blockinfile playbook

**In plain English:** We create `task2.yml`, which manages a labelled block of settings as one unit.

```yaml
---
- name: "Lab 26b Task 2 — manage a multi-line block"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    conf: /tmp/lab-26/app.conf
  tasks:
    - name: "Manage the limits block"
      ansible.builtin.blockinfile:
        path: "{{ conf }}"
        marker: "# {mark} APP LIMITS"
        block: |
          max_connections = 100
          timeout = 30
          retries = 3
        backup: true
      register: block_result

    - name: "Show whether anything changed"
      ansible.builtin.debug:
        msg: "changed: {{ block_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `marker: "# {mark} APP LIMITS"` → `{mark}` expands to BEGIN/END, wrapping the region Ansible owns.
- `block: |` → The multi-line content managed as a single idempotent unit.

**New words in this step:**

- **`blockinfile`** — manage a multi-line region as one idempotent block.
- **`marker:`** — the BEGIN/END comments delimiting the managed block.

---

### Step 2 of 2 — Run it twice and inspect the block

**In plain English:** We run the play twice; the block is inserted once and unchanged thereafter.

```bash
ansible-playbook /root/rhcsa_journal/lab-26b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-26b/playbooks/task2.yml
cat /tmp/lab-26/app.conf
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
[main]
name = demo
[network]
port = 8080
# BEGIN APP LIMITS
max_connections = 100
timeout = 30
retries = 3
# END APP LIMITS
exit was: 0
```

**Line-by-line breakdown:**

- two runs → `changed=1` then `changed=0`: the marker lets Ansible recognize its own block.
- `cat app.conf` → The managed block sits between its BEGIN/END markers.

**New words in this step:**

- **managed region** — the marker-delimited lines Ansible owns and can re-manage safely.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `blockinfile` | multi-line region | one block per marker |
| `{mark}` | BEGIN/END | unique marker per block |
| idempotent block | re-run `changed=0` | content must match |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Two blocks appear | Reused default marker | Give each a unique `marker:` |
| Block keeps changing | Trailing whitespace | Normalize the `block:` text |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the lineinfile playbook
- [ ] Task 1 · Step 2 — Run it twice and watch `changed=0`
- [ ] Task 2 · Step 1 — Write the blockinfile playbook
- [ ] Task 2 · Step 2 — Run it twice and inspect the block
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-26
rm -rf /root/rhcsa_journal/lab-26b
```

**Expected output:**

```
✅ Removed /tmp/lab-26 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Expecting a vi module | There isn't one | Use `lineinfile`/`blockinfile` |
| Reused block marker | Blocks overwrite each other | Unique `marker:` per block |
| Unanchored line | Duplicates | Add `regexp:`/`insertafter:` |

---

## 📌 Exam Strategy

Automate edits declaratively: `lineinfile` (with `insertafter:`) for single lines, `blockinfile` (with a unique `marker:`) for regions. Both are idempotent and let you own part of a file without disturbing the rest.

- One `blockinfile` per unique `marker:`.
- `insertafter:`/`insertbefore:` position single lines precisely.
- Re-run to confirm `changed=0`.

---

## 🔗 Related Labs

- [Lab 26a — Command/Insert Mode in vi (RHCSA)](../lab-26a-vi-editor-rhcsa/) — the interactive editing this replaces
- [Lab 26c — Command/Insert Mode in vi (Verify)](../lab-26c-vi-editor-verify/) — prove the edits saved
- [Lab 24b — Stream Editing with sed (Ansible)](../lab-24b-sed-stream-editor-ansible/) — `replace`/`lineinfile` edits

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
