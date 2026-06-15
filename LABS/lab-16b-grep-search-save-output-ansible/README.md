# Lab 16b: Search for a String and Save Output (Ansible) — `command: grep`, `ansible.builtin.lineinfile`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 16b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (capturing command output and editing config lines idempotently), RHCSA EX200 (the `grep` behavior underneath), DevOps (config assertions)  
**Prerequisite:** [Lab 16a](../lab-16a-grep-search-save-output-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `grep` (via command) | _Task 1 · Step 1_ |
| A2 | `ansible.builtin.copy` | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `command:` + `register` + `changed_when: false` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `stdout_lines` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `ansible.builtin.lineinfile` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `failed_when:` (grep rc) | Task 1 · Step 1 | _Task 1 · Step 1_ |

---

## 🎯 Objective

Search and capture the Ansible way. You will run `grep` through `command:` as a read-only check (registering its output and taming its exit codes), save the matches with `ansible.builtin.copy`, then switch to the *right* tool for editing a config — `ansible.builtin.lineinfile`, which idempotently ensures a setting exists. Run twice to prove `changed=0`.

---

## 🧠 Concept

`grep` is a read-only filter, so when you run it via `command:` you set `changed_when: false`. But `grep` returns exit code `1` when it finds nothing — which Ansible treats as failure — so you guard with `failed_when:` to accept rc 0 or 1. To persist results, feed the registered `stdout` into `ansible.builtin.copy`. For *changing* a config, do not shell out — `ansible.builtin.lineinfile` ensures a single line matches a regex idempotently, the declarative replacement for `grep`-then-`sed`.

```
SHELL (16a)                          ANSIBLE (16b)
─────────────────────────────       ──────────────────────────────────────
grep -i error app.log > out          command: grep ... (register, changed_when:false)
                                       copy: content="{{ result.stdout }}"
grep + sed to set a line             lineinfile: regexp=... line=... (idempotent)
```

> **Why this matters:** Running `grep` in a play without `changed_when:`/`failed_when:` produces noisy recaps and spurious failures. Knowing when to *read* (command + grep) versus *change* (lineinfile) is the core exam judgment.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.command` | Run `grep` (read-only) | pair with `changed_when:`/`failed_when:` |
| `changed_when: false` | Mark a read-only task | keeps the recap honest |
| `failed_when:` | Accept grep rc 0 or 1 | `result.rc not in [0,1]` |
| `ansible.builtin.copy` | Save registered output | `content: "{{ result.stdout }}"` |
| `ansible.builtin.lineinfile` | Idempotently ensure a line | `regexp:` + `line:` |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and playbook folder, and seed a log and a config to search and edit.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-16
mkdir -p "$LAB_ROOT/conf"
mkdir -p /root/rhcsa_journal/lab-16b/playbooks
printf 'INFO start\nERROR disk full\ninfo retry\nERROR timeout\n' > "$LAB_ROOT/app.log"
printf 'Port 22\n' > "$LAB_ROOT/conf/sshd_config"
ls -l "$LAB_ROOT"
echo "exit was: $?"
```

**Expected output:**

```
-rw-r--r--. 1 root root 41 ... app.log
drwxr-xr-x. 2 root root 24 ... conf
exit was: 0
```

---

## TASK 1 of 2 — Capture grep output safely

**In plain English:** We run `grep` as a read-only check, guard its exit code, and save the matches with `copy`.

---

### Step 1 of 2 — Write the grep-and-capture playbook

**In plain English:** We create `task1.yml`, which greps for errors, accepts the "no match" exit code, and writes the hits to a results file.

```yaml
---
- name: "Lab 16b Task 1 — capture grep output"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    log: /tmp/lab-16/app.log
    out: /tmp/lab-16/errors.txt
  tasks:
    - name: "Search for ERROR lines (read-only)"
      ansible.builtin.command: "grep -in error {{ log }}"
      register: grep_result
      changed_when: false
      failed_when: "grep_result.rc not in [0, 1]"

    - name: "Save the matches to a results file"
      ansible.builtin.copy:
        dest: "{{ out }}"
        content: "{{ grep_result.stdout }}\n"
        mode: '0644'
      register: save_result

    - name: "Show counts"
      ansible.builtin.debug:
        msg:
          - "matches: {{ grep_result.stdout_lines | length }}"
          - "saved changed: {{ save_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `command: grep ...` + `changed_when: false` → Run grep as a read-only search; it never "changes" the host.
- `failed_when: "grep_result.rc not in [0, 1]"` → Treat rc 1 (no match) as success, failing only on real errors (rc ≥ 2).
- `copy: content: "{{ grep_result.stdout }}\n"` → Persist the captured matches idempotently.

**New words in this step:**

- **`failed_when:`** — override what counts as task failure, here accepting grep's "no match" code.

---

### Step 2 of 2 — Run it twice and watch the capture converge

**In plain English:** We run the play twice; the search never changes, and the save converges to `changed=0` once the results file matches.

```bash
ansible-playbook /root/rhcsa_journal/lab-16b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-16b/playbooks/task1.yml
cat /tmp/lab-16/errors.txt
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=3    changed=1    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
2:ERROR disk full
4:ERROR timeout
exit was: 0
```

**Line-by-line breakdown:**

- two runs → The grep stays `changed=0`; the copy is `changed=1` then `changed=0` once the file matches.
- `cat errors.txt` → Confirm the saved matches.

**New words in this step:**

- **`stdout_lines`** — the registered stdout split into a list, handy for counting.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `changed_when: false` | read-only honesty | grep via command is "changed" by default |
| `failed_when:` rc | accept no-match | grep rc 1 ≠ failure |
| `copy` of stdout | persist results | idempotent on re-run |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Play fails on no match | grep rc 1 unhandled | Add `failed_when:` accepting rc 1 |
| Results task always changed | trailing newline drift | Keep `content:` stable |

---

## TASK 2 of 2 — Edit a config idempotently with `lineinfile`

**In plain English:** We ensure a setting exists in a config file using the right module, then prove it converges.

---

### Step 1 of 2 — Write the lineinfile playbook

**In plain English:** We create `task2.yml`, which ensures `PermitRootLogin no` is present, replacing any existing `PermitRootLogin` line.

```yaml
---
- name: "Lab 16b Task 2 — ensure a config setting"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    cfg: /tmp/lab-16/conf/sshd_config
  tasks:
    - name: "Ensure PermitRootLogin is set to no"
      ansible.builtin.lineinfile:
        path: "{{ cfg }}"
        regexp: '^#?PermitRootLogin'
        line: 'PermitRootLogin no'
        create: true
        mode: '0644'
      register: line_result

    - name: "Show whether the line changed"
      ansible.builtin.debug:
        msg: "changed: {{ line_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `regexp: '^#?PermitRootLogin'` → Match an existing setting (commented or not) so it is replaced, not duplicated.
- `line: 'PermitRootLogin no'` → The exact line that must end up present.
- `create: true` → Create the file if it does not exist.

**New words in this step:**

- **`ansible.builtin.lineinfile`** — ensure exactly one line matching a regex is present in a file.

---

### Step 2 of 2 — Run it twice and watch `changed=0`

**In plain English:** We run the play twice; the first adds/replaces the line, the second finds it already correct.

```bash
ansible-playbook /root/rhcsa_journal/lab-16b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-16b/playbooks/task2.yml
grep PermitRootLogin /tmp/lab-16/conf/sshd_config
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
PermitRootLogin no
exit was: 0
```

**Line-by-line breakdown:**

- two runs → `changed=1` then `changed=0` — the line is set once and then stable.
- `grep PermitRootLogin ...` → Confirm exactly one correct line.

**New words in this step:**

- **idempotent edit** — `lineinfile` only writes when the line is missing or different.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `lineinfile regexp` | match line to replace | omit it and you duplicate lines |
| `create: true` | make file if absent | default is to fail on missing file |
| idempotent edit | re-run `changed=0` | shelling `sed` would not be |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Duplicate lines added | No/loose `regexp` | Anchor the regexp |
| `file not found` | `create:` missing | Add `create: true` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the grep-and-capture playbook
- [ ] Task 1 · Step 2 — Run it twice and watch the capture converge
- [ ] Task 2 · Step 1 — Write the lineinfile playbook
- [ ] Task 2 · Step 2 — Run it twice and watch `changed=0`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-16
rm -rf /root/rhcsa_journal/lab-16b
```

**Expected output:**

```
✅ Removed /tmp/lab-16 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| grep via command with no guards | Spurious failure/changed | Add `failed_when:`/`changed_when:` |
| `sed` shell-out to edit | Non-idempotent | Use `lineinfile` |
| Loose `regexp` | Duplicate config lines | Anchor with `^` |

---

## 📌 Exam Strategy

Read with `command: grep` (guarded), change with `lineinfile`. Register grep's output, accept rc 1, and save with `copy`. Use anchored regexes in `lineinfile` so settings are replaced, not duplicated, and re-run to confirm `changed=0`.

- Always guard `command: grep` with `changed_when:` and `failed_when:`.
- `lineinfile` is the idempotent way to set a config line.
- Anchor regexes (`^`) to avoid duplicates.

---

## 🔗 Related Labs

- [Lab 16a — Search and Save Output (RHCSA)](../lab-16a-grep-search-save-output-rhcsa/) — the hand-typed `grep`/`tee` this mirrors
- [Lab 16c — Search and Save Output (Verify)](../lab-16c-grep-search-save-output-verify/) — prove the saved results are correct
- [Lab 24b — Stream Editing with sed (Ansible)](../lab-24b-sed-stream-editor-ansible/) — `replace`/`lineinfile` vs shelling out to `sed`

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
