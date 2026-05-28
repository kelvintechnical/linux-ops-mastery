# Lab 04b: Capture Both Output and Error — Ansible (`ansible.builtin.shell` with `register:` and merged streams)

- **Series:** linux-ops-mastery — Shells, Terminals & Redirection
- **Trilogy:** [`04a`](../lab-04a-capture-both-output-error-rhcsa/) (RHCSA hand-typed) → **`04b`** (Ansible — you are here) → [`04c`](../lab-04c-capture-both-output-error-verify/) (Verify)
- **Career arcs covered:** RHCSA EX200 (understand that Ansible exposes stdout and stderr separately via `register:`), DevOps (merge streams in playbooks for complete audit logs), SRE (tolerate expected stderr while failing on unexpected patterns)
- **Prerequisite:** [`Lab 04a`](../lab-04a-capture-both-output-error-rhcsa/) completed; `/root/rhcsa_journal/lab-04a/task1/` and `task2/` populated
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = capture `stdout_lines` + `stderr_lines` and merge with `copy: content:`; Task 2 = shell `&>` equivalent vs `failed_when:` for expected stderr)
- **Practice Directory (rotation #10):** `/tmp/lab04b` (reads against `/var/log`)
- **Playbooks:** `/root/rhcsa_journal/lab-04b/playbooks/`
- **Traps rehearsed this lab:** **T04-C** (only checking `result.stdout` — missing stderr half of combined capture) · **T04-D** (`ignore_errors: yes` swallows real failures; `failed_when:` is surgical) · **T41** (skipping the merged-stream re-run — the whole point of Task 2)

> **This lab's practice directory is: `/tmp/lab04b`** — reads against `/var/log` (same as 04a). Section 18 lists `&>`/`2>&1` as boundary topics, but the b-lab is kept as a trap-rehearsal artifact: `ansible.builtin.shell` with `register:` is the honest Ansible expression of combined-stream capture.

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
echo "--- /var/log combined-stream source ---"
ls -ld /var/log
ls /var/log | wc -l
echo ""
echo "--- 04a prereq check ---"
ls /root/rhcsa_journal/lab-04a/task1/done.txt \
   /root/rhcsa_journal/lab-04a/task2/done.txt 2>/dev/null \
    && echo "✅ 04a journal present" \
    || echo "❌ 04a journal missing — complete Lab 04a first"
echo "exit was: $?"
```

> **STOP — paste the output before setup.**

---

## Objective

04a built the `&>` / `2>&1` muscle in the shell. 04b exposes the same concept in Ansible:

1. **Capture both streams** from `ansible.builtin.shell` — `result.stdout_lines` and `result.stderr_lines` are the Ansible equivalents of the combined file from `&>`.
2. **Merge into one artifact** with `ansible.builtin.copy: content:` — concatenate stdout and stderr the way `&>` would on the CLI.
3. **Understand `failed_when:`** — tolerate known stderr (e.g., `Permission denied`) while still failing on unexpected errors. More precise than `ignore_errors: yes`.
4. **Prove idempotence** — re-run the merge playbook; second run shows `changed=0` when the on-disk bytes already match.

---

## Concept: `register:` Is Ansible's Stream Splitter — Merge Is Your Job

```
SHELL (04a)                              ANSIBLE (04b)
──────────────────────────────────       ──────────────────────────────────────────
find /var/log ... &> combined.txt        ansible.builtin.shell:
                                           cmd: "find /var/log -maxdepth 2 -type f"
                                         register: result

(both streams in one file)               result.stdout_lines  ← FD 1
                                         result.stderr_lines  ← FD 2

                                         ansible.builtin.copy:
                                           content: |
                                             {{ result.stdout }}
                                             {{ result.stderr }}
                                           dest: /tmp/lab04b/combined-ansible.txt
```

**T04-C:** Checking only `result.stdout` when the task generates stderr is the Ansible version of using `>` instead of `&>`. Always inspect both lists.

**T04-D:** `ignore_errors: yes` hides ALL failures. `failed_when: result.stderr_lines | length > N` fails only when stderr exceeds your tolerance threshold.

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

> **STOP — paste the `ls -ld` output before Task 1.**

---

## Task 1 — Capture both streams and merge with `copy: content:`

**Practice directory this task:** `/tmp/lab04b` (reads against `/var/log`)

### 🔁 Warm-Up

```bash
find /var/log -maxdepth 2 -type f 2>&1 | head -n 5
find /var/log -maxdepth 2 -type f 2>&1 | grep -c 'Permission denied' || echo 0
find /var/log -maxdepth 2 -type f &> /tmp/lab04b/warmup-combined.txt
wc -l /tmp/lab04b/warmup-combined.txt
grep -c 'Permission denied' /tmp/lab04b/warmup-combined.txt || echo 0
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Run `find /var/log` via `ansible.builtin.shell`, register both stream lists, merge them into `/tmp/lab04b/combined-ansible.txt` with `ansible.builtin.copy: content:`, and verify the file contains paths AND permission errors.

### 🧵 WEAVE TRACE

| Warm-up / setup command | Role inside Task 1 |
|---|---|
| `find ... 2>&1 \| head` | Preview of both streams before Ansible runs |
| `grep -c 'Permission denied'` | Baseline error count to compare against merged file |
| `find ... &> warmup-combined.txt` | Shell reference artifact — Ansible merge must match shape |
| `ansible localhost -m ping` | Connectivity gate |

### Main command block

```bash
TASKLOG=/tmp/lab04b/task1.txt
PB=/root/rhcsa_journal/lab-04b/playbooks/task1.yml

cat > "${PB}" << 'PLAYBOOK'
---
- name: "Lab 04b Task 1 — merge stdout + stderr via copy content"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    combined_path: /tmp/lab04b/combined-ansible.txt

  tasks:
    - name: "Ensure practice directory exists"
      ansible.builtin.file:
        path: /tmp/lab04b
        state: directory
        mode: '0755'

    - name: "Run find against /var/log (generates both streams)"
      ansible.builtin.shell: "find /var/log -maxdepth 2 -type f"
      register: find_result
      changed_when: false

    - name: "Show stream split"
      ansible.builtin.debug:
        msg:
          - "stdout lines: {{ find_result.stdout_lines | length }}"
          - "stderr lines: {{ find_result.stderr_lines | length }}"
          - "rc: {{ find_result.rc }}"

    - name: "Merge both streams into one file (Ansible &> equivalent)"
      ansible.builtin.copy:
        dest: "{{ combined_path }}"
        mode: '0644'
        content: |
          === STDOUT ===
          {{ find_result.stdout }}
          === STDERR ===
          {{ find_result.stderr }}
      register: merge_result

    - name: "Show merge result"
      ansible.builtin.debug:
        var: merge_result.changed
PLAYBOOK

echo "═══ Task 1: check mode ═══"                           2>&1 | tee $TASKLOG
ansible-playbook --check --diff "${PB}"                    2>&1 | tee -a $TASKLOG

echo "═══ Task 1: apply ═══"                                | tee -a $TASKLOG
ansible-playbook "${PB}"                                   2>&1 | tee -a $TASKLOG

echo "═══ Task 1: verify merged file ═══"                   | tee -a $TASKLOG
wc -l /tmp/lab04b/combined-ansible.txt                     | tee -a $TASKLOG
grep -c '=== STDOUT ===' /tmp/lab04b/combined-ansible.txt  | tee -a $TASKLOG
grep -c '=== STDERR ===' /tmp/lab04b/combined-ansible.txt  | tee -a $TASKLOG
grep -c 'Permission denied' /tmp/lab04b/combined-ansible.txt | tee -a $TASKLOG
head -n 8 /tmp/lab04b/combined-ansible.txt                 | tee -a $TASKLOG

echo "═══ Task 1: idempotence re-run ═══"                   | tee -a $TASKLOG
ansible-playbook "${PB}"                                   2>&1 | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. **`ansible.builtin.shell`** runs `find` — stdout and stderr are captured separately in `find_result`.
2. **`ansible.builtin.debug`** prints line counts for each stream — if stderr is 0 when run as root, note it; run as a limited user in production.
3. **`ansible.builtin.copy: content:`** merges both streams with section headers — the Ansible equivalent of `&>`.
4. **Idempotence re-run** — second apply should show `changed=0` on the copy task if content is unchanged.

### Expected output

```text
PLAY [Lab 04b Task 1 — merge stdout + stderr via copy content]
...
TASK [Merge both streams into one file (Ansible &> equivalent)] ***
changed: [localhost]
...
PLAY RECAP ***
localhost  ok=5  changed=1
...
42 /tmp/lab04b/combined-ansible.txt
1
1
3
=== STDOUT ===
/var/log/audit/audit.log
...
=== STDERR ===
find: ‘/var/log/private’: Permission denied
...
PLAY RECAP (idempotence)
localhost  ok=5  changed=0
```

### Switches

| Token | Meaning |
|---|---|
| `register: find_result` | Capture stdout, stderr, rc into a dict |
| `find_result.stdout_lines` | List of stdout lines (FD 1) |
| `find_result.stderr_lines` | List of stderr lines (FD 2) |
| `ansible.builtin.copy: content:` | Write inline content — no controller-side file needed |
| `--check --diff` | Preview changes before applying |

### 🧠 Concept Card

| Concept | What it does |
|---|---|
| Stream split in Ansible | `shell` module always separates stdout and stderr in `register:` |
| Merge pattern | `content: \| {{ stdout }}\n{{ stderr }}` emulates `&>` |
| Idempotence | Second `copy` with same content → `changed=false` |
| **🪤 Trap Risk T04-C** | Only reading `result.stdout` — stderr evidence lost. **Fix:** always inspect `stderr_lines`. |
| **🪤 Trap Risk** | Using `command:` for redirects — `command` rejects `\|`, `>`, `&>`. **Fix:** `ansible.builtin.shell`. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Merged file exists | `test -s /tmp/lab04b/combined-ansible.txt` | copy task wrote file |
| Both sections present | `grep -c '=== STDOUT ==='` and `grep -c '=== STDERR ==='` both = 1 | Merge included both streams |
| Idempotence | Second playbook run shows `changed=0` on copy task | Declarative merge is stable |

### Journal write

```bash
LAB=lab-04b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab04b/task1.txt              "$JDIR/evidence.txt"
cp /tmp/lab04b/combined-ansible.txt   "$JDIR/combined-ansible.txt"
cp "${PB}"                            "$JDIR/task1.yml"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    register stdout_lines + stderr_lines; merge via copy content; idempotence
COMMANDS: ansible-playbook --check --diff, ansible.builtin.shell, ansible.builtin.copy
TRAPS:    T04-C preview (stdout-only inspection)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — failed_when vs ignore_errors for expected stderr (T04-D)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /tmp/lab04b/warmup-combined.txt /tmp/lab04b/task1.txt
# Keep combined-ansible.txt for Task 2 comparison
ls /tmp/lab04b
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `stderr lines: 0` when run as root | Expected as root — the lesson still holds; compare with 04a's sudo -u capture |
| `changed=1` on idempotence re-run | Content drifted (find output changed) — normal for live logs; focus on copy task specifically |
| `command module does not support shell redirects` | You used `command:` — switch to `shell:` |

> **STOP — paste the stream line counts from debug and the idempotence `changed=0` line before Task 2.**

---

## Task 2 — `failed_when:` vs `ignore_errors:` for expected stderr (T04-D)

**Practice directory this task:** `/tmp/lab04b`

### 🔁 Warm-Up

```bash
ls /var/log /nope 2>&1 | tee /tmp/lab04b/warmup2.txt | wc -l
grep -c 'Permission denied' /tmp/lab04b/warmup2.txt || echo 0
ansible-playbook --syntax-check /root/rhcsa_journal/lab-04b/playbooks/task1.yml
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

1. Run a command that **always** produces stderr (`ls /var/log /nope`) with `ignore_errors: yes` — playbook succeeds even though stderr is non-empty.
2. Re-run with `failed_when:` that tolerates exactly one "No such file" error but fails on anything else.
3. Prove T04-D: `ignore_errors` is a blunt instrument; `failed_when` is surgical.

### 🧵 WEAVE TRACE

| Warm-up / setup command | Role inside Task 2 |
|---|---|
| `ls /var/log /nope 2>&1 \| tee` | Same dual-stream command the playbook will run |
| `grep -c 'Permission denied'` | Baseline for stderr content |
| `ansible-playbook --syntax-check` | Catches YAML errors before apply |

### Main command block

```bash
TASKLOG=/tmp/lab04b/task2.txt
PB=/root/rhcsa_journal/lab-04b/playbooks/task2.yml

cat > "${PB}" << 'PLAYBOOK'
---
- name: "Lab 04b Task 2 — failed_when vs ignore_errors"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Blunt — ignore_errors swallows everything"
      ansible.builtin.shell: "ls /var/log /nope 2>&1"
      register: blunt_result
      ignore_errors: true
      changed_when: false

    - name: "Show blunt result"
      ansible.builtin.debug:
        msg:
          - "rc: {{ blunt_result.rc }}"
          - "stderr lines: {{ blunt_result.stderr_lines | default([]) | length }}"
          - "failed: {{ blunt_result.failed | default(false) }}"

    - name: "Surgical — failed_when tolerates rc=2 only"
      ansible.builtin.shell: "ls /var/log /nope 2>&1"
      register: surgical_result
      failed_when: surgical_result.rc > 2
      changed_when: false

    - name: "Show surgical result"
      ansible.builtin.debug:
        msg:
          - "rc: {{ surgical_result.rc }}"
          - "failed: {{ surgical_result.failed | default(false) }}"

    - name: "Write combined evidence from surgical run"
      ansible.builtin.copy:
        dest: /tmp/lab04b/surgical-combined.txt
        mode: '0644'
        content: |
          rc={{ surgical_result.rc }}
          === STDOUT ===
          {{ surgical_result.stdout }}
          === STDERR ===
          {{ surgical_result.stderr }}
      when: surgical_result is defined
PLAYBOOK

echo "═══ Task 2: apply ═══"                                2>&1 | tee $TASKLOG
ansible-playbook "${PB}"                                   2>&1 | tee -a $TASKLOG

echo "═══ Task 2: verify surgical combined file ═══"        | tee -a $TASKLOG
test -s /tmp/lab04b/surgical-combined.txt \
    && wc -l /tmp/lab04b/surgical-combined.txt \
    || echo "surgical-combined.txt missing"                | tee -a $TASKLOG
grep '^rc=' /tmp/lab04b/surgical-combined.txt              | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. **Blunt task** — `ignore_errors: true` means the playbook continues even when `ls` exits 2. `failed` shows false even though rc=2.
2. **Surgical task** — `failed_when: rc > 2` allows rc=0, 1, 2 (ls missing path = 2) but would fail on rc=3+.
3. **Combined evidence** — surgical run's stdout+stderr written to disk — same merge pattern as Task 1.

### Expected output

```text
TASK [Blunt — ignore_errors swallows everything]
ok: [localhost]
TASK [Show blunt result]
ok: [localhost] => {
    "msg": ["rc: 2", "stderr lines: 0", "failed: false"]
}
TASK [Surgical — failed_when tolerates rc=2 only]
ok: [localhost]
...
rc=2
=== STDOUT ===
/var/log:
audit
...
=== STDERR ===
ls: cannot access '/nope': No such file or directory
```

### 🧠 Concept Card

| Concept | What it does |
|---|---|
| `ignore_errors: true` | Playbook continues; task marked ok even on failure |
| `failed_when: expr` | Fail only when expression is true — surgical control |
| rc=2 from ls | One missing operand — often tolerable in automation |
| **🪤 Trap Risk T04-D** | `ignore_errors` hides real failures too. **Fix:** `failed_when` with a precise condition. |

### Journal write

```bash
LAB=lab-04b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab04b/task2.txt              "$JDIR/evidence.txt"
cp /tmp/lab04b/surgical-combined.txt  "$JDIR/surgical-combined.txt"
cp "${PB}"                            "$JDIR/task2.yml"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    ignore_errors vs failed_when; surgical stderr tolerance; merge pattern reused
COMMANDS: ansible.builtin.shell, failed_when, ignore_errors, ansible.builtin.copy
TRAPS:    T04-D rehearsed (blunt vs surgical)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-04c — verify capstone: audit merged files + destroy-restore (T41)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /tmp/lab04b/warmup2.txt /tmp/lab04b/task2.txt
rm -f /tmp/lab04b/combined-ansible.txt /tmp/lab04b/surgical-combined.txt
ls /tmp/lab04b
echo "exit was: $?"
```

> **STOP — paste the blunt vs surgical debug output before moving to Lab 04c.**

---

## Lab 04b Checklist (2 tasks)

- [ ] Task 1 — both stream counts in debug; merged file has STDOUT + STDERR sections; idempotence `changed=0`
- [ ] Task 2 — blunt task shows `failed: false` with rc=2; surgical task passes with `failed_when`; combined evidence written

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 04a** — Combined Streams RHCSA | Shell `&>` / `2>&1` that this lab emulates in Ansible |
| **Lab 04c** — Combined Streams Verify | Audit the merged artifacts |
| Lab 02b — Stderr Ansible | Introduced `stderr_lines` and `failed_when:` |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
