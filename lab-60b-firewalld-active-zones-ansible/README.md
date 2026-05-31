# Lab 60b: Inspect Active Firewall Zones with Ansible — query + assert

- **Series:** linux-ops-mastery — Network Security and Service Access
- **Trilogy:** [`60a`](../lab-60a-firewalld-active-zones-rhcsa/) (RHCSA) -> `60b` (Ansible) -> [`60c`](../lab-60c-firewalld-active-zones-verify/) (Verify)
- **Topic:** Ansible-driven active-zone inspection and policy assertions
- **Distinct from Lab 56:** This lab is not broad zone tour work; it targets active-zone-with-interface evidence and runtime/permanent comparison checks.
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (ADHD format)
- **Practice Directory:** `/usr` (inspection context)
- **Sandbox (Tier B):** `/tmp/lab60b`, `USER=labuser_60_fwactive`, `GROUP=labgrp_60_fwactive`
- **Playbooks live at:** `/root/rhcsa_journal/lab-60b/playbooks/`
- **Traps rehearsed this lab:** **T60-A** · **T60-B** · **T41** · **T44**

> Read-only inspection only. No firewall rule or zone mutation is allowed in this lab.

---

## LAB HEADER BLOCK

```bash
echo "OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "TIME:  $(date -Is)"
echo "USER:  $(whoami)@$(hostname)"
echo "PRACTICE DIR: /usr"
echo "TRAPS: T60-A T60-B T41 T44"
ansible --version | head -n 2
systemctl is-active firewalld 2>/dev/null || echo "firewalld inactive"
firewall-cmd --state 2>/dev/null || true
ls -ld /usr
```

---

## Objective

1. Query active zones through Ansible with module-or-shell boundary honesty.
2. Assert that default zone appears in active-zone output.
3. Capture runtime and permanent snapshots in machine-readable playbook evidence.

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export SANDBOX=/tmp/lab60b
export GROUP=labgrp_60_fwactive
export USER=labuser_60_fwactive
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-60b/playbooks /root/rhcsa_journal/lab-60b/task1 /root/rhcsa_journal/lab-60b/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 - Query active zones (module-aware fallback with register)

### Purpose

Use Ansible to gather active zone facts. Prefer query-safe behavior and keep mutation risk at zero.

### Playbook (`/root/rhcsa_journal/lab-60b/playbooks/task1.yml`)

```yaml
---
- name: "Lab 60b Task 1 - query active zones safely"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Query active zones via firewall-cmd (read-only)"
      ansible.builtin.shell: firewall-cmd --get-active-zones
      register: active_zones
      changed_when: false

    - name: "Query default zone"
      ansible.builtin.shell: firewall-cmd --get-default-zone
      register: default_zone
      changed_when: false

    - name: "Query runtime all-zones (scoped for T60-A safety)"
      ansible.builtin.shell: firewall-cmd --list-all-zones | head -n 40
      register: runtime_zones_head
      changed_when: false

    - name: "Query permanent all-zones (scoped for T60-A safety)"
      ansible.builtin.shell: firewall-cmd --permanent --list-all-zones | head -n 40
      register: permanent_zones_head
      changed_when: false

    - name: "Emit gathered evidence"
      ansible.builtin.debug:
        msg:
          active: "{{ active_zones.stdout_lines }}"
          default: "{{ default_zone.stdout }}"
          runtime_head: "{{ runtime_zones_head.stdout_lines }}"
          permanent_head: "{{ permanent_zones_head.stdout_lines }}"
```

> Boundary note: `ansible.posix.firewalld` is mutation-oriented in many environments; for strict read-only active-zone inspection, `shell + register + changed_when: false` is the honest pattern.

### Run and capture

```bash
ansible-playbook /root/rhcsa_journal/lab-60b/playbooks/task1.yml 2>&1 | tee /tmp/lab60b/task1-apply.txt
```

### Journal write

```bash
cp /tmp/lab60b/task1-apply.txt /root/rhcsa_journal/lab-60b/task1/evidence.txt
```

---

## Task 2 - Assert default zone is present in active-zone output

### Purpose

Automate the core health check: default zone should be visible among active zones on correctly bound hosts.

### Playbook (`/root/rhcsa_journal/lab-60b/playbooks/task2.yml`)

```yaml
---
- name: "Lab 60b Task 2 - assert default zone in active zones"
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: "Get active zones output"
      ansible.builtin.shell: firewall-cmd --get-active-zones
      register: active_zones
      changed_when: false

    - name: "Get default zone"
      ansible.builtin.shell: firewall-cmd --get-default-zone
      register: default_zone
      changed_when: false

    - name: "Assert default zone appears in active output"
      ansible.builtin.assert:
        that:
          - default_zone.stdout in active_zones.stdout
        fail_msg: "Default zone is not shown as active. Review interface binding and firewalld state."
        success_msg: "Default zone appears in active-zone output."

    - name: "Show runtime/permanent public zone compare (T60-B evidence)"
      ansible.builtin.shell: |
        echo "== runtime public =="
        firewall-cmd --info-zone=public
        echo "== permanent public =="
        firewall-cmd --permanent --info-zone=public
      register: public_compare
      changed_when: false

    - name: "Emit compare block"
      ansible.builtin.debug:
        var: public_compare.stdout_lines
```

### Run and capture

```bash
ansible-playbook /root/rhcsa_journal/lab-60b/playbooks/task2.yml 2>&1 | tee /tmp/lab60b/task2-apply.txt
```

### Trap callouts

- **T60-A:** Keep `--list-all-zones` scoped (`head`, `less`) inside playbooks too.
- **T60-B:** Assertion can pass while runtime/permanent still differ; always capture both snapshots.

### Journal write

```bash
cp /tmp/lab60b/task2-apply.txt /root/rhcsa_journal/lab-60b/task2/evidence.txt
```

---

## Lab Closeout - Section 6 Teardown

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi
rm -rf "${SANDBOX}"

echo "-- lab-60b cleanup audit --"
getent passwd "${USER}" >/dev/null && echo "FAIL user remains" || echo "OK user gone"
getent group  "${GROUP}" >/dev/null && echo "FAIL group remains" || echo "OK group gone"
test -d "${SANDBOX}" && echo "FAIL sandbox remains" || echo "OK sandbox gone"
test -d "${USER_HOME}" && echo "FAIL home remains" || echo "OK home gone"

set -e
```

---

## Checklist

- [ ] Task 1 completed (active zones/default zone/runtime+permanent scoped snapshots captured with `register`)
- [ ] Task 2 completed (assert default zone in active output and captured runtime/permanent compare)
- [ ] T60-A and T60-B documented in evidence
- [ ] Section 6 closeout audit shows all `OK`

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
