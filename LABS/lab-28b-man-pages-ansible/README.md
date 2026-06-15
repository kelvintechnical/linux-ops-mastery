# Lab 28b: Exploring Manual Pages (Ansible) — capturing docs in a play

**Series:** linux-ops-mastery — Documentation · **Lab 28b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (capturing/asserting command facts), RHCSA EX200 (the `man` behavior underneath), DevOps (documenting managed nodes)  
**Prerequisite:** [Lab 28a](../lab-28a-man-pages-rhcsa/) completed and a working control node  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `man -w` / `man -f` | _Task 1 · Step 1_ |
| A2 | `changed_when: false` for reads | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | the pager boundary (`man -P cat`) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `man -w` existence check in-play | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | capture man summary to a file | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `assert` on doc content | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

Read documentation from automation. Since `man` is an interactive pager, you'll run it non-interactively (`man -P cat` / `man -f`), confirm a page exists with `man -w` inside a play, capture a command's one-line summary to a file on the node, and assert the documentation contains what you expect. This is how a play documents or validates the tools on a managed host.

---

## 🧠 Concept

`man` normally opens `less`, which has no place in automation. Force non-interactive output with `man -P cat` (use `cat` as the pager) or just use the non-paged subcommands `man -f`/`man -w`/`man -k`. In a play you run these via `ansible.builtin.command`, read-only (`changed_when: false`). `man -w name` is the cleanest *existence* check: rc 0 and a path mean the page (and usually the package) is present. To save documentation, capture `man -f`/`man -P cat` output and write it with `copy`/`lineinfile`. Then `assert` on the captured text to validate the node ships the expected tooling.

```
SHELL (28a, interactive)            ANSIBLE (28b, deterministic)
─────────────────────────────       ──────────────────────────────────────
man ls (opens less)                  command: man -P cat ls   (changed_when:false)
man -w ls                            command: man -w ls  → existence check
man -f ls                            command: man -f ls  → capture summary, assert
```

> **Why this matters:** "Is the documentation/tool installed?" is a real fleet question. `man -w` answers it cleanly in a play, and capturing summaries gives you per-node documentation artifacts.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `man -P cat` | Non-interactive page | pager = `cat` |
| `man -w` | Page path / existence | rc 0 = present |
| `man -f` | One-line summary | capturable |
| `changed_when: false` | Mark reads | for all `man` runs |
| `assert` | Validate doc content | `that:` checks |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and playbook folder for captured docs.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-28
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-28b/playbooks
echo "ready"
echo "exit was: $?"
```

**Expected output:**

```
ready
exit was: 0
```

---

## TASK 1 of 2 — Confirm a page exists

**In plain English:** We check that a man page resolves, from inside a play.

---

### Step 1 of 2 — Write the existence-check playbook

**In plain English:** We create `task1.yml`, which uses `man -w` read-only to prove the `ls` page exists.

```yaml
---
- name: "Lab 28b Task 1 — confirm a man page exists"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: "Locate the ls man page"
      ansible.builtin.command: "man -w ls"
      register: page
      changed_when: false
      failed_when: page.rc != 0

    - name: "Show the page path"
      ansible.builtin.debug:
        msg: "ls page at {{ page.stdout }}"

    - name: "Assert it is a section-1 page"
      ansible.builtin.assert:
        that:
          - "'man1/ls' in page.stdout"
        success_msg: "ls(1) present"
        fail_msg: "ls man page missing or wrong section"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `command: man -w ls` → Print the page path; rc 0 means it exists. No pager, so safe in automation.
- `failed_when: page.rc != 0` → Treat a missing page as a failure.
- `assert: 'man1/ls' in page.stdout` → Confirm it's the section-1 page.

**New words in this step:**

- **`man -w` existence check** — using the page path to prove documentation is present.

---

### Step 2 of 2 — Run it and read the result

**In plain English:** We run the play and confirm the page resolves.

```bash
ansible-playbook /root/rhcsa_journal/lab-28b/playbooks/task1.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Show the page path] ************************************************
ok: [localhost] => {"msg": "ls page at /usr/share/man/man1/ls.1.gz"}
TASK [Assert it is a section-1 page] ************************************
ok: [localhost] => {"msg": "ls(1) present"}
PLAY RECAP **********************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Locate, display, assert; read-only so `changed=0`.

**New words in this step:**

- **doc presence** — a play-level check that documentation/tooling exists.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `man -w` | path/existence | rc 0 = present |
| `failed_when` | gate on rc | missing = fail |
| `changed_when: false` | read marker | docs never "change" |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| rc non-zero | Page/package missing | Install the package |
| Hangs | Used bare `man` | Use `man -w`/`-P cat` |

---

## TASK 2 of 2 — Capture and assert a summary

**In plain English:** We save a command's one-line summary and assert its content.

---

### Step 1 of 2 — Write the capture-and-assert playbook

**In plain English:** We create `task2.yml`, which captures `man -f` for `cp`, saves it, and asserts it describes copying.

```yaml
---
- name: "Lab 28b Task 2 — capture a man summary"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    out: /tmp/lab-28/cp-summary.txt
  tasks:
    - name: "Capture the cp summary (non-interactive)"
      ansible.builtin.command: "man -f cp"
      register: summary
      changed_when: false

    - name: "Save the summary to a file"
      ansible.builtin.copy:
        dest: "{{ out }}"
        content: "{{ summary.stdout }}\n"
        mode: '0644'
      register: saved

    - name: "Assert the summary mentions copying"
      ansible.builtin.assert:
        that:
          - "'copy' in summary.stdout"
        success_msg: "cp summary captured: {{ summary.stdout }}"
        fail_msg: "unexpected cp summary"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `command: man -f cp` → Capture the one-line summary, non-interactive.
- `copy: content: summary.stdout` → Persist the doc snippet to the node.
- `assert: 'copy' in summary.stdout` → Validate the documentation says what we expect.

**New words in this step:**

- **captured summary** — a saved one-line man description as a documentation artifact.

---

### Step 2 of 2 — Run it and read the file

**In plain English:** We run the play and confirm the saved summary.

```bash
ansible-playbook /root/rhcsa_journal/lab-28b/playbooks/task2.yml
cat /tmp/lab-28/cp-summary.txt
echo "exit was: $?"
```

**Expected output:**

```
TASK [Assert the summary mentions copying] *****************************
ok: [localhost] => {"msg": "cp summary captured: cp (1) - copy files and directories"}
PLAY RECAP **********************************************************
localhost                  : ok=3    changed=1    unreachable=0    failed=0
cp (1)               - copy files and directories
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Capture, save, assert; `changed=1` only from writing the file.
- `cat cp-summary.txt` → The saved documentation snippet.

**New words in this step:**

- **documentation artifact** — captured man output persisted for records.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `man -f` capture | summary text | non-interactive |
| `copy` content | persist doc | only write is `changed` |
| assert content | validate | quote `in` expression |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Empty summary | mandb stale | `sudo mandb` on node |
| Assert fails | Wording differs | Loosen the substring |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the existence-check playbook
- [ ] Task 1 · Step 2 — Run it and read the result
- [ ] Task 2 · Step 1 — Write the capture-and-assert playbook
- [ ] Task 2 · Step 2 — Run it and read the file
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-28
rm -rf /root/rhcsa_journal/lab-28b
```

**Expected output:**

```
✅ Removed /tmp/lab-28 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Bare `man` in a play | Task hangs (pager) | `man -P cat` / `-f` / `-w` |
| Reads marked changed | Missing `changed_when: false` | Add it |
| Brittle content assert | Wording mismatch | Use a stable substring |

---

## 📌 Exam Strategy

In automation, use `man -w` to check a page/tool exists and `man -f`/`man -P cat` to capture text — never bare `man` (it pagers and hangs). Assert on captured content to validate node tooling.

- `man -w` is the clean existence check.
- `man -P cat`/`-f` for non-interactive content.
- `changed_when: false` on every doc read.

---

## 🔗 Related Labs

- [Lab 28a — Exploring Manual Pages (RHCSA)](../lab-28a-man-pages-rhcsa/) — the `man` this automates
- [Lab 28c — Exploring Manual Pages (Verify)](../lab-28c-man-pages-verify/) — prove pages exist and resolve
- [Lab 18b — Locate Command Documentation (Ansible)](../lab-18b-locate-command-docs-ansible/) — package-doc capture with `rpm -qd`

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
