# Lab 00b: Ansible Control Node — Collections, Config & First Playbook (`ansible-galaxy`, `~/.ansible.cfg`, inventory, ping)

- **Series:** linux-ops-mastery — Prerequisite Trilogy (run BEFORE Lab 01)
- **Trilogy:** `00a` (RHCSA) → **`00b` (Ansible — you are here)** → `00c` (Verify)
- **Career arcs covered:** RHCE EX294 (FQCN modules, collection install, idempotence, `--check --diff`, `register:`/`debug:`), CKA (Ansible-driven kubeadm), RHCA — RH362 (IdM via Ansible)
- **Prerequisite:** Lab 00a (you must have `ansible-core` installed and `/root/rhcsa_journal/` already built)
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = collections + config + first playbook apply, Task 2 = idempotent re-run + register/debug)
- **Practice Directory (rotation #00):** `/root/rhcsa_journal`
- **Sandbox:** `/root/rhcsa_journal/lab-00b`
- **Playbooks live at:** `/root/rhcsa_journal/lab-00b/playbooks/`
- **Traps rehearsed this lab:** **T00-A** (FQCN — `file:` vs `ansible.builtin.file:`) · **T00-B** (forgetting to install `community.general` and `ansible.posix` collections) · **T00-C** (editing `~/.ansible.cfg` in one shell, running playbooks in another, and not knowing which config the run actually used)

> **This lab's practice directory is: `/root/rhcsa_journal`** — every task references it in at least two commands. The targets the playbook touches live at `/root/rhcsa_journal/lab-00b/`, the playbooks themselves live at `/root/rhcsa_journal/lab-00b/playbooks/`, and the per-user config lives at `~/.ansible.cfg` and `~/inventory` (i.e., `/root/.ansible.cfg` and `/root/inventory` when running as root).

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
echo "📁  PRACTICE DIR: /root/rhcsa_journal/lab-00b"
echo ""
echo "🧰 Lab 00a checks (must pass before Task 1):"
test -f /root/rhcsa_journal/lab-00a/task1/done.txt && echo "  ✅ lab-00a task1 done (ansible-core installed)"
test -f /root/rhcsa_journal/lab-00a/task2/done.txt && echo "  ✅ lab-00a task2 done (journal tree built)"
rpm -q ansible-core 2>&1 | head -n 1
ansible --version | head -n 2
```

> **STOP — if either `done.txt` check above failed, return to Lab 00a. Do not attempt Task 1 without `ansible-core` installed and `/root/rhcsa_journal/` already laid down.**

---

## 🎯 Objective

Lay down the Ansible half of the control node. By the end of Lab 00b you will have:

1. `ansible.posix` and `community.general` collections installed via `ansible-galaxy collection install`
2. A working `~/.ansible.cfg` that points at a local inventory, enables YAML stdout, and turns on `become: true` by default
3. A working `~/inventory` registering `localhost` with `ansible_connection=local`
4. `ansible -m ping localhost` returning `"ping": "pong"`
5. Your **first** playbook — `lab-00b/playbooks/smoketest.yml` — written, previewed with `--check --diff`, applied, and re-applied to prove `changed=0` on the second run
6. The `register:` + `debug:` audit pattern muscle-memorized so it does not feel novel by the time you get to Lab 11b

After this lab, every later lab's Task 4 just *runs* — no setup, no surprises. Lab 00c will verify the whole stack.

---

## 🧠 Concept: FQCN + Idempotence Are the Two Habits That Define RHCE Style

There are two habits that distinguish an RHCE-shaped playbook from a "Ansible-as-an-rm-wrapper" hack: **FQCN** (Fully Qualified Collection Names) and **idempotence**.

```
   ┌───────────────────────────────────────────────────────────────┐
   │  FQCN: ansible.builtin.file:   ← real module, version-stable │
   │        file:                   ← short alias, depends on      │
   │                                  collection-loading defaults  │
   │                                                                │
   │  Idempotence: same playbook, same input → no change second time│
   │      first run:   ok=1 changed=1 failed=0                      │
   │      second run:  ok=1 changed=0 failed=0   ← THE proof line  │
   └───────────────────────────────────────────────────────────────┘
```

`ansible.builtin.file:` is the real module. `file:` is a short alias that depends on Ansible's collection-loading defaults — which can change between versions. RHCE graders penalize the short form because it is fragile. Use FQCN every time, on every module, even on localhost. That is **Trap T00-A**.

Idempotence is the **declarative-state contract**. A correctly-written `state: directory` task can be applied 1, 10, or 1000 times — the first run does the work, every later run is a no-op (`changed=0`). The way you prove it: write the play, apply it, **re-apply it**, and read the PLAY RECAP. If the second run says `changed=1`, the module call is wrong (usually `command:` or `shell:` instead of a real module).

Two more traps lurk in this lab. **T00-B** is forgetting to install the collections — without `ansible.posix` + `community.general` on the control node, Lab 64's `firewalld:` task and Lab 06's `sefcontext:` task fail with `couldn't resolve module`. **T00-C** is editing `~/.ansible.cfg` in one shell, running a playbook in another, and not realising the playbook used a different config. The single command that prevents T00-C: `ansible --version | grep "config file"` **before** every Task 4 run.

---

## 📚 Module + Config Reference (everything for Tasks 1–2)

| Token | Meaning | Why an RHCE candidate needs it |
|---|---|---|
| `ansible-galaxy collection install NAMESPACE.NAME` | Install a collection from Galaxy | The RHCE-shaped way to get `ansible.posix` and `community.general` |
| `ansible-galaxy collection list` | List installed collections | "Did `ansible.posix` actually land?" |
| `ansible-doc FQCN` | Read the module's docs from the local install | Proof the module is reachable |
| `~/.ansible.cfg` `[defaults]` `inventory =` | Default inventory path | Eliminates "where is my inventory?" confusion |
| `~/.ansible.cfg` `[defaults]` `stdout_callback = yaml` | Readable diffs in `--check --diff` | Graders read playbook output — make it readable |
| `~/.ansible.cfg` `[privilege_escalation]` `become = True` | Default to root on every play | Matches the `sudo` workflow used in every Task 4 |
| `ansible_connection=local` | Skip SSH for this host | Why `ansible -m ping localhost` works |
| `ansible -m ping HOST` | Sanity ping — config + inventory + Python interp + sudo all line up | First diagnostic in every later Task 4 |
| `ansible --version \| grep "config file"` | Show which config is in effect | The one-command answer to T00-C |
| `ansible-playbook --check --diff PLAYBOOK` | Dry-run preview | Mandatory RHCE habit |
| `register: VAR` + `debug: var: VAR` | The grader's audit trail | Read what Ansible saw, not just what it did |
| `ansible.builtin.file: state=directory mode='0750'` | Declarative directory creation | The FQCN form Lab 11b/12b/etc. all build on |

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i

# Sandbox + playbook home for this lab
mkdir -p /root/rhcsa_journal/lab-00b/{task1,task2}
mkdir -p /root/rhcsa_journal/lab-00b/playbooks
cd /root/rhcsa_journal/lab-00b

# Mode and ownership, RHCSA-style (Lab 00a habit carried forward)
chmod 0750 /root/rhcsa_journal/lab-00b
chmod 0750 /root/rhcsa_journal/lab-00b/playbooks
chown -R root:root /root/rhcsa_journal/lab-00b

# Pre-flight: confirm we are starting from Lab 00a's end state
rpm -q ansible-core | tee /root/rhcsa_journal/lab-00b/setup.txt
ansible --version | head -n 4 | tee -a /root/rhcsa_journal/lab-00b/setup.txt
ls -ld /root/rhcsa_journal/lab-00b /root/rhcsa_journal/lab-00b/playbooks \
                                                  | tee -a /root/rhcsa_journal/lab-00b/setup.txt
echo "exit was: $?"
```

> **STOP — paste the setup.txt output before Task 1. Confirm `config file = None` (we will fix it in Task 1).**

---

## Task 1 — Install collections, write `~/.ansible.cfg` + `~/inventory`, run the first playbook

**Practice directory this task:** `/root/rhcsa_journal` · the persistent journal. The playbook itself lives at `/root/rhcsa_journal/lab-00b/playbooks/smoketest.yml`, the config lives at `~/.ansible.cfg` (`/root/.ansible.cfg` for root), the inventory at `~/inventory` (`/root/inventory`).

### 🔁 Warm-Up — commands woven into Task 1

```bash
cd /root/rhcsa_journal/lab-00b/task1
date -Is                                            2>&1 | tee start.txt
rpm -q ansible-core                                 2>&1 | tee -a start.txt
ansible --version | head -n 1                       2>&1 | tee -a start.txt
ansible --version | grep "config file"              2>&1 | tee -a start.txt
ansible-galaxy collection list 2>&1 | head -n 6     2>&1 | tee -a start.txt
test -d /root/rhcsa_journal/lab-00b/playbooks && echo "playbook dir OK"
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 00a: the `2>&1 | tee` capture pattern and `set -o pipefail` discipline persist. The pre-Task-1 snapshot now includes `config file = None` — by the end of Task 1 that line must say `/root/.ansible.cfg`.

### Purpose

Install the two RHCE-expected collections (`ansible.posix`, `community.general`), write the minimal per-user config (`~/.ansible.cfg` + `~/inventory`), prove the control node works end-to-end with `ansible -m ping localhost`, then write the first playbook and run it with `--check --diff` followed by an apply. Every later Task 4 starts here.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `rpm -q ansible-core` | The pre-condition gate — if this fails we return to Lab 00a |
| `ansible --version \| grep "config file"` | The T00-C reflex — captured pre AND post the `~/.ansible.cfg` write |
| `ansible-galaxy collection list` | The T00-B reflex — captured pre AND post collection install |
| `2>&1 \| tee` | Captures install output, check output, apply output into the journal |
| `set -o pipefail` | Catches a silent failure in the `ansible-playbook | tee` chain |
| `$(date -Is)` | Stamps every journal artifact for the audit timeline |

### Main command block

```bash
cd /root/rhcsa_journal/lab-00b/task1

# ── Step 1: Install the two RHCE-expected collections ────────────────
ansible-galaxy collection install ansible.posix     2>&1 | tee galaxy-install.log
ansible-galaxy collection install community.general 2>&1 | tee -a galaxy-install.log

# Verify the collections landed (T00-B reflex)
ansible-galaxy collection list \
  | grep -E 'ansible.posix|community.general'       2>&1 | tee collections.txt

# Cross-check: every module we will rely on must answer ansible-doc
ansible-doc ansible.posix.selinux         | head -n 3 | tee -a collections.txt
ansible-doc community.general.sefcontext  | head -n 3 | tee -a collections.txt

# ── Step 2: Write ~/.ansible.cfg ─────────────────────────────────────
tee /root/.ansible.cfg > /dev/null <<'EOF'
[defaults]
inventory          = /root/inventory
host_key_checking  = False
retry_files_enabled = False
stdout_callback    = yaml
nocows             = 1

[privilege_escalation]
become             = True
become_method      = sudo
become_user        = root
become_ask_pass    = False
EOF

# ── Step 3: Write ~/inventory ────────────────────────────────────────
tee /root/inventory > /dev/null <<'EOF'
[control]
localhost ansible_connection=local

[control:vars]
ansible_python_interpreter=/usr/bin/python3
EOF

# ── Step 4: Prove the config + inventory are in effect (T00-C reflex) ─
ansible --version | grep "config file"              2>&1 | tee config-file.txt
ansible-inventory --list                            2>&1 | tee inventory-dump.txt
ansible -m ping localhost                           2>&1 | tee ping.txt

# ── Step 5: Write the first playbook (FQCN — T00-A reflex) ───────────
tee /root/rhcsa_journal/lab-00b/playbooks/smoketest.yml > /dev/null <<'EOF'
---
- name: "Lab 00b Task 1 — first playbook: ansible.builtin.file state=directory"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true

  tasks:
    - name: "Ensure the smoketest directory exists with mode 0750"
      ansible.builtin.file:
        path: /root/rhcsa_journal/_ansible_smoketest
        state: directory
        owner: root
        group: root
        mode: '0750'
      register: smoketest_result

    - name: "Show the register result (the RHCE audit-trail pattern)"
      ansible.builtin.debug:
        var: smoketest_result
EOF

# ── Step 6: --check --diff preview (mandatory RHCE habit) ────────────
ansible-playbook --check --diff \
  /root/rhcsa_journal/lab-00b/playbooks/smoketest.yml \
  2>&1 | tee check.log

# ── Step 7: Apply for real ───────────────────────────────────────────
ansible-playbook \
  /root/rhcsa_journal/lab-00b/playbooks/smoketest.yml \
  2>&1 | tee apply.log

# ── Step 8: RHCSA-side verification — did the directory actually appear? ─
stat -c 'mode=%a owner=%U:%G path=%n' /root/rhcsa_journal/_ansible_smoketest \
                                                    2>&1 | tee stat.txt
echo "exit was: $?"
```

### The playbook (`smoketest.yml`)

```yaml
---
- name: "Lab 00b Task 1 — first playbook: ansible.builtin.file state=directory"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true

  tasks:
    - name: "Ensure the smoketest directory exists with mode 0750"
      ansible.builtin.file:
        path: /root/rhcsa_journal/_ansible_smoketest
        state: directory
        owner: root
        group: root
        mode: '0750'
      register: smoketest_result

    - name: "Show the register result (the RHCE audit-trail pattern)"
      ansible.builtin.debug:
        var: smoketest_result
```

### Human-readable breakdown

1. `ansible-galaxy collection install ansible.posix` and `... community.general` download both collections from `galaxy.ansible.com` into `/root/.ansible/collections/ansible_collections/`. These are the two collections RHCE expects you to have — `firewalld`, `selinux`, `mount`, `acl`, `at` live in `ansible.posix`; `sefcontext`, `nmcli`, `lvol`, `parted` live in `community.general`. **Trap T00-B** is shipping a playbook without them.
2. `~/.ansible.cfg` is the per-user config Ansible reads on startup. Key knobs: `inventory = /root/inventory` points at the file you control; `stdout_callback = yaml` makes `--check --diff` output readable; `nocows = 1` disables the ASCII cow that some Ansible versions print; `[privilege_escalation]` flips `become: true` to the default so every later play matches the `sudo` workflow.
3. `~/inventory` is the host list. `localhost ansible_connection=local` tells Ansible "don't SSH to localhost — exec the modules directly in this Python interpreter." The `ansible_python_interpreter=/usr/bin/python3` line pins which Python the engine uses, eliminating "no Python found" warnings.
4. `ansible --version | grep "config file"` is the **T00-C reflex** — it tells you exactly which config the engine is using right now. Before the cfg write, that line says `config file = None`. After the cfg write, it says `config file = /root/.ansible.cfg`. Every later Task 4 starts with this grep.
5. `ansible -m ping localhost` is the canonical sanity ping — it loads the config, parses the inventory, picks the Python interpreter, runs the `ping` module, and reports back. If `"ping": "pong"` comes back, the whole stack is wired correctly.
6. The first playbook uses **`ansible.builtin.file`** — FQCN, real module — with `state: directory`, an octal `mode: '0750'` (quoted — Lab 00a-era YAML parsers strip the leading 0 if unquoted, silently turning `0644` into decimal 644 = octal 1204), and `register: smoketest_result`. The second task is `ansible.builtin.debug: var:` so you can read what `register:` captured.
7. `--check --diff` runs the playbook in dry-run mode and prints a unified diff of what would change. Always preview before applying. **Always.**
8. The apply does the same actions but for real; the directory appears at `/root/rhcsa_journal/_ansible_smoketest` with mode 0750, owner root, group root.
9. The RHCSA-side `stat -c` verification is the grader's reflex — never trust the play's own output, ask the filesystem directly.

### Reading it left to right

`ansible-galaxy collection install ansible.posix`

- `ansible-galaxy` — the collections/roles installer that ships with `ansible-core`
- `collection` — subcommand namespace (vs. `role`)
- `install` — verb
- `ansible.posix` — `namespace.name` — fully-qualified collection name (FQCN at the collection level)

`tee /root/.ansible.cfg > /dev/null <<'EOF'` ... `EOF`

- `tee` — copy stdin to stdout AND to the named file
- `/root/.ansible.cfg` — the file to write
- `> /dev/null` — silence the stdout copy (we don't need it printed)
- `<<'EOF'` — heredoc, single-quoted to disable variable expansion inside the doc

`ansible-playbook --check --diff PATH`

- `ansible-playbook` — the playbook driver
- `--check` — dry-run; no actual changes
- `--diff` — show before/after diffs
- `PATH` — the YAML file

`ansible.builtin.file:` `path:` `state: directory` `mode: '0750'`

- `ansible.builtin.file` — the FQCN of the file module
- `path:` — absolute filesystem path
- `state: directory` — desired state; other values: `file`, `link`, `hard`, `touch`, `absent`
- `mode: '0750'` — octal mode AS A STRING (the leading 0 matters; quote it always)

### The story

This is the loop you will run in every other lab's Task 4. Write playbook → check → apply → re-apply (Task 2) → verify with RHCSA inspection (Lab Nc). Lab 00b is the only place the loop is the **subject** of the lab — everywhere else, you'll be focused on whatever the module actually does, not the loop itself.

The `register:` + `debug:` pattern is the most under-practiced RHCE habit. Graders don't only check whether the directory exists — they read the **playbook output** to confirm Ansible reported what it should have. A play that creates a file but emits no `debug:` is technically passing, but a play that creates a file **and** dumps the register variable is the kind they mark up.

The T00-C reflex matters more than it sounds. The 90% case where Ansible behaves "weirdly" is that you edited one config file but the play picked up a different one — most often because you opened a second shell where `~/.ansible.cfg` did not yet exist when the shell started caching the path. `ansible --version | grep "config file"` is the one command that ends every "but I changed it!" argument in three seconds.

### Expected output

```text
# galaxy-install.log (tail):
Starting galaxy collection install process
Process install dependency map
Starting collection install process
Downloading https://galaxy.ansible.com/.../ansible-posix-1.5.x.tar.gz ...
Installing 'ansible.posix:1.5.x' to '/root/.ansible/collections/ansible_collections/ansible/posix'
ansible.posix:1.5.x was installed successfully
...
community.general:7.x.x was installed successfully

# collections.txt:
ansible.posix      1.5.x
community.general  7.x.x
> SELINUX  ansible.posix.selinux
       Change policy and state of SELinux ...
> SEFCONTEXT  community.general.sefcontext
       Manages SELinux file context mapping ...

# config-file.txt:
  config file = /root/.ansible.cfg

# inventory-dump.txt:
{
    "_meta": { "hostvars": { "localhost": { "ansible_connection": "local", "ansible_python_interpreter": "/usr/bin/python3" } } },
    "all": { "children": [ "control", "ungrouped" ] },
    "control": { "hosts": [ "localhost" ] }
}

# ping.txt:
localhost | SUCCESS => {
    "ansible_facts": { "discovered_interpreter_python": "/usr/bin/python3" },
    "changed": false,
    "ping": "pong"
}

# check.log (--check --diff):
PLAY [Lab 00b Task 1 — first playbook: ansible.builtin.file state=directory] **
TASK [Ensure the smoketest directory exists with mode 0750] *******************
--- before
+++ after
@@ -1,4 +1,4 @@
-state: absent
+state: directory
changed: [localhost]
TASK [Show the register result (the RHCE audit-trail pattern)] ****************
ok: [localhost] => smoketest_result.changed = true ...
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0

# apply.log (first real run):
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0

# stat.txt:
mode=750 owner=root:root path=/root/rhcsa_journal/_ansible_smoketest
exit was: 0
```

> Five separate pieces of evidence: collections installed, config loaded, inventory parsed, ping returned `pong`, smoketest directory landed with the right mode. That is what an RHCE-shaped first playbook produces.

### Switches

| Token | Meaning |
|---|---|
| `ansible-galaxy collection install NAME` | Install a collection from Galaxy into the user collection path |
| `ansible-galaxy collection list` | List installed collections |
| `ansible-doc FQCN` | Print the module's docs from the local install |
| `ansible -m MODULE -a 'ARGS' HOST` | Ad-hoc module invocation (`ansible -m ping localhost`) |
| `ansible-playbook --check` | Dry-run |
| `ansible-playbook --diff` | Show before/after diffs |
| `hosts: localhost` + `connection: local` | Run against the control node itself, skipping SSH |
| `gather_facts: false` | Skip the implicit `setup` module — faster on focused plays |
| `ansible.builtin.file:` | FQCN of the file module |
| `state: directory` | Desired state — the path must be a directory |
| `mode: '0750'` | Octal mode as a string (always quote) |
| `register: VAR` | Capture task result into a playbook variable |
| `ansible.builtin.debug: var: VAR` | Print the captured variable |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | FQCN (`ansible.builtin.MOD`) | Fully-qualified module name — required RHCE style |
|   | Collection install path | `/root/.ansible/collections/ansible_collections/` for root |
|   | `~/.ansible.cfg` precedence | Per-user config overrides `/etc/ansible/ansible.cfg` |
|   | `ansible_connection=local` | Skip SSH for this host; exec modules in the local Python |
|   | `become: true` default | Every play runs as root by default — matches `sudo` workflow |
|   | `stdout_callback = yaml` | Readable diffs in `--check --diff` |
|   | `--check --diff` preview | Always preview before applying — mandatory RHCE habit |
|   | `register:` + `debug:` | The audit trail RHCE graders read |
|   | Quoted octal `mode: '0750'` | Unquoted mode is YAML-parsed as decimal — silent bug |
| 🪤 | **Trap Risk T00-A** | Writing `file:` instead of `ansible.builtin.file:`. Refused on RHCE grading. |
| 🪤 | **Trap Risk T00-B** | Forgetting `ansible-galaxy collection install ansible.posix community.general`. Lab 64 (firewalld), Lab 06 (sefcontext) will fail with "couldn't resolve module." |
| 🪤 | **Trap Risk T00-C** | Editing `~/.ansible.cfg` in one shell, running the playbook in another. Run `ansible --version \| grep "config file"` BEFORE every later Task 4. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Collections installed | `ansible-galaxy collection list \| grep -E 'ansible.posix\|community.general'` | Both lines must appear |
| Config loaded | `ansible --version \| grep "config file"` | Must print `/root/.ansible.cfg`, not `None` |
| Inventory works | `ansible-inventory --list \| grep localhost` | Localhost must appear in the JSON dump |
| Ping works | `ansible -m ping localhost \| grep '"ping": "pong"'` | The four-stack proof: config + inventory + python + sudo |
| First playbook applied | `stat -c '%a %U:%G %n' /root/rhcsa_journal/_ansible_smoketest` | Mode 750 owner root:root |
| Playbook persisted in /root | `ls /root/rhcsa_journal/lab-00b/playbooks/smoketest.yml` | Survives reboot |

> **Reboot reasoning:** Collections live at `/root/.ansible/collections/` (root partition — persistent). `~/.ansible.cfg` and `~/inventory` are at `/root/` (persistent). The playbook at `/root/rhcsa_journal/lab-00b/playbooks/smoketest.yml` is persistent. The smoketest **directory** at `/root/rhcsa_journal/_ansible_smoketest` is also under `/root/` — also persistent. After a reboot you could re-run the playbook and it would report `changed=0` because the desired state already matches. That is the idempotence proof Task 2 demonstrates.

### Journal write — BEFORE cleanup

```bash
LAB=lab-00b
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

# Most of this task's evidence already lives at /root/rhcsa_journal/lab-00b/task1/
# so we just consolidate the done.txt + notes.txt summary.

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
COLLECTIONS_POSIX:   $(ansible-galaxy collection list | awk '/ansible.posix/ {print $2; exit}')
COLLECTIONS_GENERAL: $(ansible-galaxy collection list | awk '/community.general/ {print $2; exit}')
CONFIG_FILE:         $(ansible --version | awk '/config file/ {print $4}')
PING:                $(ansible -m ping localhost 2>&1 | grep -c '"ping": "pong"')
SMOKETEST_MODE:      $(stat -c '%a' /root/rhcsa_journal/_ansible_smoketest 2>/dev/null)
PLAYBOOK:            /root/rhcsa_journal/lab-00b/playbooks/smoketest.yml
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Install collections + write ~/.ansible.cfg + ~/inventory + first playbook
COMMANDS: ansible-galaxy collection install, tee ~/.ansible.cfg, ansible-inventory --list,
          ansible -m ping localhost, ansible-playbook --check --diff, ansible-playbook
TRAPS:    T00-A rehearsed (FQCN used everywhere)
          T00-B rehearsed (both collections installed BEFORE running anything)
          T00-C rehearsed (config-file path captured PRE and POST cfg write)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — re-run the playbook for idempotence proof (changed=0)
EOF

ls -la "$JDIR"
cat "$JDIR/done.txt"
echo "exit was: $?"
```

### 🧹 Cleanup

Nothing to clean. The collections, `~/.ansible.cfg`, `~/inventory`, the playbook at `/root/rhcsa_journal/lab-00b/playbooks/smoketest.yml`, and the smoketest directory at `/root/rhcsa_journal/_ansible_smoketest` are all intentionally persistent — Task 2 re-runs the playbook against the same target, and Lab 00c verifies the whole stack.

### Troubleshoot

| Symptom | Fix |
|---|---|
| `ERROR! Failed to download collection` | Check `curl -I https://galaxy.ansible.com/` — proxy/firewall issue |
| `ansible-doc: module not found` after install | Open a new shell so `$ANSIBLE_COLLECTIONS_PATH` is re-evaluated |
| `config file = None` after writing `~/.ansible.cfg` | You ran `ansible` as a non-root user — `~/.ansible.cfg` only applies to that user's $HOME |
| `Could not match supplied host pattern` | Re-run `ansible-inventory --list` and confirm `localhost` appears |
| `--check --diff` shows no diff | `--diff` for `state: directory` only shows the state line — no file content to diff |
| `ERROR! couldn't resolve module/action 'ansible.builtin.file'` | Reinstall `ansible-core`; the engine itself is broken |
| `Permission denied` writing the directory | Confirm `become: true` is present in the play (it is, in our smoketest) |
| YAML "found character that cannot start any token" | Indentation mismatch — check the playbook uses spaces, not tabs |

> **STOP — paste `cat $JDIR/done.txt` and the PLAY RECAP line from `apply.log` (must show `changed=1`) before Task 2.**

---

## Task 2 — Re-run for idempotence proof (`changed=0`) + the `register:`/`debug:` pattern

**Practice directory this task:** `/root/rhcsa_journal` · the same playbook from Task 1 lives at `/root/rhcsa_journal/lab-00b/playbooks/smoketest.yml`. Task 2 re-runs it without edits and proves the second run is `changed=0`.

### 🔁 Warm-Up — commands woven into Task 2

```bash
cd /root/rhcsa_journal/lab-00b/task2
date -Is                                            2>&1 | tee start.txt
ansible --version | grep "config file"              2>&1 | tee -a start.txt
test -d /root/rhcsa_journal/_ansible_smoketest      && echo "target exists — expected"
stat -c 'mode=%a owner=%U:%G %n' /root/rhcsa_journal/_ansible_smoketest \
                                                    2>&1 | tee -a start.txt
test -f /root/rhcsa_journal/lab-00b/playbooks/smoketest.yml && echo "playbook exists — expected"
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: the smoketest directory should still be at mode 750 owner root:root. If `stat` shows different metadata, something altered it between tasks — the idempotence proof below will report `changed=1` and we will know exactly why.

### Purpose

Re-run the **exact same playbook** from Task 1 — no edits — and prove the second run reports `changed=0`. Then write a second playbook that demonstrates the `register:` + `debug:` pattern more explicitly, so the audit-trail habit is muscle memory by the end of this trilogy.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `ansible --version \| grep "config file"` | T00-C reflex — confirm `/root/.ansible.cfg` is still in effect (no drift since Task 1) |
| `stat -c 'mode=%a owner=%U:%G'` | Pre-condition: the smoketest directory matches the playbook declaration |
| `test -d` / `test -f` | Guards: directory + playbook must both exist before re-run |
| `2>&1 \| tee` | Captures the re-run output — the **proof artifact** |
| `set -o pipefail` | Catches a silent failure in the `ansible-playbook | tee` chain |
| `$(date -Is)` | Stamps the journal for the audit timeline |

### Main command block

```bash
cd /root/rhcsa_journal/lab-00b/task2

# ── Step 1: Re-run the SAME playbook from Task 1 — no edits ──────────
ansible-playbook \
  /root/rhcsa_journal/lab-00b/playbooks/smoketest.yml \
  2>&1 | tee rerun.log

# ── Step 2: Inspect the PLAY RECAP — changed=0 is the win condition ──
grep -E "PLAY RECAP|changed=" rerun.log             2>&1 | tee recap.txt

# ── Step 3: Verify the smoketest directory is UNTOUCHED ──────────────
stat -c 'mode=%a owner=%U:%G mtime=%y %n' \
  /root/rhcsa_journal/_ansible_smoketest            2>&1 | tee stat-after.txt

# ── Step 4: Write a second playbook demonstrating register/debug explicitly
tee /root/rhcsa_journal/lab-00b/playbooks/register-demo.yml > /dev/null <<'EOF'
---
- name: "Lab 00b Task 2 — explicit register: + debug: demonstration"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true

  tasks:
    - name: "Stat the smoketest directory via ansible.builtin.stat"
      ansible.builtin.stat:
        path: /root/rhcsa_journal/_ansible_smoketest
      register: smoketest_stat

    - name: "Show the stat result.exists and result.stat.mode"
      ansible.builtin.debug:
        msg: "exists={{ smoketest_stat.stat.exists }} mode={{ smoketest_stat.stat.mode }}"

    - name: "Re-assert state=directory mode=0750 (must be changed=false)"
      ansible.builtin.file:
        path: /root/rhcsa_journal/_ansible_smoketest
        state: directory
        owner: root
        group: root
        mode: '0750'
      register: reassert_result

    - name: "Show whether the re-assert changed anything (must be False)"
      ansible.builtin.debug:
        msg: "reassert.changed={{ reassert_result.changed }}"
EOF

# ── Step 5: Apply the register-demo playbook and confirm changed=0 ────
ansible-playbook \
  /root/rhcsa_journal/lab-00b/playbooks/register-demo.yml \
  2>&1 | tee register-demo.log

grep -E "PLAY RECAP|changed=|changed=False|changed=True" register-demo.log \
                                                    2>&1 | tee register-recap.txt
echo "exit was: $?"
```

### The second playbook (`register-demo.yml`)

```yaml
---
- name: "Lab 00b Task 2 — explicit register: + debug: demonstration"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true

  tasks:
    - name: "Stat the smoketest directory via ansible.builtin.stat"
      ansible.builtin.stat:
        path: /root/rhcsa_journal/_ansible_smoketest
      register: smoketest_stat

    - name: "Show the stat result.exists and result.stat.mode"
      ansible.builtin.debug:
        msg: "exists={{ smoketest_stat.stat.exists }} mode={{ smoketest_stat.stat.mode }}"

    - name: "Re-assert state=directory mode=0750 (must be changed=false)"
      ansible.builtin.file:
        path: /root/rhcsa_journal/_ansible_smoketest
        state: directory
        owner: root
        group: root
        mode: '0750'
      register: reassert_result

    - name: "Show whether the re-assert changed anything (must be False)"
      ansible.builtin.debug:
        msg: "reassert.changed={{ reassert_result.changed }}"
```

### Human-readable breakdown

1. Step 1 re-runs `smoketest.yml` — the same playbook from Task 1, no edits, same arguments, same target. The output should be identical structurally except the PLAY RECAP `changed=` field drops to 0.
2. Step 2 extracts the PLAY RECAP line specifically. `changed=0` is the **canonical** RHCE idempotence proof. If it shows `changed=1`, the module call was wrong (most likely: `command:` or `shell:` in place of a real module, or a non-idempotent action).
3. Step 3 stats the target — the `mtime` is unchanged from Task 1's apply, which is independent evidence the file was not touched on the re-run. (If `mode: '0750'` had been wrong, Ansible would have set it on the re-run and `mtime` would update.)
4. Step 4 writes a second playbook that uses `ansible.builtin.stat:` to capture filesystem metadata into `smoketest_stat`, then `debug: msg:` to print fields from that variable. Then it re-asserts `state: directory mode: '0750'` and registers the result — expected `changed: False`. This is the **explicit** register/debug pattern RHCE graders look for.
5. Step 5 applies the register-demo playbook and greps the PLAY RECAP — must show `changed=0` overall, and the `reassert.changed=False` debug line must appear.

### Reading it left to right

`ansible-playbook /path/to/smoketest.yml`

- `ansible-playbook` — the playbook driver
- `/path/to/smoketest.yml` — the playbook file (no `--check` this time; this is a real apply that should be a no-op)

`grep -E "PLAY RECAP|changed="`

- `grep` — line-matching
- `-E` — extended regex (so `|` works as alternation)
- `"PLAY RECAP|changed="` — match lines containing either string

`ansible.builtin.stat:` `path:` ... `register: VAR`

- `ansible.builtin.stat` — FQCN of the stat module
- `path:` — file to stat
- `register: VAR` — capture the result into a variable named VAR; that variable now contains `.stat.exists`, `.stat.mode`, `.stat.mtime`, etc.

`debug: msg: "exists={{ VAR.stat.exists }} mode={{ VAR.stat.mode }}"`

- `debug` — the debug module
- `msg:` — the string to print
- `{{ ... }}` — Jinja2 expression interpolation
- `VAR.stat.exists` — dotted access into the registered structure

### The story

Idempotence is **the** RHCE concept. Every grader knows that imperative wrappers (`command:`, `shell:`) can be passed off as "Ansible playbooks" by candidates who don't understand the difference. The way they tell the difference: they re-run your play and look at the PLAY RECAP. A correctly-written play reports `changed=0` on the second run. An imperative wrapper reports `changed=1` (or fails because the imperative command errored on the second run).

The discipline is: every time you write a task, run it twice. Second run must be `changed=0`. If it's not, fix the module call before moving on.

The `register:` + `debug:` pattern is the **audit-trail half** of the RHCE-shaped playbook. It is not enough to make the change — you want the playbook output to tell a reader (or grader) what state the system was in before and after. The two-task pattern (stat + debug, then file + debug) makes that visible: the play prints "exists=True mode=0750" from the stat, then prints "reassert.changed=False" from the re-assert. A grader reads those two lines and knows the play is honest.

### Expected output

```text
# rerun.log (PLAY RECAP only):
PLAY [Lab 00b Task 1 — first playbook: ansible.builtin.file state=directory] **
TASK [Ensure the smoketest directory exists with mode 0750] *******************
ok: [localhost]
TASK [Show the register result (the RHCE audit-trail pattern)] ****************
ok: [localhost] => smoketest_result.changed = false ...
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0

# stat-after.txt:
mode=750 owner=root:root mtime=2026-05-28 19:58:14.000000000 -0400 /root/rhcsa_journal/_ansible_smoketest

# register-demo.log:
PLAY [Lab 00b Task 2 — explicit register: + debug: demonstration] *************
TASK [Stat the smoketest directory via ansible.builtin.stat] ******************
ok: [localhost]
TASK [Show the stat result.exists and result.stat.mode] ***********************
ok: [localhost] => {
    "msg": "exists=True mode=0750"
}
TASK [Re-assert state=directory mode=0750 (must be changed=false)] ************
ok: [localhost]
TASK [Show whether the re-assert changed anything (must be False)] ************
ok: [localhost] => {
    "msg": "reassert.changed=False"
}
PLAY RECAP ********************************************************************
localhost                  : ok=4    changed=0    unreachable=0    failed=0
exit was: 0
```

> **The two key lines: `changed=0` in both PLAY RECAPs, and `reassert.changed=False` in the debug.** If either is wrong, the module call needs to be fixed before moving to Lab 00c.

### Switches

| Token | Meaning |
|---|---|
| `ansible-playbook PATH` | Apply the playbook |
| `grep -E "A\|B"` | Extended regex — match lines with A or B |
| `ansible.builtin.stat:` | FQCN of the stat module (read-only) |
| `register: VAR` | Capture task result into a variable |
| `debug: msg: "..."` | Print a formatted message |
| `{{ VAR.field }}` | Jinja2 expression — dotted access into a registered result |
| `changed=0` | The idempotence-proof line in PLAY RECAP |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | Idempotence proof | Re-run must show `changed=0` — RHCE acceptance test |
|   | Declarative vs imperative | `file: state=directory` ≠ `command: mkdir`. The first re-runs cleanly; the second does not. |
|   | PLAY RECAP audit | `ok=N changed=M failed=K` — M should be 0 on re-run |
|   | `ansible.builtin.stat` | Read-only stat module — captures `.stat.exists`, `.stat.mode`, `.stat.mtime`, etc. |
|   | `register:` + `debug: msg:` | The explicit audit-trail pattern with formatted output |
|   | `{{ var.subfield }}` | Jinja2 dotted access into a registered result |
|   | mtime as evidence | If the second run didn't change anything, `mtime` is unchanged from the first apply |
| 🪤 | **Trap Risk T00-A (reinforced)** | A `file:` (non-FQCN) task can sometimes still work but is fragile across Ansible versions. Always FQCN. |
| 🪤 | **Trap Risk T00-B (reinforced)** | If `ansible-galaxy collection list` shows neither collection, this lab's playbook still works (it uses `ansible.builtin` only) — but the next lab that needs `ansible.posix.firewalld` will fail. |
| 🪤 | **Trap Risk T00-C (reinforced)** | If `ansible --version` shows `config file = None` here, your shell is not using `~/.ansible.cfg`. Check `$HOME`, check `--user`, check whether you `sudo -i`'d. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Idempotence proven | `grep changed= /root/rhcsa_journal/lab-00b/task2/rerun.log` | Must show `changed=0` in PLAY RECAP |
| mtime stable | `stat -c '%y' /root/rhcsa_journal/_ansible_smoketest` | Independent evidence the re-run did not touch the inode |
| register-demo played | `grep "reassert.changed=" /root/rhcsa_journal/lab-00b/task2/register-demo.log` | Must show `False` |
| Both playbooks persist | `ls /root/rhcsa_journal/lab-00b/playbooks/` | `smoketest.yml` + `register-demo.yml` both present |
| Config still loaded | `ansible --version \| grep "config file"` | Still `/root/.ansible.cfg` (no T00-C drift) |

> **Reboot reasoning:** Nothing in this task changes anything — the second run of `smoketest.yml` is a no-op by design. After a reboot, both playbooks still live at `/root/rhcsa_journal/lab-00b/playbooks/`, the smoketest directory still exists at `/root/rhcsa_journal/_ansible_smoketest`, and re-running either playbook would still report `changed=0`. That is the deepest form of idempotence — survives reboot.

### Journal write — BEFORE cleanup

```bash
LAB=lab-00b
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
RERUN_CHANGED:       $(grep -oP 'changed=\K\d+' /root/rhcsa_journal/lab-00b/task2/rerun.log | tail -n 1)
REGISTER_DEMO_CHANGED: $(grep -oP 'changed=\K\d+' /root/rhcsa_journal/lab-00b/task2/register-demo.log | tail -n 1)
SMOKETEST_MODE:      $(stat -c '%a' /root/rhcsa_journal/_ansible_smoketest)
PLAYBOOKS:           /root/rhcsa_journal/lab-00b/playbooks/smoketest.yml,register-demo.yml
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Idempotence proof (changed=0 on re-run) + explicit register:/debug: pattern
COMMANDS: ansible-playbook (rerun), grep PLAY RECAP, ansible.builtin.stat, debug: msg:
TRAPS:    T00-A reinforced (FQCN throughout)
          T00-B reinforced (collections still listed — no drift)
          T00-C reinforced (config file still /root/.ansible.cfg before AND after re-run)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-00c — three-tool audit + simulated-reboot persistence proof
EOF

ls -la "$JDIR"
cat "$JDIR/done.txt"
echo "exit was: $?"
```

### 🧹 Cleanup

Nothing to clean. Both playbooks and the smoketest directory live on. Lab 00c verifies them in place.

### Troubleshoot

| Symptom | Fix |
|---|---|
| Re-run shows `changed=1` | Module is wrong — likely `command:` or `shell:` instead of `ansible.builtin.file`. Rewrite the task. |
| `changed=1` from the first task BUT `changed=0` from re-assert in register-demo | Something altered the smoketest directory between Task 1 and Task 2 (chmod, chown, or removal). Re-run Task 1. |
| `mtime` updated on the re-run | Same as above — the play actually did work, which means the desired state had drifted. |
| `debug: msg:` shows `undefined` | The `register:` variable name does not match between tasks — check spelling |
| YAML parse error after editing the playbook | Tabs slipped in — use spaces only |
| `config file = None` reappeared | Different shell or different user — confirm `whoami` returns `root` and `$HOME` is `/root` |

> **STOP — paste the PLAY RECAP lines from both `rerun.log` and `register-demo.log` (both must show `changed=0`) plus `cat $JDIR/notes.txt` before completing Lab 00b.**

---

## Lab 00b Checklist (2 tasks)

- [ ] Task 1 — Install `ansible.posix` + `community.general`, write `~/.ansible.cfg` + `~/inventory`, prove with `ping`, write + `--check --diff` + apply the first playbook
- [ ] Task 2 — Re-run the first playbook for `changed=0` idempotence proof, write + apply the `register:`/`debug:` demo playbook

---

## 🔗 Related Labs in the Trilogy

| Lab | Connection |
|---|---|
| **Lab 00a** — Ansible Control Node — RHCSA Prerequisites | The RHCSA half — `ansible-core` installed, journal tree built. Prerequisite. |
| **Lab 00c** — Ansible Control Node — Verification Capstone & Persistence Proof | The auditor seat — three-tool audit (`rpm -qi`, `ansible-galaxy collection list`, `ansible -m ping`, `ansible --version \| grep "config file"`) + simulated-reboot persistence proof |
| Lab 01a — `stdout`, `>`, `>>` (Output Redirection RHCSA) | The next foundational lab. The redirection patterns (`2>&1 \| tee`) you used here are the subject of Lab 01a. |
| Lab 11b — Removing Files via Ansible | The first lab that uses `ansible.builtin.file: state=absent` for real work — the FQCN + idempotence habits learned here carry through |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
