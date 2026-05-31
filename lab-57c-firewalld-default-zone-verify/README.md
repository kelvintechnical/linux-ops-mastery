# Lab 57c: Verifying Default Firewall Zone Changes — audit + destroy/restore

- **Series:** linux-ops-mastery — Firewalld Zone Operations
- **Trilogy:** `57a` (RHCSA) -> `57b` (Ansible) -> `57c` (Verify — you are here)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = audit evidence, Task 2 = destroy-restore drill)
- **Practice Directory (rotation #57):** `/sbin` (command context)
- **Sandbox (Tier B):** `/tmp/lab57c` with `USER=labuser_57_fwdef`, `GROUP=labgrp_57_fwdef`
- **Traps rehearsed this lab:** **T57-A** · **T57-B** · **T41** · **T44**

> **CRITICAL SAFETY:** Explicitly log the original default zone and always restore it at task end and closeout. SSH-cutoff risk must be called out before every default-zone switch.

---

## LAB HEADER BLOCK

```bash
echo "🕒  TIME: $(date -Is)"
echo "👤  USER: $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /sbin"
echo "⚠️  TRAPS: T57-A T57-B T41 T44"
firewall-cmd --state
firewall-cmd --get-default-zone
```

---

## Objective

1. Capture journal-ready pre/post evidence for default-zone changes and reload behavior.
2. Execute destroy-restore drill: set alternate zone, verify, then restore original zone.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab57c
export GROUP=labgrp_57_fwdef
export USER=labuser_57_fwdef
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-57c/task1 /root/rhcsa_journal/lab-57c/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Audit default-zone change in journal (pre/post)

### Purpose

Produce hard evidence that default zone changed and that reload completed.

### Main command block

```bash
TASKLOG=/var/tmp/lab57c-task1.txt
orig=$(firewall-cmd --get-default-zone)
target=internal

echo "${orig}" > /root/rhcsa_journal/lab-57c/original_default_zone.txt

echo "pre-change default zone:"                           | tee "${TASKLOG}"
firewall-cmd --get-default-zone                           | tee -a "${TASKLOG}"
echo "T57-A warning: ensure ssh allowed before switch"    | tee -a "${TASKLOG}"

firewall-cmd --set-default-zone="${target}"               | tee -a "${TASKLOG}"
firewall-cmd --reload                                     | tee -a "${TASKLOG}"

echo "post-change default zone:"                          | tee -a "${TASKLOG}"
firewall-cmd --get-default-zone                           | tee -a "${TASKLOG}"

# restore for safety at end of task
firewall-cmd --set-default-zone="${orig}"                 | tee -a "${TASKLOG}"
firewall-cmd --reload                                     | tee -a "${TASKLOG}"
echo "restored default zone:"                             | tee -a "${TASKLOG}"
firewall-cmd --get-default-zone                           | tee -a "${TASKLOG}"

echo "exit was: $?"                                       | tee -a "${TASKLOG}"
```

### Journal write

```bash
cp /var/tmp/lab57c-task1.txt /root/rhcsa_journal/lab-57c/task1/audit-pre-post.txt
```

---

## Task 2 — Destroy-restore drill for default zone (T41)

### Purpose

Rehearse the operational recovery pattern: move away from baseline, verify, then return to baseline.

### Main command block

```bash
TASKLOG=/var/tmp/lab57c-task2.txt
orig=$(firewall-cmd --get-default-zone)
destroy_target=dmz

echo "original=${orig}"                                   | tee "${TASKLOG}"
echo "destroy_target=${destroy_target}"                   | tee -a "${TASKLOG}"
echo "T57-A warning: run only with console or rollback job" | tee -a "${TASKLOG}"

echo "═══ DESTROY phase ═══"                              | tee -a "${TASKLOG}"
firewall-cmd --set-default-zone="${destroy_target}"       | tee -a "${TASKLOG}"
firewall-cmd --reload                                     | tee -a "${TASKLOG}"
firewall-cmd --get-default-zone                           | tee -a "${TASKLOG}"

echo "═══ RESTORE phase ═══"                              | tee -a "${TASKLOG}"
firewall-cmd --set-default-zone="${orig}"                 | tee -a "${TASKLOG}"
firewall-cmd --reload                                     | tee -a "${TASKLOG}"
firewall-cmd --get-default-zone                           | tee -a "${TASKLOG}"

echo "exit was: $?"                                       | tee -a "${TASKLOG}"
```

### Trap callout

- **T57-A:** default-zone changes may sever SSH if target zone omits service `ssh`.
- **T57-B:** default-zone switch is immediate and persistent; recovery must be explicit.
- **T41:** verify labs must include a destroy-restore rehearsal.

### Journal write

```bash
cp /var/tmp/lab57c-task2.txt /root/rhcsa_journal/lab-57c/task2/destroy-restore.txt
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

orig_default_file=/root/rhcsa_journal/lab-57c/original_default_zone.txt
if [ -f "${orig_default_file}" ]; then
  orig="$(cat "${orig_default_file}")"
else
  orig="public"
fi

# CRITICAL SAFETY: always restore original default zone at closeout.
firewall-cmd --set-default-zone="${orig}" 2>/dev/null
firewall-cmd --reload 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 57c cleanup audit ──"
firewall-cmd --get-default-zone
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 57c Checklist

- [ ] Task 1 completed (journal captured pre/post `--get-default-zone` plus reload evidence)
- [ ] Task 2 completed (destroy-restore drill returned default zone to original)
- [ ] T57-A and T57-B documented with T41/T44 awareness
- [ ] Section 6 closeout restored original default zone and passed cleanup audit

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
