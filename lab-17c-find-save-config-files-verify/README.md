# Lab 17c: Find and Save Config Files (Verify Capstone) — audit, destroy, restore

- **Series:** linux-ops-mastery — Verification reflex and persistence proof
- **Trilogy:** [`17a`](../lab-17a-find-save-config-files-rhcsa/) (RHCSA) → [`17b`](../lab-17b-find-save-config-files-ansible/) (Ansible) → `17c` (Verify)
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 audit 17a evidence · Task 2 destroy-restore and rerun as verify user)
- **Practice Directory (rotation #03):** `/lib`
- **Sandbox (Tier B):** `/tmp/lab17c`, `USER=labuser_17_findsave`, `GROUP=labgrp_17_findsave`, `USER_HOME=/tmp/lab17c/home_labuser_17_findsave`
- **Traps rehearsed:** **T14-A**, **T14-B**, **T41**, **T44**

> **This lab's practice directory is: `/lib`**. We use `/lib` references each task while auditing and re-verifying file-search evidence.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T14-A T14-B T41 T44"
echo "📁  PRACTICE DIR: /lib"
ls -ld /lib
```

---

## Objective

Take the auditor seat:

1. Validate the list produced in Lab 17a (count, path existence, ownership assumptions).
2. Run a destroy-restore drill and prove commands still work after cleanup/rebuild.
3. Re-run verification search as the Tier B user.

---

## Lab-Wide Setup — Tier B Sandbox Stack

```bash
sudo -i

export LAB_NUM=17
export LAB_SLUG=findsave
export SANDBOX=/tmp/lab17c
export GROUP=labgrp_17_findsave
export USER=labuser_17_findsave
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
/lib is the shared-library runtime path that lets essential binaries execute.
Even verification labs keep the rotation directory in scope to reinforce recall.
EOF

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /lib
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — Audit Lab 17a list: count, path validity, ownership

**Practice directory this task:** `/lib`.

### Warm-Up

```bash
ls -ld /lib
find /lib -maxdepth 1 -type f 2>/dev/null | head -n 3
echo "verify warmup $(date -Is)" | tee /tmp/lab17c/warmup1.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Audit the list generated in Lab 17a using RHCSA inspection commands only: line count, existence validation, and ownership checks on sampled paths.

### WEAVE TRACE

| Warm-up / setup command | Role inside Task 1 |
|---|---|
| `find ... | head` | Sampling approach reused for audited list |
| `tee` | Captures audit transcript |
| `ls -ld /lib` | Practice directory continuity |
| Tier B user/group | Used for verify-user rerun prep in next task |

### Main command block

```bash
LIST17A=/tmp/lab17a/root-owned-conf-from-root.txt
AUDIT1=/tmp/lab17c/task1-audit.log

test -f "${LIST17A}" || { echo "Missing ${LIST17A} from lab 17a"; exit 1; }

echo "line count:"                                      | tee "${AUDIT1}"
wc -l "${LIST17A}"                                     | tee -a "${AUDIT1}"

echo "first 20 entries:"                               | tee -a "${AUDIT1}"
head -n 20 "${LIST17A}"                                | tee -a "${AUDIT1}"

echo "validate first 20 paths exist:"                  | tee -a "${AUDIT1}"
head -n 20 "${LIST17A}" | while read -r p; do test -e "$p" && echo "OK $p" || echo "MISS $p"; done | tee -a "${AUDIT1}"

echo "ownership spot-check first 10 paths:"            | tee -a "${AUDIT1}"
head -n 10 "${LIST17A}" | xargs -r stat -c '%U:%G %n' 2>/dev/null | tee -a "${AUDIT1}"

ls -ld /lib                                            | tee -a "${AUDIT1}"
echo "exit was: $?"
```

### Human-Readable Breakdown

- `wc -l` measures captured inventory size.
- `test -e` confirms listed paths still exist.
- `stat -c '%U:%G %n'` samples ownership assumptions from 17a.
- No Ansible is used in this capstone audit task.

### Reading it left to right

```text
head -n 10 LIST | xargs -r stat -c '%U:%G %n' 2>/dev/null
│                │        │                    └─ hide transient stat errors
│                │        └─ print owner:group path
│                └─ run stat on each sampled path (skip if empty with -r)
└─ select sample set for audit
```

### The story

Creating a list is not enough. Auditors verify that list quality is real: entries exist, ownership matches expectation, and the data can survive handoff between labs.

### Expected output

```text
line count:
N /tmp/lab17a/root-owned-conf-from-root.txt
OK /etc/...
root:root /etc/...
```

### Switches

| Token | Meaning |
|---|---|
| `wc -l` | Line count |
| `head -n` | Sample first entries |
| `test -e` | Path existence check |
| `xargs -r` | Do not run target command when input is empty |
| `stat -c` | Structured metadata output |

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | Auditor sampling | Validate representative subset quickly |
| ✅ | Existence checks | Detect stale or broken list entries |
| ✅ | Ownership checks | Confirm root-owned expectation from 17a |
| ✅ | Evidence capture | Build reusable audit log |
| 🪤 Trap Risk | **T41:** skipping verification after build | Always run explicit audit commands |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| 17a list still present | `test -s /tmp/lab17a/root-owned-conf-from-root.txt` | Confirms carry-over artifact |
| Audit log saved | `test -s /tmp/lab17c/task1-audit.log` | Proof of verification actions |
| Sample paths valid | `rg "^OK " /tmp/lab17c/task1-audit.log` | Confirms list quality |

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-17c/task1
cp /tmp/lab17c/task1-audit.log /root/rhcsa_journal/lab-17c/task1/evidence.txt
echo "LAB: lab-17c TASK: task1 DATE: $(date -Is) STATUS: COMPLETE" > /root/rhcsa_journal/lab-17c/task1/done.txt
echo "TOPIC: audit 17a list count+existence+ownership" > /root/rhcsa_journal/lab-17c/task1/notes.txt
```

### 🧹 Cleanup

```bash
rm -f /tmp/lab17c/warmup1.txt
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Missing 17a list file | Re-run Lab 17a Task 2 before continuing |
| Many `MISS` rows | Source system changed; regenerate inventory |
| `stat` permission errors | Keep `2>/dev/null` for noisy paths |

> **STOP — paste `wc -l`, at least 3 `OK` rows, and ownership sample before Task 2.**

---

## Task 2 — Destroy-Restore drill + re-run find as verify user

**Practice directory this task:** `/lib`.

### Warm-Up

```bash
ls -ld /lib
find /lib -maxdepth 2 -type f -name '*.so*' 2>/dev/null | head -n 5
echo "destroy-restore warmup $(date -Is)" | tee /tmp/lab17c/warmup2.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Perform T44-style cleanup/rebuild rehearsal, then rerun the search as `${USER}` to prove the verification flow is repeatable after state reset.

### WEAVE TRACE

| Warm-up / setup command | Role inside Task 2 |
|---|---|
| `find /lib ...` | Keeps search muscle active before rerun |
| `tee` | Captures destroy/restore evidence |
| `sudo -u "${USER}"` | Required verify-user rerun |
| `/lib` check | Maintains rotation constraint |

### Main command block

```bash
LOG2=/tmp/lab17c/task2-drill.log
VERIFY_LIST=/tmp/lab17c/verify-user-find.txt

echo "destroy phase (local artifacts only)" | tee "${LOG2}"
rm -f /tmp/lab17c/rebuild.marker "${VERIFY_LIST}" 2>/dev/null || true
echo "destroy complete at $(date -Is)" | tee -a "${LOG2}"

echo "restore phase" | tee -a "${LOG2}"
mkdir -p /tmp/lab17c
echo "restored $(date -Is)" > /tmp/lab17c/rebuild.marker
stat -c '%U:%G %a %n' /tmp/lab17c/rebuild.marker | tee -a "${LOG2}"

echo "rerun find as verify user with stderr suppression" | tee -a "${LOG2}"
sudo -u "${USER}" bash -c "find /etc -type f -name '*.conf' 2>/dev/null > '${VERIFY_LIST}'"
wc -l "${VERIFY_LIST}" | tee -a "${LOG2}"
head -n 10 "${VERIFY_LIST}" | tee -a "${LOG2}"
stat -c '%U:%G %a %n' "${VERIFY_LIST}" | tee -a "${LOG2}"

ls -ld /lib | tee -a "${LOG2}"
echo "exit was: $?"
```

### Human-Readable Breakdown

- Destroy step removes only task-local artifacts (safe reset).
- Restore step recreates marker evidence and verifies metadata.
- Verify step re-runs canonical search as lab user with `2>/dev/null`.
- If this rerun works, the workflow is resilient and repeatable.

### Reading it left to right

```text
sudo -u "${USER}" bash -c "find /etc -type f -name '*.conf' 2>/dev/null > VERIFY_LIST"
│                 │       └─ executes the redirected find as verify user
│                 └─ launch subshell for proper redirection context
└─ switch identity for Tier B repetition
```

### The story

Verification that only works once is not verification. Operators must recover from cleanup, rerun quickly, and get consistent evidence. This drill closes the loop on T41/T44.

### Expected output

```text
destroy phase (local artifacts only)
restore phase
... /tmp/lab17c/rebuild.marker
N /tmp/lab17c/verify-user-find.txt
labuser_17_findsave:labgrp_17_findsave ...
```

### Switches

| Token | Meaning |
|---|---|
| `rm -f` | Remove file if present, no prompt |
| `|| true` | Keep teardown moving despite missing artifact |
| `sudo -u USER` | Run verify command as lab user |
| `2>/dev/null` | Suppress permission noise |
| `stat -c` | Confirm ownership and mode |

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | Destroy-restore drill | Proves recoverability after cleanup |
| ✅ | Verify-user rerun | Confirms non-root workflow still valid |
| ✅ | Deterministic evidence | `wc/head/stat` give repeatable checks |
| ✅ | Safe teardown style | Guarded cleanup avoids abort cascades |
| 🪤 Trap Risk | **T44:** skipping cleanup audit | Always prove environment is clean |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Rebuild marker exists | `test -f /tmp/lab17c/rebuild.marker` | Confirms restore phase executed |
| Verify-user list exists | `test -s /tmp/lab17c/verify-user-find.txt` | Confirms rerun succeeded |
| Ownership is lab user | `stat -c '%U:%G' /tmp/lab17c/verify-user-find.txt` | Proves command ran as `${USER}` |

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-17c/task2
cp /tmp/lab17c/task2-drill.log /root/rhcsa_journal/lab-17c/task2/evidence.txt
echo "LAB: lab-17c TASK: task2 DATE: $(date -Is) STATUS: COMPLETE" > /root/rhcsa_journal/lab-17c/task2/done.txt
echo "TOPIC: destroy-restore drill + rerun find as ${USER}" > /root/rhcsa_journal/lab-17c/task2/notes.txt
```

### 🧹 Cleanup (per-task; full teardown in closeout)

```bash
rm -f /tmp/lab17c/warmup2.txt
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Verify list owned by root | You forgot `sudo -u "${USER}"` |
| No results in rerun | Recheck pattern quoting `-name '*.conf'` |
| Drill fails halfway | Use guarded cleanup (`2>/dev/null || true`) |

> **STOP — paste rerun `wc -l`, `head`, and `stat` before closeout.**

---

## Section 6 Closeout — Bulletproof Teardown Audit

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

---

## Lab 17c Checklist

- [ ] Tier B setup complete with `/tmp/lab17c/THIS_DIRECTORY.txt`
- [ ] Task 1 audited 17a list count, existence, and ownership
- [ ] Task 2 completed destroy-restore and reran find as `${USER}`
- [ ] Section 6 closeout produced all ✅ audit lines

---

## Author

**Kelvin R. Tobias**
