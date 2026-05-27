# Lab 00: Ansible Control Node Setup — `dnf`, `ansible-galaxy`, `ansible-playbook`

- **Series:** linux-ops-mastery — Prerequisite Lab (run BEFORE Lab 01)
- **Career arcs covered:** RHCE EX294 (control node, FQCN, collections), CKA (ansible-driven kubeadm), RHCA — RH362 (IdM via Ansible)
- **Prerequisite:** A running RHEL/Rocky/AlmaLinux 9 box where you can `sudo dnf install`
- **Time Estimate:** 25–35 minutes (one-time setup)
- **Tasks:** 5 (ADHD spec — Lab 00 is the only lab where all 5 tasks are setup/Ansible)
- **Practice Directory (lab-wide rotation #00):** `/root/rhcsa_journal`
- **Sandbox:** `/root/rhcsa_journal/lab00`
- **Traps rehearsed this lab:** **T00-A** (No FQCN — `file:` vs `ansible.builtin.file:`) · **T00-B** (Forgetting to install `community.general` and `ansible.posix` collections) · **T00-C** (Editing `~/.ansible.cfg` after running playbooks and not knowing which config the run actually used)

> **This lab is the prerequisite for Task 4 of every other lab in this series.** If `ansible --version` fails when you reach Task 4 of any lab, come back here.

---

## 🖥️ LAB HEADER BLOCK — run this FIRST

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T00-A T00-B T00-C"
echo "📁  PRACTICE DIR: /root/rhcsa_journal/lab00"
```

> **STOP — paste header output before starting Task 1.**

---

## 🎯 Objective

By the end of Lab 00 you will have:

1. `ansible-core` installed and on PATH
2. The two collections the RHCE exam expects: `ansible.posix` and `community.general`
3. A working `~/.ansible.cfg` that points at a local inventory
4. An inventory file that registers `localhost` so every lab's Task 4 can run
5. A persistent journal tree at `/root/rhcsa_journal/` so notes survive reboot
6. A first playbook that proves the loop works end-to-end (check → apply → idempotent re-run)

After this lab, every other lab's Task 4 just *runs* — no setup, no surprises.

---

## 🧠 Why This Lab Exists

The 3-1-1 lab structure (3 RHCSA tasks, 1 Ansible task, 1 RHCSA verification capstone) is the spine of this series. Task 4 of every lab assumes:

```
ansible --version          # works
ansible-galaxy collection list   # shows ansible.posix and community.general
ansible -m ping localhost  # returns "pong"
ls /root/rhcsa_journal     # exists
```

If any of those four facts is false, Task 4 will fail in a confusing way. So we set them up once, here, and never touch them again.

---

## Task 1 — Install `ansible-core` and Prove It Runs

**Practice directory this task:** `/root/rhcsa_journal/lab00`

### 🔁 Warm-Up — Commands from Previous Labs

You haven't done a previous lab yet, so the warm-up is the basics this whole series assumes:

```bash
sudo mkdir -p /root/rhcsa_journal/lab00/task1
cd /root/rhcsa_journal/lab00/task1
date -Is | sudo tee start.txt
echo "user=$(whoami) host=$(hostname) os=$(grep PRETTY_NAME /etc/os-release)" | sudo tee -a start.txt
echo "exit was: $?"
```

If those four lines all succeed, your shell is healthy. If any fail, fix the shell first; Ansible will not save you.

### Purpose

Install `ansible-core` from the AppStream repo and prove the binary works.

### Main Command Block

```bash
# RHEL/Rocky/Alma 9: ansible-core lives in AppStream, no EPEL needed
sudo dnf install -y ansible-core

# Prove it
ansible --version
which ansible
which ansible-playbook
which ansible-galaxy
```

Save the install transcript:

```bash
sudo dnf install -y ansible-core 2>&1 | sudo tee /root/rhcsa_journal/lab00/task1/install.log
ansible --version | sudo tee /root/rhcsa_journal/lab00/task1/version.txt
```

### Human-Readable Breakdown

`dnf install -y ansible-core` tells DNF: "install the package named `ansible-core`, and don't prompt me with yes/no." `ansible-core` is the slimmer engine (modules + runtime). The fatter `ansible` package on EPEL bundles every community collection — we do **not** install that, because RHCE wants you to add the collections deliberately.

`ansible --version` prints the engine version, the config file in use, and the Python interpreter Ansible is bound to. All three numbers will matter in Task 3.

### Reading It Left to Right

`sudo dnf install -y ansible-core`

- `sudo` — elevate; package install needs root
- `dnf` — RHEL 9 package manager
- `install` — subcommand
- `-y` — assume yes to confirmation prompts
- `ansible-core` — package name (NOT `ansible` — different package, different RHCE expectation)

### The Story

You picked `ansible-core` instead of `ansible` because the RHCE exam expects you to declare the collections you need rather than ship a kitchen-sink install. A grader who sees `dnf install ansible` on an exam VM raises an eyebrow; `dnf install ansible-core` is the right shape.

### Expected Output

```
ansible [core 2.14.x]
  config file = None
  configured module search path = ['/root/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
  ansible python module location = /usr/lib/python3.9/site-packages/ansible
  ansible collection location = /root/.ansible/collections:/usr/share/ansible/collections
  executable location = /usr/bin/ansible
  python version = 3.9.x ...
```

Two facts in that output matter: `config file = None` (we will fix that in Task 3) and `collection location` (Task 2 installs into that path).

### Switches Table

| Switch | Meaning | Why it matters |
|---|---|---|
| `-y` | Assume yes | Required in scripted installs and Ansible CI |
| `--version` | Print engine version + config + python path | First diagnostic command in every Task 4 |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| `ansible-core` | Engine + built-in `ansible.builtin.*` modules — no community modules |
| `ansible` (the fat package) | Engine + ~80 collections — convenience, but not RHCE-shaped |
| `config file = None` | You haven't created `~/.ansible.cfg` yet; defaults are in effect |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| **T00-A** | Installing `ansible` (the fat package) | Use `ansible-core` and add collections explicitly |
| **T00-A** | Calling modules without FQCN (`file:` instead of `ansible.builtin.file:`) | Always write `ansible.builtin.MODULE`, `ansible.posix.MODULE`, `community.general.MODULE` |

### 🔁 Persistence Check

```bash
rpm -q ansible-core
ansible --version | head -1
```

Both must succeed. If either fails, re-run the install.

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab00/task1/done.txt > /dev/null <<EOF
lab=00 task=1
when=$(date -Is)
ansible_version=$(ansible --version | head -1)
rpm_status=$(rpm -q ansible-core)
EOF
cat /root/rhcsa_journal/lab00/task1/done.txt
```

### 🧹 Cleanup

Nothing to clean — install is intentionally persistent.

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `Unable to find a match: ansible-core` | `sudo subscription-manager repos --enable=rhel-9-appstream` (RHEL) or `sudo dnf repolist` (Rocky/Alma — should already have appstream) |
| `ansible: command not found` after install | Open a new shell or run `hash -r` |

> **STOP — confirm `ansible --version` works before Task 2.**

---

## Task 2 — Install `ansible.posix` and `community.general` Collections

**Practice directory this task:** `/root/rhcsa_journal/lab00`

### 🔁 Warm-Up — Commands from Previous Labs

```bash
sudo mkdir -p /root/rhcsa_journal/lab00/task2
cd /root/rhcsa_journal/lab00/task2
date -Is | sudo tee start.txt
ansible --version | head -1 | sudo tee -a start.txt
echo "exit was: $?"
```

### Purpose

Install the two collections you will use over and over in Task 4 of every other lab.

### Main Command Block

```bash
# Install into the user collection path
ansible-galaxy collection install ansible.posix
ansible-galaxy collection install community.general

# Verify
ansible-galaxy collection list | grep -E 'ansible.posix|community.general'

# Capture
ansible-galaxy collection list 2>&1 | sudo tee /root/rhcsa_journal/lab00/task2/collections.txt
```

### Human-Readable Breakdown

`ansible-galaxy` is the package manager *for Ansible content*. A collection is a bundle of modules, roles, and plugins. RHCE expects you to know that `selinux`, `firewalld`, `mount`, and `acl` live in `ansible.posix`, and that `sefcontext`, `nmcli`, `lvol`, `parted`, and `nmcli` live in `community.general`.

You will use `ansible.posix.firewalld` in Lab 64. You will use `community.general.sefcontext` in Lab 06. They are not optional.

### Reading It Left to Right

`ansible-galaxy collection install ansible.posix`

- `ansible-galaxy` — the collections/roles installer that ships with `ansible-core`
- `collection` — subcommand namespace (vs. `role`)
- `install` — verb
- `ansible.posix` — namespace `ansible` + name `posix` — fully-qualified collection name (FQCN at collection level)

### The Story

RHEL 9's `/usr/share/ansible/collections` ships with **zero** collections preloaded. The Ansible engine knows about `ansible.builtin.*` because that's compiled in, but `ansible.posix.selinux` is unknown until you run `ansible-galaxy collection install ansible.posix`. RHCE exam VMs come pre-loaded — your home lab does not.

### Expected Output

```
Starting galaxy collection install process
Process install dependency map
Starting collection install process
Downloading https://galaxy.ansible.com/.../ansible-posix-1.5.x.tar.gz ...
Installing 'ansible.posix:1.5.x' to '/root/.ansible/collections/ansible_collections/ansible/posix'
ansible.posix:1.5.x was installed successfully
```

And from `ansible-galaxy collection list`:

```
# /root/.ansible/collections/ansible_collections
Collection         Version
------------------ -------
ansible.posix      1.5.x
community.general  7.x.x
```

### Switches Table

| Switch | Meaning | Why it matters |
|---|---|---|
| `collection install <name>` | Install a collection by namespace.name | The RHCE pattern |
| `--upgrade` | Upgrade existing collection | Useful when a module's behaviour changed between versions |
| `-p PATH` | Install to a specific path | Useful for project-local collections (`ansible.cfg: collections_path = ./collections`) |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| Collection | A bundle of modules + roles + plugins, installed via `ansible-galaxy` |
| FQCN | `namespace.collection.module` — required RHCE format |
| `ansible.posix` | RHEL/POSIX-oriented modules: `selinux`, `firewalld`, `mount`, `acl`, `at` |
| `community.general` | Broader RHEL coverage: `sefcontext`, `nmcli`, `lvol`, `parted`, `cron` (also exists in `ansible.builtin`) |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| **T00-B** | Writing `selinux:` in a playbook before `ansible.posix` is installed | Run `ansible-galaxy collection list \| grep ansible.posix` BEFORE starting Task 4 of any lab |

### 🔁 Persistence Check

```bash
ansible-galaxy collection list | grep -E 'ansible.posix|community.general'
ansible-doc ansible.posix.selinux | head -3
ansible-doc community.general.sefcontext | head -3
```

All three must succeed. `ansible-doc` is the RHCE-grade verification — if the module is reachable, its doc page renders.

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab00/task2/done.txt > /dev/null <<EOF
lab=00 task=2
when=$(date -Is)
posix=$(ansible-galaxy collection list | awk '/ansible.posix/ {print $2}')
general=$(ansible-galaxy collection list | awk '/community.general/ {print $2}')
EOF
cat /root/rhcsa_journal/lab00/task2/done.txt
```

### 🧹 Cleanup

Nothing to clean — collections are intentionally persistent.

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `ERROR! Failed to download collection` | Check `curl -I https://galaxy.ansible.com/` — proxy/firewall issue |
| `ansible-doc: module not found` | The shell hasn't re-read the collections path; open new shell |

> **STOP — confirm both collections list before Task 3.**

---

## Task 3 — Write `~/.ansible.cfg` and `~/inventory`

**Practice directory this task:** `/root/rhcsa_journal/lab00`

### 🔁 Warm-Up — Commands from Previous Labs

```bash
sudo mkdir -p /root/rhcsa_journal/lab00/task3
cd /root/rhcsa_journal/lab00/task3
date -Is | sudo tee start.txt
ansible --version 2>&1 | grep "config file" | sudo tee -a start.txt
echo "exit was: $?"
```

You should see `config file = None`. After Task 3 it will say `config file = /root/.ansible.cfg`.

### Purpose

Build a minimal, RHCE-style control-node config: one `~/.ansible.cfg`, one `~/inventory`, both pointed at localhost.

### Main Command Block

```bash
# ~/.ansible.cfg
sudo tee /root/.ansible.cfg > /dev/null <<'EOF'
[defaults]
inventory       = /root/inventory
host_key_checking = False
retry_files_enabled = False
stdout_callback = yaml
nocows = 1

[privilege_escalation]
become              = True
become_method       = sudo
become_user         = root
become_ask_pass     = False
EOF

# ~/inventory
sudo tee /root/inventory > /dev/null <<'EOF'
[control]
localhost ansible_connection=local

[control:vars]
ansible_python_interpreter=/usr/bin/python3
EOF

# Verify
ansible --version | grep "config file"
ansible-inventory --list
ansible -m ping localhost
```

### Human-Readable Breakdown

`~/.ansible.cfg` is the per-user config that Ansible reads on startup. The key knobs:

- `inventory = /root/inventory` — points at the file you control, so `ansible-playbook foo.yml` always knows about `localhost`
- `stdout_callback = yaml` — readable diffs in `--check --diff` mode
- `nocows = 1` — disables the ASCII cow that some versions still print (it eats screen space)
- `[privilege_escalation]` — every play becomes root by default, like an RHCE-grade host

`~/inventory` is the host list. `ansible_connection=local` tells Ansible: "don't SSH to localhost, just exec the modules in this Python interpreter."

### Reading It Left to Right

`inventory = /root/inventory`

- `inventory` — config key Ansible looks for in `[defaults]`
- `=` — assignment (INI syntax)
- `/root/inventory` — absolute path; never relative, because cwd at runtime is unpredictable

`localhost ansible_connection=local`

- `localhost` — host name (Ansible already knows this means 127.0.0.1)
- `ansible_connection=local` — per-host variable telling Ansible to skip SSH

### The Story

On a real RHCE exam, the control node has a config like this already. You're not building this exam-day — you're building it once at home so every Task 4 in this series has a known starting point. When something breaks later, you can `cat ~/.ansible.cfg` and `cat ~/inventory` to know exactly what Ansible is seeing.

### Expected Output

```
$ ansible --version | grep "config file"
  config file = /root/.ansible.cfg

$ ansible-inventory --list
{
    "_meta": { "hostvars": { "localhost": { "ansible_connection": "local", "ansible_python_interpreter": "/usr/bin/python3" } } },
    "all": { "children": [ "control", "ungrouped" ] },
    "control": { "hosts": [ "localhost" ] }
}

$ ansible -m ping localhost
localhost | SUCCESS => {
    "ansible_facts": { "discovered_interpreter_python": "/usr/bin/python3" },
    "changed": false,
    "ping": "pong"
}
```

Three pieces of evidence: config file is loaded, inventory parses, ping returns `pong`.

### Switches Table

| Switch / Key | Meaning | Why it matters |
|---|---|---|
| `inventory = PATH` | Default inventory if `-i` is not passed | Eliminates "where is my inventory?" confusion |
| `ansible_connection=local` | Skip SSH for this host | The whole reason `ansible -m ping localhost` works |
| `become = True` | Default to root on every play | Matches `sudo` workflow used in every Task 4 |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| `~/.ansible.cfg` | Per-user config; takes precedence over `/etc/ansible/ansible.cfg` |
| `~/inventory` | The hosts file Ansible runs against |
| `ansible -m ping` | Sanity ping that proves config + inventory + Python interp + sudo all line up |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| **T00-C** | Editing `~/.ansible.cfg` in one shell, running playbook in another, and not knowing which config "won" | `ansible --version \| grep "config file"` BEFORE every Task 4 |

### 🔁 Persistence Check

```bash
test -f /root/.ansible.cfg && echo "cfg ok"
test -f /root/inventory && echo "inv ok"
ansible -m ping localhost > /dev/null && echo "ping ok"
```

All three lines must print `ok`.

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab00/task3/done.txt > /dev/null <<EOF
lab=00 task=3
when=$(date -Is)
cfg_path=$(ansible --version | awk '/config file/ {print $4}')
inventory=$(grep -c '^localhost' /root/inventory)
ping=$(ansible -m ping localhost 2>&1 | grep -c '"ping": "pong"')
EOF
cat /root/rhcsa_journal/lab00/task3/done.txt
```

### 🧹 Cleanup

Nothing to clean — config files are intentionally persistent.

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `config file = None` after writing `~/.ansible.cfg` | You ran `ansible` as a non-root user; `~/.ansible.cfg` only applies to that user's $HOME |
| `Could not match supplied host pattern` | Re-run `ansible-inventory --list` and confirm `localhost` appears |

> **STOP — confirm `ansible -m ping localhost` returns `"ping": "pong"` before Task 4.**

---

## Task 4 — First Playbook: `file: state=directory` Against Localhost

**Practice directory this task:** `/root/rhcsa_journal/lab00`

### 🔁 Warm-Up — Commands from Previous Labs

```bash
sudo mkdir -p /root/rhcsa_journal/lab00/task4/playbooks
cd /root/rhcsa_journal/lab00/task4
date -Is | sudo tee start.txt
ansible --version | head -1 | sudo tee -a start.txt
ansible -m ping localhost > ping.txt 2>&1
grep -c '"ping": "pong"' ping.txt | sudo tee -a start.txt
echo "exit was: $?"
```

### Purpose

Write the FIRST playbook this series will use. It creates a sentinel directory `/root/rhcsa_journal/_ansible_smoketest` using `ansible.builtin.file`. The point is not the directory — the point is the loop: `--check --diff`, then apply, then run twice.

### Main Command Block

Write the playbook:

```bash
sudo tee /root/rhcsa_journal/lab00/task4/playbooks/smoketest.yml > /dev/null <<'EOF'
---
- name: Lab 00 Task 4 — smoketest of ansible.builtin.file
  hosts: localhost
  become: true
  gather_facts: false
  tasks:
    - name: Ensure smoketest directory exists with mode 0750
      ansible.builtin.file:
        path: /root/rhcsa_journal/_ansible_smoketest
        state: directory
        owner: root
        group: root
        mode: '0750'
      register: smoketest_result

    - name: Show the register result
      ansible.builtin.debug:
        var: smoketest_result
EOF
```

Check-mode first:

```bash
ansible-playbook --check --diff /root/rhcsa_journal/lab00/task4/playbooks/smoketest.yml \
  2>&1 | sudo tee /root/rhcsa_journal/lab00/task4/check.log
```

Apply:

```bash
ansible-playbook /root/rhcsa_journal/lab00/task4/playbooks/smoketest.yml \
  2>&1 | sudo tee /root/rhcsa_journal/lab00/task4/apply.log
```

### Human-Readable Breakdown

The playbook has one play and two tasks. The first task uses **`ansible.builtin.file`** — FQCN, real module, not a shell wrapper — to declare a desired state: "this path exists, is a directory, is mode 0750, is owned by root." The second task is `ansible.builtin.debug` which prints the register variable so you can read what changed.

`--check --diff` dry-runs the playbook and shows a unified diff of what *would* change. This is the RHCE habit: never apply blind. `register: smoketest_result` captures everything Ansible knows about the operation; `debug: var: smoketest_result` shows it.

### Reading It Left to Right

```yaml
- name: Ensure smoketest directory exists with mode 0750
  ansible.builtin.file:
    path: /root/rhcsa_journal/_ansible_smoketest
    state: directory
    mode: '0750'
```

- `- name:` — task name (printed in `PLAY RECAP` and in graders' eyes)
- `ansible.builtin.file:` — FQCN of the module
- `path:` — absolute filesystem path
- `state: directory` — desired state: "is a directory"; other values are `file`, `link`, `hard`, `touch`, `absent`
- `mode: '0750'` — octal mode AS A STRING (the leading 0 matters; YAML's number parser will strip it if you forget the quotes)

### The Story

This is the loop you will run in every other lab's Task 4. Write playbook → check → apply → verify with RHCSA in Task 5. Lab 00 is the only lab where Task 4 is "smoketest the loop itself."

### Expected Output

From `--check --diff`:

```
PLAY [Lab 00 Task 4 — smoketest of ansible.builtin.file] *********************
TASK [Ensure smoketest directory exists with mode 0750] **********************
--- before
+++ after
@@ -1,4 +1,4 @@
-state: absent
+state: directory
changed: [localhost]
TASK [Show the register result] **********************************************
ok: [localhost] => smoketest_result.changed = true ...
PLAY RECAP ********************************************************************
localhost : ok=2 changed=1 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

From apply (first run):

```
PLAY RECAP ********************************************************************
localhost : ok=2 changed=1 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

### Switches Table

| Switch / Key | Meaning | Why it matters |
|---|---|---|
| `--check` | Dry-run | Required RHCE habit; never apply blind |
| `--diff` | Show before/after diff | Reads exactly like `diff -u`; graders love this |
| `ansible.builtin.file:` | FQCN of the file module | Real module, not a shell wrapper |
| `state: directory` | Desired state | Other valid states: `file`, `link`, `hard`, `touch`, `absent` |
| `mode: '0750'` | Octal mode as string | YAML strips the leading 0 if unquoted — silent bug |
| `register: VAR` | Capture task result | Lets you debug the changed/stdout |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| `ansible-playbook --check --diff` | Dry-run with a readable diff |
| `register:` | Capture the module's result into a variable |
| `ansible.builtin.debug: var:` | Print the registered variable to stdout |
| Idempotence | Second apply with no system change must show changed=0 |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| **T00-A** | Writing `file:` instead of `ansible.builtin.file:` | Use FQCN every time, even on localhost |
| **T00-C** | Forgetting `--check --diff` and applying blind | Make it muscle memory: check, then apply |
| Mode-strip | `mode: 0750` (no quotes) → YAML parses 0750 as octal 488; module sets 0750 anyway but a future `mode: 0644` gets parsed as decimal 644 = `1204` octal = **silently wrong** | Always quote mode as a string: `mode: '0644'` |

### 🔁 Persistence Check

```bash
test -d /root/rhcsa_journal/_ansible_smoketest && echo "dir ok"
stat -c '%a %U:%G %n' /root/rhcsa_journal/_ansible_smoketest
```

Expect `750 root:root /root/rhcsa_journal/_ansible_smoketest`.

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab00/task4/done.txt > /dev/null <<EOF
lab=00 task=4
when=$(date -Is)
check_log=/root/rhcsa_journal/lab00/task4/check.log
apply_log=/root/rhcsa_journal/lab00/task4/apply.log
mode=$(stat -c '%a' /root/rhcsa_journal/_ansible_smoketest)
owner=$(stat -c '%U:%G' /root/rhcsa_journal/_ansible_smoketest)
EOF
cat /root/rhcsa_journal/lab00/task4/done.txt
```

### 🧹 Cleanup

Leave the smoketest directory in place; Task 5 verifies it. We will remove it in Task 5's cleanup.

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `ERROR! couldn't resolve module/action 'ansible.builtin.file'` | Reinstall `ansible-core`; the engine itself is broken |
| `Permission denied` writing the directory | Confirm `become: true` is present in the play |

> **STOP — confirm `apply.log` shows `changed=1` before Task 5.**

---

## Task 5 — RHCSA Verification Capstone: Prove the Playbook Run Worked

**Practice directory this task:** `/root/rhcsa_journal/lab00`

### 🔁 Warm-Up — Commands from Previous Labs

```bash
sudo mkdir -p /root/rhcsa_journal/lab00/task5
cd /root/rhcsa_journal/lab00/task5
date -Is | sudo tee start.txt
ls -ld /root/rhcsa_journal/_ansible_smoketest | sudo tee -a start.txt
echo "exit was: $?"
```

### Purpose

Use **only** RHCSA inspection commands (no `ansible` CLI) to prove the Task 4 playbook actually changed system state — and to prove **idempotence** by re-running the playbook and confirming it does nothing the second time.

### Main Command Block

Three RHCSA inspection commands plus an idempotence proof:

```bash
# 1) Existence + type
ls -ld /root/rhcsa_journal/_ansible_smoketest

# 2) Mode + ownership
stat -c 'mode=%a owner=%U group=%G path=%n' /root/rhcsa_journal/_ansible_smoketest

# 3) SELinux context (RHCSA inspection — Lab 06 deep-dives this)
ls -dZ /root/rhcsa_journal/_ansible_smoketest

# 4) Capture combined evidence
{ ls -ld /root/rhcsa_journal/_ansible_smoketest
  stat -c 'mode=%a owner=%U group=%G' /root/rhcsa_journal/_ansible_smoketest
  ls -dZ /root/rhcsa_journal/_ansible_smoketest
} 2>&1 | sudo tee /root/rhcsa_journal/lab00/task5/evidence.txt
```

Idempotence proof — re-run the same playbook and prove changed=0:

```bash
ansible-playbook /root/rhcsa_journal/lab00/task4/playbooks/smoketest.yml \
  2>&1 | sudo tee /root/rhcsa_journal/lab00/task5/rerun.log

grep -E '^localhost' /root/rhcsa_journal/lab00/task5/rerun.log
# Expect:  localhost  : ok=2 changed=0 unreachable=0 failed=0 ...
```

> Note: the idempotence proof uses `ansible-playbook` because *idempotence is a property only Ansible can demonstrate*. This is the one exception to the "no Ansible in Task 5" rule and applies only in Lab 00.

Persistence proof — answer the reboot question:

```bash
echo "REBOOT REASONING:" | sudo tee /root/rhcsa_journal/lab00/task5/reboot.txt
echo "If we rebooted now, the directory survives because mkdir/file-state on /root is persistent." | sudo tee -a /root/rhcsa_journal/lab00/task5/reboot.txt
test -d /root/rhcsa_journal/_ansible_smoketest && echo "still there after this turn" | sudo tee -a /root/rhcsa_journal/lab00/task5/reboot.txt
```

### Human-Readable Breakdown

A grader marks two things on an Ansible task:

1. The playbook syntax is correct (Task 4 proved that)
2. The system *actually* looks the way the playbook claims (Task 5 proves that)

So in Task 5 you **don't trust ansible-playbook's output**. You ask the filesystem directly: `stat`, `ls -ld`, `ls -dZ`. Then you re-run the playbook and confirm `changed=0` — that's the idempotence proof. If your second run says `changed=1`, the module was either misconfigured or you secretly used `command:`/`shell:` (the cardinal RHCE sin).

### Reading It Left to Right

`stat -c 'mode=%a owner=%U group=%G path=%n' /root/rhcsa_journal/_ansible_smoketest`

- `stat` — file metadata tool
- `-c FMT` — custom output format
- `%a` — octal access mode
- `%U` — owner name
- `%G` — group name
- `%n` — file name

### The Story

This is the auditor seat. You hand-type three commands a grader could type, you compare the output to what the playbook claimed, and you save the transcript to a journal that survives reboot. The next session, `cat /root/rhcsa_journal/lab00/task5/evidence.txt` tells you exactly what state you left the system in.

### Expected Output

```
drwxr-x---. 2 root root 6 May 27 15:04 /root/rhcsa_journal/_ansible_smoketest
mode=750 owner=root group=root path=/root/rhcsa_journal/_ansible_smoketest
unconfined_u:object_r:admin_home_t:s0 /root/rhcsa_journal/_ansible_smoketest
```

And the idempotence rerun:

```
PLAY RECAP ********************************************************************
localhost : ok=2 changed=0 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

`changed=0` is the proof.

### Switches Table

| Switch / Key | Meaning | Why it matters |
|---|---|---|
| `stat -c FMT` | Custom format string | Lets you assert mode + owner in one line |
| `ls -dZ` | SELinux context of the directory itself (not its contents) | The auditor's directory-context view |
| Re-run playbook | `changed=0` second time | The single best proof a module call is correct |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| Idempotence | Same playbook, same input → no change second time |
| Persistence | The change survives reboot; `/root/` files do, `/tmp/` files don't |
| Auditor reflex | Always verify with RHCSA inspection commands, not Ansible's own report |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| RHCE-cardinal | Trusting `changed=1` from ansible-playbook and skipping `stat`/`ls -lZ` | Always verify with ≥3 RHCSA inspection commands |
| Idempotence-blind | Running the playbook only once and declaring success | Always run twice; second run must be `changed=0` |

### 🔁 Persistence Check

```bash
test -d /root/rhcsa_journal/_ansible_smoketest && echo "dir survives"
test -f /root/rhcsa_journal/lab00/task4/playbooks/smoketest.yml && echo "playbook survives"
test -f /root/rhcsa_journal/lab00/task5/evidence.txt && echo "evidence survives"
```

All three are inside `/root/` — they survive reboot.

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab00/task5/done.txt > /dev/null <<EOF
lab=00 task=5
when=$(date -Is)
evidence=/root/rhcsa_journal/lab00/task5/evidence.txt
idempotent=$(grep -c 'changed=0' /root/rhcsa_journal/lab00/task5/rerun.log)
playbook_kept=/root/rhcsa_journal/lab00/task4/playbooks/smoketest.yml
status=lab00-complete
EOF
cat /root/rhcsa_journal/lab00/task5/done.txt
```

### 🧹 Cleanup

```bash
# Remove the smoketest directory; the playbook + journal stay
sudo rmdir /root/rhcsa_journal/_ansible_smoketest
ls -ld /root/rhcsa_journal/_ansible_smoketest 2>&1 | grep "No such file" && echo "cleanup ok"
```

The playbook stays in `/root/rhcsa_journal/lab00/task4/playbooks/smoketest.yml` so you can re-run it any time.

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| Second `ansible-playbook` run shows `changed=1` | Module call is wrong — usually means `mode: 0750` (unquoted) parsed as decimal; quote it |
| `rmdir: failed: Directory not empty` | Something wrote into the directory during the rerun; use `rm -rf` only after confirming the path |

> **STOP — record `lab00-complete` in the journal and move to Lab 01.**

---

## 🔁 ADHD Memory Refresh — End of Lab 00

If at any point during a later lab's Task 4 you see:

- `ERROR! couldn't resolve module/action 'ansible.posix.X'` → Lab 00 Task 2 was skipped, run it
- `config file = None` → Lab 00 Task 3 was skipped, run it
- `ping localhost` fails → Lab 00 Task 3 inventory is wrong, fix it
- `Permission denied` → `become: true` missing from play, or sudo unusable for the running user

---

## Lab 00 Complete When

```bash
ansible --version | head -1
ansible-galaxy collection list | grep -E 'ansible.posix|community.general'
ansible -m ping localhost | grep '"ping": "pong"'
ls /root/rhcsa_journal/lab00/task{1,2,3,4,5}/done.txt
cat /root/rhcsa_journal/lab00/task5/done.txt | grep lab00-complete
```

All five lines must succeed. Then proceed to Lab 01.
