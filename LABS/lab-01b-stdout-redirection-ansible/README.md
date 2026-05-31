# Lab 01b: Standard Output Redirection — Ansible (`ansible.builtin.copy` with `content:`)

- **Series:** linux-ops-mastery — Shells, Terminals & Redirection
- **Trilogy:** [`01a`](../lab-01a-stdout-redirection-rhcsa/) (RHCSA hand-typed) → **`01b`** (Ansible — you are here) → [`01c`](../lab-01c-stdout-redirection-verify/) (Verify)
- **Career arcs covered:** RHCSA EX200 (understand that `ansible.builtin.copy: content:` is the module-native `>`), DevOps (idempotent file delivery without shell scripts), SRE (config-file management that self-heals drift)
- **Prerequisite:** [`Lab 01a`](../lab-01a-stdout-redirection-rhcsa/) completed; `/root/rhcsa_journal/lab-01a/task1/` and `task2/` populated
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = write + apply with `--check --diff`; Task 2 = idempotence proof + drift correction)
- **Practice Directory (rotation #01):** `/tmp/lab01b`
- **Playbooks:** `/root/rhcsa_journal/lab-01b/playbooks/`
- **Traps rehearsed this lab:** **T01-C** (`src:` requires a file on the controller — `content:` embeds text inline; confusing them produces "file not found") · **T01-D** (omitting `mode:` → Ansible inherits umask, permissions become unpredictable; RHCSA grader checks `stat -c '%a'`) · **T41** (skipping the drift-correction re-run — the whole point of Task 2)

> **This lab's practice directory is: `/tmp/lab01b`** — same rotation as 01a. The point of 01b is to show that `ansible.builtin.copy: content:` does exactly what `>` does in 01a, but idempotently and with automatic drift detection and correction.

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
    || echo "❌ localhost ping failed — check /etc/ansible/hosts or add -i 'localhost,' flag"
echo ""
echo "--- 01a prereq check ---"
ls /root/rhcsa_journal/lab-01a/task1/done.txt \
   /root/rhcsa_journal/lab-01a/task2/done.txt 2>/dev/null \
    && echo "✅ 01a journal present" \
    || echo "❌ 01a journal missing — complete Lab 01a first"
echo "exit was: $?"
```

> **STOP — paste the `ansible --version` output and the `✅ 01a journal present` line before setup. If localhost ping failed, run `ansible localhost -m ping -i 'localhost,' --connection=local` (trailing comma makes a valid inventory string).**

---

## Objective

01a built the shell-redirect muscle. 01b proves the same outcome is achievable through Ansible — and that Ansible's version is idempotent where `>` is not.

1. **Write a multi-section system report** using `ansible.builtin.copy: content:` with embedded Ansible facts. The content is declared inside the playbook; no file on the controller is required.
2. **Understand `--check --diff`** — run the playbook in dry-run mode to preview the exact bytes that would be written before applying. This is your pre-apply `cat` equivalent.
3. **Prove idempotence** — re-run the playbook immediately after applying; `changed=false` because the on-disk bytes already match the declared `content:`. The shell `>` always writes; `content:` writes only when it has to.
4. **Prove drift correction** — manually corrupt the file; re-run the playbook; `changed=true` because Ansible detected the divergence and restored the declared state.

---

## Concept: `ansible.builtin.copy content:` Is the Idempotent `>`

```
SHELL (01a)                           ANSIBLE (01b)
──────────────────────────────────    ────────────────────────────────────────
echo "=== Report ===" >  /f.txt       ansible.builtin.copy:
echo "--- Host ---"   >> /f.txt         dest: /tmp/lab01b/report.txt
hostname               >> /f.txt        content: |
echo "=== End ==="    >> /f.txt           === Report ===
                                          --- Host ---
> truncates first, then writes            {{ ansible_hostname }}
>> appends to existing content            === End ===
Every run rewrites — no check           mode: '0644'
No change tracking                      owner: root
                                      register: copy_result

                                      First run:  copy_result.changed = true
                                      Second run: copy_result.changed = false
```

**T01-C: `src:` vs `content:`**
`src: /path/to/file` requires that file to exist on the Ansible controller at run time. For dynamic content that includes facts (hostname, OS version), `content:` with Jinja2 templates is always the right tool — the text lives IN the playbook, not in a separate file.

---

## Reference — `ansible.builtin.copy` Parameters Used This Lab

| Parameter   | Type   | Default | What it controls                                                      |
|-------------|--------|---------|-----------------------------------------------------------------------|
| `dest:`     | path   | —       | Target path on the managed node (required)                            |
| `content:`  | string | —       | Write this text verbatim to `dest:` (mutually exclusive with `src:`)  |
| `mode:`     | octal  | umask   | File permissions — always set explicitly (**T01-D**)                  |
| `owner:`    | string | —       | File owner                                                            |
| `group:`    | string | —       | File group                                                            |
| `register:` | string | —       | Variable name to capture the task result                              |
| `backup:`   | bool   | false   | Keep a timestamped backup on change                                   |

---

## Lab-Wide Setup

```bash
sudo -i

mkdir -p /tmp/lab01b
mkdir -p /root/rhcsa_journal/lab-01b/playbooks
mkdir -p /root/rhcsa_journal/lab-01b/task1
mkdir -p /root/rhcsa_journal/lab-01b/task2

ls -ld /tmp/lab01b /root/rhcsa_journal/lab-01b/
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the `ls -ld` output before Task 1.**

---

## Task 1 — Write a system report with `ansible.builtin.copy: content:`

**Practice directory this task:** `/tmp/lab01b`

### Warm-Up

```bash
# Confirm ansible.builtin.copy content: parameter signature
ansible-doc ansible.builtin.copy 2>/dev/null | grep -A 8 'content'
# See which facts will populate the Jinja2 templates
ansible localhost -m setup --connection=local 2>/dev/null \
    | grep -E '"ansible_(hostname|distribution|distribution_version|kernel|architecture)'
# Baseline — what's in /tmp/lab01b right now?
ls -la /tmp/lab01b/
echo "exit was: $?"
```

> `ansible-doc` is the module manual page. `ansible -m setup` is the fact oracle. Both are warm-up only — the WEAVE table below maps each to its role inside Task 1.

### Purpose

Write a multi-section system report to `/tmp/lab01b/report.txt` using `content:` with five Ansible facts embedded as Jinja2 templates. Then prove three properties of `content:`:

1. **Dry-run first** — `--check --diff` shows the planned diff without touching disk.
2. **Apply** — first run: `changed=true`; file is created with the declared content.
3. **Re-apply** — second run: `changed=false`; bytes match; no write happens.

### WEAVE TRACE

| Warm-up / setup command                    | Role inside Task 1                                                          |
|--------------------------------------------|-----------------------------------------------------------------------------|
| `ansible-doc copy \| grep -A8 content`     | Confirms `content:` parameter exists before embedding it in the playbook    |
| `ansible -m setup \| grep ansible_hostname`| Verifies the five Jinja2 facts will resolve at gather_facts time            |
| `ls -la /tmp/lab01b/`                      | Pre-flight: confirms practice directory is empty before the first run       |
| `mkdir -p .../playbooks`                   | Playbook landing zone — `ansible-playbook` needs the `.yml` path            |
| `ansible localhost -m ping`                | Connectivity test — if this fails, `ansible-playbook` will also fail        |

### Main command block

```bash
TASKLOG=/tmp/lab01b/task1.txt
PB=/root/rhcsa_journal/lab-01b/playbooks/task1.yml

# ── Step 1: Write the playbook ────────────────────────────────────────
cat > "${PB}" << 'PLAYBOOK'
---
- name: "Lab 01b Task 1 — write system report with ansible.builtin.copy content:"
  hosts: localhost
  connection: local
  gather_facts: true
  vars:
    report_path: /tmp/lab01b/report.txt

  tasks:
    - name: "Ensure practice directory exists"
      ansible.builtin.file:
        path: /tmp/lab01b
        state: directory
        mode: '0755'

    - name: "Write system report (idempotent stdout redirect)"
      ansible.builtin.copy:
        dest: "{{ report_path }}"
        content: |
          === System Report ===
          --- Hostname ---
          {{ ansible_hostname }}
          --- OS ---
          {{ ansible_distribution }} {{ ansible_distribution_version }}
          --- Kernel ---
          {{ ansible_kernel }}
          --- Architecture ---
          {{ ansible_architecture }}
          === End Report ===
        mode: '0644'
        owner: root
        group: root
      register: copy_result

    - name: "Show copy result"
      ansible.builtin.debug:
        msg:
          - "changed: {{ copy_result.changed }}"
          - "dest:    {{ copy_result.dest }}"
PLAYBOOK

echo "Playbook written: $(wc -l < ${PB}) lines"                    2>&1 | tee $TASKLOG

# ── Step 2: Dry-run — check + diff ────────────────────────────────────
echo "═══ Step 2: --check --diff (nothing written to disk) ═══"     | tee -a $TASKLOG
ansible-playbook --check --diff "${PB}" 2>&1                        | tee -a $TASKLOG
echo "dry-run exit was: $?"                                          | tee -a $TASKLOG

# ── Step 3: Apply (first run) ─────────────────────────────────────────
echo "═══ Step 3: apply (first run — expect changed=1) ═══"         | tee -a $TASKLOG
ansible-playbook "${PB}" 2>&1                                        | tee -a $TASKLOG
echo "apply exit was: $?"                                            | tee -a $TASKLOG

# ── Step 4: Verify file on disk ───────────────────────────────────────
echo "═══ Step 4: verify file on disk ═══"                          | tee -a $TASKLOG
cat /tmp/lab01b/report.txt                                          | tee -a $TASKLOG
stat -c '%U:%G %a %n' /tmp/lab01b/report.txt                       | tee -a $TASKLOG
wc -l /tmp/lab01b/report.txt                                        | tee -a $TASKLOG

# ── Step 5: Re-apply — prove idempotence ──────────────────────────────
echo "═══ Step 5: re-apply (second run — expect changed=0) ═══"     | tee -a $TASKLOG
ansible-playbook "${PB}" 2>&1                                        | tee -a $TASKLOG
echo "idempotence exit was: $?"

echo "exit was: $?"
```

### Human-readable breakdown

1. **Step 1 — write the playbook.** `cat > file << 'PLAYBOOK'` (single-quoted heredoc delimiter) prevents shell expansion inside the heredoc — `{{ ansible_hostname }}` stays as literal Jinja2 text in the `.yml` file; Ansible expands it at runtime.
2. **Step 2 — dry-run.** `--check --diff` is the Ansible equivalent of previewing without applying. The `diff` block shows the exact bytes that *would* be written. Always run this before applying to production files.
3. **Step 3 — apply.** The directory already exists; the file doesn't yet. `changed=true` for the `copy` task. The `PLAY RECAP` shows `changed=1`.
4. **Step 4 — verify.** `cat` the file; `stat -c '%U:%G %a %n'` confirms owner, group, and mode. The grader's first check is `stat -c '%a'` — mode must be `644`.
5. **Step 5 — re-apply.** Same playbook, same content. Ansible sha256-checks the on-disk file against the rendered `content:` string. They match → `changed=false`. The `PLAY RECAP` shows `changed=0`.

### Reading it left to right

```
ansible.builtin.copy:
  dest: "{{ report_path }}"    ← target path (from vars: block)
  content: |                   ← block scalar: write this text verbatim
    === System Report ===       ← literal text
    --- Hostname ---
    {{ ansible_hostname }}      ← Jinja2: expands from gathered facts
  mode: '0644'                 ← quoted octal string — T01-D: never omit this
register: copy_result          ← capture return value: .changed, .dest, .diff
```

The `|` (pipe / block scalar) in YAML preserves all newlines. A 9-line `content:` block becomes a 9-line file with a trailing newline. `>` (folding scalar) would collapse newlines to spaces — use `|` for file content.

### The story

`ansible.builtin.copy: content:` is idempotent because before writing it computes the sha256 of the existing on-disk file and compares it to the sha256 of the `content:` string after Jinja2 rendering. If they match, it skips the write (`changed=false`). If they differ, it writes and sets `changed=true`. The shell `>` has no such check — it truncates the file descriptor and writes unconditionally every time.

This is why Ansible is called "configuration management" rather than "scripting": the playbook declares desired state, and the module ensures that state is met, doing only the minimum work required. The shell equivalent would require a manual `diff` loop and a conditional write.

### Expected output

```text
Playbook written: 28 lines
═══ Step 2: --check --diff (nothing written to disk) ═══

PLAY [Lab 01b Task 1 ...] ******************************************************
...
--- before: /tmp/lab01b/report.txt
+++ after: /tmp/lab01b/report.txt
@@ -0,0 +1,9 @@
+=== System Report ===
+--- Hostname ---
+rhel9host
...
changed: [localhost]

PLAY RECAP ******* localhost : ok=3  changed=1  unreachable=0  failed=0
dry-run exit was: 0
═══ Step 3: apply (first run — expect changed=1) ═══
...
PLAY RECAP ******* localhost : ok=3  changed=1  unreachable=0  failed=0
apply exit was: 0
═══ Step 4: verify file on disk ═══
=== System Report ===
--- Hostname ---
rhel9host
--- OS ---
RedHat 9.4
--- Kernel ---
5.14.0-427.xx.el9.x86_64
--- Architecture ---
x86_64
=== End Report ===
root:root 644 /tmp/lab01b/report.txt
9 /tmp/lab01b/report.txt
═══ Step 5: re-apply (second run — expect changed=0) ═══
...
PLAY RECAP ******* localhost : ok=2  changed=0  unreachable=0  failed=0
idempotence exit was: 0
exit was: 0
```

### Switches

| Token                                 | Meaning                                                                 |
|---------------------------------------|-------------------------------------------------------------------------|
| `ansible-playbook PB`                 | Run a playbook against the inventory                                    |
| `--check`                             | Dry-run: simulate changes without applying                              |
| `--diff`                              | Show unified diff of file changes (pairs with `--check`)                |
| `content: \|`                         | Block scalar: write the indented text verbatim as file content          |
| `{{ ansible_hostname }}`              | Jinja2 template for the hostname fact                                   |
| `register: name`                      | Capture the module return value into `name`                             |
| `result.changed`                      | Boolean: did this task actually write anything?                         |
| `mode: '0644'`                        | Quoted octal string (unquoted `0644` parses as integer in YAML)         |

### Concept Card

| Concept | What it does |
|---|---|
| `content:` vs `src:` | `content:` embeds text inline; `src:` copies from the controller. Wrong one → "file not found" (**T01-C**) |
| Idempotence | `changed=false` on re-run — Ansible sha256-checks before writing |
| `--check --diff` | Dry-run + diff: see exactly what *would* change before touching disk |
| `mode:` always explicit | Without it, permissions are umask-dependent (**T01-D**) |
| Jinja2 facts in `content:` | `{{ ansible_hostname }}` etc. render from `gather_facts: true` at play time |
| `\|` block scalar | Preserves all newlines — correct for file content (`>` would collapse them) |
| **🪤 Trap Risk T01-C** | `src: /path` requires that file on the controller. For inline dynamic content, use `content:` |
| **🪤 Trap Risk T01-D** | Omitting `mode:` means the file gets the creating process's umask. Always declare it explicitly. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| `report.txt` created | `test -s /tmp/lab01b/report.txt` returns 0 | File exists and is non-empty |
| Owner/group/mode | `stat -c '%U:%G %a' /tmp/lab01b/report.txt` returns `root:root 644` | Grader checks mode first |
| Idempotence proven | Second `ansible-playbook` run shows `changed=0` in PLAY RECAP | Core property of `content:` |
| Playbook persists | `test -s /root/rhcsa_journal/lab-01b/playbooks/task1.yml` returns 0 | Playbook is the reconstruction point |

### Journal write

```bash
LAB=lab-01b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab01b/task1.txt          "$JDIR/evidence.txt"
cp /tmp/lab01b/report.txt         "$JDIR/report.txt"
# Playbook already lives at /root/rhcsa_journal/lab-01b/playbooks/task1.yml

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    ansible.builtin.copy with content: — idempotent stdout redirect via Ansible
COMMANDS: ansible-playbook --check --diff PB; ansible-playbook PB; stat -c '%U:%G %a %n'; wc -l
TRAPS:    T01-C rehearsed (content: not src:); T01-D rehearsed (mode: '0644' always explicit)
IDEMPOTENCE: second run showed changed=0 in PLAY RECAP
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — drift detection; sed -i to corrupt; re-run; confirm changed=1 and sha256 restored
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab01b/task1.txt
ls /tmp/lab01b/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `No inventory was parsed` warning | Add `-i 'localhost,'` (trailing comma) to the ansible-playbook command |
| `msg: 'file not found'` on copy task | **T01-C** — you used `src:` instead of `content:`. Check the playbook YAML |
| `mode: 0644` YAML parsing error | YAML treats bare `0644` as integer 420. Use `mode: '0644'` (quoted) |
| `changed=1` on every re-run | A Jinja2 fact changes between runs (e.g., `ansible_uptime_seconds` was used). Replace with a stable fact like `ansible_architecture` |
| `PLAY RECAP failed=1` | Module error; check the output above the RECAP for the actual message |
| `Permission denied` creating `/tmp/lab01b` | Run `sudo -i` first |

> **STOP — paste the PLAY RECAP lines from Step 3 (apply) and Step 5 (idempotence) before Task 2.**

---

## Task 2 — Drift detection: corrupt the file, re-run, prove `changed=true`

**Practice directory this task:** `/tmp/lab01b`

### Warm-Up

```bash
cat /tmp/lab01b/report.txt
wc -l /tmp/lab01b/report.txt
sha256sum /tmp/lab01b/report.txt
echo "Warm-up done at $(date -Is)"
echo "exit was: $?"
```

> `sha256sum` captures the "clean" fingerprint before the corruption step. The hash stored in this warm-up is the ground truth for the post-restore comparison.

### Purpose

1. **Snapshot** the clean file (sha256 + line count).
2. **Corrupt** using `sed -i` — simulate drift the way a manual edit or a failed `>` would cause.
3. **Re-run** the same playbook — `changed=true` because the bytes differ from the declared `content:`.
4. **Verify** the file is byte-for-byte identical to the pre-drift snapshot (sha256 match).

### WEAVE TRACE

| Warm-up / setup command     | Role inside Task 2                                                         |
|-----------------------------|----------------------------------------------------------------------------|
| `cat /tmp/.../report.txt`   | Pre-drift read — confirms the Task 1 file is still intact                  |
| `sha256sum report.txt`      | Pre-drift fingerprint — ground truth for the post-restore comparison       |
| `wc -l report.txt`          | Line count baseline — post-restore count must match                        |

### Main command block

```bash
TASKLOG=/tmp/lab01b/task2.txt
REPORT=/tmp/lab01b/report.txt
PB=/root/rhcsa_journal/lab-01b/playbooks/task1.yml

# ── Part A: snapshot (pre-drift) ──────────────────────────────────────
echo "═══ Part A: snapshot (pre-drift) ═══"              2>&1 | tee $TASKLOG
CLEAN_HASH=$(sha256sum "${REPORT}" | awk '{print $1}')
CLEAN_LINES=$(wc -l < "${REPORT}")
echo "pre-drift sha256: ${CLEAN_HASH}"                   | tee -a $TASKLOG
echo "pre-drift lines:  ${CLEAN_LINES}"                  | tee -a $TASKLOG

# ── Part B: corrupt (simulate drift) ──────────────────────────────────
echo "═══ Part B: corrupt (simulate drift) ═══"          | tee -a $TASKLOG
sed -i 's/=== System Report ===/=== DRIFTED REPORT ===/' "${REPORT}"
echo "post-drift head -3:"                               | tee -a $TASKLOG
head -3 "${REPORT}"                                      | tee -a $TASKLOG
DRIFT_HASH=$(sha256sum "${REPORT}" | awk '{print $1}')
echo "post-drift sha256: ${DRIFT_HASH}"                  | tee -a $TASKLOG
test "${CLEAN_HASH}" != "${DRIFT_HASH}" \
    && echo "✅ drift confirmed (hashes differ)"         | tee -a $TASKLOG \
    || echo "❌ drift not detected (sed -i may not have run)" | tee -a $TASKLOG

# ── Part C: re-run playbook — expect changed=true ─────────────────────
echo "═══ Part C: re-run playbook (expect changed=1) ═══" | tee -a $TASKLOG
ansible-playbook "${PB}" 2>&1                            | tee -a $TASKLOG
echo "correction exit was: $?"                           | tee -a $TASKLOG

# ── Part D: verify file restored ──────────────────────────────────────
echo "═══ Part D: verify restored ═══"                   | tee -a $TASKLOG
RESTORED_HASH=$(sha256sum "${REPORT}" | awk '{print $1}')
RESTORED_LINES=$(wc -l < "${REPORT}")
echo "restored sha256: ${RESTORED_HASH}"                 | tee -a $TASKLOG
echo "restored lines:  ${RESTORED_LINES}"                | tee -a $TASKLOG
test "${RESTORED_HASH}" = "${CLEAN_HASH}" \
    && echo "✅ restored file is byte-identical to pre-drift" | tee -a $TASKLOG \
    || echo "❌ restored file differs from pre-drift"         | tee -a $TASKLOG
test "${RESTORED_LINES}" -eq "${CLEAN_LINES}" \
    && echo "✅ line count matches"  | tee -a $TASKLOG \
    || echo "❌ line count differs"  | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. **Part A — snapshot.** `sha256sum | awk '{print $1}'` extracts the hash only (drops the filename). Stored in `CLEAN_HASH` before any destructive step.
2. **Part B — corrupt.** `sed -i` edits in-place — no backup unless you use `-i .bak`. The `s/.../.../` substitution is realistic drift: a mis-edit that changed the header text. Two different sha256 hashes prove the corruption actually happened.
3. **Part C — re-run.** Same playbook, same `content:`. Ansible sha256-checks on-disk vs declared → they differ → `changed=true` → file overwritten with the correct content.
4. **Part D — verify.** Compare post-restore hash against pre-drift hash. A match proves round-trip byte-fidelity.

### Reading it left to right

```
test "${RESTORED_HASH}" = "${CLEAN_HASH}" && echo "✅ restored" || echo "❌ drifted"
│    │                    │              │              │
│    │                    │              │              └─ fires if hashes differ
│    │                    │              └─ fires if hashes match
│    │                    └─ post-restore sha256 variable
│    └─ pre-drift sha256 variable
└─ POSIX string equality test
```

### The story

The drift-correction demo is the real exam-day skill. Exam tasks frequently say "a file was modified; restore its content." With a playbook using `content:`, the restoration is one command: `ansible-playbook task1.yml`. No manual editing. No diffing from memory. The declared `content:` block IS the backup.

T01-C appears here too: if you had used `src: /path/to/template` and that source file was missing, the drift-correction re-run would fail with "file not found" — even though the target `/tmp/lab01b/report.txt` exists. `content:` has no such dependency on a separate source file.

### Expected output

```text
═══ Part A: snapshot (pre-drift) ═══
pre-drift sha256: 7d3a8f…
pre-drift lines:  9
═══ Part B: corrupt (simulate drift) ═══
post-drift head -3:
=== DRIFTED REPORT ===
--- Hostname ---
rhel9host
post-drift sha256: a1b2c3…
✅ drift confirmed (hashes differ)
═══ Part C: re-run playbook (expect changed=1) ═══
...
PLAY RECAP ******* localhost : ok=2  changed=1  unreachable=0  failed=0
correction exit was: 0
═══ Part D: verify restored ═══
restored sha256: 7d3a8f…
restored lines:  9
✅ restored file is byte-identical to pre-drift
✅ line count matches
exit was: 0
```

### Switches

| Token                                   | Meaning                                                            |
|-----------------------------------------|--------------------------------------------------------------------|
| `sha256sum FILE`                        | Print 256-bit hash + filename                                      |
| `sha256sum FILE \| awk '{print $1}'`    | Print hash only (drop filename)                                    |
| `sed -i 's/OLD/NEW/' FILE`              | In-place substitution — modifies the file on disk                  |
| `test STR1 = STR2`                      | String equality                                                    |
| `test STR1 != STR2`                     | String inequality                                                  |
| `PLAY RECAP changed=N`                  | Ansible summary — N=1 means one task wrote to disk                 |

### Concept Card

| Concept | What it does |
|---|---|
| Sha256 fingerprint + restore | Pre-drift hash == post-restore hash proves byte-identical recovery |
| Drift correction | Re-run same playbook; `content:` sha256-checks and overwrites the corrupted file |
| `sed -i` drift simulation | Realistic in-place corruption without rewriting the whole file |
| `changed=true` on drifted run | Fires only when on-disk bytes differ from declared content — confirms detection |
| **🪤 Trap Risk T41** | Skipping the drift-correction re-run means you never tested the `changed=true` path. **Fix:** run both the clean re-run (Task 1 Step 5) and the drifted re-run (Task 2 Part C). |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Drift corrected | `sha256sum /tmp/lab01b/report.txt` matches pre-drift hash | Round-trip byte fidelity |
| Playbook still present | `test -s /root/rhcsa_journal/lab-01b/playbooks/task1.yml` | Playbook is the reconstruction artifact |
| `changed=1` on drifted run | PLAY RECAP in `task2.txt` evidence file | Drift detection works |
| Task 2 journal written | `ls /root/rhcsa_journal/lab-01b/task2/` shows done.txt | Evidence chain complete |

### Journal write

```bash
LAB=lab-01b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab01b/task2.txt          "$JDIR/evidence.txt"
cp /tmp/lab01b/report.txt         "$JDIR/report-restored.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Drift detection and correction with ansible.builtin.copy content:
COMMANDS: sha256sum | awk '{print $1}', sed -i 's/OLD/NEW/', ansible-playbook PB, test STR1 = STR2
TRAPS:    T41 rehearsed (drift-correction re-run done); T01-C/D rehearsed in Task 1
DRIFT:    sed -i changed header; ansible-playbook detected changed=true and restored
FIDELITY: post-restore sha256 matches pre-drift sha256 (byte-identical)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-01c — Verify trilogy: audit 01a and 01b evidence, destroy-restore drill
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab01b/task2.txt
ls /tmp/lab01b/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Part B: hash unchanged after `sed -i` | The sed pattern didn't match — `head -1 report.txt` still shows `=== System Report ===`. Check for extra spaces in the sed pattern |
| Part D: `❌ restored file differs` | A Jinja2 fact changed between runs (e.g., `ansible_uptime_seconds` if you used it). Use stable facts only (hostname, distribution, kernel, architecture) |
| Part C: `changed=0` despite corruption | Ansible used a cached copy — this shouldn't happen; re-check that `sed -i` actually modified the file with `sha256sum` |
| `PLAY RECAP failed=1` | Ansible module error; read the output above the RECAP |

> **STOP — paste the Part D `✅ restored file is byte-identical` and `✅ line count matches` lines before the Trilogy Completion Check.**

---

## Trilogy Completion Check

```bash
find /root/rhcsa_journal/lab-01{a,b,c} -name done.txt 2>/dev/null | sort
# Expect 6 paths:
# /root/rhcsa_journal/lab-01a/task1/done.txt
# /root/rhcsa_journal/lab-01a/task2/done.txt
# /root/rhcsa_journal/lab-01b/task1/done.txt
# /root/rhcsa_journal/lab-01b/task2/done.txt
# /root/rhcsa_journal/lab-01c/task1/done.txt
# /root/rhcsa_journal/lab-01c/task2/done.txt
```

> **6 paths = Lab 01 trilogy complete.** Fewer than 6 means at least one task's journal write was skipped — find the missing one and finish it before moving on.

---

## Lab 01b Checklist (2 tasks)

- [ ] Lab-Wide Setup — `/tmp/lab01b` and `/root/rhcsa_journal/lab-01b/playbooks/` created
- [ ] Task 1 — Playbook written; `--check --diff` dry-run captured; apply `changed=1`; re-apply `changed=0`; `stat` shows `root:root 644`
- [ ] Task 2 — Pre-drift sha256 captured; `sed -i` drift confirmed (hashes differ); re-run `changed=1`; post-restore sha256 matches pre-drift

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 01a** — Stdout Redirection RHCSA | The shell-side task this mirrors in Ansible |
| **Lab 01c** — Stdout Verify | Audits 01a + 01b evidence; runs the destroy-restore drill |
| **Lab 02b** — Stderr Redirection Ansible | Next b-lab — `ansible.builtin.shell` with `register:` and `stderr_lines` |
| **Lab 13b** — Aliases Ansible | Template b-lab — `ansible.builtin.blockinfile` vs `content:` |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
