# Lab 22b: Filtering with grep and Regex (Ansible) — `replace`, `lineinfile` regexp

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 22b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (regex-driven file edits), RHCSA EX200 (the regex behavior underneath), DevOps (idempotent config rewriting)  
**Prerequisite:** [Lab 22a](../lab-22a-grep-regex-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | regex anchors / classes | _Task 1 · Step 1_ |
| A2 | `changed_when: false` for reads | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `ansible.builtin.replace` (regexp) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | backreferences `\1` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `lineinfile` `regexp:` anchor | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `command: grep -E` count guard | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

Apply regex inside Ansible. You will rewrite matching text across a file idempotently with `ansible.builtin.replace` (including a backreference), then ensure a single canonical line exists using `ansible.builtin.lineinfile` with an anchored `regexp:`, and verify with an in-play `grep -E`. These are the regex tools that make config edits both precise and idempotent.

---

## 🧠 Concept

Two modules carry regex in Ansible. `ansible.builtin.replace` substitutes *every* match of `regexp:` with `replace:` across the file — like `sed -E 's///g'` but idempotent (re-running with the target already in place reports `changed=0`). It supports backreferences: `\1` reuses a captured group. `ansible.builtin.lineinfile` ensures *one* line matching `regexp:` equals `line:`; anchoring the `regexp:` (`^Port `) is critical so it edits the existing directive instead of appending a duplicate. To *match* without editing, shell out to `grep -E` read-only.

```
SHELL (22a)                          ANSIBLE (22b)
─────────────────────────────       ──────────────────────────────────────
sed -E 's/foo([0-9]+)/bar\1/g' f     replace: regexp='foo([0-9]+)' replace='bar\1'
grep -E '^Port ' f                   lineinfile: regexp='^Port ' line='Port 2222'
grep -E 'pattern' f                  command: grep -E 'pattern' f (changed_when:false)
```

> **Why this matters:** RHCE config tasks are full of "change this directive" work. `replace` and anchored `lineinfile` do it idempotently; an unanchored `lineinfile` regexp is the classic cause of duplicated config lines.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.replace` | Regex substitute all matches | `regexp:`, `replace:`, `backup:` |
| backreference `\1` | Reuse a capture group | in `replace:` |
| `ansible.builtin.lineinfile` | Ensure one canonical line | anchor `regexp:` |
| `command: grep -E` | Read-only regex match | `changed_when: false` |
| `failed_when:` | Allow grep rc 1 | `rc not in [0,1]` |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and playbook folder with a config to rewrite.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-22
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-22b/playbooks
cat > "$LAB_ROOT/sshd_demo.conf" <<'EOF'
# demo config
Port 22
LogLevel INFO
timeout v1 30
timeout v2 60
EOF
cat "$LAB_ROOT/sshd_demo.conf"
echo "exit was: $?"
```

**Expected output:**

```
# demo config
Port 22
LogLevel INFO
timeout v1 30
timeout v2 60
exit was: 0
```

---

## TASK 1 of 2 — Regex substitute with `replace`

**In plain English:** We rewrite all `timeout vN` markers using a backreference, idempotently.

---

### Step 1 of 2 — Write the replace playbook

**In plain English:** We create `task1.yml`, which rewrites `timeout vN` to `deadline vN` keeping the version number via `\1`.

```yaml
---
- name: "Lab 22b Task 1 — regex substitute with replace"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    conf: /tmp/lab-22/sshd_demo.conf
  tasks:
    - name: "Rename timeout vN to deadline vN (keep the number)"
      ansible.builtin.replace:
        path: "{{ conf }}"
        regexp: 'timeout (v[0-9]+)'
        replace: 'deadline \1'
        backup: true
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

- `regexp: 'timeout (v[0-9]+)'` → Capture the version token `vN` in group 1.
- `replace: 'deadline \1'` → Substitute every match, reinserting the captured version with `\1`.
- `backup: true` → Keep a timestamped backup before the edit.

**New words in this step:**

- **`ansible.builtin.replace`** — idempotent regex substitute across a file.
- **backreference `\1`** — reuse a captured group in the replacement.

---

### Step 2 of 2 — Run it twice and watch `changed=0`

**In plain English:** We run the play twice; the first rewrites the lines, the second finds nothing to change.

```bash
ansible-playbook /root/rhcsa_journal/lab-22b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-22b/playbooks/task1.yml
grep -E 'deadline|timeout' /tmp/lab-22/sshd_demo.conf
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
deadline v1 30
deadline v2 60
exit was: 0
```

**Line-by-line breakdown:**

- two runs → `changed=1` then `changed=0`: once the text is rewritten, the regexp no longer matches the old form.
- `grep -E 'deadline|timeout'` → Confirm both lines were rewritten and version numbers preserved.

**New words in this step:**

- **idempotent substitution** — a regex edit that settles after the first apply.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `replace` | substitute all | global by nature |
| `\1` backref | reuse capture | `(...)` to capture |
| idempotence | re-run `changed=0` | old pattern gone after edit |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Always `changed=1` | Replacement still matches regexp | Make regexp not match the result |
| No substitution | Group/escape wrong | Test the regex with `grep -E` first |

---

## TASK 2 of 2 — Canonical line with `lineinfile`

**In plain English:** We force a single canonical `Port` line with an anchored regexp, then verify by regex.

---

### Step 1 of 2 — Write the lineinfile playbook

**In plain English:** We create `task2.yml`, which ensures exactly one `Port` directive set to 2222, anchored so no duplicate is appended, then greps to confirm.

```yaml
---
- name: "Lab 22b Task 2 — canonical line with lineinfile"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    conf: /tmp/lab-22/sshd_demo.conf
  tasks:
    - name: "Ensure a single canonical Port directive"
      ansible.builtin.lineinfile:
        path: "{{ conf }}"
        regexp: '^Port '
        line: 'Port 2222'
        backup: true
      register: line_result

    - name: "Verify exactly one Port line via regex (read-only)"
      ansible.builtin.command: "grep -Ec '^Port ' {{ conf }}"
      register: port_count
      changed_when: false
      failed_when: port_count.rc not in [0, 1]

    - name: "Assert only one Port directive exists"
      ansible.builtin.assert:
        that:
          - "port_count.stdout | int == 1"
        success_msg: "exactly one Port directive"
        fail_msg: "found {{ port_count.stdout }} Port directives"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `regexp: '^Port '` → Anchored match of the existing directive, so `lineinfile` edits in place rather than appending.
- `line: 'Port 2222'` → The canonical value the line is forced to.
- `grep -Ec '^Port '` + `assert == 1` → Read-only regex count proving there's exactly one Port line.

**New words in this step:**

- **anchored `regexp:`** — anchoring `lineinfile`'s match to avoid duplicate lines.
- **`grep -Ec`** — count matching lines with extended regex.

---

### Step 2 of 2 — Run it twice and read the assertion

**In plain English:** We run the play twice; the directive is set once and stays canonical, and the count assertion passes both times.

```bash
ansible-playbook /root/rhcsa_journal/lab-22b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-22b/playbooks/task2.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Assert only one Port directive exists] ****************************
ok: [localhost] => {"msg": "exactly one Port directive"}
PLAY RECAP ********************************************************************
localhost                  : ok=3    changed=1    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- two runs → `changed=1` then `changed=0`: anchored `lineinfile` edits once and is idempotent thereafter.
- assertion passes → Exactly one `Port` directive, proving the anchor prevented duplicates.

**New words in this step:**

- **canonical line** — the single authoritative directive a `lineinfile` task guarantees.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| anchored regexp | edits in place | unanchored → duplicate lines |
| `grep -Ec` | count matches | counts lines, not hits |
| assert count==1 | uniqueness proof | catches accidental dupes |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Duplicate Port lines | Unanchored `regexp:` | Anchor with `^Port ` |
| Assert fails (count 2) | Pre-existing dup | Remove dups, re-run |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the replace playbook
- [ ] Task 1 · Step 2 — Run it twice and watch `changed=0`
- [ ] Task 2 · Step 1 — Write the lineinfile playbook
- [ ] Task 2 · Step 2 — Run it twice and read the assertion
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-22
rm -rf /root/rhcsa_journal/lab-22b
```

**Expected output:**

```
✅ Removed /tmp/lab-22 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Unanchored `lineinfile` regexp | Duplicate directives | Anchor with `^` |
| `replace` regexp matches result | Always `changed` | Ensure result doesn't re-match |
| Forgetting capture group | `\1` empty | Wrap with `(...)` |

---

## 📌 Exam Strategy

Use `replace` for global regex substitution and `lineinfile` for a single canonical directive — always anchor the `lineinfile` regexp. Verify edits with a read-only `grep -Ec` and an assertion so you prove uniqueness, not just success.

- Anchor `lineinfile` `regexp:` every time.
- `replace` is idempotent only if the result no longer matches the regexp.
- `grep -Ec` + assert proves there are no duplicate directives.

---

## 🔗 Related Labs

- [Lab 22a — Filtering with grep and Regex (RHCSA)](../lab-22a-grep-regex-rhcsa/) — the regex syntax these modules use
- [Lab 22c — Filtering with grep and Regex (Verify)](../lab-22c-grep-regex-verify/) — prove matches and extractions
- [Lab 24b — Stream Editing with sed (Ansible)](../lab-24b-sed-stream-editor-ansible/) — deeper substitution patterns

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
