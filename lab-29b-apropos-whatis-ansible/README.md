# Lab 29b: Searching Manuals by Keyword (Ansible) — boundary-aware `mandb`, `whatis`, `apropos`

- **Series:** linux-ops-mastery — Documentation Discovery and Command Fluency
- **Trilogy:** [`29a`](../lab-29a-apropos-whatis-rhcsa/) (RHCSA hand-typed) → **`29b`** (Ansible trap practice across boundary) → [`29c`](../lab-29c-apropos-whatis-verify/) (Verify capstone)
- **Section 18 boundary note:** there is no dedicated Ansible module for rebuilding the man-db cache or reproducing every `apropos` matching semantic. This b-lab is intentionally kept for trap practice via `command`/`shell` + assertions.
- **Time Estimate:** 30-40 minutes
- **Tasks:** 2 (Task 1 = boundary-safe `mandb -c` automation pattern · Task 2 = T29-A proof with `register` + `assert` that `apropos` returns >0)
- **Practice Directory (rotation #29):** `/proc`
- **Playbooks:** `/root/rhcsa_journal/lab-29b/playbooks/`
- **Sandbox (Tier B):** `/tmp/lab29b` with `USER=labuser_29_apropos`, `GROUP=labgrp_29_apropos`, `USER_HOME=/tmp/lab29b/home_labuser_29_apropos`
- **Traps rehearsed:** **T29-A** · **T29-B** · **T41** · **T44**

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
ansible --version | head -n 2
ansible localhost -m ping --connection=local
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T29-A T29-B T41 T44"
echo "📁  PRACTICE DIR: /proc"
ls -ld /proc /var/cache/man
```

> **STOP — paste header output before setup.**

---

## Objective

1. Automate man-db rebuild using boundary-safe patterns (`command` guard + `shell` proof).
2. Capture and assert searchable documentation state using `register` outputs.
3. Explicitly catch stale-index failures before they leak into later labs.

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=29
export LAB_SLUG=apropos
export SANDBOX=/tmp/lab29b
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-29b/playbooks /root/rhcsa_journal/lab-29b/task1 /root/rhcsa_journal/lab-29b/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /var/cache/man /proc
```

---

## Task 1 — Automate `mandb -c` with boundary-safe patterns

### Purpose

Implement the exact boundary behavior requested:

- either `ansible.builtin.command` with a `creates:` guard trick
- or `ansible.builtin.shell` with explicit `changed_when`

This task demonstrates both in one playbook for comparison.

### Playbook (`/root/rhcsa_journal/lab-29b/playbooks/task1.yml`)

```yaml
---
- name: "Lab 29b Task 1 - boundary-safe mandb rebuild"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    sentinel: /tmp/lab29b/.mandb_rebuilt_once

  tasks:
    - name: "Ensure sandbox exists"
      ansible.builtin.file:
        path: /tmp/lab29b
        state: directory
        mode: "0755"

    - name: "Boundary pattern A - command mandb -c with creates trick"
      ansible.builtin.command:
        cmd: /usr/bin/bash -lc 'mandb -c >/tmp/lab29b/mandb-command.log 2>&1 && touch {{ sentinel }}'
        creates: "{{ sentinel }}"
      register: mandb_cmd

    - name: "Boundary pattern B - shell mandb -c with changed_when"
      ansible.builtin.shell: "mandb -c"
      register: mandb_shell
      changed_when: "'processed' in (mandb_shell.stdout | lower) or 'processed' in (mandb_shell.stderr | lower)"
      failed_when: mandb_shell.rc != 0

    - name: "Capture whatis/apropos sample"
      ansible.builtin.shell: |
        set -o pipefail
        {
          echo "whatis grep:"
          whatis grep
          echo ""
          echo "apropos list directory:"
          apropos 'list directory'
        } > /tmp/lab29b/task1-sample.txt
      register: sample_capture
      changed_when: false

    - name: "Write task summary"
      ansible.builtin.copy:
        dest: /tmp/lab29b/task1-summary.txt
        mode: "0644"
        content: |
          mandb_cmd_changed={{ mandb_cmd.changed }}
          mandb_shell_changed={{ mandb_shell.changed }}
          mandb_shell_rc={{ mandb_shell.rc }}
          sample_capture_rc={{ sample_capture.rc }}
```

### Run + verify

```bash
TASKLOG=/tmp/lab29b/task1.txt
ansible-playbook /root/rhcsa_journal/lab-29b/playbooks/task1.yml 2>&1 | tee "$TASKLOG"
cat /tmp/lab29b/task1-summary.txt | tee -a "$TASKLOG"
cat /tmp/lab29b/task1-sample.txt  | tee -a "$TASKLOG"
ls -l /tmp/lab29b/.mandb_rebuilt_once /tmp/lab29b/mandb-command.log 2>/dev/null | tee -a "$TASKLOG"
echo "exit was: $?" | tee -a "$TASKLOG"
```

### Concept Card

| Concept | What it does |
|---|---|
| Boundary command pattern | `command` with `creates:` makes imperative command re-runs idempotent |
| Boundary shell pattern | `shell` allows richer checks but must set `changed_when` and `failed_when` explicitly |
| Sentinel file | Encodes one-time completion for idempotence |
| **Section 18 boundary** | No dedicated module for `mandb` index rebuild semantics |

### Journal write

```bash
LAB=lab-29b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab29b/task1.txt "$JDIR/evidence.txt"
cp /tmp/lab29b/task1-summary.txt "$JDIR/task1-summary.txt"
cp /tmp/lab29b/task1-sample.txt "$JDIR/task1-sample.txt"
cp /root/rhcsa_journal/lab-29b/playbooks/task1.yml "$JDIR/task1.yml"
```

---

## Task 2 — Trap T29-A: assert `apropos` returns >0 after rebuild

### Purpose

Treat stale index behavior as a hard failure in automation by asserting query output quality.

### Playbook (`/root/rhcsa_journal/lab-29b/playbooks/task2.yml`)

```yaml
---
- name: "Lab 29b Task 2 - T29-A trap checks"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Run mandb -c and capture output"
      ansible.builtin.shell: "mandb -c"
      register: mandb_rebuild
      changed_when: true
      failed_when: mandb_rebuild.rc != 0

    - name: "Query apropos phrase"
      ansible.builtin.command:
        cmd: apropos list directory
      register: apropos_query
      changed_when: false

    - name: "Query whatis target"
      ansible.builtin.command:
        cmd: whatis grep
      register: whatis_query
      changed_when: false

    - name: "Assert T29-A conditions"
      ansible.builtin.assert:
        that:
          - mandb_rebuild.rc == 0
          - (apropos_query.stdout_lines | length) > 0
          - (whatis_query.stdout_lines | length) > 0
        fail_msg: "T29-A triggered: cache/query evidence incomplete after mandb -c"
        success_msg: "✅ T29-A guarded: apropos and whatis return indexed results"

    - name: "Write trap-check summary"
      ansible.builtin.copy:
        dest: /tmp/lab29b/task2-assertions.txt
        mode: "0644"
        content: |
          mandb_rc={{ mandb_rebuild.rc }}
          apropos_lines={{ apropos_query.stdout_lines | length }}
          whatis_lines={{ whatis_query.stdout_lines | length }}
          apropos_first={{ (apropos_query.stdout_lines | first | default('none')) }}
```

### Run + verify

```bash
TASKLOG=/tmp/lab29b/task2.txt
ansible-playbook /root/rhcsa_journal/lab-29b/playbooks/task2.yml 2>&1 | tee "$TASKLOG"
cat /tmp/lab29b/task2-assertions.txt | tee -a "$TASKLOG"
sudo -u "${USER}" bash -c "apropos 'list directory' > '${USER_HOME}/apropos-verify-asuser.txt'"
stat -c '%U:%G %a %n' "${USER_HOME}/apropos-verify-asuser.txt" | tee -a "$TASKLOG"
echo "exit was: $?" | tee -a "$TASKLOG"
```

### Concept Card

| Concept | What it does |
|---|---|
| `register` | Captures command output for validation |
| `assert` | Converts trap conditions into deterministic pass/fail gates |
| Query line-count checks | Guards against silent empty-output regressions |
| **🪤 Trap Risk T29-A** | `apropos` may return nothing if index stale; must rebuild and assert non-empty |
| **🪤 Trap Risk T29-B** | `apropos` phrase matching can differ from exact literal; use explicit options when required |

### Journal write

```bash
LAB=lab-29b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab29b/task2.txt "$JDIR/evidence.txt"
cp /tmp/lab29b/task2-assertions.txt "$JDIR/task2-assertions.txt"
cp /root/rhcsa_journal/lab-29b/playbooks/task2.yml "$JDIR/task2.yml"
cp "${USER_HOME}/apropos-verify-asuser.txt" "$JDIR/apropos-verify-asuser.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
LAB_USER: ${USER}
LAB_GROUP: ${GROUP}
STATUS: COMPLETE
EOF
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 29b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"   || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}"               && echo "❌ sandbox remains"|| echo "✅ sandbox gone"
test -d "${USER_HOME}"             && echo "❌ home remains"   || echo "✅ home gone"

set -e
```

---

## Lab 29b Checklist (2 tasks + closeout)

- [ ] Task 1 implemented boundary-safe `mandb -c` automation pattern(s)
- [ ] Task 2 registered mandb output and asserted `apropos` returns >0
- [ ] Section 18 boundary note preserved; b-lab retained for trap practice
- [ ] Section 6 closeout ended with four `✅` audit lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
