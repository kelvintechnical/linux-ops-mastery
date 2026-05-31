# Lab 39a: Configure SSH Key-Based Authentication (RHCSA) — `ssh-keygen`, `ssh-copy-id`, `authorized_keys`

- **Series:** linux-ops-mastery — SSH Access and Authentication
- **Trilogy:** `39a` (RHCSA hand-typed) -> `39b` (Ansible mirror) -> `39c` (Verify capstone)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation #39):** `/lib64`
- **Sandbox (Tier B):** `/tmp/lab39a` with `USER=labuser_39_sshkey`, `GROUP=labgrp_39_sshkey`
- **Traps rehearsed this lab:** **T39-A** (`~/.ssh` permission drift causes silent key auth failure) · **T39-B** (`ssh-copy-id` without `-i` can install wrong key) · **T41** · **T44**

> **Prerequisite:** `sshd` must be running on localhost before testing key login (`systemctl status sshd`).

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /lib64"
echo "⚠️  TRAP REMINDERS THIS LAB: T39-A T39-B T41 T44"
ls -ld /lib64
systemctl is-active sshd 2>/dev/null || echo "sshd not active"
```

> **STOP — paste header output before setup.**

---

## Objective

1. Generate a dedicated SSH keypair for the Tier B lab user with `ssh-keygen -t ed25519`.
2. Deploy that exact public key to `~/.ssh/authorized_keys` on localhost.
3. Verify strict SSH permission model (`~/.ssh` = `700`, private key = `600`, `authorized_keys` = `600`).
4. Avoid trap T39-B by always using `ssh-copy-id -i`.

---

## Core Reference

| Command | Meaning |
|---|---|
| `ssh-keygen -t ed25519 -f KEY -N ''` | Create modern keypair with empty passphrase |
| `ssh-keygen -t rsa -b 4096 -f KEY -N ''` | Alternate keypair type for compatibility testing |
| `ssh-copy-id -i KEY.pub USER@HOST` | Install a specific public key into `authorized_keys` |
| `chmod 700 ~/.ssh` | Required directory permission for key auth |
| `chmod 600 ~/.ssh/authorized_keys` | Required key list permission |
| `ssh -i KEY USER@localhost true` | Non-interactive key login check |

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab39a
export GROUP=labgrp_39_sshkey
export USER=labuser_39_sshkey
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-39a/task1 /root/rhcsa_journal/lab-39a/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

sudo -u "${USER}" mkdir -p "${USER_HOME}/.ssh"
chmod 700 "${USER_HOME}/.ssh"
chown -R "${USER}:${GROUP}" "${USER_HOME}/.ssh"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" "${USER_HOME}/.ssh"
```

> **STOP — paste `id` and `ls -ld` outputs before Task 1.**

---

## Task 1 — Generate and permission-check the lab keypair

### Purpose

Create a dedicated Tier B key (`lab39_ed25519`) owned by `labuser_39_sshkey`, then validate all required permission bits before attempting authentication.

### Main command block

```bash
TASKLOG=/tmp/lab39a/task1.txt

sudo -u "${USER}" ssh-keygen -t ed25519 -f "${USER_HOME}/.ssh/lab39_ed25519" -N '' 2>&1 | tee "${TASKLOG}"

chmod 700 "${USER_HOME}/.ssh"
chmod 600 "${USER_HOME}/.ssh/lab39_ed25519"
chmod 644 "${USER_HOME}/.ssh/lab39_ed25519.pub"

stat -c '%a %U:%G %n' "${USER_HOME}/.ssh"                       | tee -a "${TASKLOG}"
stat -c '%a %U:%G %n' "${USER_HOME}/.ssh/lab39_ed25519"         | tee -a "${TASKLOG}"
stat -c '%a %U:%G %n' "${USER_HOME}/.ssh/lab39_ed25519.pub"     | tee -a "${TASKLOG}"
sudo -u "${USER}" ssh-keygen -lf "${USER_HOME}/.ssh/lab39_ed25519.pub" | tee -a "${TASKLOG}"

echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Trap callout

- **T39-A:** wrong perms on `~/.ssh` or key files cause key rejection with little/no obvious error server-side.
- Keep this reflex: `700` on `.ssh`, `600` on private key, `600` on `authorized_keys`.

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-39a/task1
cp /tmp/lab39a/task1.txt "${JDIR}/evidence.txt"
```

---

## Task 2 — Deploy key to localhost and verify key login

### Purpose

Install the exact public key with `ssh-copy-id -i` (or manual append path), then prove passwordless login as the same Tier B user on localhost.

### Main command block

```bash
TASKLOG=/tmp/lab39a/task2.txt

# Prefer explicit -i to avoid T39-B when multiple keys exist
ssh-copy-id -i "${USER_HOME}/.ssh/lab39_ed25519.pub" "${USER}@localhost" 2>&1 | tee "${TASKLOG}" || true

# If ssh-copy-id is unavailable/blocked, manual fallback:
sudo -u "${USER}" bash -c 'cat "'"${USER_HOME}"'/.ssh/lab39_ed25519.pub" >> "'"${USER_HOME}"'/.ssh/authorized_keys"'

chmod 700 "${USER_HOME}/.ssh"
chmod 600 "${USER_HOME}/.ssh/authorized_keys"
chown -R "${USER}:${GROUP}" "${USER_HOME}/.ssh"

stat -c '%a %U:%G %n' "${USER_HOME}/.ssh"                    | tee -a "${TASKLOG}"
stat -c '%a %U:%G %n' "${USER_HOME}/.ssh/authorized_keys"    | tee -a "${TASKLOG}"
sudo -u "${USER}" ssh -i "${USER_HOME}/.ssh/lab39_ed25519" \
  -o PreferredAuthentications=publickey \
  -o PasswordAuthentication=no \
  -o StrictHostKeyChecking=accept-new \
  "${USER}@localhost" true                                    2>&1 | tee -a "${TASKLOG}"

echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Trap callout

- **T39-B:** `ssh-copy-id ${USER}@localhost` may install `id_rsa.pub` or another default key instead of your lab key.
- Use `ssh-copy-id -i "${USER_HOME}/.ssh/lab39_ed25519.pub" ...` every time.

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-39a/task2
cp /tmp/lab39a/task2.txt "${JDIR}/evidence.txt"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# Cleanup generated keys before user removal
rm -f "${USER_HOME}/.ssh/lab39_ed25519" \
      "${USER_HOME}/.ssh/lab39_ed25519.pub" \
      "${USER_HOME}/.ssh/authorized_keys"

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 39a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 39a Checklist

- [ ] Task 1 completed (`ssh-keygen -t ed25519` run as `labuser_39_sshkey`, key perms validated)
- [ ] Task 2 completed (`ssh-copy-id -i` used or manual append done, `ssh -i ... true` succeeded)
- [ ] T39-A and T39-B trap notes captured in evidence
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
