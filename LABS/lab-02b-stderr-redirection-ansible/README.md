# Lab 02b: Standard Error Redirection — Ansible (`ansible.builtin.shell` with `register:` and `stderr_lines`)

- **Series:** linux-ops-mastery — Shells, Terminals & Redirection
- **Trilogy:** [`02a`](../lab-02a-stderr-redirection-rhcsa/) (RHCSA hand-typed) → **`02b`** (Ansible — you are here) → [`02c`](../lab-02c-stderr-redirection-verify/) (Verify)
- **Career arcs covered:** RHCSA EX200 (understand that shell tasks in Ansible expose both stdout and stderr via `register:`), DevOps (distinguish expected errors from real failures in CI pipelines), SRE (alert on unexpected stderr patterns while tolerating known noise)
- **Prerequisite:** [`Lab 02a`](../lab-02a-stderr-redirection-rhcsa/) completed; `/root/rhcsa_journal/lab-02a/task1/` and `task2/` populated
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = capture and inspect `stderr_lines` from `ansible.builtin.shell`; Task 2 = selective failure with `failed_when:` vs `ignore_errors:`)
- **Practice Directory (rotation #02):** `/tmp/lab02b` (reads against `/var/log`)
- **Playbooks:** `/root/rhcsa_journal/lab-02b/playbooks/`
- **Traps rehearsed this lab:** **T02-C** (not checking `stderr_lines` — assuming a task succeeded because `rc=0`, missing silent errors) · **T02-D** (`ignore_errors: yes` swallows ALL failures including real ones; `failed_when:` targets only specific conditions) · **T41** (skipping the `failed_when:` re-run — the whole point of Task 2)

> **This lab's practice directory is: `/tmp/lab02b`** — reads against `/var/log` (same as 02a). The shell task generates both stdout (log paths) and stderr (`Permission denied`); `register:` captures them as separate lists.

---

## LAB HEADER BLOCK

```bash
echo "--- Ansible controller ---"
ansible --version
echo ""
echo "--- Python binding ---"
python3 --version 2>/dev/null || python --version
echo ""
echo "--- localhost connection test ---"
ansible localhost -m ping --connection=local 2>/dev/null \
    && echo "✅ localhost reachable" \
    || echo "❌ localhost ping failed"
echo ""
echo "--- /var/log access ---"
ls -ld /var/log
ls /var/log | wc -l
echo ""
echo "--- 02a prereq check ---"
ls /root/rhcsa_journal/lab-02a/task1/done.txt \
   /root/rhcsa_journal/lab-02a/task2/done.txt 2>/dev/null \
    && echo "✅ 02a journal present" \
    || echo "❌ 02a journal missing — complete Lab 02a first"
echo "exit was: $?"
```

> **STOP — paste the output before setup. If `ls /var/log | wc -l` returns 0, something is wrong with the system — `/var/log` is always populated on RHEL.**

---

## Objective

02a built the `2>` / `2>/dev/null` muscle in the shell. 02b exposes the same concept in Ansible: when you run a shell command with `ansible.builtin.shell`, the module automatically splits the output into `stdout_lines` (FD 1) and `stderr_lines` (FD 2) in the registered result.

1. **Capture both streams** from a `find /var/log` command. `result.stdout_lines` holds the log paths; `result.stderr_lines` holds the `Permission denied` errors — identical to `>` and `2>` in 02a, but separated automatically by the module.
2. **Inspect the registered result** — `result.rc`, `result.stdout_lines`, `result.stderr_lines` are the Ansible equivalents of the exit code, stdout file, and stderr file from 02a.
3. **Understand `failed_when:`** — the Ansible-native way to tolerate known stderr content while still failing on unexpected errors. This is more precise than `ignore_errors: yes`.
4. **Prove T02-D** — show that `ignore_errors: yes` is a blunt instrument (it hides even real failures), while `failed_when:` is a surgical one (it fails only on your specified condition).

---

## Concept: `register:` Splits Streams — No `2>` Required

```
SHELL (02a)                            ANSIBLE (02b)
──────────────────────────────────     ──────────────────────────────────────────
find /var/log -name "*.log" \          ansible.builtin.shell:
    >  /tmp/log-files.txt \              cmd: "find /var/log -name '*.log' -type f"
    2> /tmp/log-errors.txt             register: result

cat /tmp/log-files.txt  (FD1)          result.stdout       (string, FD1 content)
cat /tmp/log-errors.txt (FD2)          result.stdout_lines (list,   FD1 per line)
                                       result.stderr       (string, FD2 content)
                                       result.stderr_lines (list,   FD2 per line)
                                       result.rc           (exit code)
```

**T02-C: Not checking `stderr_lines`**
A task can finish with `rc=0` and still produce stderr. `grep` on a readable file returns 0 even if it also prints a warning. Without checking `result.stderr_lines`, that warning is invisible.

**T02-D: `ignore_errors: yes` vs `failed_when:`**
`ignore_errors: yes` — the play continues regardless of rc, stdout, or stderr. Real failures are silently swallowed.
`failed_when:` — the play fails only when YOUR condition is true. You can tolerate `Permission denied` while still catching real errors like `No such file or directory (parent path missing)`.

---

## Reference — `ansible.builtin.shell` Result Keys Used This Lab

| Key                   | Type   | What it holds                                                      |
|-----------------------|--------|--------------------------------------------------------------------|
| `result.rc`           | int    | Exit code of the shell command                                     |
| `result.stdout`       | string | Everything written to FD 1 (newlines preserved)                    |
| `result.stdout_lines` | list   | FD 1 content split on newlines — one element per line              |
| `result.stderr`       | string | Everything written to FD 2                                         |
| `result.stderr_lines` | list   | FD 2 content split on newlines                                     |
| `result.changed`      | bool   | Always `true` for shell tasks unless you add `changed_when: false` |
| `result.cmd`          | string | The command that was run                                           |

---

## Lab-Wide Setup

```bash
sudo -i

mkdir -p /tmp/lab02b
mkdir -p /root/rhcsa_journal/lab-02b/playbooks
mkdir -p /root/rhcsa_journal/lab-02b/task1
mkdir -p /root/rhcsa_journal/lab-02b/task2

ls -ld /tmp/lab02b /root/rhcsa_journal/lab-02b/
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the `ls -ld` output before Task 1.**

---

## Task 1 — Capture and inspect `stderr_lines` from `ansible.builtin.shell`

**Practice directory this task:** `/tmp/lab02b` (reads against `/var/log`)

### Warm-Up

```bash
# What does a non-root find generate — baseline for what the playbook will see
find /var/log -name "*.log" -type f 2>/dev/null | head -5
find /var/log -name "*.log" -type f 2>&1 | grep 'Permission denied' | head -3
# How many log files vs errors
find /var/log -name "*.log" -type f > /dev/null 2>/tmp/lab02b/warmup-errors.txt
wc -l /tmp/lab02b/warmup-errors.txt
# Confirm ansible-doc shows register keys
ansible-doc ansible.builtin.shell 2>/dev/null | grep -E '(stdout_lines|stderr_lines|rc:)' | head -6
echo "exit was: $?"
```

> Carry from Lab 02a: `find /var/log -name "*.log" 2>`, `grep 'Permission denied'`. The WEAVE below maps each warm-up command to its role.

### Purpose

Run `find /var/log -name "*.log" -type f` via `ansible.builtin.shell`, register the result, and demonstrate that:

1. `result.stdout_lines` is a list of log file paths (FD 1 — the "stdout" stream).
2. `result.stderr_lines` is a list of `Permission denied` strings (FD 2 — the "stderr" stream).
3. The shell task can have `rc=1` AND still have useful stdout content — `rc` alone is not the whole story.
4. Each stream can be saved to a file using `ansible.builtin.copy: content: "{{ result.stdout }}"`.

### WEAVE TRACE

| Warm-up / setup command                   | Role inside Task 1                                                        |
|-------------------------------------------|---------------------------------------------------------------------------|
| `find ... 2>/dev/null \| head -5`         | Shows what `result.stdout_lines` will look like                           |
| `find ... 2>&1 \| grep 'Permission denied'`| Shows what `result.stderr_lines` will look like                          |
| `wc -l warmup-errors.txt`                 | Baseline stderr line count — used to sanity-check `stderr_lines \| length`|
| `ansible-doc shell \| grep stdout_lines`  | Confirms the key names in the registered result before using them         |

### Main command block

```bash
TASKLOG=/tmp/lab02b/task1.txt
PB=/root/rhcsa_journal/lab-02b/playbooks/task1.yml

# ── Step 1: Write the playbook ────────────────────────────────────────
cat > "${PB}" << 'PLAYBOOK'
---
- name: "Lab 02b Task 1 — capture stderr_lines from ansible.builtin.shell"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    output_dir: /tmp/lab02b

  tasks:
    - name: "Ensure practice directory exists"
      ansible.builtin.file:
        path: "{{ output_dir }}"
        state: directory
        mode: '0755'

    - name: "Find .log files — captures stdout AND stderr separately via register:"
      ansible.builtin.shell:
        cmd: "find /var/log -name '*.log' -type f"
      register: find_result
      failed_when: false
      changed_when: false

    - name: "Show the split capture — stdout_lines vs stderr_lines"
      ansible.builtin.debug:
        msg:
          - "rc:                  {{ find_result.rc }}"
          - "stdout lines:        {{ find_result.stdout_lines | length }}"
          - "stderr lines:        {{ find_result.stderr_lines | length }}"
          - "first stdout line:   {{ find_result.stdout_lines[0] | default('(none)') }}"
          - "first stderr line:   {{ find_result.stderr_lines[0] | default('(none)') }}"

    - name: "Save stdout (log paths) to file"
      ansible.builtin.copy:
        dest: "{{ output_dir }}/log-files.txt"
        content: "{{ find_result.stdout }}\n"
        mode: '0644'

    - name: "Save stderr (Permission denied lines) to file"
      ansible.builtin.copy:
        dest: "{{ output_dir }}/log-errors.txt"
        content: "{{ find_result.stderr }}\n"
        mode: '0644'

    - name: "T02-C proof — assert stderr_lines was actually checked"
      ansible.builtin.debug:
        msg:
          - "T02-C: if we had NOT checked stderr_lines we would never see:"
          - "{{ find_result.stderr_lines[:3] }}"
          - "(this list was invisible if you only looked at rc)"
PLAYBOOK

echo "Playbook written: $(wc -l < ${PB}) lines"                    2>&1 | tee $TASKLOG

# ── Step 2: Run the playbook ──────────────────────────────────────────
echo "═══ Step 2: apply playbook ═══"                              | tee -a $TASKLOG
ansible-playbook "${PB}" 2>&1                                      | tee -a $TASKLOG
echo "apply exit was: $?"                                          | tee -a $TASKLOG

# ── Step 3: Verify split capture on disk ──────────────────────────────
echo "═══ Step 3: verify split capture on disk ═══"               | tee -a $TASKLOG
wc -l /tmp/lab02b/log-files.txt /tmp/lab02b/log-errors.txt        | tee -a $TASKLOG
grep -c 'Permission denied' /tmp/lab02b/log-errors.txt            | tee -a $TASKLOG
grep -c '\.log$'             /tmp/lab02b/log-files.txt             | tee -a $TASKLOG

# stream-separation check (mirrors 02a Task 1 assertions)
PD_IN_FILES=$(grep -c 'Permission denied' /tmp/lab02b/log-files.txt 2>/dev/null || echo 0)
test "${PD_IN_FILES}" -eq 0 \
    && echo "✅ stdout file has NO Permission denied" \
    || echo "❌ stdout file contaminated" \
    | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. **`failed_when: false`** — by default, `ansible.builtin.shell` fails when `rc != 0`. `find` returns rc=1 when it encounters `Permission denied`. Without `failed_when: false`, the play would abort before we could inspect `stderr_lines`. This is the explicit, visible version of `2>/dev/null`.
2. **`changed_when: false`** — `find` is a read-only operation that never changes system state. Without this, the PLAY RECAP would always show `changed=1`, which is misleading.
3. **`find_result.stdout_lines[:3]`** — Jinja2 slice syntax; the first three elements of the list. Equivalent to `head -3` in the shell.
4. **`content: "{{ find_result.stdout }}\n"`** — the `\n` adds a final newline. Without it, `wc -l` would report one fewer line than expected (last line has no newline terminator).
5. **Stream-separation check** — mirrors 02a Task 1: stdout file must have zero `Permission denied` lines; stderr file must have non-zero `Permission denied` lines.

### Reading it left to right

```
find_result.stderr_lines | length
│            │           │
│            │           └─ Jinja2 filter: count elements in the list
│            └─ list attribute: one element per FD2 line
└─ the registered result variable
```

```
find_result.stderr_lines[:3]
│            │           │
│            │           └─ Python-style slice: first 3 elements
│            └─ list of all FD2 lines
└─ registered result
```

### The story

`register:` is Ansible's answer to the file-redirect dance. In 02a you wrote `2>errors.txt` to capture stderr separately. In Ansible, you don't need to — the module does the split automatically. But there's a T02-C trap hiding in the convenience: because you can ignore `result.stderr_lines` entirely and the play will still finish with `rc=0` in many cases, people ship playbooks that produce hundreds of warning lines every run and never notice because they only check the PLAY RECAP.

The habit to build: always check `result.stderr_lines | length` in your debug task. Non-zero stderr isn't always failure — it's always information.

### Expected output

```text
Playbook written: 40 lines
═══ Step 2: apply playbook ═══

PLAY [Lab 02b Task 1 ...] ******************************************************
...
TASK [Show the split capture] **************************************************
ok: [localhost] => {
    "msg": [
        "rc:                  1",
        "stdout lines:        24",
        "stderr lines:        3",
        "first stdout line:   /var/log/audit/audit.log",
        "first stderr line:   find: '/var/log/private': Permission denied"
    ]
}
...
PLAY RECAP ******* localhost : ok=5  changed=2  unreachable=0  failed=0
apply exit was: 0
═══ Step 3: verify split capture on disk ═══
   21 /tmp/lab02b/log-files.txt
    3 /tmp/lab02b/log-errors.txt
3
21
✅ stdout file has NO Permission denied
exit was: 0
```

### Switches

| Token                                         | Meaning                                                             |
|-----------------------------------------------|---------------------------------------------------------------------|
| `register: result`                            | Capture module return value                                         |
| `result.stdout_lines`                         | List of FD 1 lines                                                  |
| `result.stderr_lines`                         | List of FD 2 lines                                                  |
| `result.rc`                                   | Exit code (int)                                                     |
| `failed_when: false`                          | Never fail this task regardless of rc                               |
| `changed_when: false`                         | Never report this task as changed                                   |
| `LIST \| length`                              | Jinja2 filter: count list elements                                  |
| `LIST[:N]`                                    | Jinja2 slice: first N elements                                      |
| `LIST[0] \| default('(none)')`                | First element with fallback for empty list                          |

### Concept Card

| Concept | What it does |
|---|---|
| `register:` split | `result.stdout_lines` = FD1 list; `result.stderr_lines` = FD2 list — automatic split, no `2>` needed |
| `failed_when: false` | Tolerate any `rc` — essential when the command legitimately produces non-zero exit |
| `changed_when: false` | Mark read-only tasks honestly — prevents misleading `changed=N` in PLAY RECAP |
| T02-C | Check `stderr_lines \| length` — non-zero stderr with rc=0 is invisible without this |
| `content: result.stdout` | Saves the FD1 content to a file — Ansible's `> file` equivalent |
| **🪤 Trap Risk T02-C** | A task with `rc=0` and non-empty `stderr_lines` looks like success. Always inspect stderr. |
| **🪤 Trap Risk T02-D** | `ignore_errors: yes` hides real failures. Use `failed_when:` to target only expected errors. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| `log-files.txt` written | `test -s /tmp/lab02b/log-files.txt` returns 0 | Stdout captured to file |
| `log-errors.txt` written | `test -s /tmp/lab02b/log-errors.txt` returns 0 | Stderr captured to file |
| Stream separation | `grep -c 'Permission denied' log-files.txt` returns 0 | FD1 has no FD2 contamination |
| Playbook persists | `test -s /root/rhcsa_journal/lab-02b/playbooks/task1.yml` | Reconstruction point |

### Journal write

```bash
LAB=lab-02b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab02b/task1.txt           "$JDIR/evidence.txt"
cp /tmp/lab02b/log-files.txt       "$JDIR/log-files.txt"
cp /tmp/lab02b/log-errors.txt      "$JDIR/log-errors.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    ansible.builtin.shell with register: — split stdout_lines / stderr_lines; failed_when: false; changed_when: false
COMMANDS: ansible-playbook PB; result.stdout_lines | length; result.stderr_lines[:3]; grep -c 'Permission denied'
TRAPS:    T02-C rehearsed (checked stderr_lines explicitly); T02-D deferred to Task 2
SPLIT:    log-files.txt has log paths; log-errors.txt has Permission denied lines; no contamination
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — failed_when: selective failure vs ignore_errors: yes (T02-D proof)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab02b/warmup-errors.txt /tmp/lab02b/task1.txt
ls /tmp/lab02b/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `result.stderr_lines` is empty | Running as root with full access to `/var/log`. Try running the find as a restricted user — or use a directory you can't read (e.g., `find /var/log/audit`) |
| `PLAY RECAP failed=1` on the find task | Remove `failed_when: false` accidentally — it must be present to tolerate `rc=1` |
| `log-errors.txt` is 1 byte (newline only) | `find` had no `Permission denied` errors. Try `/var/log/audit` as the target |
| Jinja2 `\| length` error in debug | Running an older Ansible version. Use `result.stdout_lines \| count` instead |

> **STOP — paste the debug task output (rc, stdout lines, stderr lines counts) and the `✅ stdout file has NO Permission denied` line before Task 2.**

---

## Task 2 — Selective failure with `failed_when:` (T02-D proof)

**Practice directory this task:** `/tmp/lab02b`

### Warm-Up

```bash
cat /tmp/lab02b/log-errors.txt
wc -l /tmp/lab02b/log-errors.txt
grep -c 'Permission denied' /tmp/lab02b/log-errors.txt
echo "Warm-up done at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: `result.stderr_lines`, `failed_when:`, `grep -c`. The warm-up confirms the stderr content from Task 1 is still on disk.

### Purpose

1. **Prove `failed_when:`** — run the `find` command and fail ONLY if stderr contains something other than `Permission denied` (i.e., an unexpected error).
2. **Prove `ignore_errors: yes` is a blunt instrument (T02-D)** — show a deliberately broken command that fails silently under `ignore_errors: yes` but triggers correctly under `failed_when:`.
3. **See the difference in PLAY RECAP output** — `ignore_errors: yes` shows `failed=0, ignored=1`; a real failure with `failed_when:` shows `failed=1` and halts the play.

### WEAVE TRACE

| Warm-up / setup command                   | Role inside Task 2                                                       |
|-------------------------------------------|--------------------------------------------------------------------------|
| `cat /tmp/lab02b/log-errors.txt`          | Shows the baseline stderr pattern — only `Permission denied` expected    |
| `grep -c 'Permission denied' log-errors.txt` | Confirms error count — used to verify the `failed_when:` condition is correct |
| `wc -l log-errors.txt`                    | Line count sanity check before the Task 2 playbook runs                  |

### Main command block

```bash
TASKLOG=/tmp/lab02b/task2.txt
PB2=/root/rhcsa_journal/lab-02b/playbooks/task2.yml

# ── Step 1: Write the playbook ────────────────────────────────────────
cat > "${PB2}" << 'PLAYBOOK'
---
- name: "Lab 02b Task 2 — failed_when: selective failure vs ignore_errors: (T02-D)"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    output_dir: /tmp/lab02b

  tasks:
    - name: "Find .log files — fail ONLY on unexpected errors"
      ansible.builtin.shell:
        cmd: "find /var/log -name '*.log' -type f"
      register: selective_result
      changed_when: false
      failed_when: >
        selective_result.rc != 0 and
        (selective_result.stderr_lines
         | reject('search', 'Permission denied')
         | list | length) > 0

    - name: "Show selective result"
      ansible.builtin.debug:
        msg:
          - "rc:                       {{ selective_result.rc }}"
          - "total stderr lines:       {{ selective_result.stderr_lines | length }}"
          - "unexpected stderr lines:  {{ selective_result.stderr_lines | reject('search', 'Permission denied') | list | length }}"
          - "task PASSED (only Permission denied in stderr — expected)"

    - name: "T02-D: ignore_errors demo — broken find path (swallows real error)"
      ansible.builtin.shell:
        cmd: "find /DOES_NOT_EXIST -name '*.log' -type f"
      register: broken_result
      ignore_errors: true
      changed_when: false

    - name: "T02-D: show that ignore_errors hid the real failure"
      ansible.builtin.debug:
        msg:
          - "rc:           {{ broken_result.rc }}"
          - "stderr:       {{ broken_result.stderr_lines }}"
          - "ignore_errors: play continued — real error is INVISIBLE in PLAY RECAP"

    - name: "T02-D: same broken path — failed_when: catches it properly"
      ansible.builtin.shell:
        cmd: "find /DOES_NOT_EXIST -name '*.log' -type f"
      register: caught_result
      changed_when: false
      failed_when: >
        caught_result.rc != 0 and
        (caught_result.stderr_lines
         | reject('search', 'Permission denied')
         | list | length) > 0
      ignore_errors: true

    - name: "T02-D: compare outcome"
      ansible.builtin.debug:
        msg:
          - "failed_when: caught the unexpected error (rc={{ caught_result.rc }})"
          - "stderr:      {{ caught_result.stderr_lines }}"
          - "Conclusion:  failed_when: is the surgical tool; ignore_errors: is the sledgehammer"
PLAYBOOK

echo "Playbook written: $(wc -l < ${PB2}) lines"                   2>&1 | tee $TASKLOG

# ── Step 2: Run the playbook ──────────────────────────────────────────
echo "═══ Step 2: apply Task 2 playbook ═══"                       | tee -a $TASKLOG
ansible-playbook "${PB2}" 2>&1                                     | tee -a $TASKLOG
echo "apply exit was: $?"

echo "exit was: $?"
```

### Human-readable breakdown

1. **`failed_when:` condition.** `selective_result.stderr_lines | reject('search', 'Permission denied') | list | length > 0` means: "take the stderr lines, throw out any that mention Permission denied, count what remains — if count > 0, there are unexpected errors, fail." This is the surgical `failed_when:`.
2. **`ignore_errors: true` on the broken path.** The task fails (rc=1, stderr says "No such file"), but the play continues. The PLAY RECAP shows `ignored=1` — a clue, but easy to overlook.
3. **`failed_when:` on the broken path.** The `reject('search', 'Permission denied')` filter doesn't match "No such file or directory" — so the unexpected-error count is 1, and `failed_when:` triggers correctly.
4. **The comparison conclusion.** Two tasks, same broken path, different error-handling. One silently continues; one fails with an honest signal. The PLAY RECAP tells the story.

### Reading it left to right

```
stderr_lines | reject('search', 'Permission denied') | list | length > 0
│             │                                      │       │
│             │                                      │       └─ count remaining
│             │                                      └─ materialize generator to list
│             └─ Jinja2 filter: discard lines matching the pattern
└─ list of FD2 lines from the registered result
```

```
failed_when: rc != 0 and (unexpected_stderr_count) > 0
              │               │
              │               └─ only unexpected stderr makes us fail
              └─ rc=0 means success regardless of stderr content
```

### The story

`ignore_errors: yes` was added to Ansible for emergency hacks. It's the equivalent of putting `|| true` at the end of every command in a shell script. The problem: it hides signal. A developer adds `ignore_errors: yes` to tolerate one known error, and six months later a completely different error starts appearing — silently.

`failed_when:` is the replacement. You declare exactly which condition constitutes failure. Everything else — including `rc != 0` with only `Permission denied` in stderr — passes cleanly. The condition is readable, testable, and composable. It's the difference between `2>/dev/null` (silence everything) and `2> errors.txt; test $(wc -l < errors.txt) -eq 0` (capture and assert).

### Expected output

```text
Playbook written: 52 lines
═══ Step 2: apply Task 2 playbook ═══

TASK [Find .log files — fail ONLY on unexpected errors] ****
ok: [localhost]

TASK [Show selective result] *******************************************
ok: [localhost] => {
    "msg": [
        "rc:                       1",
        "total stderr lines:       3",
        "unexpected stderr lines:  0",
        "task PASSED (only Permission denied in stderr — expected)"
    ]
}

TASK [T02-D: ignore_errors demo — broken find path] ********************
...ignoring
ok: [localhost]

TASK [T02-D: show that ignore_errors hid the real failure] **************
ok: [localhost] => {
    "msg": [
        "rc:           1",
        "stderr:       [\"find: '/DOES_NOT_EXIST': No such file or directory\"]",
        "ignore_errors: play continued — real error is INVISIBLE in PLAY RECAP"
    ]
}

PLAY RECAP ******* localhost : ok=5  changed=0  unreachable=0  failed=0  ignored=1
apply exit was: 0
exit was: 0
```

### Switches

| Token                                                    | Meaning                                                          |
|----------------------------------------------------------|------------------------------------------------------------------|
| `failed_when: CONDITION`                                 | Fail the task only when CONDITION is true                        |
| `ignore_errors: true`                                    | Continue play even if this task fails (blunt instrument)         |
| `LIST \| reject('search', 'PAT')`                        | Jinja2: discard list elements matching PAT (regex)               |
| `LIST \| select('search', 'PAT')`                        | Jinja2: keep only elements matching PAT                          |
| `LIST \| list`                                           | Materialize a Jinja2 generator into a real list                  |
| `ignored=N` in PLAY RECAP                                | N tasks had `ignore_errors:` and actually failed                 |

### Concept Card

| Concept | What it does |
|---|---|
| `failed_when:` | Surgical failure condition — fail only on YOUR specified stderr pattern |
| `reject('search', PAT)` | Discards lines matching PAT — leaves only unexpected errors |
| `ignore_errors:` vs `failed_when:` | `ignore_errors:` is a sledgehammer; `failed_when:` is a scalpel (T02-D) |
| `ignored=N` in PLAY RECAP | Tells you how many tasks had `ignore_errors: true` AND actually failed |
| Non-zero stderr with rc=0 | T02-C: real scenario where only `stderr_lines` reveals the problem |
| **🪤 Trap Risk T02-C** | `rc=0` does not mean clean output. Always log `stderr_lines \| length`. |
| **🪤 Trap Risk T02-D** | `ignore_errors: yes` swallows real failures. Use `failed_when:` to target known-OK errors. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| `failed_when:` passed for expected errors | PLAY RECAP `failed=0` with `unexpected stderr lines: 0` | T02-D selective failure works |
| `ignore_errors:` demo showed `ignored=1` | PLAY RECAP `ignored=1` | Proves ignore_errors hides real failures |
| Both playbooks in journal | `ls /root/rhcsa_journal/lab-02b/playbooks/` | Reconstruction points |
| Task 2 journal written | `ls /root/rhcsa_journal/lab-02b/task2/` shows done.txt | Evidence chain |

### Journal write

```bash
LAB=lab-02b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab02b/task2.txt           "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    failed_when: selective failure vs ignore_errors: yes — T02-D proof
COMMANDS: ansible-playbook PB; stderr_lines | reject('search', 'PAT') | list | length; failed_when: rc != 0 and unexpected > 0
TRAPS:    T02-C rehearsed (stderr_lines inspected); T02-D proved (ignore_errors vs failed_when)
RESULT:   find with Permission denied only → task passed; find to nonexistent path → failed_when: caught it; ignore_errors missed it
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-02c — Verify trilogy: audit 02a and 02b evidence, stream-separation and order-trap proof
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab02b/task2.txt
ls /tmp/lab02b/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `failed_when:` condition triggers on expected errors | `reject('search', 'Permission denied')` filter typo — the string must match exactly what `find` prints |
| `result.stderr_lines \| reject(...)` Jinja2 error | Ansible < 2.8 doesn't support `reject`. Upgrade or use `selectattr` workaround |
| `PLAY RECAP` shows `failed=1` on the selective task | An unexpected error appeared in `/var/log` (e.g., filesystem error). Check the actual `stderr_lines` output |
| Both `ignore_errors` and `failed_when:` demo tasks show `ignored=0` | The broken path `/DOES_NOT_EXIST` was created between runs. Remove it first |

> **STOP — paste the `PLAY RECAP` line (showing `ignored=1`) and the `unexpected stderr lines: 0` message before the Trilogy Completion Check.**

---

## Trilogy Completion Check

```bash
find /root/rhcsa_journal/lab-02{a,b,c} -name done.txt 2>/dev/null | sort
# Expect 6 paths:
# /root/rhcsa_journal/lab-02a/task1/done.txt
# /root/rhcsa_journal/lab-02a/task2/done.txt
# /root/rhcsa_journal/lab-02b/task1/done.txt
# /root/rhcsa_journal/lab-02b/task2/done.txt
# /root/rhcsa_journal/lab-02c/task1/done.txt
# /root/rhcsa_journal/lab-02c/task2/done.txt
```

> **6 paths = Lab 02 trilogy complete.**

---

## Lab 02b Checklist (2 tasks)

- [ ] Lab-Wide Setup — `/tmp/lab02b` and `/root/rhcsa_journal/lab-02b/playbooks/` created
- [ ] Task 1 — Playbook written; `find` run; `stdout_lines` count and `stderr_lines` count shown in debug; `log-files.txt` has no `Permission denied` lines
- [ ] Task 2 — `failed_when:` passed for expected stderr; `ignore_errors:` demo showed `ignored=1` in PLAY RECAP; T02-D contrast explained

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 02a** — Stderr Redirection RHCSA | The shell-side task this mirrors in Ansible |
| **Lab 02c** — Stderr Verify | Audits 02a + 02b evidence; runs the destroy-restore drill |
| **Lab 01b** — Stdout Redirection Ansible | Previous b-lab — `ansible.builtin.copy: content:` vs `register:` |
| **Lab 03b** — Pipe Text Streams Ansible | Next b-lab — `set -o pipefail` and `stdout_lines` in pipelines |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
