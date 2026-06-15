# Lab 00c: Ansible Control Node (Verify) — `rpm -q`, `ansible --version`, `ansible -m ping`

**Series:** linux-ops-mastery — Prerequisite Trilogy · **Lab 00c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving tooling is correctly installed), RHCE EX294 (pre-flight checks before any playbook), SRE/DevOps (control-plane readiness gates)  
**Prerequisite:** [Lab 00a](../lab-00a-ansible-control-node-rhcsa/) and [Lab 00b](../lab-00b-ansible-control-node-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `rpm -q` | _Task 1 · Step 1_ |
| A2 | `ansible -m ping` | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `command -v` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `ansible-config dump --only-changed` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `ansible all --list-hosts` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `ansible-inventory --graph` | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Take the auditor's seat: prove the control node from 00a/00b is genuinely ready. You will assert `ansible-core` is installed and on `PATH`, that the active config points at your sandbox inventory, that `localhost` answers a `ping`, and that the inventory parses into exactly the hosts you expect. Each check is a scriptable pass/fail — the same pre-flight a grader (or your CI pipeline) runs before trusting a control node.

---

## 🧠 Concept

"The control node works" is a claim you verify in layers. **Binary**: `rpm -q` and `command -v` prove the package is installed and discoverable. **Config**: `ansible-config dump --only-changed` prints exactly which defaults you overrode, so you can confirm the inventory path took effect. **Reachability**: `ansible -m ping` proves the engine can actually talk to a host. **Inventory shape**: `--list-hosts` and `ansible-inventory --graph` prove the host list parses into what you intended. Each layer turns a guess into evidence.

```
rpm -q ansible-core            → ansible-core-2.16.x        (installed)
ansible-config dump --only-changed → DEFAULT_HOST_LIST = ... (config active)
ansible -m ping localhost      → "pong"                     (reachable)
ansible-inventory --graph      → @all: └── localhost        (parses)
```

> **Why this matters:** Most "Ansible won't run" failures are a wrong config or an unparsed inventory, not a broken engine. These four checks localize the fault in seconds.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `rpm -q PKG` | Confirm a package is installed | rc 1 + `not installed` when missing |
| `command -v BIN` | Print a binary's path if on `PATH` | rc 1 when not found — clean pass/fail |
| `ansible --version` | Show engine version + config path | confirms which `ansible.cfg` is active |
| `ansible-config dump --only-changed` | List only overridden settings | proves your inventory/collections paths apply |
| `ansible-inventory --graph` | Render the parsed inventory tree | exposes group/host structure problems |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Re-point the config at the sandbox and rebuild the inventory so there is a known-good control node to audit.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-00
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"

export ANSIBLE_CONFIG="$LAB_ROOT/ansible.cfg"
printf '[defaults]\ninventory = %s/inventory\nhost_key_checking = False\n' "$LAB_ROOT" > "$LAB_ROOT/ansible.cfg"
printf 'localhost ansible_connection=local\n' > "$LAB_ROOT/inventory"

ls -1 "$LAB_ROOT"
echo "exit was: $?"
```

**Expected output:**

```
ansible.cfg
inventory
exit was: 0
```

---

## TASK 1 of 2 — Assert the engine and active config

**In plain English:** We prove the package is installed and on `PATH`, then prove the active config really points at our sandbox inventory.

---

### Step 1 of 2 — Assert `ansible-core` is installed and discoverable

**In plain English:** We confirm the RPM is present and that the `ansible` binary resolves on `PATH`.

```bash
rpm -q ansible-core && echo "PKG OK" || echo "PKG MISSING (FAIL)"
command -v ansible && echo "BIN ON PATH (OK)" || echo "BIN MISSING (FAIL)"
ansible --version | head -1
```

**Expected output:**

```
ansible-core-2.16.3-1.el9.x86_64
PKG OK
/usr/bin/ansible
BIN ON PATH (OK)
ansible [core 2.16.3]
```

**Line-by-line breakdown:**

- `rpm -q ansible-core && ... || ...` → Query the RPM DB; a version string fires the OK branch, `not installed` (rc 1) fires FAIL.
- `command -v ansible` → Print the resolved path of the binary; rc 1 (nothing printed) means it is not on `PATH`.
- `ansible --version | head -1` → Confirm the engine executes and report its version.

**New words in this step:**

- **`command -v`** — a portable, scriptable "where is this binary?" that returns a clean exit code.

---

### Step 2 of 2 — Assert the active config points at the sandbox inventory

**In plain English:** We dump only the overridden settings and confirm the inventory path resolves to our sandbox file.

```bash
ansible-config dump --only-changed | grep -i inventory
ansible --version | grep -i 'config file'
echo "exit was: $?"
```

**Expected output:**

```
DEFAULT_HOST_LIST(/tmp/lab-00/ansible.cfg) = ['/tmp/lab-00/inventory']
  config file = /tmp/lab-00/ansible.cfg
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-config dump --only-changed | grep -i inventory` → Print only settings you overrode; the `DEFAULT_HOST_LIST` line proves the inventory path took effect and which file set it.
- `ansible --version | grep -i 'config file'` → Confirm the active `ansible.cfg` is the sandbox one, not a stray system config.

**New words in this step:**

- **`ansible-config dump --only-changed`** — shows just the non-default settings, the fastest way to see what your config actually changed.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `rpm -q` | confirms install | a `which` hit does not prove the RPM is registered |
| `ansible-config dump` | shows effective settings | `--only-changed` hides defaults you did not set |
| `config file =` line | reveals active cfg | nearest cfg wins; `ANSIBLE_CONFIG` overrides all |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `config file = None` | No cfg discovered | Set `ANSIBLE_CONFIG` or add a project `ansible.cfg` |
| Inventory line absent | Inventory not overridden | Add `inventory =` under `[defaults]` |

---

## TASK 2 of 2 — Assert reachability and inventory shape

**In plain English:** We ping `localhost` to prove the engine reaches it, then render the parsed inventory tree to prove it contains exactly the host we expect.

---

### Step 1 of 2 — Ping and list hosts

**In plain English:** We run the `ping` module and list the hosts the inventory resolves to, proving connectivity and parsing in one pass.

```bash
ansible -m ping all | grep -E 'SUCCESS|pong'
ansible all --list-hosts
echo "exit was: $?"
```

**Expected output:**

```
localhost | SUCCESS => {
    "ping": "pong"
  hosts (1):
    localhost
exit was: 0
```

**Line-by-line breakdown:**

- `ansible -m ping all | grep -E 'SUCCESS|pong'` → Ping every host in the inventory; the `pong` line proves the engine reached it via the local connection.
- `ansible all --list-hosts` → Show which hosts the pattern `all` expands to without running anything.

**New words in this step:**

- **`--list-hosts`** — prints the hosts a pattern matches, a dry way to confirm inventory targeting.

---

### Step 2 of 2 — Render the inventory graph

**In plain English:** We draw the parsed inventory as a tree to confirm `localhost` sits under `@all` and nothing unexpected appears.

```bash
ansible-inventory --graph
echo "exit was: $?"
```

**Expected output:**

```
@all:
  |--@ungrouped:
  |  |--localhost
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-inventory --graph` → Parse the inventory and render its group/host tree; `localhost` under `@ungrouped` confirms our one-line inventory parsed correctly.
- `echo "exit was: $?"` → A `0` confirms the inventory parsed without error.

**New words in this step:**

- **`ansible-inventory --graph`** — renders the fully-parsed inventory as a tree, exposing grouping mistakes a flat file hides.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `ping` module | Python round-trip | success even when ICMP is firewalled |
| `--list-hosts` | shows matched hosts | empty list = wrong pattern or inventory |
| `--graph` | renders parsed tree | catches a host stranded in the wrong group |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `No hosts matched` | Inventory empty/unparsed | Check the inventory path in `ansible.cfg` |
| `UNREACHABLE` | Missing `ansible_connection=local` | Add it to the localhost line |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Assert `ansible-core` is installed and discoverable
- [ ] Task 1 · Step 2 — Assert the active config points at the sandbox inventory
- [ ] Task 2 · Step 1 — Ping and list hosts
- [ ] Task 2 · Step 2 — Render the inventory graph
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-00
```

**Expected output:**

```
✅ Removed /tmp/lab-00 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Trusting `which` over `rpm -q` | A stale binary masquerades as installed | Verify with `rpm -q` |
| Forgetting `ANSIBLE_CONFIG` | Audits hit a different config | Export it before checking |
| Reading `ping` as ICMP | Confused by firewall rules | It is a Python check, not ICMP |

---

## 📌 Exam Strategy

Before any RHCE task, run the pre-flight: `ansible --version` (right config?), `ansible all --list-hosts` (right hosts?), `ansible all -m ping` (reachable?). If all three pass, the rest of the exam is just modules. If one fails, you know exactly which layer to fix.

- `ansible --version` first — it tells you which config is active.
- `ansible-inventory --graph` is the fastest way to debug grouping.
- A clean `ping` to `all` is your green light to start writing plays.

---

## 🔗 Related Labs

- [Lab 00a — Ansible Control Node (RHCSA)](../lab-00a-ansible-control-node-rhcsa/) — the hand-built node this audits
- [Lab 00b — Ansible Control Node (Ansible)](../lab-00b-ansible-control-node-ansible/) — the playbook-managed node this audits
- [Lab 01c — Stdout Redirection (Verify)](../lab-01c-stdout-redirection-verify/) — the first content-verification lab

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
