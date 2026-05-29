# Lab 06c: Verifying SELinux File Contexts (Capstone) — Audit + Persistence Drill

- **Series:** linux-ops-mastery — Essential Tools & File Operations
- **Trilogy:** [`06a`](../lab-06a-listing-files-selinux-rhcsa/) → [`06b`](../lab-06b-listing-files-selinux-ansible/) → **`06c`** (Verify — you are here)
- **Prerequisite:** Labs 06a + 06b completed
- **Time Estimate:** 20–30 minutes
- **Tasks:** 2 (Task 1 = audit semanage rule + on-disk context · Task 2 = destroy-restore drill — drop rule, re-add via journal playbook, prove context restored)
- **Sandbox (Tier B):** `/tmp/lab06c` with `USER=labuser_06_verify`, `GROUP=labgrp_06_verify`
- **Traps rehearsed:** **T01** (audit Enforcing) · **T02** (audit rule + restorecon idempotence) · **T41** (destroy-restore the rule) · **T42** (verbalize survival across reboot)

---

## LAB HEADER BLOCK

```bash
echo "🔐  SE: $(getenforce)"
echo "📓 06a + 06b journals:"
ls -la /root/rhcsa_journal/lab-06a/task2/ /root/rhcsa_journal/lab-06b/task1/
```

---

## Lab-Wide Setup

```bash
sudo -i

export LAB_NUM=06
export LAB_SLUG=verify
export SANDBOX=/tmp/lab06c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-06c/task1 /root/rhcsa_journal/lab-06c/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — Audit 06a/06b artifacts

### 🔁 Warm-Up

```bash
ls -la /root/rhcsa_journal/lab-06a/ /root/rhcsa_journal/lab-06b/
getenforce
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab06c/task1.txt

echo "═══ Part A: T01 — SELinux Enforcing ═══"           2>&1 | tee $TASKLOG
ENF=$(getenforce)
echo "getenforce: ${ENF}"                               | tee -a $TASKLOG
test "${ENF}" = "Enforcing" \
    && echo "✅ T01 — Enforcing" \
    || echo "⚠️  T01 — running ${ENF} (not Enforcing)" \
    | tee -a $TASKLOG

echo "═══ Part B: T02 — semanage rule from 06b present ═══" | tee -a $TASKLOG
RULE=$(semanage fcontext -l | grep '/tmp/lab06b/web' || echo "")
echo "${RULE:-no rule found}"                            | tee -a $TASKLOG
echo "${RULE}" | grep -q 'httpd_sys_content_t' \
    && echo "✅ T02 — semanage rule present" \
    || echo "❌ T02 — rule missing; re-run 06b" \
    | tee -a $TASKLOG

echo "═══ Part C: on-disk label matches rule ═══"         | tee -a $TASKLOG
ls -lZ /tmp/lab06b/web/index.html 2>/dev/null            | tee -a $TASKLOG
CTX=$(stat -c '%C' /tmp/lab06b/web/index.html 2>/dev/null)
echo "${CTX}" | grep -q 'httpd_sys_content_t' \
    && echo "✅ on-disk label matches rule" \
    || echo "❌ label drift — restorecon not applied" \
    | tee -a $TASKLOG

echo "═══ Part D: restorecon idempotence ═══"             | tee -a $TASKLOG
restorecon -Rv /tmp/lab06b/web 2>&1                      | tee -a $TASKLOG
restorecon -Rv /tmp/lab06b/web 2>&1                      | tee -a $TASKLOG
# Second run should produce no relabel output
echo "(second run should be silent — idempotent)"        | tee -a $TASKLOG

echo "═══ Part E: AS ${USER} — read but cannot relabel ═══" | tee -a $TASKLOG
sudo -u "${USER}" -H bash -c '
    ls -lZ /tmp/lab06b/web/index.html
    chcon -t user_tmp_t /tmp/lab06b/web/index.html 2>&1 \
        && echo "❌ user could relabel — bad" \
        || echo "✅ user cannot relabel (Permission denied as expected)"
' > "${USER_HOME}/audit-asuser.txt" 2>&1
cat "${USER_HOME}/audit-asuser.txt"                      | tee -a $TASKLOG

echo "exit was: $?"
```

### Journal write

```bash
LAB=lab-06c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab06c/task1.txt "$JDIR/evidence.txt"
cp "${USER_HOME}/audit-asuser.txt" "$JDIR/audit-asuser.txt"
semanage fcontext -l | grep '/tmp/lab06b/web' > "$JDIR/rule.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
LAB_USER: ${USER}
LAB_GROUP: ${GROUP}
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Audit Enforcing, semanage rule, on-disk label, restorecon idempotence
COMMANDS: getenforce, semanage fcontext -l, restorecon -Rv (twice), sudo -u USER chcon
TRAPS:    T01 audited; T02 audited
NEXT:     task2 — destroy-restore drill (T41/T42)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup (per-task)

```bash
rm -f /tmp/lab06c/task1.txt
echo "exit was: $?"
```

> **STOP — paste five `✅` lines (Parts A–E) before Task 2.**

---

## Task 2 — Destroy-restore drill (T41 / T42)

### 🔁 Warm-Up

```bash
findmnt /tmp 2>/dev/null || echo "/tmp not separately mounted"
sha256sum /root/rhcsa_journal/lab-06b/playbooks/task1.yml
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab06c/task2.txt
PB=/root/rhcsa_journal/lab-06b/playbooks/task1.yml

echo "═══ Part A: snapshot ═══"                          2>&1 | tee $TASKLOG
A_HASH=$(sha256sum "${PB}" | awk '{print $1}')
echo "playbook sha256: ${A_HASH}"                       | tee -a $TASKLOG
ls -lZ /tmp/lab06b/web/index.html                        | tee -a $TASKLOG

echo "═══ Part B: destroy — drop semanage rule + chcon back ═══" | tee -a $TASKLOG
semanage fcontext -d '/tmp/lab06b/web(/.*)?' 2>&1        | tee -a $TASKLOG
chcon -R -t user_tmp_t /tmp/lab06b/web
ls -lZ /tmp/lab06b/web/index.html                        | tee -a $TASKLOG
semanage fcontext -l | grep '/tmp/lab06b/web' \
    && echo "❌ rule still present" \
    || echo "✅ rule destroyed"                          | tee -a $TASKLOG

echo "═══ Part C: restore via 06b playbook ═══"           | tee -a $TASKLOG
ansible-playbook "${PB}"                                 2>&1 | tee -a $TASKLOG

echo "═══ Part D: verify rule + on-disk label ═══"        | tee -a $TASKLOG
semanage fcontext -l | grep '/tmp/lab06b/web'            | tee -a $TASKLOG
ls -lZ /tmp/lab06b/web/index.html                        | tee -a $TASKLOG
CTX=$(stat -c '%C' /tmp/lab06b/web/index.html)
echo "${CTX}" | grep -q 'httpd_sys_content_t' \
    && echo "✅ T41 — rule + label restored from journal playbook" \
    || echo "❌ restore failed" \
    | tee -a $TASKLOG

echo "═══ Part E: T42 reboot reasoning ═══"              | tee -a $TASKLOG
cat <<'EOF' | tee -a $TASKLOG
SURVIVES A REBOOT:
  semanage rule (in /etc/selinux/targeted/contexts/files/file_contexts.local)
  /root/rhcsa_journal/lab-06b/playbooks/task1.yml (root home)

DOES NOT SURVIVE A REBOOT (in this lab):
  /tmp/lab06b/web/  (sandbox content)
  /tmp/lab06c/      (sandbox)

REBUILD ON BOOT:
  - semanage rule still active — restorecon -Rv applies it
  - Re-run 06b Lab-Wide Setup to recreate /tmp/lab06b/web
  - ansible-playbook re-applies rule + label idempotently
EOF

echo "exit was: $?"
```

### Journal write

```bash
LAB=lab-06c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab06c/task2.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
LAB_USER: ${USER}
LAB_GROUP: ${GROUP}
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Destroy semanage rule + chcon, then restore via journal playbook
COMMANDS: semanage fcontext -d, chcon, ansible-playbook (restore)
TRAPS:    T41 rehearsed; T42 verbalized
NEXT:     Lab 07a — touch + timestamps
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup (per-task)

```bash
rm -f /tmp/lab06c/task2.txt
echo "exit was: $?"
```

> **STOP — paste Part D `✅ T41` line before Lab Closeout.**

---

## Lab Closeout — Bulletproof Teardown

```bash
set +e

# Drop the rule we created in 06b/restored in 06c so the system is clean
semanage fcontext -d '/tmp/lab06b/web(/.*)?' 2>/dev/null
rm -rf /tmp/lab06b
rm -rf /tmp/lab06c

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi

echo "── Lab 06c cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
semanage fcontext -l | grep -q '/tmp/lab06b/web' \
    && echo "❌ fcontext rule remains" \
    || echo "✅ fcontext rule gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — four `✅` audit lines. Lab 06 trilogy complete.**

---

## Lab 06c Checklist

- [ ] Task 1 — five `✅` (Enforcing, rule present, label matches, restorecon idempotent, USER cannot relabel)
- [ ] Task 2 — destroy clean; restore via playbook works; T42 reasoning recorded
- [ ] Lab Closeout — four `✅`

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
