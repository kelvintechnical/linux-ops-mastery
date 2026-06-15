# Lab 17b: Find and Save Config Files (Ansible) — `ansible.builtin.find`, `ansible.builtin.copy`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 17b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (structured file discovery, acting on results), RHCSA EX200 (the `find` behavior underneath), DevOps (config inventory as data)  
**Prerequisite:** [Lab 17a](../lab-17a-find-save-config-files-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `find` (by name/type) | _Task 1 · Step 1_ |
| A2 | `ansible.builtin.copy` | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `ansible.builtin.find` `patterns:` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `file_type:` / `use_regex:` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `map(attribute='path')` filter | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N4 | `loop:` over found files | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

Replace shell `find` with `ansible.builtin.find`, which returns a **structured list** instead of text you must parse. You will discover `.conf` files by pattern and type, save the paths with `ansible.builtin.copy`, then loop over the results to act on each one. Structured data is what makes Ansible discovery safe and composable.

---

## 🧠 Concept

`ansible.builtin.find` takes `paths:`, `patterns:` (globs or, with `use_regex: true`, regexes), `file_type:`, `age:`, `size:`, and returns `files` (a list of dicts) plus `matched`. You extract paths with the Jinja `map(attribute='path')` filter and persist them with `copy`. Because the result is data, you can `loop:` over `find_result.files` to act on each — no fragile `for` loop parsing `find` output. The module also skips permission errors quietly, so there is no `2>/dev/null` to remember.

```
SHELL (17a)                          ANSIBLE (17b)
─────────────────────────────       ──────────────────────────────────────
find etc -type f -name '*.conf'      find: paths=etc patterns='*.conf' file_type=file
  > list.txt                         copy: content="{{ files|map('path')|join('\n') }}"
for f in $(find ...); do ...         loop: "{{ find_result.files }}"
```

> **Why this matters:** Parsing `find` text breaks on spaces and newlines in names. `ansible.builtin.find` returns clean structured data — the safe, exam-correct way to discover and act on files.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.find` | Structured file discovery | `patterns:`, `file_type:`, `use_regex:` |
| `map(attribute='path')` | Pull paths from result dicts | chain with `list`/`join` |
| `ansible.builtin.copy` | Save the path list | `content:` from the joined paths |
| `loop:` | Iterate the found files | `loop: "{{ result.files }}"` |
| `register:` + `debug:` | Inspect `matched`/`files` | read structured output |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and playbook folder with a tree of mixed config files.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-17
mkdir -p "$LAB_ROOT/etc/app" "$LAB_ROOT/etc/svc"
mkdir -p /root/rhcsa_journal/lab-17b/playbooks
echo a > "$LAB_ROOT/etc/app/app.conf"
echo b > "$LAB_ROOT/etc/svc/svc.conf"
echo c > "$LAB_ROOT/etc/svc/notes.txt"
ls -R "$LAB_ROOT/etc"
echo "exit was: $?"
```

**Expected output:**

```
/tmp/lab-17/etc/app:
app.conf
...
exit was: 0
```

---

## TASK 1 of 2 — Discover and save the path list

**In plain English:** We find `.conf` files with the module and save their paths with `copy`.

---

### Step 1 of 2 — Write the find-and-save playbook

**In plain English:** We create `task1.yml`, which discovers regular `.conf` files recursively and writes the joined paths to a file.

```yaml
---
- name: "Lab 17b Task 1 — discover and save config paths"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    root: /tmp/lab-17/etc
    out: /tmp/lab-17/configs.txt
  tasks:
    - name: "Find all .conf regular files"
      ansible.builtin.find:
        paths: "{{ root }}"
        patterns: "*.conf"
        file_type: file
        recurse: true
      register: find_result

    - name: "Save the paths to a list file"
      ansible.builtin.copy:
        dest: "{{ out }}"
        content: "{{ find_result.files | map(attribute='path') | sort | join('\n') }}\n"
        mode: '0644'
      register: save_result

    - name: "Show count and changed"
      ansible.builtin.debug:
        msg:
          - "matched: {{ find_result.matched }}"
          - "changed: {{ save_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.find: patterns: "*.conf" file_type: file recurse: true` → Discover regular `.conf` files through the whole tree.
- `content: "{{ find_result.files | map(attribute='path') | sort | join('\n') }}\n"` → Turn the list of dicts into sorted newline-joined paths.
- `register:` + `debug:` → Report the match count and whether the file changed.

**New words in this step:**

- **`ansible.builtin.find`** — structured filesystem discovery returning a list of file dicts.
- **`map(attribute='path')`** — pull the `path` field out of each result dict.

---

### Step 2 of 2 — Run it twice and confirm the list

**In plain English:** We run the play twice; discovery is read-only, and the saved list converges to `changed=0`.

```bash
ansible-playbook /root/rhcsa_journal/lab-17b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-17b/playbooks/task1.yml
cat /tmp/lab-17/configs.txt
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=3    changed=1    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
/tmp/lab-17/etc/app/app.conf
/tmp/lab-17/etc/svc/svc.conf
exit was: 0
```

**Line-by-line breakdown:**

- two runs → `find` never changes; the saved list is `changed=1` then `changed=0`.
- `cat configs.txt` → Confirm both `.conf` paths, sorted.

**New words in this step:**

- **`matched`** — the count of files `find` returned.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `find` module | structured data | no `2>/dev/null` needed |
| `map(attribute=)` | extract a field | returns a generator — chain `list`/`join` |
| `sort` filter | stable order | unsorted output flips `changed` |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `matched: 0` | `recurse` off / wrong path | Set `recurse: true`, check `paths:` |
| Re-run always changed | Unsorted join | Add `| sort` for stable output |

---

## TASK 2 of 2 — Act on each found file with `loop:`

**In plain English:** We loop over the discovered files to normalize their permissions.

---

### Step 1 of 2 — Write the loop-and-act playbook

**In plain English:** We create `task2.yml`, which finds the `.conf` files and sets each to mode 0640 in a loop.

```yaml
---
- name: "Lab 17b Task 2 — normalize permissions on found configs"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    root: /tmp/lab-17/etc
  tasks:
    - name: "Find the .conf files"
      ansible.builtin.find:
        paths: "{{ root }}"
        patterns: "*.conf"
        file_type: file
        recurse: true
      register: find_result

    - name: "Set each config to 0640"
      ansible.builtin.file:
        path: "{{ item.path }}"
        mode: '0640'
      loop: "{{ find_result.files }}"
      loop_control:
        label: "{{ item.path }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `register: find_result` → Capture the discovered files.
- `loop: "{{ find_result.files }}"` → Iterate over each file dict; `item.path` is the path.
- `loop_control: label:` → Print a clean per-item label instead of the whole dict.

**New words in this step:**

- **`loop:`** — run a task once per element of a list.
- **`loop_control: label:`** → tidy the per-iteration output.

---

### Step 2 of 2 — Run it twice and confirm convergence

**In plain English:** We run the play twice; the first sets modes (`changed`), the second finds them already correct.

```bash
ansible-playbook /root/rhcsa_journal/lab-17b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-17b/playbooks/task2.yml
stat -c '%a %n' /tmp/lab-17/etc/app/app.conf /tmp/lab-17/etc/svc/svc.conf
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
640 /tmp/lab-17/etc/app/app.conf
640 /tmp/lab-17/etc/svc/svc.conf
exit was: 0
```

**Line-by-line breakdown:**

- two runs → Modes are set once (`changed`), then stable (`changed=0`).
- `stat -c '%a %n' ...` → Confirm both configs are mode 640.

**New words in this step:**

- **convergent loop** — looping a state-aware module so re-runs settle to `changed=0`.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `loop:` over `files` | act on each result | `item.path`, not `item` |
| `file: mode:` | declarative perms | string `'0640'` keeps leading zero |
| `loop_control` | clean output | huge dicts spam the log otherwise |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `item is undefined` | Wrong loop var | Use `item.path` |
| Loop output unreadable | No `label:` | Add `loop_control: label:` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the find-and-save playbook
- [ ] Task 1 · Step 2 — Run it twice and confirm the list
- [ ] Task 2 · Step 1 — Write the loop-and-act playbook
- [ ] Task 2 · Step 2 — Run it twice and confirm convergence
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-17
rm -rf /root/rhcsa_journal/lab-17b
```

**Expected output:**

```
✅ Removed /tmp/lab-17 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Parsing shell `find` text | Breaks on spaces/newlines | Use the `find` module |
| Unsorted `join` | Re-run flips `changed` | Add `| sort` |
| Looping over `result` not `.files` | Type error | `loop: "{{ result.files }}"` |

---

## 📌 Exam Strategy

Use `ansible.builtin.find` to discover, then `loop:` to act — never parse shell `find` output. Sort joined paths for idempotent saves, and use `loop_control: label:` to keep logs readable.

- The `find` module returns data; treat results as a list of dicts.
- Sort before saving to keep `changed=0` on re-runs.
- `loop` + a state-aware module converges cleanly.

---

## 🔗 Related Labs

- [Lab 17a — Find and Save Config Files (RHCSA)](../lab-17a-find-save-config-files-rhcsa/) — the shell `find` this play mirrors
- [Lab 17c — Find and Save Config Files (Verify)](../lab-17c-find-save-config-files-verify/) — prove the list and permissions
- [Lab 07b — Touch Timestamps (Ansible)](../lab-07b-touch-timestamps-ansible/) — `ansible.builtin.find` by age

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
