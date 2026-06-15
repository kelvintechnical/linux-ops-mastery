# Lab 31b: Configure a Static IP (Ansible) — `community.general.nmcli`

**Series:** linux-ops-mastery — Networking · **Lab 31b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (idempotent network configuration), RHCSA EX200 (the `nmcli` work), DevOps (declarative host networking)  
**Prerequisite:** [Lab 31a](../lab-31a-static-ip-nmcli-rhcsa/) completed and a working control node · **root/sudo required**  
**Time Estimate:** 30–40 minutes  
**Difficulty:** Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `nmcli` profiles | _Task 1 · Step 1_ |
| A2 | idempotence (`changed=0`) | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `community.general.nmcli` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `type: dummy` + `conn_name:` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `ip4:`/`gw4:`/`dns4:` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N4 | `state: absent` removal | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

Manage a static IP declaratively with the `community.general.nmcli` module. You will create a dummy-interface profile with a static IPv4 config, prove a re-run is `changed=0`, then update and finally remove it with `state: absent`. The module is the idempotent automation of every `nmcli con add/mod/up/delete` from Lab 31a — safely on a dummy device.

> **⚠️ System-state lab.** Operates only on a `dummy0` device and `lab-static` profile; the real NIC is untouched. Teardown removes both. Use a practice VM.

---

## 🧠 Concept

`community.general.nmcli` wraps NetworkManager declaratively. You describe the desired profile — `conn_name`, `ifname`, `type`, `ip4`, `gw4`, `dns4`, `method4` — and the module reconciles it: creating, modifying, or leaving it alone, reporting `changed=0` when it already matches. `state: present` ensures the profile exists and is configured; `state: absent` deletes it. This replaces the imperative `con add`/`con mod`/`con delete` sequence with one idempotent task. We keep `type: dummy` so it's safe to run repeatedly without touching production interfaces.

```
RHCSA (31a)                          ANSIBLE (31b)
─────────────────────────────       ──────────────────────────────────────
nmcli con add ... ipv4.method manual nmcli: conn_name=lab-static type=dummy
nmcli con mod ... ipv4.gateway         ip4=10.99.99.2/24 gw4=... dns4=... state=present
nmcli con delete                     nmcli: conn_name=lab-static state=absent
```

> **Why this matters:** RHCE network tasks must be idempotent. The `nmcli` module gives you create/modify/remove in one declarative step, with `changed=0` proving convergence — exactly what the exam and real fleets need.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `community.general.nmcli` | Manage a profile | `conn_name:`, `type:`, `state:` |
| `ip4:` / `gw4:` / `dns4:` | Static IPv4 settings | manual addressing |
| `method4: manual` | Static method | vs `auto` |
| `state: present/absent` | Ensure/remove | declarative |
| `register:` + re-run | Prove idempotence | `changed=0` |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Ensure the dummy module and playbook folder are ready.

> Run this block **once** before Task 1. `LAB_ROOT` is a Teardown marker; the real changes are the profile/device, removed in Teardown.

```bash
export LAB_ROOT=/tmp/lab-31
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-31b/playbooks
sudo modprobe dummy 2>/dev/null || true
ansible-galaxy collection list 2>/dev/null | grep -i community.general || echo "install community.general if missing"
echo "exit was: $?"
```

**Expected output:**

```
community.general    ...
exit was: 0
```

---

## TASK 1 of 2 — Create the profile idempotently

**In plain English:** We declare the static profile and prove a re-run changes nothing.

---

### Step 1 of 2 — Write the nmcli playbook

**In plain English:** We create `task1.yml`, which ensures the `lab-static` dummy profile exists with a static IP.

```yaml
---
- name: "Lab 31b Task 1 — static IP on a dummy interface"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  tasks:
    - name: "Ensure the lab-static profile exists (static IPv4)"
      community.general.nmcli:
        conn_name: lab-static
        ifname: dummy0
        type: dummy
        method4: manual
        ip4: 10.99.99.2/24
        gw4: 10.99.99.1
        dns4:
          - 10.99.99.53
        state: present
      register: nm_result

    - name: "Show whether anything changed"
      ansible.builtin.debug:
        msg: "changed: {{ nm_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `community.general.nmcli: conn_name/type: dummy` → Declare a safe dummy profile.
- `method4: manual`, `ip4/gw4/dns4` → The full static IPv4 configuration.
- `state: present` → Ensure it exists and matches; idempotent.

**New words in this step:**

- **`community.general.nmcli`** — declarative NetworkManager profile management.

---

### Step 2 of 2 — Run it twice and watch `changed=0`

**In plain English:** We run the play twice; the profile is created once and then already matches.

```bash
ansible-playbook /root/rhcsa_journal/lab-31b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-31b/playbooks/task1.yml
nmcli -g ipv4.addresses con show lab-static
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP (run 1) : ok=2  changed=1  ...
PLAY RECAP (run 2) : ok=2  changed=0  ...
10.99.99.2/24
exit was: 0
```

**Line-by-line breakdown:**

- two runs → `changed=1` then `changed=0`: the module converges to the declared profile.
- `nmcli -g ipv4.addresses con show lab-static` → Confirms the static address is set.

**New words in this step:**

- **declarative networking** — describing the desired profile rather than running `con add/mod`.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `nmcli` module | manage profile | wraps `nmcli` |
| `method4: manual` | static | `auto` = DHCP |
| idempotent | re-run `changed=0` | matches existing |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Module not found | Collection missing | Install `community.general` |
| Always `changed` | dns4 type mismatch | Use a list for `dns4` |

---

## TASK 2 of 2 — Update and remove

**In plain English:** We change a setting, then remove the profile with `state: absent`.

---

### Step 1 of 2 — Write the update/remove playbook

**In plain English:** We create `task2.yml`, which first updates DNS, then (commented step) shows the removal with `state: absent`.

```yaml
---
- name: "Lab 31b Task 2 — update then remove the profile"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  tasks:
    - name: "Update the DNS server on lab-static"
      community.general.nmcli:
        conn_name: lab-static
        type: dummy
        method4: manual
        ip4: 10.99.99.2/24
        dns4:
          - 10.99.99.54
        state: present
      register: upd

    - name: "Show the change status"
      ansible.builtin.debug:
        msg: "changed: {{ upd.changed }}"

    - name: "Remove the profile (cleanup demo)"
      community.general.nmcli:
        conn_name: lab-static
        type: dummy
        state: absent
      register: rm
      # Comment this task out if you want to keep the profile for Lab 31c.
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- update task → Re-declares the profile with a new `dns4`; only the DNS change is `changed`.
- `state: absent` → Deletes the profile — the declarative `nmcli con delete`.

**New words in this step:**

- **`state: absent`** — declaratively remove a connection profile.

---

### Step 2 of 2 — Run it and confirm removal

**In plain English:** We run the play and confirm the profile was updated then removed.

```bash
ansible-playbook /root/rhcsa_journal/lab-31b/playbooks/task2.yml
nmcli con show | grep -q lab-static && echo "still present" || echo "REMOVED (OK)"
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP : ok=3  changed=2  ...
REMOVED (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Update DNS (changed) then delete the profile (changed).
- `nmcli con show | grep -q lab-static` → No match confirms removal.

**New words in this step:**

- **declarative removal** — deleting infrastructure by declaring it absent.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| update via present | reconcile change | only diff is changed |
| `state: absent` | delete profile | idempotent removal |
| cleanup | leaves no trace | safe re-runs |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Profile lingers | `absent` task skipped | Run/uncomment it |
| Update no-op | Same value | Change the value to see `changed` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the nmcli playbook
- [ ] Task 1 · Step 2 — Run it twice and watch `changed=0`
- [ ] Task 2 · Step 1 — Write the update/remove playbook
- [ ] Task 2 · Step 2 — Run it and confirm removal
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + **profile and dummy interface removed**

---

## 🧹 Teardown

**In plain English:** Ensure the test profile and dummy interface are gone, then delete the sandbox.

> This lab changed system state. These commands **reverse** it (idempotent even if Task 2 already removed the profile).

```bash
sudo nmcli con delete lab-static 2>/dev/null || true
sudo ip link delete dummy0 2>/dev/null || true
nmcli con show | grep -q lab-static && echo "still present (FAIL)" || echo "lab-static removed"
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-31
rm -rf /root/rhcsa_journal/lab-31b
```

**Expected output:**

```
lab-static removed
✅ Removed /tmp/lab-31 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `dns4` as string | Always `changed` | Use a YAML list |
| Missing collection | Module not found | Install `community.general` |
| Real NIC in `ifname` | Lose connectivity | Keep `type: dummy`/`dummy0` |

---

## 📌 Exam Strategy

Use `community.general.nmcli` for idempotent static-IP config: declare `method4: manual` with `ip4`/`gw4`/`dns4`, use `state: present`/`absent`, and re-run to confirm `changed=0`. It's the automation of the whole Lab 31a workflow.

- `dns4` is a list, not a string.
- `state: absent` for clean, idempotent removal.
- Re-run to prove convergence.

---

## 🔗 Related Labs

- [Lab 31a — Configure a Static IP (RHCSA)](../lab-31a-static-ip-nmcli-rhcsa/) — the `nmcli` this automates
- [Lab 31c — Configure a Static IP (Verify)](../lab-31c-static-ip-nmcli-verify/) — prove the address and persistence
- [Lab 33b — Display IP and Routing Info (Ansible)](../lab-33b-ip-addr-route-show-ansible/) — reading network facts

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
