# Lab 24a: Stream Editing with `sed` (RHCSA) — safe in-place edits and print/delete filters

- **Series:** linux-ops-mastery — Text Processing & Validation
- **Trilogy:** **`24a`** (RHCSA hand-typed) → [`24b`](../lab-24b-sed-stream-editor-ansible/) (Ansible idempotent equivalent) → [`24c`](../lab-24c-sed-stream-editor-verify/) (Verify + destroy-restore)
- **Prerequisite:** Basic shell navigation (`ls`, `cp`, `cat`, `diff`)
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = safe `sed -i.bak` replace with diff proof; Task 2 = `sed -n`, `1,5p`, `/pattern/d`, `$d` filters on `/etc/services` snapshot)
- **Practice Directory (rotation #24):** `/var` (read target) + writes in `/tmp/lab24a`
- **Sandbox (Tier B):** `/tmp/lab24a` with `USER=labuser_24_sed`, `GROUP=labgrp_24_sed`, `USER_HOME=/tmp/lab24a/home_labuser_24_sed`
- **Traps rehearsed this lab:** **T24-A** (`sed -i` without backup destroys source on a bad pattern) · **T24-B** (forgetting `g` replaces only first match per line) · **T41** (skip destroy-restore rehearsal) · **T44** (cleanup residue after closeout)

> **This lab's practice directory is: `/var`** — we read realistic system content from `/var` and `/etc/services`, but all mutation stays in the Tier B sandbox.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T24-A T24-B T41 T44"
echo "📁  PRACTICE DIR: /var"
echo ""
ls -ld /var
ls -ld /etc/services
echo "Shell version: $BASH_VERSION"
```

> **STOP — paste header output before setup.**

---

## Objective

Build reliable `sed` reflexes for in-place edits and stream filtering:

1. Use `sed -i.bak 's/old/new/g' file` safely, then prove exactly what changed with `diff`.
2. Understand why **T24-A** is costly: `sed -i` mutates immediately and gives no rollback.
3. Use read-only filters (`sed -n`, `1,5p`, `/pattern/d`, `$d`, `-e`) against a service snapshot.
4. Produce journal evidence showing backup, diff, and filtered outputs.

---

## Concept: `sed` edits streams first, files second

`sed` always processes a text stream line by line.  
`-i` and `-i.bak` change where output lands:

- `sed 's/a/b/g' file` prints transformed text to stdout (file unchanged).
- `sed -i 's/a/b/g' file` writes back into the file directly (**no safety net**).
- `sed -i.bak 's/a/b/g' file` writes in-place **and** keeps `file.bak` as rollback.
- `sed -n '1,5p' file` prints only selected lines.
- `sed '/pattern/d' file` deletes matching lines from output stream.
- `sed '$d' file` drops the last line from output stream.
- `sed -e 'expr1' -e 'expr2' file` chains edits in one pass.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export LAB_NUM=24
export LAB_SLUG=sed
export SANDBOX=/tmp/lab24a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-24a/task1
mkdir -p /root/rhcsa_journal/lab-24a/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
getent passwd "${USER}"
getent group  "${GROUP}"
echo "exit was: $?"
```

> **STOP — paste `id`, `ls -ld`, and both `getent` lines before Task 1.**

---

## Task 1 — Safe in-place replacement (`sed -i.bak`) + diff proof

**Practice directory this task:** `/tmp/lab24a` (source copied from `/var` context)

### Warm-Up

```bash
ls -ld /var
cp /etc/services /tmp/lab24a/app.conf
printf '%s\n' 'old=alpha old=beta old=gamma' 'owner=old-team' >> /tmp/lab24a/app.conf
grep -n 'old' /tmp/lab24a/app.conf | head -n 5
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab24a/task1.txt
TARGET=/tmp/lab24a/app.conf

cp /etc/services "${TARGET}"
printf '%s\n' \
  'old=alpha old=beta old=gamma' \
  'legacy_path=/var/old/cache old old' \
  'owner=old-team' >> "${TARGET}"

echo "before replace (tail preview)"                         | tee "${TASKLOG}"
tail -n 5 "${TARGET}"                                        | tee -a "${TASKLOG}"

# Required pattern for this task:
sed -i.bak 's/old/new/g' "${TARGET}"

echo "backup exists?"                                        | tee -a "${TASKLOG}"
ls -l "${TARGET}" "${TARGET}.bak"                            | tee -a "${TASKLOG}"

echo "after replace (tail preview)"                          | tee -a "${TASKLOG}"
tail -n 5 "${TARGET}"                                        | tee -a "${TASKLOG}"

echo "diff against backup (proof)"                           | tee -a "${TASKLOG}"
diff -u "${TARGET}.bak" "${TARGET}"                          | tee -a "${TASKLOG}"

echo "sanity: any old tokens left?"                          | tee -a "${TASKLOG}"
grep -n 'old' "${TARGET}"                                    | tee -a "${TASKLOG}" || true

echo "exit was: $?"
```

### Why this matters

- `-i.bak` protects you from **T24-A** by preserving pre-edit state.
- `s/old/new/g` prevents **T24-B** by replacing every match per line, not just the first.
- `diff -u file.bak file` is your audit trail and rollback confidence.

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-24a/task1
mkdir -p "${JDIR}"
cp /tmp/lab24a/task1.txt "${JDIR}/evidence.txt"
cp /tmp/lab24a/app.conf "${JDIR}/app.conf.after"
cp /tmp/lab24a/app.conf.bak "${JDIR}/app.conf.before"
diff -u /tmp/lab24a/app.conf.bak /tmp/lab24a/app.conf > "${JDIR}/app.diff"
ls -la "${JDIR}"
echo "exit was: $?"
```

---

## Task 2 — `sed -n`, `1,5p`, `/pattern/d`, `$d`, and `-e` chaining

**Practice directory this task:** `/tmp/lab24a` (snapshot source from `/etc/services`)

### Warm-Up

```bash
cp /etc/services /tmp/lab24a/services.snap
wc -l /tmp/lab24a/services.snap
grep -n '^ssh' /tmp/lab24a/services.snap | head -n 3
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab24a/task2.txt
SRC=/tmp/lab24a/services.snap

cp /etc/services "${SRC}"

echo "A) print first 5 lines only (sed -n '1,5p')"            | tee "${TASKLOG}"
sed -n '1,5p' "${SRC}"                                         | tee -a "${TASKLOG}"

echo "B) drop ssh lines (/ssh/d) and print sample"             | tee -a "${TASKLOG}"
sed '/ssh/d' "${SRC}" | sed -n '1,5p'                          | tee -a "${TASKLOG}"

echo "C) remove final line (\$d) and show tail"                | tee -a "${TASKLOG}"
sed '$d' "${SRC}" | tail -n 3                                  | tee -a "${TASKLOG}"

echo "D) chain with -e (drop comments + print first 5)"        | tee -a "${TASKLOG}"
sed -e '/^#/d' -e '1,5p' -n "${SRC}"                           | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-24a/task2
mkdir -p "${JDIR}"
cp /tmp/lab24a/task2.txt "${JDIR}/evidence.txt"
cp /tmp/lab24a/services.snap "${JDIR}/services.snap"
ls -la "${JDIR}"
echo "exit was: $?"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group  "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi

rm -rf "${SANDBOX}"

echo "── Lab 24a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"   || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"  || echo "✅ group gone"
test -d "${SANDBOX}"               && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"             && echo "❌ home remains"    || echo "✅ home gone"

set -e
echo "Cleanup complete at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the four `✅` audit lines.**

---

## Lab 24a Checklist (2 tasks + closeout)

- [ ] Task 1: `sed -i.bak 's/old/new/g'` run; `.bak` present; `diff -u` captured
- [ ] Task 2: `sed -n '1,5p'`, `/pattern/d`, `$d`, and `-e` chain demonstrated on `/etc/services` snapshot
- [ ] Traps rehearsed: T24-A and T24-B explicitly proven
- [ ] Section 6 closeout completed with four `✅` audit lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
