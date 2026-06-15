# Lab 00a: Ansible Control Node (RHCSA) — `dnf install ansible-core`, `ansible -m ping`

**Series:** linux-ops-mastery — Prerequisite Trilogy · **Lab 00a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (`dnf` package management, `rpm -q` verification), RHCE EX294 (standing up a working control node — the prerequisite for every playbook task), SRE/DevOps (reproducible automation tooling)  
**Prerequisite:** A RHEL/Rocky/Alma 9 box you can `sudo dnf install` on — no prior lab required (this is the bootstrap lab)  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `dnf install` | _Task 1 · Step 1_ |
| A2 | `rpm -q` | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `ansible-galaxy collection install` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N2 | `ansible -m ping` (ad-hoc module) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N3 | `ansible-playbook --check --diff` | Task 2 · Step 2 | _Task 2 · Step 2_ |
| N4 | `ANSIBLE_CONFIG` env var | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

Stand up a working Ansible control node from nothing: install `ansible-core` from the AppStream repo, verify the package landed, add a Galaxy collection, then prove the tooling actually runs by pinging `localhost` with an ad-hoc module and dry-running a tiny playbook with `--check --diff`. By the end you have the exact environment every `b`-variant lab in this series depends on — config and inventory kept inside a throwaway sandbox so nothing leaks into your real home directory.

---

## 🧠 Concept

Ansible has two package faces on RHEL 9. `ansible-core` (in AppStream) is the slim engine: the `ansible`, `ansible-playbook`, and `ansible-galaxy` binaries plus the `ansible.builtin` modules. The fat `ansible` package (EPEL) bundles hundreds of extra collections you usually do not need and is the wrong choice on an exam box. A control node needs three things to be useful: the engine, a **config file** that tells it where to look, and an **inventory** that lists the hosts it manages. We point `ANSIBLE_CONFIG` at a sandbox file so the whole setup is disposable.

```
dnf install ansible-core   →  /usr/bin/ansible, ansible-playbook, ansible-galaxy
ANSIBLE_CONFIG=$LAB_ROOT/ansible.cfg  →  [defaults] inventory = $LAB_ROOT/inventory
ansible -m ping localhost  →  "pong"  (the engine + connection plugin work)
```

> **Why this matters:** Every RHCE task assumes a control node that already pings its hosts. Knowing `ansible-core` vs `ansible`, and how the config/inventory pair is discovered, is the difference between starting the exam and staring at "no hosts matched."

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `dnf install ansible-core` | Install the slim Ansible engine from AppStream | `-y` to skip the prompt; prefer `ansible-core` over fat `ansible` |
| `rpm -q ansible-core` | Confirm a package is installed and show its version | prints `not installed` (rc 1) when missing |
| `ansible-galaxy collection install` | Add a content collection (modules/roles) | `-p PATH` installs into a custom collections dir |
| `ansible -m ping` | Run the `ping` module ad-hoc against hosts | `-m` picks the module; this is NOT ICMP, it is a Python round-trip |
| `ansible-playbook --check --diff` | Dry-run a playbook and show would-be changes | `--check` makes no changes; `--diff` prints the delta |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Create one sandbox folder and point Ansible's config at a file inside it, so the inventory, config, and collections all live in one disposable place.

> Run this block **once** before Task 1. It defines a single sandbox root
> (`LAB_ROOT`) that every file in this lab lives under, so the Teardown
> section can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-00
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"

export ANSIBLE_CONFIG="$LAB_ROOT/ansible.cfg"
mkdir -p "$LAB_ROOT/collections"
ls -ld "$LAB_ROOT"
echo "exit was: $?"
```

**Expected output:**

```
drwxr-xr-x. 3 root root 60 Jun 15 18:00 /tmp/lab-00
exit was: 0
```

---

## TASK 1 of 2 — Install the engine and add a collection

**In plain English:** We install `ansible-core`, prove the package is present, then pull a Galaxy collection into the sandbox so we never touch the system collections path.

---

### Step 1 of 2 — Install `ansible-core` and verify with `rpm -q`

**In plain English:** We install the slim Ansible engine from AppStream and immediately confirm the package landed with its version.

```bash
sudo dnf install -y ansible-core
rpm -q ansible-core
ansible --version | head -1
echo "exit was: $?"
```

**Expected output:**

```
... Installed: ansible-core-2.16.x ...
ansible-core-2.16.3-1.el9.x86_64
ansible [core 2.16.3]
exit was: 0
```

**Line-by-line breakdown:**

- `sudo dnf install -y ansible-core` → Install the slim engine from AppStream; `-y` answers "yes" so the install is non-interactive. We deliberately do NOT install the fat `ansible` package.
- `rpm -q ansible-core` → Query the RPM database for the package; printing `ansible-core-2.16...` (not `not installed`) proves it is present.
- `ansible --version | head -1` → Run the binary itself and show the first line, confirming the engine actually executes.

**New words in this step:**

- **AppStream** — the RHEL 9 repository that ships application runtimes like `ansible-core`, separate from the BaseOS core repo.
- **`ansible-core`** — the minimal Ansible package (engine + `ansible.builtin` only), the RHCE-correct choice over the EPEL `ansible` bundle.

---

### Step 2 of 2 — Add a Galaxy collection into the sandbox

**In plain English:** We install the `community.general` collection into a sandbox path so the extra modules are available without polluting the system-wide collections directory.

```bash
ansible-galaxy collection install community.general -p "$LAB_ROOT/collections"
ansible-galaxy collection list -p "$LAB_ROOT/collections" | grep community.general
echo "exit was: $?"
```

**Expected output:**

```
Starting galaxy collection install process
... community.general:8.x.x was installed successfully
community.general 8.6.0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-galaxy collection install community.general -p "$LAB_ROOT/collections"` → Download and unpack the collection; `-p` forces it into the sandbox path instead of `~/.ansible/collections`.
- `ansible-galaxy collection list -p ...` → List the collections in that path; piping to `grep` confirms `community.general` is there.

**New words in this step:**

- **collection** — a packaged bundle of Ansible modules, roles, and plugins published on Ansible Galaxy.
- **`-p` (collections path)** — installs the collection into a chosen directory instead of the default user path.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `ansible-core` vs `ansible` | core = slim engine; fat = bundle | installing fat `ansible` from EPEL is the wrong reflex |
| `rpm -q pkg` | confirms install + version | exit code 1 (not an error message) means "not installed" |
| `ansible-galaxy ... -p` | sandbox the collection path | omitting `-p` writes to `~/.ansible`, surviving teardown |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `No match for argument: ansible-core` | AppStream repo disabled | `sudo dnf repolist`; enable AppStream, retry |
| `command not found: ansible` | Install failed silently | Re-run `dnf install`; check `rpm -q ansible-core` |

---

## TASK 2 of 2 — Wire up config + inventory and prove it runs

**In plain English:** We write a sandbox `ansible.cfg` and `inventory`, ping `localhost` with an ad-hoc module to prove connectivity, then dry-run a tiny playbook with `--check --diff`.

---

### Step 1 of 2 — Write config + inventory, then `ansible -m ping`

**In plain English:** We create the config and inventory files inside the sandbox, then run the ad-hoc `ping` module against `localhost` to confirm the engine, config discovery, and local connection all work.

```bash
cat > "$LAB_ROOT/ansible.cfg" <<EOF
[defaults]
inventory = $LAB_ROOT/inventory
collections_path = $LAB_ROOT/collections
host_key_checking = False
EOF

cat > "$LAB_ROOT/inventory" <<'EOF'
localhost ansible_connection=local
EOF

ansible -m ping localhost
echo "exit was: $?"
```

**Expected output:**

```
localhost | SUCCESS => {
    "ansible_facts": {"discovered_interpreter_python": "/usr/bin/python3"},
    "changed": false,
    "ping": "pong"
}
exit was: 0
```

**Line-by-line breakdown:**

- `cat > "$LAB_ROOT/ansible.cfg" <<EOF ... EOF` → Heredoc writing the config; `[defaults]` tells Ansible where the inventory and collections live. Because `$ANSIBLE_CONFIG` points here, this file is auto-discovered.
- `cat > "$LAB_ROOT/inventory" <<'EOF' ... EOF` → Heredoc writing a one-host inventory; `ansible_connection=local` means "run here, do not SSH."
- `ansible -m ping localhost` → Run the `ping` module ad-hoc; `pong` proves the engine reached the host through the local connection plugin (this is a Python check, not ICMP).

**New words in this step:**

- **ad-hoc command** — a one-off `ansible -m MODULE` run, no playbook file involved.
- **`ANSIBLE_CONFIG`** — an environment variable that overrides config discovery to point at an exact file.

---

### Step 2 of 2 — Dry-run a tiny playbook with `--check --diff`

**In plain English:** We write a one-task playbook and run it with `--check --diff` so Ansible reports what it *would* change without actually changing anything.

```bash
cat > "$LAB_ROOT/hello.yml" <<'EOF'
---
- name: "Lab 00a smoke test"
  hosts: localhost
  gather_facts: false
  tasks:
    - name: "Ensure a marker file exists"
      ansible.builtin.copy:
        dest: /tmp/lab-00/marker.txt
        content: "control node is alive\n"
        mode: '0644'
EOF

ansible-playbook --check --diff "$LAB_ROOT/hello.yml"
echo "exit was: $?"
```

**Expected output:**

```
TASK [Ensure a marker file exists] *********************************************
--- before
+++ after
@@ -0,0 +1 @@
+control node is alive
changed: [localhost]

PLAY RECAP ********************************************************************
localhost                  : ok=1    changed=1    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `cat > "$LAB_ROOT/hello.yml" <<'EOF' ... EOF` → Write a minimal playbook with one `copy` task targeting a sandbox file.
- `ansible-playbook --check --diff ...` → `--check` runs in "dry-run" mode making no real change; `--diff` prints the unified delta the task would apply, so `changed=1` is *predicted*, not performed.

**New words in this step:**

- **check mode** — `--check` simulates a run and reports would-be changes without touching anything.
- **diff mode** — `--diff` prints the before/after delta for tasks that support it.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `ansible.cfg [defaults]` | sets inventory + collections path | nearest cfg wins; `ANSIBLE_CONFIG` overrides all |
| `ping` module | Python round-trip to the host | it is NOT ICMP — a firewall blocking ping is irrelevant |
| `--check --diff` | dry-run + show the delta | `changed=1` here means "would change," nothing happened |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `Could not match supplied host pattern` | Inventory not found | Confirm `ANSIBLE_CONFIG` and the `inventory =` path |
| `UNREACHABLE` on localhost | Missing `ansible_connection=local` | Add it to the inventory line |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Install `ansible-core` and verify with `rpm -q`
- [ ] Task 1 · Step 2 — Add a Galaxy collection into the sandbox
- [ ] Task 2 · Step 1 — Write config + inventory, then `ansible -m ping`
- [ ] Task 2 · Step 2 — Dry-run a tiny playbook with `--check --diff`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-00
```

**This lab installed a SYSTEM package — reverse it only if you want a fully clean box** (`rm` will not):

```bash
# sudo dnf remove -y ansible-core      # remove the engine you installed
```

**Expected output:**

```
✅ Removed /tmp/lab-00 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Installing fat `ansible` from EPEL | Hundreds of extra collections, slow | Install `ansible-core` from AppStream |
| Editing the wrong `ansible.cfg` | Changes ignored | Set `ANSIBLE_CONFIG` to the exact file |
| Expecting `ping` to use ICMP | Confusion when ICMP is blocked | The `ping` module is a Python round-trip, not ICMP |

---

## 📌 Exam Strategy

On the RHCE the control node is assumed working, but you must be able to rebuild it fast. Install `ansible-core`, drop a project-local `ansible.cfg` next to your playbooks (nearest config wins), list hosts in an inventory, and confirm with `ansible -m ping all` before writing a single play.

- Use a project-local `ansible.cfg` so the grader's environment cannot interfere.
- `ansible all -m ping` is the first command of every Ansible session — make it muscle memory.
- Reach for `--check --diff` to preview risky plays before committing.

---

## 🔗 Related Labs

- [Lab 00b — Ansible Control Node (Ansible)](../lab-00b-ansible-control-node-ansible/) — manage the control node's own packages and config with a playbook
- [Lab 00c — Ansible Control Node (Verify)](../lab-00c-ansible-control-node-verify/) — prove the engine, config, and ping all work
- [Lab 01a — Stdout Redirection (RHCSA)](../lab-01a-stdout-redirection-rhcsa/) — the first content lab, now that your tooling is ready

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
