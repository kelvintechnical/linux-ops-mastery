# Lab 12b: Creating Nested Directories via Ansible — `ansible.builtin.file: state=directory`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `12a` (RHCSA) → **`12b` (Ansible — you are here)** → `12c` (Verify)
- **Career arcs covered:** RHCE EX294 (`ansible.builtin.file` with `state=directory` + `mode` + `recurse`), SRE (declarative directory provisioning), DevOps (per-environment tree creation), Platform (host bootstrap layouts)
- **Prerequisite:** Lab 12a complete, Lab 00 (Ansible Control Node Setup)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = write + apply, Task 2 = idempotence proof)
- **Practice Directory (rotation #12):** `/opt`
- **Sandbox:** `/tmp/mk-ansible-lab`
- **Playbooks live at:** `/root/rhcsa_journal/lab-12b/playbooks/`
- **Traps rehearsed this lab:** **T12-C** (using `ansible.builtin.command: mkdir -p` instead of `file: state=directory`) · **T12-D** (Task 2 re-run shows `changed=1` — non-idempotent module call)

> **This lab's practice directory is: `/opt`** — every task references it in at least two commands.

---

## LAB HEADER BLOCK — run this FIRST

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T12-C T12-D"
echo "📁  PRACTICE DIR: /opt"
echo ""
ansible --version | head -n 2
ansible -m ping localhost 2>&1 | tail -n 4
```

> **STOP — if `ansible --version` fails, return to Lab 00.**

---

## Objective

Replace `mkdir -p -m 0750 ...` from Lab 12a with the declarative `ansible.builtin.file: state=directory` form. Build a 9-leaf project tree with explicit mode and ownership, run it twice, and prove the second run is `changed=0`.

---

## Concept: `state=directory` Is "Ensure Exists With These Properties"

```
   target:  state=directory, path=X, mode=0750, owner=root, group=wheel

   actual:  X missing                  →  create X, chmod 0750, chown root:wheel,  changed=1
   actual:  X exists, mode=0755        →  chmod to 0750,                            changed=1
   actual:  X exists, mode=0750, owner=user  →  chown to root:wheel,                changed=1
   actual:  X exists, all properties match  →  do nothing,                          changed=0
```

This is **stronger** than `mkdir -p -m 0750`. `mkdir -p -m` only sets mode on **newly created** segments. The Ansible module ensures mode/owner/group on **every** specified path on every run — drift correction is built in.

> **The RHCE failure mode (T12-C):** Writing `ansible.builtin.command: mkdir -p /opt/app` instead of `ansible.builtin.file: path=/opt/app state=directory`. The `command:` form is not idempotent: it succeeds the first time, succeeds on re-run (mkdir -p), but **does not correct drift** (if mode was manually changed between runs, the command form would not fix it).

---

## Module Reference (everything for Tasks 1–2)

| Token | Meaning |
|---|---|
| `ansible.builtin.file` | FQCN — required on RHCE EX294 |
| `path: PATH` | Target directory |
| `state: directory` | Desired end state: this path is a directory with the declared properties |
| `mode: '0750'` | Octal mode (quote it — bash treats 0750 as a number, YAML keeps it literal) |
| `owner: NAME` / `group: NAME` | Set owner/group |
| `recurse: yes` | Apply mode/owner/group to all children too |
| `register: VAR` | Capture the task result |
| `loop:` / `with_items:` | Iterate over a list |

---

## Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i

mkdir -p /tmp/mk-ansible-lab
mkdir -p /root/rhcsa_journal/lab-12b/playbooks

# Ensure the wheel group exists (RHEL has it by default; some distros don't)
groupadd -f wheel 2>/dev/null || true

ls -la /tmp/mk-ansible-lab
getent group wheel
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

## Task 1 — Write playbook, `--check --diff`, then apply

**Practice directory this task:** `/opt` · we read `/opt`'s layout as the model for what a `state=directory` tree should look like; writes happen in `/tmp/mk-ansible-lab/`.

### Warm-Up — commands woven into Task 1

```bash
ansible --version | head -n 1
ansible -m ping localhost                            2>&1 | tail -n 2
ls -ld /opt /tmp/mk-ansible-lab                      2>&1 | tee /tmp/mk-ansible-lab/pre.txt
find /tmp/mk-ansible-lab -type d                     2>/dev/null | wc -l
stat -c '%n mode=%a owner=%U:%G' /opt
test -d /root/rhcsa_journal/lab-12b/playbooks && echo "playbook dir OK"
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 12a: `stat -c '%n mode=%a owner=%U:%G'` is the same auditor primitive we used in 12a's Task 2 to verify mode. It now verifies what Ansible produced.

### Purpose

Write a playbook that builds the 9-leaf `projects/{web,api,db}/{logs,configs,backups}` tree at `/tmp/mk-ansible-lab/projects/`, with `mode=0750` and `owner=root group=wheel`. Run it with `--check --diff` to preview, then apply for real. Capture results with `register:` + `debug:`.

### WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `ansible --version` | Confirms control node before the play |
| `ls -ld /opt` | Real-world layout reference; we expect our build to look similar to `/opt`'s ls -ld output |
| `find /tmp/mk-ansible-lab -type d \| wc -l` | Counter: baseline vs post-play; should go from 1 to 10 (`projects/` + 9 leaves... actually 1 → 13 because of the intermediate dirs) |
| `stat -c '%n mode=%a owner=%U:%G'` | Verifies the playbook actually set mode + owner — three independent properties checked per leaf |
| `2>&1 \| tee` | Captures playbook output to `task1/apply.txt` for the journal |
| `set -o pipefail` | Ensures `ansible-playbook \| tee` failures are caught |

### Main command block

```bash
mkdir -p /tmp/mk-ansible-lab/task1

# 1. Confirm the playbook lives in the persistent journal location
ls /root/rhcsa_journal/lab-12b/playbooks/task1.yml

# 2. Preview with --check --diff
ansible-playbook --check --diff /root/rhcsa_journal/lab-12b/playbooks/task1.yml \
  2>&1 | tee /tmp/mk-ansible-lab/task1/check.txt

# 3. Apply for real
ansible-playbook /root/rhcsa_journal/lab-12b/playbooks/task1.yml \
  2>&1 | tee /tmp/mk-ansible-lab/task1/apply.txt

# 4. Verify the tree exists with the right mode + ownership
find /tmp/mk-ansible-lab/projects -type d                     2>&1 | tee /tmp/mk-ansible-lab/task1/post.txt
find /tmp/mk-ansible-lab/projects -mindepth 2 -type d -exec \
  stat -c '%n mode=%a owner=%U:%G' {} +                       2>&1 | tee -a /tmp/mk-ansible-lab/task1/post.txt
echo "exit was: $?"
```

### The playbook (`task1.yml`)

```yaml
---
- name: "Lab 12b Task 1 — build projects tree with mode 0750 owned root:wheel"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    base_dir: /tmp/mk-ansible-lab/projects
    services: [web, api, db]
    folders:  [logs, configs, backups]

  tasks:
    - name: "Ensure each leaf directory exists with correct mode + ownership"
      ansible.builtin.file:
        path: "{{ base_dir }}/{{ item.0 }}/{{ item.1 }}"
        state: directory
        mode: '0750'
        owner: root
        group: wheel
      loop: "{{ services | product(folders) | list }}"
      loop_control:
        label: "{{ item.0 }}/{{ item.1 }}"
      register: build_result

    - name: "Show what Ansible did (the register: + debug: pattern)"
      ansible.builtin.debug:
        msg: "{{ item.path }}  changed={{ item.changed }}  mode={{ item.mode | default('?') }}"
      loop: "{{ build_result.results }}"
      loop_control:
        label: "{{ item.path }}"
```

### Human-readable breakdown

1. Define two lists in `vars:` — three services and three folder types per service.
2. The `loop:` uses Jinja's `product()` filter to compute the Cartesian product (9 combinations).
3. For each combination, `ansible.builtin.file: state=directory` ensures the path exists with mode `0750`, owner `root`, group `wheel`. If the directory is missing, Ansible creates it. If it exists with wrong mode, Ansible fixes it. If it exists already correct, Ansible does nothing (`changed=false`).
4. `register: build_result` captures the per-iteration result into a list at `build_result.results[]`.
5. The debug task iterates the results and prints one line per leaf, showing `path`, `changed`, and `mode`.
6. `--check --diff` previews the actions; the apply step does them for real.

### Reading it left to right

- `vars:` — playbook-scoped variables; cleaner than hard-coding paths in every task.
- `services | product(folders) | list` — Jinja filter chain: take the cross product of two lists, materialize into a list of `[a, b]` pairs (which become `item.0` and `item.1` inside the loop).
- `loop_control: label:` — shortens the displayed task name; without it, the entire loop item dict appears in the output.
- `mode: '0750'` — quoted as a string. YAML parses `0750` as a base-10 integer 750; quoting forces literal string interpretation. Ansible converts the string to octal.
- `register: build_result` — captures `{ results: [iteration1, iteration2, ...] }`.

### The story

Two patterns to internalize from this task:

**1. Cartesian-product loops with `product()`.** Three services × three folders = 9 leaves in one task definition, not 9 separate tasks. This is the declarative equivalent of bash brace expansion `{a,b,c}/{x,y,z}` — same fan-out, expressed as data instead of syntax.

**2. Octal mode quoting.** YAML interprets `0750` as **integer 750** (seven hundred fifty), not octal 0750 (mode 488 decimal). Always quote octal modes as strings: `'0750'`. This is one of the most common YAML gotchas on the RHCE exam.

The `--check --diff` preview is the safety habit. Always preview before applying — `--diff` will literally show "the directory does not exist, would create with these properties" line by line.

### Expected output

```text
ansible [core 2.16.x]
localhost | SUCCESS => { "changed": false, "ping": "pong" }
drwxr-xr-x. 4 root root 39 ... /opt
drwxr-xr-x. 2 root root  6 ... /tmp/mk-ansible-lab
1
/opt mode=755 owner=root:root
playbook dir OK

# --- --check --diff preview (9 iterations) ---
PLAY [Lab 12b Task 1 — build projects tree with mode 0750 owned root:wheel] **
TASK [Ensure each leaf directory exists with correct mode + ownership] *******
changed: [localhost] => (item=web/logs)
changed: [localhost] => (item=web/configs)
... (9 iterations, all changed) ...
TASK [Show what Ansible did] *************************************************
ok: [localhost] => (item=/tmp/mk-ansible-lab/projects/web/logs)  =>  ...

# --- apply (real run) ---
... same iterations, all changed=true ...
PLAY RECAP **********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0

# --- post-state verification ---
/tmp/mk-ansible-lab/projects
/tmp/mk-ansible-lab/projects/web
/tmp/mk-ansible-lab/projects/web/logs
... (13 directories total: projects + 3 services + 9 leaves) ...
/tmp/mk-ansible-lab/projects/web/logs mode=750 owner=root:wheel
/tmp/mk-ansible-lab/projects/web/configs mode=750 owner=root:wheel
... (9 leaves, all 750 root:wheel) ...
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| `state: directory` | Desired end state — path must be a directory with these properties |
| `mode: '0750'` | Octal mode as a quoted string (avoid YAML int interpretation) |
| `owner: root` / `group: wheel` | Set ownership |
| `services \| product(folders) \| list` | Jinja filter — Cartesian product as a list |
| `loop_control: label:` | Readable per-iteration display |
| `register: VAR` | Capture per-item results |
| `ansible.builtin.debug: var:/msg:` | Print captured data |

### Concept Card

| Concept | What it does |
|---|---|
| FQCN `ansible.builtin.file` | Fully qualified collection name — required on RHCE EX294 |
| `state: directory` declarative | "Ensure exists with these properties" — corrects drift, not just creates |
| Mode + owner + group together | Idempotent for all three properties simultaneously |
| `product()` Jinja filter | Cartesian product — the brace-expansion equivalent for declarative code |
| Quoted octal mode `'0750'` | Prevents YAML from interpreting as integer 750 |
| `--check --diff` preview | Safety habit — show what would change, line by line |
| **🪤 Trap Risk T12-C** | Using `command: mkdir -p` instead of `file: state=directory`. The command form creates but doesn't correct drift. |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| 9 leaves created | `find /tmp/mk-ansible-lab/projects -mindepth 2 -type d \| wc -l` | Must be `9` |
| All leaves mode 0750 | `find /tmp/mk-ansible-lab/projects -mindepth 2 -type d -exec stat -c '%a' {} + \| sort -u` | Must print `750` only |
| All leaves owned root:wheel | `find /tmp/mk-ansible-lab/projects -mindepth 2 -type d -exec stat -c '%U:%G' {} + \| sort -u` | Must print `root:wheel` only |
| Playbook persisted | `ls /root/rhcsa_journal/lab-12b/playbooks/task1.yml` | Survives reboot in `/root/` |

> **Reboot reasoning:** Targets in `/tmp` evaporate; playbooks under `/root/rhcsa_journal/lab-12b/playbooks/` do not. After reboot, re-running `ansible-playbook .../task1.yml` rebuilds the entire tree with correct mode + ownership in one command — that is the deepest form of declarative idempotence.

### Journal write — BEFORE cleanup

```bash
LAB=lab-12b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/mk-ansible-lab/task1/check.txt "$JDIR/check.txt"
cp /tmp/mk-ansible-lab/task1/apply.txt "$JDIR/apply.txt"
cp /tmp/mk-ansible-lab/task1/post.txt  "$JDIR/post.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    ansible.builtin.file state=directory — first run (preview + apply)
COMMANDS: ansible-playbook --check --diff, product() filter, loop_control, register
TRAPS:    T12-C rehearsed (used file: state=directory, NOT command: mkdir)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — re-run for idempotence (changed=0); then introduce drift and watch Ansible correct it
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup

```bash
rm -rf /tmp/mk-ansible-lab/task1
ls /tmp/mk-ansible-lab/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `mode` ended up as `0750 / 0775 / 1356` (junk number) | YAML parsed `0750` as integer 750. Quote it: `mode: '0750'`. |
| `wheel` group doesn't exist | `groupadd wheel` (Setup step does this). |
| `product()` filter not found | Old Ansible — upgrade or use `with_nested:` legacy syntax. |
| `register:` data structure unclear | Add `ansible.builtin.debug: var: build_result` to inspect the raw dict. |
| Task says `changed=0` on first run | The directory already existed with the right properties from a previous lab run — that is correct idempotence. |

> **STOP — paste the PLAY RECAP line and the post-state `mode=750 owner=root:wheel` lines before Task 2.**

---

## Task 2 — The contrast: drift correction + idempotence

**Practice directory this task:** `/opt` · `state=directory` does something `mkdir -p -m` cannot — it **corrects drift**. We deliberately damage one leaf, re-run, and watch Ansible put it back.

### Warm-Up — commands woven into Task 2

```bash
find /tmp/mk-ansible-lab/projects -mindepth 2 -type d -exec \
  stat -c '%n mode=%a owner=%U:%G' {} +                       2>&1 | tee /tmp/mk-ansible-lab/pre-task2.txt
test -d /tmp/mk-ansible-lab/projects/web/logs && echo "tree intact"
ansible --version | head -n 1
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: the `stat -c '%n mode=%a owner=%U:%G'` audit primitive is now our **drift detector**. We use it to capture the state before AND after our deliberate sabotage.

### Purpose

Demonstrate two contracts simultaneously:

1. **Idempotence on clean state.** Re-run the playbook unchanged → `changed=0`.
2. **Drift correction.** Manually change one leaf's mode/owner, re-run → Ansible reports `changed=1` for that leaf only, restores it to spec.

If both behaviors hold, the play is correctly written. If either fails, the module call is wrong (T12-D).

### WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `stat -c '%n mode=%a owner=%U:%G'` | Captures the **before** drift state, the **drift introduction**, and the **after-correction** state — three independent snapshots |
| `find ... -mindepth 2 -type d` | Iterates all 9 leaves so we audit every one, not just the one we damaged |
| `2>&1 \| tee` | Captures each phase to `task2/timeline.txt` — the drift narrative as journal evidence |
| `ansible --version` | Sanity check before the rerun |
| `set -o pipefail` | Catches a silent failure in the playbook/tee chain |
| `$(date -Is)` | Stamps every phase boundary |

### Main command block

```bash
mkdir -p /tmp/mk-ansible-lab/task2

echo "═══ Phase 1: clean-state idempotence rerun ═══" \
  2>&1 | tee /tmp/mk-ansible-lab/task2/timeline.txt

ansible-playbook /root/rhcsa_journal/lab-12b/playbooks/task2.yml \
  2>&1 | tee /tmp/mk-ansible-lab/task2/clean-rerun.txt | \
  grep -E "PLAY RECAP|changed=" | tee -a /tmp/mk-ansible-lab/task2/timeline.txt

echo "═══ Phase 2: introduce drift on /projects/web/logs ═══" \
  2>&1 | tee -a /tmp/mk-ansible-lab/task2/timeline.txt
chmod 0777 /tmp/mk-ansible-lab/projects/web/logs
chown nobody:nobody /tmp/mk-ansible-lab/projects/web/logs 2>/dev/null || \
  chown nobody:nogroup /tmp/mk-ansible-lab/projects/web/logs
stat -c '  drift: %n mode=%a owner=%U:%G' /tmp/mk-ansible-lab/projects/web/logs \
  2>&1 | tee -a /tmp/mk-ansible-lab/task2/timeline.txt

echo "═══ Phase 3: re-run playbook — expect changed=1 (correction) ═══" \
  2>&1 | tee -a /tmp/mk-ansible-lab/task2/timeline.txt
ansible-playbook /root/rhcsa_journal/lab-12b/playbooks/task2.yml \
  2>&1 | tee /tmp/mk-ansible-lab/task2/drift-correct.txt | \
  grep -E "PLAY RECAP|changed=" | tee -a /tmp/mk-ansible-lab/task2/timeline.txt

echo "═══ Phase 4: verify drift corrected ═══" \
  2>&1 | tee -a /tmp/mk-ansible-lab/task2/timeline.txt
stat -c '  corrected: %n mode=%a owner=%U:%G' /tmp/mk-ansible-lab/projects/web/logs \
  2>&1 | tee -a /tmp/mk-ansible-lab/task2/timeline.txt

echo "exit was: $?"
```

### The playbook (`task2.yml`)

```yaml
---
- name: "Lab 12b Task 2 — rerun for idempotence + drift correction"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    base_dir: /tmp/mk-ansible-lab/projects
    services: [web, api, db]
    folders:  [logs, configs, backups]

  tasks:
    - name: "Re-assert state=directory on every leaf"
      ansible.builtin.file:
        path: "{{ base_dir }}/{{ item.0 }}/{{ item.1 }}"
        state: directory
        mode: '0750'
        owner: root
        group: wheel
      loop: "{{ services | product(folders) | list }}"
      loop_control:
        label: "{{ item.0 }}/{{ item.1 }}"
      register: rerun_result

    - name: "Per-leaf idempotence proof"
      ansible.builtin.debug:
        msg: "{{ item.path }}  changed={{ item.changed }}"
      loop: "{{ rerun_result.results }}"
      loop_control:
        label: "{{ item.path }}"
```

### Human-readable breakdown

1. **Phase 1 — clean rerun.** Re-run the play unchanged. Expect PLAY RECAP `changed=0`. All 9 leaves are already in the desired state.
2. **Phase 2 — drift introduction.** Manually `chmod 0777` and `chown nobody:nobody` on one leaf. Now it deviates from the declared state in two dimensions.
3. **Phase 3 — drift correction.** Re-run the same play. Ansible scans every leaf, finds 8 are correct (skip), 1 is wrong (correct it). PLAY RECAP reports `changed=1` (one leaf changed). The 8 unchanged leaves do not contribute to the changed count.
4. **Phase 4 — verify.** `stat` the damaged leaf — mode back to `0750`, owner back to `root:wheel`. Drift corrected.

### Reading it left to right

- `chmod 0777 ... ; chown nobody:nobody ...` — the deliberate sabotage. Both properties changed.
- `stat -c '  drift: %n mode=%a owner=%U:%G' PATH` — captures the damaged state as evidence in the timeline.
- `ansible-playbook .../task2.yml | tee ... | grep -E "PLAY RECAP|changed="` — runs the play, captures full output to `drift-correct.txt`, and extracts only the audit-critical lines into `timeline.txt`.
- `stat -c '  corrected: %n mode=%a owner=%U:%G' PATH` — captures the post-correction state. If this line still shows `0777 / nobody`, the play didn't work.

### The story

Drift correction is the property `mkdir -p -m` cannot provide. If you run `mkdir -p -m 0750 /tmp/X` and someone later runs `chmod 0777 /tmp/X`, the next `mkdir -p -m 0750 /tmp/X` does **not** restore the mode — `mkdir -p` only sets mode on **newly created** segments. The Ansible `file: state=directory` module checks AND corrects every property on every run.

This is what RHCE graders look for when they say "make this play idempotent." `changed=0` on rerun proves idempotence. `changed=1` after deliberate drift proves drift correction. A correctly-written play does both.

### Expected output

```text
═══ Phase 1: clean-state idempotence rerun ═══
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
═══ Phase 2: introduce drift on /projects/web/logs ═══
  drift: /tmp/mk-ansible-lab/projects/web/logs mode=777 owner=nobody:nobody
═══ Phase 3: re-run playbook — expect changed=1 (correction) ═══
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
═══ Phase 4: verify drift corrected ═══
  corrected: /tmp/mk-ansible-lab/projects/web/logs mode=750 owner=root:wheel
exit was: 0
```

> **The two key lines: `changed=0` after clean rerun and `changed=1` after drift introduction.** Both must hold for the play to be correctly written.

### Switches

| Token | Meaning |
|---|---|
| `chmod 0777 PATH` | Set permissive mode for the drift demo |
| `chown nobody:nobody PATH` | Change ownership for the drift demo |
| `grep -E "PLAY RECAP\|changed="` | Extract just the audit-critical lines |
| `tee FILE` and `tee -a FILE` | Capture (overwrite) and capture (append) |
| `stat -c '%n mode=%a owner=%U:%G'` | Three properties per line — drift narrative primitive |

### Concept Card

| Concept | What it does |
|---|---|
| Idempotence on clean state | Re-run shows `changed=0` because actual matches declared |
| Drift correction | Re-run after manual change shows `changed=1` and **restores** the property |
| Per-property correction | Mode, owner, group all checked independently each run |
| PLAY RECAP audit metric | Bottom-line `ok=N changed=M failed=K` — the grader's first look |
| Timeline narrative | Each phase's output appended to one file — the journal evidence |
| **🪤 Trap Risk T12-D** | If Phase 1 shows `changed=1` (when nothing changed), the play is wrong — module is creating something it shouldn't, or properties differ subtly. |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Idempotence proven | `grep 'changed=0' /root/rhcsa_journal/lab-12b/task2/timeline.txt` | Phase 1 line must contain `changed=0` |
| Drift correction proven | `grep 'changed=1' /root/rhcsa_journal/lab-12b/task2/timeline.txt` | Phase 3 line must contain `changed=1` |
| Post-correction state | `stat -c '%a %U:%G' /tmp/mk-ansible-lab/projects/web/logs` | Must show `750 root:wheel` |
| Both playbooks persisted | `ls /root/rhcsa_journal/lab-12b/playbooks/` | `task1.yml` and `task2.yml` both in `/root/` |

> **Reboot reasoning:** After a reboot, `/tmp/mk-ansible-lab/projects/` is gone entirely. Re-running `task1.yml` rebuilds it with correct properties from scratch — declarative provisioning is reboot-safe because the play describes the **goal**, not the path to get there.

### Journal write — BEFORE cleanup

```bash
LAB=lab-12b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/mk-ansible-lab/task2/timeline.txt      "$JDIR/timeline.txt"
cp /tmp/mk-ansible-lab/task2/clean-rerun.txt   "$JDIR/clean-rerun.txt"
cp /tmp/mk-ansible-lab/task2/drift-correct.txt "$JDIR/drift-correct.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Idempotence (changed=0) + drift correction (changed=1)
COMMANDS: ansible-playbook rerun, chmod/chown sabotage, stat audit primitive
TRAPS:    T12-D rehearsed (Phase 1 changed=0 verified; Phase 3 changed=1 verified)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-12c — auditor seat: prove the tree exists with declared properties
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup

```bash
rm -rf /tmp/mk-ansible-lab
test -d /tmp/mk-ansible-lab || echo "sandbox gone — clean exit"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Phase 1 shows `changed=1` (when nothing changed) | The play is wrong — likely YAML parsed `0750` as int 750. Quote it. |
| Phase 3 shows `changed=0` (drift not corrected) | The play isn't checking ownership or mode — re-read the playbook's `owner:` and `group:` lines. |
| `chown nobody:nobody` fails | RHEL uses `nobody` user but `nobody` group is named `nobody` on some distros, `nogroup` on others. The script tries both. |
| `grep PLAY RECAP` returns nothing | `tee` failed silently. Confirm `set -o pipefail` was active. |
| Mode is back to 0777 after rerun | Module call is wrong — likely missing the `mode:` line on the file: task. |

> **STOP — paste the two `PLAY RECAP` lines (Phase 1 and Phase 3) and the four `stat` outputs (pre, drift, post) before moving to Lab 12c.**

---

## Lab 12b Checklist (2 tasks)

- [ ] Task 1 — Write playbook with `state=directory mode='0750' owner=root group=wheel` + `product()` loop + `--check --diff` + apply
- [ ] Task 2 — Clean rerun shows `changed=0`; drift introduction shows `changed=1` correction

---

## Related Labs in the Trilogy

| Lab | Connection |
|---|---|
| **Lab 12a** — RHCSA hand-typed mkdir | The imperative form being replaced by `state=directory` |
| **Lab 12c** — Verifying Created Directories | The auditor seat: prove the tree's properties using RHCSA inspection commands |
| Lab 11b — Removing Files via Ansible | The complementary declarative pattern: `state=absent` |
| Lab 13b — Aliases via Ansible | Uses `lineinfile:` / `blockinfile:` for shell-init management |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
