# Lab 20b: Scrolling Large Files (Ansible) — extracting ranges without a pager

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 20b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (reading file ranges in automation), RHCSA EX200 (the `less`/`sed` behavior underneath), SRE (log slicing in playbooks)  
**Prerequisite:** [Lab 20a](../lab-20a-less-more-scrolling-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | reading large files (`less`/`sed`) | _Task 1 · Step 1_ |
| A2 | `changed_when: false` for reads | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | The pager boundary (no `less` module) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `command: sed -n 'A,Bp'` (page range) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `stdout_lines` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N4 | `command: grep -n` search-in-play | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

`less` is interactive, so there is no `less` module — automation cannot "scroll." Instead you extract exactly the lines you need. You will pull a page range with `sed -n 'A,Bp'` run via `command:` (read-only, `changed_when: false`), inspect it through `stdout_lines`, then search the log in-play with `grep -n` and assert the match. This is how playbooks read big files deterministically.

---

## 🧠 Concept

Interactive paging has no place in automation — there's no terminal to scroll. The Ansible equivalent of "go to lines 500–510" is `sed -n '500,510p' file` executed with `ansible.builtin.command`, marked `changed_when: false` because reading changes nothing. The result's `stdout_lines` gives you the page as a list. The equivalent of "search the log" is `grep -n pattern file`; because `grep` returns exit code 1 when nothing matches, you guard it with `failed_when:` so "no match" isn't a play failure. Together they replace `less` with reproducible, assertable reads.

```
SHELL (20a, interactive)            ANSIBLE (20b, deterministic)
─────────────────────────────       ──────────────────────────────────────
less file → /pattern, G, g          command: grep -n pattern file
less +N, scroll to lines 500-510    command: sed -n '500,510p' file
                                       └─ changed_when: false (read-only)
```

> **Why this matters:** Playbooks frequently need a specific slice of a log or config to drive a decision. `sed -n` ranges and `grep -n` give you that deterministically, with proper read-only and exit-code handling.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `command: sed -n 'A,Bp'` | Extract a line range | quote the range |
| `changed_when: false` | Mark a read as no-change | for all read commands |
| `stdout_lines` | Result as a list | iterate or index |
| `command: grep -n` | Search with line numbers | guard rc 1 with `failed_when` |
| `failed_when:` | Custom failure logic | allow grep rc 0 or 1 |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and playbook folder with a large log.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-20
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-20b/playbooks
seq 1 1000 | sed 's/^/line /' > "$LAB_ROOT/big.log"
sed -i '750a ERROR disk full' "$LAB_ROOT/big.log"
wc -l "$LAB_ROOT/big.log"
echo "exit was: $?"
```

**Expected output:**

```
1001 /tmp/lab-20/big.log
exit was: 0
```

---

## TASK 1 of 2 — Extract a page range

**In plain English:** We pull a specific block of lines and inspect it as a list.

---

### Step 1 of 2 — Write the range-extract playbook

**In plain English:** We create `task1.yml`, which extracts lines 748–752 with `sed -n` as a read-only command.

```yaml
---
- name: "Lab 20b Task 1 — extract a page range"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    log: /tmp/lab-20/big.log
  tasks:
    - name: "Read lines 748-752 (a 'page')"
      ansible.builtin.command: "sed -n '748,752p' {{ log }}"
      register: page
      changed_when: false

    - name: "Show the extracted page"
      ansible.builtin.debug:
        var: page.stdout_lines
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `command: sed -n '748,752p'` → Print only lines 748–752 — a precise "page" without scrolling.
- `changed_when: false` → Reading a file changes nothing, so never report `changed`.
- `debug: var: page.stdout_lines` → Show the page as a clean list.

**New words in this step:**

- **`sed -n 'A,Bp'`** — print only the line range A through B.
- **`stdout_lines`** — command output split into a list of lines.

---

### Step 2 of 2 — Run it and read the page

**In plain English:** We run the play and confirm the ERROR line sits inside the extracted range.

```bash
ansible-playbook /root/rhcsa_journal/lab-20b/playbooks/task1.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Show the extracted page] *******************************************
ok: [localhost] => {
    "page.stdout_lines": [
        "line 748", "line 749", "line 750", "ERROR disk full", "line 751"
    ]
}
PLAY RECAP **************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Extract and display the page; `changed=0` confirms it was read-only.

**New words in this step:**

- **page range** — a deterministic slice of lines extracted instead of scrolled.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `sed -n 'A,Bp'` | print a range | quote the range string |
| `changed_when: false` | read marker | omit and reads show changed |
| `stdout_lines` | list output | `stdout` is one big string |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Task shows `changed` | No `changed_when` | Add `changed_when: false` |
| Empty page | Range past EOF | Check `wc -l` bounds |

---

## TASK 2 of 2 — Search the log in-play

**In plain English:** We search for a pattern with `grep -n` and assert it was found.

---

### Step 1 of 2 — Write the search playbook

**In plain English:** We create `task2.yml`, which runs `grep -n ERROR` with proper exit-code handling and asserts a hit.

```yaml
---
- name: "Lab 20b Task 2 — search the log"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    log: /tmp/lab-20/big.log
  tasks:
    - name: "Search for ERROR with line numbers"
      ansible.builtin.command: "grep -n ERROR {{ log }}"
      register: hits
      changed_when: false
      failed_when: hits.rc not in [0, 1]

    - name: "Show matches"
      ansible.builtin.debug:
        var: hits.stdout_lines

    - name: "Assert at least one ERROR exists"
      ansible.builtin.assert:
        that:
          - "hits.rc == 0"
        success_msg: "found {{ hits.stdout_lines | length }} match(es)"
        fail_msg: "no ERROR lines found"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `command: grep -n ERROR` → Search with line numbers, like `/ERROR` in `less`.
- `failed_when: hits.rc not in [0, 1]` → Treat "no match" (rc 1) as normal, only real errors (rc ≥ 2) fail.
- `assert: hits.rc == 0` → Gate the play on actually finding a match.

**New words in this step:**

- **`grep -n` in-play** — search a file and capture matching line numbers.
- **`failed_when:`** — custom failure rule so grep's rc 1 isn't fatal.

---

### Step 2 of 2 — Run it and read the assertion

**In plain English:** We run the play and confirm the match and passing assertion.

```bash
ansible-playbook /root/rhcsa_journal/lab-20b/playbooks/task2.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Show matches] ****************************************************
ok: [localhost] => {"hits.stdout_lines": ["751:ERROR disk full"]}
TASK [Assert at least one ERROR exists] ******************************
ok: [localhost] => {"msg": "found 1 match(es)"}
PLAY RECAP **********************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Search, display, assert; all read-only so `changed=0`.

**New words in this step:**

- **match assertion** — proving a search found the expected pattern.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `grep -n` | search + line nums | rc 1 means "no match" |
| `failed_when:` | exit-code policy | allow rc 0 and 1 |
| `assert rc==0` | require a hit | distinguishes "found" from "ran" |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Play fails on no match | grep rc 1 unhandled | Add `failed_when: rc not in [0,1]` |
| Assert always passes | Wrong condition | Gate on `hits.rc == 0` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the range-extract playbook
- [ ] Task 1 · Step 2 — Run it and read the page
- [ ] Task 2 · Step 1 — Write the search playbook
- [ ] Task 2 · Step 2 — Run it and read the assertion
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-20
rm -rf /root/rhcsa_journal/lab-20b
```

**Expected output:**

```
✅ Removed /tmp/lab-20 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Expecting a `less` module | There isn't one | Extract ranges with `sed -n` |
| Unhandled grep rc 1 | Play fails on no match | Use `failed_when:` |
| Reads marked changed | Missing `changed_when: false` | Add it to read commands |

---

## 📌 Exam Strategy

Automation can't scroll — it extracts. Use `sed -n 'A,Bp'` for a range and `grep -n` for a search, both read-only with proper exit-code handling, and assert on the result to drive decisions.

- `changed_when: false` on every read command.
- `failed_when: rc not in [0,1]` whenever you grep.
- `stdout_lines` gives you a clean list to iterate or assert.

---

## 🔗 Related Labs

- [Lab 20a — Scrolling Large Files (RHCSA)](../lab-20a-less-more-scrolling-rhcsa/) — the `less` this replaces in automation
- [Lab 20c — Scrolling Large Files (Verify)](../lab-20c-less-more-scrolling-verify/) — prove the right lines were read
- [Lab 22b — Filtering with grep and Regex (Ansible)](../lab-22b-grep-regex-ansible/) — regex matching in plays

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
