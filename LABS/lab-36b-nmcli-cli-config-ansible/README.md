# Lab 36b: Command-Line Network Config (Ansible) — `community.general.nmcli`

**Series:** linux-ops-mastery — Networking · **Lab 36b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (network module mastery), RHCSA EX200 (the `nmcli` data underneath), SRE (fleet network config)  
**Prerequisite:** [Lab 36a](../lab-36a-nmcli-cli-config-rhcsa/) completed and a working control node  
**Time Estimate:** 30–40 minutes  
**Difficulty:** Intermediate

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
| N1 | `dns4` as a list | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `command: nmcli -g` verify | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `method4: auto` toggle | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `state: absent` removal | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Translate `nmcli`'s add/modify/activate workflow into idempotent Ansible. You'll declare a full static profile (address, gateway, DNS list) with `community.general.nmcli`, verify the stored fields, toggle the method to `auto`, and finally remove the profile with `state: absent`. The module handles the `+`/`-` list nuance for you — you just declare the desired end state.

> **Safety note:** All work targets a throwaway **dummy** profile (`lab-cli` on `dummy0`). Teardown removes it.

---

## 🧠 Concept

`community.general.nmcli` is the declarative face of the `nmcli` you used by hand. Instead of `con add` then a series of `con mod` commands, you describe the **desired final state** and the module reconciles to it: `state: present` creates or updates, `state: absent` deletes. List properties like DNS are given as YAML lists (`dns4: [a, b]`) — the module makes the stored list exactly that, no `+`/`-` bookkeeping. Idempotence is the payoff: re-running yields `changed=0` when the system already matches. Switching addressing is just changing `method4` between `manual` and `auto`. Because the module wraps `nmcli`, you verify with the same `nmcli -g` reads from Lab 36a (as read-only `command` tasks with `changed_when: false`).

```
state: present + method4: manual + ip4 + dns4[]  → full static profile
re-run                                            → changed=0
method4: auto                                     → switch to DHCP
state: absent                                     → remove the profile
command: nmcli -g ... (changed_when: false)       → verify stored fields
```

> **Why this matters:** Hand-running `nmcli` across many hosts is unrepeatable; the module gives you version-controlled, idempotent network config that converges to a declared state — the RHCE/SRE way.

---

## 📚 Command Reference

| Command | Purpose | Critical detail |
|---|---|---|
| `community.general.nmcli` | Manage profile | `conn_name`, `state:` |
| `method4` | Static/DHCP | `manual`/`auto` |
| `ip4` / `gw4` / `dns4` | Addressing | `dns4` is a list |
| `state: absent` | Remove profile | clean deletion |
| `command: nmcli -g` | Verify | `changed_when: false` |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox, playbook folder, and load the dummy module.

> Run this block **once** before Task 1.

```bash
export LAB_ROOT=/tmp/lab-36
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-36b/playbooks
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

## TASK 1 of 2 — Declare and verify a static profile

**In plain English:** We declare the full profile, then verify the stored DNS list.

---

### Step 1 of 2 — Write the profile playbook

**In plain English:** We create `task1.yml` describing a complete static profile with a DNS list.

```yaml
---
- name: "Lab 36b Task 1 — declare a static profile"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  tasks:
    - name: "Ensure lab-cli matches the desired static config"
      community.general.nmcli:
        conn_name: lab-cli
        ifname: dummy0
        type: dummy
        method4: manual
        ip4: 10.66.66.2/24
        gw4: 10.66.66.1
        dns4:
          - 10.66.66.53
          - 10.66.66.54
        state: present
      register: nm

    - name: "Show whether anything changed"
      ansible.builtin.debug:
        msg: "changed: {{ nm.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `method4: manual` + `ip4`/`gw4` → Static addressing and gateway in one declaration.
- `dns4: [..., ...]` → The DNS list is set to exactly these entries — no `+`/`-` needed.
- `state: present` → Create or reconcile to this desired state.

**New words in this step:**

- **`dns4` list** — declaring the full DNS server list declaratively.

---

### Step 2 of 2 — Run, verify, and prove idempotence

**In plain English:** We apply the play, read back the DNS list, and re-run for `changed=0`.

```bash
ansible-playbook /root/rhcsa_journal/lab-36b/playbooks/task1.yml
nmcli -g ipv4.dns con show lab-cli
ansible-playbook /root/rhcsa_journal/lab-36b/playbooks/task1.yml | grep -E 'changed='
```

**Expected output:**

```
10.66.66.53,10.66.66.54
localhost                  : ok=2    changed=0    unreachable=0    failed=0
```

**Line-by-line breakdown:**

- `nmcli -g ipv4.dns con show lab-cli` → Confirms the stored DNS list matches the declared one.
- Second run → `changed=0`, proving the module is idempotent.

**New words in this step:**

- **convergence** — the system reaching and staying at the declared state.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| declared list | sets exact DNS | replaces, not appends |
| `state: present` | create/update | idempotent |
| verify read | confirm stored | `changed_when: false` |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Module missing | No collection | Install `community.general` |
| Always changed | Param mismatch | Declare all managed fields |

---

## TASK 2 of 2 — Toggle method and remove

**In plain English:** We switch to auto, then delete the profile cleanly.

---

### Step 1 of 2 — Write the toggle-and-remove playbook

**In plain English:** We create `task2.yml` that flips to `auto`, then removes the profile.

```yaml
---
- name: "Lab 36b Task 2 — toggle then remove"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  tasks:
    - name: "Switch lab-cli to automatic addressing"
      community.general.nmcli:
        conn_name: lab-cli
        type: dummy
        method4: auto
        state: present
      register: toggled

    - name: "Show the method change"
      ansible.builtin.debug:
        msg: "changed to auto: {{ toggled.changed }}"

    - name: "Remove the lab-cli profile"
      community.general.nmcli:
        conn_name: lab-cli
        type: dummy
        state: absent
      register: removed

    - name: "Show removal status"
      ansible.builtin.debug:
        msg: "removed: {{ removed.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `method4: auto` → Switch to DHCP-style addressing declaratively.
- `state: absent` → Delete the profile entirely — the declarative form of `nmcli con delete`.

**New words in this step:**

- **`state: absent`** — declaratively remove a connection profile.

---

### Step 2 of 2 — Run it and confirm removal

**In plain English:** We run the play and confirm the profile is gone.

```bash
ansible-playbook /root/rhcsa_journal/lab-36b/playbooks/task2.yml
nmcli con show lab-cli 2>&1 | grep -qi 'no.*lab-cli\|not found' && echo "GONE" || nmcli con show | grep -q lab-cli && echo "STILL THERE" || echo "GONE"
```

**Expected output:**

```
TASK [Show removal status] *********************************************
ok: [localhost] => {"msg": "removed: True"}
GONE
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Toggles to auto, then deletes; final debug shows `removed: True`.
- The grep confirms `lab-cli` no longer appears in the connection list.

**New words in this step:**

- **clean removal** — declaratively deleting the profile leaves no trace.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `method4: auto` | DHCP | no static address needed |
| `state: absent` | delete | idempotent removal |
| verify gone | confirm | grep the con list |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Profile remains | `state` not absent | Set `state: absent` |
| Error on absent | Already gone | Idempotent — safe |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the profile playbook
- [ ] Task 1 · Step 2 — Run, verify, and prove idempotence
- [ ] Task 2 · Step 1 — Write the toggle-and-remove playbook
- [ ] Task 2 · Step 2 — Run it and confirm removal
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + dummy profile removed

---

## 🧹 Teardown

**In plain English:** Ensure the dummy profile is gone and clear the sandbox.

> Task 2 already removes the profile; this is a safety net plus sandbox cleanup.

```bash
sudo nmcli con delete lab-cli 2>/dev/null || true
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-36
rm -rf /root/rhcsa_journal/lab-36b
```

**Expected output:**

```
✅ Removed /tmp/lab-36 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Missing collection | Module error | Install `community.general` |
| Expecting append | List replaced | Module sets exact list |
| Read task marks changed | Noisy runs | `changed_when: false` |

---

## 📌 Exam Strategy

Declare the end state; let the module reconcile. `state: present` to create/update (with full lists), `state: absent` to remove, `method4` to toggle static/DHCP. Idempotence (`changed=0` on re-run) is the proof it's right.

- `dns4: []` sets the exact list — no `+`/`-`.
- `state: absent` is the declarative `con delete`.
- Verify with the same `nmcli -g` reads as the CLI lab.

---

## 🔗 Related Labs

- [Lab 36a — Command-Line Network Config (RHCSA)](../lab-36a-nmcli-cli-config-rhcsa/) — the `nmcli` commands this module wraps
- [Lab 36c — Command-Line Network Config (Verify)](../lab-36c-nmcli-cli-config-verify/) — prove profile properties
- [Lab 31b — Configure a Static IP (Ansible)](../lab-31b-static-ip-nmcli-ansible/) — the focused static-IP version

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
