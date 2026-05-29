# Lab 28a: Exploring Manual Pages (RHCSA) — `man`, sections, and pager navigation

- **Series:** linux-ops-mastery — Documentation & Networking
- **Trilogy:** **`28a`** (RHCSA hand-typed) → [`28b`](../lab-28b-man-pages-ansible/) (Ansible boundary artifact) → [`28c`](../lab-28c-man-pages-verify/) (Verify)
- **Career arcs covered:** RHCSA EX200 (fast command lookup under pressure), RHCE EX294 (documentation-driven troubleshooting), SRE (on-host docs when internet is unavailable)
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = keyword + section navigation with `man`; Task 2 = man-page package verification + `MANPATH` practice)
- **Practice Directory (rotation slot):** `/dev` (read-only inspection target)
- **Sandbox (Tier B):** `/tmp/lab28a` with `USER=labuser_28_man`, `GROUP=labgrp_28_man`
- **Traps rehearsed:** **T28-A** (section confusion: `man 1` vs `man 5` vs `man 8`) · **T28-B** (minimal install missing `man-db`/`man-pages`) · **T41** (cannot restore workflow after deleting artifacts) · **T44** (skip closeout audit)

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /dev"
ls -ld /dev
ls /dev | wc -l
echo "📦 man binaries:"
command -v man || true
echo "🕒 $(date -Is)"
echo "👤 $(whoami)@$(hostname)"
```

> **STOP — paste header output before setup.**

---

## Objective

Build fast reflexes for local documentation lookup:

1. Find commands by keyword with `man -k`.
2. Resolve section collisions (`passwd` in section 1 vs 5).
3. Extract short descriptions non-interactively with `man -P cat ... | head`.
4. Verify where man pages are stored (`man --path`, `MANPATH`, `/usr/share/man`).

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export LAB_NUM=28
export LAB_SLUG=man
export SANDBOX=/tmp/lab28a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-28a/task1 /root/rhcsa_journal/lab-28a/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

echo "Tier B sandbox ready at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — `man -k`, section contrast, and non-interactive capture

**Practice directory this task:** `/dev` (read-only context checks) + `/tmp/lab28a` (evidence files).

### Main command block

```bash
TASKLOG=/tmp/lab28a/task1.txt

echo "═══ Part A: /dev context + keyword discovery ═══"         2>&1 | tee "${TASKLOG}"
ls -ld /dev                                                    | tee -a "${TASKLOG}"
man -k passwd | head -n 10                                    | tee -a "${TASKLOG}"

echo "═══ Part B: T28-A section contrast (1 vs 5) ═══"         | tee -a "${TASKLOG}"
man 1 passwd | head -n 20                                     | tee -a "${TASKLOG}"
man 5 passwd | head -n 20                                     | tee -a "${TASKLOG}"

echo "═══ Part C: capture descriptions with -P cat ═══"        | tee -a "${TASKLOG}"
man -P cat 1 passwd | head -n 12                              | tee -a "${TASKLOG}"
man -P cat 5 passwd | head -n 12                              | tee -a "${TASKLOG}"

echo "═══ Part D: less navigation checklist (interactive) ═══" | tee -a "${TASKLOG}"
cat <<'EOF'                                                    | tee -a "${TASKLOG}"
Inside man:
  /pattern   search forward
  ?pattern   search backward
  n / N      next / previous match
  g / G      top / bottom
  q          quit
EOF

echo "exit was: $?"
```

### Concept Card

| Concept | What it does |
|---|---|
| `man -k KEYWORD` | Searches man page names/descriptions (apropos database) |
| `man N cmd` | Opens a specific section explicitly |
| `man 1 passwd` | Command behavior and flags |
| `man 5 passwd` | `/etc/passwd` file format |
| `man -P cat ... | head` | Non-interactive excerpt capture |
| **🪤 Trap Risk T28-A** | Wrong section means wrong answer; always verify `NAME` + section |

### Journal write

```bash
LAB=lab-28a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab28a/task1.txt "${JDIR}/evidence.txt"

cat > "${JDIR}/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

echo "exit was: $?"
```

---

## Task 2 — Package checks, `man --path`, and `MANPATH`

### Main command block

```bash
TASKLOG=/tmp/lab28a/task2.txt

echo "═══ Part A: baseline package checks ═══"                    2>&1 | tee "${TASKLOG}"
rpm -q man-db man-pages man-pages-extra                           | tee -a "${TASKLOG}" || true
rpm -ql man-pages | head -n 20                                    | tee -a "${TASKLOG}" || true

echo "═══ Part B: T28-B remediation on minimal installs ═══"      | tee -a "${TASKLOG}"
dnf install -y man-db man-pages man-pages-extra                   | tee -a "${TASKLOG}"

echo "═══ Part C: path and MANPATH checks ═══"                    | tee -a "${TASKLOG}"
man --path                                                        | tee -a "${TASKLOG}"
echo "MANPATH(before)=${MANPATH:-<unset>}"                        | tee -a "${TASKLOG}"
export MANPATH=/usr/share/man
echo "MANPATH(after)=${MANPATH}"                                  | tee -a "${TASKLOG}"
man --path                                                        | tee -a "${TASKLOG}"
ls -ld /usr/share/man /usr/share/man/man1 /usr/share/man/man5     | tee -a "${TASKLOG}"
ls -ld /dev                                                       | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Concept Card

| Concept | What it does |
|---|---|
| `man --path` | Prints search path used for manual pages |
| `MANPATH` | Overrides/appends man page lookup path |
| `rpm -ql man-pages` | Lists installed page files |
| `dnf install man-db man-pages` | Restores missing man infrastructure |
| **🪤 Trap Risk T28-B** | Minimal images may have no pages; install before assuming docs exist |

### Journal write

```bash
LAB=lab-28a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab28a/task2.txt "${JDIR}/evidence.txt"

cat > "${JDIR}/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

echo "exit was: $?"
```

---

## Lab Closeout (Section 6)

```bash
set +e
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 28a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"   || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"  || echo "✅ group gone"
test -d "${SANDBOX}"              && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d /tmp/lab28a               && echo "❌ /tmp/lab28a remains" || echo "✅ /tmp/lab28a gone"
set -e
```

> **T44 check:** closeout is complete only when all four audit lines are `✅`.

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
