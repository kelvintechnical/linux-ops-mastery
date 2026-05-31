# Lab 35c: Verifying Text-Based Network Config (Capstone) — hostname audit + destroy-restore

- **Series:** linux-ops-mastery — NetworkManager and Host Identity
- **Trilogy:** [`35a`](../lab-35a-nmtui-tui-config-rhcsa/) (RHCSA TUI/CLI parity) → [`35b`](../lab-35b-nmtui-tui-config-ansible/) (Ansible boundary replacement) → **`35c`** (verify capstone)
- **Time Estimate:** 30-45 minutes
- **Tasks:** 2 (Task 1 = audit hostname state evidence in journal and runtime; Task 2 = destroy-restore drill restoring original hostname from journal)
- **Practice Directory (rotation #35):** `/tmp`
- **Sandbox (Tier B):** `/tmp/lab35c` with `USER=labuser_35_nmtui`, `GROUP=labgrp_35_nmtui`, `USER_HOME=/tmp/lab35c/home_labuser_35_nmtui`
- **Traps rehearsed:** **T35-A** · **T35-B** · **T41** · **T44**

> **Capstone focus:** verify that hostname changes were both recorded and recoverable, not just applied once.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T35-A T35-B T41 T44"
echo "📁  PRACTICE DIR: /tmp"
ls -ld /tmp
ls -la /root/rhcsa_journal/lab-35a /root/rhcsa_journal/lab-35b 2>/dev/null || true
hostnamectl status --static
```

> **STOP — paste header output. If `lab-35a`/`lab-35b` journal evidence is missing, complete them first.**

---

## Objective

1. Audit persistent hostname evidence from journal artifacts and system logs.
2. Rehearse T41 via explicit destroy-restore hostname flow.
3. Restore original hostname from journal, then prove success.

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=35
export LAB_SLUG=nmtui
export SANDBOX=/tmp/lab35c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-35c/task1 /root/rhcsa_journal/lab-35c/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

# Prefer 35a source of truth, fall back to current static hostname if absent.
if test -s /root/rhcsa_journal/lab-35a/task1/original-hostname.txt; then
  cp /root/rhcsa_journal/lab-35a/task1/original-hostname.txt /tmp/lab35c/original-hostname.txt
else
  hostnamectl --static > /tmp/lab35c/original-hostname.txt
fi

id "${USER}"
cat /tmp/lab35c/original-hostname.txt
```

---

## Task 1 — Audit hostname state in journal and logs

### Purpose

Validate that hostname transitions are traceable through both journal artifacts and system log records.

### Main command block

```bash
TASKLOG=/tmp/lab35c/task1.txt

echo "═══ Part A: journal artifact audit ═══"                          2>&1 | tee "$TASKLOG"
REQ=(
  /root/rhcsa_journal/lab-35a/task1/evidence.txt
  /root/rhcsa_journal/lab-35a/task1/original-hostname.txt
  /root/rhcsa_journal/lab-35b/task2/task2-assertions.txt
)
MISS=0
for f in "${REQ[@]}"; do
  if test -s "$f"; then
    echo "✅ $f"
  else
    echo "❌ missing/empty: $f"
    MISS=$((MISS+1))
  fi
done | tee -a "$TASKLOG"
echo "missing_count=${MISS}" | tee -a "$TASKLOG"

echo "═══ Part B: runtime hostname checks ═══"                         | tee -a "$TASKLOG"
hostnamectl --static                                                   | tee -a "$TASKLOG"
hostname                                                               | tee -a "$TASKLOG"
cat /etc/hostname                                                      | tee -a "$TASKLOG"

echo "═══ Part C: audit hostname events in journalctl ═══"             | tee -a "$TASKLOG"
journalctl -b --no-pager | grep -Ei 'hostname|hostnamed|NetworkManager' | tail -n 30 | tee -a "$TASKLOG"

echo "═══ Part D: Tier B user-context capture ═══"                     | tee -a "$TASKLOG"
sudo -u "${USER}" bash -c "hostnamectl --static > '${USER_HOME}/hostname-audit-asuser.txt'"
stat -c '%U:%G %a %n' "${USER_HOME}/hostname-audit-asuser.txt"         | tee -a "$TASKLOG"
cat "${USER_HOME}/hostname-audit-asuser.txt"                           | tee -a "$TASKLOG"

echo "exit was: $?"                                                    | tee -a "$TASKLOG"
```

### Journal write

```bash
LAB=lab-35c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab35c/task1.txt "$JDIR/evidence.txt"
cp "${USER_HOME}/hostname-audit-asuser.txt" "$JDIR/hostname-audit-asuser.txt"
```

---

## Task 2 — Destroy-restore drill: restore original hostname from journal

### Purpose

Rehearse recovery muscle: intentionally set a throwaway hostname, then restore the original from the journal artifact.

### Main command block

```bash
TASKLOG=/tmp/lab35c/task2.txt
ORIG_HOST="$(cat /tmp/lab35c/original-hostname.txt)"
DRIFT_HOST="lab35c-drifted"

echo "═══ Part A: baseline before destroy ═══"                          2>&1 | tee "$TASKLOG"
echo "original_hostname=${ORIG_HOST}"                                   | tee -a "$TASKLOG"
hostnamectl --static                                                    | tee -a "$TASKLOG"

echo "═══ Part B: destroy (intentional drift) ═══"                      | tee -a "$TASKLOG"
hostnamectl set-hostname "${DRIFT_HOST}"
hostnamectl --static                                                    | tee -a "$TASKLOG"
hostname                                                                | tee -a "$TASKLOG"

echo "═══ Part C: restore from journal source of truth ═══"             | tee -a "$TASKLOG"
hostnamectl set-hostname "${ORIG_HOST}"
hostnamectl --static                                                    | tee -a "$TASKLOG"
hostname                                                                | tee -a "$TASKLOG"

echo "═══ Part D: assert restore success ═══"                           | tee -a "$TASKLOG"
CUR_HOST="$(hostnamectl --static)"
test "${CUR_HOST}" = "${ORIG_HOST}" \
  && echo "✅ restore succeeded from journal value" \
  || echo "❌ restore mismatch: expected=${ORIG_HOST} got=${CUR_HOST}"  | tee -a "$TASKLOG"

echo "exit was: $?"                                                     | tee -a "$TASKLOG"
```

### Trap card

| Trap | Proof in this task |
|---|---|
| **T41** | Destroy-restore was executed, not skipped |
| **T35-B** | Permanent hostname restoration verified with `hostnamectl --static` |
| **T44** | Audit artifacts written before teardown |

### Journal write

```bash
LAB=lab-35c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab35c/task2.txt "$JDIR/evidence.txt"
cp /tmp/lab35c/original-hostname.txt "$JDIR/original-hostname.txt"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

ORIG_HOST="$(cat /tmp/lab35c/original-hostname.txt 2>/dev/null)"
test -n "${ORIG_HOST}" && hostnamectl set-hostname "${ORIG_HOST}"

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 35c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"   || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}"               && echo "❌ sandbox remains"|| echo "✅ sandbox gone"
test -d "${USER_HOME}"             && echo "❌ home remains"   || echo "✅ home gone"

set -e
```

---

## Lab 35c Checklist (2 tasks + closeout)

- [ ] Task 1 audited hostname state from journal files and `journalctl`
- [ ] Task 2 completed destroy-restore using original hostname from journal
- [ ] T41 and T44 evidence captured in journal
- [ ] Section 6 closeout ended with four `✅` audit lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
