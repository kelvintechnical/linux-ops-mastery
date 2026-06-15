# Lab 35b: Text-Based Network Config (Ansible) — declarative profiles + hostname

**Series:** linux-ops-mastery — Networking · **Lab 35b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (network & hostname modules), RHCSA EX200 (the profiles `nmtui` writes), SRE (fleet-wide network config)  
**Prerequisite:** [Lab 35a](../lab-35a-nmtui-tui-config-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `community.general.nmcli` (from Lab 31) | _Task 1 · Step 1_ |
| A2 | idempotence (`changed=0`) | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `nmcli` module via TUI-equivalent | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `dns4` / multiple settings | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `ansible.builtin.hostname` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | verify hostname (`command: hostnamectl`) | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Do declaratively what `nmtui` does interactively. `nmtui` "Edit a connection" maps to `community.general.nmcli`; `nmtui` "Set system hostname" maps to `ansible.builtin.hostname`. You'll build a connection profile and set the hostname in a repeatable, idempotent play — the scalable replacement for clicking through a TUI on each box.

> **Safety note:** All work targets a throwaway **dummy** profile (`lab-tui` on `dummy0`). Teardown removes it.

---

## 🧠 Concept

`nmtui` is great for one box, but it can't scale or be version-controlled — that's where Ansible comes in. Each `nmtui` screen has a module counterpart: editing/activating a connection is `community.general.nmcli` (same `nmcli` backend, declarative `state:`), and "Set system hostname" is `ansible.builtin.hostname`. Because these modules are idempotent, re-running the play reports `changed=0` once the system matches the desired state — something a TUI can never guarantee. The mental model: **TUI screen → Ansible module → versioned, repeatable config**.

```
nmtui "Edit a connection"  ≈ community.general.nmcli (state: present)
nmtui "Activate"           ≈ nmcli module sets the profile up
nmtui "Set hostname"       ≈ ansible.builtin.hostname
re-run play                → changed=0 (idempotent)
```

> **Why this matters:** Configuring 50 servers through `nmtui` is error-prone and unrepeatable. The same intent in Ansible is one play applied to all hosts, idempotently, in source control.

---

## 📚 Command Reference

| Command | Purpose | Critical detail |
|---|---|---|
| `community.general.nmcli` | Manage connection | `conn_name`, `state:` |
| `method4: manual` | Static IPv4 | with `ip4:` |
| `ansible.builtin.hostname` | Set hostname | `name:` |
| `command: nmcli -g` | Verify field | `changed_when: false` |
| `command: hostnamectl` | Verify hostname | read-only |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox, playbook folder, and ensure the dummy module is available.

> Run this block **once** before Task 1.

```bash
export LAB_ROOT=/tmp/lab-35
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-35b/playbooks
sudo modprobe dummy 2>/dev/null || true
echo "ready"
echo "exit was: $?"
```

**Expected output:**

```
ready
exit was: 0
```

---

## TASK 1 of 2 — Profile as code (TUI "Edit a connection")

**In plain English:** We build and refine the dummy connection declaratively.

---

### Step 1 of 2 — Write the connection playbook

**In plain English:** We create `task1.yml` that defines the `lab-tui` profile — the `nmtui` editor as code.

```yaml
---
- name: "Lab 35b Task 1 — connection as code"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  tasks:
    - name: "Ensure lab-tui exists with a static IPv4"
      community.general.nmcli:
        conn_name: lab-tui
        ifname: dummy0
        type: dummy
        method4: manual
        ip4: 10.55.55.3/24
        dns4:
          - 10.55.55.53
        state: present
      register: nm
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `community.general.nmcli` → The declarative equivalent of `nmtui` "Edit a connection".
- `method4: manual` + `ip4:` → Static addressing, exactly what you'd type in the TUI's IPv4 screen.
- `state: present` → Create or update to match — idempotent.

**New words in this step:**

- **declarative profile** — describing the desired connection rather than clicking through screens.

---

### Step 2 of 2 — Run it twice to prove idempotence

**In plain English:** We apply the play, then re-run to confirm `changed=0`.

```bash
ansible-playbook /root/rhcsa_journal/lab-35b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-35b/playbooks/task1.yml | grep -E 'changed=|ok='
```

**Expected output:**

```
PLAY RECAP **********************************************************
localhost                  : ok=1    changed=1    unreachable=0    failed=0
localhost                  : ok=1    changed=0    unreachable=0    failed=0
```

**Line-by-line breakdown:**

- First run → `changed=1` (profile created/updated).
- Second run → `changed=0` (already matches) — the idempotence a TUI can't promise.

**New words in this step:**

- **idempotent config** — re-applying makes no change once state matches.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `nmcli` module | profile as code | needs collection |
| `state: present` | create/update | declarative |
| idempotence | no-op on match | `changed=0` |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Module not found | Collection missing | `ansible-galaxy collection install community.general` |
| Always changed | Param drift | Match all set fields |

---

## TASK 2 of 2 — Hostname as code (TUI "Set hostname")

**In plain English:** We set the hostname declaratively and verify it.

---

### Step 1 of 2 — Write the hostname playbook

**In plain English:** We create `task2.yml` using `ansible.builtin.hostname` — the `nmtui-hostname` screen as code.

```yaml
---
- name: "Lab 35b Task 2 — hostname as code"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  vars:
    desired_hostname: labhost.example.com
  tasks:
    - name: "Capture the current hostname (to restore later)"
      ansible.builtin.command: "hostnamectl --static status"
      register: before
      changed_when: false

    - name: "Set the static hostname"
      ansible.builtin.hostname:
        name: "{{ desired_hostname }}"
      register: hn

    - name: "Report old vs new"
      ansible.builtin.debug:
        msg: "was '{{ before.stdout }}', now '{{ desired_hostname }}' (changed: {{ hn.changed }})"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `command: hostnamectl --static status` → Records the old hostname first so teardown can restore it.
- `ansible.builtin.hostname: name:` → Sets the static hostname — the `nmtui-hostname` equivalent.

**New words in this step:**

- **`ansible.builtin.hostname`** — module that sets the system hostname declaratively.

---

### Step 2 of 2 — Run it and verify

**In plain English:** We run the play and confirm the hostname changed.

```bash
ansible-playbook /root/rhcsa_journal/lab-35b/playbooks/task2.yml
hostnamectl --static status
echo "exit was: $?"
```

**Expected output:**

```
TASK [Report old vs new] ***********************************************
ok: [localhost] => {"msg": "was 'oldname', now 'labhost.example.com' (changed: True)"}
labhost.example.com
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Applies the hostname and reports the before/after.
- `hostnamectl --static status` → Confirms the static hostname is now set.

> **Reset note:** Teardown restores your original hostname.

**New words in this step:**

- **static hostname** — the persistent name (vs transient/runtime).

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `hostname` module | set name | static persists |
| capture before | enables restore | save old value |
| verify | `hostnamectl` | confirm result |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Permission denied | No `become` | Add `become: true` |
| Reverts on reboot | Transient set | Module sets static (ok) |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the connection playbook
- [ ] Task 1 · Step 2 — Run it twice to prove idempotence
- [ ] Task 2 · Step 1 — Write the hostname playbook
- [ ] Task 2 · Step 2 — Run it and verify
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + dummy profile + hostname restored

---

## 🧹 Teardown

**In plain English:** Remove the dummy profile, restore the hostname, and clear the sandbox.

> This lab changed network and hostname state — all reversed here.

```bash
sudo nmcli con down lab-tui 2>/dev/null || true
sudo nmcli con delete lab-tui 2>/dev/null || true
# Restore your original hostname (replace with the value captured in Task 2):
# sudo hostnamectl set-hostname your-original-hostname
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-35
rm -rf /root/rhcsa_journal/lab-35b
```

**Expected output:**

```
Connection 'lab-tui' (...) successfully deleted.
✅ Removed /tmp/lab-35 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Missing collection | `nmcli` module errors | Install `community.general` |
| No `become` | Permission denied | Add `become: true` |
| Not capturing old hostname | Can't restore | Save it before changing |

---

## 📌 Exam Strategy

Map TUI screens to modules: connection → `community.general.nmcli`, hostname → `ansible.builtin.hostname`. The win over `nmtui` is idempotence and scale — re-running yields `changed=0`.

- `nmcli` module = `nmtui` "Edit/Activate" as code.
- `hostname` module = `nmtui-hostname` as code.
- Capture state before changing so you can restore it.

---

## 🔗 Related Labs

- [Lab 35a — Text-Based Network Config (RHCSA)](../lab-35a-nmtui-tui-config-rhcsa/) — the `nmtui` screens these modules replace
- [Lab 35c — Text-Based Network Config (Verify)](../lab-35c-nmtui-tui-config-verify/) — prove the profile and hostname
- [Lab 36b — Command-Line Network Config (Ansible)](../lab-36b-nmcli-cli-config-ansible/) — deeper `nmcli` module options

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
