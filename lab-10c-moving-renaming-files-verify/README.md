# Lab 10c: Verifying Moves and Renames (Capstone) — Audit + Persistence

- **Series:** linux-ops-mastery — Essential Tools & File Operations
- **Trilogy:** [`10a`](../lab-10a-moving-renaming-files-rhcsa/) → [`10b`](../lab-10b-moving-renaming-files-ansible/) → **`10c`**
- **Prerequisite:** Labs 10a + 10b completed
- **Time Estimate:** 20–30 minutes
- **Tasks:** 2 (Task 1 = audit T10-A through T10-E + completeness · Task 2 = destroy-restore drill — wipe `/tmp/lab10b/`, re-apply playbooks, verify atomic + idempotent)
- **Sandbox (Tier B):** `/tmp/lab10c` with `USER=labuser_10_verify`, `GROUP=labgrp_10_verify`
- **Traps rehearsed:** **T10-A/B/C/D/E** (audit) · **T41/T42**

---

## LAB HEADER BLOCK

```bash
echo "🔐 SE: $(getenforce 2>/dev/null || echo n/a)"
ls -la /root/rhcsa_journal/lab-10a/ /root/rhcsa_journal/lab-10b/
```

---

## Lab-Wide Setup

```bash
sudo -i

export LAB_NUM=10
export LAB_SLUG=verify
export SANDBOX=/tmp/lab10c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-10c/task1 /root/rhcsa_journal/lab-10c/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — Audit 10a/10b artifacts

### Main command block

```bash
TASKLOG=/tmp/lab10c/task1.txt

echo "═══ Part A: completeness ═══"                      2>&1 | tee $TASKLOG
EXPECTED=(
    /root/rhcsa_journal/lab-10a/task1/evidence.txt
    /root/rhcsa_journal/lab-10a/task1/asuser.txt
    /root/rhcsa_journal/lab-10a/task2/evidence.txt
    /root/rhcsa_journal/lab-10a/task2/swap-asuser.txt
    /root/rhcsa_journal/lab-10b/task1/task1.yml
    /root/rhcsa_journal/lab-10b/task2/task2.yml
    /root/rhcsa_journal/lab-10b/task2/backup-list.txt
)
M=0
for f in "${EXPECTED[@]}"; do
    test -s "$f" && echo "✅ $f" || { echo "❌ $f"; M=$((M+1)); }
done                                                    | tee -a $TASKLOG

echo "═══ Part B: T10-A — cross-FS cp+rm captured ═══"    | tee -a $TASKLOG
grep 'T10-A — cross-FS mv changed inode' /root/rhcsa_journal/lab-10a/task2/evidence.txt \
    && echo "✅ T10-A captured" \
    || echo "❌ T10-A missing" \
    | tee -a $TASKLOG

echo "═══ Part C: T10-C — mv -t order captured ═══"       | tee -a $TASKLOG
grep -E 'mv -t .* A.txt B.txt' /root/rhcsa_journal/lab-10a/task1/evidence.txt \
    && echo "✅ T10-C captured" \
    || echo "❌ T10-C missing" \
    | tee -a $TASKLOG

echo "═══ Part D: T10-D — creates: idempotence captured ═══" | tee -a $TASKLOG
grep 'T10-D fix' /root/rhcsa_journal/lab-10b/task1/evidence.txt \
    && echo "✅ T10-D captured" \
    || echo "❌ T10-D missing" \
    | tee -a $TASKLOG

echo "═══ Part E: T10-E — atomic replace backup captured ═══" | tee -a $TASKLOG
test -s /root/rhcsa_journal/lab-10b/task2/backup-list.txt \
    && cat /root/rhcsa_journal/lab-10b/task2/backup-list.txt \
    && echo "✅ T10-E captured" \
    || echo "❌ T10-E missing" \
    | tee -a $TASKLOG

echo "exit was: $?"
```

### Journal write

```bash
LAB=lab-10c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab10c/task1.txt "$JDIR/evidence.txt"

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
TOPIC:    Audit T10-A/C/D/E + completeness
NEXT:     task2 — destroy-restore (T41)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /tmp/lab10c/task1.txt
echo "exit was: $?"
```

> **STOP — paste five `✅` lines before Task 2.**

---

## Task 2 — Destroy-restore drill (T41)

### Main command block

```bash
TASKLOG=/tmp/lab10c/task2.txt
PB1=/root/rhcsa_journal/lab-10b/playbooks/task1.yml
PB2=/root/rhcsa_journal/lab-10b/playbooks/task2.yml

echo "═══ Part A: snapshot ═══"                          2>&1 | tee $TASKLOG
ls -l /tmp/lab10b/dest/ 2>/dev/null                      | tee -a $TASKLOG

echo "═══ Part B: destroy ═══"                            | tee -a $TASKLOG
rm -rf /tmp/lab10b
test ! -d /tmp/lab10b && echo "✅ destroyed" || echo "❌ destroy failed" | tee -a $TASKLOG

echo "═══ Part C: restore — re-stage source files + apply both playbooks ═══" | tee -a $TASKLOG
mkdir -p /tmp/lab10b/dest
echo "report content" > /tmp/lab10b/report.txt
echo "v1 config" > /tmp/lab10b/dest/config.cfg

ansible-playbook "${PB1}"                                 2>&1 | tee -a $TASKLOG
ansible-playbook "${PB2}"                                 2>&1 | tee -a $TASKLOG

echo "═══ Part D: verify ═══"                             | tee -a $TASKLOG
ls -l /tmp/lab10b/ /tmp/lab10b/dest/                     | tee -a $TASKLOG
test -f /tmp/lab10b/dest/report.txt \
    && echo "✅ T10-D restore — Boundary mv idempotently moved report.txt" \
    || echo "❌ report.txt not in dest" \
    | tee -a $TASKLOG

cat /tmp/lab10b/dest/config.cfg                          | tee -a $TASKLOG
ls /tmp/lab10b/dest/config.cfg.* 2>/dev/null             | tee -a $TASKLOG
test -f /tmp/lab10b/dest/config.cfg.* \
    && echo "✅ T10-E restore — atomic config replace with backup again" \
    || echo "(no backup — config was identical, no replace needed)" \
    | tee -a $TASKLOG

echo "═══ Part E: T42 reasoning ═══"                     | tee -a $TASKLOG
cat <<'EOF' | tee -a $TASKLOG
SURVIVES A REBOOT:
  /root/rhcsa_journal/lab-10b/playbooks/  (task1.yml, task2.yml)
DOES NOT SURVIVE A REBOOT:
  /tmp/lab10b/  (sandbox)
REBUILD:
  recreate report.txt + config.cfg in /tmp/lab10b/, then re-apply both playbooks
EOF

echo "exit was: $?"
```

### Journal write

```bash
LAB=lab-10c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab10c/task2.txt "$JDIR/evidence.txt"

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
TOPIC:    Destroy /tmp/lab10b/, re-stage sources, re-apply 10b playbooks
TRAPS:    T41/T42 rehearsed
NEXT:     Continue curriculum (Lab 11+ already exists)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /tmp/lab10c/task2.txt
echo "exit was: $?"
```

> **STOP — paste Part D `✅` lines before Closeout.**

---

## Lab Closeout

```bash
set +e
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}" /tmp/lab10b

echo "── Lab 10c cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d /tmp/lab10b                 && echo "❌ lab10b remains"  || echo "✅ lab10b gone"
set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
