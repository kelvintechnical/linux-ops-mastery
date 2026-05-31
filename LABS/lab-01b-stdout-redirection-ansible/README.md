# lab-01b — stdout redirection — Ansible boundary trap drill

This is a Section 18 BOUNDARY b-lab. Stdout redirection has no honest
`ansible.builtin` module equivalent — `>` and `>>` are shell operators
the kernel processes, not data structures Ansible can reason about.
Instead of skipping the b-slot, this lab becomes a TRAP DRILL LAB:

- **Task 1** — wrong-way demo of the unquoted-filename-with-redirect
  trap. You make the mistake on purpose, watch what bash does with it,
  then run the correct quoted form and explain the difference.
- **Task 2** — Ansible boundary statement. You use
  `ansible.builtin.shell:` (the closest honest substitute) with
  `register:` and `failed_when:`, run the playbook twice, and prove
  why `changed=1` shows up on every run — i.e. the operation is not
  idempotent and Ansible cannot replace knowing the shell cold.

Built per `cursor-adhd-lab-prompt.txt` sections 0–20. Two tasks, no
more. Begins after `lab-01a-stdout-redirection-rhcsa` is complete and
the `--category io` drill score is >= 80%.

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

TRAPS THIS LAB: T43 T44
PRACTICE DIR:   /tmp — sandbox scratch space; cleared on reboot; safe to write without sudo
```

Trap rationale (per Sections 11 and 12):

- **T43** (getting stuck >10 min on one task) — Task 1's wrong-way
  demo produces a confusing "ambiguous redirect" or weird-filename
  state. T43 says: skip and return rather than thrash. Drill it now.
- **T44** (cleanup orphan audit) — Task 2 builds `${LAB_USER}` again;
  the audit at the end of each task proves no orphan was left.

(Section 11 has no io-specific traps yet. When you add an entry like
`T01-A unquoted filename with redirect — always quote the path`,
update this header to match.)

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

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
/tmp is sandbox scratch space; cleared on reboot.
RHCSA labs use it because nothing here survives reboot and no sudo is needed to write.
EOF

echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

Verify ansible-core is present (per Section 19 prerequisite):

```bash
ansible --version | head -2
```

If `ansible --version` fails, complete `lab-00-ansible-control-node`
before continuing. Task 2 cannot run without it.

---

## TASK 1 of 2 — Wrong-way demo: unquoted filename with redirect

```
LAB:   lab-01b — stdout redirection — Ansible boundary trap drill
TASK:  1 of 2 — unquoted filename with `>` deletes the wrong file
TRAPS: T43 (don't get stuck on the confusing error, fix and move on)
```

### Quiz warm-up (from lab-01a, Section 4 rule)

- **Q1:** What does `>>` do that `>` does not?
- **Q2:** In `wc -l < file`, what is `<` doing? Why is the output
  cleaner with `<` than with `wc -l file`?

Confirm or correct before we proceed.

---

### Step 1 of 4 — Stage the trap (the wrong way to write a path)

Run this exactly as written. Yes, it has a space in the filename
deliberately. That's the whole point of the lesson.

```bash
echo "test data" > "${SANDBOX}/my file.txt"
```

Wait — that line has the path quoted, so it works. To trigger the
trap, run the *unquoted* version next:

```bash
echo "second test" > ${SANDBOX}/my file.txt
```

Before I explain — predict what bash does with that second line. Where
does `second test` end up? Is `my file.txt` modified? Is anything else
modified? (Type your guess.)

**After you've answered:**

Bash sees `>` followed by two whitespace-separated tokens:
`${SANDBOX}/my` and `file.txt`. It treats `${SANDBOX}/my` as the
redirect target (so it creates a file literally named `my` under the
sandbox) and treats `file.txt` as an extra positional argument to
`echo`. So:

- `${SANDBOX}/my` is created (or truncated) and gets the bytes
  `second test file.txt\n`.
- `${SANDBOX}/my file.txt` (the file you thought you were writing) is
  unchanged from Step 1.
- No error. No warning. The shell did exactly what you typed.

Run this to see the wreckage:

```bash
ls -la "${SANDBOX}/"
echo "--- contents of my (the accidental file) ---"
cat "${SANDBOX}/my" 2>/dev/null
echo "--- contents of my file.txt (the intended file) ---"
cat "${SANDBOX}/my file.txt"
```

Paste your output. You should see two files: `my` and `my file.txt`.
The `my` file holds `second test file.txt`. The `my file.txt` file
still holds `test data` from Step 1.

This is the canonical "shell tokenization beat me" trap. On a real
system this happens to admins who copy a path with a space from a
ticket and paste it without quotes. The wrong file gets truncated;
the right file is untouched and looks fine; nothing complains.
T43 says: notice fast, fix faster. Don't spend 10 minutes wondering
why your file isn't being updated — read your own command first.

---

### Step 2 of 4 — Recover and write the correct way

Run this:

```bash
rm -f "${SANDBOX}/my"
echo "second test, properly quoted" >> "${SANDBOX}/my file.txt"
cat                                    "${SANDBOX}/my file.txt"
echo "exit was: $?"
```

Before I explain — what changed between the broken Step 1b command
and this one, beyond the `rm`? (Two things.)

**After you've answered:**

1. The path is fully quoted: `"${SANDBOX}/my file.txt"`. The double
   quotes prevent the shell from splitting on the space, so bash sees
   ONE redirect target.
2. The operator changed from `>` to `>>`. Step 1's intended file
   already has data in it; using `>` would truncate. `>>` appends.

Both fixes are required. The quoting fix is the trap drill; the
`>>` choice is the lab-01a muscle memory you're carrying forward.

Paste your output. You should see both lines and `exit was: 0`.

---

### Step 3 of 4 — Defensive habit: catch unquoted paths with `set -u`

Run this:

```bash
set -u
echo "with set -u" > "${SANDBOX}/$DOES_NOT_EXIST.txt"
echo "exit was: $?"
set +u
```

Before I explain — predict what `set -u` does to a redirect that
references an unset variable. (Type your guess.)

**After you've answered:**

`set -u` (also `set -o nounset`) tells bash to error out when an
unset variable is dereferenced. Without `set -u`, `$DOES_NOT_EXIST`
expands to an empty string, your redirect target becomes
`${SANDBOX}/.txt` (a hidden file — different trap), and you never
notice. With `set -u`, bash says
`bash: DOES_NOT_EXIST: unbound variable` and `$?` is non-zero,
which Section 8 says is a hard blocker.

This is not a fix for the unquoted-space trap — only quoting fixes
that. But `set -u` catches the related "typo in a variable name"
trap that lives in the same neighborhood.

Paste your output. You should see the unbound-variable error and
`exit was: 1`.

---

### Step 4 of 4 — Audit and clean up Task 1

Run this:

```bash
ls -la "${SANDBOX}/"
test -f "${SANDBOX}/my"           && echo "my STILL exists (FAIL)" || echo "my removed (OK)"
test -f "${SANDBOX}/my file.txt"  && echo "my file.txt exists (OK)" || echo "my file.txt missing (FAIL)"
wc -l < "${SANDBOX}/my file.txt"
```

Before I explain — what does `test -f` return non-zero for?

**After you've answered:**

`test -f PATH` returns 0 (true) if PATH is a regular file, non-zero
otherwise. Combined with `&& echo OK || echo FAIL` it becomes a
one-line audit primitive. RHCSA capstones lean on it constantly.

Paste your output. Both audit lines should say `(OK)` and `wc -l`
should print `2`.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---------|--------------|-----------|
| `> path with space` (unquoted) | shell splits on whitespace; redirect target is the first token | wrong file gets truncated, intended file untouched, no error |
| `> "path with space"` (quoted) | shell treats the whole path as one token | the canonical safe form — always quote paths from outside data |
| `set -u` | error on unset variable expansion | catches typos in variable names; turn back off after the strict block |
| `>>` for follow-up writes | preserves prior content | using `>` instead silently truncates (lab-01a Task 2 trap) |
| `test -f PATH && ... \|\| ...` | one-line existence audit | combine with `(OK)/(FAIL)` echo for paste-and-prove |
| `ls -la` after a redirect | shows the file you didn't mean to make | trap-drill discipline: always `ls` after a redirect with variables |
| T43 (don't get stuck) | recognize the wrong-state fast, recover, move on | spending 20 min reading man pages instead of `ls`-ing your sandbox |

Drill mapping: every row above → `--category io`.

---

### Persistence check

Question: If we rebooted right now, what state survives?

```bash
findmnt /tmp
ls -la "${SANDBOX}/"
```

Paste output. Same answer as lab-01a: nothing under `${SANDBOX}` survives.
The trap-drill insight is that EVEN IF /tmp survived reboot, the wrong
file `my` we accidentally created would also survive — silent
collateral damage outlives the reboot. That is exactly why every
RHCSA capstone ends with `ls` of the working directory.

---

### Journal write (run before cleanup)

```bash
LAB=lab01
TASK=task1b
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cat > "$JDIR/done.txt" <<EOF
LAB:    lab-01b-stdout-redirection-ansible
TASK:   1 of 2 — unquoted filename trap drill
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname -s)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    stdout redirection — unquoted-path trap
COMMANDS: echo, ls, cat, test -f, wc -l, set -u
TRAPS:    T43 (drill: recognize wrong-state fast, fix faster)
MISSED:   [list any quiz question you got wrong, or "none"]
NEXT:     task2 — ansible.builtin.shell: boundary + idempotence reality
EOF

echo "Journal written: $(ls -la $JDIR)"
echo "exit was: $?"
```

Paste output.

---

### Cleanup (Section 6 teardown)

```bash
set +e

podman ps -aq --filter "name=^${CTR}$" 2>/dev/null \
    | xargs -r podman rm -f >/dev/null 2>&1

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts \
    | tac | xargs -r -n1 umount -l 2>/dev/null

if vgs "${VG}" >/dev/null 2>&1; then
    lvremove -fy  "${VG}"          2>/dev/null
    vgremove -fy  "${VG}"          2>/dev/null
fi

losetup -j "${SANDBOX}/disk.img" 2>/dev/null \
    | cut -d: -f1 | xargs -r losetup -d 2>/dev/null

if getent passwd "${LAB_USER}" >/dev/null 2>&1; then
    userdel -r "${LAB_USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
    groupdel "${GROUP}"  2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── cleanup audit ──"
getent passwd "${LAB_USER}"  && echo "user remains (FAIL)"   || echo "user gone (OK)"
getent group  "${GROUP}"     && echo "group remains (FAIL)"  || echo "group gone (OK)"
test -d "${SANDBOX}"         && echo "sandbox remains (FAIL)" || echo "sandbox gone (OK)"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

Every audit row must say `(OK)`.

**STOP.** Task 2 is below. Do not look until you have pasted all step
outputs, the persistence check, the journal write, and all `(OK)` audit
lines.

---

## TASK 2 of 2 — Ansible boundary: `ansible.builtin.shell:` with register

Per Section 18: there is no `ansible.builtin` module that owns the
operation "redirect stdout to a file". You can use `copy:` for static
content, `template:` for templated content, or `lineinfile:` for line
edits — none of those IS what `>` does. The closest honest substitute
is `ansible.builtin.shell:` with the redirect inside, plus `register:`
and `failed_when:` so you treat the result like real engineering.

The point of this task is to PROVE the boundary by running the
playbook twice and showing `changed=1` every time. That is what
"not idempotent" means in practice and is why RHCSA muscle memory
cannot be replaced.

```
LAB:   lab-01b — stdout redirection — Ansible boundary trap drill
TASK:  2 of 2 — ansible.builtin.shell: + register + idempotence proof
TRAPS: T44 (cleanup orphan audit)
```

### Quiz warm-up (from Task 1)

- **Q1:** What turns `> path with space` from a trap into safe code?
- **Q2:** What does `set -u` catch?

Confirm or correct before we proceed.

---

### Prerequisite — re-run the lab-wide setup

The Task 1 cleanup tore down `${LAB_USER}`, `${GROUP}`, and `${SANDBOX}`.
Re-run the **LAB-WIDE SETUP** block at the top of this file, then
verify Ansible:

```bash
ansible --version | head -2
```

Both the sandbox and Ansible must be ready before Step 1.

---

### Step 1 of 4 — Write the playbook

Run this:

```bash
mkdir -p /root/rhcsa_journal/lab01/playbooks
cat > /root/rhcsa_journal/lab01/playbooks/task2.yml <<'EOF'
---
- name: lab-01b boundary — stdout redirection via shell module
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    target: "/tmp/labsandbox_01/notes.txt"
  tasks:
    - name: write a line via shell + > (NOT idempotent)
      ansible.builtin.shell: |
        echo "written by ansible at $(date -Is)" > "{{ target }}"
      register: write_result
      failed_when: write_result.rc != 0

    - name: read it back via shell + cat (also NOT idempotent)
      ansible.builtin.shell: |
        cat "{{ target }}"
      register: read_result
      changed_when: false

    - name: show what changed and what we read
      ansible.builtin.debug:
        msg:
          - "write rc:      {{ write_result.rc }}"
          - "write changed: {{ write_result.changed }}"
          - "read  changed: {{ read_result.changed }}"
          - "read  stdout:  {{ read_result.stdout }}"
EOF

ls -l /root/rhcsa_journal/lab01/playbooks/task2.yml
```

Before I explain — three things to predict:

1. Why is `ansible.builtin.shell:` the right module here, not `command:`?
2. Why does the read task have `changed_when: false`?
3. Why does the write task have `failed_when: write_result.rc != 0`
   instead of relying on the default?

**After you've answered:**

1. `command:` does NOT spawn a shell, so `>` would be passed as a
   literal argument to `echo`, and you'd see `echo "..." > /tmp/...`
   — `>` printed alongside the text instead of redirected. `shell:`
   spawns bash, which interprets `>` correctly.
2. Reading is observation. It doesn't change anything. Without
   `changed_when: false`, `shell:` always reports `changed=true`,
   which lies to anyone reading the play recap.
3. The default behavior of `shell:` is to fail when rc != 0, but
   stating it explicitly makes the boundary visible: this is the
   line where Ansible's "did it succeed?" plugs into the shell's
   `$?`. RHCE graders look for that.

Paste your `ls -l` output.

---

### Step 2 of 4 — Run the playbook in check mode first

Run this:

```bash
ansible-playbook --check --diff /root/rhcsa_journal/lab01/playbooks/task2.yml
```

Before I explain — what do you think `--check --diff` does for a
`shell:` task?

**After you've answered:**

For real modules (file, copy, lineinfile, etc.) `--check` simulates
without writing and `--diff` shows the would-be diff. For `shell:`
and `command:`, `--check` SKIPS the task entirely (Ansible has no
way to predict what arbitrary shell does). You will see `skipped`
on both shell tasks, and the debug task may show empty values.

That is itself a boundary lesson: a real module can be planned,
audited, and dry-run reviewed. A shell call cannot. RHCE answers
that ask for "idempotent and check-friendly" reject `shell:` for
exactly this reason.

Paste your output.

---

### Step 3 of 4 — Run for real, twice, and prove non-idempotence

First run:

```bash
ansible-playbook /root/rhcsa_journal/lab01/playbooks/task2.yml
```

Read the PLAY RECAP. Note the `changed=` count. Then run it again:

```bash
ansible-playbook /root/rhcsa_journal/lab01/playbooks/task2.yml
```

Before I explain — predict the second run's `changed=` count.
(Type your guess.)

**After you've answered:**

Both runs report `changed=1` (the write task always claims to have
changed; the read task is forced to `changed_when: false`). The
file is rewritten with a new `$(date -Is)` value every run. There
is no "is this already the desired state?" check, because there is
no way for `shell:` to know what the desired state is.

Compare with `ansible.builtin.copy:` — if you used `copy:` to write
a fixed line, the second run would say `changed=0` because the file
content already matches. That is what idempotence looks like, and
that is what `>` cannot give you.

Paste both PLAY RECAPs and the file content:

```bash
cat /tmp/labsandbox_01/notes.txt
```

You should see the timestamp from the SECOND run (proving the first
write was overwritten — which is also a tiny lab-01a Task 2 callback:
`>` truncates).

---

### Step 4 of 4 — Audit + state the boundary in writing

Run this:

```bash
echo "BOUNDARY STATEMENT: there is no ansible.builtin module for stdout redirection." \
    | tee -a /root/rhcsa_journal/lab01/playbooks/BOUNDARY.txt
echo "shell: + > is the closest substitute and it is not idempotent." \
    | tee -a /root/rhcsa_journal/lab01/playbooks/BOUNDARY.txt
echo "RHCSA muscle memory for >, >>, |, tee is required — Ansible cannot replace it." \
    | tee -a /root/rhcsa_journal/lab01/playbooks/BOUNDARY.txt
cat /root/rhcsa_journal/lab01/playbooks/BOUNDARY.txt
```

Before I explain — why is `tee -a` the right tool here instead of
`echo ... >> file`?

**After you've answered:**

Both work. `tee -a` is the lab-01a callback: you write the line AND
see it in your terminal in one shot, instead of writing silently and
then `cat`ing to verify. It is a small consistency choice that pays
off when you are reviewing your own session output. Either is correct;
`tee -a` is the "show your work" form.

Paste output.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---------|--------------|-----------|
| `ansible.builtin.shell:` | spawn bash, interpret operators | not idempotent for `>`/`>>`; treat as a boundary |
| `register: name` | capture rc / stdout / stderr / changed | RHCE graders look for `register:` on every shell call |
| `failed_when: rc != 0` | make the failure semantics explicit | default is fine, but explicit is RHCE-grade |
| `changed_when: false` | tell Ansible "this is observation only" | without it, every `shell:` lies as `changed=true` |
| `--check` on a shell task | skipped, not simulated | a real module would run in check mode |
| `--diff` on a shell task | nothing to diff | only meaningful for state-aware modules |
| 2nd run still `changed=1` | proof of non-idempotence | the boundary made visible |
| `command:` vs `shell:` | command does NOT spawn a shell | `>` becomes literal echo argument, not redirect |

Drill mapping: every row above → `--category ansible` and `--category io`.

Trap-Risk row (Section 16h requirement): wrapping shell commands in
`command:`/`shell:` when a real module exists. For `>` redirection there
IS no module, so the wrapping is honest. For everything else, refuse to
wrap.

---

### Persistence check

Question: After reboot, which of these survive?

1. `${SANDBOX}/notes.txt` (the file the playbook writes)
2. `/root/rhcsa_journal/lab01/playbooks/task2.yml` (the playbook itself)
3. `${LAB_USER}` (the sandbox user)
4. `/root/rhcsa_journal/lab01/playbooks/BOUNDARY.txt`

Run:

```bash
findmnt /tmp /root
ls -l /root/rhcsa_journal/lab01/playbooks/
getent passwd "${LAB_USER}"
```

Paste output and answer:

- 1: NO — `/tmp` is volatile. Re-run the playbook to recreate.
- 2: YES — `/root` is on the root partition.
- 3: YES — until cleanup runs. THIS is why T44 matters.
- 4: YES — `/root` is on the root partition.

Lesson: the artifacts that survive (playbook + boundary statement)
are the documentation-grade outputs. The artifacts that don't
survive (notes.txt + LAB_USER) need cleanup discipline. Section 6
audit catches the second category.

---

### Journal write (run before cleanup)

```bash
LAB=lab01
TASK=task2b
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cat > "$JDIR/done.txt" <<EOF
LAB:    lab-01b-stdout-redirection-ansible
TASK:   2 of 2 — ansible.builtin.shell: boundary + idempotence proof
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname -s)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Ansible boundary for stdout redirection
COMMANDS: ansible-playbook, ansible.builtin.shell, register, failed_when, changed_when, debug
TRAPS:    T44 (cleanup orphan ${LAB_USER}/${GROUP} audit)
BOUNDARY: documented in /root/rhcsa_journal/lab01/playbooks/BOUNDARY.txt
PROOF:    two runs both reported changed=1 — non-idempotent
MISSED:   [list any quiz question or step you got wrong, or "none"]
NEXT:     lab-01c-stdout-redirection-verify (audit + destroy-restore drill)
EOF

echo "Journal written: $(ls -la $JDIR)"
echo "exit was: $?"
```

Paste output.

---

### Cleanup (Section 6 teardown — final, full audit)

```bash
set +e

podman ps -aq --filter "name=^${CTR}$" 2>/dev/null \
    | xargs -r podman rm -f >/dev/null 2>&1

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts \
    | tac | xargs -r -n1 umount -l 2>/dev/null

if vgs "${VG}" >/dev/null 2>&1; then
    lvremove -fy  "${VG}"          2>/dev/null
    vgremove -fy  "${VG}"          2>/dev/null
fi

losetup -j "${SANDBOX}/disk.img" 2>/dev/null \
    | cut -d: -f1 | xargs -r losetup -d 2>/dev/null

if getent passwd "${LAB_USER}" >/dev/null 2>&1; then
    userdel -r "${LAB_USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
    groupdel "${GROUP}"  2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── cleanup audit ──"
getent passwd "${LAB_USER}"  && echo "user remains (FAIL)"   || echo "user gone (OK)"
getent group  "${GROUP}"     && echo "group remains (FAIL)"  || echo "group gone (OK)"
test -d "${SANDBOX}"         && echo "sandbox remains (FAIL)" || echo "sandbox gone (OK)"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

Note: the playbook and BOUNDARY.txt are NOT cleaned up — they live
under `/root/rhcsa_journal/` on purpose. The journal is the artifact
that survives between sessions.

Every audit row must say `(OK)`.

---

### Drill (run AFTER cleanup audit shows all OK)

```bash
python3 ~/scripts/rhcsa_drill.py --category io
python3 ~/scripts/rhcsa_drill.py --category ansible
```

Paste both scores. If either is <80%, drill again before starting
lab-01c.

---

### Rotation tracker (no change for the b-lab)

```bash
cat /root/rhcsa_journal/dir_rotation.txt
```

The directory rotation only advances at the end of the c-lab (when
the trilogy is complete). For now `last_used=01` should still be the
last value.

**STOP — lab-01b complete.** Begin lab-01c only after both drill
scores are pasted. lab-01c is the verification capstone: Task 1
audits the artifacts the trilogy produced; Task 2 is the
destroy-restore drill that proves persistence reasoning end-to-end.
