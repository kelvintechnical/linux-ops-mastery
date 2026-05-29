# Lab 20a: Scrolling Through Large Files (RHCSA) — `less`, `more`, search nav, follow mode

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `20a` (RHCSA) → [`20b`](../lab-20b-less-more-scrolling-ansible/) (Ansible) → [`20c`](../lab-20c-less-more-scrolling-verify/) (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = interactive navigation muscle memory, Task 2 = `less +F` vs `tail -f` under rotation)
- **Practice Directory (rotation #20):** `/etc`
- **Sandbox (Tier B):** `/tmp/lab20a` with `USER=labuser_20_pager`, `GROUP=labgrp_20_pager`
- **Traps rehearsed:** **T20-A** (`less +F` and `tail -f` behave differently when logs rotate) · **T20-B** (ANSI/binary display noise; use `less -R` for raw color codes) · **T41** · **T44**

> **This lab's practice directory is `/etc`**. We read real system files there and write sandbox evidence under `/tmp/lab20a`.

---

## LAB HEADER BLOCK

```bash
echo "ENV:  ${ENV:-DECLARE_ME}"
echo "TIME: $(date -Is)"
echo "USER: $(whoami)@$(hostname)"
echo "TRAPS THIS LAB: T20-A T20-B T41 T44"
echo "PRACTICE DIR: /etc"
ls -ld /etc
ls /etc | wc -l
echo "Shell: $BASH_VERSION"
```

> **STOP - Paste header output before setup.**

---

## Objective

Build pager reflexes for exam speed:

1. Navigate large files with `less` using `/pattern`, `?pattern`, `n`, `N`, `g`, `G`, `q`.
2. Understand `less` flags: `-N` line numbers, `-S` no wrap, `+F` follow mode, `-R` raw ANSI colors.
3. Contrast `less +F` versus `tail -f` behavior when a file rotates (T20-A).

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export LAB_NUM=20
export LAB_SLUG=pager
export SANDBOX=/tmp/lab20a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-20a/task1 /root/rhcsa_journal/lab-20a/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
getent group "${GROUP}"
getent passwd "${USER}"
echo "setup exit: $?"
```

> **STOP - Paste `id`, `ls -ld`, and both `getent` lines before Task 1.**

---

## Task 1 — `less` navigation drill on `/var/log/messages`

### Warm-Up

```bash
ls -l /var/log/messages 2>&1 | tee /tmp/lab20a/warmup-task1.txt
wc -l /var/log/messages
head -n 5 /var/log/messages
tail -n 5 /var/log/messages
set -o pipefail
echo "warm-up exit: $?"
```

### Purpose

Practice all key motions in one pass and capture proof.  
Target keys: `/`, `?`, `n`, `N`, `g`, `G`, `q`, plus flags `-N`, `-S`.

### Main command block

```bash
TASKLOG=/tmp/lab20a/task1.txt
NAV_SCRIPT=/tmp/lab20a/less-nav-demo.sh

cat > "${NAV_SCRIPT}" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
FILE=/var/log/messages
echo "Demo file: ${FILE}"
echo "1) less -N -S ${FILE}"
echo "2) keys: /error ENTER, n, N, ?systemd ENTER, n, g, G, q"
echo "3) capture approximations with grep/head/tail:"
echo "--- /error equivalent ---"
grep -in "error" "${FILE}" | head -n 5 || true
echo "--- ?systemd equivalent ---"
grep -in "systemd" "${FILE}" | tail -n 5 || true
echo "--- g equivalent (top) ---"
head -n 3 "${FILE}"
echo "--- G equivalent (bottom) ---"
tail -n 3 "${FILE}"
EOF

chmod +x "${NAV_SCRIPT}"
"${NAV_SCRIPT}" 2>&1 | tee "${TASKLOG}"

echo "Now run interactively:"
echo "  less -N -S /var/log/messages" | tee -a "${TASKLOG}"
echo "  keys: /error ENTER, n, N, ?systemd ENTER, n, g, G, q" | tee -a "${TASKLOG}"
echo "task1 exit: $?"
```

### Expected output

```text
Demo file: /var/log/messages
1) less -N -S /var/log/messages
2) keys: /error ENTER, n, N, ?systemd ENTER, n, g, G, q
...
Now run interactively:
less -N -S /var/log/messages
keys: /error ENTER, n, N, ?systemd ENTER, n, g, G, q
```

### Concept Card

| Key / Flag | Meaning |
|---|---|
| `/pattern` | Forward search |
| `?pattern` | Backward search |
| `n` / `N` | Next / previous match |
| `g` / `G` | Jump to top / bottom |
| `q` | Quit pager |
| `-N` | Show line numbers |
| `-S` | Chop long lines (no wrap) |
| **🪤 T20-B** | ANSI escape soup in logs: use `less -R FILE` when color codes are present |

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-20a/task1
mkdir -p "${JDIR}"
cp /tmp/lab20a/task1.txt "${JDIR}/evidence.txt"
cp /tmp/lab20a/less-nav-demo.sh "${JDIR}/less-nav-demo.sh"
echo "TASK1 COMPLETE $(date -Is)" > "${JDIR}/done.txt"
ls -la "${JDIR}"
```

---

## Task 2 — `less +F` vs `tail -f` under rotation (T20-A)

### Warm-Up

```bash
touch /tmp/lab20a/growing.log
echo "seed-$(date -Is)" >> /tmp/lab20a/growing.log
tail -n 3 /tmp/lab20a/growing.log
set -o pipefail
echo "warm-up exit: $?"
```

### Purpose

Show that `less +F` is pager-follow mode (can return to navigation) while `tail -f` is stream-follow mode, and highlight rotate behavior differences.

### Main command block

```bash
TASKLOG=/tmp/lab20a/task2.txt
LOG=/tmp/lab20a/growing.log
ROT=/tmp/lab20a/growing.log.1

{
  echo "=== create growth and rotation ==="
  for i in 1 2 3; do echo "before-rotate-$i $(date -Is)" >> "${LOG}"; done
  mv "${LOG}" "${ROT}"
  touch "${LOG}"
  for i in 1 2 3; do echo "after-rotate-$i $(date -Is)" >> "${LOG}"; done
  echo
  echo "=== commands to run in separate terminals ==="
  echo "less +F ${LOG}        # Ctrl-C to stop follow, then scroll/search"
  echo "tail -f ${LOG}        # stream only; use tail -F for name-follow across rotate"
  echo "tail -F ${LOG}        # better for rotate by filename"
  echo
  echo "=== Tier B weave (run as ${USER}) ==="
} | tee "${TASKLOG}"

sudo -u "${USER}" bash -c "tail -n 5 '${LOG}' > '${USER_HOME}/tail-asuser.txt'"
stat -c '%U:%G %a %n' "${USER_HOME}/tail-asuser.txt" | tee -a "${TASKLOG}"
cat "${USER_HOME}/tail-asuser.txt" | tee -a "${TASKLOG}"

echo "task2 exit: $?"
```

### Expected output

```text
=== commands to run in separate terminals ===
less +F /tmp/lab20a/growing.log
tail -f /tmp/lab20a/growing.log
tail -F /tmp/lab20a/growing.log
...
labuser_20_pager:labgrp_20_pager 644 /tmp/lab20a/home_labuser_20_pager/tail-asuser.txt
after-rotate-1 ...
after-rotate-2 ...
after-rotate-3 ...
```

### Concept Card

| Command | Behavior |
|---|---|
| `less +F FILE` | Follow end of file, then `Ctrl-C` returns to browse/search mode |
| `tail -f FILE` | Follows file descriptor; may miss new file after rename/rotate |
| `tail -F FILE` | Follows filename and retries; better across rotation |
| **🪤 T20-A** | Confusing `-f` with `-F` and expecting same rotation behavior |

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-20a/task2
mkdir -p "${JDIR}"
cp /tmp/lab20a/task2.txt "${JDIR}/evidence.txt"
cp /tmp/lab20a/growing.log /tmp/lab20a/growing.log.1 "${JDIR}/" 2>/dev/null || true
cp "${USER_HOME}/tail-asuser.txt" "${JDIR}/tail-asuser.txt"
echo "TASK2 COMPLETE $(date -Is)" > "${JDIR}/done.txt"
ls -la "${JDIR}"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e
rm -f /tmp/lab20a/warmup-task1.txt /tmp/lab20a/task1.txt /tmp/lab20a/task2.txt
rm -f /tmp/lab20a/growing.log /tmp/lab20a/growing.log.1 /tmp/lab20a/less-nav-demo.sh
rm -f "${USER_HOME}/tail-asuser.txt"

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "---- lab-20a cleanup audit ----"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 20b** | Ansible-safe pager patterns and profile defaults |
| **Lab 20c** | Audit + destroy-restore verification |

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
