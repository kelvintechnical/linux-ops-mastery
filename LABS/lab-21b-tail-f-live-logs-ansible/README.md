# Lab 21b: Monitoring Live Logs (Ansible) — capturing recent log lines

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 21b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (reading logs to drive decisions), RHCSA EX200 (the `tail` behavior underneath), SRE (log-based assertions in automation)  
**Prerequisite:** [Lab 21a](../lab-21a-tail-f-live-logs-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `tail -n N` | _Task 1 · Step 1_ |
| A2 | `changed_when: false` for reads | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | The follow boundary (no `tail -f` module) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `command: tail -n` snapshot | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `select('search', ...)` filter | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `assert` on captured lines | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

Automation can't sit and watch a log forever, so it takes *snapshots*. You will capture the last N lines with `tail -n` via `command:` (read-only), then filter the captured lines for a pattern using Jinja's `select('search', ...)` and assert on the result. This is the playbook pattern for "check the recent log and react."

---

## 🧠 Concept

`tail -f` is a long-running, interactive follow — there is no Ansible module for it, and a playbook task must terminate. The automation equivalent is a *snapshot*: `tail -n 50 file` captured at a moment in time with `ansible.builtin.command`, marked `changed_when: false`. You then process `stdout_lines` in Jinja — `select('search', 'ERROR')` keeps only matching lines — and `assert` on the count to drive the play. For continuous monitoring you'd schedule the playbook (cron/AWX) rather than follow inside one run.

```
SHELL (21a, continuous)             ANSIBLE (21b, snapshot)
─────────────────────────────       ──────────────────────────────────────
tail -f app.log | grep ERROR        command: tail -n 50 app.log  (changed_when:false)
  (runs forever)                       └─ stdout_lines | select('search','ERROR')
                                       └─ assert on the filtered count
                                     (re-run on a schedule to "monitor")
```

> **Why this matters:** Health checks and remediation playbooks routinely read the tail of a log and act on what they find. Snapshot + filter + assert is the idiomatic, terminating way to do it.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `command: tail -n N` | Snapshot last N lines | `changed_when: false` |
| `stdout_lines` | Captured lines as list | iterate/filter |
| `select('search', P)` | Keep matching lines | regex search filter |
| `length` | Count filtered lines | for assertions |
| `ansible.builtin.assert` | Gate on findings | `that:` conditions |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and playbook folder with a log holding a known ERROR.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-21
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-21b/playbooks
seq 1 40 | sed 's/^/event /' > "$LAB_ROOT/app.log"
echo "ERROR disk pressure" >> "$LAB_ROOT/app.log"
seq 41 50 | sed 's/^/event /' >> "$LAB_ROOT/app.log"
wc -l "$LAB_ROOT/app.log"
echo "exit was: $?"
```

**Expected output:**

```
51 /tmp/lab-21/app.log
exit was: 0
```

---

## TASK 1 of 2 — Snapshot the tail

**In plain English:** We capture the last 15 lines of the log into a variable.

---

### Step 1 of 2 — Write the snapshot playbook

**In plain English:** We create `task1.yml`, which runs `tail -n 15` read-only and shows the captured lines.

```yaml
---
- name: "Lab 21b Task 1 — snapshot the tail"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    log: /tmp/lab-21/app.log
  tasks:
    - name: "Capture the last 15 lines"
      ansible.builtin.command: "tail -n 15 {{ log }}"
      register: tail_out
      changed_when: false

    - name: "Show the captured tail"
      ansible.builtin.debug:
        var: tail_out.stdout_lines
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `command: tail -n 15` → Capture a point-in-time snapshot of the newest 15 lines.
- `changed_when: false` → Reading a log never counts as a change.
- `debug: var: tail_out.stdout_lines` → Show the captured lines as a list.

**New words in this step:**

- **snapshot** — a one-time capture of the log's tail, the automation alternative to following.

---

### Step 2 of 2 — Run it and read the snapshot

**In plain English:** We run the play and confirm the ERROR line is inside the captured tail.

```bash
ansible-playbook /root/rhcsa_journal/lab-21b/playbooks/task1.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Show the captured tail] ********************************************
ok: [localhost] => {
    "tail_out.stdout_lines": [
        "ERROR disk pressure", "event 41", "...", "event 50"
    ]
}
PLAY RECAP **************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Snapshot and display; `changed=0` confirms it was read-only.

**New words in this step:**

- **point-in-time read** — capturing the log state at one moment for inspection.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `tail -n` snapshot | last N lines | no follow in a play |
| `changed_when: false` | read marker | omit and it shows changed |
| `stdout_lines` | list output | filter it in Jinja |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Task hangs | Used `tail -f` | Use `tail -n`, never `-f` |
| Shows `changed` | Missing `changed_when` | Add `changed_when: false` |

---

## TASK 2 of 2 — Filter and assert

**In plain English:** We keep only ERROR lines from the snapshot and assert at least one exists.

---

### Step 1 of 2 — Write the filter-and-assert playbook

**In plain English:** We create `task2.yml`, which snapshots the tail, filters for ERROR with `select('search', ...)`, and asserts a hit.

```yaml
---
- name: "Lab 21b Task 2 — filter and assert"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    log: /tmp/lab-21/app.log
  tasks:
    - name: "Capture the last 20 lines"
      ansible.builtin.command: "tail -n 20 {{ log }}"
      register: tail_out
      changed_when: false

    - name: "Keep only ERROR lines"
      ansible.builtin.set_fact:
        errors: "{{ tail_out.stdout_lines | select('search', 'ERROR') | list }}"

    - name: "Show the filtered errors"
      ansible.builtin.debug:
        var: errors

    - name: "Assert at least one ERROR was seen"
      ansible.builtin.assert:
        that:
          - "errors | length > 0"
        success_msg: "{{ errors | length }} ERROR line(s) in recent log"
        fail_msg: "no ERROR lines in the recent tail"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `tail -n 20` → Snapshot a slightly larger window.
- `select('search', 'ERROR')` → Jinja filter keeping only lines matching the regex `ERROR` — the in-play `grep`.
- `assert: errors | length > 0` → Gate the play on having found at least one error.

**New words in this step:**

- **`select('search', P)`** — Jinja filter that keeps list items matching a regex.

---

### Step 2 of 2 — Run it and read the assertion

**In plain English:** We run the play and confirm the filtered errors and passing assertion.

```bash
ansible-playbook /root/rhcsa_journal/lab-21b/playbooks/task2.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Show the filtered errors] ******************************************
ok: [localhost] => {"errors": ["ERROR disk pressure"]}
TASK [Assert at least one ERROR was seen] *******************************
ok: [localhost] => {"msg": "1 ERROR line(s) in recent log"}
PLAY RECAP **********************************************************
localhost                  : ok=4    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Snapshot, filter, assert; read-only so `changed=0`.

**New words in this step:**

- **log-driven assertion** — making a play succeed/fail based on recent log content.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `select('search', ...)` | regex filter list | `search` ≠ `match` (anchored) |
| `set_fact` | store filtered list | reuse across tasks |
| schedule to monitor | cron/AWX re-run | one play ≠ continuous |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Filter matches nothing | Used `match` not `search` | `search` is unanchored |
| Assert fails unexpectedly | Window too small | Increase `tail -n` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the snapshot playbook
- [ ] Task 1 · Step 2 — Run it and read the snapshot
- [ ] Task 2 · Step 1 — Write the filter-and-assert playbook
- [ ] Task 2 · Step 2 — Run it and read the assertion
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-21
rm -rf /root/rhcsa_journal/lab-21b
```

**Expected output:**

```
✅ Removed /tmp/lab-21 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `tail -f` in a play | Task never finishes | Snapshot with `tail -n` |
| `match` vs `search` | No matches | `search` for unanchored |
| Reads marked changed | Missing `changed_when: false` | Add it |

---

## 📌 Exam Strategy

Plays snapshot logs, they don't follow them. Capture the tail read-only, filter with `select('search', ...)`, assert on the count, and schedule the play if you need ongoing monitoring.

- Never `tail -f` in a play — it won't terminate.
- `select('search', P)` is the Jinja `grep`.
- Re-run on a schedule for continuous monitoring.

---

## 🔗 Related Labs

- [Lab 21a — Monitoring Live Logs (RHCSA)](../lab-21a-tail-f-live-logs-rhcsa/) — the `tail -f` this snapshots
- [Lab 21c — Monitoring Live Logs (Verify)](../lab-21c-tail-f-live-logs-verify/) — prove the right tail was captured
- [Lab 20b — Scrolling Large Files (Ansible)](../lab-20b-less-more-scrolling-ansible/) — range extraction and in-play search

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
