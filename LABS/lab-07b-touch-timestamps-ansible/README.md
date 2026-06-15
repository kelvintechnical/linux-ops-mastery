# Lab 07b: Touch Timestamps (Ansible) — `ansible.builtin.file` (`state: touch`), `ansible.builtin.find`

**Series:** linux-ops-mastery — Essential Tools & File Operations · **Lab 07b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (idempotent timestamp control, finding files by age), RHCSA EX200 (the `touch`/`find` behavior underneath), DevOps (artifact freshness gates)  
**Prerequisite:** [Lab 07a](../lab-07a-touch-timestamps-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `stat` (read times) | _Task 1 · Step 2_ |
| A2 | `find` by age | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `ansible.builtin.file` `state: touch` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `modification_time` / `access_time` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `ansible.builtin.find` `age:` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `modification_time_format` | Task 1 · Step 1 | _Task 1 · Step 1_ |

---

## 🎯 Objective

Reproduce Lab 07a's timestamp control in Ansible and learn the subtlety that makes `state: touch` idempotent: when you pin `modification_time` and `access_time` to explicit values, the `file` module only acts when the times differ — so a re-run reports `changed=0`. Then replace `find -mtime` with `ansible.builtin.find`'s `age:` to locate files declaratively.

---

## 🧠 Concept

A bare `state: touch` is **not** idempotent — it sets the time to "now" every run, so `changed=1` forever. The fix is to give `modification_time:` and `access_time:` explicit values (formatted per `modification_time_format`); now the module compares desired vs actual and only changes on drift. For searching, `ansible.builtin.find` takes an `age:` (e.g. `age: 1m` for one minute, `-1d` for newer than a day) and returns a structured list you can register — the declarative replacement for parsing `find` output.

```
SHELL (07a)                          ANSIBLE (07b)
─────────────────────────────       ──────────────────────────────────────
touch -t 202601011200 f             file: path=f state=touch
                                       modification_time="202601011200.00"
                                       access_time="202601011200.00"
                                       └─ changed=0 on re-run (times match)
find . -mmin -5                      find: paths=... age=-5m   (register results)
```

> **Why this matters:** A `state: touch` task that reports `changed=1` forever is a classic non-idempotent smell on the exam. Pinning the times is how you make timestamp management converge.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.file` `state: touch` | Create/bump a file's times | bare touch is NOT idempotent |
| `modification_time` / `access_time` | Pin times for idempotence | values match `modification_time_format` |
| `modification_time_format` | Strptime format for the times | default `%Y%m%d%H%M.%S` |
| `ansible.builtin.find` | Search files declaratively | `age:`, `paths:`, `patterns:`, `age_stamp:` |
| `register:` + `debug:` | Capture/print the matched files | inspect `.matched` and `.files` |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and the durable playbook folder, and seed a couple of files to time-stamp and search.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-07
mkdir -p "$LAB_ROOT/logs"
mkdir -p /root/rhcsa_journal/lab-07b/playbooks
echo "entry" > "$LAB_ROOT/logs/app.log"
ls -l "$LAB_ROOT/logs"
echo "exit was: $?"
```

**Expected output:**

```
-rw-r--r--. 1 root root 6 Jun 15 18:35 app.log
exit was: 0
```

---

## TASK 1 of 2 — Idempotent `state: touch` with pinned times

**In plain English:** We write a play that sets a file's atime and mtime to fixed values, then run it twice to prove the second run reports `changed=0`.

---

### Step 1 of 2 — Write the pinned-touch playbook

**In plain English:** We create `task1.yml`, which uses `ansible.builtin.file` with `state: touch` plus explicit `modification_time`/`access_time` so the time is deterministic, not "now."

```yaml
---
- name: "Lab 07b Task 1 — idempotent timestamp control"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    target: /tmp/lab-07/logs/app.log
  tasks:
    - name: "Pin atime and mtime to a fixed value (idempotent)"
      ansible.builtin.file:
        path: "{{ target }}"
        state: touch
        modification_time: "202601011200.00"
        access_time: "202601011200.00"
        modification_time_format: "%Y%m%d%H%M.%S"
        access_time_format: "%Y%m%d%H%M.%S"
      register: touch_result

    - name: "Show whether the timestamp changed"
      ansible.builtin.debug:
        msg: "changed: {{ touch_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `state: touch` → Create the file if missing and manage its times.
- `modification_time` / `access_time: "202601011200.00"` → Pin both to `2026-01-01 12:00:00`; explicit values are what make touch idempotent.
- `modification_time_format` / `access_time_format` → Tell the module how to parse the value strings.

**New words in this step:**

- **`state: touch`** — the `file` module mode that creates a file and/or updates its times.
- **pinned time** — an explicit timestamp value that lets `touch` converge to `changed=0`.

---

### Step 2 of 2 — Run it twice and watch `changed=0` on the re-run

**In plain English:** We run the play twice; the first sets the time (or finds it already set), and the second reports `changed=0` because the times already match.

```bash
ansible-playbook /root/rhcsa_journal/lab-07b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-07b/playbooks/task1.yml
stat -c '%y %n' /tmp/lab-07/logs/app.log
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
2026-01-01 12:00:00.000000000 -0500 /tmp/lab-07/logs/app.log
exit was: 0
```

**Line-by-line breakdown:**

- first run → Sets the pinned times; `changed=1`.
- second run → Times already match the pinned values, so `changed=0` — the idempotence proof a bare touch could never give.
- `stat -c '%y %n' ...` → Confirm the mtime equals the pinned value.

**New words in this step:**

- **idempotent touch** — `state: touch` made convergent by pinning explicit times.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| bare `state: touch` | sets time to now | `changed=1` every run — not idempotent |
| pinned `modification_time` | deterministic time | format must match `*_time_format` |
| `file` module | manages paths + times | distinct from `copy` (content) |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `changed=1` every run | No pinned times | Add `modification_time`/`access_time` |
| `failed to parse time` | Format mismatch | Align value with `*_time_format` |

---

## TASK 2 of 2 — Find files by age with `ansible.builtin.find`

**In plain English:** We replace `find -mtime` with the `find` module's `age:` and read the structured result.

---

### Step 1 of 2 — Write the find-by-age playbook

**In plain English:** We create `task2.yml`, which searches the logs directory for files modified within a time window and registers the matches.

```yaml
---
- name: "Lab 07b Task 2 — find files by age"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    log_dir: /tmp/lab-07/logs
  tasks:
    - name: "Find .log files older than 1 day (by mtime)"
      ansible.builtin.find:
        paths: "{{ log_dir }}"
        patterns: "*.log"
        age: "1d"
        age_stamp: mtime
        recurse: true
      register: old_logs

    - name: "Show how many matched and their paths"
      ansible.builtin.debug:
        msg:
          - "matched: {{ old_logs.matched }}"
          - "files: {{ old_logs.files | map(attribute='path') | list }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.find: paths/patterns:` → Search the log dir for `*.log` files.
- `age: "1d"` + `age_stamp: mtime` → Match files whose mtime is older than one day (our pinned 2026-01-01 file qualifies).
- `register:` + `debug:` → Capture the result and print the count (`matched`) and the list of paths.

**New words in this step:**

- **`ansible.builtin.find`** — the module that searches the filesystem and returns a structured file list.
- **`age:`** — the age threshold; a plain value means "older than," a `-` prefix means "younger than."

---

### Step 2 of 2 — Run it and read the matched files

**In plain English:** We run the play and confirm the registered result lists the aged log file.

```bash
ansible-playbook /root/rhcsa_journal/lab-07b/playbooks/task2.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Show how many matched and their paths] ********************************
ok: [localhost] => {
    "msg": [
        "matched: 1",
        "files: ['/tmp/lab-07/logs/app.log']"
    ]
}
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Run the search; `matched: 1` and the path prove the aged file was found.
- PLAY RECAP `changed=0` → `find` is read-only, so it never reports change — no `changed_when:` needed.

**New words in this step:**

- **`matched`** → the count field returned by `find`, useful for assertions.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `find` module | structured file search | read-only, always `changed=0` |
| `age:` + `age_stamp:` | age threshold + which time | default stamp is mtime |
| `-1d` vs `1d` | younger vs older than | the `-` prefix flips the window |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `matched: 0` | Wrong age direction | Use `-1d` for younger, `1d` for older |
| Subdirs missed | `recurse` off | Set `recurse: true` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the pinned-touch playbook
- [ ] Task 1 · Step 2 — Run it twice and watch `changed=0` on the re-run
- [ ] Task 2 · Step 1 — Write the find-by-age playbook
- [ ] Task 2 · Step 2 — Run it and read the matched files
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-07
rm -rf /root/rhcsa_journal/lab-07b
```

**Expected output:**

```
✅ Removed /tmp/lab-07 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Bare `state: touch` for stable files | `changed=1` every run | Pin `modification_time`/`access_time` |
| Wrong time format | Parse error | Match `modification_time_format` |
| `age: 1d` expecting "newer" | Empty result | Use `-1d` for younger-than |

---

## 📌 Exam Strategy

When automating timestamps, pin the times so `state: touch` is idempotent, and use `ansible.builtin.find` instead of shelling out to `find`. Register the search result and act on `.files`/`.matched` rather than parsing text.

- Pinned times are the trick to a convergent `touch`.
- `find` module returns structured data — far safer than parsing CLI output.
- Re-run to confirm `changed=0` on the touch task.

---

## 🔗 Related Labs

- [Lab 07a — Touch Timestamps (RHCSA)](../lab-07a-touch-timestamps-rhcsa/) — the hand-typed `touch`/`find` this play mirrors
- [Lab 07c — Touch Timestamps (Verify)](../lab-07c-touch-timestamps-verify/) — prove the times with `stat` and `find`
- [Lab 14b — Searching with find (Ansible)](../lab-14b-searching-with-find-ansible/) — more `ansible.builtin.find` predicates

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
