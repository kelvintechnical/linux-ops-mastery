# Lab 37c: Verifying Local Host Resolution (Capstone) — Audit + Destroy-Restore Drill

- **Series:** linux-ops-mastery — Networking Name Resolution Fundamentals
- **Trilogy:** [`37a`](../lab-37a-etc-hosts-resolution-rhcsa/) (RHCSA hand-typed) → [`37b`](../lab-37b-etc-hosts-resolution-ansible/) (Ansible) → **`37c`** (Verify capstone — you are here)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = audit `/etc/hosts` state against journal, Task 2 = destroy-restore drill)
- **Practice Directory (rotation #37):** `/sbin`
- **Sandbox (Tier B):** `/tmp/lab37c` with `USER=labuser_37_hosts`, `GROUP=labgrp_37_hosts`, `USER_HOME=/tmp/lab37c/home_labuser_37_hosts`
- **Traps rehearsed this lab:** **T37-A** (host-file edits without backup evidence) · **T37-B** (`hosts:` order not validated) · **T41** (skip destroy-restore drill) · **T44** (incomplete teardown)

> **This lab's practice directory is: `/sbin`** — verify mode still keeps command-path awareness while auditing host-resolution state.

---

## LAB HEADER BLOCK

```bash
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T37-A T37-B T41 T44"
echo "📁  PRACTICE DIR: /sbin"
ls -ld /sbin /etc/hosts /etc/nsswitch.conf
grep '^hosts:' /etc/nsswitch.conf
ls -la /root/rhcsa_journal/lab-37a/task1 /root/rhcsa_journal/lab-37a/task2 2>/dev/null || true
ls -la /root/rhcsa_journal/lab-37b/task1 /root/rhcsa_journal/lab-37b/task2 2>/dev/null || true
```

---

## Objective

Validate that local resolution work was done safely and can be recovered:

1. Audit `/etc/hosts` and `getent hosts` behavior against journal evidence.
2. Confirm `hosts:` line policy in `/etc/nsswitch.conf` and explain priority.
3. Run a full destroy-restore drill for `/etc/hosts` backup material (**T41**).

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export LAB_NUM=37
export LAB_SLUG=hosts
export SANDBOX=/tmp/lab37c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-37c/task1
mkdir -p /root/rhcsa_journal/lab-37c/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Audit `/etc/hosts` state vs journal

### Purpose

Prove current host-resolution state matches expected evidence and policy.

### Main command block

```bash
TASKLOG=/tmp/lab37c/task1.txt

echo "═══ Audit /etc/hosts and nsswitch policy ═══" | tee "$TASKLOG"
cp /etc/hosts /tmp/lab37c/hosts.audit.snapshot
sha256sum /etc/hosts /tmp/lab37c/hosts.audit.snapshot | tee -a "$TASKLOG"

grep '^hosts:' /etc/nsswitch.conf | tee -a "$TASKLOG"
getent hosts lab37test.local  | tee -a "$TASKLOG" || true
getent hosts lab37node1.local | tee -a "$TASKLOG" || true
getent hosts lab37node2.local | tee -a "$TASKLOG" || true

# Minimal journal consistency check: evidence files exist
test -s /root/rhcsa_journal/lab-37a/task1/evidence.txt && echo "✅ 37a task1 evidence exists" | tee -a "$TASKLOG"
test -s /root/rhcsa_journal/lab-37a/task2/evidence.txt && echo "✅ 37a task2 evidence exists" | tee -a "$TASKLOG"

echo "exit was: $?"
```

### Expected result

- You can state whether `hosts:` is `files dns` or `dns files` and what resolves first (**T37-B**).
- Journal evidence from 37a exists and current lookup tests are captured.

---

## Task 2 — Destroy-restore drill for `/etc/hosts` (T41)

### Purpose

Practice safe recovery by restoring from backup material after intentional destruction of lab scratch state.

### Main command block

```bash
TASKLOG=/tmp/lab37c/task2.txt

echo "═══ Destroy-restore drill ═══" | tee "$TASKLOG"

# Always take backup first (T37-A defense)
cp /etc/hosts /root/rhcsa_journal/lab-37c/hosts.before-drill.bak

# Destroy sandbox and recreate it
rm -rf /tmp/lab37c
mkdir -p /tmp/lab37c

# Restore /etc/hosts from backup
cp /root/rhcsa_journal/lab-37c/hosts.before-drill.bak /etc/hosts

# Validate exact restore and lookup behavior
diff -u /root/rhcsa_journal/lab-37c/hosts.before-drill.bak /etc/hosts | tee -a "$TASKLOG"
getent hosts lab37test.local  | tee -a "$TASKLOG" || true
getent hosts lab37node1.local | tee -a "$TASKLOG" || true
getent hosts lab37node2.local | tee -a "$TASKLOG" || true

cp /tmp/lab37c/task1.txt /root/rhcsa_journal/lab-37c/task1/evidence.txt
cp /tmp/lab37c/task2.txt /root/rhcsa_journal/lab-37c/task2/evidence.txt

echo "exit was: $?"
```

### Expected result

- `diff -u` empty after restore.
- Host lookups behave consistently before and after the drill.

---

## Lab Closeout — Section 6 Bulletproof Teardown

```bash
set +e

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group  "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}"  2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 37c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"               && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"             && echo "❌ home remains"    || echo "✅ home gone"

set -e
```

---

## Lab 37c Checklist

- [ ] Audited `/etc/hosts` plus `getent hosts` outputs and journal traces
- [ ] Verified and explained `hosts:` lookup priority in `/etc/nsswitch.conf` (**T37-B**)
- [ ] Executed destroy-restore drill for `/etc/hosts` backup/recovery (**T41**)
- [ ] Confirmed backup-first reflex before edits/restores (**T37-A**)
- [ ] Completed Section 6 closeout with four `✅` lines (**T44**)

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
