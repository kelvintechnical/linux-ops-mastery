# Lab 36a: Command-Line Network Config with `nmcli` (RHCSA)

- **Series:** linux-ops-mastery — Network Configuration and Verification
- **Trilogy:** `36a` (RHCSA hand-typed) -> `36b` (Ansible mirror) -> `36c` (Verify capstone)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation slot 1):** `/bin`
- **Sandbox (Tier B):** `/tmp/lab36a` with `USER=labuser_36_nmcli`, `GROUP=labgrp_36_nmcli`
- **Traps rehearsed this lab:** **T36-A** (config saved but not applied until `nmcli con up`) · **T36-B** (never edit your management profile) · **T41** · **T44**

> **Safety rule (hard):** use a test profile only. Do not modify your real management connection. This lab uses `lab36test` on dummy interface `dummy-lab36`.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV: ${ENV:-DECLARE_ME}"
echo "📦  OS:  $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME: $(date -Is)"
echo "👤  USER: $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /bin"
echo "⚠️  TRAP REMINDERS THIS LAB: T36-A T36-B T41 T44"
nmcli --version
nmcli dev status
```

> **STOP — paste header output before setup.**

---

## Objective

Build safe reflexes for command-line NetworkManager profile work:

1. Create and modify a test connection with `nmcli con add` and `nmcli con mod`.
2. Apply and verify runtime state with `nmcli con up`, `nmcli dev status`, and `nmcli con show`.
3. Bring test config down cleanly and remove it in cleanup.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab36a
export GROUP=labgrp_36_nmcli
export USER=labuser_36_nmcli
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-36a/task1 /root/rhcsa_journal/lab-36a/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
```

---

## Task 1 — Create safe test profile and set static IPv4

### Purpose

Use the exact safe command flow on a dummy interface and keep your SSH path untouched.

### Main command block

```bash
TASKLOG=/tmp/lab36a/task1.txt

nmcli con add type dummy ifname dummy-lab36 con-name lab36test                      2>&1 | tee "${TASKLOG}"
nmcli con mod lab36test ipv4.method manual ipv4.addresses 10.99.0.1/24              2>&1 | tee -a "${TASKLOG}"
nmcli con show lab36test                                                              2>&1 | tee -a "${TASKLOG}"
nmcli -f NAME,DEVICE,TYPE,STATE con show --active                                    2>&1 | tee -a "${TASKLOG}"

echo "exit was: $?"                                                                   | tee -a "${TASKLOG}"
```

### Trap callout

- **T36-B:** never run `nmcli con mod` against your active management profile during remote sessions.
- Always use test profile `lab36test` on `dummy-lab36` for drills.

### Journal write

```bash
cp /tmp/lab36a/task1.txt /root/rhcsa_journal/lab-36a/task1/evidence.txt
```

---

## Task 2 — Apply, verify, down, and cleanly remove test profile

### Purpose

Practice the apply-state reflex that avoids T36-A and finish with clean teardown.

### Main command block

```bash
TASKLOG=/tmp/lab36a/task2.txt

nmcli con up lab36test                                  2>&1 | tee "${TASKLOG}"
nmcli dev status                                        2>&1 | tee -a "${TASKLOG}"
nmcli -f GENERAL.STATE con show lab36test              2>&1 | tee -a "${TASKLOG}"

nmcli con down lab36test                                2>&1 | tee -a "${TASKLOG}"
nmcli con delete lab36test                              2>&1 | tee -a "${TASKLOG}"
nmcli con show | grep -E '^lab36test\b'                2>&1 | tee -a "${TASKLOG}" || echo "✅ lab36test removed" | tee -a "${TASKLOG}"

echo "exit was: $?"                                     | tee -a "${TASKLOG}"
```

### Trap callout

- **T36-A:** `nmcli con mod` writes persistent config, but runtime state does not change until `nmcli con up` (or reconnect).

### Journal write

```bash
cp /tmp/lab36a/task2.txt /root/rhcsa_journal/lab-36a/task2/evidence.txt
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# Safety: remove leftover test profile if present.
nmcli con show lab36test >/dev/null 2>&1 && nmcli con delete lab36test >/dev/null 2>&1

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 36a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 36a Checklist

- [ ] Task 1 completed (`nmcli con add` + `nmcli con mod` on `lab36test` dummy profile)
- [ ] Task 2 completed (`con up` + `dev status` + `con down` + delete cleanup)
- [ ] T36-A and T36-B trap behavior explained in your notes
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
