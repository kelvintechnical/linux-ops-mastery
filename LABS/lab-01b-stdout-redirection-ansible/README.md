# lab-01b — stdout redirection — trap drill (Section 18 boundary)

Stdout redirection has no honest `ansible.builtin` module equivalent.
`>` and `>>` are shell operators the kernel processes — not data
structures Ansible can reason about. This b-lab is a **TRAP DRILL LAB**
per Section 18:

- **Task 1** — wrong-way demo of T01-B (unquoted space in redirect target)
- **Task 2** — `ansible.builtin.shell:` boundary + idempotence proof

Built per `cursor-adhd-lab-prompt.txt` sections 0–20. Two tasks, no more.
Begins after `lab-01a` is complete.

---

## LAB HEADER (confirm or correct before Task 1)

```
ENV:   BAREMETAL
DISK:  /dev/sda
NIC:   ens3
SE:    $(getenforce 2>/dev/null || echo n/a)
OS:    $(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"')
TIME:  $(date -Is)
USER:  $(whoami)@$(hostname -s)

TRAPS: T01-A silent > truncation | T01-B unquoted redirect target |
       T44 cleanup orphan audit | T31 usermod -G without -a
PRACTICE DIR: /tmp — sandbox scratch space; cleared on reboot
```

Trap selection (Section 12 — exactly 4):
- **T01-A** + **T01-B** — io category (this topic's two exam-relevant traps)
- **T44** — repeated from lab-01a (cleanup orphan audit)
- **T31** — Users category rotation (different from io)

---

## LAB-WIDE SETUP (run once before Task 1; paste output)

```bash
export LAB_NUM=01
export LAB_SLUG=stdout-redirection
export SANDBOX=/tmp/labsandbox_${LAB_NUM}
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
# Never use USER= — bash reserves it; sudo -i resets it to root silently
export LAB_USER=labuser_${LAB_NUM}_${LAB_SLUG}
export LAB_USER_HOME=${SANDBOX}/home_${LAB_USER}

mkdir -p "${SANDBOX}" "${LAB_USER_HOME}"
getent group  "${GROUP}"    >/dev/null || groupadd "${GROUP}"
getent passwd "${LAB_USER}" >/dev/null || useradd \
    -d "${LAB_USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${LAB_USER}"
chown -R "${LAB_USER}:${GROUP}" "${SANDBOX}"
id    "${LAB_USER}"
ls -ld "${SANDBOX}" "${LAB_USER_HOME}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

Verify Ansible (Section 19):

```bash
ansible --version | head -2
```

If this fails, complete `lab-00-ansible-control-node` first.

---

## TASK 1 of 2 — Wrong-way demo: T01-B unquoted redirect target

```
LAB:   lab-01b — stdout redirection — trap drill
TASK:  1 of 2 — T01-B unquoted space in redirect target
TRAPS: T01-A T01-B T44 T31
```

### Quiz warm-up (from lab-01a)

- **Q1:** What does `>>` do that `>` does not?
- **Q2:** What happens when you use `>` instead of `>>` on a file that
  already has data?

Confirm or correct before we proceed.

---

### Step 1 of 4 — Build the intended file (correct form first)

Run this:

```bash
echo "test data" > "${SANDBOX}/my file.txt"
```

Before I explain — what do you think the quotes around the path do?

**After you've answered — paste your output, then read this:**

**SYNTAX BREAKDOWN**
- `echo` — print arguments to stdout
- `"test data"` — the string to print (quotes preserve the space inside)
- `>` — truncate the redirect target, then write stdout into it
- `"${SANDBOX}/my file.txt"` — full path, quoted so the space in
  `my file.txt` is ONE token, not two

**PLAIN ENGLISH:** Create (or truncate) a file named `my file.txt` inside
the sandbox and write `test data` into it.

**WHY:** We need a known-good file before we deliberately break the
redirect in Step 2.

---

### Step 2 of 4 — T01-B trap: unquoted path with a space

Run this exactly — do NOT add quotes:

```bash
echo "second test" > ${SANDBOX}/my file.txt
```

Before I explain — predict: which file gets written? What happens to
`my file.txt` from Step 1?

**After you've answered — paste output, then read this:**

**SYNTAX BREAKDOWN**
- `>` — truncate-then-write (T01-A: silent destruction if you meant `>>`)
- `${SANDBOX}/my` — bash sees this as the redirect target (first token
  after `>`)
- `file.txt` — bash treats this as an extra argument to `echo`, NOT part
  of the path (T01-B: unquoted space splits the path)

**PLAIN ENGLISH:** Bash writes to a file literally named `my` (not
`my file.txt`) and passes `file.txt` as text for echo to print.

**WHY:** This is T01-B. No error. No warning. The intended file looks
untouched. This is how admins lose data on real systems.

Verify the wreckage:

```bash
ls -la "${SANDBOX}/"
cat "${SANDBOX}/my" 2>/dev/null
cat "${SANDBOX}/my file.txt"
```

**After paste — SYNTAX BREAKDOWN**
- `ls -la` — list all files including hidden, long format
- `cat "${SANDBOX}/my"` — read the accidental file bash created
- `cat "${SANDBOX}/my file.txt"` — read the intended file (unchanged)

**PLAIN ENGLISH:** Show both files side by side so you see the trap.

**WHY:** T43 says recognize wrong-state fast — `ls` before you debug.

Paste all output.

---

### Step 3 of 4 — Fix it: quote the path, use `>>`

Run this:

```bash
rm -f "${SANDBOX}/my"
echo "second test, properly quoted" >> "${SANDBOX}/my file.txt"
cat "${SANDBOX}/my file.txt"
echo "exit was: $?"
```

Before I explain — why `>>` and not `>` here?

**After paste — SYNTAX BREAKDOWN**
- `rm -f` — remove the accidental `my` file (`-f` = no error if missing)
- `>>` — append stdout (preserves Step 1's `test data`)
- `"${SANDBOX}/my file.txt"` — quoted path = one token = T01-B fixed

**PLAIN ENGLISH:** Delete the wrong file, append a second line to the
right file, verify both lines survived.

**WHY:** Both fixes required — quote the path AND choose `>>` over `>`.

Paste output. You should see two lines and `exit was: 0`.

---

### Step 4 of 4 — Audit with `test -f`

Run this:

```bash
test -f "${SANDBOX}/my"          && echo "my exists (FAIL)" || echo "my gone (OK)"
test -f "${SANDBOX}/my file.txt"  && echo "target exists (OK)" || echo "target missing (FAIL)"
wc -l < "${SANDBOX}/my file.txt"
```

**After paste — SYNTAX BREAKDOWN**
- `test -f PATH` — returns 0 if PATH is a regular file
- `&& echo ... || echo ...` — one-line pass/fail audit
- `wc -l < file` — count lines via stdin (clean number only)

**PLAIN ENGLISH:** Prove the trap file is gone and the real file has
two lines.

**WHY:** T44 cleanup discipline starts with knowing what's on disk.

Paste output. Both audit lines should say `(OK)`, `wc -l` should print `2`.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---------|--------------|-----------|
| `> "path with space"` | safe redirect to spaced filename | unquoted = T01-B |
| `>>` | append without truncating | `>` instead = T01-A data loss |
| `test -f && \|\|` | one-line existence audit | RHCSA capstone primitive |
| T01-B | space splits redirect target | wrong file truncated, no error |
| T01-A | `>` truncates silently | one `>` instead of `>>` |

---

### Persistence check

```bash
findmnt /tmp
```

**After paste:** /tmp is volatile — nothing here survives reboot.
That's why sandboxes live here, not in `/etc`.

---

### Journal write (before cleanup — Section 14)

```bash
LAB=lab01
TASK=task1b
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cat > "$JDIR/done.txt" <<EOF
LAB:    lab-01b-stdout-redirection-ansible
TASK:   1 of 2 — T01-B unquoted redirect target
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname -s)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    T01-B unquoted-path redirect trap
TRAPS:    T01-A T01-B T44 T31
MISSED:   [none or list quiz misses]
NEXT:     task2 — ansible.builtin.shell: boundary
EOF

echo "Journal written: $(ls -la $JDIR)"
echo "exit was: $?"
```

---

### Cleanup (Section 6)

```bash
set +e
if getent passwd "${LAB_USER}" >/dev/null 2>&1; then userdel -r "${LAB_USER}" 2>/dev/null; fi
if getent group  "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"
echo "── cleanup audit ──"
getent passwd "${LAB_USER}" && echo "user remains (FAIL)" || echo "user gone (OK)"
getent group  "${GROUP}"    && echo "group remains (FAIL)" || echo "group gone (OK)"
test -d "${SANDBOX}"        && echo "sandbox remains (FAIL)" || echo "sandbox gone (OK)"
set -e
echo "exit was: $?"
```

All rows must say `(OK)`. **STOP** — do not open Task 2 until pasted.

---

## TASK 2 of 2 — Ansible boundary: no module for `>` or `>>`

```
LAB:   lab-01b — stdout redirection — trap drill
TASK:  2 of 2 — ansible.builtin.shell: boundary + idempotence proof
TRAPS: T01-A T01-B T44 T31
```

### Quiz warm-up (from Task 1)

- **Q1:** What token does bash treat as the redirect target in
  `echo hi > /tmp/my file.txt` (unquoted)?
- **Q2:** Why must you use `>>` instead of `>` when appending?

Confirm or correct before we proceed.

Re-run **LAB-WIDE SETUP** (Task 1 cleanup destroyed the sandbox).

---

### Step 1 of 4 — Write the playbook

Run this:

```bash
mkdir -p /root/rhcsa_journal/lab01/playbooks
cat > /root/rhcsa_journal/lab01/playbooks/task2b.yml <<'EOF'
---
- name: lab-01b boundary — no ansible module for stdout redirection
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    target: "/tmp/labsandbox_01/notes.txt"
  tasks:
    - name: write via shell + > (NOT idempotent)
      ansible.builtin.shell: |
        echo "ansible wrote at $(date -Is)" > "{{ target }}"
      register: write_result
      failed_when: write_result.rc != 0

    - name: show what happened
      ansible.builtin.debug:
        msg:
          - "rc:      {{ write_result.rc }}"
          - "changed: {{ write_result.changed }}"
          - "stdout:  {{ write_result.stdout }}"
EOF
ls -l /root/rhcsa_journal/lab01/playbooks/task2b.yml
```

Before I explain — why `ansible.builtin.shell:` and not `command:`?

**After paste — SYNTAX BREAKDOWN**
- `ansible.builtin.shell:` — spawns `/bin/bash`; `>` is interpreted
- `ansible.builtin.command:` — NO shell; `>` becomes literal text
- `register: write_result` — capture rc/changed/stdout into a variable
- `failed_when: write_result.rc != 0` — explicit failure wiring
- `"{{ target }}"` — Jinja2 template variable (Ansible's `$()`)

**PLAIN ENGLISH:** There is no `ansible.builtin` module for `>` or `>>`.
This playbook uses `shell:` as the closest honest substitute.

**WHY:** Section 18 boundary — state it explicitly, don't pretend a
module exists.

---

### Step 2 of 4 — Run twice; prove non-idempotence

```bash
ansible-playbook /root/rhcsa_journal/lab01/playbooks/task2b.yml
ansible-playbook /root/rhcsa_journal/lab01/playbooks/task2b.yml
cat /tmp/labsandbox_01/notes.txt
```

Before I explain — predict the `changed=` count on BOTH runs.

**After paste — SYNTAX BREAKDOWN**
- First run: `changed=1` — file created/overwritten
- Second run: `changed=1` AGAIN — timestamp differs every time
- `cat` — verify only the second timestamp survived (T01-A: `>` truncated)

**PLAIN ENGLISH:** Ansible cannot know if the file "should" contain this
timestamp. It runs the shell command every time.

**WHY:** This proves RHCSA muscle memory for `>`/`>>` cannot be
outsourced to Ansible. Idempotence requires a state-aware module;
there isn't one for redirection.

Paste both PLAY RECAPs and `cat` output.

---

### Step 3 of 4 — Boundary statement on disk

```bash
cat > /root/rhcsa_journal/lab01/playbooks/BOUNDARY.txt <<'EOF'
BOUNDARY: no ansible.builtin module for stdout redirection (> or >>).
SUBSTITUTE: ansible.builtin.shell: with register: and failed_when:
PROOF: two runs both show changed=1 — not idempotent.
CONCLUSION: RHCSA muscle memory for >, >>, |, tee is required.
EOF
cat /root/rhcsa_journal/lab01/playbooks/BOUNDARY.txt
```

**After paste — SYNTAX BREAKDOWN**
- Heredoc `<<'EOF'` — write multi-line text to a file (`'` = no expansion)
- `/root/rhcsa_journal/` — durable path (survives reboot unlike /tmp)

**PLAIN ENGLISH:** Document the boundary where Ansible ends and shell
begins.

**WHY:** T41 — persistent artifacts in `/root`, not volatile `/tmp`.

Paste output.

---

### Step 4 of 4 — T31 awareness (Users trap, different category)

```bash
id -nG "${LAB_USER}"
usermod -G wheel "${LAB_USER}" 2>/dev/null || echo "wheel group may not exist — that's OK for the demo"
id -nG "${LAB_USER}"
```

Before I explain — what did `usermod -G` do to `${LAB_USER}`'s groups?

**After paste — SYNTAX BREAKDOWN**
- `usermod -G wheel` — WITHOUT `-a`, REPLACES all supplementary groups
- `usermod -aG wheel` — the CORRECT form (T31: always `-a` with `-G`)
- `id -nG` — show group names for current user

**PLAIN ENGLISH:** `-G` alone wipes existing groups; `-aG` adds to them.

**WHY:** T31 is our rotated trap from a different category. Same class
of "silent destruction" as T01-A/T01-B — the command succeeds, the
damage is invisible until you inspect.

Restore groups if wheel exists:

```bash
usermod -aG "${GROUP}" "${LAB_USER}" 2>/dev/null || true
id -nG "${LAB_USER}"
```

Paste output.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---------|--------------|-----------|
| `ansible.builtin.shell:` | spawn bash; operators work | not idempotent for `>` |
| `register:` | capture task result | RHCE graders expect this |
| `changed=1` every run | proof of non-idempotence | boundary made visible |
| `command:` vs `shell:` | no shell = no `>` | `>` becomes literal echo arg |
| T31 `usermod -G` | replaces ALL supp groups | always use `-aG` |

---

### Persistence check

```bash
test -f /root/rhcsa_journal/lab01/playbooks/BOUNDARY.txt && echo "boundary doc survives (OK)"
test -f /tmp/labsandbox_01/notes.txt && echo "sandbox file volatile" || echo "sandbox gone or never existed"
getent passwd "${LAB_USER}" && echo "LAB_USER on disk until cleanup (T44)"
```

Paste output.

---

### Journal write (before cleanup)

```bash
LAB=lab01
TASK=task2b
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cat > "$JDIR/done.txt" <<EOF
LAB:    lab-01b-stdout-redirection-ansible
TASK:   2 of 2 — ansible shell boundary + idempotence proof
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname -s)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Ansible boundary for stdout redirection
TRAPS:    T01-A T01-B T44 T31
PROOF:    changed=1 on both playbook runs
BOUNDARY: /root/rhcsa_journal/lab01/playbooks/BOUNDARY.txt
NEXT:     lab-01c-stdout-redirection-verify
EOF

echo "Journal written: $(ls -la $JDIR)"
echo "exit was: $?"
```

---

### Cleanup (Section 6 — final)

```bash
set +e
if getent passwd "${LAB_USER}" >/dev/null 2>&1; then userdel -r "${LAB_USER}" 2>/dev/null; fi
if getent group  "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"
echo "── cleanup audit ──"
getent passwd "${LAB_USER}" && echo "user remains (FAIL)" || echo "user gone (OK)"
getent group  "${GROUP}"    && echo "group remains (FAIL)" || echo "group gone (OK)"
test -d "${SANDBOX}"        && echo "sandbox remains (FAIL)" || echo "sandbox gone (OK)"
set -e
echo "exit was: $?"
```

All rows `(OK)`.

### Drill (after cleanup)

```bash
python3 ~/scripts/rhcsa_drill.py --tier 1
```

**STOP — lab-01b complete.** Begin lab-01c only after cleanup audit
and drill are pasted.
