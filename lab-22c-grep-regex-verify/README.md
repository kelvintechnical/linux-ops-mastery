# Lab 22c: Verifying `grep` and Regex Outcomes (Capstone) — Audit + Destroy-Restore

- **Series:** linux-ops-mastery — Text Processing and Pattern Matching
- **Trilogy:** [`22a`](../lab-22a-grep-regex-rhcsa/) → [`22b`](../lab-22b-grep-regex-ansible/) → **`22c`**
- **Prerequisite:** labs `22a` and `22b` journals exist
- **Time Estimate:** 20–30 minutes
- **Tasks:** 2 (Task 1 = audit 22a regex outputs in journal · Task 2 = destroy-restore drill)
- **Practice Directory (rotation slot):** `/home`
- **Sandbox (Tier B):** `/tmp/lab22c` with `USER=labuser_22_regex`, `GROUP=labgrp_22_regex`
- **Traps rehearsed:** **T22-A**, **T22-B**, **T41**, **T44**

---

## LAB HEADER BLOCK

```bash
echo "🔐 SE: $(getenforce 2>/dev/null || echo n/a)"
echo "🕒 TIME: $(date -Is)"
ls -la /root/rhcsa_journal/lab-22a/ /root/rhcsa_journal/lab-22b/ 2>/dev/null
```

---

## Lab-Wide Setup

```bash
sudo -i

export LAB_NUM=22
export LAB_SLUG=regex
export SANDBOX=/tmp/lab22c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-22c/task1 /root/rhcsa_journal/lab-22c/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Audit `22a` regex artifacts in journal

### Main command block

```bash
TASKLOG=/tmp/lab22c/task1.txt

echo "═══ Part A: completeness checks ═══"                    2>&1 | tee "$TASKLOG"
EXPECTED=(
  /root/rhcsa_journal/lab-22a/task1/evidence.txt
  /root/rhcsa_journal/lab-22a/task2/evidence.txt
)
MISS=0
for f in "${EXPECTED[@]}"; do
  test -s "$f" && echo "✅ $f" || { echo "❌ $f"; MISS=$((MISS+1)); }
done                                                       | tee -a "$TASKLOG"

echo "═══ Part B: verify Task 1 (`-E`) signals ═══"          | tee -a "$TASKLOG"
grep -E 'Part A: anchors|Part D: context' /root/rhcsa_journal/lab-22a/task1/evidence.txt \
  && echo "✅ ERE + context evidence present" \
  || echo "❌ missing ERE/context evidence"                  | tee -a "$TASKLOG"

echo "═══ Part C: verify Task 2 (`-P`) signals ═══"          | tee -a "$TASKLOG"
grep -E 'PCRE lookahead|greedy trap demo' /root/rhcsa_journal/lab-22a/task2/evidence.txt \
  && echo "✅ PCRE evidence present" \
  || echo "❌ missing PCRE evidence"                         | tee -a "$TASKLOG"

echo "═══ Part D: trap markers ═══"                          | tee -a "$TASKLOG"
grep -E 'T22-A|T22-B' /root/rhcsa_journal/lab-22a/task2/evidence.txt \
  && echo "✅ trap references captured" \
  || echo "❌ trap references missing"                       | tee -a "$TASKLOG"
```

### Journal write

```bash
LAB=lab-22c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab22c/task1.txt "$JDIR/evidence.txt"
```

---

## Task 2 — Destroy-restore drill (T41)

### Main command block

```bash
TASKLOG=/tmp/lab22c/task2.txt

echo "═══ Part A: snapshot ═══"                               2>&1 | tee "$TASKLOG"
ls -l /tmp/lab22a /tmp/lab22b 2>/dev/null                     | tee -a "$TASKLOG"

echo "═══ Part B: destroy sandboxes ═══"                      | tee -a "$TASKLOG"
rm -rf /tmp/lab22a /tmp/lab22b
test ! -d /tmp/lab22a && test ! -d /tmp/lab22b \
  && echo "✅ destroyed /tmp/lab22a and /tmp/lab22b" \
  || echo "❌ destroy failed"                                  | tee -a "$TASKLOG"

echo "═══ Part C: restore minimal artifacts from journal ═══" | tee -a "$TASKLOG"
mkdir -p /tmp/lab22a /tmp/lab22b
cp /root/rhcsa_journal/lab-22a/task1/evidence.txt /tmp/lab22a/restored-task1.txt
cp /root/rhcsa_journal/lab-22a/task2/evidence.txt /tmp/lab22a/restored-task2.txt
test -s /tmp/lab22a/restored-task1.txt && test -s /tmp/lab22a/restored-task2.txt \
  && echo "✅ restored evidence from journal" \
  || echo "❌ restore missing data"                            | tee -a "$TASKLOG"

echo "═══ Part D: reboot survivability reasoning (T44) ═══"   | tee -a "$TASKLOG"
cat <<'EOF' | tee -a "$TASKLOG"
SURVIVES REBOOT:
  /root/rhcsa_journal/lab-22a/
DOES NOT GUARANTEE REBOOT SURVIVAL:
  /tmp/lab22a and /tmp/lab22b
RECOVERY ACTION:
  restore from journal files and re-run source commands/playbooks
EOF
```

### Journal write

```bash
LAB=lab-22c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab22c/task2.txt "$JDIR/evidence.txt"
```

---

## Lab Closeout — Section 6 teardown + audit

```bash
set +e
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}" /tmp/lab22a /tmp/lab22b /tmp/lab22c

echo "── Lab 22c cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d /tmp/lab22a                 && echo "❌ lab22a remains"  || echo "✅ lab22a gone"
test -d /tmp/lab22b                 && echo "❌ lab22b remains"  || echo "✅ lab22b gone"
test -d /tmp/lab22c                 && echo "❌ lab22c remains"  || echo "✅ lab22c gone"
set -e
```

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
