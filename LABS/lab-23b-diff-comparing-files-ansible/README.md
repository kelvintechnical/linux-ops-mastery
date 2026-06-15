# Lab 23b: Comparing File Differences (Ansible) — `--check --diff`, `diff:` mode

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 23b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (preview changes safely with check/diff mode), RHCSA EX200 (the `diff` behavior underneath), DevOps (dry-run review)  
**Prerequisite:** [Lab 23a](../lab-23a-diff-comparing-files-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | unified diff format | _Task 1 · Step 2_ |
| A2 | `ansible.builtin.copy` | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `--check` (dry run) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N2 | `--diff` (show changes) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `command: diff` with `failed_when` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `diff` rc handling (0/1/2) | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

Preview changes before you make them — the safest habit in automation. You will run a `copy` task in `--check --diff` mode to see the unified diff of what *would* change without touching the file, then run a `command: diff` inside a play with proper exit-code handling to compare two files programmatically. This is dry-run review, the Ansible way.

---

## 🧠 Concept

Ansible has `diff` built in. `--check` is a dry run: modules report what they *would* do but make no changes. `--diff` prints the unified diff of file-content modules (`copy`, `template`, `lineinfile`). Together (`--check --diff`) you get a no-risk preview — exactly the RHCE habit of "show me before you do it." Separately, when you need to compare two arbitrary files inside a play, `command: diff a b` works, but `diff` returns rc 1 for "differ," so you must set `failed_when: result.rc not in [0,1]` so a normal difference isn't treated as a failure.

```
SHELL (23a)                          ANSIBLE (23b)
─────────────────────────────       ──────────────────────────────────────
diff -u current proposed            ansible-playbook task1.yml --check --diff
                                       └─ shows the would-be unified diff, no write
diff a b; echo $?                    command: diff a b   (failed_when rc not in [0,1])
```

> **Why this matters:** Running `--check --diff` before a real apply prevents surprises on production configs. And knowing `diff` rc 1 ≠ failure keeps comparison tasks from aborting good plays.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `--check` | Dry run, no changes | combine with `--diff` |
| `--diff` | Show unified diffs | for content modules |
| `ansible.builtin.copy` | Manage file content | diff-aware |
| `command: diff` | Compare two files | guard rc with `failed_when` |
| `failed_when:` | Exit-code policy | `rc not in [0,1]` |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and playbook folder with a baseline config and a proposed version.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-23
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-23b/playbooks
printf 'LogLevel INFO\nPort 22\n'   > "$LAB_ROOT/current.conf"
printf 'LogLevel DEBUG\nPort 22\n'  > "$LAB_ROOT/proposed.conf"
ls "$LAB_ROOT"
echo "exit was: $?"
```

**Expected output:**

```
current.conf
proposed.conf
exit was: 0
```

---

## TASK 1 of 2 — Preview with `--check --diff`

**In plain English:** We write a copy task and preview its change before applying it.

---

### Step 1 of 2 — Write the copy playbook

**In plain English:** We create `task1.yml`, which manages `current.conf` so its `LogLevel` becomes DEBUG.

```yaml
---
- name: "Lab 23b Task 1 — manage config content"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    conf: /tmp/lab-23/current.conf
  tasks:
    - name: "Ensure the config has the desired content"
      ansible.builtin.copy:
        dest: "{{ conf }}"
        content: |
          LogLevel DEBUG
          Port 22
        mode: '0644'
      register: copy_result
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.copy: content:` → Declare the desired file content; the module diffs it against the current file.

**New words in this step:**

- **declared content** — the target state `copy` compares against and converges to.

---

### Step 2 of 2 — Preview, then apply

**In plain English:** We run with `--check --diff` to see the change safely, then run for real and confirm idempotence.

```bash
cd /root/rhcsa_journal/lab-23b/playbooks
ansible-playbook task1.yml --check --diff
ansible-playbook task1.yml
ansible-playbook task1.yml
echo "exit was: $?"
```

**Expected output:**

```
--- before: /tmp/lab-23/current.conf
+++ after
@@ -1,2 +1,2 @@
-LogLevel INFO
+LogLevel DEBUG
 Port 22
changed: [localhost]   (check mode — no file written)

PLAY RECAP (real run 1)  : ok=1  changed=1  ...
PLAY RECAP (real run 2)  : ok=1  changed=0  ...
exit was: 0
```

**Line-by-line breakdown:**

- `--check --diff` → Shows the unified diff of the would-be change **without writing** the file.
- real run 1 → Applies the change (`changed=1`).
- real run 2 → No change needed (`changed=0`), proving idempotence.

**New words in this step:**

- **`--check`** — dry run; modules report intent, make no changes.
- **`--diff`** — print the unified diff of content changes.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `--check` | dry run | some modules can't predict fully |
| `--diff` | show content diff | works on file modules |
| copy idempotence | re-run `changed=0` | content must match exactly |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| No diff shown | Module not diff-aware | Use file-content modules |
| Check mode "changed" but no file | That's correct | It's a preview only |

---

## TASK 2 of 2 — Compare two files in a play

**In plain English:** We run `diff` inside a play with correct exit-code handling and assert on the result.

---

### Step 1 of 2 — Write the diff playbook

**In plain English:** We create `task2.yml`, which diffs `current.conf` against `proposed.conf` and treats rc 1 (differ) as normal.

```yaml
---
- name: "Lab 23b Task 2 — compare two files"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    a: /tmp/lab-23/current.conf
    b: /tmp/lab-23/proposed.conf
  tasks:
    - name: "Diff the two files"
      ansible.builtin.command: "diff -u {{ a }} {{ b }}"
      register: diff_out
      changed_when: false
      failed_when: diff_out.rc not in [0, 1]

    - name: "Report identical or different"
      ansible.builtin.debug:
        msg: "{{ 'identical' if diff_out.rc == 0 else 'differ' }}"

    - name: "Show the unified diff if any"
      ansible.builtin.debug:
        var: diff_out.stdout_lines
      when: diff_out.rc == 1
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `command: diff -u {{ a }} {{ b }}` → Compare the two files, capturing the unified diff.
- `failed_when: diff_out.rc not in [0, 1]` → Treat "differ" (rc 1) as success; only rc ≥ 2 (real error) fails.
- `when: diff_out.rc == 1` → Only print the diff when the files actually differ.

**New words in this step:**

- **`diff` rc handling** — accepting rc 0/1 and failing only on rc 2.

---

### Step 2 of 2 — Run it and read the result

**In plain English:** We run the play and confirm it reports the difference without failing.

```bash
ansible-playbook /root/rhcsa_journal/lab-23b/playbooks/task2.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Report identical or different] *************************************
ok: [localhost] => {"msg": "differ"}
TASK [Show the unified diff if any] *************************************
ok: [localhost] => {"diff_out.stdout_lines": ["--- ...", "-LogLevel INFO", "+LogLevel DEBUG", ...]}
PLAY RECAP **********************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Reports "differ" and shows the diff; `failed=0` proves rc 1 was handled gracefully.

**New words in this step:**

- **graceful diff** — a comparison task that reports differences without aborting the play.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `failed_when rc not in [0,1]` | accept "differ" | default treats 1 as fail |
| `changed_when: false` | read-only | diff changes nothing |
| `when: rc == 1` | conditional output | only show real diffs |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Play fails on difference | Default rc handling | Add `failed_when: rc not in [0,1]` |
| Always shows diff block | Missing `when:` | Gate on `rc == 1` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the copy playbook
- [ ] Task 1 · Step 2 — Preview, then apply
- [ ] Task 2 · Step 1 — Write the diff playbook
- [ ] Task 2 · Step 2 — Run it and read the result
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-23
rm -rf /root/rhcsa_journal/lab-23b
```

**Expected output:**

```
✅ Removed /tmp/lab-23 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Skipping `--check --diff` | Surprise changes | Always preview first |
| `diff` rc 1 unhandled | Play aborts | `failed_when: rc not in [0,1]` |
| Reads marked changed | Missing `changed_when: false` | Add it |

---

## 📌 Exam Strategy

Preview every risky change with `--check --diff`, and when comparing files in a play, handle `diff`'s rc 1 as "differ," not failure. Dry-run review is the difference between confident and reckless automation.

- `--check --diff` shows the unified diff with zero risk.
- `failed_when: rc not in [0,1]` for any `diff` command.
- Gate diff output with `when: rc == 1`.

---

## 🔗 Related Labs

- [Lab 23a — Comparing File Differences (RHCSA)](../lab-23a-diff-comparing-files-rhcsa/) — the `diff` formats this builds on
- [Lab 23c — Comparing File Differences (Verify)](../lab-23c-diff-comparing-files-verify/) — prove identity and drift
- [Lab 22b — Filtering with grep and Regex (Ansible)](../lab-22b-grep-regex-ansible/) — idempotent config edits

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
