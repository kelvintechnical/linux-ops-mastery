# Lab 05b: Directory Navigation (Ansible) — `chdir:`, `ansible.builtin.command`

**Series:** linux-ops-mastery — Essential Tools & File Operations · **Lab 05b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (running a command in a specific directory the right way), RHCSA EX200 (the `cd` behavior underneath), DevOps (path-correct automation)  
**Prerequisite:** [Lab 05a](../lab-05a-directory-navigation-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `pwd` (inside a task) | _Task 1 · Step 1_ |
| A2 | `ansible.builtin.command` | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `chdir:` task argument | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `creates:` guard | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N3 | `register:` + `stdout` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N4 | `changed_when: false` | Task 1 · Step 1 | _Task 1 · Step 1_ |

---

## 🎯 Objective

Learn the Ansible boundary that surprises everyone coming from the shell: **there is no `cd` module**, because a "current directory" is per-process state that does not persist between tasks. The honest equivalent is the `chdir:` argument on `command`/`shell`, which runs that one task inside a directory. You will prove a task's working directory with `pwd`, set it with `chdir:`, and make a directory-scoped action idempotent with `creates:`.

---

## 🧠 Concept

Each Ansible task spawns a fresh process. There is nothing to "change directory" into that would carry to the next task, so a `cd` module would be meaningless. Instead, `command:`/`shell:` accept `chdir:`, which sets the working directory **for that task only**. To keep such tasks idempotent you guard them: `creates:` skips the task when a target file already exists, so a re-run reports `changed=0`. Read-only checks use `changed_when: false` so they never pollute the recap.

```
SHELL (05a)                          ANSIBLE (05b)
─────────────────────────────       ──────────────────────────────────────
cd /tmp/lab-05 ; ls                  ansible.builtin.command: ls
                                       args: { chdir: /tmp/lab-05 }
cd /dir ; touch f   (not idempotent) command: touch f  args:{chdir,creates:f}
                                       └─ changed=0 once f exists
```

> **Why this matters:** Candidates lose points writing `cd /path && cmd` inside `shell:` when `chdir:` is the clean, documented way. Knowing why `cd` has no module is exactly the judgment the exam tests.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.command` | Run a binary with no shell | safest default; `>`/`|` are NOT interpreted |
| `chdir:` | Set the task's working directory | an `args:` key on command/shell |
| `creates:` | Skip the task if a path already exists | the idempotence guard for command/shell |
| `changed_when: false` | Mark a task as never "changed" | use for read-only checks like `pwd`/`ls` |
| `register:` | Capture `rc`/`stdout` for later | pair with `debug:` to read results |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox plus the durable playbook folder, and make a subdirectory we can target with `chdir:`.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-05
mkdir -p "$LAB_ROOT/work"
mkdir -p /root/rhcsa_journal/lab-05b/playbooks
ls -ld "$LAB_ROOT/work"
echo "exit was: $?"
```

**Expected output:**

```
drwxr-xr-x. 2 root root 6 Jun 15 18:15 /tmp/lab-05/work
exit was: 0
```

---

## TASK 1 of 2 — Prove `chdir:` is the real `cd`

**In plain English:** We run `pwd` as a task with and without `chdir:` to prove the working directory is per-task state set only by `chdir:`.

---

### Step 1 of 2 — Write the `chdir:` demonstration playbook

**In plain English:** We create `task1.yml`, which runs `pwd` twice — once with no directory set and once with `chdir:` pointing at the sandbox.

```yaml
---
- name: "Lab 05b Task 1 — chdir replaces cd"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    work_dir: /tmp/lab-05/work
  tasks:
    - name: "Run pwd with chdir set to the sandbox"
      ansible.builtin.command: pwd
      args:
        chdir: "{{ work_dir }}"
      register: with_chdir
      changed_when: false

    - name: "Show the working directory the task ran in"
      ansible.builtin.debug:
        msg: "task ran in: {{ with_chdir.stdout }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.command: pwd` → Run `pwd` with no shell; `command` is preferred when no shell features are needed.
- `args: chdir: "{{ work_dir }}"` → Set the task's working directory to the sandbox — this is the `cd` equivalent, scoped to this task only.
- `changed_when: false` → `pwd` reads state and changes nothing, so we keep the recap honest.
- `register:` + `debug:` → Capture and print `stdout` to prove which directory the task ran in.

**New words in this step:**

- **`chdir:`** — the task argument that sets the working directory for a single command/shell task.
- **`changed_when: false`** — declares a task never reports `changed`, correct for read-only checks.

---

### Step 2 of 2 — Run it and read the working directory

**In plain English:** We run the play and confirm the captured `pwd` output is the sandbox directory we set with `chdir:`.

```bash
ansible-playbook /root/rhcsa_journal/lab-05b/playbooks/task1.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Show the working directory the task ran in] ****************************
ok: [localhost] => {
    "msg": "task ran in: /tmp/lab-05/work"
}
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Run the play; the debug line prints `/tmp/lab-05/work`, proving `chdir:` set the CWD.
- PLAY RECAP `changed=0` → Because of `changed_when: false`, the read-only task never inflates the change count.

**New words in this step:**

- **`stdout`** — the captured standard output of a registered command task.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| no `cd` module | CWD is per-process | writing `cd /x && cmd` in `shell:` is the wrong reflex |
| `chdir:` | sets task CWD | it is under `args:`, not a top-level key |
| `changed_when: false` | read-only honesty | omitting it makes `command` always report changed |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `chdir` ignored | Put it at task level, not under `args:` | Nest `chdir:` under `args:` |
| Task always `changed` | `command` reports changed by default | Add `changed_when: false` for read-only |

---

## TASK 2 of 2 — Idempotent directory-scoped action with `creates:`

**In plain English:** We create a file inside a target directory using `chdir:` and guard it with `creates:` so a re-run does nothing.

---

### Step 1 of 2 — Write the guarded create playbook

**In plain English:** We create `task2.yml`, which runs `touch` inside the sandbox via `chdir:` and skips itself once the file exists thanks to `creates:`.

```yaml
---
- name: "Lab 05b Task 2 — directory-scoped, idempotent create"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    work_dir: /tmp/lab-05/work
  tasks:
    - name: "Create a marker file inside work_dir (idempotent via creates)"
      ansible.builtin.command: touch marker.txt
      args:
        chdir: "{{ work_dir }}"
        creates: "{{ work_dir }}/marker.txt"
      register: touch_result

    - name: "Show whether the task ran"
      ansible.builtin.debug:
        msg: "changed: {{ touch_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.command: touch marker.txt` → Create the file by relative name; `chdir:` makes the relative path resolve inside the sandbox.
- `creates: "{{ work_dir }}/marker.txt"` → If that file already exists, Ansible skips the task — the idempotence guard.
- `register:` + `debug:` → Print whether the task actually ran.

**New words in this step:**

- **`creates:`** — a guard that skips a command/shell task when the named path already exists.

---

### Step 2 of 2 — Run it twice and watch `changed=0` on the re-run

**In plain English:** We run the play twice; the first creates the file (`changed=1`), and the second is skipped by `creates:` (`changed=0`).

```bash
ansible-playbook /root/rhcsa_journal/lab-05b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-05b/playbooks/task2.yml
ls -l /tmp/lab-05/work/marker.txt
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
-rw-r--r--. 1 root root 0 Jun 15 18:16 /tmp/lab-05/work/marker.txt
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → File does not exist, so `touch` runs; `changed=1`.
- second `ansible-playbook ...` → `creates:` sees the file and skips the task; `changed=0` — the idempotence proof.
- `ls -l ...` → Confirm the marker exists at the sandbox path.

**New words in this step:**

- **guarded task** — a command/shell task made idempotent by `creates:` or `removes:`.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `creates:` | skip if path exists | give the FULL path, not a relative name |
| `chdir:` + relative cmd | resolves paths in the target dir | without `chdir:`, relatives hit the wrong dir |
| `command` vs `shell` | command has no shell | use `shell:` only for `>`/`|`/globs |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `changed=1` every run | `creates:` path wrong/relative | Use the absolute target path |
| File created in wrong place | `chdir:` not set | Add `chdir:` so relatives resolve correctly |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the `chdir:` demonstration playbook
- [ ] Task 1 · Step 2 — Run it and read the working directory
- [ ] Task 2 · Step 1 — Write the guarded create playbook
- [ ] Task 2 · Step 2 — Run it twice and watch `changed=0` on the re-run
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-05
rm -rf /root/rhcsa_journal/lab-05b
```

**Expected output:**

```
✅ Removed /tmp/lab-05 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Writing `cd /x && cmd` in `shell:` | Works but is non-idiomatic and fragile | Use `command:` with `chdir:` |
| Expecting CWD to persist between tasks | Second task is in the wrong dir | Set `chdir:` on each task that needs it |
| Relative `creates:` path | Re-run still reports changed | Use the absolute path in `creates:` |

---

## 📌 Exam Strategy

When a task must run "in a directory," reach for `chdir:`, not a `cd` inside `shell:`. Pair any file-creating command with `creates:` so the play is idempotent, and mark read-only commands `changed_when: false`. These three habits keep your PLAY RECAP honest.

- `chdir:` lives under `args:` — memorize the nesting.
- `creates:`/`removes:` are the only way to make raw commands idempotent.
- Prefer real modules (`file`, `copy`) over `command:` whenever one exists.

---

## 🔗 Related Labs

- [Lab 05a — Directory Navigation (RHCSA)](../lab-05a-directory-navigation-rhcsa/) — the `cd`/`pwd` reflexes this play replaces
- [Lab 05c — Directory Navigation (Verify)](../lab-05c-directory-navigation-verify/) — prove path behavior with hard evidence
- [Lab 01b — Stdout Redirection (Ansible)](../lab-01b-stdout-redirection-ansible/) — the `shell:` vs module boundary, same lesson

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
