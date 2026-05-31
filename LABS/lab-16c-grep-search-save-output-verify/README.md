# Lab 16c: Search for a String and Save Output (Verify) — Audit + Destroy/Restore

- **Series:** linux-ops-mastery — Search and Capture Verification
- **Trilogy:** [`16a`](../lab-16a-grep-search-save-output-rhcsa/) (RHCSA) → [`16b`](../lab-16b-grep-search-save-output-ansible/) (Ansible) → **`16c`** (Verify)
- **Tasks:** 2 (Task 1 = audit 16a evidence; Task 2 = destroy-restore from journal and verify as non-root user)
- **Practice Directory:** `/sbin`
- **Sandbox (Tier B):** `/tmp/lab16c`, `USER=labuser_16_grepsave`, `GROUP=labgrp_16_grepsave`
- **Traps rehearsed:** `T16-A` · `T16-B` · `T41` · `T44`

> **This lab's practice directory is: `/sbin`** — verification commands still target `/sbin` data while all temporary manipulation occurs in `/tmp/lab16c`.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T16-A T16-B T41 T44"
echo "📁  PRACTICE DIR: /sbin"
```

> **STOP — paste header output before setup.**

---

## Lab-Wide Setup — Tier B Sandbox Stack

```bash
sudo -i

export LAB_NUM=16
export LAB_SLUG=grepsave
export SANDBOX=/tmp/lab16c
export GROUP=labgrp_16_grepsave
export USER=labuser_16_grepsave
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-16c/task1
mkdir -p /root/rhcsa_journal/lab-16c/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
/sbin is the verification source path for this lab.
We inspect grep artifacts created in 16a/16b and re-run searches against /sbin after restore.
EOF

id "${USER}"
ls -ld /sbin "${SANDBOX}" "${USER_HOME}"
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste setup proof before Task 1.**

---

## Task 1 — Audit Lab 16a evidence (`grep -c`, ownership, regex correctness)

**Practice directory this task:** `/sbin` — regex validation compares stored evidence with a fresh `/sbin` query.

### Warm-Up

```bash
ls -ld /sbin
ls -1 /sbin 2>/dev/null | grep -E 'sh$|ctl$' | head -5
test -s /root/rhcsa_journal/lab-16a/task2/lab16a-regex.txt && echo "16a root evidence present"
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Audit that Lab 16a produced valid evidence: expected match lines exist, root-owned capture file is present, and regex output quality is consistent with `/sbin` source.

### WEAVE TRACE

| Warm-up / setup command | Role inside Task 1 |
|---|---|
| `ls -ld /sbin` | Confirms practice target before validation |
| `/sbin` regex sample | Baseline to compare against journal evidence |
| `test -s` journal path | Prevents auditing a missing artifact |
| `id "${USER}"` | Tier B identity used in ownership checks |

### Main Command Block

```bash
TASKLOG=/tmp/lab16c/task1.txt
E16A=/root/rhcsa_journal/lab-16a/task2/lab16a-regex.txt

test -s "${E16A}" || { echo "missing ${E16A}" | tee "${TASKLOG}"; false; }

sudo ls -l "${E16A}" | tee "${TASKLOG}"
sudo grep -cE 'sh$|ctl$' "${E16A}" | tee -a "${TASKLOG}"
sudo grep -n "captured by" "${E16A}" | tee -a "${TASKLOG}"

# compare with fresh source sample from /sbin
ls -1 /sbin 2>/dev/null | grep -E 'sh$|ctl$' | head -10 > /tmp/lab16c/fresh-sbin.txt
sudo grep -E 'sh$|ctl$' "${E16A}" | head -10 > /tmp/lab16c/evidence-sample.txt
diff -u /tmp/lab16c/fresh-sbin.txt /tmp/lab16c/evidence-sample.txt | tee -a "${TASKLOG}" || true

# Tier B ownership drill in verify lab
sudo -u "${USER}" bash -c 'echo "verify-owner-line" > '"${USER_HOME}"'/verify-owner.txt'
stat -c '%U:%G %a %n' "${USER_HOME}/verify-owner.txt" | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Human-Readable Breakdown

- `grep -cE` asserts the evidence still contains regex-selected lines.
- `grep -n "captured by"` validates footer audit line from 16a task2.
- `diff -u` compares sample of live `/sbin` matches to journal-copied evidence.
- Tier B write in verify lab prevents skill decay in user/group ownership mechanics.

### Reading It Left to Right

```text
sudo grep -cE 'sh$|ctl$' /root/rhcsa_journal/lab-16a/task2/lab16a-regex.txt
│    │       │             │
│    │       │             └─ audited evidence file
│    │       └─ count only
│    └─ extended regex
└─ run read as root for root-owned file
```

### The Story

Verification is not rerunning the old command blindly; it is proving that saved artifacts are real, complete, and attributable. This task turns capture files into auditable records instead of one-off terminal output.

### Expected Output

```text
-rw-r--r--. 1 root root ... /root/rhcsa_journal/lab-16a/task2/lab16a-regex.txt
<count>
<line>:captured by root at ...
labuser_16_grepsave:labgrp_16_grepsave 644 /tmp/lab16c/home_labuser_16_grepsave/verify-owner.txt
```

### Switches

| Token | Meaning |
|---|---|
| `grep -cE` | Count matches with extended regex |
| `grep -n` | Show matching line number |
| `diff -u` | Unified diff comparison |
| `sudo -u USER` | Write as verify user |
| `stat -c` | Ownership and mode report |

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | Evidence counting | Proves saved lines still present |
| ✅ | Ownership audit | Confirms root vs non-root write origin |
| ✅ | Source-vs-evidence diff | Detects drift or bad capture |
| ✅ | `/sbin` anchored validation | Keeps verify tied to practice path |
| 🪤 Trap Risk | What goes wrong | How to avoid |
| ⚠️ `T41` | Skipping reboot/persistence reasoning after verification | Always run persistence table checks and saved-evidence tests |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| 16a evidence exists | `test -s /root/rhcsa_journal/lab-16a/task2/lab16a-regex.txt` | Journal survives `/tmp` loss |
| Evidence contains expected regex lines | `sudo grep -cE 'sh$|ctl$' /root/rhcsa_journal/lab-16a/task2/lab16a-regex.txt` | Confirms saved signal |
| Tier B verify artifact ownership | `stat -c '%U:%G' "${USER_HOME}/verify-owner.txt"` | Confirms user/group discipline |

### Journal Write

```bash
LAB=lab-16c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cp /tmp/lab16c/task1.txt "$JDIR/evidence.txt"
cp /tmp/lab16c/fresh-sbin.txt "$JDIR/fresh-sbin.txt"
cp /tmp/lab16c/evidence-sample.txt "$JDIR/evidence-sample.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    audit 16a evidence count/ownership/regex quality
COMMANDS: grep -cE, grep -n, diff -u, stat -c
TRAPS:    T41 reinforced via persistence proof workflow
NEXT:     task2 destroy-restore from journal then re-verify
EOF

echo "Journal written: $(ls -la "$JDIR")"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab16c/task1.txt /tmp/lab16c/fresh-sbin.txt /tmp/lab16c/evidence-sample.txt
rm -f "${USER_HOME}/verify-owner.txt"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Evidence file missing | Re-run 16a Task 2 journal copy or recover from backup |
| Regex count is zero | Inspect evidence content and pattern anchors |
| Ownership unexpected | Recreate verify file using `sudo -u "${USER}"` |

> **STOP — paste audit proof before Task 2.**

---

## Task 2 — Destroy/Restore drill: wipe `/tmp`, restore from journal, verify as `${USER}`

**Practice directory this task:** `/sbin` — restored workflow re-runs grep against `/sbin` to validate recoverability.

### Warm-Up

```bash
ls -ld /sbin
test -s /root/rhcsa_journal/lab-16a/task2/lab16a-regex.txt && echo "journal source ready"
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Simulate accidental `/tmp` loss, restore key artifacts from journal, and re-run search as verify user to prove recovery and repeatability.

### WEAVE TRACE

| Warm-up / setup command | Role inside Task 2 |
|---|---|
| `ls -ld /sbin` | Confirms source path for post-restore search |
| `test -s journal source` | Ensures restore input exists before wipe |
| Tier B `${USER}` identity | Runs post-restore verify command as non-root |

### Main Command Block

```bash
TASKLOG=/tmp/lab16c/task2.txt
RESTORE_DIR=/tmp/lab16c/restore
SRC=/root/rhcsa_journal/lab-16a/task2/lab16a-regex.txt

# Destroy phase (simulate tmp loss)
rm -rf /tmp/lab16c/*
mkdir -p "${RESTORE_DIR}" "${USER_HOME}"
echo "destroy complete at $(date -Is)" | tee "${TASKLOG}"

# Restore phase
cp "${SRC}" "${RESTORE_DIR}/lab16a-regex-restored.txt"
ls -l "${RESTORE_DIR}/lab16a-regex-restored.txt" | tee -a "${TASKLOG}"

# Re-run search as verify user
chown -R "${USER}:${GROUP}" /tmp/lab16c
sudo -u "${USER}" bash -c "ls -1 /sbin 2>/dev/null | grep -E 'sh$|ctl$' | tee ${RESTORE_DIR}/verify-user-run.txt >/dev/null"

grep -cE 'sh$|ctl$' "${RESTORE_DIR}/verify-user-run.txt" | tee -a "${TASKLOG}"
grep -cE 'sh$|ctl$' "${RESTORE_DIR}/lab16a-regex-restored.txt" | tee -a "${TASKLOG}"
stat -c '%U:%G %a %n' "${RESTORE_DIR}/verify-user-run.txt" | tee -a "${TASKLOG}"
echo "exit was: $?"
```

### Human-Readable Breakdown

- `rm -rf /tmp/lab16c/*` is intentional local wipe for restore rehearsal.
- Restore copies evidence from persistent `/root/rhcsa_journal`.
- Post-restore grep runs as `${USER}` to verify non-root operability.
- Match counts compare restored reference vs newly generated run.

### Reading It Left to Right

```text
sudo -u "${USER}" bash -c "ls -1 /sbin | grep -E 'sh$|ctl$' | tee .../verify-user-run.txt"
│       │         │       │            │
│       │         │       │            └─ save user-run evidence
│       │         │       └─ regex filter
│       │         └─ list source from /sbin
│       └─ run whole pipeline as verify user
└─ privilege drop for realistic non-root validation
```

### The Story

Real operations fail when temporary data vanishes or nodes reboot. The recovery skill is to rebuild state from persistent journal evidence and prove behavior still works under intended runtime identity. This task rehearses that exact loop.

### Expected Output

```text
destroy complete at <timestamp>
-rw-r--r--. 1 root root ... /tmp/lab16c/restore/lab16a-regex-restored.txt
<count>
<count>
labuser_16_grepsave:labgrp_16_grepsave 644 /tmp/lab16c/restore/verify-user-run.txt
```

### Switches

| Token | Meaning |
|---|---|
| `rm -rf` | Recursive force delete (controlled sandbox only) |
| `grep -cE` | Count regex matches |
| `sudo -u USER` | Execute recovery verification as non-root |
| `tee` | Persist command output to restore evidence |
| `stat -c` | Verify ownership and mode |

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | Destroy/restore drill | Tests recovery from volatile path loss |
| ✅ | Journal-first restore | Rebuilds artifacts from persistent evidence |
| ✅ | User-context revalidation | Confirms workflow works beyond root shell |
| ✅ | Count comparison | Verifies restored and regenerated outputs align |
| 🪤 Trap Risk | What goes wrong | How to avoid |
| ⚠️ `T44` | Cleanup or restore leaves orphaned users/files impacting next lab | Run full closeout audit and fix every `❌` before completion |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Restored evidence file | `test -s /tmp/lab16c/restore/lab16a-regex-restored.txt` | Confirms journal recovery succeeded |
| User-run verify output | `test -s /tmp/lab16c/restore/verify-user-run.txt` | Confirms non-root execution path |
| Journal baseline still present | `test -s /root/rhcsa_journal/lab-16a/task2/lab16a-regex.txt` | Confirms persistent source unaffected by tmp wipe |

### Journal Write

```bash
LAB=lab-16c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cp /tmp/lab16c/task2.txt "$JDIR/evidence.txt"
cp /tmp/lab16c/restore/lab16a-regex-restored.txt "$JDIR/lab16a-regex-restored.txt"
cp /tmp/lab16c/restore/verify-user-run.txt "$JDIR/verify-user-run.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    destroy /tmp then restore from journal and re-verify as lab user
COMMANDS: rm -rf, cp, sudo -u ${USER}, grep -cE, stat -c
TRAPS:    T41 + T44 rehearsed via persistence and closeout discipline
NEXT:     proceed to next trilogy after closeout audit passes
EOF

echo "Journal written: $(ls -la "$JDIR")"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /tmp/lab16c/task2.txt
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Restore source missing | Rebuild from previous lab evidence before rerun |
| User-run file not created | Confirm `chown -R "${USER}:${GROUP}" /tmp/lab16c` before `sudo -u` |
| Counts diverge sharply | Review regex pattern consistency in both commands |

> **STOP — paste restore and verify-user evidence before Lab Closeout.**

---

## Lab Closeout — Section 6 Bulletproof Teardown

```bash
set +e

podman ps -aq --filter "name=^${CTR}$" 2>/dev/null | xargs -r podman rm -f >/dev/null 2>&1
awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null
if vgs "${VG}" >/dev/null 2>&1; then
    lvremove -fy "${VG}" 2>/dev/null
    vgremove -fy "${VG}" 2>/dev/null
    pvremove -ffy /dev/loop* 2>/dev/null
fi
losetup -j "${SANDBOX}/disk.img" 2>/dev/null | cut -d: -f1 | xargs -r losetup -d 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── cleanup audit ──"
getent passwd "${USER}" && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" && echo "❌ group remains" || echo "✅ group gone"
vgs "${VG}" 2>/dev/null && echo "❌ VG remains" || echo "✅ vg gone"
losetup -l | grep -q "${SANDBOX}" && echo "❌ loop remains" || echo "✅ loop gone"
podman ps -a --filter "name=^${CTR}$" --format '{{.Names}}' | grep -q . && echo "❌ ctr remains" || echo "✅ ctr gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste cleanup audit lines.**

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
