# Lab 36b: Command-Line Network Config with Ansible `community.general.nmcli`

- **Series:** linux-ops-mastery — Network Configuration and Verification
- **Trilogy:** `36a` (RHCSA) -> `36b` (Ansible) -> `36c` (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation slot 1):** `/bin`
- **Sandbox (Tier B):** `/tmp/lab36b` with `USER=labuser_36_nmcli`, `GROUP=labgrp_36_nmcli`
- **Playbooks live at:** `/root/rhcsa_journal/lab-36b/playbooks/`
- **Traps rehearsed this lab:** **T36-A** · **T36-B** · **T41** · **T44**

> **Safety rule (hard):** manage only the test profile `lab36test` on dummy interface `dummy-lab36`. Never touch your active management profile from automation.

---

## LAB HEADER BLOCK

```bash
echo "📦 OS: $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒 TIME: $(date -Is)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "📁 PRACTICE DIR: /bin"
echo "⚠️ TRAPS: T36-A T36-B T41 T44"
ansible --version | head -n 2
ansible-galaxy collection list | grep community.general || true
nmcli --version
```

---

## Objective

Mirror the RHCSA flow with idempotent Ansible:

1. Use the FQCN `community.general.nmcli` to create/modify `lab36test`.
2. Run check/diff to prove declarative idempotence.
3. Assert runtime state is `activated` to block T36-A regressions.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab36b
export GROUP=labgrp_36_nmcli
export USER=labuser_36_nmcli
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-36b/playbooks
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Build test profile with `community.general.nmcli` and prove idempotence

### Purpose

Define the same connection as 36a using module-first automation and verify repeatability.

### Playbook (`/root/rhcsa_journal/lab-36b/playbooks/task1.yml`)

```yaml
---
- name: "Lab 36b Task 1 - create lab36test profile safely"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Create/modify dummy test connection"
      community.general.nmcli:
        conn_name: lab36test
        ifname: dummy-lab36
        type: dummy
        ip4: 10.99.0.1/24
        method4: manual
        state: present

    - name: "Show resulting profile"
      ansible.builtin.command:
        cmd: nmcli con show lab36test
      changed_when: false
```

### Run with check/diff

```bash
ansible-galaxy collection install community.general

ansible-playbook /root/rhcsa_journal/lab-36b/playbooks/task1.yml --check --diff 2>&1 | tee /tmp/lab36b/task1-check.txt
ansible-playbook /root/rhcsa_journal/lab-36b/playbooks/task1.yml --diff          2>&1 | tee /tmp/lab36b/task1-apply-1.txt
ansible-playbook /root/rhcsa_journal/lab-36b/playbooks/task1.yml --diff          2>&1 | tee /tmp/lab36b/task1-apply-2.txt
```

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-36b/task1
cp /tmp/lab36b/task1-check.txt   /root/rhcsa_journal/lab-36b/task1/check.txt
cp /tmp/lab36b/task1-apply-1.txt /root/rhcsa_journal/lab-36b/task1/apply-1.txt
cp /tmp/lab36b/task1-apply-2.txt /root/rhcsa_journal/lab-36b/task1/apply-2.txt
```

---

## Task 2 — Trap T36-A guard: assert profile is activated

### Purpose

Prevent "saved but not applied" drift by requiring active state verification.

### Playbook (`/root/rhcsa_journal/lab-36b/playbooks/task2.yml`)

```yaml
---
- name: "Lab 36b Task 2 - ensure lab36test is activated"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Bring connection up"
      ansible.builtin.command:
        cmd: nmcli con up lab36test
      changed_when: false

    - name: "Query connection state"
      ansible.builtin.command:
        cmd: nmcli -t -f GENERAL.STATE con show lab36test
      register: con_state
      changed_when: false

    - name: "Assert activated state (T36-A guard)"
      ansible.builtin.assert:
        that:
          - "'activated' in con_state.stdout"
        fail_msg: "T36-A: profile exists but is not activated."
        success_msg: "lab36test is activated."
```

### Run and inspect

```bash
ansible-playbook /root/rhcsa_journal/lab-36b/playbooks/task2.yml 2>&1 | tee /tmp/lab36b/task2-apply.txt
nmcli dev status                                                 2>&1 | tee -a /tmp/lab36b/task2-apply.txt
```

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-36b/task2
cp /tmp/lab36b/task2-apply.txt /root/rhcsa_journal/lab-36b/task2/evidence.txt
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

nmcli con show lab36test >/dev/null 2>&1 && nmcli con down lab36test >/dev/null 2>&1
nmcli con show lab36test >/dev/null 2>&1 && nmcli con delete lab36test >/dev/null 2>&1

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 36b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 36b Checklist

- [ ] Task 1 completed (`community.general.nmcli` built `lab36test`; check/diff and second apply confirm idempotence)
- [ ] Task 2 completed (activation assertion passed; T36-A guarded)
- [ ] Test-only profile safety rule followed (T36-B)
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
