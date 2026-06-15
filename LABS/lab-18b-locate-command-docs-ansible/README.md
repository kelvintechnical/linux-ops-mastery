# Lab 18b: Locate Command Documentation (Ansible) — `ansible.builtin.package_facts`, `command: rpm`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 18b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (querying package state as facts), RHCSA EX200 (the `rpm -q*` behavior underneath), DevOps (software inventory automation)  
**Prerequisite:** [Lab 18a](../lab-18a-locate-command-docs-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `rpm -qd` (via command) | _Task 2 · Step 1_ |
| A2 | `ansible.builtin.copy` | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `ansible.builtin.package_facts` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `ansible_facts.packages` lookup | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `ansible.builtin.assert` on facts | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N4 | `command: rpm -qd` capture | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

Query package state as **facts** instead of parsing CLI text. You will gather installed packages with `ansible.builtin.package_facts`, assert a package is present and read its version from the structured fact tree, then capture its documentation list with a read-only `command: rpm -qd` and save it. Facts make "is this installed and what version?" a clean, scriptable check.

---

## 🧠 Concept

`ansible.builtin.package_facts` populates `ansible_facts.packages`, a dict keyed by package name whose values carry `version`, `release`, and `arch`. Testing membership (`'coreutils' in ansible_facts.packages`) and reading the version is far more robust than scraping `rpm -q`. For listing docs there is no dedicated module, so you run `rpm -qd` via `command:` as a read-only check (`changed_when: false`) and persist the result with `copy`. Facts for state, command for the one-off query.

```
SHELL (18a)                          ANSIBLE (18b)
─────────────────────────────       ──────────────────────────────────────
rpm -qi coreutils | grep Version     package_facts → ansible_facts.packages['coreutils']
rpm -qd coreutils > docs.txt         command: rpm -qd ... (register) → copy
```

> **Why this matters:** Grading often checks "package X version Y is installed." `package_facts` answers that as data, not text — the idiomatic, reliable way RHCE expects.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.package_facts` | Populate installed-package facts | `manager: rpm` (auto-detected) |
| `ansible_facts.packages` | Dict of installed packages | `[name][0].version` |
| `ansible.builtin.assert` | Fail unless a fact holds | `that:` with a membership test |
| `ansible.builtin.command` | Run `rpm -qd` read-only | `changed_when: false` |
| `ansible.builtin.copy` | Save the doc list | `content:` from stdout |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and playbook folder; the package data comes from the live RPM database.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-18
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-18b/playbooks
rpm -q coreutils
echo "exit was: $?"
```

**Expected output:**

```
coreutils-9.0-...el9.x86_64
exit was: 0
```

---

## TASK 1 of 2 — Query package state as facts

**In plain English:** We gather package facts and assert `coreutils` is installed, printing its version.

---

### Step 1 of 2 — Write the package_facts playbook

**In plain English:** We create `task1.yml`, which gathers package facts and asserts the target package is present.

```yaml
---
- name: "Lab 18b Task 1 — query package facts"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    pkg: coreutils
  tasks:
    - name: "Gather installed package facts"
      ansible.builtin.package_facts:
        manager: rpm

    - name: "Assert the package is installed"
      ansible.builtin.assert:
        that:
          - "pkg in ansible_facts.packages"
        success_msg: "{{ pkg }} is installed"
        fail_msg: "{{ pkg }} is NOT installed"

    - name: "Show the version from facts"
      ansible.builtin.debug:
        msg: "{{ pkg }} version: {{ ansible_facts.packages[pkg][0].version }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.package_facts: manager: rpm` → Populate `ansible_facts.packages` from the RPM DB.
- `assert: that: "pkg in ansible_facts.packages"` → Fail the play unless the package is present.
- `debug: ... packages[pkg][0].version` → Read the version straight from the fact tree.

**New words in this step:**

- **`package_facts`** — module that builds a structured map of installed packages.
- **fact lookup** — reading a value like `version` from `ansible_facts`.

---

### Step 2 of 2 — Run it and read the version

**In plain English:** We run the play and confirm the assertion passes and the version prints.

```bash
ansible-playbook /root/rhcsa_journal/lab-18b/playbooks/task1.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Assert the package is installed] *************************************
ok: [localhost] => {"changed": false, "msg": "coreutils is installed"}
TASK [Show the version from facts] ****************************************
ok: [localhost] => {"msg": "coreutils version: 9.0"}
PLAY RECAP ****************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Gather facts, assert presence, print version; everything is read-only so `changed=0`.

**New words in this step:**

- **read-only play** — a play that only inspects state, never changing it.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `package_facts` | inventory as data | must run before reading `packages` |
| `[pkg][0].version` | first entry's version | a name can have multiple installs |
| `assert` | gate on a fact | quote the `that:` expression |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `packages is undefined` | Facts not gathered | Run `package_facts` first |
| Assertion fails | Package absent | Install it or fix the name |

---

## TASK 2 of 2 — Capture the documentation list

**In plain English:** We run `rpm -qd` read-only and save the doc paths idempotently.

---

### Step 1 of 2 — Write the doc-capture playbook

**In plain English:** We create `task2.yml`, which lists a package's docs and writes them to a file.

```yaml
---
- name: "Lab 18b Task 2 — capture package documentation"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    pkg: coreutils
    out: /tmp/lab-18/coreutils-docs.txt
  tasks:
    - name: "List the package's documentation files (read-only)"
      ansible.builtin.command: "rpm -qd {{ pkg }}"
      register: docs
      changed_when: false

    - name: "Save the doc list"
      ansible.builtin.copy:
        dest: "{{ out }}"
        content: "{{ docs.stdout }}\n"
        mode: '0644'
      register: save_result

    - name: "Show count and changed"
      ansible.builtin.debug:
        msg:
          - "doc files: {{ docs.stdout_lines | length }}"
          - "changed: {{ save_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `command: rpm -qd {{ pkg }}` + `changed_when: false` → Read the package's doc files without changing anything.
- `copy: content: "{{ docs.stdout }}\n"` → Persist the list idempotently.

**New words in this step:**

- **doc capture** — saving a package's documentation paths for offline reference.

---

### Step 2 of 2 — Run it twice and confirm the saved list

**In plain English:** We run the play twice; the command is read-only and the saved list converges to `changed=0`.

```bash
ansible-playbook /root/rhcsa_journal/lab-18b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-18b/playbooks/task2.yml
head -n 3 /tmp/lab-18/coreutils-docs.txt
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ****************************************************************
localhost                  : ok=3    changed=1    unreachable=0    failed=0
PLAY RECAP ****************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
/usr/share/man/man1/ls.1.gz
/usr/share/man/man1/cp.1.gz
...
exit was: 0
```

**Line-by-line breakdown:**

- two runs → Command stays `changed=0`; saved list is `changed=1` then `changed=0`.
- `head -n 3 ...` → Confirm the captured doc paths.

**New words in this step:**

- **idempotent capture** — saving query output so re-runs do not re-write an identical file.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `command: rpm -qd` | read-only query | mark `changed_when: false` |
| `copy` of stdout | persist results | trailing newline drift |
| facts vs command | data vs one-off | use facts for state checks |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Empty doc list | Package ships no docs | Expected; choose a documented package |
| Always changed | Newline mismatch | Keep `content:` stable |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the package_facts playbook
- [ ] Task 1 · Step 2 — Run it and read the version
- [ ] Task 2 · Step 1 — Write the doc-capture playbook
- [ ] Task 2 · Step 2 — Run it twice and confirm the saved list
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-18
rm -rf /root/rhcsa_journal/lab-18b
```

**Expected output:**

```
✅ Removed /tmp/lab-18 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Reading `packages` before gathering | Undefined error | Run `package_facts` first |
| `command: rpm` without `changed_when` | Noisy recap | Mark it `changed_when: false` |
| Assuming one version per name | Wrong index | Iterate `packages[name]` |

---

## 📌 Exam Strategy

Use `package_facts` for "is X installed / what version?" checks and `command: rpm -q*` (read-only) for one-off queries you must capture. Assert on facts to gate plays, and mark query commands `changed_when: false`.

- `package_facts` is the idiomatic installed-software check.
- Reach for `command` only when no fact/module covers the query.
- Keep query commands read-only with `changed_when: false`.

---

## 🔗 Related Labs

- [Lab 18a — Locate Command Documentation (RHCSA)](../lab-18a-locate-command-docs-rhcsa/) — the `rpm -q*` chain this mirrors
- [Lab 18c — Locate Command Documentation (Verify)](../lab-18c-locate-command-docs-verify/) — prove ownership and doc presence
- [Lab 00b — Ansible Control Node (Ansible)](../lab-00b-ansible-control-node-ansible/) — `ansible.builtin.dnf` package management

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
