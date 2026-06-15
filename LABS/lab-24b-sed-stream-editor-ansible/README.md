# Lab 24b: Stream Editing with sed (Ansible) — `replace`, `lineinfile`, idempotence

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 24b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (idempotent text edits the Ansible way), RHCSA EX200 (the `sed` behavior underneath), DevOps (config convergence)  
**Prerequisite:** [Lab 24a](../lab-24a-sed-stream-editor-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `sed s///` substitution | _Task 1 · Step 1_ |
| A2 | `ansible.builtin.replace` | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | why `sed -i` is non-idempotent | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `ansible.builtin.lineinfile` `state: absent` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `replace` for global edits | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `validate:` safe-config gate | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

Do `sed` edits the idempotent way. You will remove comment lines with `lineinfile state: absent`, replace text globally with `ansible.builtin.replace`, and add a `validate:` step so a bad edit can't be saved. The theme: a raw `sed -i` re-applies blindly every run, while these modules converge to a state and report `changed=0` once it's reached.

---

## 🧠 Concept

`sed -i 's/x/y/'` is not idempotent in spirit: it runs every time and, with the wrong pattern, can keep "changing" or corrupt a file silently. Ansible replaces it with stateful modules. `ansible.builtin.replace` does a global regex substitution like `sed s///g`, but only writes when the file isn't already in the target state. `ansible.builtin.lineinfile` with `regexp:` + `state: absent` removes matching lines (like `sed '/re/d'`) idempotently. Critically, both support `validate:` — a command (with `%s` for the temp file) that must succeed before the change is committed, so a syntactically broken config is never written.

```
SHELL (24a)                          ANSIBLE (24b)
─────────────────────────────       ──────────────────────────────────────
sed -i '/^#/d' f                     lineinfile: regexp='^#' state=absent
sed -i 's/INFO/DEBUG/g' f            replace: regexp='INFO' replace='DEBUG'
(no safety check)                    + validate: 'somecmd -t %s'  (gate the write)
```

> **Why this matters:** RHCE expects idempotent, *safe* config edits. `validate:` is what stops you from saving a broken sshd/sudoers file — the single most valuable habit in this lab.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.replace` | Global regex substitute | `regexp:`, `replace:` |
| `ansible.builtin.lineinfile` | Ensure/remove a line | `state: absent`, `regexp:` |
| `validate:` | Gate the write | `%s` = temp file |
| `backup: true` | Keep a backup | timestamped copy |
| `register:` + re-run | Prove idempotence | `changed=0` second time |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and playbook folder with a config to edit safely.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-24
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-24b/playbooks
cat > "$LAB_ROOT/app.conf" <<'EOF'
# header comment
# another comment
LogLevel INFO
mode INFO
retries 3
EOF
cat "$LAB_ROOT/app.conf"
echo "exit was: $?"
```

**Expected output:**

```
# header comment
# another comment
LogLevel INFO
mode INFO
retries 3
exit was: 0
```

---

## TASK 1 of 2 — Remove lines idempotently

**In plain English:** We strip comment lines with `lineinfile state: absent` and prove a re-run is `changed=0`.

---

### Step 1 of 2 — Write the remove-comments playbook

**In plain English:** We create `task1.yml`, which removes every comment line idempotently.

```yaml
---
- name: "Lab 24b Task 1 — remove comment lines"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    conf: /tmp/lab-24/app.conf
  tasks:
    - name: "Remove all comment lines (like sed '/^#/d')"
      ansible.builtin.lineinfile:
        path: "{{ conf }}"
        regexp: '^#'
        state: absent
        backup: true
      register: rm_result

    - name: "Show whether anything changed"
      ansible.builtin.debug:
        msg: "changed: {{ rm_result.changed }} ({{ rm_result.found }} matched)"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `regexp: '^#'` + `state: absent` → Remove every line starting with `#`, the idempotent `sed '/^#/d'`.
- `backup: true` → Keep a backup before editing.
- `rm_result.found` → How many lines matched and were removed.

**New words in this step:**

- **`lineinfile state: absent`** — remove matching lines idempotently.

---

### Step 2 of 2 — Run it twice and watch `changed=0`

**In plain English:** We run the play twice; comments are removed once, then nothing is left to remove.

```bash
ansible-playbook /root/rhcsa_journal/lab-24b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-24b/playbooks/task1.yml
cat /tmp/lab-24/app.conf
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
LogLevel INFO
mode INFO
retries 3
exit was: 0
```

**Line-by-line breakdown:**

- two runs → `changed=1` then `changed=0`: once comments are gone, the module has nothing to do.
- `cat app.conf` → Confirms the comment lines are removed.

**New words in this step:**

- **convergence** — repeated runs settle at `changed=0` once the target state holds.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `state: absent` | remove lines | re-run is `changed=0` |
| `found` | match count | useful for reporting |
| vs `sed -i` | stateful vs blind | sed re-runs every time |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Always `changed` | regexp also matches new content | Tighten the regexp |
| Removed too much | Loose regexp | Anchor it (`^#`) |

---

## TASK 2 of 2 — Global replace with validation

**In plain English:** We substitute INFO→DEBUG globally and gate the write with `validate:`.

---

### Step 1 of 2 — Write the replace+validate playbook

**In plain English:** We create `task2.yml`, which replaces INFO with DEBUG everywhere and only saves if a validation command passes.

```yaml
---
- name: "Lab 24b Task 2 — global replace with validation"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    conf: /tmp/lab-24/app.conf
  tasks:
    - name: "Replace INFO with DEBUG everywhere (validated)"
      ansible.builtin.replace:
        path: "{{ conf }}"
        regexp: 'INFO'
        replace: 'DEBUG'
        backup: true
        validate: 'grep -q DEBUG %s'
      register: rep_result

    - name: "Show whether anything changed"
      ansible.builtin.debug:
        msg: "changed: {{ rep_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `regexp: 'INFO'` / `replace: 'DEBUG'` → Global substitution like `sed s/INFO/DEBUG/g`.
- `validate: 'grep -q DEBUG %s'` → Ansible writes to a temp file, runs the command with `%s` = that temp path, and only commits if it succeeds — the safety gate.

**New words in this step:**

- **`validate:`** — a command that must pass before the edited file is committed.

---

### Step 2 of 2 — Run it twice and confirm idempotence

**In plain English:** We run the play twice; INFO is replaced once, then there is no INFO left to change.

```bash
ansible-playbook /root/rhcsa_journal/lab-24b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-24b/playbooks/task2.yml
grep -E 'INFO|DEBUG' /tmp/lab-24/app.conf
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
LogLevel DEBUG
mode DEBUG
exit was: 0
```

**Line-by-line breakdown:**

- two runs → `changed=1` then `changed=0`: after the replace, `INFO` no longer matches.
- `grep -E 'INFO|DEBUG'` → Confirms both INFO occurrences became DEBUG.

**New words in this step:**

- **validated write** — committing an edit only after a safety command passes.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `replace` | global substitute | idempotent if result won't re-match |
| `validate: %s` | gate the write | `%s` is the temp file |
| `backup: true` | keep original | timestamped copy |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Change rejected | `validate` failed | Fix the regexp/command |
| Always `changed` | result still matches regexp | Make regexp not match result |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the remove-comments playbook
- [ ] Task 1 · Step 2 — Run it twice and watch `changed=0`
- [ ] Task 2 · Step 1 — Write the replace+validate playbook
- [ ] Task 2 · Step 2 — Run it twice and confirm idempotence
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-24
rm -rf /root/rhcsa_journal/lab-24b
```

**Expected output:**

```
✅ Removed /tmp/lab-24 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `sed -i` in a play | Non-idempotent | Use `replace`/`lineinfile` |
| No `validate:` | Broken config saved | Gate with `validate: '... %s'` |
| Replace re-matches result | Always `changed` | Ensure result differs from regexp |

---

## 📌 Exam Strategy

Replace `sed -i` with stateful modules: `lineinfile state: absent` to remove, `replace` for global edits, and always add `validate:` for critical configs. Idempotence plus validation is the RHCE standard.

- `replace` = idempotent `sed s///g`.
- `lineinfile state: absent` = idempotent `sed '/re/d'`.
- `validate: '... %s'` stops broken configs from saving.

---

## 🔗 Related Labs

- [Lab 24a — Stream Editing with sed (RHCSA)](../lab-24a-sed-stream-editor-rhcsa/) — the `sed` these modules replace
- [Lab 24c — Stream Editing with sed (Verify)](../lab-24c-sed-stream-editor-verify/) — prove edits and backups
- [Lab 22b — Filtering with grep and Regex (Ansible)](../lab-22b-grep-regex-ansible/) — anchored `lineinfile` edits

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
