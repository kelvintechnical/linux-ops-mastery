# lab-01b — stdout redirection — trap drill (Section 18 boundary)

Stdout redirection has no honest `ansible.builtin` module equivalent.
("stdout" = *standard output*, the normal text a command prints to your
screen.) `>` and `>>` are shell operators the kernel processes — not data
structures Ansible can reason about. This b-lab is a **TRAP DRILL LAB** per
Section 18:

- **Task 1** — wrong-way demo of T01-B (unquoted space in redirect target)
- **Task 2** — `ansible.builtin.shell:` boundary + idempotence proof

This README reads like a book for a beginner: every command block has a
plain-English "what we're about to do" line in front of it, and every line of
syntax is explained one sentence at a time underneath. Jargon gets defined the
first time it appears.

Built per `cursor-adhd-lab-prompt.txt` sections 0–20. Two tasks, no more.
Begins after `lab-01a` is complete.

---

## LAB HEADER (confirm or correct before Task 1)

**In plain English:** This block records the machine you're on so we agree on
the environment. The lines with `$(...)` mean "run this and paste its answer
here" — the shell runs what's inside the parentheses and substitutes the
result.

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

Line by line:

- `ENV: BAREMETAL` — Note this runs on real hardware, not a virtual machine.
- `DISK: /dev/sda` / `NIC: ens3` — The names Linux gives the first disk and
  network card; labels only here.
- `SE: $(getenforce 2>/dev/null || echo n/a)` — Ask SELinux what mode it's
  in; `2>/dev/null` discards any error, and `||` ("or else") prints `n/a` if
  the command fails.
- `OS: $(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"')` — Find
  the friendly OS name: `grep` pulls the line, the `|` (pipe) hands it to
  `cut` which keeps the part after `=`, and `tr -d '"'` deletes the quotes.
- `TIME: $(date -Is)` — Print the current time in tidy ISO format (`-Is` =
  ISO, to the second).
- `USER: $(whoami)@$(hostname -s)` — Show your login name and the short
  machine name (`-s` = short, no domain).
- `TRAPS:` line — The four mistakes this lab drills: a silent `>` truncation,
  an unquoted redirect target, a cleanup orphan, and `usermod -G` without
  `-a`.
- `PRACTICE DIR: /tmp` — Where we scribble; wiped on reboot.

Trap selection (Section 12 — exactly 4):
- **T01-A** + **T01-B** — io category (this topic's two exam-relevant traps)
- **T44** — repeated from lab-01a (cleanup orphan audit)
- **T31** — Users category rotation (different from io)

---

## LAB-WIDE SETUP (run once before Task 1; paste output)

**In plain English:** Build the workspace plus the throwaway group and user
account that own it. We save names in variables first so we never retype them.
Run this whole block once.

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

Line by line:

- `export LAB_NUM=01` — Save the number `01` so we can reuse it everywhere
  instead of retyping it. (`export` makes the variable visible to other
  commands.)
- `export LAB_SLUG=stdout-redirection` — Save the topic's short text label.
- `export SANDBOX=/tmp/labsandbox_${LAB_NUM}` — Build the playground path;
  `${LAB_NUM}` pastes in the `01`.
- `export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}` — Save the owning group's name.
- `# Never use USER= ...` — A comment (`#` = "ignore this line") warning that
  `USER` is special to bash.
- `export LAB_USER=labuser_${LAB_NUM}_${LAB_SLUG}` — Save the throwaway user's
  name.
- `export LAB_USER_HOME=${SANDBOX}/home_${LAB_USER}` — Save that user's home
  path inside the sandbox.
- `mkdir -p "${SANDBOX}" "${LAB_USER_HOME}"` — Create both folders; `-p` =
  "don't error if they exist, and make parent folders as needed."
- `getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"` — Check if the
  group exists; if not, create it. (`>/dev/null` = "hide normal output.")
- `getent passwd "${LAB_USER}" >/dev/null || useradd \` — Check if the user
  exists; if not, create it. The `\` continues the command on the next line.
- `-d "${LAB_USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${LAB_USER}"` —
  `useradd` options: `-d` sets the home folder, `-M` means "don't make a home
  directory," `-s` sets the login shell, `-g` sets the main group.
- `chown -R "${LAB_USER}:${GROUP}" "${SANDBOX}"` — Give the sandbox to our
  user and group; `-R` = "recursively, including everything inside."
- `id "${LAB_USER}"` — Print the user's IDs and groups to confirm it was
  created.
- `ls -ld "${SANDBOX}" "${LAB_USER_HOME}"` — List the two folders; `-l` = long
  format, `-d` = "show the folder itself, not its contents."
- `echo "Sandbox built by $(whoami) at $(date -Is)"` — Print a confirmation
  with your username and the current time.
- `echo "exit was: $?"` — Print the *exit status* (the success/failure code
  the last command left behind; `0` = success, non-zero = failure).

Verify Ansible (Section 19):

**In plain English:** Confirm Ansible is installed before Task 2 needs it.

```bash
ansible --version | head -2
```

- `ansible --version | head -2` — Print Ansible's version, then `|` (pipe)
  hands it to `head -2` which keeps only the first two lines.

If this fails, complete `lab-00-ansible-control-node` first.

**New words in this step:**
- **stdout** — the normal text output a command prints to the screen.
- **exit status** — the number a command leaves behind to report success
  (`0`) or failure (non-zero).

---

## TASK 1 of 2 — Wrong-way demo: T01-B unquoted redirect target

**In plain English:** We build a file with a space in its name the right way,
then deliberately leave the quotes off to spring the T01-B trap, watch bash
write to the wrong file, and finally fix it and audit the result.

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

### Step 1 of 2 — Build the good file, then spring the T01-B trap and inspect both files

**In plain English:** First we create a known-good file whose name contains a
space, using quotes so the space is safe. Then we run the exact same idea
*without* quotes to spring the T01-B trap — bash silently writes to a
different file than you intended — and we list and read both files to see the
damage.

Run this (the correct, quoted form first):

```bash
echo "test data" > "${SANDBOX}/my file.txt"
```

Before I explain — what do you think the quotes around the path do? (Type
your guess.)

**After you've answered, line by line:**

- `echo "test data"` — Print the text `test data`; the quotes keep the space
  inside it as part of one string.
- `>` — Truncate the *redirect target* (the file the arrow points at) to zero
  bytes, then write stdout into it.
- `"${SANDBOX}/my file.txt"` — The full path, quoted so the space in
  `my file.txt` stays as ONE *token* (one whole word bash treats as a single
  argument) rather than splitting into two.

So this creates (or empties) a file literally named `my file.txt` inside the
sandbox and writes `test data` into it. We need a known-good file before we
deliberately break the redirect.

Now spring the trap — run this exactly, do NOT add quotes:

```bash
echo "second test" > ${SANDBOX}/my file.txt
```

Before I explain — predict: which file gets written? What happens to
`my file.txt` from before? (Type your guess.)

**After you've answered, line by line:**

- `>` — Still truncate-then-write; if you ever meant `>>` here, this would be
  T01-A (silent destruction of existing content).
- `${SANDBOX}/my` — Because there are no quotes, bash splits on the space and
  treats only `${SANDBOX}/my` as the redirect target (the first word after
  `>`).
- `file.txt` — Bash treats this leftover word as an extra argument to `echo`,
  NOT as part of the path — that's T01-B, the unquoted space splitting the
  path.

So bash writes to a brand-new file literally named `my` (not `my file.txt`)
and just prints `file.txt` as text. There is no error and no warning, and the
original `my file.txt` looks untouched — exactly how admins lose data on real
systems.

Now inspect the wreckage:

```bash
ls -la "${SANDBOX}/"
cat "${SANDBOX}/my" 2>/dev/null
cat "${SANDBOX}/my file.txt"
```

Line by line:

- `ls -la "${SANDBOX}/"` — List everything in the sandbox; `-l` = long
  format, `-a` = include hidden files — so you can see the accidental `my`
  file sitting next to `my file.txt`.
- `cat "${SANDBOX}/my" 2>/dev/null` — Read the accidental file bash created;
  `2>/dev/null` throws away an error if it somehow doesn't exist.
- `cat "${SANDBOX}/my file.txt"` — Read the intended file to confirm it still
  holds the original `test data`.

Showing both files side by side is how you recognize a wrong-state fast (T43)
— always `ls` before you debug. Paste all output.

**New words in this step:**
- **redirect target** — the file an arrow (`>` / `>>`) points at, i.e. where
  the output goes.
- **token** — one whole "word" bash treats as a single argument; spaces split
  text into separate tokens unless quoted.

---

### Step 2 of 2 — Fix it (quote the path, use `>>`) and audit

**In plain English:** We clean up the accidental file, then append a second
line to the *correct* file using both fixes at once — quote the path AND use
`>>` so we don't wipe the first line. Then we audit with `test -f` and a line
count to prove the trap file is gone and the real file has two lines.

Run this:

```bash
rm -f "${SANDBOX}/my"
echo "second test, properly quoted" >> "${SANDBOX}/my file.txt"
cat "${SANDBOX}/my file.txt"
echo "exit was: $?"
```

Before I explain — why `>>` and not `>` here? (Type your guess.)

**After you've answered, line by line:**

- `rm -f "${SANDBOX}/my"` — Remove the accidental `my` file; `-f` = "force,
  don't error if it's already missing."
- `echo "second test, properly quoted" >> "${SANDBOX}/my file.txt"` — Append
  a second line; `>>` preserves the first line, and the quoted path keeps the
  space as one token (T01-B fixed).
- `cat "${SANDBOX}/my file.txt"` — Read the file back to confirm both lines
  survived.
- `echo "exit was: $?"` — Print the exit status of `cat`.

Both fixes are required together: quote the path AND choose `>>` over `>`. You
should see two lines and `exit was: 0`.

Now audit with `test -f`:

```bash
test -f "${SANDBOX}/my"          && echo "my exists (FAIL)" || echo "my gone (OK)"
test -f "${SANDBOX}/my file.txt"  && echo "target exists (OK)" || echo "target missing (FAIL)"
wc -l < "${SANDBOX}/my file.txt"
```

Line by line:

- `test -f "${SANDBOX}/my" && echo "my exists (FAIL)" || echo "my gone (OK)"`
  — `test -f` returns success if the path is a regular file; `&&` runs the
  first echo on success, `||` ("or else") runs the second on failure. We
  WANT `my gone (OK)` — the accidental file should no longer exist.
- `test -f "${SANDBOX}/my file.txt" && echo "target exists (OK)" || echo "target missing (FAIL)"`
  — Same one-line pass/fail check for the real file; here we WANT `target
  exists (OK)`.
- `wc -l < "${SANDBOX}/my file.txt"` — Count the lines; `-l` = count lines,
  `<` feeds the file as input so you get just the number.

Knowing exactly what's on disk is where cleanup discipline (T44) starts. Both
audit lines should say `(OK)`, and `wc -l` should print `2`.

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

**In plain English:** "Persistence" is the question *would this survive a
reboot?* We check what `/tmp` is mounted on to answer it.

```bash
findmnt /tmp
```

- `findmnt /tmp` — Show what storage `/tmp` is mounted on, including its
  filesystem type.

`/tmp` is volatile — nothing here survives reboot. That's why sandboxes live
here, not in `/etc`.

**New words in this step:**
- **persistence** — whether a file *survives a reboot* (stays) or disappears.

---

### Journal write (before cleanup — Section 14)

**In plain English:** Write a small "I finished Task 1" record into the durable
`/root` journal before tearing the sandbox down.

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

Line by line:

- `LAB=lab01` / `TASK=task1b` — Short labels for this lab and task.
- `JDIR="/root/rhcsa_journal/${LAB}/${TASK}"` — Build the journal folder path
  under `/root`.
- `mkdir -p "$JDIR"` — Create it, making parents as needed.
- `cat > "$JDIR/done.txt" <<EOF` plus its lines — Open a *heredoc* (a block of
  inline text fed straight into a file) and write the completion record; this
  unquoted `EOF` lets `$(date -Is)` and friends run and paste their answers
  in.
- `cat > "$JDIR/notes.txt" <<EOF` plus its lines — Write the study notes:
  topic, traps, any quiz misses, and what's next.
- `echo "Journal written: $(ls -la $JDIR)"` — Confirm by listing the folder
  (`ls -la` = long format including hidden files).
- `echo "exit was: $?"` — Print the exit status.

**New words in this step:**
- **heredoc** — a block of text typed inline that gets fed into a command or
  file, ending at a marker word like `EOF`.

---

### Cleanup (Section 6)

**In plain English:** Tear down the lab user, group, and sandbox, then *audit*
that nothing got left behind. A leftover account, group, or folder is an
"orphan," and leaving one is the T44 mistake.

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

Line by line:

- `set +e` — Turn OFF "stop on first error" so cleanup runs to the end even if
  a step has nothing to remove.
- `if getent passwd "${LAB_USER}" >/dev/null 2>&1; then userdel -r "${LAB_USER}" 2>/dev/null; fi`
  — If the lab user exists, delete it; `-r` also removes its home directory.
- `if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi`
  — If the lab group exists, delete it.
- `rm -rf "${SANDBOX}"` — Delete the sandbox and everything in it; `-r` =
  recursive, `-f` = force.
- `echo "── cleanup audit ──"` — Print a header for the verification lines.
- `getent passwd "${LAB_USER}" && echo "user remains (FAIL)" || echo "user gone (OK)"`
  — Check for the user again; print FAIL if still present, or else OK. We want
  `user gone (OK)` — no orphan account.
- `getent group "${GROUP}" && ... (FAIL) || ... (OK)` — Same check for the
  group; we want `group gone (OK)`.
- `test -d "${SANDBOX}" && ... (FAIL) || ... (OK)` — Check the folder; `test
  -d` asks "is this a directory?" We want `sandbox gone (OK)`.
- `set -e` — Turn "stop on first error" back on.
- `echo "exit was: $?"` — Print the final exit status.

**New words in this step:**
- **orphan** — a leftover user, group, or directory that cleanup missed.

All rows must say `(OK)`. **STOP** — do not open Task 2 until pasted.

---

## TASK 2 of 2 — Ansible boundary: no module for `>` or `>>`

**In plain English:** We write a tiny Ansible playbook that does the only
honest thing it can with redirection — shell out — then run it twice to prove
it's *not idempotent*, document that boundary on disk, and finish with a
T31 awareness demo about `usermod` groups.

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

### Step 1 of 2 — Write the playbook, then run it twice to prove non-idempotence

**In plain English:** We write a playbook that uses `shell:` (the only honest
substitute, since no Ansible module owns `>`), then run it twice. A
well-behaved Ansible task reports `changed=0` on the second run because
nothing needed changing — that property is *idempotence*. This one reports
`changed=1` both times, which is the boundary made visible.

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

Before I explain — why `ansible.builtin.shell:` and not `command:`? (Type
your guess.)

**After you've answered, line by line:**

- `mkdir -p /root/rhcsa_journal/lab01/playbooks` — Create the durable folder
  to hold the playbook (`-p` = make parents, don't error if present).
- `cat > .../task2b.yml <<'EOF'` — Open a heredoc and write the playbook into
  `task2b.yml`; the quoted `'EOF'` means "write the text exactly, don't
  expand `$(...)` or `{{ }}` here in the shell."
- `- name: ...` / `hosts: localhost` / `connection: local` — Name the play and
  tell Ansible to run it on this machine directly.
- `gather_facts: false` — Skip Ansible's fact-collection step (we don't need
  it).
- `vars: target: "/tmp/labsandbox_01/notes.txt"` — Define a variable for the
  file path so the task below can reuse it.
- `ansible.builtin.shell: |` — Use the `shell` module, which spawns
  `/bin/bash` so `>` is actually interpreted as redirection; the `|` keeps the
  command as a literal multi-line block.
- `echo "ansible wrote at $(date -Is)" > "{{ target }}"` — Write a
  timestamped line to the file; `{{ target }}` is a *Jinja2 template*
  expression (Ansible's way of pasting a variable's value in, like the shell's
  `$()`).
- `register: write_result` — Save the task's result (its return code, changed
  flag, and output) into a variable.
- `failed_when: write_result.rc != 0` — Mark the task failed only if the
  shell command's return code isn't `0`.
- `ansible.builtin.debug: msg: [...]` — Print the captured return code,
  changed flag, and stdout so you can read what happened.
- `ls -l /root/.../task2b.yml` — Long-list the playbook file to confirm it was
  written.

For contrast: `ansible.builtin.command:` runs WITHOUT a shell, so `>` would be
passed to `echo` as literal text rather than acting as redirection — which is
why we must use `shell:` here. There is no `ansible.builtin` module for `>` or
`>>`; `shell:` is the closest honest substitute. Section 18 says state that
boundary explicitly rather than pretend a module exists.

Now run it twice and check the file:

```bash
ansible-playbook /root/rhcsa_journal/lab01/playbooks/task2b.yml
ansible-playbook /root/rhcsa_journal/lab01/playbooks/task2b.yml
cat /tmp/labsandbox_01/notes.txt
```

Before I explain — predict the `changed=` count on BOTH runs. (Type your
guess.)

**After you've answered, line by line:**

- first `ansible-playbook ...` — Run the playbook; the first run shows
  `changed=1` because the file gets created/overwritten.
- second `ansible-playbook ...` — Run it again; it shows `changed=1` AGAIN
  because the timestamp differs every time, so Ansible can't tell the state is
  "already correct."
- `cat /tmp/labsandbox_01/notes.txt` — Read the file; only the second run's
  timestamp survives, because each run's `>` truncated the previous content
  (T01-A in action).

Ansible cannot know whether the file "should" contain this timestamp, so it
runs the shell command every time. That proves RHCSA muscle memory for `>`/`>>`
cannot be outsourced to Ansible: idempotence needs a state-aware module, and
there isn't one for redirection. Paste both PLAY RECAPs and the `cat` output.

**New words in this step:**
- **idempotence** — the property that running something twice leaves the same
  end state with no extra change reported; `changed=0` on a re-run is the
  proof.
- **Jinja2 template** — Ansible's text-substitution syntax (`{{ ... }}`) that
  pastes a variable's value into a string.

---

### Step 2 of 2 — Write BOUNDARY.txt, then the T31 `usermod -G` awareness demo

**In plain English:** We record the Ansible-vs-shell boundary in a durable
note, then run a quick demo of a *different* category's trap (T31): using
`usermod -G` without `-a` silently replaces a user's groups instead of adding
to them. Then we restore the groups.

Run this:

```bash
cat > /root/rhcsa_journal/lab01/playbooks/BOUNDARY.txt <<'EOF'
BOUNDARY: no ansible.builtin module for stdout redirection (> or >>).
SUBSTITUTE: ansible.builtin.shell: with register: and failed_when:
PROOF: two runs both show changed=1 — not idempotent.
CONCLUSION: RHCSA muscle memory for >, >>, |, tee is required.
EOF
cat /root/rhcsa_journal/lab01/playbooks/BOUNDARY.txt
```

Line by line:

- `cat > .../BOUNDARY.txt <<'EOF' ... EOF` — Open a heredoc and write the
  four-line boundary statement into `BOUNDARY.txt`; the quoted `'EOF'` means
  "write the text exactly, no variable expansion."
- the four text lines — Document the boundary: no module exists, `shell:` is
  the substitute, two runs proved non-idempotence, and shell muscle memory is
  required.
- `cat /root/rhcsa_journal/lab01/playbooks/BOUNDARY.txt` — Read the note back
  to confirm it was written.

We keep this in `/root` (which survives reboot) rather than volatile `/tmp` —
that's the T41 persistence habit. Paste output.

Now the T31 awareness demo:

```bash
id -nG "${LAB_USER}"
usermod -G wheel "${LAB_USER}" 2>/dev/null || echo "wheel group may not exist — that's OK for the demo"
id -nG "${LAB_USER}"
```

Before I explain — what did `usermod -G` do to `${LAB_USER}`'s groups? (Type
your guess.)

**After you've answered, line by line:**

- `id -nG "${LAB_USER}"` — Show the user's group names; `-n` = print names not
  numbers, `-G` = list all groups. This is the "before" snapshot.
- `usermod -G wheel "${LAB_USER}" 2>/dev/null || echo "wheel group may not exist — that's OK for the demo"`
  — `usermod -G wheel` REPLACES all of the user's *supplementary groups* (the
  extra groups beyond the main one) with just `wheel`; `2>/dev/null` hides an
  error and `||` ("or else") prints a note if `wheel` doesn't exist. The
  CORRECT form is `usermod -aG wheel`, where `-a` means "append" — that's T31.
- `id -nG "${LAB_USER}"` — Show the groups again; the "after" snapshot reveals
  that the previous group membership was wiped, not added to.

`-G` alone wipes existing supplementary groups; `-aG` adds to them. T31 is the
same class of "silent destruction" as T01-A/T01-B — the command succeeds, and
the damage is invisible until you inspect.

Now restore the groups if `wheel` exists:

```bash
usermod -aG "${GROUP}" "${LAB_USER}" 2>/dev/null || true
id -nG "${LAB_USER}"
```

Line by line:

- `usermod -aG "${GROUP}" "${LAB_USER}" 2>/dev/null || true` — Add the lab
  group back the CORRECT way; `-aG` appends without wiping, and `|| true`
  ("or else succeed") keeps the exit status at `0` if there's nothing to do.
- `id -nG "${LAB_USER}"` — Show the groups once more to confirm the lab group
  is back.

Paste output.

**New words in this step:**
- **supplementary group** — an *extra* group a user belongs to beyond their
  one main (primary) group.

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

**In plain English:** Confirm the durable boundary note survives while the
`/tmp` sandbox file is volatile, and note that the lab user lives on disk until
cleanup.

```bash
test -f /root/rhcsa_journal/lab01/playbooks/BOUNDARY.txt && echo "boundary doc survives (OK)"
test -f /tmp/labsandbox_01/notes.txt && echo "sandbox file volatile" || echo "sandbox gone or never existed"
getent passwd "${LAB_USER}" && echo "LAB_USER on disk until cleanup (T44)"
```

Line by line:

- `test -f /root/.../BOUNDARY.txt && echo "boundary doc survives (OK)"` —
  Check the boundary note exists on durable `/root`; `test -f` confirms it's a
  regular file and `&&` runs the echo on success.
- `test -f /tmp/labsandbox_01/notes.txt && echo "sandbox file volatile" || echo "sandbox gone or never existed"`
  — Check the sandbox file; whether present or not, the point is it lives in
  volatile `/tmp`.
- `getent passwd "${LAB_USER}" && echo "LAB_USER on disk until cleanup (T44)"`
  — Look the lab user up; if found, it's a real on-disk account that WOULD
  survive reboot — exactly why cleanup is mandatory.

Paste output.

---

### Journal write (before cleanup)

**In plain English:** Write the "I finished Task 2" record into the durable
`/root` journal.

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

Line by line:

- `LAB=lab01` / `TASK=task2b` — Short labels for this lab and task.
- `JDIR="/root/rhcsa_journal/${LAB}/${TASK}"` — Build the journal folder path.
- `mkdir -p "$JDIR"` — Create it, making parents as needed.
- `cat > "$JDIR/done.txt" <<EOF` plus its lines — Write the completion record;
  the unquoted `EOF` lets `$(date -Is)` and friends run.
- `cat > "$JDIR/notes.txt" <<EOF` plus its lines — Write the study notes:
  topic, traps, the non-idempotence proof, the boundary path, and what's next.
- `echo "Journal written: $(ls -la $JDIR)"` — Confirm by listing the folder.
- `echo "exit was: $?"` — Print the exit status.

---

### Cleanup (Section 6 — final)

**In plain English:** Final teardown and orphan audit. Every row must read
`(OK)`.

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

Line by line:

- `set +e` — Turn off stop-on-error so cleanup runs to the end.
- `if getent passwd "${LAB_USER}" ...; then userdel -r "${LAB_USER}" ...; fi`
  — If the lab user exists, delete it along with its home (`-r`).
- `if getent group "${GROUP}" ...; then groupdel "${GROUP}" ...; fi` — If the
  lab group exists, delete it.
- `rm -rf "${SANDBOX}"` — Delete the sandbox tree (`-r` recursive, `-f`
  force).
- `echo "── cleanup audit ──"` — Header for the verification lines.
- `getent passwd "${LAB_USER}" && ... (FAIL) || ... (OK)` — Check the user is
  gone; we want `user gone (OK)`, no orphan account.
- `getent group "${GROUP}" && ... (FAIL) || ... (OK)` — Check the group is
  gone; we want `group gone (OK)`.
- `test -d "${SANDBOX}" && ... (FAIL) || ... (OK)` — Check the folder is gone;
  we want `sandbox gone (OK)`.
- `set -e` — Re-enable stop-on-error.
- `echo "exit was: $?"` — Print the final exit status.

All rows `(OK)`.

### Drill (after cleanup)

**In plain English:** Run the tier-1 practice quiz to lock in the muscle
memory.

```bash
python3 ~/scripts/rhcsa_drill.py --tier 1
```

- `python3 ~/scripts/rhcsa_drill.py --tier 1` — Run the drill script limited
  to tier-1 questions.

**STOP — lab-01b complete.** Begin lab-01c only after cleanup audit and drill
are pasted.
