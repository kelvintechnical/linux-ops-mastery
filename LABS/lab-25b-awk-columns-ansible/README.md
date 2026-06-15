# Lab 25b: Extracting Columns with awk (Ansible) — parsing output, Jinja filters

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 25b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (parsing command output into facts), RHCSA EX200 (the `awk` behavior underneath), DevOps (data extraction in pipelines)  
**Prerequisite:** [Lab 25a](../lab-25a-awk-columns-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `awk '{print $N}'` | _Task 1 · Step 1_ |
| A2 | `changed_when: false` for reads | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `command: awk` capture | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `split()` Jinja field-split | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N3 | `map('int') | sum` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `set_fact` from parsed data | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

Parse columns inside Ansible. You will capture an `awk` extraction with `command:` (read-only) into a fact, then do the *pure-Jinja* equivalent — splitting fields with `split()` and totaling with `map('int') | sum` — so you can choose between shelling out and staying native. Both turn structured text into variables a play can act on.

---

## 🧠 Concept

There's no `awk` module — `awk` is a shell tool — so you have two idiomatic options. **Shell out**: `command: awk '...'` captured read-only (`changed_when: false`), reading `stdout`/`stdout_lines`. It's fine and familiar. **Stay native**: read the data (slurp/lookup), then use Jinja filters — `line.split()` to get fields, `[2]` to pick a column, `map('int')` to convert, `sum` to total. The native path avoids spawning processes and keeps logic visible in the play. Use `set_fact` to store the parsed result for later tasks.

```
SHELL (25a)                          ANSIBLE (25b)
─────────────────────────────       ──────────────────────────────────────
awk '{print $1}' f                   command: awk '{print $1}' f (changed_when:false)
awk '{s+=$3} END{print s}' f         lines | map('split') | map('last') |
                                       map('int') | sum    (pure Jinja)
```

> **Why this matters:** Playbooks constantly parse command output (PIDs, sizes, counts). Knowing both the `command: awk` and the pure-Jinja approaches lets you pick the cleanest tool for each parse.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `command: awk` | Capture extraction | `changed_when: false` |
| `stdout_lines` | Output as list | iterate/filter |
| `split()` | Split a string | default whitespace |
| `map('int')` | Convert to ints | before `sum` |
| `sum` | Total a list | needs numbers |
| `set_fact` | Store parsed value | reuse later |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and playbook folder with a columnar data file.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-25
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-25b/playbooks
cat > "$LAB_ROOT/sales.txt" <<'EOF'
alice east 120
bob west 90
carol east 200
dave west 60
EOF
cat "$LAB_ROOT/sales.txt"
echo "exit was: $?"
```

**Expected output:**

```
alice east 120
bob west 90
carol east 200
dave west 60
exit was: 0
```

---

## TASK 1 of 2 — Capture an awk extraction

**In plain English:** We run `awk` via `command:` and store the result.

---

### Step 1 of 2 — Write the awk-capture playbook

**In plain English:** We create `task1.yml`, which extracts the name column with `awk` read-only.

```yaml
---
- name: "Lab 25b Task 1 — capture an awk extraction"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    data: /tmp/lab-25/sales.txt
  tasks:
    - name: "Extract the name column with awk"
      ansible.builtin.command: "awk '{print $1}' {{ data }}"
      register: names
      changed_when: false

    - name: "Show the captured names"
      ansible.builtin.debug:
        var: names.stdout_lines
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `command: awk '{print $1}'` → Extract the first column; `awk` runs in the shell.
- `changed_when: false` → Reading/extracting changes nothing.
- `debug: var: names.stdout_lines` → The names as a list.

**New words in this step:**

- **`command: awk`** — shelling out to `awk` and capturing the result.

---

### Step 2 of 2 — Run it and read the names

**In plain English:** We run the play and confirm the name column was captured.

```bash
ansible-playbook /root/rhcsa_journal/lab-25b/playbooks/task1.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Show the captured names] *******************************************
ok: [localhost] => {"names.stdout_lines": ["alice", "bob", "carol", "dave"]}
PLAY RECAP **************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Extract and display; `changed=0` confirms read-only.

**New words in this step:**

- **captured column** — a field extracted from text into a play variable.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `command: awk` | shell extraction | quote the program |
| `changed_when: false` | read marker | omit and it shows changed |
| `stdout_lines` | list result | `stdout` is one string |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Quoting errors | `$1` interpolated | Use single quotes for awk body |
| Marked changed | Missing `changed_when` | Add `changed_when: false` |

---

## TASK 2 of 2 — Parse natively with Jinja

**In plain English:** We total the amount column using only Jinja filters, no awk.

---

### Step 1 of 2 — Write the pure-Jinja parse playbook

**In plain English:** We create `task2.yml`, which slurps the file, splits each line, takes the third field, and sums them — the awk total without awk.

```yaml
---
- name: "Lab 25b Task 2 — parse natively with Jinja"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    data: /tmp/lab-25/sales.txt
  tasks:
    - name: "Read the file"
      ansible.builtin.slurp:
        src: "{{ data }}"
      register: raw

    - name: "Total the third column with Jinja"
      ansible.builtin.set_fact:
        total: "{{ (raw.content | b64decode).splitlines()
                   | map('split') | map('last') | map('int') | sum }}"

    - name: "Show the total"
      ansible.builtin.debug:
        msg: "total = {{ total }}"

    - name: "Assert the total is 470"
      ansible.builtin.assert:
        that:
          - "total | int == 470"
        success_msg: "total matches"
        fail_msg: "expected 470, got {{ total }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `(raw.content | b64decode).splitlines()` → Decode the slurped file into a list of lines.
- `map('split') | map('last')` → Split each line into fields and take the last one (the amount).
- `map('int') | sum` → Convert to integers and total — the `awk '{s+=$3} END{print s}'` equivalent.
- `assert: total | int == 470` → Gate on the expected sum.

**New words in this step:**

- **`split()` / `map('last')`** — Jinja field-splitting and column selection.
- **`map('int') | sum`** — convert and total a list natively.

---

### Step 2 of 2 — Run it and read the assertion

**In plain English:** We run the play and confirm the native total equals 470.

```bash
ansible-playbook /root/rhcsa_journal/lab-25b/playbooks/task2.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Show the total] ****************************************************
ok: [localhost] => {"msg": "total = 470"}
TASK [Assert the total is 470] *****************************************
ok: [localhost] => {"msg": "total matches"}
PLAY RECAP **********************************************************
localhost                  : ok=4    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Slurp, parse, total, assert; all read-only so `changed=0`.

**New words in this step:**

- **native parse** — extracting/aggregating data with Jinja instead of shelling out.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `splitlines()` | text → lines | after `b64decode` |
| `map('split')` | lines → fields | default whitespace |
| `map('int')|sum` | total | strings won't sum |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Sum is string concat | Forgot `map('int')` | Convert before `sum` |
| Empty line error | Trailing newline | Filter empties or trim |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the awk-capture playbook
- [ ] Task 1 · Step 2 — Run it and read the names
- [ ] Task 2 · Step 1 — Write the pure-Jinja parse playbook
- [ ] Task 2 · Step 2 — Run it and read the assertion
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-25
rm -rf /root/rhcsa_journal/lab-25b
```

**Expected output:**

```
✅ Removed /tmp/lab-25 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Double-quoting awk body | Shell eats `$1` | Single-quote the program |
| Summing strings | Concatenation/error | `map('int')` first |
| Reads marked changed | Missing `changed_when: false` | Add it |

---

## 📌 Exam Strategy

Parse columns either by shelling out to `awk` (read-only) or natively with Jinja `split`/`map`/`sum`. Prefer native filters for portability and visibility; reach for `command: awk` when the extraction is gnarlier than Jinja handles cleanly.

- Single-quote awk programs so the shell doesn't eat `$N`.
- `map('int') | sum` is the native column total.
- `changed_when: false` on every extraction.

---

## 🔗 Related Labs

- [Lab 25a — Extracting Columns with awk (RHCSA)](../lab-25a-awk-columns-rhcsa/) — the `awk` this mirrors
- [Lab 25c — Extracting Columns with awk (Verify)](../lab-25c-awk-columns-verify/) — prove extractions and totals
- [Lab 19b — Concatenating Files (Ansible)](../lab-19b-cat-concatenate-files-ansible/) — slurp + Jinja text handling

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
