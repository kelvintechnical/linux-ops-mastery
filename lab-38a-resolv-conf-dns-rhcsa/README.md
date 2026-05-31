# Lab 38a: Configuring DNS Servers (RHCSA) — `/etc/resolv.conf`, `nameserver`, `search`, `nmcli ipv4.dns`

- **Series:** linux-ops-mastery — Networking and Name Resolution
- **Trilogy:** **`38a`** (RHCSA hand-typed) → [`38b`](../lab-38b-resolv-conf-dns-ansible/) (Ansible) → [`38c`](../lab-38c-resolv-conf-dns-verify/) (Verify capstone)
- **Time Estimate:** 30-45 minutes
- **Tasks:** 2 (Task 1 = configure DNS via `nmcli` on `lab38test` and observe `/etc/resolv.conf` regeneration · Task 2 = trigger T38-A by manual edit and prove overwrite on reconnect)
- **Practice Directory (rotation #38):** `/lib`
- **Sandbox (Tier B):** `/tmp/lab38a` with `USER=labuser_38_resolv`, `GROUP=labgrp_38_resolv`, `USER_HOME=/tmp/lab38a/home_labuser_38_resolv`
- **Test Connection:** `lab38test` only (do not touch production connection profiles)
- **Traps rehearsed:** **T38-A** (NetworkManager rewrites `/etc/resolv.conf` on connection up) · **T38-B** (only first 3 `nameserver` lines are used; extras ignored) · **T41** · **T44**

> **Focus:** make DNS changes in the profile, not in a volatile file that NetworkManager regenerates.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T38-A T38-B T41 T44"
echo "📁  PRACTICE DIR: /lib"
ls -ld /lib /etc
nmcli --version
nmcli con show | head -n 12
ls -l /etc/resolv.conf
```

> **STOP — paste header output before setup.**

---

## Objective

1. Configure DNS servers declaratively in NetworkManager with `nmcli con mod ... ipv4.dns`.
2. Watch `/etc/resolv.conf` regenerate when the connection comes up.
3. Prove why direct edits are fragile when NM manages resolver state (T38-A).
4. Recognize and avoid overloading `nameserver` entries past the effective limit (T38-B).

---

## Concept: NM-Managed vs Static `/etc/resolv.conf`

- **NM-managed mode (default on modern RHEL/Fedora):** `/etc/resolv.conf` is a generated file (or symlink target) updated from active connection profile fields.
- **Static mode (boundary/edge case):** admins intentionally break management linkage and freeze the file (`rm` symlink + plain file + `chattr +i`) when they want manual-only control.
- **Rule:** if NM owns resolver state, set DNS in connection profile (`ipv4.dns`, `ipv4.dns-search`) and reactivate.

Static pattern (explanation only; do not run in Task 1 unless explicitly testing boundary behavior):

```bash
# Boundary pattern: force static resolv.conf (manual management mode)
rm -f /etc/resolv.conf
cat > /etc/resolv.conf <<'EOF'
nameserver 1.1.1.1
search lab38.local
EOF
chattr +i /etc/resolv.conf
```

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=38
export LAB_SLUG=resolv
export SANDBOX=/tmp/lab38a
export GROUP=labgrp_38_resolv
export USER=labuser_38_resolv
export USER_HOME=${SANDBOX}/home_${USER}
export CON_NAME=lab38test

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-38a/task1 /root/rhcsa_journal/lab-38a/task2
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

# Ensure a dedicated safe profile exists for this lab.
nmcli con show "${CON_NAME}" >/dev/null 2>&1 || nmcli con add type ethernet ifname lo con-name "${CON_NAME}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /lib
nmcli con show "${CON_NAME}"
```

---

## Task 1 — Configure DNS using `lab38test` and observe regeneration

### Purpose

Perform the exact RHCSA-safe sequence:

1. backup `/etc/resolv.conf`
2. configure DNS in the test profile
3. reactivate profile
4. verify regenerated resolver file

### Main command block

```bash
TASKLOG=/tmp/lab38a/task1.txt

echo "═══ Part A: required command sequence ═══"                         2>&1 | tee "$TASKLOG"
cp /etc/resolv.conf /tmp/lab38a/resolv.bak                               2>&1 | tee -a "$TASKLOG"
nmcli con mod lab38test ipv4.dns '1.1.1.1 8.8.8.8'                       2>&1 | tee -a "$TASKLOG"
nmcli con mod lab38test ipv4.dns-search 'lab38.local example.internal'   2>&1 | tee -a "$TASKLOG"
nmcli con up lab38test                                                    2>&1 | tee -a "$TASKLOG"
cat /etc/resolv.conf | tee /tmp/lab38a/resolv.after-task1                2>&1 | tee -a "$TASKLOG"

echo "═══ Part B: nameserver cap rehearsal (T38-B) ═══"                 | tee -a "$TASKLOG"
nmcli con mod lab38test ipv4.dns '1.1.1.1 8.8.8.8 9.9.9.9 208.67.222.222' 2>&1 | tee -a "$TASKLOG"
nmcli con up lab38test                                                    2>&1 | tee -a "$TASKLOG"
grep -E '^(nameserver|search)' /etc/resolv.conf                           | tee -a "$TASKLOG"
echo "Note: resolv.conf effectively uses max 3 nameserver lines."        | tee -a "$TASKLOG"

echo "═══ Part C: Tier B evidence write as lab user ═══"                 | tee -a "$TASKLOG"
sudo -u "${USER}" bash -c "grep -E '^(nameserver|search)' /etc/resolv.conf > '${USER_HOME}/dns-state-asuser.txt'"
stat -c '%U:%G %a %n' "${USER_HOME}/dns-state-asuser.txt"                 | tee -a "$TASKLOG"
wc -l "${USER_HOME}/dns-state-asuser.txt"                                 | tee -a "$TASKLOG"

echo "exit was: $?"                                                       | tee -a "$TASKLOG"
```

### Concept Card

| Concept | What it does |
|---|---|
| `nmcli con mod <name> ipv4.dns` | Persists DNS servers in the connection profile |
| `nmcli con mod <name> ipv4.dns-search` | Persists resolver search domain list |
| `nmcli con up <name>` | Re-applies profile and regenerates resolver file when NM-managed |
| `cp /etc/resolv.conf ...` | Mandatory backup before DNS experiments |
| **🪤 Trap Risk T38-B** | More than three `nameserver` lines leads to silently ignored extras |

### Journal write

```bash
LAB=lab-38a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cp /tmp/lab38a/task1.txt "$JDIR/evidence.txt"
cp /tmp/lab38a/resolv.bak "$JDIR/resolv.bak"
cp /tmp/lab38a/resolv.after-task1 "$JDIR/resolv.after-task1"
cp "${USER_HOME}/dns-state-asuser.txt" "$JDIR/dns-state-asuser.txt"
```

---

## Task 2 — Trigger T38-A: manual edit gets overwritten on reconnect

### Purpose

Prove that editing `/etc/resolv.conf` directly is not durable when NM controls resolver data.

### Main command block

```bash
TASKLOG=/tmp/lab38a/task2.txt

echo "═══ Part A: inject manual edit (expected to be overwritten) ═══"   2>&1 | tee "$TASKLOG"
cp /etc/resolv.conf /tmp/lab38a/resolv.pre-trap                           2>&1 | tee -a "$TASKLOG"
cat > /etc/resolv.conf <<'EOF'
# manual edit for T38-A demo
nameserver 4.4.4.4
search overwritten.local
EOF
cat /etc/resolv.conf                                                       | tee -a "$TASKLOG"

echo "═══ Part B: reactivate NM profile and observe overwrite ═══"        | tee -a "$TASKLOG"
nmcli con up lab38test                                                     2>&1 | tee -a "$TASKLOG"
cat /etc/resolv.conf | tee /tmp/lab38a/resolv.after-trap                  2>&1 | tee -a "$TASKLOG"
grep -E '4\.4\.4\.4|overwritten\.local' /etc/resolv.conf                   | tee -a "$TASKLOG" || echo "✅ T38-A proven: manual edit was replaced" | tee -a "$TASKLOG"

echo "═══ Part C: restore DNS baseline from backup ═══"                   | tee -a "$TASKLOG"
cp /tmp/lab38a/resolv.bak /etc/resolv.conf                                 2>&1 | tee -a "$TASKLOG"
cat /etc/resolv.conf                                                        | tee -a "$TASKLOG"

echo "exit was: $?"                                                         | tee -a "$TASKLOG"
```

### Concept Card

| Concept | What it does |
|---|---|
| Manual file edit | Works only until NM next regenerates resolver state |
| `nmcli con up lab38test` | Trigger that recreates managed resolver output |
| Backup restore | Ensures host returns to known baseline |
| **🪤 Trap Risk T38-A** | Direct edits in NM-managed mode are transient and overwritten |

### Journal write

```bash
LAB=lab-38a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cp /tmp/lab38a/task2.txt "$JDIR/evidence.txt"
cp /tmp/lab38a/resolv.pre-trap "$JDIR/resolv.pre-trap"
cp /tmp/lab38a/resolv.after-trap "$JDIR/resolv.after-trap"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# Always restore resolv.conf if backup exists.
test -f /tmp/lab38a/resolv.bak && cp /tmp/lab38a/resolv.bak /etc/resolv.conf

# Always clean test connection.
nmcli con delete lab38test 2>/dev/null || true

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 38a cleanup audit ──"
nmcli con show | grep -w lab38test >/dev/null && echo "❌ connection remains" || echo "✅ connection gone"
test -f /etc/resolv.conf && echo "✅ resolv.conf present" || echo "❌ resolv.conf missing"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"

set -e
```

---

## Lab 38a Checklist (2 tasks + closeout)

- [ ] Task 1 ran the exact DNS configure sequence on `lab38test` and captured regenerated `/etc/resolv.conf`
- [ ] Task 1 rehearsed T38-B by attempting >3 DNS servers and documenting effective cap
- [ ] Task 2 proved T38-A by manual edit overwrite after `nmcli con up`
- [ ] `/etc/resolv.conf` backup was restored and `lab38test` removed
- [ ] Section 6 closeout ended with cleanup audit checks

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
