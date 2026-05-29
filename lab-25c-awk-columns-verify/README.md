# Lab 25c: Verifying `awk` Column Extraction (Capstone) — Audit + Destroy-Restore

- **Series:** linux-ops-mastery — Text Processing and Parsing
- **Trilogy:** [`25a`](../lab-25a-awk-columns-rhcsa/) → [`25b`](../lab-25b-awk-columns-ansible/) → **`25c`**
- **Prerequisite:** Labs 25a and 25b complete
- **Time Estimate:** 20–30 minutes
- **Tasks:** 2 (Task 1 = audit 25a awk outputs and trap evidence · Task 2 = destroy-restore drill and re-verify)
- **Practice Directory (rotation slot):** `/tmp`
- **Sandbox (Tier B):** `/tmp/lab25c` with `USER=labuser_25_awk`, `GROUP=labgrp_25_awk`
- **Traps rehearsed:** **T25-A** · **T25-B** · **T41** · **T44**

---

## LAB HEADER BLOCK

```bash
echo "🔐 SE: $(getenforce 2>/dev/null || echo n/a)"
ls -la /root/rhcsa_journal/lab-25a/ /root/rhcsa_journal/lab-25b/
echo "⚠️ TRAPS: T25-A T25-B T41 T44"
echo "exit was: $?"
```

---

## Objective

Take the auditor seat:

1. Confirm 25a produced correct `awk` outputs for `-F:`, `$1`, `$3>1000`, `NR`, `NF`, `BEGIN/END`, and `printf`.
2. Validate trap coverage evidence.
3. Rebuild from partial destruction to prove repeatability (T41).
4. Finish with strict teardown auditing so no Tier B residue remains (T44).

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export LAB_NUM=25
export LAB_SLUG=awk
export SANDBOX=/tmp/lab25c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-25c/task1 /root/rhcsa_journal/lab-25c/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — Audit Lab 25a outputs

### Main command block

```bash
TASKLOG=/tmp/lab25c/task1.txt

echo "═══ Part A: completeness checks ═══"                             2>&1 | tee $TASKLOG
EXPECTED=(
  /root/rhcsa_journal/lab-25a/task1/evidence.txt
  /root/rhcsa_journal/lab-25a/task2/evidence.txt
  /root/rhcsa_journal/lab-25a/task2/passwd-summary.txt
  /root/rhcsa_journal/lab-25a/task2/task2-asuser.txt
)
M=0
for f in "${EXPECTED[@]}"; do
  test -s "$f" && echo "✅ $f" || { echo "❌ $f"; M=$((M+1)); }
done | tee -a $TASKLOG

echo "═══ Part B: verify required Task 1 commands were executed ═══"   | tee -a $TASKLOG
rg "awk -F: '\\{print \\$1\\}' /etc/passwd \\| head" /root/rhcsa_journal/lab-25a/task1/evidence.txt \
  && echo "✅ required command #1 found" \
  || echo "❌ missing required command #1" \
  | tee -a $TASKLOG

rg "awk '\\$3>1000 \\{print \\$1\\}' /etc/passwd" /root/rhcsa_journal/lab-25a/task1/evidence.txt \
  && echo "✅ required command #2 found" \
  || echo "❌ missing required command #2" \
  | tee -a $TASKLOG

echo "═══ Part C: verify BEGIN/END + printf evidence ═══"              | tee -a $TASKLOG
rg "TOTAL=.*UID_GT_1000=" /root/rhcsa_journal/lab-25a/task2/passwd-summary.txt \
  && echo "✅ BEGIN/END totals captured" \
  || echo "❌ missing totals" \
  | tee -a $TASKLOG

rg "^USER\\s+UID\\s+SHELL" /root/rhcsa_journal/lab-25a/task2/passwd-summary.txt \
  && echo "✅ printf header captured" \
  || echo "❌ missing printf header" \
  | tee -a $TASKLOG

echo "═══ Part D: trap evidence audit ═══"                             | tee -a $TASKLOG
rg "single-quoted shell var literal" /root/rhcsa_journal/lab-25a/task2/evidence.txt \
  && echo "✅ T25-B proof captured" \
  || echo "❌ T25-B proof missing" \
  | tee -a $TASKLOG

stat -c '%U:%G %a %n' /root/rhcsa_journal/lab-25a/task2/task2-asuser.txt | tee -a $TASKLOG
echo "exit was: $?"
```

### Journal write

```bash
LAB=lab-25c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab25c/task1.txt "$JDIR/evidence.txt"

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

## Task 2 — Destroy-restore drill (T41)

### Main command block

```bash
TASKLOG=/tmp/lab25c/task2.txt
PB1=/root/rhcsa_journal/lab-25b/playbooks/task1.yml
PB2=/root/rhcsa_journal/lab-25b/playbooks/task2.yml

echo "═══ Part A: snapshot before destroy ═══"                         2>&1 | tee $TASKLOG
ls -la /tmp/lab25b 2>/dev/null                                        | tee -a $TASKLOG

echo "═══ Part B: destroy working state ═══"                           | tee -a $TASKLOG
rm -rf /tmp/lab25b
test ! -d /tmp/lab25b \
  && echo "✅ destroyed /tmp/lab25b" \
  || echo "❌ destroy failed" \
  | tee -a $TASKLOG

echo "═══ Part C: restore minimal state and re-apply playbooks ═══"    | tee -a $TASKLOG
mkdir -p /tmp/lab25b
cat > /tmp/lab25b/passwd-sample.txt <<'EOF'
root:x:0:0:root:/root:/bin/bash
nobody:x:65534:65534:nobody:/:
student1:x:1001:1001:Student One:/home/student1:/bin/bash
student2:x:2002:2002:Student Two:/home/student2:/bin/zsh
EOF

ansible-playbook "${PB1}"                                              2>&1 | tee -a $TASKLOG
ansible-playbook "${PB2}"                                              2>&1 | tee -a $TASKLOG

echo "═══ Part D: verify restore artifacts ═══"                        | tee -a $TASKLOG
test -s /tmp/lab25b/awk-task1-output.txt \
  && echo "✅ restored task1 artifact" \
  || echo "❌ task1 artifact missing" \
  | tee -a $TASKLOG

test -s /tmp/lab25b/passwd-regex-fix.txt \
  && echo "✅ restored task2 artifact" \
  || echo "❌ task2 artifact missing" \
  | tee -a $TASKLOG

echo "═══ Part E: T42 persistence reasoning ═══"                       | tee -a $TASKLOG
cat <<'EOF' | tee -a $TASKLOG
SURVIVES REBOOT:
  /root/rhcsa_journal/lab-25b/playbooks/task1.yml
  /root/rhcsa_journal/lab-25b/playbooks/task2.yml
DOES NOT SURVIVE REBOOT:
  /tmp/lab25b/*
REBUILD:
  recreate /tmp/lab25b/passwd-sample.txt, then re-apply both playbooks
EOF

echo "exit was: $?"
```

### Journal write

```bash
LAB=lab-25c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab25c/task2.txt "$JDIR/evidence.txt"

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

## Lab Closeout — Section 6 Bulletproof Teardown

```bash
set +e
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}" /tmp/lab25b /tmp/lab25c/task1.txt /tmp/lab25c/task2.txt

echo "── Lab 25c cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d /tmp/lab25b                 && echo "❌ lab25b remains"  || echo "✅ lab25b gone"
set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> T44 enforcement: closeout is not complete until every audit line is `✅`.

---

## Lab 25c Checklist

- [ ] Task 1 audit passed for 25a outputs and trap evidence
- [ ] Task 2 destroy-restore passed and artifacts rebuilt
- [ ] T41/T42 reasoning captured in evidence log
- [ ] Section 6 closeout audit returned all `✅`

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
