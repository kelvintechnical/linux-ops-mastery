# Lab 10b: Moving and Renaming Files (Ansible) — `command: mv` (`creates:`/`removes:`), `copy` (`backup`)

**Series:** linux-ops-mastery — Essential Tools & File Operations · **Lab 10b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (making a non-module action idempotent), RHCSA EX200 (the `mv` behavior underneath), DevOps (safe relocations with rollback)  
**Prerequisite:** [Lab 10a](../lab-10a-moving-renaming-files-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `ansible.builtin.command` | _Task 1 · Step 1_ |
| A2 | `ansible.builtin.copy` `backup:` | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `creates:` + `removes:` together | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `command: mv` idiom | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `ansible.builtin.stat` `exists` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N4 | `copy` + `backup` as a "replace" | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

There is **no `mv` module** — moving is one action with two side effects (create destination, remove source). You will make `command: mv` idempotent by guarding it with both `creates:` (destination) and `removes:` (source), so a re-run after the move is a clean skip. Then you will express the safe "replace this file, keep a backup" pattern with `ansible.builtin.copy` + `backup: true`, the declarative alternative to `mv -b`.

---

## 🧠 Concept

Because `mv` both creates and deletes, a single guard is not enough. The idiom is `command: mv src dst` with `args: { creates: dst, removes: src }`: on the first run, `src` exists and `dst` does not, so it runs; on the re-run, `src` is gone (so `removes:` makes it skip) — `changed=0`. For an idempotent *replace* (rather than a move), `ansible.builtin.copy` with `backup: true` is cleaner than `mv -b`: it writes only on drift and returns the backup path. Use `ansible.builtin.stat`'s `exists` to assert the move's outcome.

```
SHELL (10a)                          ANSIBLE (10b)
─────────────────────────────       ──────────────────────────────────────
mv src dst                           command: mv src dst
                                       args: { creates: dst, removes: src }
mv -b new target                     copy: src=new dest=target backup=true
```

> **Why this matters:** A `command: mv` with no guards reports `changed=1` forever and re-fails when src is gone. The `creates:`+`removes:` pair is the canonical way to make a raw move idempotent — a frequent RHCE judgment.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.command` | Run `mv` (no module exists) | guard with `creates:`/`removes:` |
| `creates:` | Skip if destination exists | half the move guard |
| `removes:` | Skip if source is gone | the other half — key for `mv` |
| `ansible.builtin.copy` `backup: true` | Idempotent replace with backup | the `mv -b` alternative |
| `ansible.builtin.stat` | Assert `exists` on src/dst | confirm the outcome |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and playbook folder, and seed a file to move plus a target to replace.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-10
mkdir -p "$LAB_ROOT/archive"
mkdir -p /root/rhcsa_journal/lab-10b/playbooks
echo "report v1" > "$LAB_ROOT/report.txt"
echo "old target" > "$LAB_ROOT/live.conf"
ls -l "$LAB_ROOT"
echo "exit was: $?"
```

**Expected output:**

```
-rw-r--r--. 1 root root 10 ... report.txt
-rw-r--r--. 1 root root 11 ... live.conf
drwxr-xr-x. 2 root root  6 ... archive
exit was: 0
```

---

## TASK 1 of 2 — Idempotent move with `creates:` + `removes:`

**In plain English:** We write a guarded `command: mv` that runs once and skips cleanly on the re-run, then prove the outcome with `stat`.

---

### Step 1 of 2 — Write the guarded move playbook

**In plain English:** We create `task1.yml`, which moves a file into the archive and guards the command with both the destination (`creates:`) and the source (`removes:`).

```yaml
---
- name: "Lab 10b Task 1 — idempotent move"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    src: /tmp/lab-10/report.txt
    dst: /tmp/lab-10/archive/report.txt
  tasks:
    - name: "Move the file (idempotent via creates + removes)"
      ansible.builtin.command: "mv {{ src }} {{ dst }}"
      args:
        creates: "{{ dst }}"
        removes: "{{ src }}"
      register: move_result

    - name: "Show whether the move ran"
      ansible.builtin.debug:
        msg: "changed: {{ move_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.command: "mv {{ src }} {{ dst }}"` → Run the move; there is no `mv` module.
- `creates: "{{ dst }}"` + `removes: "{{ src }}"` → Skip the task if the destination already exists OR the source is already gone — together they make `mv` idempotent.
- `register:` + `debug:` → Report whether the move ran.

**New words in this step:**

- **`removes:`** — a guard that skips a command/shell task when the named path is absent.

---

### Step 2 of 2 — Run it twice and assert the outcome with `stat`

**In plain English:** We run the play twice; the first moves the file (`changed=1`), the second skips (`changed=0`), and we confirm the file now lives only in the archive.

```bash
ansible-playbook /root/rhcsa_journal/lab-10b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-10b/playbooks/task1.yml
test -e /tmp/lab-10/report.txt && echo "src STILL THERE (FAIL)" || echo "src gone (OK)"
test -e /tmp/lab-10/archive/report.txt && echo "dst present (OK)" || echo "dst MISSING (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
src gone (OK)
dst present (OK)
exit was: 0
```

**Line-by-line breakdown:**

- two runs → `changed=1` then `changed=0`; the guards make the second run a clean skip instead of a failure.
- the two `test -e` checks → Confirm the source is gone and the destination exists — a correct, complete move.

**New words in this step:**

- **double guard** — using `creates:` and `removes:` together to make a destructive command idempotent.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `creates:`+`removes:` | move idempotence | one guard alone is not enough |
| no `mv` module | use `command:` | a real module would be preferred if it existed |
| `stat`/`test -e` | assert outcome | verify both src gone and dst present |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Second run fails "no such file" | Only `creates:` used | Add `removes:` for the source |
| `changed=1` every run | No guards | Add both `creates:` and `removes:` |

---

## TASK 2 of 2 — Safe replace with `copy` + `backup`

**In plain English:** We replace a live file declaratively, keeping a timestamped backup — the idempotent alternative to `mv -b`.

---

### Step 1 of 2 — Write the backup-replace playbook

**In plain English:** We create `task2.yml`, which writes new content over `live.conf` and saves the old version with `backup: true`.

```yaml
---
- name: "Lab 10b Task 2 — safe replace with backup"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    target: /tmp/lab-10/live.conf
  tasks:
    - name: "Replace the file, keeping a backup"
      ansible.builtin.copy:
        dest: "{{ target }}"
        content: "new config v2\n"
        mode: '0644'
        backup: true
      register: replace_result

    - name: "Show change status and backup path"
      ansible.builtin.debug:
        msg:
          - "changed: {{ replace_result.changed }}"
          - "backup_file: {{ replace_result.backup_file | default('none') }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.copy: content:` + `backup: true` → Set the file's new contents; if it changed, save the prior version first.
- `register:` + `debug:` → Print whether it changed and the backup path.

**New words in this step:**

- **declarative replace** — using `copy` to set the final content rather than moving a file over it.

---

### Step 2 of 2 — Run it twice and watch `changed=0`, backup once

**In plain English:** We run the play twice; the first replaces and backs up (`changed=1`), the second matches and does nothing (`changed=0`).

```bash
ansible-playbook /root/rhcsa_journal/lab-10b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-10b/playbooks/task2.yml
cat /tmp/lab-10/live.conf
ls -1 /tmp/lab-10/live.conf*
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
new config v2
/tmp/lab-10/live.conf
/tmp/lab-10/live.conf.18-50-02.2026-06-15@...~
exit was: 0
```

**Line-by-line breakdown:**

- first run → Content differs, so it writes and creates a backup; `changed=1`.
- second run → Content already matches; `changed=0` and no new backup — idempotent.
- `ls -1 ...live.conf*` → Show the live file plus the one backup from the first run.

**New words in this step:**

- **idempotent replace** — `copy` only rewrites on drift, so backups are made only when something actually changes.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `copy` + `backup` | replace + safety copy | backup only on actual change |
| vs `command: mv -b` | declarative, idempotent | `mv -b` via command needs guards |
| `backup_file` | rollback path | empty when nothing changed |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Multiple backups pile up | Content keeps changing | Stabilize the desired content |
| No backup made | File already matched | Backups happen only on overwrite |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the guarded move playbook
- [ ] Task 1 · Step 2 — Run it twice and assert the outcome with `stat`
- [ ] Task 2 · Step 1 — Write the backup-replace playbook
- [ ] Task 2 · Step 2 — Run it twice and watch `changed=0`, backup once
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-10
rm -rf /root/rhcsa_journal/lab-10b
```

**Expected output:**

```
✅ Removed /tmp/lab-10 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `command: mv` with only `creates:` | Re-run fails when src gone | Add `removes:` too |
| Using `command: mv` to set content | Non-idempotent | Use `copy` + `backup` for replaces |
| Forgetting to read `backup_file` | No rollback path known | Register and debug it |

---

## 📌 Exam Strategy

When you must move with a raw command, guard it with both `creates:` and `removes:`. When you really mean "this file should have these contents," use `ansible.builtin.copy` with `backup: true` instead — it is idempotent and keeps a rollback. Re-run everything twice to confirm `changed=0`.

- The `creates:`+`removes:` pair is the move-idempotence pattern.
- Prefer a declarative replace over a `command: mv` when content is the goal.
- `backup: true` gives you a free rollback path.

---

## 🔗 Related Labs

- [Lab 10a — Moving and Renaming Files (RHCSA)](../lab-10a-moving-renaming-files-rhcsa/) — the `mv` flags this play mirrors
- [Lab 10c — Moving and Renaming Files (Verify)](../lab-10c-moving-renaming-files-verify/) — prove inode survival and no data loss
- [Lab 08b — Copying Files (Ansible)](../lab-08b-copying-files-ansible/) — `copy` + `backup` in the copy context

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
