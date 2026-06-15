# Lab 06b: Listing Files and SELinux (Ansible) — `community.general.sefcontext`, `restorecon`

**Series:** linux-ops-mastery — Essential Tools & File Operations · **Lab 06b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (managing SELinux contexts declaratively — a listed objective), RHCSA EX200 (the `semanage`/`restorecon` behavior underneath), DevOps (security labels as code)  
**Prerequisite:** [Lab 06a](../lab-06a-listing-files-selinux-rhcsa/) completed; `community.general` collection installed  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `restorecon` | _Task 2 · Step 1_ |
| A2 | `ansible.builtin.copy` | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `community.general.sefcontext` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N2 | `ansible.builtin.file` (state=directory) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `command:` + `register` + `changed_when` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `setype:` option | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

Express Lab 06a's "set the label persistently, then apply it" loop as idempotent automation: `community.general.sefcontext` records the policy rule (the `semanage fcontext` equivalent) and a guarded `restorecon` applies it. You will run the play twice to watch the rule converge to `changed=0`, the same persistence you achieved by hand — now repeatable across every host.

---

## 🧠 Concept

There is a real module for the policy rule (`community.general.sefcontext`) but **not** for applying it — `restorecon` is still a command you run. So the idiomatic play is two tasks: declare the rule with `sefcontext` (idempotent: `changed=0` once the rule exists), then run `restorecon` via `command:` and tell Ansible when that counts as a change with `changed_when:`. This mirrors the hand pattern exactly: rule first, relabel second.

```
SHELL (06a)                          ANSIBLE (06b)
─────────────────────────────       ──────────────────────────────────────
semanage fcontext -a -t T 'P(/.*)?'  community.general.sefcontext: target/setype/state=present
restorecon -Rv P                     ansible.builtin.command: restorecon -Rv P  (changed_when:)
```

> **Why this matters:** Graders re-run your play. `sefcontext` is idempotent, so the rule task settles to `changed=0`; only the `restorecon` task may still report change. Knowing which task can and cannot be idempotent is the exam-level nuance.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `community.general.sefcontext` | Manage persistent fcontext rules | `target`, `setype`, `state: present` |
| `ansible.builtin.file` | Create/manage paths | `state: directory` makes folders idempotently |
| `ansible.builtin.command` | Run `restorecon` (no module exists) | guard with `changed_when:` |
| `register:` | Capture `restorecon` output | inspect `stdout` to decide `changed_when` |
| `become: true` | Run as root | required for SELinux policy changes |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and the durable playbook folder, and confirm the `community.general` collection is reachable.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-06
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-06b/playbooks
ansible-galaxy collection list 2>/dev/null | grep community.general || \
  ansible-galaxy collection install community.general
echo "exit was: $?"
```

**Expected output:**

```
community.general 8.6.0
exit was: 0
```

---

## TASK 1 of 2 — Build the content directory declaratively

**In plain English:** We create the webroot and an index file with real modules so the structure exists idempotently before we label it.

---

### Step 1 of 2 — Write the directory + file playbook

**In plain English:** We create `task1.yml`, which makes the webroot with `ansible.builtin.file` and writes an index page with `ansible.builtin.copy`.

```yaml
---
- name: "Lab 06b Task 1 — build the content directory"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    webroot: /tmp/lab-06/webroot
  tasks:
    - name: "Ensure the webroot exists"
      ansible.builtin.file:
        path: "{{ webroot }}"
        state: directory
        mode: '0755'

    - name: "Write the index page"
      ansible.builtin.copy:
        dest: "{{ webroot }}/index.html"
        content: "<h1>lab 06</h1>\n"
        mode: '0644'
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.file: state: directory` → Create the folder idempotently; re-runs report `changed=0`.
- `ansible.builtin.copy: content:` → Declare the index file's exact contents.

**New words in this step:**

- **`ansible.builtin.file`** — the module for paths: directories, symlinks, ownership, and deletion.

---

### Step 2 of 2 — Run it and confirm the structure

**In plain English:** We run the play twice and confirm the directory and file converge to `changed=0`.

```bash
ansible-playbook /root/rhcsa_journal/lab-06b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-06b/playbooks/task1.yml
ls -lZ /tmp/lab-06/webroot
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=2    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
-rw-r--r--. 1 root root unconfined_u:object_r:tmp_t:s0 16 ... index.html
exit was: 0
```

**Line-by-line breakdown:**

- two `ansible-playbook` runs → First creates the dir + file (`changed=2`), second is fully idempotent (`changed=0`).
- `ls -lZ ...` → Confirm the file exists with the default `tmp_t` type, ready to relabel in Task 2.

**New words in this step:**

- **state: directory** → declares a folder should exist, creating it only when missing.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `file: state: directory` | idempotent mkdir | `state: touch` is NOT idempotent (updates mtime) |
| `copy: content:` | exact file content | newline drift keeps `changed=1` |
| default `tmp_t` | `/tmp` files inherit temp type | services may be denied until relabeled |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `changed=1` every run | Used `state: touch` | Use `state: directory`/`copy` for idempotence |
| Wrong perms | `mode:` omitted | Set `mode:` explicitly |

---

## TASK 2 of 2 — Label persistently with `sefcontext` + `restorecon`

**In plain English:** We declare the fcontext rule with the module and apply it with a guarded `restorecon`, then prove idempotence.

---

### Step 1 of 2 — Write the sefcontext + restorecon playbook

**In plain English:** We create `task2.yml`, which records the web-content rule with `community.general.sefcontext` and runs `restorecon` only when relabeling is needed.

```yaml
---
- name: "Lab 06b Task 2 — persistent SELinux label"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  vars:
    webroot: /tmp/lab-06/webroot
  tasks:
    - name: "Record the fcontext rule for the webroot"
      community.general.sefcontext:
        target: "{{ webroot }}(/.*)?"
        setype: httpd_sys_content_t
        state: present

    - name: "Apply the rule by relabeling"
      ansible.builtin.command: "restorecon -Rv {{ webroot }}"
      register: relabel
      changed_when: "'Relabeled' in relabel.stdout"

    - name: "Show what was relabeled"
      ansible.builtin.debug:
        msg: "{{ relabel.stdout_lines }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `community.general.sefcontext: target/setype/state: present` → Declare the persistent rule; idempotent, so a re-run reports `changed=0`.
- `ansible.builtin.command: restorecon -Rv ...` → Apply the rule (no module exists for this step).
- `changed_when: "'Relabeled' in relabel.stdout"` → Only count the task as changed when `restorecon` actually relabeled something.

**New words in this step:**

- **`community.general.sefcontext`** — the module that manages SELinux file-context rules, the `semanage fcontext` equivalent.
- **`setype:`** — the SELinux type to assign in the rule.

---

### Step 2 of 2 — Run it twice and watch it converge

**In plain English:** We run the play twice; the first relabels (`changed`), and the second finds nothing to do once the rule and labels already match.

```bash
ansible-playbook /root/rhcsa_journal/lab-06b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-06b/playbooks/task2.yml
ls -lZ /tmp/lab-06/webroot/index.html
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=3    changed=2    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
-rw-r--r--. 1 root root system_u:object_r:httpd_sys_content_t:s0 16 ... index.html
exit was: 0
```

**Line-by-line breakdown:**

- first run → Records the rule and relabels the tree; both tasks report change.
- second run → Rule already present and files already labeled, so `changed=0` — convergence.
- `ls -lZ ...` → Confirm the file now carries `httpd_sys_content_t`.

**New words in this step:**

- **convergence** — re-running the play reaches a steady `changed=0` state.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `sefcontext` | idempotent rule | does NOT relabel — you still need `restorecon` |
| `changed_when:` | custom change logic | without it, `command` is always `changed` |
| `become: true` | root for policy | omit and SELinux changes fail |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `module not found` | Collection missing | `ansible-galaxy collection install community.general` |
| `restorecon` always `changed` | No `changed_when:` | Gate on `'Relabeled' in stdout` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the directory + file playbook
- [ ] Task 1 · Step 2 — Run it and confirm the structure
- [ ] Task 2 · Step 1 — Write the sefcontext + restorecon playbook
- [ ] Task 2 · Step 2 — Run it twice and watch it converge
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-06
rm -rf /root/rhcsa_journal/lab-06b
```

**This lab created SYSTEM state (an SELinux fcontext rule) — reverse it explicitly:**

```bash
sudo semanage fcontext -d "/tmp/lab-06/webroot(/.*)?"
```

**Expected output:**

```
✅ Removed /tmp/lab-06 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Expecting `sefcontext` to relabel | Files keep old type | Follow with a `restorecon` task |
| No `changed_when:` on `restorecon` | Recap never settles | Gate on the `Relabeled` string |
| Forgetting `become: true` | SELinux task fails | Add it to the play |

---

## 📌 Exam Strategy

For SELinux on the RHCE, pair `community.general.sefcontext` (the rule) with a guarded `restorecon` (the apply). Mark `restorecon` with `changed_when:` so the recap is honest, and always re-run to prove the rule converges to `changed=0`.

- The rule module is idempotent; the relabel command needs `changed_when:`.
- Use `state: absent` in `sefcontext` to remove rules cleanly.
- Re-run twice — convergence is the acceptance test.

---

## 🔗 Related Labs

- [Lab 06a — Listing Files and SELinux (RHCSA)](../lab-06a-listing-files-selinux-rhcsa/) — the hand-typed `semanage`/`restorecon` pattern
- [Lab 06c — Listing Files and SELinux (Verify)](../lab-06c-listing-files-selinux-verify/) — prove the label matches policy
- [Lab 00b — Ansible Control Node (Ansible)](../lab-00b-ansible-control-node-ansible/) — installing the `community.general` collection used here

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
