# Lab 29b: Searching Manuals by Keyword (Ansible) — discovery in a play

**Series:** linux-ops-mastery — Documentation · **Lab 29b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (capturing/asserting tool facts), RHCSA EX200 (the `apropos`/`whatis` behavior underneath), DevOps (tool-inventory reports)  
**Prerequisite:** [Lab 29a](../lab-29a-apropos-whatis-rhcsa/) completed and a working control node  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `whatis` / `apropos` | _Task 1 · Step 1_ |
| A2 | `changed_when: false` for reads | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `command: whatis` capture | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `failed_when` for whatis rc | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `command: apropos` inventory | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `stdout_lines | length` count | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

Run documentation discovery from a play. You will capture a `whatis` summary (handling its exit codes), then build a small *tool inventory* with `apropos`, count the results, and assert a required tool is present. This lets a playbook confirm a managed node ships the commands a role depends on.

---

## 🧠 Concept

`whatis`/`apropos` are non-interactive, so they're easy to run via `ansible.builtin.command` (read-only, `changed_when: false`). The catch is exit codes: both return non-zero ("nothing appropriate") when there's no match, so guard with `failed_when` so "no result" isn't treated as a play failure when that's acceptable — or assert rc 0 when a match is *required*. `apropos KEYWORD` gives you `stdout_lines` you can count (`| length`) for a "how many tools match" metric, and you can assert a specific command appears (`select('search', '^chown')`) to verify a dependency exists on the node.

```
SHELL (29a)                          ANSIBLE (29b)
─────────────────────────────       ──────────────────────────────────────
whatis chown                         command: whatis chown (changed_when:false,
                                       failed_when rc not in [0,16])
apropos owner                        command: apropos owner → stdout_lines | length
                                       + assert a required tool is listed
```

> **Why this matters:** Roles assume tools exist (`chown`, `tar`, `firewall-cmd`). A discovery+assert task documents and enforces those assumptions on every node, failing fast when a tool is missing.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `command: whatis` | Capture summary | `changed_when: false` |
| `failed_when:` | Handle "no match" rc | `rc not in [0,16]` |
| `command: apropos` | Keyword inventory | read-only |
| `stdout_lines | length` | Count matches | metric |
| `assert` + `select` | Require a tool | gate the play |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and playbook folder for captured discovery.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-29
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-29b/playbooks
echo "ready"
echo "exit was: $?"
```

**Expected output:**

```
ready
exit was: 0
```

---

## TASK 1 of 2 — Capture a whatis summary

**In plain English:** We capture a command's summary, handling its exit codes.

---

### Step 1 of 2 — Write the whatis playbook

**In plain English:** We create `task1.yml`, which captures `whatis chown` read-only and asserts it succeeded.

```yaml
---
- name: "Lab 29b Task 1 — capture a whatis summary"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: "Look up the chown summary"
      ansible.builtin.command: "whatis chown"
      register: w
      changed_when: false
      failed_when: w.rc not in [0, 16]

    - name: "Show the summary"
      ansible.builtin.debug:
        var: w.stdout

    - name: "Assert chown is documented"
      ansible.builtin.assert:
        that:
          - "w.rc == 0"
          - "'change file owner' in w.stdout"
        success_msg: "chown documented"
        fail_msg: "chown summary missing"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `command: whatis chown` → Capture the one-line summary, non-interactive.
- `failed_when: w.rc not in [0, 16]` → `whatis` returns 16 for "nothing appropriate"; accept it so the task can decide, only real errors fail.
- `assert: w.rc == 0 and 'change file owner' in w.stdout` → Require the tool to be documented and the summary to match.

**New words in this step:**

- **whatis rc handling** — accepting the "nothing appropriate" code (16) explicitly.

---

### Step 2 of 2 — Run it and read the assertion

**In plain English:** We run the play and confirm the summary and passing assertion.

```bash
ansible-playbook /root/rhcsa_journal/lab-29b/playbooks/task1.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Show the summary] **************************************************
ok: [localhost] => {"w.stdout": "chown (1)            - change file owner and group"}
TASK [Assert chown is documented] **************************************
ok: [localhost] => {"msg": "chown documented"}
PLAY RECAP **********************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Look up, display, assert; read-only so `changed=0`.

**New words in this step:**

- **dependency assertion** — proving a required command is documented/present.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `whatis` capture | summary | rc 16 = no match |
| `failed_when` | rc policy | allow 0 and 16 |
| content assert | validate | quote `in` |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Play fails on no match | rc 16 unhandled | Add `failed_when` |
| Empty summary | Stale index | `mandb` on the node |

---

## TASK 2 of 2 — Build a tool inventory

**In plain English:** We search by keyword, count matches, and require a tool to be present.

---

### Step 1 of 2 — Write the apropos-inventory playbook

**In plain English:** We create `task2.yml`, which runs `apropos owner`, counts results, and asserts `chown` is among them.

```yaml
---
- name: "Lab 29b Task 2 — tool inventory by keyword"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: "Find ownership-related tools"
      ansible.builtin.command: "apropos owner"
      register: ap
      changed_when: false
      failed_when: ap.rc not in [0, 16]

    - name: "Report how many matched"
      ansible.builtin.debug:
        msg: "{{ ap.stdout_lines | length }} ownership tools found"

    - name: "Assert chown is in the inventory"
      ansible.builtin.assert:
        that:
          - "ap.stdout_lines | select('search', '^chown ') | list | length > 0"
        success_msg: "chown present in inventory"
        fail_msg: "chown not found among ownership tools"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `command: apropos owner` → Keyword inventory of ownership tools.
- `stdout_lines | length` → Count how many tools matched — a discovery metric.
- `select('search', '^chown ')` → Require `chown` to appear, asserting the dependency exists.

**New words in this step:**

- **tool inventory** — a keyword-driven list of available commands on a node.

---

### Step 2 of 2 — Run it and read the count

**In plain English:** We run the play and confirm the count and that `chown` is present.

```bash
ansible-playbook /root/rhcsa_journal/lab-29b/playbooks/task2.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Report how many matched] ******************************************
ok: [localhost] => {"msg": "5 ownership tools found"}
TASK [Assert chown is in the inventory] ********************************
ok: [localhost] => {"msg": "chown present in inventory"}
PLAY RECAP **********************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Inventory, count, assert; read-only so `changed=0` (count may vary by system).

**New words in this step:**

- **discovery metric** — a count of matching tools used for reporting.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `apropos` capture | keyword list | rc 16 if none |
| `length` | match count | varies by system |
| `select('search')` | require a tool | anchor the pattern |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Count is 0 | Stale index | `sudo mandb` |
| Assert fails | Pattern too strict | Loosen the regex |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the whatis playbook
- [ ] Task 1 · Step 2 — Run it and read the assertion
- [ ] Task 2 · Step 1 — Write the apropos-inventory playbook
- [ ] Task 2 · Step 2 — Run it and read the count
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-29
rm -rf /root/rhcsa_journal/lab-29b
```

**Expected output:**

```
✅ Removed /tmp/lab-29 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Unhandled rc 16 | Play fails on no match | `failed_when: rc not in [0,16]` |
| Hard-coding counts | Brittle across systems | Assert presence, not exact count |
| Reads marked changed | Missing `changed_when: false` | Add it |

---

## 📌 Exam Strategy

Use `whatis`/`apropos` in plays to confirm a node has the tools a role needs. Handle their rc 16 ("no match"), count results for reporting, and assert specific tools are present to fail fast on missing dependencies.

- `failed_when: rc not in [0,16]` for `whatis`/`apropos`.
- Assert tool presence, not exact counts.
- `changed_when: false` on every lookup.

---

## 🔗 Related Labs

- [Lab 29a — Searching Manuals by Keyword (RHCSA)](../lab-29a-apropos-whatis-rhcsa/) — the `whatis`/`apropos` this automates
- [Lab 29c — Searching Manuals by Keyword (Verify)](../lab-29c-apropos-whatis-verify/) — prove searches return the right tools
- [Lab 18b — Locate Command Documentation (Ansible)](../lab-18b-locate-command-docs-ansible/) — package-fact discovery

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
