# Lab 10a: Moving and Renaming Files (RHCSA) — `mv`, atomic rename, hard-link survival

- **Series:** linux-ops-mastery — Essential Tools & File Operations
- **Trilogy:** `10a` (RHCSA hand-typed) → [`10b`](../lab-10b-moving-renaming-files-ansible/) (Ansible — `command: mv` Boundary AND `copy` for atomic config replace) → [`10c`](../lab-10c-moving-renaming-files-verify/)
- **Career arcs covered:** RHCSA EX200 (rename + move + atomic config swap), DevOps (deploy by rename instead of write-in-place)
- **Prerequisite:** [`Lab 09c`](../lab-09c-hard-and-soft-links-verify/) completed
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = `mv`, `mv -i/-n/-b/-u/-t` flag tour · Task 2 = same-FS atomic rename vs cross-FS `cp+rm`; hard-link survival — **T10-A**, **T10-B**, **T10-C**)
- **Practice Directory (rotation #11):** `/var`
- **Sandbox (Tier B):** `/tmp/lab10a` with `USER=labuser_10_mv`, `GROUP=labgrp_10_mv`
- **Traps rehearsed:** **T10-A** (cross-FS `mv` is silently `cp+rm` — hard links break) · **T10-B** (`mv` without `-i` over an existing file silently overwrites) · **T10-C** (`mv -t DIR src1 src2` swap order — flag must come BEFORE sources)

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T10-A T10-B T10-C"
echo "📁  PRACTICE DIR: /var"
ls -ld /var /var/tmp /var/log
df -h /var /tmp
```

---

## Lab-Wide Setup

```bash
sudo -i

export LAB_NUM=10
export LAB_SLUG=mv
export SANDBOX=/tmp/lab10a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-10a/task1 /root/rhcsa_journal/lab-10a/task2

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
Practice directory: /var
/var hosts mutable system data: spool, lib, log. Atomic rename within
/var (e.g. /var/lib/dpkg/status -> .new -> rename) is the canonical
"safe config swap" pattern. RHCSA tasks "rename FILE.cfg" and "move
this report into /var/log" reduce to mv done correctly.
EOF

# Two filesystems: /tmp (likely tmpfs) and /var (rootfs) — let's actually use them
echo "primary on /tmp" > "${SANDBOX}/primary.txt"

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — `mv` flags: `-i/-n/-b/-u/-t`

### 🔁 Warm-Up

```bash
ls -l "${SANDBOX}"                                       2>&1 | tee /tmp/lab10a/warmup.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab10a/task1.txt

echo "═══ Part A: rename ═══"                            2>&1 | tee $TASKLOG
mv "${SANDBOX}/primary.txt" "${SANDBOX}/renamed.txt"
ls -l "${SANDBOX}/renamed.txt"                          | tee -a $TASKLOG

echo "═══ Part B: -i (interactive) — answer NO ═══"       | tee -a $TASKLOG
echo "second" > "${SANDBOX}/second.txt"
echo n | mv -i "${SANDBOX}/renamed.txt" "${SANDBOX}/second.txt"  2>&1 | tee -a $TASKLOG
ls -l "${SANDBOX}/renamed.txt" "${SANDBOX}/second.txt"   | tee -a $TASKLOG

echo "═══ Part C: -n (no-clobber) ═══"                    | tee -a $TASKLOG
mv -n "${SANDBOX}/renamed.txt" "${SANDBOX}/second.txt"   2>&1 | tee -a $TASKLOG
echo "(both files still distinct — n refused overwrite)" | tee -a $TASKLOG
ls -l "${SANDBOX}/renamed.txt" "${SANDBOX}/second.txt"   | tee -a $TASKLOG

echo "═══ Part D: -b (backup) ═══"                        | tee -a $TASKLOG
mv -b "${SANDBOX}/renamed.txt" "${SANDBOX}/second.txt"
ls -l "${SANDBOX}/"                                      | tee -a $TASKLOG
echo "(second.txt~ created as backup)"                  | tee -a $TASKLOG

echo "═══ Part E: -u (update only if newer) ═══"          | tee -a $TASKLOG
echo "old" > "${SANDBOX}/old.txt"
touch -d '2010-01-01' "${SANDBOX}/old.txt"
echo "new" > "${SANDBOX}/new.txt"
mv -u "${SANDBOX}/old.txt" "${SANDBOX}/new.txt"          2>&1 | tee -a $TASKLOG
echo "(should be no-op since old.txt is OLDER than new.txt)" | tee -a $TASKLOG
ls -l "${SANDBOX}/old.txt" "${SANDBOX}/new.txt"          | tee -a $TASKLOG

echo "═══ Part F: -t DIR (target dir flag — T10-C order) ═══" | tee -a $TASKLOG
mkdir -p "${SANDBOX}/dest"
echo "alpha" > "${SANDBOX}/A.txt"
echo "bravo" > "${SANDBOX}/B.txt"
mv -t "${SANDBOX}/dest" "${SANDBOX}/A.txt" "${SANDBOX}/B.txt"
ls -l "${SANDBOX}/dest/"                                 | tee -a $TASKLOG

echo "═══ Part G: AS ${USER} ═══"                          | tee -a $TASKLOG
sudo -u "${USER}" -H bash -c '
    cd "'"${USER_HOME}"'"
    echo "u" > u.txt
    mv u.txt v.txt
    ls -l
' > "${USER_HOME}/asuser.txt"
cat "${USER_HOME}/asuser.txt"                            | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${USER_HOME}/asuser.txt"           | tee -a $TASKLOG

echo "exit was: $?"
```

### Switches

| Token | Meaning |
|---|---|
| `mv SRC DST` | Rename or move |
| `mv -i` | Prompt before overwrite |
| `mv -n` | Never overwrite |
| `mv -b` | Backup (`DST~`) before overwrite |
| `mv -u` | Move only if SRC is newer than DST (or DST missing) |
| `mv -t DIR src1 src2 ...` | Move many sources INTO DIR — flag goes BEFORE sources |

### 🧠 Concept Card

| Concept | What it does |
|---|---|
| `-i` vs `-n` | Interactive prompt vs silent skip |
| `-b` for safety | Always usable on config files when you want a rollback |
| `-u` for sync-style | "Only move if newer" — useful in batch/cron |
| **🪤 Trap Risk T10-B** | Plain `mv` clobbers DST silently. **Fix:** `-i`/`-n`/`-b` per intent. |
| **🪤 Trap Risk T10-C** | `mv src1 src2 -t DIR` is wrong — `-t DIR` must come first. **Fix:** put `-t DIR` immediately after `mv`. |

### Journal write

```bash
LAB=lab-10a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab10a/task1.txt "$JDIR/evidence.txt"
cp "${USER_HOME}/asuser.txt" "$JDIR/asuser.txt"

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
TOPIC:    mv -i/-n/-b/-u/-t flag tour
TRAPS:    T10-B noted; T10-C demonstrated
TIER B:   asuser.txt owned by ${USER}
NEXT:     task2 — same-FS atomic vs cross-FS cp+rm + hard-link survival (T10-A)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /tmp/lab10a/warmup.txt /tmp/lab10a/task1.txt
ls /tmp/lab10a
echo "exit was: $?"
```

> **STOP — paste Parts D + F + G outputs before Task 2.**

---

## Task 2 — Same-FS atomic rename vs cross-FS `cp+rm`; hard-link survival (T10-A)

### 🔁 Warm-Up

```bash
df /tmp /var | awk 'NR>1 {print $1, $6}'                 2>&1 | tee /tmp/lab10a/warmup2.txt
mkdir -p "${SANDBOX}/dest"
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab10a/task2.txt

echo "═══ Part A: same-FS atomic rename — inode preserved ═══" 2>&1 | tee $TASKLOG
echo "atomic" > "${SANDBOX}/atomic-source.txt"
A_INO=$(stat -c '%i' "${SANDBOX}/atomic-source.txt")
mv "${SANDBOX}/atomic-source.txt" "${SANDBOX}/atomic-dest.txt"
B_INO=$(stat -c '%i' "${SANDBOX}/atomic-dest.txt")
echo "before inode: ${A_INO}  after inode: ${B_INO}"     | tee -a $TASKLOG
test "${A_INO}" = "${B_INO}" \
    && echo "✅ same-FS mv preserved inode (atomic rename)" \
    || echo "❌ inode changed — was actually cp+rm" \
    | tee -a $TASKLOG

echo "═══ Part B: T10-A — cross-FS mv silently becomes cp+rm ═══" | tee -a $TASKLOG
# /tmp (tmpfs) → /var/tmp (rootfs) is usually a cross-FS hop
echo "cross" > "${SANDBOX}/cross-source.txt"
ln "${SANDBOX}/cross-source.txt" "${SANDBOX}/cross-hardlink.txt"
C_INO_BEFORE=$(stat -c '%i' "${SANDBOX}/cross-source.txt")
HL_INO=$(stat -c '%i' "${SANDBOX}/cross-hardlink.txt")
echo "source inode: ${C_INO_BEFORE}  hardlink inode: ${HL_INO}"  | tee -a $TASKLOG

CROSS_DEST=/var/tmp/lab10a-cross.txt
mv "${SANDBOX}/cross-source.txt" "${CROSS_DEST}"
ls -l "${CROSS_DEST}"                                    | tee -a $TASKLOG
C_INO_AFTER=$(stat -c '%i' "${CROSS_DEST}")
echo "after-mv inode: ${C_INO_AFTER}"                    | tee -a $TASKLOG

if test "${C_INO_BEFORE}" != "${C_INO_AFTER}"; then
    echo "✅ T10-A — cross-FS mv changed inode (cp+rm under the hood)" | tee -a $TASKLOG
else
    echo "❌ inode preserved — these may be on the same FS"            | tee -a $TASKLOG
fi

echo "═══ Part C: hard-link survival check ═══"           | tee -a $TASKLOG
ls -li "${SANDBOX}/cross-hardlink.txt"                  | tee -a $TASKLOG
HL_LINKS=$(stat -c '%h' "${SANDBOX}/cross-hardlink.txt")
echo "remaining hardlink count: ${HL_LINKS}"            | tee -a $TASKLOG
test "${HL_LINKS}" -eq 1 \
    && echo "✅ T10-A — original hardlink lost its sibling (cross-FS mv broke the inode link)" \
    || echo "(unexpected hardlink count)" \
    | tee -a $TASKLOG

echo "═══ Part D: atomic config swap pattern (same-FS) ═══" | tee -a $TASKLOG
echo "v1 config" > "${SANDBOX}/dest/config.cfg"
echo "v2 config new" > "${SANDBOX}/dest/config.cfg.new"
mv -b "${SANDBOX}/dest/config.cfg.new" "${SANDBOX}/dest/config.cfg"
ls -l "${SANDBOX}/dest/"                                 | tee -a $TASKLOG
cat "${SANDBOX}/dest/config.cfg"                         | tee -a $TASKLOG

echo "═══ Part E: AS ${USER} (same-FS rename) ═══"        | tee -a $TASKLOG
sudo -u "${USER}" -H bash -c '
    cd "'"${USER_HOME}"'"
    echo "v1" > config.cfg
    echo "v2" > config.cfg.new
    mv -b config.cfg.new config.cfg
    ls -l
    cat config.cfg
' > "${USER_HOME}/swap.txt"
cat "${USER_HOME}/swap.txt"                              | tee -a $TASKLOG

# Cleanup the cross-FS file we left behind
rm -f /var/tmp/lab10a-cross.txt

echo "exit was: $?"
```

### 🧠 Concept Card

| Concept | What it does |
|---|---|
| Same-FS `mv` | rename(2) syscall — inode preserved, atomic |
| Cross-FS `mv` | `cp + unlink` under the hood — new inode |
| Atomic config swap | Write `.new`, then `mv -b .new actual` — readers always see a complete file |
| **🪤 Trap Risk T10-A** | Cross-FS `mv` breaks hard links AND loses any open file handles' positions. **Fix:** stay within one FS, or accept it's `cp+rm`. |

### Journal write

```bash
LAB=lab-10a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab10a/task2.txt "$JDIR/evidence.txt"
cp "${USER_HOME}/swap.txt" "$JDIR/swap-asuser.txt"

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
TOPIC:    Same-FS atomic rename vs cross-FS cp+rm (T10-A); atomic config swap
TRAPS:    T10-A demonstrated; T10-B and T10-C carried in
NEXT:     lab-10b — Boundary AND copy with backup
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup (per-task)

```bash
rm -f /tmp/lab10a/warmup2.txt /tmp/lab10a/task2.txt
rm -f "${USER_HOME}/asuser.txt" "${USER_HOME}/swap.txt"
ls /tmp/lab10a
echo "exit was: $?"
```

> **STOP — paste Part A + Part B `✅` lines before Closeout.**

---

## Lab Closeout

```bash
set +e
rm -f /var/tmp/lab10a-cross.txt
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 10a cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -f /var/tmp/lab10a-cross.txt   && echo "❌ /var/tmp residue"|| echo "✅ /var/tmp clean"
set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
