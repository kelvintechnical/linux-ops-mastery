# Lab 09c: Verifying Links (Capstone) — Audit + Persistence Drill

- **Series:** linux-ops-mastery — Essential Tools & File Operations
- **Trilogy:** [`09a`](../lab-09a-hard-and-soft-links-rhcsa/) → [`09b`](../lab-09b-hard-and-soft-links-ansible/) → **`09c`**
- **Prerequisite:** Labs 09a + 09b completed
- **Time Estimate:** 20–30 minutes
- **Tasks:** 2 (Task 1 = audit hard/symlink evidence + dangling drill · Task 2 = destroy-restore — wipe `/tmp/lab09b/`, re-apply playbooks)
- **Sandbox (Tier B):** `/tmp/lab09c` with `USER=labuser_09_verify`, `GROUP=labgrp_09_verify`
- **Traps rehearsed:** **T17/T18/T19/T17-X** (audit each) · **T41/T42**

---

## LAB HEADER BLOCK

```bash
echo "🔐 SE: $(getenforce 2>/dev/null || echo n/a)"
ls -la /root/rhcsa_journal/lab-09a/ /root/rhcsa_journal/lab-09b/
```

---

## Lab-Wide Setup

```bash
sudo -i

export LAB_NUM=09
export LAB_SLUG=verify
export SANDBOX=/tmp/lab09c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-09c/task1 /root/rhcsa_journal/lab-09c/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — Audit 09a/09b artifacts + dangling drill

### Main command block

```bash
TASKLOG=/tmp/lab09c/task1.txt

echo "═══ Part A: completeness ═══"                      2>&1 | tee $TASKLOG
EXPECTED=(
    /root/rhcsa_journal/lab-09a/task1/evidence.txt
    /root/rhcsa_journal/lab-09a/task1/asuser.txt
    /root/rhcsa_journal/lab-09a/task2/evidence.txt
    /root/rhcsa_journal/lab-09a/task2/sym-asuser.txt
    /root/rhcsa_journal/lab-09b/task1/task1.yml
    /root/rhcsa_journal/lab-09b/task2/task2.yml
)
M=0
for f in "${EXPECTED[@]}"; do
    test -s "$f" && echo "✅ $f" || { echo "❌ $f"; M=$((M+1)); }
done                                                    | tee -a $TASKLOG

echo "═══ Part B: T17 — hard-link survival captured ═══"  | tee -a $TASKLOG
grep 'T17 — hard1.txt still readable' /root/rhcsa_journal/lab-09a/task1/evidence.txt \
    && echo "✅ T17 captured" \
    || echo "❌ T17 missing" \
    | tee -a $TASKLOG

echo "═══ Part C: T18 — dangling captured ═══"            | tee -a $TASKLOG
grep 'T18 demonstrated' /root/rhcsa_journal/lab-09a/task2/evidence.txt \
    && echo "✅ T18 captured" \
    || echo "❌ T18 missing" \
    | tee -a $TASKLOG

echo "═══ Part D: T19 — relative resolve captured ═══"    | tee -a $TASKLOG
grep 'T19 — rel-bad does NOT resolve' /root/rhcsa_journal/lab-09a/task2/evidence.txt \
    && echo "✅ T19 captured" \
    || echo "❌ T19 missing" \
    | tee -a $TASKLOG

echo "═══ Part E: T17-X — force: true captured ═══"       | tee -a $TASKLOG
grep 'T17-X — force: true' /root/rhcsa_journal/lab-09b/task2/evidence.txt \
    && echo "✅ T17-X captured" \
    || echo "❌ T17-X missing" \
    | tee -a $TASKLOG

echo "═══ Part F: live dangling-symlink scan AS ${USER} ═══" | tee -a $TASKLOG
sudo -u "${USER}" -H bash -c '
    cd "'"${USER_HOME}"'"
    echo "tmp" > target.txt
    ln -s target.txt link.txt
    rm target.txt
    test -L link.txt && test ! -e link.txt && echo "T18 live: dangling confirmed"
    find . -xtype l
' > "${USER_HOME}/dangling.txt" 2>&1
cat "${USER_HOME}/dangling.txt"                          | tee -a $TASKLOG

echo "exit was: $?"
```

### Journal write

```bash
LAB=lab-09c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab09c/task1.txt "$JDIR/evidence.txt"
cp "${USER_HOME}/dangling.txt" "$JDIR/dangling.txt"

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
TOPIC:    Audit T17/T18/T19/T17-X + live dangling drill AS USER
NEXT:     task2 — destroy-restore (T41)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /tmp/lab09c/task1.txt
rm -f "${USER_HOME}/dangling.txt"
echo "exit was: $?"
```

> **STOP — paste five `✅` lines (B-E + completeness) before Task 2.**

---

## Task 2 — Destroy-restore drill (T41)

### Main command block

```bash
TASKLOG=/tmp/lab09c/task2.txt
PB1=/root/rhcsa_journal/lab-09b/playbooks/task1.yml
PB2=/root/rhcsa_journal/lab-09b/playbooks/task2.yml

echo "═══ Part A: snapshot ═══"                          2>&1 | tee $TASKLOG
ls -li /tmp/lab09b/ 2>/dev/null                          | tee -a $TASKLOG
A_INO=$(stat -c '%i' /tmp/lab09b/primary.txt 2>/dev/null || echo "0")
echo "primary inode: ${A_INO}"                           | tee -a $TASKLOG

echo "═══ Part B: destroy ═══"                            | tee -a $TASKLOG
rm -rf /tmp/lab09b
test ! -d /tmp/lab09b && echo "✅ destroyed" || echo "❌ destroy failed" | tee -a $TASKLOG

echo "═══ Part C: restore + re-apply ═══"                  | tee -a $TASKLOG
mkdir -p /tmp/lab09b
echo "primary content" > /tmp/lab09b/primary.txt
echo "PRE-EXISTING REGULAR FILE" > /tmp/lab09b/will-be-link.txt
ansible-playbook "${PB1}"                                2>&1 | tee -a $TASKLOG
ansible-playbook "${PB2}"                                2>&1 | tee -a $TASKLOG

echo "═══ Part D: verify ═══"                             | tee -a $TASKLOG
ls -li /tmp/lab09b/                                      | tee -a $TASKLOG
P_INO=$(stat -c '%i' /tmp/lab09b/primary.txt)
H_INO=$(stat -c '%i' /tmp/lab09b/hard.txt)
test "${P_INO}" = "${H_INO}" \
    && echo "✅ hard.txt shares inode with primary (post-restore)" \
    || echo "❌ inodes differ" \
    | tee -a $TASKLOG
test -L /tmp/lab09b/sym.txt && echo "✅ sym.txt is symlink" | tee -a $TASKLOG
test -L /tmp/lab09b/will-be-link.txt && echo "✅ will-be-link.txt is symlink (force worked again)" | tee -a $TASKLOG

echo "═══ Part E: T42 reasoning ═══"                     | tee -a $TASKLOG
cat <<'EOF' | tee -a $TASKLOG
SURVIVES A REBOOT:
  /root/rhcsa_journal/lab-09b/playbooks/  (task1.yml, task2.yml)
DOES NOT SURVIVE A REBOOT:
  /tmp/lab09b/  (primary.txt + links)
REBUILD:
  recreate /tmp/lab09b/primary.txt + will-be-link.txt; then re-apply both playbooks
EOF

echo "exit was: $?"
```

### Journal write

```bash
LAB=lab-09c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab09c/task2.txt "$JDIR/evidence.txt"

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
TOPIC:    Destroy /tmp/lab09b/, restore via 09b playbooks; verify links
NEXT:     Lab 10a — moving and renaming
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /tmp/lab09c/task2.txt
echo "exit was: $?"
```

> **STOP — paste Part D inode-match + symlink lines.**

---

## Lab Closeout

```bash
set +e
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}" /tmp/lab09b

echo "── Lab 09c cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d /tmp/lab09b                 && echo "❌ lab09b remains"  || echo "✅ lab09b gone"
set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
