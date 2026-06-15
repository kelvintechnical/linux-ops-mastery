# Lab 19b: Concatenating Files with cat (Ansible) — `ansible.builtin.assemble`, `ansible.builtin.slurp`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 19b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (assembling configs from fragments idempotently), RHCSA EX200 (the `cat` behavior underneath), DevOps (drop-in config directories)  
**Prerequisite:** [Lab 19a](../lab-19a-cat-concatenate-files-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `cat` concatenation | _Task 1 · Step 1_ |
| A2 | `ansible.builtin.copy` | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `ansible.builtin.assemble` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `regexp:` fragment filter | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `ansible.builtin.slurp` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `b64decode` filter | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

Replace `cat parts/* > combined` with the purpose-built module: `ansible.builtin.assemble` concatenates the fragments in a directory into one file, idempotently. You will assemble a config from drop-in pieces, prove a re-run is `changed=0`, then read the result back with `ansible.builtin.slurp` and decode it — the Ansible way to "cat a remote file" into a variable.

---

## 🧠 Concept

`ansible.builtin.assemble` is `cat fragments/* > dest` made declarative and idempotent: it concatenates every file in `src:` (a directory) in sorted order into `dest:`, optionally filtering with `regexp:`, and only writes when the result differs. This is exactly how `*.d` config directories work. To *read* a remote file into a play you use `ansible.builtin.slurp`, which returns the content base64-encoded; the `b64decode` filter turns it back into text — the equivalent of `cat`-ing a file to inspect it.

```
SHELL (19a)                          ANSIBLE (19b)
─────────────────────────────       ──────────────────────────────────────
cat parts/*.txt > combined.txt       assemble: src=parts dest=combined.txt
                                       └─ changed=0 when fragments unchanged
cat combined.txt                     slurp: src=combined.txt → content | b64decode
```

> **Why this matters:** Drop-in `conf.d` assembly is a real RHCE pattern. `assemble` keeps it idempotent, and `slurp` is the safe way to read file content into a variable for assertions.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.assemble` | Concatenate a dir of fragments | `src:` dir, `dest:` file, `regexp:` filter |
| `regexp:` | Only include matching fragments | applied to fragment filenames |
| `ansible.builtin.slurp` | Read a remote file (base64) | returns `.content` |
| `b64decode` | Decode slurp content | `{{ result.content | b64decode }}` |
| `register:` + `debug:` | Inspect results | read `changed` / decoded text |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and playbook folder with a fragments directory.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-19
mkdir -p "$LAB_ROOT/parts"
mkdir -p /root/rhcsa_journal/lab-19b/playbooks
printf 'header line\n' > "$LAB_ROOT/parts/01-header.txt"
printf 'body line\n'   > "$LAB_ROOT/parts/02-body.txt"
printf 'footer line\n' > "$LAB_ROOT/parts/03-footer.txt"
ls "$LAB_ROOT/parts"
echo "exit was: $?"
```

**Expected output:**

```
01-header.txt
02-body.txt
03-footer.txt
exit was: 0
```

---

## TASK 1 of 2 — Assemble fragments into one file

**In plain English:** We write a play that concatenates the fragments with `assemble` and prove it is idempotent.

---

### Step 1 of 2 — Write the assemble playbook

**In plain English:** We create `task1.yml`, which assembles every `.txt` fragment in `parts/` into one combined file.

```yaml
---
- name: "Lab 19b Task 1 — assemble fragments"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    parts: /tmp/lab-19/parts
    dest: /tmp/lab-19/combined.txt
  tasks:
    - name: "Concatenate fragments into one file"
      ansible.builtin.assemble:
        src: "{{ parts }}"
        dest: "{{ dest }}"
        regexp: '\.txt$'
        mode: '0644'
      register: asm_result

    - name: "Show whether anything changed"
      ansible.builtin.debug:
        msg: "changed: {{ asm_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.assemble: src/dest:` → Concatenate the fragments directory into the destination, sorted by filename.
- `regexp: '\.txt$'` → Only include fragments whose name ends in `.txt`.
- `register:` + `debug:` → Report whether the assembled file changed.

**New words in this step:**

- **`ansible.builtin.assemble`** — the idempotent `cat fragments/* > dest` module.

---

### Step 2 of 2 — Run it twice and watch `changed=0`

**In plain English:** We run the play twice; the first assembles the file, the second sees the fragments unchanged and does nothing.

```bash
ansible-playbook /root/rhcsa_journal/lab-19b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-19b/playbooks/task1.yml
cat /tmp/lab-19/combined.txt
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
header line
body line
footer line
exit was: 0
```

**Line-by-line breakdown:**

- two runs → `changed=1` then `changed=0`, proving `assemble` only rewrites on fragment changes.
- `cat combined.txt` → Confirm the fragments are concatenated in sorted order.

**New words in this step:**

- **drop-in assembly** — building one file from many small fragments, the `conf.d` pattern.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `assemble` | concat dir → file | fragments sorted by name |
| `regexp:` | filter fragments | applies to names, not content |
| idempotent | re-run `changed=0` | editing a fragment flips it |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Wrong order | Fragment names unsorted | Zero-pad names (`01-`) |
| Extra files included | No/loose `regexp:` | Tighten the `regexp:` |

---

## TASK 2 of 2 — Read the result back with `slurp`

**In plain English:** We read the assembled file into a variable and decode it to assert its content.

---

### Step 1 of 2 — Write the slurp-and-decode playbook

**In plain English:** We create `task2.yml`, which slurps the combined file and prints its decoded text.

```yaml
---
- name: "Lab 19b Task 2 — read a file with slurp"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    dest: /tmp/lab-19/combined.txt
  tasks:
    - name: "Read the assembled file (base64)"
      ansible.builtin.slurp:
        src: "{{ dest }}"
      register: slurped

    - name: "Decode and show the content"
      ansible.builtin.debug:
        msg: "{{ (slurped.content | b64decode).split('\n') }}"

    - name: "Assert the header is present"
      ansible.builtin.assert:
        that:
          - "'header line' in (slurped.content | b64decode)"
        success_msg: "header found"
        fail_msg: "header missing"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.slurp: src:` → Read the remote file; the content comes back base64-encoded in `.content`.
- `b64decode` → Decode it to readable text for display and assertions.
- `assert: that: "'header line' in ..."` → Gate on the decoded content containing the expected line.

**New words in this step:**

- **`ansible.builtin.slurp`** — read a remote file into a variable (base64-encoded).
- **`b64decode`** — Jinja filter that decodes base64 back to text.

---

### Step 2 of 2 — Run it and read the assertion

**In plain English:** We run the play and confirm the decoded content prints and the assertion passes.

```bash
ansible-playbook /root/rhcsa_journal/lab-19b/playbooks/task2.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Decode and show the content] ****************************************
ok: [localhost] => {"msg": ["header line", "body line", "footer line", ""]}
TASK [Assert the header is present] **************************************
ok: [localhost] => {"msg": "header found"}
PLAY RECAP **************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Slurp, decode, assert; all read-only so `changed=0`.

**New words in this step:**

- **content assertion** — proving a file holds an expected string via decoded slurp content.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `slurp` | read remote file | content is base64 — decode it |
| `b64decode` | decode to text | forgetting it yields gibberish |
| `assert` on content | gate on text | quote the `in` expression |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Gibberish output | Forgot `b64decode` | Pipe `.content` through `b64decode` |
| `src not found` | Wrong path | Point `slurp` at the assembled file |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the assemble playbook
- [ ] Task 1 · Step 2 — Run it twice and watch `changed=0`
- [ ] Task 2 · Step 1 — Write the slurp-and-decode playbook
- [ ] Task 2 · Step 2 — Run it and read the assertion
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-19
rm -rf /root/rhcsa_journal/lab-19b
```

**Expected output:**

```
✅ Removed /tmp/lab-19 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `cat` shell-out to assemble | Non-idempotent | Use `ansible.builtin.assemble` |
| Forgetting `b64decode` | Unreadable slurp output | Decode the content |
| Unsorted fragments | Wrong assembled order | Zero-pad fragment names |

---

## 📌 Exam Strategy

Assemble drop-in configs with `ansible.builtin.assemble` (idempotent, sorted), and read remote files with `slurp` + `b64decode` for assertions. Filter fragments with `regexp:` so only intended pieces are included.

- `assemble` is the idempotent `cat fragments/*`.
- `slurp` + `b64decode` is how you read content into a variable.
- Re-run to confirm `assemble` settles at `changed=0`.

---

## 🔗 Related Labs

- [Lab 19a — Concatenating Files (RHCSA)](../lab-19a-cat-concatenate-files-rhcsa/) — the `cat` this play mirrors
- [Lab 19c — Concatenating Files (Verify)](../lab-19c-cat-concatenate-files-verify/) — prove order and content integrity
- [Lab 16b — Search and Save Output (Ansible)](../lab-16b-grep-search-save-output-ansible/) — capturing/asserting file content

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
