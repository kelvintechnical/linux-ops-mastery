# Lab 08b: Copying Files via Ansible — `ansible.builtin.copy` with `remote_src:`, `mode:`, `owner:`, `backup:`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `08a` (RHCSA) → **`08b` (Ansible — you are here)** → `08c` (Verify)
- **Career arcs covered:** RHCE EX294 (copy module + remote_src + backup pattern), SRE (declarative config replication + backup-before-replace habit), DevOps (artifact promotion with rollback), Platform (host configuration management with safe-by-default semantics)
- **Prerequisite:** Lab 08a (you must have the hand-typed `cp -a` muscle memory first), Lab 00 (Ansible Control Node Setup)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = write + apply with `backup: true`, Task 2 = idempotence + backup-rotation proof)
- **Practice Directory (rotation #08):** `/etc/skel`
- **Sandbox:** `/tmp/copy-lab/`
- **Playbooks live at:** `/root/rhcsa_journal/lab-08b/playbooks/`
- **Traps rehearsed this lab:** **T08-D** (forgetting `remote_src: true` when copying from a target-side path — Ansible looks in playbook-relative `files/` instead and fails with `Could not find or access`) · **T08-E** (writing `ansible.builtin.command: cp -a SRC DST` instead of `ansible.builtin.copy` — non-idempotent, RHCE-grading-disqualifier) · **T08-F** (forgetting `backup: true` on a config-replace task — no rollback path when the new content breaks the service)

> **This lab's practice directory is: `/etc/skel`** — the same template used in Lab 08a, now copied via the declarative module instead of by hand.

---

## 🖥️ LAB HEADER BLOCK — run this FIRST

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T08-D T08-E T08-F"
echo "📁  PRACTICE DIR: /etc/skel"
echo ""
echo "🧰 Ansible toolchain check (must pass before Task 1):"
ansible --version | head -n 2
ansible -m ping localhost 2>&1 | tail -n 4
```

> **STOP — if `ansible --version` fails or the ping returns anything other than `pong`, return to Lab 00 (Ansible Control Node Setup). Do not attempt Task 1 without a working control node.**

---

## 🎯 Objective

Replace the hand-typed `cp -a` from Lab 08a with the **idempotent declarative form** that RHCE graders expect. By the end of this lab you can write a playbook that copies a file (or tree) with explicit `mode:`, `owner:`, `group:`, and `backup: true`; preview with `--check --diff`; apply and prove idempotence on re-run; and demonstrate that `backup: true` actually rotates a `dest~timestamp` file when the source changes.

---

## 🧠 Concept: The copy module vs `template:` vs `file:`

`ansible.builtin.copy` is for **byte-for-byte file replication** — the destination ends up identical to the source. It is the declarative equivalent of `cp -a` with explicit `mode:` / `owner:` / `group:` knobs.

```
   ┌──────────────────────────┬─────────────────────────────────────────┐
   │  ansible.builtin.copy    │  Copy bytes from SRC to DEST.           │
   │                          │  SRC: control node by default;          │
   │                          │       remote_src: true → SRC on target. │
   │                          │  Idempotent: checksums dest, no-op if   │
   │                          │              already matches.           │
   ├──────────────────────────┼─────────────────────────────────────────┤
   │  ansible.builtin.template│  Render a Jinja2 template, then copy.   │
   │                          │  Use when DEST must contain variables.  │
   ├──────────────────────────┼─────────────────────────────────────────┤
   │  ansible.builtin.file    │  Manage state only (mode/owner/state).  │
   │                          │  Does NOT copy content.                 │
   └──────────────────────────┴─────────────────────────────────────────┘
```

**The RHCE failure mode (T08-E):** writing `ansible.builtin.command: cp -a /etc/skel /tmp/copy-lab/new-home/` instead of `ansible.builtin.copy`. The `command:` form is **imperative** — every run reports `changed=1`, there is no checksum-skip, and the grader marks it down because it ignores Ansible's whole point. Always reach for the module.

**The hidden gotcha (T08-D):** `src:` is resolved on the **control node by default**. When the source already lives on the target (as in `/etc/skel`), you must set `remote_src: true`. Otherwise Ansible searches `files/` relative to the playbook directory and fails with `Could not find or access '/etc/skel'`.

**The production habit (T08-F):** `backup: true` makes the module rename the existing destination to `DEST.NNNNNNNN.bak` (or similar timestamped suffix) before overwriting. The path lands in `register: result.backup_file`. This is the rollback path you will be glad you have when the new content breaks the service at 2 a.m.

---

## 📚 `ansible.builtin.copy` Reference (everything for Tasks 1–2)

| Key | Meaning | Why it matters |
|---|---|---|
| `ansible.builtin.copy:` | FQCN of the copy module — **always** use full name on RHCE | Grader requirement |
| `src:` | Source path | Control node by default; see `remote_src:` |
| `dest:` | Destination path on the target | Always required |
| `remote_src: true` | "src is on the target, not the control node" | Required for `/etc/skel`, `/etc/...` sources |
| `owner:`, `group:`, `mode:` | DAC — set unconditionally on the destination | Equivalent to `chown` + `chmod` after `cp` |
| `preserve: true` | Preserve mode + ownership + mtime from source | The `cp -p` analogue |
| `backup: true` | Save existing dest as `dest.YYYYMMDD-HHMMSS.bak` before overwrite | Rollback path |
| `force: false` | Don't overwrite if dest exists | The `cp -n` analogue |
| `validate:` | Run a command to validate before final move | Critical for `sshd_config`, `sudoers`, `httpd.conf` |
| `register: VAR` | Capture the task result | `VAR.changed`, `VAR.dest`, `VAR.backup_file`, `VAR.checksum` |
| `--check` | Dry run | Combined with `--diff` for preview |
| `--diff` | Show line-level diffs | Read what `--check` would have changed |

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i

# Sandbox for the destination
mkdir -p /tmp/copy-lab/new-home

# Confirm /etc/skel is intact (source for the copy module)
ls -laZ /etc/skel
test -d /etc/skel && echo "skel template OK"

# Playbook home (persists across reboots — Section 14 of the prompt template)
mkdir -p /root/rhcsa_journal/lab-08b/playbooks

# Seed a small fixture file we can later mutate to demonstrate backup behaviour
echo "original-config-v1"      > /tmp/copy-lab/source-config.conf
chmod 0640                       /tmp/copy-lab/source-config.conf
ls -lZ /tmp/copy-lab/source-config.conf

echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

## Task 1 — Write the playbook, preview with `--check --diff`, then apply

**Practice directory this task:** `/etc/skel` (read), `/tmp/copy-lab/new-home/` (write) · The source is the system template living on the target host — that is *why* we need `remote_src: true`. The destination is the writable sandbox — never the real `/home/` on this lab.

### 🔁 Warm-Up — commands woven into Task 1

```bash
ansible --version | head -n 2
ansible -m ping localhost                            2>&1 | tail -n 4
ls /tmp/copy-lab                                    2>&1 | tee /tmp/copy-lab/pre.txt
test -d /etc/skel && echo "skel source OK"
test -d /root/rhcsa_journal/lab-08b/playbooks && echo "playbook dir OK"
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 08a: the `stat -c '%y %C'` before/after pattern is the same — we use it after the playbook runs to prove the destination has the SELinux context and mtime we declared.

### Purpose

Write a playbook that uses `ansible.builtin.copy` with `remote_src: true`, explicit `mode:` / `owner:` / `group:`, and `backup: true` to copy two things:

1. A single file (`/tmp/copy-lab/source-config.conf`) into `/tmp/copy-lab/new-home/etc/config.conf` — the canonical config-deploy pattern with backup enabled
2. The full `/etc/skel` tree into `/tmp/copy-lab/new-home/skel/` — the directory-tree deploy with `preserve: true` so mode/timestamps survive

Preview with `ansible-playbook --check --diff` first, then apply for real. Register the result and dump it with `debug:` so you can read the `.changed`, `.dest`, `.checksum`, and (after Task 2's mutation) `.backup_file` keys.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `ansible --version` | Confirms the control node before the play — if missing, abort to Lab 00 |
| `ls /tmp/copy-lab` | Snapshot **before** the play (saved to `pre.txt`) so we can diff against `post.txt` |
| `test -d /etc/skel` | Guards `src:` — the play would T08-D-fail without `remote_src: true` if skel were missing |
| `2>&1 \| tee` | Captures the playbook output to `task1/apply.txt` for the journal |
| `set -o pipefail` | Catches a silent failure in the `ansible-playbook | tee` chain |
| `$(date -Is)` | Stamps the journal `notes.txt` |

### Main command block

```bash
cd /tmp/copy-lab
mkdir -p /tmp/copy-lab/task1

# 1. The playbook is at /root/rhcsa_journal/lab-08b/playbooks/task1.yml
#    (See the playbook content below or open the file directly.)
ls /root/rhcsa_journal/lab-08b/playbooks/task1.yml

# 2. Preview — --check --diff shows what WOULD change without changing anything
ansible-playbook --check --diff /root/rhcsa_journal/lab-08b/playbooks/task1.yml \
  2>&1 | tee /tmp/copy-lab/task1/check.txt

# 3. Apply — first real run
ansible-playbook /root/rhcsa_journal/lab-08b/playbooks/task1.yml \
  2>&1 | tee /tmp/copy-lab/task1/apply.txt

# 4. Verify with the same stat/ls -lZ pattern from Lab 08a
ls -lZ /tmp/copy-lab/new-home/etc/config.conf       2>&1 | tee /tmp/copy-lab/task1/post.txt
stat -c 'mode=%a owner=%U:%G mtime=%y ctx=%C' \
       /tmp/copy-lab/new-home/etc/config.conf       2>&1 | tee -a /tmp/copy-lab/task1/post.txt
diff /tmp/copy-lab/source-config.conf /tmp/copy-lab/new-home/etc/config.conf \
  && echo "  ✅ byte-identical" | tee -a /tmp/copy-lab/task1/post.txt
echo "exit was: $?"
```

### The playbook (`task1.yml`)

```yaml
---
- name: "Lab 08b Task 1 — copy a file and a tree via ansible.builtin.copy"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    src_file:  /tmp/copy-lab/source-config.conf
    dest_file: /tmp/copy-lab/new-home/etc/config.conf
    skel_src:  /etc/skel/
    skel_dest: /tmp/copy-lab/new-home/skel/

  tasks:
    - name: "Ensure destination parent directories exist"
      ansible.builtin.file:
        path: "{{ item }}"
        state: directory
        mode: '0755'
      loop:
        - /tmp/copy-lab/new-home/etc
        - /tmp/copy-lab/new-home/skel

    - name: "Copy a single config file with explicit DAC + backup"
      ansible.builtin.copy:
        src:        "{{ src_file }}"
        dest:       "{{ dest_file }}"
        remote_src: true        # source is on the target, not the control node
        owner:      root
        group:      root
        mode:       '0640'
        backup:     true        # save dest.NNNNNNNN.bak before overwriting
      register: file_copy_result

    - name: "Copy the /etc/skel tree with preserve: true (mode + mtime + owner)"
      ansible.builtin.copy:
        src:        "{{ skel_src }}"
        dest:       "{{ skel_dest }}"
        remote_src: true
        preserve:   true        # equivalent to cp -p
      register: tree_copy_result

    - name: "Show what changed (the register: + debug pattern RHCE graders look for)"
      ansible.builtin.debug:
        msg:
          - "file copy changed: {{ file_copy_result.changed }}"
          - "file copy dest:    {{ file_copy_result.dest }}"
          - "file copy backup:  {{ file_copy_result.backup_file | default('(none — dest did not exist)') }}"
          - "tree copy changed: {{ tree_copy_result.changed }}"
          - "tree copy dest:    {{ tree_copy_result.dest }}"
```

### Human-readable breakdown

1. The play runs against `localhost` with `connection: local` — no SSH, no remote inventory needed. This is the standard pattern for the `linux-ops-mastery` series.
2. The first task ensures the destination parent directories exist (a `copy:` task does NOT auto-create deep parent paths — that's `file:` territory).
3. The second task copies a single config file with `remote_src: true`, explicit `owner: root / group: root / mode: '0640'`, and `backup: true`. The `register: file_copy_result` captures `.changed`, `.dest`, `.backup_file`, and `.checksum`.
4. The third task copies the `/etc/skel/` tree (note the trailing slash — Lab 08a's T08-B applies here too: with the slash, the **contents** of `/etc/skel/` land directly under `/tmp/copy-lab/new-home/skel/`). `preserve: true` is the module's analogue of `cp -p`.
5. The fourth task is the audit-trail `debug:` block — every RHCE play should print the result keys so the grader can read them without re-running anything.

### Reading it left to right

- `hosts: localhost / connection: local / gather_facts: false` — the standard "lab against the control node" header.
- `ansible.builtin.copy:` — FQCN form. RHCE graders penalize the bare `copy:` form because it relies on collection-loading defaults that can change.
- `src: "{{ src_file }}"` — Jinja2 template that pulls from `vars:`.
- `dest:` — destination on the target.
- `remote_src: true` — the SRC is **on the target**, not on the control node. Without this, Ansible searches `playbook_dir/files/` for the literal path and T08-D fails.
- `owner: root / group: root / mode: '0640'` — DAC, set unconditionally. Note `mode:` is **quoted** — unquoted `0640` would be parsed as decimal 640 (mode `1200`).
- `backup: true` — before overwriting an existing dest, save it as `dest.TIMESTAMP.bak`. The path is available in `result.backup_file`.
- `preserve: true` — for the tree task: keep mode + ownership + timestamps from the source (like `cp -p`).
- `register: file_copy_result` — capture the task result; `.changed`, `.dest`, `.backup_file`, `.checksum`.
- `ansible.builtin.debug: msg: [...]` — print the captured keys; the grader reads this.

### The story

A grader hands you the task: "Deploy `/etc/skel` into a brand new user-home location and replace `/tmp/copy-lab/new-home/etc/config.conf` with the current `source-config.conf`. The deploy must be idempotent, the destination must be root:root mode 0640, and you must keep a backup of any pre-existing config." The RHCE answer is exactly the playbook above:

- `ansible.builtin.copy` (not `command: cp`) — for idempotence and grader-visible declarative intent (avoiding T08-E)
- `remote_src: true` — because both sources live on the target (avoiding T08-D)
- `mode: '0640'`, `owner: root`, `group: root` — declared explicitly so the second run also reports `changed=0` even if someone `chmod`'d the file between runs
- `backup: true` — so the previous content is recoverable as `dest.TIMESTAMP.bak` (avoiding T08-F)
- `register:` + `debug:` — the grader's audit trail

Task 2 closes the loop by re-running the same play (idempotence proof) AND mutating the source to force a real change so we can see `backup_file` populated.

### Expected output

```text
ansible [core 2.16.x] ...
localhost | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
source-config.conf  ... new-home  pre.txt

# --- --check --diff preview ---
PLAY [Lab 08b Task 1 — copy a file and a tree via ansible.builtin.copy] *******
TASK [Ensure destination parent directories exist] ***************************
changed: [localhost] => (item=/tmp/copy-lab/new-home/etc)
changed: [localhost] => (item=/tmp/copy-lab/new-home/skel)
TASK [Copy a single config file with explicit DAC + backup] ******************
--- before
+++ after: /tmp/copy-lab/new-home/etc/config.conf
@@ -0,0 +1 @@
+original-config-v1
changed: [localhost]
TASK [Copy the /etc/skel tree with preserve: true (mode + mtime + owner)] ****
changed: [localhost]
TASK [Show what changed ...] *************************************************
ok: [localhost] =>
  msg:
  - 'file copy changed: True'
  - 'file copy dest:    /tmp/copy-lab/new-home/etc/config.conf'
  - 'file copy backup:  (none — dest did not exist)'
  - 'tree copy changed: True'
  - 'tree copy dest:    /tmp/copy-lab/new-home/skel/'
PLAY RECAP *******************************************************************
localhost                  : ok=4    changed=3    unreachable=0    failed=0

# --- post-state verification ---
-rw-r-----. 1 root root unconfined_u:object_r:user_tmp_t:s0 19 May 28 ... /tmp/copy-lab/new-home/etc/config.conf
mode=640 owner=root:root mtime=2026-05-28 20:01:00.000000000 -0400 ctx=unconfined_u:object_r:user_tmp_t:s0
  ✅ byte-identical
exit was: 0
```

> **Critical line:** `backup: (none — dest did not exist)`. On a first run, there is no backup because there was no pre-existing file. Task 2 mutates the source and re-runs — *then* `backup_file` becomes a path.

### Switches

| Token | Meaning |
|---|---|
| `ansible-playbook` | The driver that reads YAML and executes its tasks |
| `--check` | Dry run — no actual changes |
| `--diff` | Show line-level diffs for changed resources |
| `hosts: localhost` | Run against the control node itself |
| `connection: local` | Skip SSH; run as the local user |
| `gather_facts: false` | Skip the implicit `setup` module |
| `ansible.builtin.copy:` | FQCN — required on RHCE |
| `src:` / `dest:` | Source / destination |
| `remote_src: true` | Source is on the target, not the control node |
| `owner:` / `group:` / `mode:` | DAC — set unconditionally |
| `preserve: true` | Preserve mode + ownership + timestamps from source |
| `backup: true` | Save existing dest before overwrite |
| `validate:` | Run a command to validate before final move |
| `register: VAR` | Capture the task result into a playbook variable |
| `ansible.builtin.debug:` | Print a variable or message |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | FQCN (`ansible.builtin.copy`) | Fully qualified collection name — required on RHCE EX294 |
|   | `remote_src: true` | "src is on the target, not the control node" — must-have for `/etc/...` sources |
|   | Trailing slash on `src:` | Same semantics as `cp`: `/etc/skel/` copies contents; `/etc/skel` copies the directory |
|   | `preserve: true` | The module's `cp -p` — preserves mode + ownership + timestamps from source |
|   | `backup: true` + `register:` | Result has `.backup_file` populated when dest was replaced |
|   | Idempotence | Module checksums dest; second run = `changed=0` if content + mode + owner all match |
|   | `--check --diff` preview | Safety habit: always preview before applying |
|   | Quote `mode:` | `mode: '0640'` (octal string), NOT `mode: 0640` (parsed as decimal) |
| 🪤 | **Trap Risk T08-D** | Forgetting `remote_src: true` → Ansible searches `playbook_dir/files/` and fails with `Could not find or access` |
| 🪤 | **Trap Risk T08-E** | `ansible.builtin.command: cp -a SRC DST` → non-idempotent, RHCE penalty |
| 🪤 | **Trap Risk T08-F** | Omitting `backup: true` on a config-replace task → no rollback path |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| File copy landed | `ls -lZ /tmp/copy-lab/new-home/etc/config.conf` | Mode `0640`, owner `root:root`, context inherited |
| Tree copy landed | `ls /tmp/copy-lab/new-home/skel/` | Should list `.bashrc`, `.bash_profile`, `.bash_logout` directly (trailing-slash semantics) |
| Playbook persisted | `ls /root/rhcsa_journal/lab-08b/playbooks/task1.yml` | Playbook in `/root/` survives reboot; `/tmp/` would not |
| Evidence captured | `wc -l /root/rhcsa_journal/lab-08b/task1/apply.txt` | The PLAY RECAP line (`ok=4 changed=3`) is the auditable result |

> **Reboot reasoning:** The destination tree in `/tmp/copy-lab/` evaporates at reboot, but the playbook in `/root/rhcsa_journal/lab-08b/playbooks/` does not. After a reboot, you could re-run `ansible-playbook .../task1.yml` and reproduce the exact same destination layout — **proof of declarative idempotence across reboot**. Lab 08c Task 2 closes this loop with a simulated reboot.

### Journal write — BEFORE cleanup

```bash
LAB=lab-08b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/copy-lab/task1/check.txt "$JDIR/check.txt"
cp /tmp/copy-lab/task1/apply.txt "$JDIR/apply.txt"
cp /tmp/copy-lab/task1/post.txt  "$JDIR/post.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    ansible.builtin.copy with remote_src + mode + owner + group + backup + preserve
COMMANDS: ansible-playbook --check --diff, ansible-playbook, register, debug
TRAPS:    T08-D rehearsed (remote_src: true set), T08-E rehearsed (used module not command),
          T08-F rehearsed (backup: true set even though no backup written on first run)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — re-run for idempotence proof + mutate source to demonstrate backup rotation
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
# Keep the playbook AND the journal — drop only the live sandbox transcript
rm -rf /tmp/copy-lab/task1
ls /tmp/copy-lab/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `ansible-playbook: command not found` | Return to Lab 00 — control node not installed |
| `Could not find or access '/etc/skel'` | T08-D — `remote_src: true` missing. Add it. |
| `mode: 0640` parsed as `1200` on disk | Unquoted octal. Use `mode: '0640'` (quoted). |
| First-run `backup_file: (none ...)` | Correct — backup only created when dest already exists. Task 2 proves it. |
| `changed=3` on first run | Correct — dirs were created + file copy + tree copy = three changes. |
| `Permission denied` writing dest | `become: true` missing — add it to the play. |

> **STOP — paste the PLAY RECAP line (`ok=4 changed=3`) and the `backup: (none ...)` line from the debug block before Task 2. The first-run "no backup" is correct; Task 2 mutates the source so the second run *will* populate `backup_file`.**

---

## Task 2 — Idempotence proof + force a real change to demonstrate `backup: true` rotation

**Practice directory this task:** `/etc/skel` (read), `/tmp/copy-lab/new-home/` (write) · The destination from Task 1 is already in place. Task 2 re-runs to prove `changed=0`, then mutates the source and re-runs again to prove `backup_file` is populated when an actual replacement occurs.

### 🔁 Warm-Up — commands woven into Task 2

```bash
ls /tmp/copy-lab/new-home/etc                       2>&1 | tee /tmp/copy-lab/pre-task2.txt
test -f /tmp/copy-lab/new-home/etc/config.conf && echo "dest from task1 present"
test -d /tmp/copy-lab/new-home/skel && echo "tree from task1 present"
stat -c 'dest mode=%a owner=%U:%G mtime=%y' /tmp/copy-lab/new-home/etc/config.conf
ansible --version | head -n 1
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: the playbook is unchanged. We re-run it. If `task1.yml` was correctly declarative, the second run reports `changed=0` even though the playbook itself did not change.

### Purpose

Two-phase proof:

1. **Phase A — Idempotence proof.** Re-run `task1.yml` with no changes. Both copy tasks must report `ok` (not `changed`) and the PLAY RECAP must show `changed=0`. This is the canonical Ansible idempotence contract.
2. **Phase B — Backup-rotation proof.** Mutate the source (`source-config.conf` → `v2 content`) and re-run. The file-copy task now reports `changed=1`, and `register: file_copy_result` exposes `.backup_file` pointing at the previous v1 content saved as `dest.TIMESTAMP.bak`. Confirm the backup file exists, contains the v1 content, and that the new dest contains the v2 content.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `ls /tmp/copy-lab/new-home/etc` | Pre-condition check — config.conf must exist from Task 1 |
| `test -f` / `test -d` | Confirm Task 1 outputs are present before the re-run |
| `stat -c '%y'` | Records the dest mtime BEFORE the re-run; in Phase A it must NOT change |
| `2>&1 \| tee` | Captures the second-run output to `task2/rerun.txt` — the **proof artifact** |
| `set -o pipefail` | Ensures the `tee` chain reports a failed `ansible-playbook` honestly |
| `ansible --version` | Confirms control node still working (rules out version-skew false negatives) |

### Main command block

```bash
mkdir -p /tmp/copy-lab/task2

# ───────────────────────── Phase A — idempotence proof ─────────────────────────
echo "═══ Phase A — re-run task1.yml unchanged; expect changed=0 ═══" \
  | tee /tmp/copy-lab/task2/rerun.txt

ansible-playbook /root/rhcsa_journal/lab-08b/playbooks/task1.yml \
  2>&1 | tee -a /tmp/copy-lab/task2/rerun.txt

echo "── grep the audit-critical lines ──" | tee -a /tmp/copy-lab/task2/rerun.txt
grep -E "PLAY RECAP|changed=|backup" /tmp/copy-lab/task2/rerun.txt

# ─────────────────── Phase B — mutate source, force backup rotation ──────────
echo "═══ Phase B — mutate source, re-run, verify backup_file is populated ═══" \
  | tee /tmp/copy-lab/task2/backup-proof.txt

# Capture v1 content + timestamp BEFORE the mutation
cat /tmp/copy-lab/new-home/etc/config.conf | tee -a /tmp/copy-lab/task2/backup-proof.txt
stat -c 'pre  mtime=%y'   /tmp/copy-lab/new-home/etc/config.conf \
                                                     | tee -a /tmp/copy-lab/task2/backup-proof.txt

# Mutate the source to v2 content
echo "updated-config-v2" > /tmp/copy-lab/source-config.conf
cat /tmp/copy-lab/source-config.conf | tee -a /tmp/copy-lab/task2/backup-proof.txt

# Use a slightly modified playbook (task2.yml) that adds a verbose debug of backup_file
ansible-playbook /root/rhcsa_journal/lab-08b/playbooks/task2.yml \
  2>&1 | tee /tmp/copy-lab/task2/rotation.txt

# Inspect the result
BACKUP=$(grep -Eo '/tmp/copy-lab/new-home/etc/config.conf\.[0-9.]+\.[0-9]+(\.bak)?' \
            /tmp/copy-lab/task2/rotation.txt | head -n 1)
echo "Detected backup_file: $BACKUP" | tee -a /tmp/copy-lab/task2/backup-proof.txt

if [ -n "$BACKUP" ] && [ -f "$BACKUP" ]; then
  echo "── backup CONTENTS (should be v1) ──"    | tee -a /tmp/copy-lab/task2/backup-proof.txt
  cat "$BACKUP"                                   | tee -a /tmp/copy-lab/task2/backup-proof.txt
  echo "── current dest (should be v2) ──"        | tee -a /tmp/copy-lab/task2/backup-proof.txt
  cat /tmp/copy-lab/new-home/etc/config.conf      | tee -a /tmp/copy-lab/task2/backup-proof.txt
  echo "  ✅ backup rotation honest"              | tee -a /tmp/copy-lab/task2/backup-proof.txt
else
  echo "  ❌ no backup file found — backup: true was missing or rotation failed" \
                                                  | tee -a /tmp/copy-lab/task2/backup-proof.txt
fi

# Phase A re-verify: re-run task2.yml one more time and prove it now reports changed=0
echo "═══ Phase A redux — task2.yml is now idempotent at v2 ═══" \
  | tee -a /tmp/copy-lab/task2/rerun.txt
ansible-playbook /root/rhcsa_journal/lab-08b/playbooks/task2.yml \
  2>&1 | tee -a /tmp/copy-lab/task2/rerun.txt
grep -E "PLAY RECAP|changed=" /tmp/copy-lab/task2/rerun.txt | tail -n 4
echo "exit was: $?"
```

### The playbook (`task2.yml` — same module, more verbose debug for backup_file)

```yaml
---
- name: "Lab 08b Task 2 — re-run + force backup rotation"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    src_file:  /tmp/copy-lab/source-config.conf
    dest_file: /tmp/copy-lab/new-home/etc/config.conf
    skel_src:  /etc/skel/
    skel_dest: /tmp/copy-lab/new-home/skel/

  tasks:
    - name: "Re-copy the single config file (mode/owner/group/backup as before)"
      ansible.builtin.copy:
        src:        "{{ src_file }}"
        dest:       "{{ dest_file }}"
        remote_src: true
        owner:      root
        group:      root
        mode:       '0640'
        backup:     true
      register: file_copy_result

    - name: "Re-copy the /etc/skel tree (preserve: true as before)"
      ansible.builtin.copy:
        src:        "{{ skel_src }}"
        dest:       "{{ skel_dest }}"
        remote_src: true
        preserve:   true
      register: tree_copy_result

    - name: "Show backup_file — the rollback path (populated only when dest existed and differed)"
      ansible.builtin.debug:
        msg:
          - "file changed: {{ file_copy_result.changed }}"
          - "file dest:    {{ file_copy_result.dest }}"
          - "file checksum:{{ file_copy_result.checksum | default('n/a') }}"
          - "BACKUP_FILE:  {{ file_copy_result.backup_file | default('(none — dest matched source already)') }}"
          - "tree changed: {{ tree_copy_result.changed }}"
```

### Human-readable breakdown

1. **Phase A** — re-run `task1.yml` (the *exact same* playbook from Task 1) with no source mutation. Both `copy:` tasks see the destination already matches their declaration (same content, same mode, same owner, same group) and report `ok` instead of `changed`. PLAY RECAP shows `changed=0`. That is idempotence proven.
2. **Phase B — capture v1 state** — read the current contents of `dest_file` (should still say `original-config-v1`) and snapshot the mtime. This is the "before" baseline.
3. **Phase B — mutate source** — overwrite `/tmp/copy-lab/source-config.conf` with `updated-config-v2`. Now the source and destination genuinely differ.
4. **Phase B — re-run** `task2.yml`. The file-copy task detects the checksum mismatch, renames the existing dest to `dest.NNNN.bak` (because `backup: true`), copies the new content into place, and `register:` captures `.backup_file` as the path to the rotated file.
5. **Phase B — verify** — `cat` the backup file (should be v1 content) and the current dest (should be v2 content). Both must be true for `backup: true` to have done its job.
6. **Phase A redux** — re-run `task2.yml` one more time at the v2 state. Idempotence holds: `changed=0` again, no new backup created (because nothing changed).

### Reading it left to right

- `grep -E "PLAY RECAP|changed=|backup"` — extended regex with three alternations; pulls just the audit-critical lines out of the verbose play output.
- `grep -Eo '/tmp/copy-lab/new-home/etc/config.conf\.[0-9.]+\.[0-9]+(\.bak)?'` — `-o` prints only the matched text; the regex matches Ansible's backup-file naming scheme (`dest.NNNNN.NN.bak` or `dest.NNNNN`).
- `[ -n "$BACKUP" ] && [ -f "$BACKUP" ]` — guard the `cat` so we don't error if backup detection failed.
- `file_copy_result.backup_file | default('(none — ...)')` — Jinja default filter; renders fallback text if the key is unset (which it is on a no-change run).
- `tee -a` (append) vs `tee` (overwrite) — `-a` is critical when multiple commands write to the same evidence file.

### The story

Idempotence is **the** RHCE concept. The canonical re-run test is the grader's fastest way to tell a correctly-written `copy:` task from an imperative `command: cp` wrapper. The first form reports `changed=0` on the second run; the second form reports `changed=1` every single time (T08-E).

`backup: true` is the **production** concept. In a real cluster, you replace `/etc/httpd/conf/httpd.conf` and the new content has a typo — httpd refuses to restart. Without `backup: true`, your rollback is "find the old content from git history or a recent backup tarball." With `backup: true`, your rollback is one command: `cp /etc/httpd/conf/httpd.conf.NNNNN.bak /etc/httpd/conf/httpd.conf && systemctl restart httpd`. The discipline is: every config-replace task in production gets `backup: true`, every time, no exceptions. Lab 08b bakes that habit in before you ever touch a real production config.

### Expected output

```text
═══ Phase A — re-run task1.yml unchanged; expect changed=0 ═══
PLAY [Lab 08b Task 1 — copy a file and a tree via ansible.builtin.copy] *******
TASK [Ensure destination parent directories exist] ***************************
ok: [localhost] => (item=/tmp/copy-lab/new-home/etc)
ok: [localhost] => (item=/tmp/copy-lab/new-home/skel)
TASK [Copy a single config file with explicit DAC + backup] ******************
ok: [localhost]
TASK [Copy the /etc/skel tree with preserve: true (mode + mtime + owner)] ****
ok: [localhost]
TASK [Show what changed ...] *************************************************
ok: [localhost] =>
  msg:
  - 'file copy changed: False'
  - 'file copy backup:  (none — dest did not exist)'
  - 'tree copy changed: False'
PLAY RECAP *******************************************************************
localhost                  : ok=4    changed=0    unreachable=0    failed=0

═══ Phase B — mutate source, re-run, verify backup_file is populated ═══
original-config-v1
pre  mtime=2026-05-28 20:01:00.000000000 -0400
updated-config-v2

TASK [Re-copy the single config file ...] ************************************
changed: [localhost]
TASK [Re-copy the /etc/skel tree ...] ****************************************
ok: [localhost]
TASK [Show backup_file ...] **************************************************
ok: [localhost] =>
  msg:
  - 'file changed: True'
  - 'file dest:    /tmp/copy-lab/new-home/etc/config.conf'
  - 'BACKUP_FILE:  /tmp/copy-lab/new-home/etc/config.conf.12345.2026-05-28@20:02:00~'
  - 'tree changed: False'
PLAY RECAP *******************************************************************
localhost                  : ok=3    changed=1    unreachable=0    failed=0

Detected backup_file: /tmp/copy-lab/new-home/etc/config.conf.12345.2026-05-28@20:02:00~
── backup CONTENTS (should be v1) ──
original-config-v1
── current dest (should be v2) ──
updated-config-v2
  ✅ backup rotation honest

═══ Phase A redux — task2.yml is now idempotent at v2 ═══
PLAY RECAP *******************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
exit was: 0
```

> **Two key lines:** Phase A's `changed=0` (idempotence) AND Phase B's `BACKUP_FILE: /tmp/copy-lab/new-home/etc/config.conf.NNNNN...` (rotation honest). Both must be present.

### Switches

| Token | Meaning |
|---|---|
| `grep -E "A\|B\|C"` | Extended regex; match any of three alternations |
| `grep -Eo PATTERN` | Print only the matched text, one per line |
| `[ -n "$VAR" ]` | True if `$VAR` is non-empty |
| `[ -f PATH ]` | True if PATH is an existing regular file |
| `file_copy_result.backup_file` | The Ansible-populated path of the rotated previous content |
| `\| default('text')` | Jinja2 filter — fallback text when the key is unset |
| `tee -a FILE` | Append to FILE (not overwrite) |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | Idempotence proof | Re-run with no change → `changed=0`. RHCE acceptance test. |
|   | Declarative vs imperative | `copy:` checksums dest; `command: cp` does not — re-run cleanly is the test |
|   | `backup_file` register key | Populated only when dest was overwritten with different content |
|   | Backup file naming | `dest.PID.YYYY-MM-DD@HH:MM:SS~` (suffix may vary by ansible-core version) |
|   | Phase A vs Phase B | Phase A proves idempotence; Phase B proves backup rotation actually works |
|   | Idempotence holds across reboot | Even after `/tmp` clears, re-running the playbook reproduces the same dest with `changed=1` on the FIRST post-reboot run, then `changed=0` on the second |
| 🪤 | **Trap Risk T08-F** | If `backup: true` is omitted and the new content breaks the service, no rollback path exists. Always include backup on config-replace. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Idempotence proven (Phase A) | `grep 'changed=0' /root/rhcsa_journal/lab-08b/task2/rerun.txt` | Must match — that's the contract |
| Backup file exists (Phase B) | `ls /tmp/copy-lab/new-home/etc/config.conf.*` | Must show one timestamped backup file |
| Backup content is v1 | `cat $(ls /tmp/copy-lab/new-home/etc/config.conf.* \| head -n 1)` | Must print `original-config-v1` |
| Current dest is v2 | `cat /tmp/copy-lab/new-home/etc/config.conf` | Must print `updated-config-v2` |
| Playbooks survive reboot | `ls /root/rhcsa_journal/lab-08b/playbooks/` | Both `task1.yml` and `task2.yml` live in `/root/` |

> **Reboot reasoning:** Everything under `/tmp/copy-lab/` evaporates at reboot — including the backup file. The **only** durable artifact is the playbook itself under `/root/rhcsa_journal/lab-08b/playbooks/`. Lab 08c Task 2 simulates a reboot and proves that re-running the playbook from the journal still produces the correct destination layout.

### Journal write — BEFORE cleanup

```bash
LAB=lab-08b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/copy-lab/task2/rerun.txt        "$JDIR/rerun.txt"
cp /tmp/copy-lab/task2/rotation.txt     "$JDIR/rotation.txt"
cp /tmp/copy-lab/task2/backup-proof.txt "$JDIR/backup-proof.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Idempotence (Phase A) + backup: true rotation (Phase B)
COMMANDS: ansible-playbook (rerun), grep -E "PLAY RECAP|changed=|backup", register backup_file
TRAPS:    T08-D / T08-E / T08-F rehearsed — module form, remote_src, backup all verified
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-08c — auditor seat: diff -r + stat + ls -lZ + simulated-reboot persistence proof
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
# Keep playbooks + journal; clean only the sandbox
rm -rf /tmp/copy-lab/task2
ls /tmp/copy-lab/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Phase A re-run shows `changed=1` | Module is wrong (likely `command: cp`) — switch to `ansible.builtin.copy`. T08-E. |
| Phase A re-run fails on mode mismatch | The previous run did NOT set mode — re-apply with `mode: '0640'` then re-test. |
| Phase B re-run shows `BACKUP_FILE: (none ...)` | Source and dest already matched. Mutate source first: `echo "v2" > $src`. |
| No `*.bak`-style file in dest dir | `backup: true` was missing in the task — T08-F. Add it. |
| Backup file name doesn't match the regex | Ansible-core version difference. Inspect `ls /tmp/copy-lab/new-home/etc/` and adjust the regex (or just `ls config.conf.*`). |
| `grep PLAY RECAP` returns nothing | `tee` failed silently; turn on `set -o pipefail`. |

> **STOP — paste both the Phase A `changed=0` line AND the Phase B `BACKUP_FILE: ...` line before moving on to Lab 08c. Both are required — Phase A proves the module is correct, Phase B proves the safety net is real.**

---

## Lab 08b Checklist (2 tasks)

- [ ] Task 1 — Write the playbook with `remote_src` + `mode` + `owner` + `backup` + `preserve` + `--check --diff` preview + apply + `register`/`debug` evidence
- [ ] Task 2 — Phase A idempotence (`changed=0`) + Phase B backup rotation (`backup_file` populated) + journal both transcripts

---

## 🔗 Related Labs in the Trilogy

| Lab | Connection |
|---|---|
| **Lab 08a** — RHCSA hand-typed copy | The imperative form of what `ansible.builtin.copy` does declaratively |
| **Lab 08c** — Verifying Copies | The auditor seat: `diff -r` + `stat` + `ls -lZ` + simulated-reboot persistence |
| Lab 00 — Ansible Control Node Setup | Prerequisite — without a working control node, this lab cannot start |
| Lab 11b — Removing Files via Ansible | The destructive counterpart — `file: state=absent` with the same idempotence story |
| Lab 12b — Creating Nested Directories via Ansible | Complementary pattern — `file: state=directory` for parents that `copy:` cannot auto-create |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
