# Lab 04b: Capture Both Output and Error — Ansible (`ansible.builtin.shell` with `2>&1` in `cmd`)

- **Series:** linux-ops-mastery — Shells, Terminals & Redirection
- **Trilogy:** [`04a`](../lab-04a-capture-both-output-error-rhcsa/) (RHCSA hand-typed) → **`04b`** (Ansible — you are here) → [`04c`](../lab-04c-capture-both-output-error-verify/) (Verify)
- **Career arcs covered:** RHCSA EX200 (redirection-order precision), DevOps (complete command logging in automation), SRE (retaining stderr context for incident triage)
- **Prerequisite:** [`Lab 04a`](../lab-04a-capture-both-output-error-rhcsa/) completed; `/root/rhcsa_journal/lab-04a/task1/` and `task2/` populated
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = required exact command capture + register/debug + file verification; Task 2 = wrong-vs-correct order trap demo + `ignore_errors` vs `failed_when`)
- **Practice Directory (rotation #04):** `/tmp/lab04b` (reads against `/lib64`)
- **Playbooks:** `/root/rhcsa_journal/lab-04b/playbooks/`
- **Traps rehearsed this lab:** **T04-A** (expected stderr is signal, not auto-failure) · **T04-C** (order trap: `2>&1 > file` is wrong for merge intent) · **T04-D** (`ignore_errors: true` is blunt; `failed_when:` is surgical)

> **This lab's practice directory is: `/tmp/lab04b`** — reads against `/lib64` with intentional missing target `/nonexistent` to generate mixed output.
>
> **Section 18 boundary note:** kept as trap-rehearsal artifact. For `2>&1` ordering drills, `ansible.builtin.shell` is the honest path because shell redirection semantics are the lesson.

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
echo "--- /lib64 baseline ---"
ls -ld /lib64
ls /lib64 | wc -l
echo ""
echo "--- 04a prereq check ---"
ls /root/rhcsa_journal/lab-04a/task1/done.txt \
   /root/rhcsa_journal/lab-04a/task2/done.txt 2>/dev/null \
    && echo "✅ 04a journal present" \
    || echo "❌ 04a journal missing — complete Lab 04a first"
echo "exit was: $?"
```

> **STOP — paste the output before setup.** If `/lib64` appears empty, pause and validate your environment.

---

## Objective

04a trained direct shell behavior for `> file 2>&1`, `2>&1 > file`, and `&> file`.  
04b keeps the same shell truth but executes it through Ansible.

1. **Capture both streams in one file** from the required command string:
   `ls /lib64 /nonexistent > /tmp/lab04b/combined.log 2>&1`
2. **Inspect `register` outputs** (`rc`, `stdout`, `stderr`) and understand why they can be sparse when redirection sends output to file.
3. **Rehearse T04-C** by contrasting wrong order (`2>&1 > file`) vs correct order (`> file 2>&1`) plus shorthand (`&> file`).
4. **Rehearse T04-A and T04-D** by treating expected stderr intentionally and preferring `failed_when:` over blanket `ignore_errors`.

---

## Concept Diagram — Shell vs Ansible

```text
SHELL (04a)                               ANSIBLE (04b)
────────────────────────────────────       ─────────────────────────────────────────
ls /lib64 /nonexistent \                  ansible.builtin.shell:
  > /tmp/lab04b/combined.log \              cmd: "ls /lib64 /nonexistent > /tmp/lab04b/combined.log 2>&1"
  2>&1                                    register: result

cat /tmp/lab04b/combined.log              result.rc
# contains stdout+stderr                  result.stdout / result.stderr
                                          # may be minimal: shell redirected both streams to file
```

**T04-C order trap recap**

- `2>&1 > file`: stderr points to original stdout (terminal), stdout goes to file
- `> file 2>&1`: stdout goes to file, then stderr follows to same file
- `&> file`: Bash shorthand for both streams to one file

---

## Reference Table — Keys and Tokens

| Key / token | Type | Meaning |
|---|---|---|
| `result.rc` | int | Exit status of the shell command |
| `result.stdout` | string | Captured stdout not redirected away |
| `result.stderr` | string | Captured stderr not redirected away |
| `result.changed` | bool | Shell task change flag |
| `> file 2>&1` | shell syntax | Correct merge order |
| `2>&1 > file` | shell syntax | Wrong merge order (trap) |
| `&> file` | shell syntax | Shorthand merge |
| `failed_when:` | Ansible control | Fail only on your rule |
| `ignore_errors: true` | Ansible control | Always continue even on failure |

---

## Lab-Wide Setup

```bash
sudo -i

mkdir -p /tmp/lab04b
mkdir -p /root/rhcsa_journal/lab-04b/playbooks
mkdir -p /root/rhcsa_journal/lab-04b/task1
mkdir -p /root/rhcsa_journal/lab-04b/task2

ls -ld /tmp/lab04b /root/rhcsa_journal/lab-04b/
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste `ls -ld` output before Task 1.**

---

## Task 1 — Required exact merge command in `ansible.builtin.shell`

**Practice directory this task:** `/tmp/lab04b` (reads against `/lib64`)

### Warm-Up

```bash
ls /lib64 /nonexistent > /tmp/lab04b/warmup-combined.log 2>&1
echo "warmup ec=$?"
wc -l /tmp/lab04b/warmup-combined.log
rg -n "^/lib64|/nonexistent|No such file" /tmp/lab04b/warmup-combined.log
ansible-doc ansible.builtin.shell 2>/dev/null | rg -n "check_mode|cmd|creates|removes"
echo "exit was: $?"
```

### Purpose

1. Use the exact required command under Ansible shell.
2. Register task output and debug `rc/stdout/stderr`.
3. Verify merged file exists and contains stdout-style plus stderr-style markers.
4. Run `--check --diff` first, then apply, then re-run for repeatability signal.

### WEAVE TRACE

| Warm-up command | Task 1 role |
|---|---|
| `ls /lib64 /nonexistent > ... 2>&1` | Baseline merged behavior |
| `wc -l warmup-combined.log` | Quick artifact existence sanity |
| `rg ... /nonexistent|No such file` | Expected stderr markers |
| `ansible-doc ...` | check-mode caveat awareness |

### Main command block

```bash
TASKLOG=/tmp/lab04b/task1.txt
PB=/root/rhcsa_journal/lab-04b/playbooks/task1.yml

# ── Step 1: Write playbook ────────────────────────────────────────────
cat > "${PB}" << 'PLAYBOOK'
---
- name: "Lab 04b Task 1 — exact cmd with > file 2>&1"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Ensure practice directory exists"
      ansible.builtin.file:
        path: /tmp/lab04b
        state: directory
        mode: '0755'

    - name: "Run exact required command"
      ansible.builtin.shell:
        cmd: "ls /lib64 /nonexistent > /tmp/lab04b/combined.log 2>&1"
      register: combined_result
      failed_when: false
      changed_when: false

    - name: "Debug registered rc/stdout/stderr"
      ansible.builtin.debug:
        msg:
          - "rc: {{ combined_result.rc }}"
          - "stdout: {{ combined_result.stdout | default('(empty)') }}"
          - "stderr: {{ combined_result.stderr | default('(empty)') }}"
          - "note: streams redirected to /tmp/lab04b/combined.log by shell"

    - name: "Verify merged file exists and has bytes"
      ansible.builtin.stat:
        path: /tmp/lab04b/combined.log
      register: combined_stat

    - name: "Count stdout/stderr markers from merged file"
      ansible.builtin.shell:
        cmd: |
          OUT_COUNT="$(rg -c '^/lib64' /tmp/lab04b/combined.log || true)"
          ERR_COUNT="$(rg -c '/nonexistent|No such file or directory' /tmp/lab04b/combined.log || true)"
          echo "OUT_COUNT=${OUT_COUNT}"
          echo "ERR_COUNT=${ERR_COUNT}"
      register: marker_result
      changed_when: false

    - name: "Show file and marker evidence"
      ansible.builtin.debug:
        msg:
          - "combined exists={{ combined_stat.stat.exists }} size={{ combined_stat.stat.size | default(0) }}"
          - "{{ marker_result.stdout_lines }}"

    - name: "Trap marker T04-C"
      ansible.builtin.debug:
        msg: "T04-C: wrong order '2>&1 > file' is not equivalent to '> file 2>&1'."
PLAYBOOK

echo "Playbook written: $(wc -l < "${PB}") lines"                     2>&1 | tee "${TASKLOG}"

# ── Step 2: check+diff first (required) ───────────────────────────────
echo "═══ Task 1 check/diff ═══"                                      | tee -a "${TASKLOG}"
ansible-playbook "${PB}" --check --diff 2>&1                          | tee -a "${TASKLOG}"
echo "check exit was: $?"                                             | tee -a "${TASKLOG}"

# ── Step 3: apply ─────────────────────────────────────────────────────
echo "═══ Task 1 apply ═══"                                           | tee -a "${TASKLOG}"
ansible-playbook "${PB}" 2>&1                                         | tee -a "${TASKLOG}"
echo "apply exit was: $?"                                             | tee -a "${TASKLOG}"

# ── Step 4: re-run apply (repeatability signal) ───────────────────────
echo "═══ Task 1 re-run ═══"                                          | tee -a "${TASKLOG}"
ansible-playbook "${PB}" 2>&1                                         | tee -a "${TASKLOG}"
echo "rerun exit was: $?"                                             | tee -a "${TASKLOG}"

# ── Step 5: host-side evidence snapshot ───────────────────────────────
echo "═══ Task 1 verification ═══"                                    | tee -a "${TASKLOG}"
wc -l /tmp/lab04b/combined.log                                        | tee -a "${TASKLOG}"
rg -n "^/lib64|/nonexistent|No such file" /tmp/lab04b/combined.log \
  | head -10                                                          | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Human-readable breakdown

1. Exact command string is preserved in `cmd`.
2. `register` still captures control data (`rc`) even though output is redirected to file.
3. `stat` proves file existence/size; marker counts prove both stream-origin patterns exist.
4. `--check --diff` first is mandatory rehearsal; apply/re-run provides operational repeatability.

### Reading it left to right

```text
ls /lib64 /nonexistent > /tmp/lab04b/combined.log 2>&1
│                    │                           │
│                    │                           └─ redirect stderr to stdout target
│                    └─ redirect stdout to file
└─ command emits both normal entries and error text
```

### The story

Task 1 keeps shell semantics front-and-center inside Ansible. `ansible.builtin.shell` is used specifically because redirection order is the training objective. You validate both the shell artifact (`combined.log`) and Ansible signal (`rc`), so you do not lose observability.

### Expected output

```text
TASK [Debug registered rc/stdout/stderr] ********************************
ok: [localhost] => {
  "msg": [
    "rc: 2",
    "stdout: ",
    "stderr: ",
    "note: streams redirected to /tmp/lab04b/combined.log by shell"
  ]
}
TASK [Show file and marker evidence] *************************************
ok: [localhost] => {
  "msg": [
    "combined exists=True size=1234",
    "['OUT_COUNT=34', 'ERR_COUNT=1']"
  ]
}
PLAY RECAP ***** localhost : ok=7 changed=0 failed=0
```

### Switches

| Token | Meaning |
|---|---|
| `cmd: "ls /lib64 /nonexistent > /tmp/lab04b/combined.log 2>&1"` | Required command |
| `register: combined_result` | Capture task return object |
| `failed_when: false` | Keep flow running for inspection |
| `changed_when: false` | Honest no-change reporting |
| `ansible-playbook --check --diff` | Preview before apply |
| `ansible.builtin.stat` | File existence and size check |

### Concept Card

| Concept | What it does |
|---|---|
| `> file 2>&1` | Merges both streams into one file |
| `register.rc` | Maintains exit-code observability |
| T04-A | Expected stderr can be normal in mixed-path command |
| T04-C | Wrong order breaks merge intent |
| T04-D | `failed_when` preferred over blanket ignore |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Merged file created | `test -s /tmp/lab04b/combined.log` | Artifact exists with data |
| stdout marker present | `rg -n '^/lib64' /tmp/lab04b/combined.log` | Normal output captured |
| stderr marker present | `rg -n '/nonexistent|No such file' /tmp/lab04b/combined.log` | Error output captured |
| Playbook persisted | `test -s /root/rhcsa_journal/lab-04b/playbooks/task1.yml` | Re-runnable |

### Journal write

```bash
LAB=lab-04b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab04b/task1.txt "${JDIR}/evidence.txt"
cp /tmp/lab04b/combined.log "${JDIR}/combined.log"

cat > "${JDIR}/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "${JDIR}/notes.txt" <<EOF
TOPIC:    exact shell cmd in ansible.builtin.shell with > file 2>&1
COMMANDS: check/diff first, apply, rerun, marker verification
TRAPS:    T04-A reviewed, T04-C reminder captured
RESULT:   /tmp/lab04b/combined.log contains both /lib64 lines and /nonexistent error text
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — order trap proof + T04-D contrast
EOF

ls -la "${JDIR}"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab04b/warmup-combined.log /tmp/lab04b/task1.txt
ls /tmp/lab04b/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `combined.log` missing | Verify `cmd` path and write permissions under `/tmp/lab04b` |
| Debug `stdout/stderr` empty | Expected when shell already redirected output to file |
| `ERR_COUNT=0` | Confirm command includes `/nonexistent` exactly |
| check mode seems limited | Normal for shell tasks; apply run is the source of full data |

> **STOP — paste Task 1 `rc/stdout/stderr`, stat evidence, and marker counts before Task 2.**

---

## Task 2 — Order trap proof + `ignore_errors` vs `failed_when` (T04-D)

**Practice directory this task:** `/tmp/lab04b`

### Warm-Up

```bash
ls /lib64 /nonexistent 2>&1 > /tmp/lab04b/order-wrong-warmup.log
echo "wrong ec=$?"
ls /lib64 /nonexistent > /tmp/lab04b/order-right-warmup.log 2>&1
echo "right ec=$?"
ls /lib64 /nonexistent &> /tmp/lab04b/order-amp-warmup.log
echo "amp ec=$?"
wc -l /tmp/lab04b/order-*-warmup.log
echo "exit was: $?"
```

### Purpose

1. Show the wrong order trap with `2>&1 > file` (T04-C).
2. Show correct order with `> file 2>&1` and `&> file`.
3. Write an evidence file with EC and trap-order markers.
4. Rehearse T04-D by contrasting `ignore_errors` and selective `failed_when`.

### WEAVE TRACE

| Warm-up command | Task 2 role |
|---|---|
| `2>&1 > wrong.log` | Trap behavior baseline |
| `> right.log 2>&1` | Correct merged behavior baseline |
| `&> amp.log` | Correct shorthand baseline |
| `wc -l order-*` | Fast comparison baseline |

### Main command block

```bash
TASKLOG=/tmp/lab04b/task2.txt
PB2=/root/rhcsa_journal/lab-04b/playbooks/task2.yml

# ── Step 1: Write playbook ────────────────────────────────────────────
cat > "${PB2}" << 'PLAYBOOK'
---
- name: "Lab 04b Task 2 — order trap and failure control"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Wrong order trap demo"
      ansible.builtin.shell:
        cmd: "ls /lib64 /nonexistent 2>&1 > /tmp/lab04b/order-wrong.log"
      register: wrong_order
      failed_when: false
      changed_when: false

    - name: "Correct order demo"
      ansible.builtin.shell:
        cmd: "ls /lib64 /nonexistent > /tmp/lab04b/order-right.log 2>&1"
      register: right_order
      failed_when: false
      changed_when: false

    - name: "Correct shorthand demo"
      ansible.builtin.shell:
        cmd: "ls /lib64 /nonexistent &> /tmp/lab04b/order-amp.log"
      register: amp_order
      failed_when: false
      changed_when: false

    - name: "T04-D blunt control demo"
      ansible.builtin.shell:
        cmd: "ls /THIS_PATH_SHOULD_NOT_EXIST_04B"
      register: ignored_fail
      ignore_errors: true
      changed_when: false

    - name: "T04-D selective control demo"
      ansible.builtin.shell:
        cmd: "ls /lib64 /nonexistent"
      register: selective_result
      changed_when: false
      failed_when: >
        selective_result.rc != 0 and
        (selective_result.stderr_lines
         | reject('search', '/nonexistent')
         | reject('search', 'No such file or directory')
         | list | length) > 0

    - name: "Gather line counts"
      ansible.builtin.shell:
        cmd: |
          echo "WRONG_LINES=$(wc -l < /tmp/lab04b/order-wrong.log)"
          echo "RIGHT_LINES=$(wc -l < /tmp/lab04b/order-right.log)"
          echo "AMP_LINES=$(wc -l < /tmp/lab04b/order-amp.log)"
      register: line_counts
      changed_when: false

    - name: "Write order/evidence markers"
      ansible.builtin.copy:
        dest: /tmp/lab04b/order-evidence.txt
        mode: '0644'
        content: |
          LAB=04b TASK=2
          WRONG_EC={{ wrong_order.rc }}
          RIGHT_EC={{ right_order.rc }}
          AMP_EC={{ amp_order.rc }}
          {{ line_counts.stdout }}
          IGNORE_ERRORS_EC={{ ignored_fail.rc }}
          IGNORE_ERRORS_FAILED={{ ignored_fail.failed | default(false) }}
          SELECTIVE_EC={{ selective_result.rc }}
          SELECTIVE_UNEXPECTED_ERR={{ selective_result.stderr_lines
            | reject('search', '/nonexistent')
            | reject('search', 'No such file or directory')
            | list | length }}
          TRAP_MARKER_T04-C=order_matters
          TRAP_MARKER_T04-A=expected_stderr_context
          TRAP_MARKER_T04-D=failed_when_over_ignore_errors

    - name: "Debug summary"
      ansible.builtin.debug:
        msg:
          - "wrong={{ wrong_order.rc }} right={{ right_order.rc }} amp={{ amp_order.rc }}"
          - "ignore_errors rc={{ ignored_fail.rc }} (continued by design)"
          - "selective unexpected stderr count={{ selective_result.stderr_lines | reject('search', '/nonexistent') | reject('search', 'No such file or directory') | list | length }}"
          - "evidence=/tmp/lab04b/order-evidence.txt"
PLAYBOOK

echo "Playbook written: $(wc -l < "${PB2}") lines"                    2>&1 | tee "${TASKLOG}"

# ── Step 2: apply ─────────────────────────────────────────────────────
echo "═══ Task 2 apply ═══"                                           | tee -a "${TASKLOG}"
ansible-playbook "${PB2}" 2>&1                                        | tee -a "${TASKLOG}"
echo "apply exit was: $?"                                             | tee -a "${TASKLOG}"

# ── Step 3: verify evidence ───────────────────────────────────────────
echo "═══ Task 2 verification ═══"                                    | tee -a "${TASKLOG}"
wc -l /tmp/lab04b/order-wrong.log /tmp/lab04b/order-right.log /tmp/lab04b/order-amp.log \
                                                                       | tee -a "${TASKLOG}"
rg -n "TRAP_MARKER|_EC=|_LINES=" /tmp/lab04b/order-evidence.txt       | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Human-readable breakdown

1. Wrong-order, right-order, and shorthand runs happen in one play for direct comparison.
2. Evidence file stores EC values and line-count markers for post-lab audit.
3. `ignore_errors` demo shows how a real failure can be hidden from fail/stop behavior.
4. `failed_when` demo tolerates expected `/nonexistent` stderr while still protecting against unexpected stderr.

### Reading it left to right

```text
2>&1 > file
│    │
│    └─ stdout moved later; stderr still points to old stdout destination
└─ stderr first follows current stdout
```

```text
> file 2>&1
│      │
│      └─ stderr now follows stdout to file
└─ stdout first redirected to file
```

### The story

This task makes the trap mechanical: same base command, three redirection forms, one evidence ledger. The operational takeaway is equally mechanical: `ignore_errors` is for exceptional temporary workflows; day-to-day automation should express intent with `failed_when`.

### Expected output

```text
TASK [Wrong order trap demo] ********************************************
ok: [localhost]
TASK [Correct order demo] ************************************************
ok: [localhost]
TASK [Correct shorthand demo] ********************************************
ok: [localhost]
TASK [T04-D blunt control demo] ******************************************
fatal: [localhost]: FAILED! => ...
...ignoring
TASK [Debug summary] ******************************************************
ok: [localhost] => {
  "msg": [
    "wrong=2 right=2 amp=2",
    "ignore_errors rc=2 (continued by design)",
    "selective unexpected stderr count=0",
    "evidence=/tmp/lab04b/order-evidence.txt"
  ]
}
PLAY RECAP ***** localhost : ok=8 changed=1 failed=0 ignored=1
```

### Switches

| Token | Meaning |
|---|---|
| `2>&1 > file` | Wrong merge order trap |
| `> file 2>&1` | Correct merge order |
| `&> file` | Correct shorthand |
| `failed_when: false` | Keep trap demos from aborting play |
| `ignore_errors: true` | Continue despite hard failure |
| `failed_when: ... reject('search', ...)` | Allow expected stderr only |

### Concept Card

| Concept | What it does |
|---|---|
| T04-C | Confirms order changes destination behavior |
| T04-A | Expected stderr requires contextual interpretation |
| T04-D | `failed_when` preserves signal; `ignore_errors` suppresses it |
| `order-evidence.txt` | Consolidated proof artifact |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Wrong-order file exists | `test -s /tmp/lab04b/order-wrong.log` | Trap artifact captured |
| Correct files exist | `test -s /tmp/lab04b/order-right.log && test -s /tmp/lab04b/order-amp.log` | Correct variants captured |
| Evidence file exists | `test -s /tmp/lab04b/order-evidence.txt` | Audit markers persisted |
| Trap markers present | `rg -n 'TRAP_MARKER' /tmp/lab04b/order-evidence.txt` | Explicit trap proof retained |

### Journal write

```bash
LAB=lab-04b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab04b/task2.txt "${JDIR}/evidence.txt"
cp /tmp/lab04b/order-evidence.txt "${JDIR}/order-evidence.txt"
cp /tmp/lab04b/order-wrong.log "${JDIR}/order-wrong.log"
cp /tmp/lab04b/order-right.log "${JDIR}/order-right.log"
cp /tmp/lab04b/order-amp.log "${JDIR}/order-amp.log"

cat > "${JDIR}/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "${JDIR}/notes.txt" <<EOF
TOPIC:    redirection order trap and Ansible failure controls
COMMANDS: wrong/right/&> shell forms, marker evidence write, recap checks
TRAPS:    T04-A/T04-C/T04-D rehearsed with explicit markers
RESULT:   order-evidence.txt contains EC and trap marker lines
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-04c — verify trilogy evidence
EOF

ls -la "${JDIR}"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab04b/task2.txt \
      /tmp/lab04b/order-wrong-warmup.log \
      /tmp/lab04b/order-right-warmup.log \
      /tmp/lab04b/order-amp-warmup.log
ls /tmp/lab04b/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Wrong/right artifacts seem similar | Re-check wrong command is exactly `2>&1 > /tmp/lab04b/order-wrong.log` |
| `ignored=0` in recap | Ensure bad-path demo task still has `ignore_errors: true` and impossible path |
| Selective task fails unexpectedly | Inspect `selective_result.stderr_lines`; adjust expected-pattern filter only if message format differs |
| Evidence file missing markers | Re-run and confirm copy task succeeded |

> **STOP — paste the `PLAY RECAP` line and `order-evidence.txt` marker block before Trilogy Completion Check.**

---

## Trilogy Completion Check

```bash
find /root/rhcsa_journal/lab-04{a,b,c} -name done.txt 2>/dev/null | sort
# Expect 6 paths:
# /root/rhcsa_journal/lab-04a/task1/done.txt
# /root/rhcsa_journal/lab-04a/task2/done.txt
# /root/rhcsa_journal/lab-04b/task1/done.txt
# /root/rhcsa_journal/lab-04b/task2/done.txt
# /root/rhcsa_journal/lab-04c/task1/done.txt
# /root/rhcsa_journal/lab-04c/task2/done.txt
```

> **6 paths = Lab 04 trilogy complete.**

---

## Lab 04b Checklist (2 tasks)

- [ ] Lab-Wide Setup complete (`/tmp/lab04b` and `/root/rhcsa_journal/lab-04b/playbooks/` created)
- [ ] Task 1 complete (exact command used, `register` debug shown, file verified, `--check --diff` run first)
- [ ] Task 2 complete (wrong/right/`&>` comparison done, evidence file written with EC/trap markers, T04-D contrast proved)

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 04a** — Capture Both Output+Error RHCSA | Shell-first prerequisite this lab mirrors |
| **Lab 04c** — Capture Both Output+Error Verify | Validates 04a+04b evidence chain |
| **Lab 02b** — Stderr Redirection Ansible | Earlier stream-discipline pattern with `register` |
| **Lab 03b** — Pipe Text Streams Ansible | Pipeline handling and `pipefail` follow-on |

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
