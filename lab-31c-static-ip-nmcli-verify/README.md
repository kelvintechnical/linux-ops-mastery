# Lab 31c: Configure a Static IP Address (Verify Capstone)

- **Series:** linux-ops-mastery
- **Trilogy:** `31a` (RHCSA) -> `31b` (Ansible) -> `31c` (Verify)
- **Practice Directory:** `/run`
- **Tier B Sandbox:** `/tmp/lab31c`
- **Lab User/Group:** `labuser_31_staticip` / `labgrp_31_staticip`
- **Test Connection:** `lab31test` only (do not touch management interface)
- **Traps rehearsed:** `T31-A`, `T31-B`, `T41`, `T44`

This lab's practice directory is: `/run`

---

## LAB HEADER

```bash
echo "TIME: $(date -Is)"
echo "USER: $(whoami)@$(hostname)"
echo "PRACTICE DIR: /run"
echo "VERIFY TARGET: lab31test journal + restore drill"
nmcli con show | tee /tmp/lab31c_header_connections.txt
find /root/rhcsa_journal -maxdepth 2 -type d -name 'lab-31*' | sort
echo "TRAPS: T31-A T31-B T41 T44"
echo "exit was: $?"
```

> STOP and confirm header output before continuing.

---

## Lab-Wide Tier B Setup (run before Task 1)

```bash
sudo -i
export LAB_NUM=31
export LAB_SLUG=staticip
export SANDBOX=/tmp/lab31c
export GROUP=labgrp_31_staticip
export USER=labuser_31_staticip
export USER_HOME=${SANDBOX}/home_${USER}
export CON_NAME=lab31test

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-31c/task1 /root/rhcsa_journal/lab-31c/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
/run holds runtime data that is rebuilt each boot. Verification labs use it
to reinforce "active now" versus "persistent config" thinking.
EOF

id "${USER}"
ls -ld /run "${SANDBOX}" "${USER_HOME}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 - Audit Lab 31a/31b journal artifacts

Practice directory this task: `/run`

### Warm-Up

```bash
ls -ld /run /root/rhcsa_journal
find /root/rhcsa_journal -maxdepth 2 -type d -name 'lab-31*' | sort
nmcli con show | head -n 10
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### WEAVE TRACE

- `find /root/rhcsa_journal...` -> drives which artifacts must be audited.
- `nmcli con show` -> compares journal intent to current state.
- `ls -ld /run` -> confirms runtime context for evidence output.

### Purpose

Audit evidence from `31a` and `31b` and confirm expected files exist and contain key signals (static fields, check/diff outputs, and teardown evidence).

### Main Block

```bash
export SANDBOX=/tmp/lab31c
export JROOT=/root/rhcsa_journal

{
  echo "=== LAB31 JOURNAL AUDIT ==="
  find "${JROOT}" -maxdepth 3 -type f \( -name done.txt -o -name notes.txt -o -name '*.txt' \) | sort
  echo "--- 31a done files ---"
  find "${JROOT}/lab-31a" -name done.txt -print 2>/dev/null
  echo "--- 31b done files ---"
  find "${JROOT}/lab-31b" -name done.txt -print 2>/dev/null
  echo "--- grep static indicators ---"
  rg -n "lab31test|IP4.ADDRESS|changed=0|con delete" "${JROOT}/lab-31a" "${JROOT}/lab-31b" 2>/dev/null || true
  echo "--- current nm state ---"
  nmcli con show | grep -w lab31test || echo "lab31test currently absent"
} 2>&1 | tee "${SANDBOX}/task1.txt"

sudo -u "${USER}" bash -c 'echo "Task1 audit signed by $(whoami) at $(date -Is)" >> /tmp/lab31c/task1-reviewed-by-user.txt'
stat -c '%U:%G %a %n' /tmp/lab31c/task1-reviewed-by-user.txt | tee -a "${SANDBOX}/task1.txt"
echo "exit was: $?"
```

### Breakdown

- enumerates journal artifacts from previous trilogy labs.
- scans for key proof markers (`lab31test`, `changed=0`, `con delete`).
- compares persisted notes with current `nmcli` connection state.

### L->R

`rg -n "lab31test|IP4.ADDRESS|changed=0|con delete" ...`

- `rg` fast recursive search
- `-n` include line numbers in results
- regex pattern lists mandatory proof markers
- paths scope search to `lab-31a` and `lab-31b`

### Story

Verification discipline closes the loop between "I ran commands" and "I can prove state, evidence, and cleanup." This is the operator reflex graders reward.

### Expected Output

- path list of `done.txt`/`notes.txt`/evidence files.
- marker hits for static IP and idempotence.
- current `nmcli` state line or explicit absence message.

### Switches

| Token | Meaning |
|---|---|
| `find -maxdepth` | limit traversal depth |
| `-name` | filename filter |
| `rg -n` | content search with line numbers |
| `grep -w` | exact connection-name match |

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | artifact audit | validates previous lab execution evidence |
| ✅ | marker grep/rg scan | confirms critical proof strings exist |
| ✅ | state-vs-evidence compare | catches drift between logs and live host |
| 🪤 Trap Risk | `T41`: skipping persistence verification | always audit both journal files and live `nmcli` state |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| prior tasks recorded | `find /root/rhcsa_journal/lab-31{a,b} -name done.txt` | proves checkpoints persisted |
| static fields evidenced | `rg "IP4.ADDRESS|ipv4.method|manual" /root/rhcsa_journal/lab-31b` | confirms static config intent |
| cleanup intent evidenced | `rg "con delete|cleanup audit" /root/rhcsa_journal/lab-31a` | confirms teardown discipline |

### Journal Write

```bash
LAB=lab-31c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab31c/task1.txt "${JDIR}/evidence.txt"
cat > "${JDIR}/done.txt" <<EOF
LAB: ${LAB}
TASK: ${TASK}
DATE: $(date -Is)
USER: $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "${JDIR}/notes.txt" <<EOF
TOPIC: audit of lab-31a/lab-31b evidence and live state
COMMANDS: find, rg, nmcli con show, grep -w
TRAPS: T41 rehearsed
NEXT: task2 destroy-restore drill
EOF
ls -la "${JDIR}"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab31c/task1-reviewed-by-user.txt
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| missing journal paths | rerun previous labs or reconstruct expected artifacts |
| no marker matches | inspect notes/evidence and update capture commands |
| `rg` not found | install ripgrep or fallback to `grep -R` manually |

### STOP

Stop and paste Task 1 output before moving on.

---

## Task 2 - Destroy and restore `lab31test` from playbook

Practice directory this task: `/run`

### Warm-Up

```bash
nmcli con show | grep -w lab31test || true
ls -l /root/rhcsa_journal/lab-31b/playbooks/task1.yml
ip addr show lo
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### WEAVE TRACE

- `nmcli con show` -> baseline before forced delete and restore.
- `ls -l task1.yml` -> validates restore source exists.
- `ip addr show lo` -> runtime proof after restore.

### Purpose

Run a controlled destroy-restore drill: delete the connection, restore it from `31b` playbook, and verify static fields plus active state.

### Main Block

```bash
export SANDBOX=/tmp/lab31c
export CON_NAME=lab31test
export RESTORE_PLAY=/root/rhcsa_journal/lab-31b/playbooks/task1.yml

nmcli con delete "${CON_NAME}" 2>&1 | tee "${SANDBOX}/task2.txt" || true
nmcli con show | grep -w "${CON_NAME}" 2>&1 | tee -a "${SANDBOX}/task2.txt" || true

ansible-playbook --check --diff "${RESTORE_PLAY}" 2>&1 | tee -a "${SANDBOX}/task2.txt"
ansible-playbook "${RESTORE_PLAY}"                 2>&1 | tee -a "${SANDBOX}/task2.txt"

nmcli -f NAME,IPV4.METHOD,IP4.ADDRESS,IP4.GATEWAY,IP4.DNS con show "${CON_NAME}" \
    2>&1 | tee -a "${SANDBOX}/task2.txt"
ip addr show lo   2>&1 | tee -a "${SANDBOX}/task2.txt"
ip route show     2>&1 | tee -a "${SANDBOX}/task2.txt"

sudo -u "${USER}" bash -c 'echo "Task2 destroy-restore signed at $(date -Is)" >> /tmp/lab31c/task2-reviewed-by-user.txt'
stat -c '%U:%G %a %n' /tmp/lab31c/task2-reviewed-by-user.txt | tee -a "${SANDBOX}/task2.txt"
echo "exit was: $?"
```

### Breakdown

- deletes profile first to simulate outage/recovery.
- replays tested playbook artifact to restore desired state.
- validates both profile metadata and runtime network view.

### L->R

`ansible-playbook /root/rhcsa_journal/lab-31b/playbooks/task1.yml`

- `ansible-playbook` apply automation artifact
- absolute path guarantees correct source
- same playbook reuses idempotent desired-state logic

### Story

Recovery drills prove operational resilience. Knowing configuration commands is not enough; you must restore known-good state quickly from versioned artifacts.

### Expected Output

- `lab31test` absent immediately after delete.
- playbook recreate and activation output.
- post-restore `nmcli con show` lists manual static IPv4 fields.

### Switches

| Token | Meaning |
|---|---|
| `con delete` | removes profile before drill |
| `--check --diff` | preview restoration effects |
| `-f` in `nmcli` | focused verification fields |
| `grep -w` | exact profile-name confirmation |

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | destroy-restore cycle | validates recoverability |
| ✅ | playbook reuse | ensures reliable reconstruction |
| ✅ | runtime plus persistent checks | catches activation gaps |
| 🪤 Trap Risk | `T44`: leaving restored artifacts dirty | always finish with Section 6 teardown audit |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| profile restored | `nmcli con show lab31test` | proves persistent profile recreation |
| active after restore | `ip addr show lo` and `nmcli con up lab31test` | confirms runtime activation |
| restore source persisted | `ls -l /root/rhcsa_journal/lab-31b/playbooks/task1.yml` | ensures repeatable recovery artifact |

### Journal Write

```bash
LAB=lab-31c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab31c/task2.txt "${JDIR}/evidence.txt"
cat > "${JDIR}/done.txt" <<EOF
LAB: ${LAB}
TASK: ${TASK}
DATE: $(date -Is)
USER: $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "${JDIR}/notes.txt" <<EOF
TOPIC: destroy-restore static profile from prior playbook
COMMANDS: nmcli con delete, ansible-playbook, nmcli con show, ip addr, ip route
TRAPS: T44 rehearsed
NEXT: trilogy complete
EOF
ls -la "${JDIR}"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab31c/task2-reviewed-by-user.txt
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| restore playbook missing | regenerate from lab-31b task1 instructions |
| profile restores but no runtime effect | run `nmcli con up lab31test` and re-check |
| delete command errors on absent profile | acceptable in drill; continue to restore step |

### STOP

Stop and paste Task 2 output before final closeout.

---

## Section 6 Closeout (after Task 2)

```bash
set +e
export SANDBOX=/tmp/lab31c
export GROUP=labgrp_31_staticip
export USER=labuser_31_staticip
export CON_NAME=lab31test

nmcli con delete "${CON_NAME}" 2>/dev/null || true
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
nmcli con show | grep -w "${CON_NAME}" >/dev/null && echo "❌ connection remains" || echo "✅ connection gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Author

Kelvin R. Tobias
