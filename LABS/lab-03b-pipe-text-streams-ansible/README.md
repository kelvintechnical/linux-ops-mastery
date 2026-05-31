# Lab 03b: Pipe Text Streams — Ansible (`ansible.builtin.shell` with `set -o pipefail`)

- **Series:** linux-ops-mastery — Shells, Terminals & Redirection
- **Trilogy:** [`03a`](../lab-03a-pipe-text-streams-rhcsa/) (RHCSA hand-typed) → **`03b`** (Ansible — you are here) → [`03c`](../lab-03c-pipe-text-streams-verify/) (Verify)
- **Career arcs covered:** RHCSA EX200 (understand that Ansible pipelines require `ansible.builtin.shell`, not `command:`), DevOps (CI pipelines that must fail when an upstream stage fails), SRE (alerting on broken pipe chains in automation)
- **Prerequisite:** [`Lab 03a`](../lab-03a-pipe-text-streams-rhcsa/) completed; `/root/rhcsa_journal/lab-03a/task1/` and `task2/` populated
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = pipeline with `grep | wc -l` via `ansible.builtin.shell`; Task 2 = `set -o pipefail` trap with `false | true` — **T03-A** and **T03-B**)
- **Practice Directory (rotation #03):** `/tmp/lab03b` (reads against `/etc`)
- **Playbooks:** `/root/rhcsa_journal/lab-03b/playbooks/`
- **Traps rehearsed this lab:** **T03-A** (`false | true` returns 0 without `set -o pipefail` — upstream failures are silent) · **T03-B** (using `ansible.builtin.command:` for a pipeline — it rejects `|` and forces a broken workaround) · **T41** (skipping the pipefail re-run — the whole point of Task 2)

> **This lab's practice directory is: `/tmp/lab03b`** — reads against `/etc` (same as 03a). Section 18 lists `|`/`tee` as boundary topics, but the b-lab is kept here as a trap-rehearsal artifact: `ansible.builtin.shell` is the only honest way to express a pipeline in Ansible, and `set -o pipefail` must be embedded in the `cmd:` string.

---

## LAB HEADER BLOCK

```bash
echo "--- Ansible controller ---"
ansible --version
echo ""
echo "--- localhost connection test ---"
ansible localhost -m ping --connection=local 2>/dev/null \
    && echo "✅ localhost reachable" \
    || echo "❌ localhost ping failed"
echo ""
echo "--- /etc pipe source ---"
ls -ld /etc
grep -c 'nologin' /etc/passwd
echo ""
echo "--- 03a prereq check ---"
ls /root/rhcsa_journal/lab-03a/task1/done.txt \
   /root/rhcsa_journal/lab-03a/task2/done.txt 2>/dev/null \
    && echo "✅ 03a journal present" \
    || echo "❌ 03a journal missing — complete Lab 03a first"
echo "exit was: $?"
```

> **STOP — paste the output before setup. If `grep -c 'nologin' /etc/passwd` returns 0, check that `/etc/passwd` exists and is readable.**

---

## Objective

03a built the `|`, `grep`, `wc -l`, `tee`, and `set -o pipefail` muscle in the shell. 03b proves the same outcomes in Ansible — and rehearses the traps that break real playbooks.

1. **Run a pipeline** with `ansible.builtin.shell: cmd: "grep ... | wc -l"` — the only honest Ansible expression of a pipe chain.
2. **Capture the result** with `register:` — `result.stdout` holds the final pipeline output (the count), `result.rc` holds the exit code.
3. **Prove T03-B** — show that `ansible.builtin.command:` rejects `|` (no shell metacharacters allowed), forcing you to use `shell:` for pipelines.
4. **Prove T03-A with `set -o pipefail`** — run `false | true` twice: once without pipefail (rc=0, trap hit), once with `set -o pipefail` embedded in `cmd:` (rc=1, trap avoided).

---

## Concept: `ansible.builtin.shell` Is the Ansible Pipe

```
SHELL (03a)                              ANSIBLE (03b)
──────────────────────────────────       ──────────────────────────────────────────
grep -c 'nologin' /etc/passwd \          ansible.builtin.shell:
    | tee /tmp/nologin.txt \               cmd: "grep -c 'nologin' /etc/passwd | tee /tmp/lab03b/nologin.txt | wc -l"
    | wc -l                              register: result

$? = exit of last stage                  result.rc = exit of last stage (unless pipefail)
${PIPESTATUS[@]} = all stages           (not exposed — embed set -o pipefail in cmd:)
```

**T03-B: `command:` vs `shell:`**
`ansible.builtin.command:` runs the command directly — no shell, no `|`, no `>`, no `&&`. Pipelines require `ansible.builtin.shell:` which invokes `/bin/sh -c '...'`. Using `command:` for a pipeline is a compile-time error in Ansible 2.x+.

**T03-A: pipefail in Ansible**
Embed `set -o pipefail` at the start of every `cmd:` string that contains `|`. Without it, `false | true` returns rc=0 and your playbook reports success even though an upstream stage failed.

---

## Lab-Wide Setup

```bash
sudo -i

mkdir -p /tmp/lab03b
mkdir -p /root/rhcsa_journal/lab-03b/playbooks
mkdir -p /root/rhcsa_journal/lab-03b/task1
mkdir -p /root/rhcsa_journal/lab-03b/task2

ls -ld /tmp/lab03b /root/rhcsa_journal/lab-03b/
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the `ls -ld` output before Task 1.**

---

## Task 1 — Pipeline with `grep | wc -l` via `ansible.builtin.shell`

**Practice directory this task:** `/tmp/lab03b` (reads against `/etc/passwd`)

### Warm-Up

```bash
grep -c 'nologin' /etc/passwd
grep 'nologin' /etc/passwd | wc -l
grep 'nologin' /etc/passwd | tee /tmp/lab03b/warmup-nologin.txt | wc -l
cat /tmp/lab03b/warmup-nologin.txt | head -n 3
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Run the canonical 03a pipeline (`grep 'nologin' /etc/passwd | wc -l`) inside an Ansible playbook using `ansible.builtin.shell`. Capture the count with `register:` and write it to `/tmp/lab03b/nologin-count.txt` using `ansible.builtin.copy: content:`.

### WEAVE TRACE

| Warm-up / setup command | Role inside Task 1 |
|---|---|
| `grep -c 'nologin' /etc/passwd` | Baseline count — must match the pipeline result |
| `grep ... \| wc -l` | Same pipeline the playbook will run |
| `tee /tmp/lab03b/warmup-nologin.txt` | Proves tee works in the sandbox before Ansible runs |
| `ansible localhost -m ping` | Connectivity gate — if this fails, playbook will too |

### Main command block

```bash
TASKLOG=/tmp/lab03b/task1.txt
PB=/root/rhcsa_journal/lab-03b/playbooks/task1.yml

cat > "${PB}" << 'PLAYBOOK'
---
- name: "Lab 03b Task 1 — grep | wc -l pipeline via ansible.builtin.shell"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    count_path: /tmp/lab03b/nologin-count.txt

  tasks:
    - name: "Ensure practice directory exists"
      ansible.builtin.file:
        path: /tmp/lab03b
        state: directory
        mode: '0755'

    - name: "Count nologin users via pipeline"
      ansible.builtin.shell: "grep 'nologin' /etc/passwd | wc -l"
      register: pipe_result
      changed_when: false

    - name: "Show pipeline result"
      ansible.builtin.debug:
        msg:
          - "rc:      {{ pipe_result.rc }}"
          - "stdout:  {{ pipe_result.stdout | trim }}"
          - "stderr:  {{ pipe_result.stderr | trim }}"

    - name: "Write count to file (idempotent copy)"
      ansible.builtin.copy:
        dest: "{{ count_path }}"
        content: |
          nologin_count={{ pipe_result.stdout | trim }}
          captured_at={{ ansible_date_time.iso8601 | default('unknown') }}
        mode: '0644'
      register: copy_result
PLAYBOOK

echo "Playbook written: $(wc -l < ${PB}) lines"                    2>&1 | tee $TASKLOG

echo "═══ Step 1: --check --diff ═══"                               | tee -a $TASKLOG
ansible-playbook --check --diff "${PB}" 2>&1                        | tee -a $TASKLOG

echo "═══ Step 2: apply (first run) ═══"                            | tee -a $TASKLOG
ansible-playbook "${PB}" 2>&1                                        | tee -a $TASKLOG

echo "═══ Step 3: verify on disk ═══"                               | tee -a $TASKLOG
cat /tmp/lab03b/nologin-count.txt                                   | tee -a $TASKLOG
BASELINE=$(grep -c 'nologin' /etc/passwd)
PIPELINE=$(grep 'nologin' /etc/passwd | wc -l | tr -d ' ')
echo "baseline grep -c: ${BASELINE}  pipeline wc -l: ${PIPELINE}"   | tee -a $TASKLOG
test "${BASELINE}" = "${PIPELINE}" \
    && echo "✅ counts match" | tee -a $TASKLOG \
    || echo "❌ counts differ" | tee -a $TASKLOG

echo "═══ Step 4: re-apply (idempotence) ═══"                       | tee -a $TASKLOG
ansible-playbook "${PB}" 2>&1                                        | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. **`ansible.builtin.shell: cmd: "grep ... | wc -l"`** — invokes `/bin/sh -c '...'` so the pipe is interpreted by the shell. `changed_when: false` prevents the task from showing `changed=true` on every run (shell tasks always "change" by default).
2. **`register: pipe_result`** — captures `stdout` (the count as a string), `stderr`, and `rc`.
3. **`ansible.builtin.copy: content:`** — writes the count to a file idempotently, mirroring 03a's `tee` pattern but declaratively.
4. **Baseline comparison** — `grep -c` and `grep | wc -l` must return the same number. If they differ, the pipeline or the `-c` flag was misused.

### Expected output

```text
Playbook written: 28 lines
═══ Step 2: apply (first run) ═══
...
TASK [Count nologin users via pipeline] ***
ok: [localhost]
TASK [Show pipeline result] ***
ok: [localhost] => {
    "msg": ["rc: 0", "stdout: 24", "stderr: "]
}
PLAY RECAP ******* localhost : ok=4  changed=1  unreachable=0  failed=0
═══ Step 3: verify on disk ═══
nologin_count=24
captured_at=2026-05-28T19:45:00Z
baseline grep -c: 24  pipeline wc -l: 24
✅ counts match
═══ Step 4: re-apply (idempotence) ═══
PLAY RECAP ******* localhost : ok=4  changed=0  unreachable=0  failed=0
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| `ansible.builtin.shell: cmd:` | Run a shell command — required for `\|` pipelines |
| `changed_when: false` | Prevent shell tasks from always showing changed |
| `register: pipe_result` | Capture stdout, stderr, rc |
| `pipe_result.stdout \| trim` | Jinja2 filter — strip trailing newline from count |
| `ansible.builtin.copy: content:` | Write the count to disk idempotently |

### Concept Card

| Concept | What it does |
|---|---|
| `shell:` for pipelines | Only module that accepts `\|` — `command:` rejects shell metacharacters (**T03-B**) |
| `changed_when: false` | Shell tasks default to changed=true; override for read-only pipelines |
| `register:` + `debug:` | RHCE habit: always inspect what the module returned |
| `grep -c` vs `grep \| wc -l` | Both count lines; must agree — proves the pipeline is correct |
| **🪤 Trap Risk T03-B** | Using `ansible.builtin.command:` for a pipeline fails at parse time. Use `shell:` |
| **🪤 Trap Risk T01-D** | Omitting `mode:` on the copy task — always set `mode: '0644'` explicitly |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Count file created | `test -s /tmp/lab03b/nologin-count.txt` | Evidence file exists |
| Count matches baseline | `grep -c 'nologin' /etc/passwd` equals pipeline output | Pipeline is correct |
| Playbook persists | `test -s /root/rhcsa_journal/lab-03b/playbooks/task1.yml` | Reconstruction artifact |
| Idempotence | Second run shows `changed=0` in PLAY RECAP | Copy task is idempotent |

### Journal write

```bash
LAB=lab-03b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab03b/task1.txt              "$JDIR/evidence.txt"
cp /tmp/lab03b/nologin-count.txt      "$JDIR/nologin-count.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    ansible.builtin.shell pipeline — grep | wc -l with register: and copy: content:
COMMANDS: ansible-playbook --check --diff PB; ansible-playbook PB; grep -c; grep | wc -l
TRAPS:    T03-B rehearsed (shell: not command: for pipelines); T01-D rehearsed (mode: explicit)
IDEMPOTENCE: second run changed=0
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — set -o pipefail trap: false | true with and without pipefail
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab03b/task1.txt /tmp/lab03b/warmup-nologin.txt
ls /tmp/lab03b/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `stdout: 0` but you expect matches | Pattern wrong — try `grep -c nologin /etc/passwd` without quotes around nologin |
| `changed=1` on every re-run | Add `changed_when: false` to the shell task |
| `No inventory was parsed` | Add `-i 'localhost,'` to ansible-playbook |
| `command: ... \| ...` parse error | **T03-B** — switch to `ansible.builtin.shell:` |

> **STOP — paste the PLAY RECAP and `✅ counts match` line before Task 2.**

---

## Task 2 — `set -o pipefail` trap: `false | true` with and without pipefail

**Practice directory this task:** `/tmp/lab03b`

### Warm-Up

```bash
false | true ; echo "without pipefail: exit=$?"
set -o pipefail
false | true ; echo "with pipefail: exit=$?"
echo "PIPESTATUS=${PIPESTATUS[@]}"
set +o pipefail
echo "Warm-up done at $(date -Is)"
echo "exit was: $?"
```

### Purpose

1. Run `false | true` **without** `set -o pipefail` in an Ansible shell task — expect `rc=0` (**T03-A trap hit**).
2. Run the same pipeline **with** `set -o pipefail` embedded in `cmd:` — expect `rc=1` (trap avoided).
3. Write both results to `/tmp/lab03b/pipefail-evidence.txt` and prove the contrast with `grep -c`.

### WEAVE TRACE

| Warm-up / setup command | Role inside Task 2 |
|---|---|
| `false \| true ; echo exit=$?` (no pipefail) | Baseline: exit=0 even though `false` failed — T03-A |
| `set -o pipefail; false \| true` | Contrast: exit=1 — upstream failure surfaces |
| `${PIPESTATUS[@]}` | Shows both stage exit codes — 1 and 0 respectively |
| `grep -c 'nologin'` from Task 1 | Re-used to prove the sandbox and `/etc/passwd` are still accessible |

### Main command block

```bash
TASKLOG=/tmp/lab03b/task2.txt
PB=/root/rhcsa_journal/lab-03b/playbooks/task2.yml

cat > "${PB}" << 'PLAYBOOK'
---
- name: "Lab 03b Task 2 — pipefail trap: false | true"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "TRAP — false | true WITHOUT pipefail (expect rc=0)"
      ansible.builtin.shell: "false | true"
      register: no_pf
      changed_when: false
      failed_when: false

    - name: "CORRECT — false | true WITH pipefail (expect rc=1)"
      ansible.builtin.shell: "set -o pipefail; false | true"
      register: with_pf
      changed_when: false
      failed_when: false

    - name: "Write evidence file"
      ansible.builtin.copy:
        dest: /tmp/lab03b/pipefail-evidence.txt
        content: |
          EC_WITHOUT_PIPEFAIL={{ no_pf.rc }}
          EC_WITH_PIPEFAIL={{ with_pf.rc }}
          TRAP_T03A={{ 'HIT' if no_pf.rc == 0 else 'AVOIDED' }}
        mode: '0644'

    - name: "Show trap contrast"
      ansible.builtin.debug:
        msg:
          - "without pipefail: rc={{ no_pf.rc }} (expect 0 — T03-A trap)"
          - "with pipefail:    rc={{ with_pf.rc }} (expect 1 — trap avoided)"
PLAYBOOK

echo "Playbook written: $(wc -l < ${PB}) lines"                    2>&1 | tee $TASKLOG
ansible-playbook "${PB}" 2>&1                                        | tee -a $TASKLOG

echo "═══ Evidence on disk ═══"                                     | tee -a $TASKLOG
cat /tmp/lab03b/pipefail-evidence.txt                               | tee -a $TASKLOG

grep -c 'EC_WITHOUT_PIPEFAIL=0' /tmp/lab03b/pipefail-evidence.txt | tee -a $TASKLOG
grep -c 'EC_WITH_PIPEFAIL=1'    /tmp/lab03b/pipefail-evidence.txt | tee -a $TASKLOG
grep -c 'TRAP_T03A=HIT'         /tmp/lab03b/pipefail-evidence.txt | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. **`failed_when: false`** — both shell tasks are allowed to exit non-zero without failing the play. We want to *capture* the rc, not abort on it.
2. **`set -o pipefail` inside `cmd:`** — must be embedded in the same shell invocation as the pipeline. A separate task setting pipefail in the Ansible process does NOT affect the subshell that runs `cmd:`.
3. **`TRAP_T03A=HIT`** — Jinja2 conditional writes `HIT` when rc=0 on the no-pipefail run. This is the evidence 03c will audit.

### Expected output

```text
TASK [Show trap contrast] ***
ok: [localhost] => {
    "msg": [
        "without pipefail: rc=0 (expect 0 — T03-A trap)",
        "with pipefail:    rc=1 (expect 1 — trap avoided)"
    ]
}
PLAY RECAP ******* localhost : ok=4  changed=1  unreachable=0  failed=0
═══ Evidence on disk ═══
EC_WITHOUT_PIPEFAIL=0
EC_WITH_PIPEFAIL=1
TRAP_T03A=HIT
1
1
1
exit was: 0
```

### Concept Card

| Concept | What it does |
|---|---|
| `set -o pipefail` in `cmd:` | Must be in the same shell string as the pipeline — not a separate Ansible task |
| `failed_when: false` | Capture rc without aborting the play — essential for trap demos |
| T03-A | `false \| true` returns 0 without pipefail — upstream failure is invisible |
| T03-B | Pipelines require `shell:` — `command:` rejects `\|` |
| **🪤 Trap Risk T41** | Skipping the pipefail re-run means you never tested the `rc=1` path |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| T03-A trap hit | `grep TRAP_T03A=HIT pipefail-evidence.txt` | Proves the no-pipefail run returned rc=0 |
| Pipefail works | `grep EC_WITH_PIPEFAIL=1 pipefail-evidence.txt` | Proves embedded pipefail changed rc to 1 |
| Evidence file | `test -s /tmp/lab03b/pipefail-evidence.txt` | 03c audits this file |
| Playbook persists | `test -s /root/rhcsa_journal/lab-03b/playbooks/task2.yml` | Reconstruction artifact |

### Journal write

```bash
LAB=lab-03b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab03b/task2.txt                "$JDIR/evidence.txt"
cp /tmp/lab03b/pipefail-evidence.txt    "$JDIR/pipefail-evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    set -o pipefail in ansible.builtin.shell — T03-A trap rehearsal
COMMANDS: ansible-playbook PB; grep -c; false | true; set -o pipefail
TRAPS:    T03-A rehearsed (rc=0 without pipefail); T03-B rehearsed in Task 1 (shell: not command:)
EVIDENCE: EC_WITHOUT_PIPEFAIL=0 EC_WITH_PIPEFAIL=1 TRAP_T03A=HIT
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-03c — audit pipefail-evidence.txt and nologin-count.txt from journal
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab03b/task2.txt
ls /tmp/lab03b/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Both runs show rc=0 | Pipefail not embedded in `cmd:` — it must be `set -o pipefail; false \| true` in one string |
| Both runs show rc=1 | Pipefail leaked from a prior task — each `cmd:` gets a fresh subshell; check the playbook YAML |
| `TRAP_T03A=AVOIDED` when you expected HIT | The no-pipefail task accidentally included pipefail — remove it from that task's `cmd:` |

> **STOP — paste the evidence file contents and all three `grep -c` results returning `1` before the Trilogy Completion Check.**

---

## Trilogy Completion Check

```bash
find /root/rhcsa_journal/lab-03{a,b,c} -name done.txt 2>/dev/null | sort
# Expect 6 paths (task1 + task2 for each of a, b, c)
```

---

## Lab 03b Checklist (2 tasks)

- [ ] Lab-Wide Setup — `/tmp/lab03b` and playbooks directory created
- [ ] Task 1 — Pipeline via `ansible.builtin.shell`; count matches `grep -c` baseline; idempotence `changed=0`
- [ ] Task 2 — `false | true` without pipefail rc=0 (T03-A HIT); with pipefail rc=1; evidence file written

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 03a** — Pipe Text Streams RHCSA | The shell-side pipelines this mirrors |
| **Lab 03c** — Pipe Verify | Audits `pipefail-evidence.txt` and `nologin-count.txt` |
| **Lab 02b** — Stderr Ansible | Previous b-lab — `register:` and `stderr_lines` |
| **Lab 04b** — Combined Output Ansible | Next b-lab — `2>&1` inside `shell:` cmd strings |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
