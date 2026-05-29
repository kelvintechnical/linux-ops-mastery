# Lab 30c: Verifying `info` Pages — audit + destroy/restore

- **Series:** linux-ops-mastery — Documentation Navigation and Discovery
- **Trilogy:** `30a` (RHCSA) -> `30b` (Ansible) -> `30c` (Verify — you are here)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = audit info package state + journal evidence, Task 2 = destroy-restore drill)
- **Practice Directory (rotation #30):** `/sys` (orientation)
- **Sandbox (Tier B):** `/tmp/lab30c` with `USER=labuser_30_info`, `GROUP=labgrp_30_info`
- **Traps rehearsed this lab:** **T30-A** · **T30-B** · **T41** · **T44**

> **This lab verifies** that info-page tooling is truly present and recoverable, not just "recently installed."

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /sys"
echo "⚠️  TRAP REMINDERS THIS LAB: T30-A T30-B T41 T44"
ls -ld /sys /usr/share/info 2>/dev/null || true
rpm -q info 2>/dev/null || echo "info package not currently installed"
```

> **STOP — paste header output before setup.**

---

## Objective

1. Audit package state, command availability, docs tree content, and journal evidence quality.
2. Perform a destroy-restore cycle to prove operational recovery when `info` pages disappear.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab30c
export GROUP=labgrp_30_info
export USER=labuser_30_info
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-30c/task1 /root/rhcsa_journal/lab-30c/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Audit info package state and journal-grade evidence

### Purpose

Run direct system checks without trusting past output:

- Package installed state (`rpm -q info`)
- Binary presence (`command -v info`, `command -v install-info`)
- Docs tree populated (`/usr/share/info`)
- Journal evidence captures all checks for replay

### Main command block

```bash
TASKLOG=/tmp/lab30c/task1.txt

echo "═══ package + binary audit ═══"                     | tee "${TASKLOG}"
rpm -q info                                              2>&1 | tee -a "${TASKLOG}"
command -v info                                          2>&1 | tee -a "${TASKLOG}"
command -v install-info                                  2>&1 | tee -a "${TASKLOG}"

echo "═══ docs tree audit ═══"                           | tee -a "${TASKLOG}"
ls -la /usr/share/info                                   2>&1 | tee -a "${TASKLOG}"
ls -1 /usr/share/info 2>/dev/null | wc -l               2>&1 | tee -a "${TASKLOG}"

echo "═══ non-interactive info export audit ═══"         | tee -a "${TASKLOG}"
info coreutils 'ls invocation' -o /tmp/lab30c/ls.txt     2>&1 | tee -a "${TASKLOG}"
test -s /tmp/lab30c/ls.txt \
  && echo "✅ exported ls invocation text exists"        | tee -a "${TASKLOG}" \
  || echo "❌ missing exported ls invocation text"        | tee -a "${TASKLOG}"

echo "═══ journal evidence hooks ═══"                    | tee -a "${TASKLOG}"
journalctl --since "today" --no-pager 2>/dev/null \
  | grep -Ei 'dnf|info' | tail -n 20                     2>&1 | tee -a "${TASKLOG}" || true

echo "exit was: $?"                                      | tee -a "${TASKLOG}"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-30c/task1
cp /tmp/lab30c/task1.txt "${JDIR}/audit.txt"
cp /tmp/lab30c/ls.txt "${JDIR}/ls.txt"
```

---

## Task 2 — Destroy-restore drill (T30-B recovery)

### Purpose

Simulate failure and recover cleanly:

1. Remove `info` package (destroy).
2. Prove `/usr/share/info` and `info` command are missing/broken.
3. Reinstall and re-audit (restore).

### Main command block

```bash
TASKLOG=/tmp/lab30c/task2.txt

echo "═══ DESTROY phase ═══"                             | tee "${TASKLOG}"
dnf remove -y info                                       2>&1 | tee -a "${TASKLOG}" || true
rpm -q info                                              2>&1 | tee -a "${TASKLOG}" || true
command -v info                                          2>&1 | tee -a "${TASKLOG}" || true
ls -la /usr/share/info                                   2>&1 | tee -a "${TASKLOG}" || true

echo "═══ RESTORE phase ═══"                             | tee -a "${TASKLOG}"
dnf install -y info                                      2>&1 | tee -a "${TASKLOG}"
rpm -q info                                              2>&1 | tee -a "${TASKLOG}"
command -v info                                          2>&1 | tee -a "${TASKLOG}"
ls -1 /usr/share/info 2>/dev/null | wc -l               2>&1 | tee -a "${TASKLOG}"
info coreutils 'ls invocation' -o /tmp/lab30c/ls-restored.txt 2>&1 | tee -a "${TASKLOG}"
test -s /tmp/lab30c/ls-restored.txt \
  && echo "✅ restore verified"                          | tee -a "${TASKLOG}" \
  || echo "❌ restore failed"                            | tee -a "${TASKLOG}"

echo "exit was: $?"                                      | tee -a "${TASKLOG}"
```

### Trap callout

- **T30-B:** failing to install `info` on minimal images means every `info ...` operation fails.
- This drill forces the failure first, then proves recovery path under pressure.

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-30c/task2
cp /tmp/lab30c/task2.txt "${JDIR}/destroy-restore.txt"
cp /tmp/lab30c/ls-restored.txt "${JDIR}/ls-restored.txt"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 30c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 30c Checklist

- [ ] Task 1 completed (package/binary/docs-tree audit + journal evidence capture)
- [ ] Task 2 completed (destroy-restore drill proved T30-B recovery)
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
