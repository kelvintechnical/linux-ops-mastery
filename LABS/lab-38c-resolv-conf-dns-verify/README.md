# Lab 38c: Verifying DNS Server Configuration (Capstone) — audit + destroy-restore

- **Series:** linux-ops-mastery — Networking and Name Resolution
- **Trilogy:** [`38a`](../lab-38a-resolv-conf-dns-rhcsa/) (RHCSA) → [`38b`](../lab-38b-resolv-conf-dns-ansible/) (Ansible) → **`38c`** (Verify capstone)
- **Time Estimate:** 30-45 minutes
- **Tasks:** 2 (Task 1 = audit DNS state and journal artifacts · Task 2 = destroy-restore by deleting `lab38test` and restoring `/etc/resolv.conf` from backup)
- **Practice Directory (rotation #38):** `/lib`
- **Sandbox (Tier B):** `/tmp/lab38c` with `USER=labuser_38_resolv`, `GROUP=labgrp_38_resolv`, `USER_HOME=/tmp/lab38c/home_labuser_38_resolv`
- **Test Connection:** `lab38test` only
- **Traps rehearsed:** **T38-A** · **T38-B** · **T41** · **T44**

> **Capstone focus:** verify evidence quality, then restore baseline state so no resolver/test-profile residue leaks into later labs.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T38-A T38-B T41 T44"
echo "📁  PRACTICE DIR: /lib"
ls -ld /lib /etc
ls -la /root/rhcsa_journal/lab-38a /root/rhcsa_journal/lab-38b 2>/dev/null || true
nmcli con show | head -n 12
```

> **STOP — paste header output. If 38a/38b journals are missing, complete those first.**

---

## Objective

1. Audit DNS configuration evidence from prior labs plus live resolver state.
2. Validate trap coverage signals (T38-A, T38-B, T41, T44) in artifacts.
3. Execute destroy-restore drill: remove test connection and restore resolver baseline.

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=38
export LAB_SLUG=resolv
export SANDBOX=/tmp/lab38c
export GROUP=labgrp_38_resolv
export USER=labuser_38_resolv
export USER_HOME=${SANDBOX}/home_${USER}
export CON_NAME=lab38test

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-38c/task1 /root/rhcsa_journal/lab-38c/task2
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

# Mandatory backup before verify drills.
cp /etc/resolv.conf /tmp/lab38c/resolv.bak

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /lib
```

---

## Task 1 — Audit DNS state in journal and current host

### Purpose

Confirm prior labs produced required DNS artifacts and current resolver state is inspectable/auditable.

### Main command block

```bash
TASKLOG=/tmp/lab38c/task1.txt

echo "═══ Part A: required journal files present ═══"                    2>&1 | tee "$TASKLOG"
REQUIRED=(
  /root/rhcsa_journal/lab-38a/task1/evidence.txt
  /root/rhcsa_journal/lab-38a/task2/evidence.txt
  /root/rhcsa_journal/lab-38b/task1/evidence.txt
  /root/rhcsa_journal/lab-38b/task2/evidence.txt
)
MISSING=0
for f in "${REQUIRED[@]}"; do
  if test -s "$f"; then
    echo "✅ $f"
  else
    echo "❌ missing/empty: $f"
    MISSING=$((MISSING+1))
  fi
done | tee -a "$TASKLOG"
echo "missing_count=${MISSING}" | tee -a "$TASKLOG"

echo "═══ Part B: live DNS state audit ═══"                              | tee -a "$TASKLOG"
ls -l /etc/resolv.conf                                                   | tee -a "$TASKLOG"
grep -E '^(nameserver|search)' /etc/resolv.conf                          | tee -a "$TASKLOG"
nmcli -f NAME,DEVICE,IP4.DNS,IP4.DOMAIN,IPV4.METHOD con show lab38test 2>&1 | tee -a "$TASKLOG" || true

echo "═══ Part C: Tier B as-user resolver capture ═══"                   | tee -a "$TASKLOG"
sudo -u "${USER}" bash -c "grep -E '^(nameserver|search)' /etc/resolv.conf > '${USER_HOME}/dns-audit-asuser.txt'"
stat -c '%U:%G %a %n' "${USER_HOME}/dns-audit-asuser.txt"                | tee -a "$TASKLOG"
wc -l "${USER_HOME}/dns-audit-asuser.txt"                                | tee -a "$TASKLOG"

echo "exit was: $?"                                                      | tee -a "$TASKLOG"
```

### Concept Card

| Concept | What it does |
|---|---|
| Journal artifact audit | Verifies prior tasks were completed and persisted |
| Resolver live grep | Captures effective DNS/search runtime lines |
| NM connection field audit | Confirms profile-level DNS intent |
| **🪤 Trap Risk T44** | Skipping verification/cleanup leaves hidden state drift |

### Journal write

```bash
LAB=lab-38c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab38c/task1.txt "$JDIR/evidence.txt"
cp "${USER_HOME}/dns-audit-asuser.txt" "$JDIR/dns-audit-asuser.txt"
```

---

## Task 2 — Destroy-restore drill: delete test connection, restore resolver backup

### Purpose

Practice the T41/T44 teardown reflex: intentionally remove test profile state and return `/etc/resolv.conf` to backup baseline.

### Main command block

```bash
TASKLOG=/tmp/lab38c/task2.txt

echo "═══ Part A: baseline snapshot before destroy ═══"                  2>&1 | tee "$TASKLOG"
nmcli con show | grep -w lab38test                                       | tee -a "$TASKLOG" || echo "(lab38test not present before delete)" | tee -a "$TASKLOG"
grep -E '^(nameserver|search)' /etc/resolv.conf                          | tee -a "$TASKLOG"

echo "═══ Part B: destroy test profile ═══"                              | tee -a "$TASKLOG"
nmcli con delete lab38test                                                2>&1 | tee -a "$TASKLOG" || true
nmcli con show | grep -w lab38test                                        | tee -a "$TASKLOG" && echo "❌ still present" | tee -a "$TASKLOG" || echo "✅ lab38test removed" | tee -a "$TASKLOG"

echo "═══ Part C: restore /etc/resolv.conf from backup ═══"              | tee -a "$TASKLOG"
cp /tmp/lab38c/resolv.bak /etc/resolv.conf                                2>&1 | tee -a "$TASKLOG"
cat /etc/resolv.conf | tee /tmp/lab38c/resolv.restored                    2>&1 | tee -a "$TASKLOG"

echo "═══ Part D: post-restore proof ═══"                                | tee -a "$TASKLOG"
cmp -s /tmp/lab38c/resolv.bak /etc/resolv.conf \
  && echo "✅ restore matches backup byte-for-byte" \
  || echo "❌ restore mismatch"                                            | tee -a "$TASKLOG"

echo "exit was: $?"                                                       | tee -a "$TASKLOG"
```

### Concept Card

| Concept | What it does |
|---|---|
| `nmcli con delete lab38test` | Removes test-only profile residue |
| Backup restore (`cp resolv.bak`) | Returns resolver file to known baseline |
| `cmp -s` | Deterministic equality check of restored file |
| **🪤 Trap Risk T41** | If you never run destroy-restore, you cannot trust recovery readiness |
| **🪤 Trap Risk T38-A** | Reconnect-based overwrites are avoided by cleaning test profile state |

### Journal write

```bash
LAB=lab-38c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab38c/task2.txt "$JDIR/evidence.txt"
cp /tmp/lab38c/resolv.bak "$JDIR/resolv.bak"
cp /tmp/lab38c/resolv.restored "$JDIR/resolv.restored"

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

test -f /tmp/lab38c/resolv.bak && cp /tmp/lab38c/resolv.bak /etc/resolv.conf
nmcli con delete lab38test 2>/dev/null || true

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 38c cleanup audit ──"
nmcli con show | grep -w lab38test >/dev/null && echo "❌ connection remains" || echo "✅ connection gone"
test -f /etc/resolv.conf && echo "✅ resolv.conf present" || echo "❌ resolv.conf missing"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"

set -e
```

---

## Lab 38c Checklist (2 tasks + closeout)

- [ ] Task 1 audited journal artifacts and current DNS state (`resolv.conf` + NM fields)
- [ ] Task 2 deleted `lab38test` and restored `/etc/resolv.conf` from backup
- [ ] T38-A/T38-B/T41/T44 evidence and cleanup signals were captured
- [ ] Section 6 closeout ended with cleanup audit checks

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
