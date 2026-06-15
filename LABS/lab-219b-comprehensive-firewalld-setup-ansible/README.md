# Lab 219b: Comprehensive firewalld Setup (Ansible) — `ansible.posix.firewalld`, handlers

**Series:** linux-ops-mastery — Security Administration · **Lab 219b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (`ansible.posix.firewalld`, handlers, `creates:` guards), RHCSA EX200 (the `firewall-cmd` behavior underneath), SRE/DevOps (declarative host firewalling at fleet scale)  
**Prerequisite:** [Lab 219a](../lab-219a-comprehensive-firewalld-setup-rhcsa/) completed, a working Ansible control node, and the `ansible.posix` collection (`ansible-galaxy collection install ansible.posix`)  
**Time Estimate:** 30–40 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Rebuild Lab 219a's complete bastion-zone firewall policy as an idempotent Ansible play using the real `ansible.posix.firewalld` module. You will create a dedicated throwaway `bastion` zone (guarded so it is only created once), then declare named services, a raw port, an ICMP block, masquerade, and a source-scoped rich rule — every one with `permanent: true` *and* `immediate: true` so runtime and on-disk state stay in sync. You will see how a handler runs `firewall-cmd --reload` exactly once, and prove the whole play converges to `changed=0` on a second run.

---

## 🧠 Concept

In the shell you repeat `firewall-cmd --permanent ... ; firewall-cmd --reload`. The `ansible.posix.firewalld` module collapses that into one state-aware task: `permanent: true` writes to disk, `immediate: true` also applies it to the running firewall, and `state: enabled/disabled` says whether the rule should exist. Because the module checks current state first, re-declaring a rule that is already present reports `changed=0` — the idempotence graders look for. Zone *creation* has no native module parameter, so we shell out once with `ansible.builtin.command` guarded by `creates:` (skip if the zone XML already exists) and use a **handler** + `meta: flush_handlers` to reload firewalld immediately so the zone exists before any rule targets it.

```
SHELL (219a)                                  ANSIBLE (219b)
──────────────────────────────────────        ──────────────────────────────────────────
firewall-cmd --permanent --new-zone=bastion   command: firewall-cmd --permanent --new-zone=bastion
firewall-cmd --reload                            args: { creates: /etc/firewalld/zones/bastion.xml }

firewall-cmd --permanent --add-service=ssh    ansible.posix.firewalld:
firewall-cmd --reload                            zone: bastion
                                                 service: ssh
                                                 permanent: true
                                                 immediate: true       ← runtime too
                                                 state: enabled        → changed=1 then 0
```

> **Why this matters:** A firewall task that is not idempotent re-applies (and re-logs) every run, and one that sets only `permanent` without `immediate` leaves runtime and disk out of sync until a reload. Mastering `permanent + immediate + state` is the difference between a play that *converges* a fleet's firewall and one that drifts.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.posix.firewalld` | Declaratively manage zones' services/ports/rules | `permanent:`, `immediate:`, `state:`, `zone:` |
| `ansible.builtin.command` + `creates:` | Create the zone once (no native module param) | `args: creates:` skips the task if the file exists |
| `ansible.builtin.meta: flush_handlers` | Force queued handlers to run *now* | makes the zone exist before rules are added |
| handler (`firewall-cmd --reload`) | Reload firewalld once after notifying tasks | `changed_when: true` so the notify fires |
| `ansible-playbook` | Run a playbook | run it **twice** to test idempotence |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Confirm Ansible and the `ansible.posix` collection are present, create the durable playbook folder under `/root`, and define the `/tmp` sandbox root; the only firewall change is the dedicated `bastion` zone the plays manage.

> Run this block **once** before Task 1. It builds the clean, private
> workspace that both tasks depend on.

```bash
sudo -i

export LAB_ROOT=/tmp/lab-219
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-219b/playbooks

ansible --version | head -2
ansible-galaxy collection list ansible.posix | grep ansible.posix \
  || ansible-galaxy collection install ansible.posix
ls -ld "$LAB_ROOT" /root/rhcsa_journal/lab-219b/playbooks
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
ansible [core 2.16.x]
  config file = /etc/ansible/ansible.cfg
ansible.posix 1.5.4
drwxr-xr-x. 2 root root 6 Jun 15 17:45 /tmp/lab-219
drwxr-xr-x. 2 root root 6 Jun 15 17:45 /root/rhcsa_journal/lab-219b/playbooks
Setup complete at 2026-06-15T17:45:08-04:00
exit was: 0
```

---

## TASK 1 of 2 — Zone, services, and a custom port (idempotent)

**In plain English:** We write a playbook that creates the throwaway `bastion` zone once, then declares the `ssh` and `http` services and the raw `8080/tcp` port into it, and run it twice to watch the second run report `changed=0`.

---

### Step 1 of 2 — Write the zone-and-services playbook

**In plain English:** We create `task1.yml`, which creates the zone (guarded by `creates:`), flushes a reload handler so the zone is live, then loops `ansible.posix.firewalld` over the services and adds the custom port — all `permanent: true` and `immediate: true`.

```yaml
---
- name: "Lab 219b Task 1 — services + custom port in bastion zone"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  vars:
    fw_zone: bastion
  tasks:
    - name: "Create the dedicated throwaway zone (permanent)"
      ansible.builtin.command: firewall-cmd --permanent --new-zone={{ fw_zone }}
      args:
        creates: "/etc/firewalld/zones/{{ fw_zone }}.xml"
      notify: reload firewalld

    - name: "Flush handlers so the zone exists before we add rules"
      ansible.builtin.meta: flush_handlers

    - name: "Allow named services ssh and http (permanent + runtime)"
      ansible.posix.firewalld:
        zone: "{{ fw_zone }}"
        service: "{{ item }}"
        permanent: true
        immediate: true
        state: enabled
      loop:
        - ssh
        - http

    - name: "Allow raw custom port 8080/tcp (permanent + runtime)"
      ansible.posix.firewalld:
        zone: "{{ fw_zone }}"
        port: 8080/tcp
        permanent: true
        immediate: true
        state: enabled
  handlers:
    - name: reload firewalld
      ansible.builtin.command: firewall-cmd --reload
      changed_when: true
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.command: firewall-cmd --permanent --new-zone={{ fw_zone }}` with `args: creates:` → Create the zone once; the `creates:` guard skips this task entirely if `bastion.xml` already exists, making it idempotent despite being a raw command.
- `notify: reload firewalld` + `ansible.builtin.meta: flush_handlers` → Queue a reload and then force it to run *now*, so the new zone is loaded before any rule tries to target it.
- `ansible.posix.firewalld: service / permanent: true / immediate: true / state: enabled` looped over `ssh` and `http` → Add both named services to the zone in disk *and* runtime in one state-aware task.
- `port: 8080/tcp` task → Add the raw port the same way; `8080/tcp` has no named service, so we specify it literally.
- the `handlers:` block → Defines the single `firewall-cmd --reload` run, with `changed_when: true` so the notify always triggers it.

**New words in this step:**

- **`ansible.posix.firewalld`** — the module that manages firewalld zones, services, ports, and rich rules declaratively.
- **handler** — a task that runs only when notified, and only once per play, ideal for "reload after changes."
- **`creates:`** — a command-module guard that skips the task if the named file already exists (cheap idempotence).

---

### Step 2 of 2 — Run it twice and watch `changed=0` on the re-run

**In plain English:** We run the saved playbook two times; the first run creates the zone and adds the rules (`changed>=1`), and the second finds everything already present (`changed=0`), confirmed by `firewall-cmd --list-all`.

```bash
ansible-playbook /root/rhcsa_journal/lab-219b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-219b/playbooks/task1.yml
sudo firewall-cmd --zone=bastion --list-all
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP *********************************************************************
localhost                  : ok=5    changed=4    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=4    changed=0    unreachable=0    failed=0
bastion
  target: default
  services: http ssh
  ports: 8080/tcp
  masquerade: no
  rich rules:
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → First run creates the zone, reloads, and adds two services + the port; the recap shows several `changed`.
- second `ansible-playbook ...` → Second run: the `creates:` guard skips zone creation (so the reload handler does not fire) and every `firewalld` rule is already present, so `changed=0`.
- `sudo firewall-cmd --zone=bastion --list-all` → Confirm out-of-band that `services: http ssh` and `ports: 8080/tcp` are present in the live zone.

**New words in this step:**

- **PLAY RECAP** — Ansible's end-of-run summary of `ok`, `changed`, and `failed` counts per host.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `permanent: true` + `immediate: true` | writes disk AND runtime together | `permanent` alone leaves runtime out of sync until reload |
| `creates:` guard on `command` | makes a raw command idempotent | without it, `--new-zone` errors on the second run |
| `flush_handlers` | runs the reload before later tasks | skip it and rules may target a not-yet-loaded zone |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `ERROR ... firewalld` module not found | `ansible.posix` collection missing | `ansible-galaxy collection install ansible.posix` |
| `ZONE_CONFLICT` / zone already exists | `creates:` guard omitted | Add `args: creates: .../bastion.xml` to the create task |

---

## TASK 2 of 2 — ICMP block, masquerade, and a rich rule (idempotent)

**In plain English:** We extend the bastion zone declaratively — block ping, enable source NAT, and accept SSH only from one subnet via a rich rule — then prove the play converges to `changed=0`.

---

### Step 1 of 2 — Write the icmp/masquerade/rich-rule playbook

**In plain English:** We create `task2.yml`, which uses three `ansible.posix.firewalld` tasks — `icmp_block`, `masquerade`, and `rich_rule` — each `permanent: true` and `immediate: true`, so the harder rules are managed as declaratively as the simple ones.

```yaml
---
- name: "Lab 219b Task 2 — icmp block, masquerade, rich rule in bastion zone"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  vars:
    fw_zone: bastion
  tasks:
    - name: "Block ICMP echo-request / ping (permanent + runtime)"
      ansible.posix.firewalld:
        zone: "{{ fw_zone }}"
        icmp_block: echo-request
        permanent: true
        immediate: true
        state: enabled

    - name: "Enable masquerade / source NAT (permanent + runtime)"
      ansible.posix.firewalld:
        zone: "{{ fw_zone }}"
        masquerade: true
        permanent: true
        immediate: true
        state: enabled

    - name: "Accept SSH only from 192.0.2.0/24 via a rich rule"
      ansible.posix.firewalld:
        zone: "{{ fw_zone }}"
        rich_rule: rule family="ipv4" source address="192.0.2.0/24" service name="ssh" accept
        permanent: true
        immediate: true
        state: enabled
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `icmp_block: echo-request` task → Drop inbound ping for the zone via the module's `icmp_block` parameter (the declarative `--add-icmp-block`).
- `masquerade: true` task → Enable source NAT for forwarded traffic (the declarative `--add-masquerade`).
- `rich_rule: rule family="ipv4" ...` task → Add the source-scoped accept rule; the module takes the same rule string `firewall-cmd` uses, so it transfers your 219a knowledge directly. (No surrounding shell quotes are needed — YAML passes the value verbatim.)
- `permanent: true` + `immediate: true` on each → Keep disk and runtime in lockstep for every rule, and `state: enabled` makes each one idempotent.

**New words in this step:**

- **`rich_rule:`** — the firewalld module parameter that takes a full rich-rule string for fine-grained source/service/action logic.
- **source NAT (masquerade)** — rewriting forwarded packets to appear from the host's own IP so a private subnet can reach the outside.

---

### Step 2 of 2 — Run it twice and watch `changed=0` on the re-run

**In plain English:** We run the playbook twice; the first run adds the ICMP block, masquerade, and rich rule (`changed=3`), and the second finds them already set (`changed=0`), confirmed by `--list-all`.

```bash
ansible-playbook /root/rhcsa_journal/lab-219b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-219b/playbooks/task2.yml
sudo firewall-cmd --zone=bastion --list-all
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP *********************************************************************
localhost                  : ok=3    changed=3    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
bastion
  services: http ssh
  ports: 8080/tcp
  masquerade: yes
  icmp-blocks: echo-request
  rich rules:
	rule family="ipv4" source address="192.0.2.0/24" service name="ssh" accept
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → First run adds all three rules; `changed=3`.
- second `ansible-playbook ...` → Second run finds every rule already present, so it makes no change; `changed=0` — the idempotence proof for the complex rules.
- `sudo firewall-cmd --zone=bastion --list-all` → Confirm `masquerade: yes`, `icmp-blocks: echo-request`, and the rich rule are all live.

**New words in this step:**

- **convergence** — repeatedly applying a declarative play until the firewall holds the desired state, then reporting `changed=0`.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `icmp_block:` / `masquerade:` | declarative ICMP drop / source NAT | each is a distinct module param, not a service |
| `rich_rule:` | a full rich rule as a string | reuse the exact `firewall-cmd` rule text |
| idempotent complex rules | re-run is `changed=0` | proves convergence on the whole policy |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Rich rule re-applies every run | Rule string differs from stored form | Match the canonical `firewall-cmd` rule text exactly |
| `masquerade` shows `no` after the play | Targeted the wrong zone | Set `zone: bastion` on every task |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the zone-and-services playbook
- [ ] Task 1 · Step 2 — Run it twice and watch `changed=0` on the re-run
- [ ] Task 2 · Step 1 — Write the icmp/masquerade/rich-rule playbook
- [ ] Task 2 · Step 2 — Run it twice and watch `changed=0` on the re-run

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

This lab changed **system state** (it created a firewalld zone and rules), and `rm` does NOT undo firewall config. Because every rule lives in the dedicated `bastion` zone, deleting that one zone removes them all:

```bash
sudo firewall-cmd --permanent --delete-zone=bastion
sudo firewall-cmd --reload
sudo firewall-cmd --get-zones | tr ' ' '\n' | grep -x bastion || echo "bastion zone gone (OK)"
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-219
```

**Expected output:**

```
✅ Removed /tmp/lab-219 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Setting `permanent: true` without `immediate: true` | Disk and runtime drift until a reload | Set both so the rule is live and persistent |
| Re-creating the zone with no `creates:` guard | Second run errors on `--new-zone` | Add `args: creates: .../bastion.xml` |
| Editing the default/active zone | A bad rule can lock you out over SSH | Manage the dedicated `bastion` zone, never the live one |

---

## 📌 Exam Strategy

RHCE firewall questions reward declarative, idempotent policy. Reach for `ansible.posix.firewalld` with `permanent: true` *and* `immediate: true` so runtime and disk agree, guard any raw zone-creation command with `creates:`, and use a handler to reload once. Stage everything in a named zone you control and prove it with `--list-all` after a double run.

- Always pair `permanent: true` with `immediate: true` to avoid runtime/disk drift.
- Guard raw `firewall-cmd --new-zone` with `args: creates:` for idempotence.
- Reuse your exact `firewall-cmd` rich-rule string in the module's `rich_rule:`.

---

## 🔗 Related Labs

- [Lab 219a — Comprehensive firewalld Setup (RHCSA)](../lab-219a-comprehensive-firewalld-setup-rhcsa/) — the hand-typed `firewall-cmd` version this play mirrors
- [Lab 219c — Comprehensive firewalld Setup (Verify)](../lab-219c-comprehensive-firewalld-setup-verify/) — assert every rule is present with `firewall-cmd --list-all` greps
- [Lab 218b — Build a Bastion Server (Ansible)](../lab-218b-build-bastion-server-ansible/) — the host this firewall policy protects, hardened in Ansible

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
