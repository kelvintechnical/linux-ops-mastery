# Lab 09a: Hard and Soft Links (RHCSA) — `ln`, `ln -s`, `readlink`, `find -inum`

- **Series:** linux-ops-mastery — Essential Tools & File Operations
- **Trilogy:** `09a` (RHCSA hand-typed) → [`09b`](../lab-09b-hard-and-soft-links-ansible/) (Ansible — `state=link`/`state=hard`) → [`09c`](../lab-09c-hard-and-soft-links-verify/)
- **Career arcs covered:** RHCSA EX200 (link reflexes; identify dangling symlinks; same-inode hardlinks)
- **Prerequisite:** [`Lab 08c`](../lab-08c-copying-files-directories-verify/) completed
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = hard link create + verify same inode + `stat -c %h` · Task 2 = symlink create + `readlink -f` + dangling test — **T17**, **T18**, **T19**)
- **Practice Directory (rotation #10):** `/var/log`
- **Sandbox (Tier B):** `/tmp/lab09a` with `USER=labuser_09_link`, `GROUP=labgrp_09_link`
- **Traps rehearsed:** **T17** (hard link survives delete of original — both names point to the same inode) · **T18** (symlink CAN dangle — `test -L` is true even when target is gone) · **T19** (`ln -s relative/path` resolves relative to symlink's location, not your CWD)

> **Practice directory: `/var/log`** — log rotation creates symlinks like `journal/` and hardlinks for current/rotated.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T17 T18 T19"
echo "📁  PRACTICE DIR: /var/log"
ls -ld /var/log
ls -l /var/log/journal 2>/dev/null | head -n 3
```

---

## Lab-Wide Setup

```bash
sudo -i

export LAB_NUM=09
export LAB_SLUG=link
export SANDBOX=/tmp/lab09a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-09a/task1 /root/rhcsa_journal/lab-09a/task2

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
Practice directory: /var/log
/var/log uses both hardlinks (rotated logs share inodes briefly) and
symlinks (e.g. /var/log/journal -> /run/log/journal on some setups).
Mastering ln + ln -s on /var/log mirrors how RHEL distributes logs.
EOF

# Source file we'll link to
echo "primary content line 1" > "${SANDBOX}/primary.txt"
echo "primary content line 2" >> "${SANDBOX}/primary.txt"

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — Hard links: `ln`, `stat -c %h`, `find -inum` (T17)

### 🔁 Warm-Up

```bash
ls -li "${SANDBOX}/primary.txt"                          2>&1 | tee /tmp/lab09a/warmup.txt
stat -c '%i %h %n' "${SANDBOX}/primary.txt"
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab09a/task1.txt

echo "═══ Part A: create hard link ═══"                  2>&1 | tee $TASKLOG
ln "${SANDBOX}/primary.txt" "${SANDBOX}/hard1.txt"
ls -li "${SANDBOX}/primary.txt" "${SANDBOX}/hard1.txt"  | tee -a $TASKLOG
P_INO=$(stat -c '%i' "${SANDBOX}/primary.txt")
H_INO=$(stat -c '%i' "${SANDBOX}/hard1.txt")
echo "primary inode: ${P_INO}  hard1 inode: ${H_INO}"   | tee -a $TASKLOG
test "${P_INO}" = "${H_INO}" \
    && echo "✅ same inode (true hard link)" \
    || echo "❌ different inodes" \
    | tee -a $TASKLOG

echo "═══ Part B: stat -c %h shows link count ═══"        | tee -a $TASKLOG
stat -c 'links: %h  name: %n' "${SANDBOX}/primary.txt" "${SANDBOX}/hard1.txt" | tee -a $TASKLOG

echo "═══ Part C: find -inum ═══"                         | tee -a $TASKLOG
find "${SANDBOX}" -inum "${P_INO}"                       | tee -a $TASKLOG

echo "═══ Part D: T17 — delete primary, hard1 still works ═══" | tee -a $TASKLOG
rm "${SANDBOX}/primary.txt"
test ! -f "${SANDBOX}/primary.txt" && echo "primary.txt removed" | tee -a $TASKLOG
ls -li "${SANDBOX}/hard1.txt"                            | tee -a $TASKLOG
cat "${SANDBOX}/hard1.txt"                               | tee -a $TASKLOG
echo "✅ T17 — hard1.txt still readable after primary deleted" | tee -a $TASKLOG

# Recreate primary for Task 2
ln "${SANDBOX}/hard1.txt" "${SANDBOX}/primary.txt"

echo "═══ Part E: AS ${USER} (Tier B) ═══"                | tee -a $TASKLOG
sudo -u "${USER}" -H bash -c '
    echo "asuser content" > "'"${USER_HOME}"'/u-primary.txt"
    ln "'"${USER_HOME}"'/u-primary.txt" "'"${USER_HOME}"'/u-hard.txt"
    stat -c "%i %h %n" "'"${USER_HOME}"'"/u-primary.txt "'"${USER_HOME}"'"/u-hard.txt
' > "${USER_HOME}/asuser.txt"
cat "${USER_HOME}/asuser.txt"                            | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${USER_HOME}/asuser.txt"           | tee -a $TASKLOG

echo "exit was: $?"
```

### 🧠 Concept Card

| Concept | What it does |
|---|---|
| Hard link | New name pointing at the SAME inode |
| `stat -c %h` | Inode link count — 1 = unique, 2+ = hard-linked |
| `find -inum N` | Find every name pointing at inode N |
| Same-FS only | Hard links cannot cross filesystems |
| **🪤 Trap Risk T17** | Thinking `rm` deletes the file — it only unlinks one name. **Fix:** check `stat -c %h` before assuming `rm` frees disk. |

### Journal write

```bash
LAB=lab-09a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab09a/task1.txt "$JDIR/evidence.txt"
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
TOPIC:    Hard links — same inode; survives unlink of original
TRAPS:    T17 rehearsed
NEXT:     task2 — symlinks (T18, T19)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /tmp/lab09a/warmup.txt /tmp/lab09a/task1.txt
ls /tmp/lab09a
echo "exit was: $?"
```

> **STOP — paste Part A `same inode`, Part D `T17 ✅`, and Part E ownership before Task 2.**

---

## Task 2 — Symlinks: `ln -s`, `readlink -f`, dangling (T18, T19)

### 🔁 Warm-Up

```bash
ls -l "${SANDBOX}"/*.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab09a/task2.txt

echo "═══ Part A: create absolute symlink ═══"           2>&1 | tee $TASKLOG
ln -s "${SANDBOX}/primary.txt" "${SANDBOX}/sym-abs.txt"
ls -l "${SANDBOX}/sym-abs.txt"                          | tee -a $TASKLOG
readlink "${SANDBOX}/sym-abs.txt"                        | tee -a $TASKLOG
readlink -f "${SANDBOX}/sym-abs.txt"                     | tee -a $TASKLOG

echo "═══ Part B: T19 — relative symlink resolves vs symlink's location ═══" | tee -a $TASKLOG
mkdir -p "${SANDBOX}/sub"
# Wrong intuition: ln -s ../primary.txt creates link relative to CWD
cd "${SANDBOX}/sub"
ln -s ../primary.txt rel-good.txt
ls -l "${SANDBOX}/sub/rel-good.txt"                      | tee -a $TASKLOG
readlink -f "${SANDBOX}/sub/rel-good.txt"                | tee -a $TASKLOG
test -e "${SANDBOX}/sub/rel-good.txt" \
    && echo "✅ relative symlink resolves to existing target" \
    || echo "❌ rel-good resolves to nothing" \
    | tee -a $TASKLOG

# Demonstrate T19 wrong: symlink in subdir pointing to "primary.txt" (no ../)
ln -s primary.txt "${SANDBOX}/sub/rel-bad.txt"
test -e "${SANDBOX}/sub/rel-bad.txt" \
    && echo "❌ rel-bad shouldn't resolve (T19 not demonstrated)" \
    || echo "✅ T19 — rel-bad does NOT resolve (target lookup is relative to symlink's dir, not CWD)" \
    | tee -a $TASKLOG

cd /tmp

echo "═══ Part C: T18 — dangling symlink (test -L vs test -e) ═══" | tee -a $TASKLOG
echo "victim" > "${SANDBOX}/victim.txt"
ln -s "${SANDBOX}/victim.txt" "${SANDBOX}/sym-victim.txt"
test -L "${SANDBOX}/sym-victim.txt" && echo "test -L: yes (it's a symlink)"   | tee -a $TASKLOG
test -e "${SANDBOX}/sym-victim.txt" && echo "test -e: yes (target exists)"    | tee -a $TASKLOG

rm "${SANDBOX}/victim.txt"

test -L "${SANDBOX}/sym-victim.txt" && echo "after rm: test -L still yes (symlink itself exists)" | tee -a $TASKLOG
test -e "${SANDBOX}/sym-victim.txt" || echo "after rm: test -e: NO (T18 demonstrated — dangling)" | tee -a $TASKLOG

ls -l "${SANDBOX}/sym-victim.txt"                        | tee -a $TASKLOG

echo "═══ Part D: find dangling symlinks ═══"             | tee -a $TASKLOG
find "${SANDBOX}" -xtype l                               | tee -a $TASKLOG

echo "═══ Part E: AS ${USER} (Tier B) ═══"                | tee -a $TASKLOG
sudo -u "${USER}" -H bash -c '
    cd "'"${USER_HOME}"'"
    echo "user-target" > target.txt
    ln -s target.txt sym.txt
    ls -l sym.txt
    readlink -f sym.txt
    rm target.txt
    test -L sym.txt && echo "still a symlink"
    test -e sym.txt || echo "but dangling — T18"
' > "${USER_HOME}/sym.txt"
cat "${USER_HOME}/sym.txt"                               | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${USER_HOME}/sym.txt"              | tee -a $TASKLOG

echo "exit was: $?"
```

### Switches

| Token | Meaning |
|---|---|
| `ln -s TARGET LINK` | Create symbolic link |
| `readlink LINK` | Print stored target string |
| `readlink -f LINK` | Resolve through chains; print canonical path |
| `find -xtype l` | Find symlinks whose targets don't exist (dangling) |
| `test -L F` | True if F is a symlink (regardless of target) |
| `test -e F` | True if F exists (target follow-through) |

### 🧠 Concept Card

| Concept | What it does |
|---|---|
| Symlink target | A stored path string, not an inode reference |
| Cross-FS OK | Symlinks can point at other filesystems (unlike hard links) |
| **🪤 Trap Risk T18** | Treating `test -L` as "exists" — it isn't. **Fix:** combine `test -L && test -e`. |
| **🪤 Trap Risk T19** | Relative `ln -s` paths are interpreted from the symlink's directory, not your CWD. **Fix:** prefer absolute targets, or `cd` into the destination dir before creating. |

### Journal write

```bash
LAB=lab-09a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab09a/task2.txt "$JDIR/evidence.txt"
cp "${USER_HOME}/sym.txt" "$JDIR/sym-asuser.txt"

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
TOPIC:    Symlinks — readlink, dangling (T18), relative resolution (T19)
TRAPS:    T18 rehearsed; T19 rehearsed
NEXT:     lab-09b — ansible.builtin.file state=link / state=hard
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /tmp/lab09a/task2.txt
rm -f "${USER_HOME}/sym.txt" "${USER_HOME}/asuser.txt"
ls /tmp/lab09a
echo "exit was: $?"
```

> **STOP — paste T18 + T19 `✅` lines and Part E ownership before Closeout.**

---

## Lab Closeout

```bash
set +e
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 09a cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"              && echo "❌ home remains"    || echo "✅ home gone"
set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
