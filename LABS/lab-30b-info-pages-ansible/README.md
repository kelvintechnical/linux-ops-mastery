# Lab 30b: Navigating info Pages (Ansible) — exporting info nodes in a play

**Series:** linux-ops-mastery — Documentation · **Lab 30b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (capturing/asserting doc facts), RHCSA EX200 (the `info` behavior underneath), DevOps (doc artifact generation)  
**Prerequisite:** [Lab 30a](../lab-30a-info-pages-rhcsa/) completed and a working control node  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `info --output` | _Task 1 · Step 1_ |
| A2 | `changed_when: false` for reads | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | the interactive-reader boundary | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `info --output=-` to stdout | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | save node as artifact | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `assert` on node content | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

Pull info documentation from automation. Since `info` is an interactive reader, you'll use `info --output` to render a node non-interactively, capture it read-only, save it as a documentation artifact, and assert it contains an expected option. This is how a play extracts and validates the long-form GNU docs on a node.

---

## 🧠 Concept

`info` opens an interactive node reader — no good in a play. The escape hatch is `info --output=FILE NODE` (or `--output=-` to write to stdout), which renders the node as plain text and exits. Run it via `ansible.builtin.command`, read-only (`changed_when: false`), and you have the node in `stdout`. Save it with `copy` for a per-node documentation artifact, or assert on its content to confirm the installed tool documents a feature you depend on. This is the `info` analog of Lab 28b's `man -P cat`.

```
SHELL (30a, interactive)            ANSIBLE (30b, deterministic)
─────────────────────────────       ──────────────────────────────────────
info coreutils 'ls invocation'      command: info --output=- coreutils 'ls invocation'
  (opens the reader)                  └─ changed_when: false, capture stdout
                                     copy: save the node text as an artifact
                                     assert: '--human-readable' in node
```

> **Why this matters:** GNU tool behavior (coreutils, bash) is fully documented only in info. Extracting a node lets a play archive that documentation or assert that the node version on a host documents the option a role relies on.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `info --output=-` | Render node to stdout | non-interactive |
| `info --output=FILE` | Render node to a file | artifact |
| `command:` capture | Read into a var | `changed_when: false` |
| `ansible.builtin.copy` | Persist artifact | `content:` |
| `assert` | Validate content | `that:` checks |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and playbook folder for captured info nodes.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-30
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-30b/playbooks
echo "ready"
echo "exit was: $?"
```

**Expected output:**

```
ready
exit was: 0
```

---

## TASK 1 of 2 — Render a node non-interactively

**In plain English:** We capture an info node as text from inside a play.

---

### Step 1 of 2 — Write the render playbook

**In plain English:** We create `task1.yml`, which renders the coreutils `ls` node to stdout read-only and shows its first lines.

```yaml
---
- name: "Lab 30b Task 1 — render an info node"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: "Render the ls info node to stdout"
      ansible.builtin.command: "info --output=- coreutils 'ls invocation'"
      register: node
      changed_when: false

    - name: "Show the first lines of the node"
      ansible.builtin.debug:
        msg: "{{ node.stdout_lines[:5] }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `command: info --output=- coreutils 'ls invocation'` → Render the node to stdout (`-`), no interactive reader.
- `changed_when: false` → Reading docs changes nothing.
- `node.stdout_lines[:5]` → Show the first five lines as a preview.

**New words in this step:**

- **`info --output=-`** — render an info node to stdout for capture.

---

### Step 2 of 2 — Run it and read the node

**In plain English:** We run the play and confirm the node text was captured.

```bash
ansible-playbook /root/rhcsa_journal/lab-30b/playbooks/task1.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Show the first lines of the node] *********************************
ok: [localhost] => {
    "msg": ["10.1 'ls': List directory contents", "...", "..."]
}
PLAY RECAP **************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Render and preview; read-only so `changed=0`.

**New words in this step:**

- **node capture** — reading an info node's text into a play variable.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `--output=-` | stdout render | no reader |
| quoted node | exact name | `'ls invocation'` |
| `changed_when: false` | read marker | docs never change |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Task hangs | Bare `info` | Use `--output` |
| Empty stdout | Wrong node name | Quote the exact node |

---

## TASK 2 of 2 — Save and assert a node

**In plain English:** We persist a node as an artifact and assert it documents an option.

---

### Step 1 of 2 — Write the save-and-assert playbook

**In plain English:** We create `task2.yml`, which renders the `ls` node, saves it, and asserts it documents `--human-readable`.

```yaml
---
- name: "Lab 30b Task 2 — save and assert an info node"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    out: /tmp/lab-30/ls-node.txt
  tasks:
    - name: "Render the ls node"
      ansible.builtin.command: "info --output=- coreutils 'ls invocation'"
      register: node
      changed_when: false

    - name: "Save the node as a documentation artifact"
      ansible.builtin.copy:
        dest: "{{ out }}"
        content: "{{ node.stdout }}\n"
        mode: '0644'
      register: saved

    - name: "Assert the node documents --human-readable"
      ansible.builtin.assert:
        that:
          - "'--human-readable' in node.stdout"
        success_msg: "node documents --human-readable"
        fail_msg: "expected option not documented"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `command: info --output=- ...` → Render the node text.
- `copy: content: node.stdout` → Persist it as an artifact on the node.
- `assert: '--human-readable' in node.stdout` → Confirm the installed docs cover the option a role might rely on.

**New words in this step:**

- **doc artifact** — a saved info node kept for records or auditing.

---

### Step 2 of 2 — Run it and read the file

**In plain English:** We run the play and confirm the artifact and assertion.

```bash
ansible-playbook /root/rhcsa_journal/lab-30b/playbooks/task2.yml
grep -c human-readable /tmp/lab-30/ls-node.txt
echo "exit was: $?"
```

**Expected output:**

```
TASK [Assert the node documents --human-readable] **********************
ok: [localhost] => {"msg": "node documents --human-readable"}
PLAY RECAP **********************************************************
localhost                  : ok=3    changed=1    unreachable=0    failed=0
1
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Render, save, assert; `changed=1` only from the file write.
- `grep -c human-readable ls-node.txt` → Confirm the artifact contains the option.

**New words in this step:**

- **content assertion** — proving a captured node documents an expected feature.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| save node | artifact | only write is changed |
| assert content | validate docs | quote `in` |
| `--output=-` | stdout | then `copy` |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Assert fails | Option name differs | Check exact spelling |
| File empty | Node not rendered | Fix the node name |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the render playbook
- [ ] Task 1 · Step 2 — Run it and read the node
- [ ] Task 2 · Step 1 — Write the save-and-assert playbook
- [ ] Task 2 · Step 2 — Run it and read the file
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-30
rm -rf /root/rhcsa_journal/lab-30b
```

**Expected output:**

```
✅ Removed /tmp/lab-30 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Bare `info` in a play | Task hangs | Use `--output` |
| Wrong node name | Empty render | Quote `'X invocation'` |
| Reads marked changed | Missing `changed_when: false` | Add it |

---

## 📌 Exam Strategy

Render info nodes with `info --output=-` to capture GNU docs in automation — never bare `info`. Save nodes as artifacts and assert on their content to validate the documentation/tooling a role depends on.

- `info --output=-` is the non-interactive renderer.
- Quote the exact node (`'ls invocation'`).
- `changed_when: false` on every render.

---

## 🔗 Related Labs

- [Lab 30a — Navigating info Pages (RHCSA)](../lab-30a-info-pages-rhcsa/) — the `info` reader this automates
- [Lab 30c — Navigating info Pages (Verify)](../lab-30c-info-pages-verify/) — prove nodes exist and resolve
- [Lab 28b — Exploring Manual Pages (Ansible)](../lab-28b-man-pages-ansible/) — the `man` capture analog

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
