# Lab 13b: Aliases via Ansible — `ansible.builtin.blockinfile`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `13a` (RHCSA) → **`13b` (Ansible — you are here)** → `13c` (Verify)
- **Career arcs covered:** RHCE EX294 (`blockinfile` is the canonical "managed block" module), SRE (fleet-wide shortcut deployment), DevOps (rc-file standardization across hosts), Platform (managed shell init files)
- **Prerequisite:** Lab 13a complete, Lab 00 (Ansible Control Node Setup)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = write + apply, Task 2 = idempotence + drift correction)
- **Practice Directory (rotation #13):** `/srv`
- **Sandbox:** `/etc/profile.d/lab13b-managed-aliases.sh`
- **Playbooks live at:** `/root/rhcsa_journal/lab-13b/playbooks/`
- **Traps rehearsed this lab:** **T13-C** (using `ansible.builtin.shell: echo "alias..." >> file` instead of `blockinfile` — no idempotence, content keeps appending) · **T13-D** (forgetting `create: yes` on `blockinfile` — module errors if the target file doesn't exist)

> **This lab's practice directory is: `/srv`** — every task references it.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T13-C T13-D"
echo "📁  PRACTICE DIR: /srv"
echo ""
ansible --version | head -n 2
ansible -m ping localhost 2>&1 | tail -n 4
```

> **STOP — if `ansible --version` fails, return to Lab 00.**

---

## Objective

Replace the hand-typed heredoc-append from Lab 13a with the declarative, idempotent `ansible.builtin.blockinfile` module. Manage a labeled block of aliases inside `/etc/profile.d/lab13b-managed-aliases.sh`. Re-run the playbook → `changed=0`. Damage the block → re-run → Ansible restores it.

---

## Concept: `blockinfile` Is Idempotent Heredoc-Append

The `blockinfile` module:

1. Looks for a **marker block** (default: `# BEGIN ANSIBLE MANAGED BLOCK` and `# END ANSIBLE MANAGED BLOCK`) inside a target file.
2. If the markers don't exist, inserts the markers + your block content.
3. If the markers exist but the content between them is wrong, replaces the content (preserves everything outside the markers).
4. If everything matches, does nothing (`changed=0`).

```
   target file BEFORE:
       (does not exist)

   target file AFTER first run:
       # BEGIN ANSIBLE MANAGED BLOCK
       alias ll='ls -lhA'
       alias srv='cd /srv'
       # END ANSIBLE MANAGED BLOCK

   target file after manual edit (someone removed a line):
       # BEGIN ANSIBLE MANAGED BLOCK
       alias ll='ls -lhA'
       # END ANSIBLE MANAGED BLOCK

   re-run playbook:
       restores the missing alias srv line
       leaves the rest of the file untouched
```

> **The RHCE failure mode (T13-C):** Writing `ansible.builtin.shell: echo "alias ll=..." >> /etc/profile.d/file.sh`. The `shell:` form appends on every run — file grows forever, never converges, never reports `changed=0`.

---

## Module Reference

| Token | Meaning |
|---|---|
| `ansible.builtin.blockinfile` | FQCN — manages a marker-delimited block inside a file |
| `path: PATH` | Target file (created if `create: yes`) |
| `block: \|` | The literal block content (multi-line YAML literal) |
| `marker: "# {mark} LAB 13B ALIASES"` | Custom marker (recommended — distinguish from other Ansible-managed blocks) |
| `create: yes` | Create the file if it doesn't exist (T13-D fix) |
| `owner` / `group` / `mode` | File-level attributes (applied to the whole file) |
| `state: present` / `state: absent` | Add the block / remove the block (with markers) |

---

## Lab-Wide Setup

```bash
sudo -i
mkdir -p /root/rhcsa_journal/lab-13b/playbooks
ls -la /etc/profile.d/ | head -n 10
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

## Task 1 — Write playbook, `--check --diff`, apply

**Practice directory this task:** `/srv` · the aliases we deploy target `/srv` paths.

### Warm-Up

```bash
ansible --version | head -n 1
ansible -m ping localhost                              2>&1 | tail -n 2
ls -la /etc/profile.d/                                 2>&1 | tee /tmp/lab13b-pre.txt
test ! -f /etc/profile.d/lab13b-managed-aliases.sh && echo "target file does not yet exist (expected)"
stat -c '%n mode=%a' /etc/profile.d
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 12b: `--check --diff` preview is now standard practice before any apply.

### Purpose

Write a playbook that uses `blockinfile` to deploy a managed alias block to `/etc/profile.d/lab13b-managed-aliases.sh`. Run with `--check --diff` to preview, then apply. Verify the file exists with the right mode + SELinux context, and the markers + content are in place.

### WEAVE TRACE

| Warm-up command | Role inside Task 1 |
|---|---|
| `ls -la /etc/profile.d/` | Snapshot **before** the play — confirms target file does NOT exist; second snapshot shows it AFTER |
| `test ! -f /etc/profile.d/lab13b-managed-aliases.sh` | Verifies the precondition (file absent) so we can prove the play created it |
| `stat -c '%a'` | Captures mode of `/etc/profile.d` and (after play) of our managed file |
| `2>&1 \| tee` | Captures playbook output to `task1/apply.txt` |
| `ansible --version` | Confirms toolchain |

### Main command block

```bash
mkdir -p /tmp/lab13b/task1

# Preview
ansible-playbook --check --diff /root/rhcsa_journal/lab-13b/playbooks/task1.yml \
  2>&1 | tee /tmp/lab13b/task1/check.txt

# Apply
ansible-playbook /root/rhcsa_journal/lab-13b/playbooks/task1.yml \
  2>&1 | tee /tmp/lab13b/task1/apply.txt

# Verify file exists with mode + SELinux context
ls -lZ /etc/profile.d/lab13b-managed-aliases.sh        2>&1 | tee /tmp/lab13b/task1/post.txt
cat /etc/profile.d/lab13b-managed-aliases.sh           2>&1 | tee -a /tmp/lab13b/task1/post.txt

# Verify aliases actually source correctly
bash -lc 'source /etc/profile.d/lab13b-managed-aliases.sh; type ll srv'  2>&1 | tee -a /tmp/lab13b/task1/post.txt
echo "exit was: $?"
```

### The playbook (`task1.yml`)

```yaml
---
- name: "Lab 13b Task 1 — deploy managed alias block via blockinfile"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    aliases_file: /etc/profile.d/lab13b-managed-aliases.sh
    aliases:
      - { name: ll,     body: "ls -lhA --color=auto" }
      - { name: srv,    body: "cd /srv" }
      - { name: svc,    body: "systemctl --no-pager status" }
      - { name: listen, body: "ss -tunap" }

  tasks:
    - name: "Deploy the managed alias block (creates file if missing, mode 0644)"
      ansible.builtin.blockinfile:
        path: "{{ aliases_file }}"
        create: yes
        owner: root
        group: root
        mode: '0644'
        marker: "# {mark} LAB 13B ALIASES"
        block: |
          {% for a in aliases %}
          alias {{ a.name }}='{{ a.body }}'
          {% endfor %}
      register: block_result

    - name: "Restore SELinux context to bin_t (sourced scripts in /etc need this)"
      ansible.builtin.command:
        cmd: "restorecon -v {{ aliases_file }}"
      register: restorecon_result
      changed_when: "'Relabeled' in restorecon_result.stdout"

    - name: "Show the result"
      ansible.builtin.debug:
        msg: "{{ aliases_file }}  block changed={{ block_result.changed }}  selinux changed={{ restorecon_result.changed }}"
```

### Human-readable breakdown

1. **Vars.** A list of `{name, body}` dicts — one entry per alias. Easy to extend.
2. **Task 1 — blockinfile.** Manages the block inside `/etc/profile.d/lab13b-managed-aliases.sh`. `create: yes` makes the file if it doesn't exist (T13-D fix). The `block:` is a Jinja `for` loop that emits one `alias NAME='BODY'` line per entry. The `marker:` is custom (`# {mark} LAB 13B ALIASES`) — distinguishes from other Ansible-managed blocks the same file might have later.
3. **Task 2 — restorecon.** `blockinfile` does not set SELinux context (it's not its job). We follow with a `command:` that runs `restorecon`. The `changed_when:` heuristic reports the task as `changed` only if `restorecon`'s stdout contains "Relabeled" — otherwise the relabel was a no-op and we shouldn't pollute the change counter.
4. **Task 3 — debug.** Show the change status of both tasks.

### Reading it left to right

- `marker: "# {mark} LAB 13B ALIASES"` — `{mark}` is a templating placeholder that becomes `BEGIN` for the top marker and `END` for the bottom marker. The result: `# BEGIN LAB 13B ALIASES` and `# END LAB 13B ALIASES` bracketing the managed block.
- `block: |` — YAML literal block scalar; preserves newlines exactly. Inside, the Jinja `{% for %}` loop generates lines.
- `create: yes` — without this, `blockinfile` errors out if the path doesn't exist (T13-D).
- `changed_when: "'Relabeled' in restorecon_result.stdout"` — overrides Ansible's default change detection for `command:`/`shell:`. Without this, every `restorecon` run would report `changed=1`, breaking idempotence even when no relabel happened.
- `register: VAR` — captures the task result; `VAR.stdout` is the command output; `VAR.changed` is the change boolean.

### The story

`blockinfile` is the **right** RHCE answer for "manage a block of lines inside a config file." Common alternatives and why they're worse:

- `ansible.builtin.lineinfile` — manages **one line** at a time. For four aliases, that's four tasks. Verbose and brittle.
- `ansible.builtin.copy` — replaces the **whole file**. Destroys any other content (like other Ansible blocks, or hand-edits the operator wanted to keep).
- `ansible.builtin.template` — Jinja-rendered whole-file. Best for files that are **entirely** managed; overkill when you just want to inject a block into an existing file.
- `ansible.builtin.shell: echo >> file` — T13-C trap. Not idempotent. The file grows on every run.

`blockinfile` is the only one that combines "manage multiple lines" + "respect everything outside my block" + "idempotent."

The `changed_when:` line on the `restorecon` task is a quiet RHCE habit graders look for. It demonstrates you understand that the default `command:`/`shell:` always reports `changed=1` — and that a senior admin overrides this with a precise heuristic. Otherwise your idempotence proof in Task 2 would always show `changed=1` because of the relabel step.

### Expected output

```text
# ── --check --diff preview ──
TASK [Deploy the managed alias block ...] *************************
--- before
+++ after: /etc/profile.d/lab13b-managed-aliases.sh
@@ -0,0 +1,7 @@
+# BEGIN LAB 13B ALIASES
+alias ll='ls -lhA --color=auto'
+alias srv='cd /srv'
+alias svc='systemctl --no-pager status'
+alias listen='ss -tunap'
+# END LAB 13B ALIASES
+

changed: [localhost]

# ── apply ──
TASK [Deploy the managed alias block ...] *** changed: [localhost]
TASK [Restore SELinux context to bin_t]    *** changed: [localhost]
TASK [Show the result]                     *** ok: [localhost] => {
    "msg": "/etc/profile.d/lab13b-managed-aliases.sh  block changed=True  selinux changed=True"
}
PLAY RECAP **********************************************************************
localhost                  : ok=3    changed=2    unreachable=0    failed=0

# ── post-state verification ──
-rw-r--r--. 1 root root system_u:object_r:bin_t:s0 ... lab13b-managed-aliases.sh
# BEGIN LAB 13B ALIASES
alias ll='ls -lhA --color=auto'
alias srv='cd /srv'
alias svc='systemctl --no-pager status'
alias listen='ss -tunap'
# END LAB 13B ALIASES

ll is aliased to `ls -lhA --color=auto'
srv is aliased to `cd /srv'
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| `blockinfile.path` | Target file |
| `blockinfile.create: yes` | Create file if missing (T13-D fix) |
| `blockinfile.marker` | Custom block delimiter; `{mark}` becomes BEGIN/END |
| `blockinfile.block: \|` | YAML literal block scalar, multi-line content |
| Jinja `{% for x in list %}` | Loop in the block content |
| `changed_when:` | Override default change detection |

### Concept Card

| Concept | What it does |
|---|---|
| `blockinfile` markers | Bracket a managed block; everything outside is preserved |
| `{mark}` template variable | Placeholder for BEGIN / END in the marker line |
| `create: yes` | Idempotent file creation as part of block management |
| `changed_when:` for command tasks | Honest change reporting — only flip changed=1 when something real happened |
| Jinja `for` in block | Generate lines from a structured `vars` list — extensible |
| **🪤 Trap Risk T13-C** | `shell: echo >> file` is not idempotent; the file grows forever. Always `blockinfile` for managed blocks. |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| File exists with markers | `grep -c "LAB 13B ALIASES" /etc/profile.d/lab13b-managed-aliases.sh` | Must be `2` (BEGIN + END) |
| Aliases sourceable | `bash -lc 'source /etc/profile.d/lab13b-managed-aliases.sh; type ll'` | Honest interactive-shell test |
| SELinux context correct | `ls -lZ /etc/profile.d/lab13b-managed-aliases.sh \| grep bin_t` | RHEL needs `bin_t` for `/etc` sourced scripts |
| Playbook persisted | `ls /root/rhcsa_journal/lab-13b/playbooks/task1.yml` | Survives reboot |

> **Reboot reasoning:** `/etc/profile.d/` is on the root partition. Survives reboot. Every new login shell sources it. The playbook itself is in `/root/rhcsa_journal/` — also persistent.

### Journal write

```bash
LAB=lab-13b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab13b/task1/check.txt "$JDIR/check.txt"
cp /tmp/lab13b/task1/apply.txt "$JDIR/apply.txt"
cp /tmp/lab13b/task1/post.txt  "$JDIR/post.txt"
cp /etc/profile.d/lab13b-managed-aliases.sh "$JDIR/deployed-file.sh"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    blockinfile deploys managed alias block to /etc/profile.d/
COMMANDS: ansible.builtin.blockinfile (FQCN), create: yes, marker: {mark}, restorecon, changed_when
TRAPS:    T13-C / T13-D rehearsed (used blockinfile not shell: echo; create: yes for missing file)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — re-run for idempotence (changed=0) + introduce drift
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup

```bash
rm -rf /tmp/lab13b/task1
ls /etc/profile.d/lab13b-managed-aliases.sh
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `blockinfile` errors "Destination /path does not exist" | Add `create: yes` (T13-D) |
| File mode wrong (0640 instead of 0644) | Quote mode as string: `mode: '0644'` |
| SELinux blocked sourcing | Run `restorecon -v PATH` (the playbook does this) |
| `restorecon` task always reports changed=1 | Add `changed_when: "'Relabeled' in result.stdout"` |
| Markers appear inside the block content | `block: \|` (literal) vs `block: >` (folded) — use `\|` |

> **STOP — paste the `cat /etc/profile.d/lab13b-managed-aliases.sh` and the `type ll srv` lines before Task 2.**

---

## Task 2 — Idempotence + drift correction

**Practice directory this task:** `/srv` · the aliases stay pointed at `/srv` while we damage and restore the file.

### Warm-Up

```bash
cat /etc/profile.d/lab13b-managed-aliases.sh             2>&1 | tee /tmp/lab13b-pre-t2.txt
wc -l /etc/profile.d/lab13b-managed-aliases.sh
grep -c "LAB 13B ALIASES" /etc/profile.d/lab13b-managed-aliases.sh
ansible --version | head -n 1
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Three phases:

1. **Clean rerun.** Re-run the play unchanged → PLAY RECAP `changed=0`.
2. **Drift introduction.** Manually remove the `srv` alias line from inside the managed block, leaving the markers intact.
3. **Drift correction.** Re-run the play → Ansible detects the block content doesn't match declared, restores the missing line, PLAY RECAP `changed=1`.

### WEAVE TRACE

| Warm-up command | Role inside Task 2 |
|---|---|
| `cat FILE` | Captures the **before** content; used three times as snapshots |
| `wc -l FILE` | Counts lines — drops by 1 after drift, restores after Ansible re-run |
| `grep -c "LAB 13B ALIASES"` | Verifies markers stay intact through the drift (must remain 2) |
| `2>&1 \| tee` | Captures the timeline to `task2/timeline.txt` |
| `set -o pipefail` | Catches silent failures in the play/tee chain |

### Main command block

```bash
mkdir -p /tmp/lab13b/task2
JDIR="/root/rhcsa_journal/lab-13b/task2"
mkdir -p "$JDIR"

echo "═══ Phase 1: clean rerun ═══"                       2>&1 | tee /tmp/lab13b/task2/timeline.txt
ansible-playbook /root/rhcsa_journal/lab-13b/playbooks/task2.yml \
  2>&1 | tee /tmp/lab13b/task2/clean-rerun.txt | \
  grep -E "PLAY RECAP|changed=" | tee -a /tmp/lab13b/task2/timeline.txt

echo "═══ Phase 2: drift — remove alias srv line ═══"    | tee -a /tmp/lab13b/task2/timeline.txt
sed -i "/^alias srv=/d" /etc/profile.d/lab13b-managed-aliases.sh
cat /etc/profile.d/lab13b-managed-aliases.sh             | tee -a /tmp/lab13b/task2/timeline.txt
echo "── file lines after drift: $(wc -l < /etc/profile.d/lab13b-managed-aliases.sh)" \
  | tee -a /tmp/lab13b/task2/timeline.txt

echo "═══ Phase 3: re-run play — expect changed=1 (block restored) ═══" \
  | tee -a /tmp/lab13b/task2/timeline.txt
ansible-playbook /root/rhcsa_journal/lab-13b/playbooks/task2.yml \
  2>&1 | tee /tmp/lab13b/task2/drift-correct.txt | \
  grep -E "PLAY RECAP|changed=" | tee -a /tmp/lab13b/task2/timeline.txt

echo "═══ Phase 4: verify block restored ═══"             | tee -a /tmp/lab13b/task2/timeline.txt
cat /etc/profile.d/lab13b-managed-aliases.sh             | tee -a /tmp/lab13b/task2/timeline.txt
bash -lc 'source /etc/profile.d/lab13b-managed-aliases.sh; type srv' \
  2>&1 | tee -a /tmp/lab13b/task2/timeline.txt

echo "exit was: $?"
```

### The playbook (`task2.yml` — identical structure to task1.yml, distinct play name)

```yaml
---
- name: "Lab 13b Task 2 — re-assert managed alias block for idempotence + drift correction"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    aliases_file: /etc/profile.d/lab13b-managed-aliases.sh
    aliases:
      - { name: ll,     body: "ls -lhA --color=auto" }
      - { name: srv,    body: "cd /srv" }
      - { name: svc,    body: "systemctl --no-pager status" }
      - { name: listen, body: "ss -tunap" }

  tasks:
    - name: "Re-assert the managed alias block"
      ansible.builtin.blockinfile:
        path: "{{ aliases_file }}"
        create: yes
        owner: root
        group: root
        mode: '0644'
        marker: "# {mark} LAB 13B ALIASES"
        block: |
          {% for a in aliases %}
          alias {{ a.name }}='{{ a.body }}'
          {% endfor %}
      register: rerun_result

    - name: "Re-assert SELinux context"
      ansible.builtin.command:
        cmd: "restorecon -v {{ aliases_file }}"
      register: restorecon_result
      changed_when: "'Relabeled' in restorecon_result.stdout"

    - name: "Per-task idempotence report"
      ansible.builtin.debug:
        msg: "block changed={{ rerun_result.changed }}  selinux changed={{ restorecon_result.changed }}"
```

### Human-readable breakdown

1. Phase 1 — clean rerun. `blockinfile` sees the block content matches declared. SELinux context is already correct. Both tasks report `changed=0`. PLAY RECAP: `changed=0`.
2. Phase 2 — `sed -i '/^alias srv=/d' FILE` deletes the `srv` alias line from inside the managed block. The markers (BEGIN / END) are still in place, but the content between them is wrong.
3. Phase 3 — re-run the play. `blockinfile` compares its declared content against actual; sees one line missing. Rewrites the entire block content (preserves the markers + everything outside). PLAY RECAP: `changed=1` (block task changed). SELinux task is `changed=0` because no relabel was needed.
4. Phase 4 — verify the `srv` alias is back; `bash -lc` confirms the alias is sourceable.

### Reading it left to right

- `sed -i "/^alias srv=/d" FILE` — `-i` in-place edit, `/PATTERN/d` deletes matching lines, `^alias srv=` anchors to start-of-line.
- `grep -E "PLAY RECAP\|changed="` — pulls just the audit-critical lines.
- `bash -lc 'source ...; type srv'` — login shell + source the file + check the alias. This is the **functional** verification, not just "file looks right."

### The story

`blockinfile` is the only standard Ansible module that combines "manage multi-line content" with "respect everything outside my block." Drift correction is what graders test by re-running your play after a deliberate edit. If the block restores, you wrote it correctly. If the block doesn't restore (because you used `copy:` or `template:` with a different pattern, or `shell:` not at all), you lose points.

The `changed_when` on `restorecon` is the second silent grader test: a play that always reports `changed=1` on rerun fails the idempotence audit even if the system is in the right state. Honest change reporting is part of the contract.

### Expected output

```text
═══ Phase 1: clean rerun ═══
PLAY RECAP ********************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
═══ Phase 2: drift — remove alias srv line ═══
# BEGIN LAB 13B ALIASES
alias ll='ls -lhA --color=auto'
alias svc='systemctl --no-pager status'
alias listen='ss -tunap'
# END LAB 13B ALIASES
── file lines after drift: 5
═══ Phase 3: re-run play — expect changed=1 (block restored) ═══
PLAY RECAP ********************************************************************
localhost                  : ok=3    changed=1    unreachable=0    failed=0
═══ Phase 4: verify block restored ═══
# BEGIN LAB 13B ALIASES
alias ll='ls -lhA --color=auto'
alias srv='cd /srv'
alias svc='systemctl --no-pager status'
alias listen='ss -tunap'
# END LAB 13B ALIASES
srv is aliased to `cd /srv'
exit was: 0
```

### Concept Card

| Concept | What it does |
|---|---|
| Clean rerun idempotence | `changed=0` proves the play converges to a stable state |
| Drift correction | Re-run after manual edit restores the managed block |
| Marker preservation | BEGIN / END stay in place; only content between is replaced |
| Honest `changed_when:` | The `restorecon` task only flips changed=1 when a relabel happens |
| `bash -lc 'source FILE; type ALIAS'` | The functional verification habit |
| **🪤 Trap Risk T13-D** | Forgetting `create: yes` means the play errors out the first time the file doesn't exist. |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Clean rerun `changed=0` | `grep changed=0 /root/rhcsa_journal/lab-13b/task2/timeline.txt` | Phase 1 line |
| Drift corrected `changed=1` | `grep changed=1 /root/rhcsa_journal/lab-13b/task2/timeline.txt` | Phase 3 line |
| Block contents restored | `grep -c '^alias ' /etc/profile.d/lab13b-managed-aliases.sh` | Must be `4` |
| Both playbooks survived | `ls /root/rhcsa_journal/lab-13b/playbooks/` | task1.yml and task2.yml |

### Journal write

```bash
LAB=lab-13b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab13b/task2/timeline.txt      "$JDIR/timeline.txt"
cp /tmp/lab13b/task2/clean-rerun.txt   "$JDIR/clean-rerun.txt"
cp /tmp/lab13b/task2/drift-correct.txt "$JDIR/drift-correct.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    blockinfile idempotence (changed=0) + drift correction (changed=1)
COMMANDS: ansible-playbook rerun, sed -i drift, bash -lc source/type verification
TRAPS:    T13-D verified (Phase 1 changed=0; Phase 3 changed=1)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-13c — auditor seat: verify cross-user + simulated reboot re-source
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup

```bash
# Leave the deployed file in place for Lab 13c to audit
rm -rf /tmp/lab13b
ls /etc/profile.d/lab13b-managed-aliases.sh
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Phase 1 shows `changed=1` (no drift, should be clean) | Likely `restorecon` task reporting changed without the `changed_when:` filter. Add it. |
| Phase 3 shows `changed=0` (drift not corrected) | `block:` content differs from what `blockinfile` is comparing. Check Jinja loop output. |
| Markers duplicated in the file | Multiple plays use the same default marker. Use custom `marker:` strings. |
| File mode/owner wrong after rerun | `blockinfile` enforces `owner/group/mode` on every run — that may report `changed=1` on first run if file existed with different perms. |

> **STOP — paste the two PLAY RECAP lines (clean and drift-corrected) before moving to Lab 13c.**

---

## Lab 13b Checklist (2 tasks)

- [ ] Task 1 — Write playbook with `blockinfile + create: yes + custom marker`, preview, apply, verify
- [ ] Task 2 — Clean rerun `changed=0`, drift introduction, re-run `changed=1` correction

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 13a** — RHCSA hand-typed aliases | The imperative form being replaced |
| **Lab 13c** — Verifying Aliases | Auditor seat: cross-user shell + simulated reboot re-source |
| Lab 12b — Directories via Ansible | Same declarative pattern, different module (`file:` vs `blockinfile:`) |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
