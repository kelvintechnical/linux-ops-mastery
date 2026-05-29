# Lab 00a: Ansible Control Node Setup (RHCSA)

- **Series:** linux-ops-mastery
- **Trilogy:** `00a` (RHCSA hand-typed) -> `00b` (Ansible FQCN playbook) -> `00c` (verify capstone)
- **Tasks:** **2 exactly**
- **Practice directory (rotation):** `/root`
- **Traps rehearsed:** `T00-A` (wrong inventory format), `T00-B` (missing collections), `T00-C` (ping without `connection=local`)

This lab builds the control-node baseline used by every later `b`-lab.

---

## Lab-Wide Setup

This lab's practice directory is: `/root`

```bash
sudo -i
mkdir -p /tmp/lab00a
cat > /tmp/lab00a/THIS_DIRECTORY.txt <<'EOF'
/root is root's home directory on the root filesystem. It stores persistent
administrator files and survives reboot. This matters for RHCSA because answer
files, custom inventory, and journal artifacts are commonly stored here.
EOF

cat /tmp/lab00a/THIS_DIRECTORY.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1

Practice directory this task: `/root`

### 🔁 Warm-Up

```bash
cd /root
pwd
ls -la /root | head -n 5
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Install `ansible-core`, install required collections, write `~/.ansible.cfg` and `~/inventory`, and verify localhost connectivity with `ansible -m ping localhost`.

### 🧵 Weave Trace

- `cd /root` and `pwd` keep all config artifacts in the intended persistent path.
- `ls -la` is reused to verify the files were actually created.
- `$(whoami)` and `$(date -Is)` stamp evidence lines.

### Command block

```bash
dnf install -y ansible-core
ansible-galaxy collection install ansible.posix community.general

cat > /root/.ansible.cfg <<'EOF'
[defaults]
inventory = /root/inventory
host_key_checking = False
collections_path = /root/.ansible/collections:/usr/share/ansible/collections

[privilege_escalation]
become = True
become_method = sudo
become_user = root
become_ask_pass = False
EOF

cat > /root/inventory <<'EOF'
[control]
localhost ansible_connection=local
EOF

ansible --version | head -n 3
ansible-galaxy collection list | grep -E 'ansible.posix|community.general'
ansible -i /root/inventory -m ping localhost
echo "exit was: $?"
```

### Human-Readable Breakdown

- `dnf install -y ansible-core` installs the Ansible engine.
- `ansible-galaxy collection install ...` pulls required external modules.
- `~/.ansible.cfg` sets defaults so later playbooks resolve inventory and collections cleanly.
- `inventory` defines localhost in INI format and forces local connection.
- `ansible -m ping localhost` confirms Ansible execution path works.

### Reading it left to right

`ansible -i /root/inventory -m ping localhost`

- `ansible`: ad-hoc Ansible command
- `-i /root/inventory`: explicit inventory file
- `-m ping`: run `ansible.builtin.ping` module
- `localhost`: host pattern target

### The story

Later `b`-labs should focus on module behavior, not setup failures. This task eliminates control-node drift up front.

### Expected output

```text
localhost | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

### Switches table

| Token | Meaning |
|---|---|
| `-y` | auto-confirm DNF install prompts |
| `-i` | choose inventory file |
| `-m` | select ad-hoc module |
| `head -n` | show top lines of command output |

### 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | `ansible-core` | installs the core engine and built-ins |
| ✅ | collections | add non-built-in modules (`ansible.posix`, `community.general`) |
| ✅ | `ansible_connection=local` | avoids SSH for localhost runs |
| ✅ | T00-A | inventory format must be valid INI/YAML |
| ✅ | T00-B | missing collections break many future playbooks |
| ✅ | T00-C | ping can fail if localhost is not local-connected |

### 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| Ansible installed | `ansible --version` | confirms engine path + config parse |
| Collections installed | `ansible-galaxy collection list \| grep -E 'ansible.posix\|community.general'` | confirms module availability |
| Localhost inventory works | `ansible -i /root/inventory -m ping localhost` | proves control node is usable |

### 🧹 Cleanup

```bash
rm -rf /tmp/lab00a
echo "exit was: $?"
```

### Troubleshoot table

| Symptom | Fix |
|---|---|
| `Unable to parse /root/inventory` | rewrite inventory exactly in INI format |
| `ERROR! couldn't resolve module/action` | install missing collection with `ansible-galaxy collection install ...` |
| `UNREACHABLE` on localhost | ensure `localhost ansible_connection=local` is present |

---

## Task 2

Practice directory this task: `/root`

### 🔁 Warm-Up

```bash
cd /root
ls -ld /root /root/.ansible.cfg /root/inventory
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Create the persistent journal root at `/root/rhcsa_journal/` and verify the tree using `find`.

### 🧵 Weave Trace

- `cd /root` keeps journal creation in the persistent root context.
- `ls -ld` checks target path ownership/mode.
- `find` provides machine-checkable structure evidence.

### Command block

```bash
mkdir -p /root/rhcsa_journal/{lab00,playbooks,evidence}
touch /root/rhcsa_journal/lab00/.keep

find /root/rhcsa_journal -maxdepth 2 -print | sort
ls -la /root/rhcsa_journal /root/rhcsa_journal/lab00
echo "Journal initialized at $(date -Is) by $(whoami)" >> /root/rhcsa_journal/evidence/lab00a.log
echo "exit was: $?"
```

### Human-Readable Breakdown

- `mkdir -p` builds base journal directories idempotently.
- `touch .keep` ensures `lab00` is non-empty.
- `find ... | sort` produces stable verification output.
- evidence log is appended for later resume checkpoints.

### Reading it left to right

`find /root/rhcsa_journal -maxdepth 2 -print | sort`

- `find /root/rhcsa_journal`: traverse journal tree
- `-maxdepth 2`: keep output concise and deterministic
- `-print`: emit each path
- `| sort`: stable ordering for comparison

### The story

Every trilogy writes persistent artifacts. A clean journal tree means you can resume work after interruption or reboot without guessing state.

### Expected output

```text
/root/rhcsa_journal
/root/rhcsa_journal/evidence
/root/rhcsa_journal/lab00
/root/rhcsa_journal/lab00/.keep
/root/rhcsa_journal/playbooks
```

### Switches table

| Token | Meaning |
|---|---|
| `-p` | create parent dirs as needed |
| `-maxdepth 2` | limit find recursion |
| `-print` | explicitly print paths |

### 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | `mkdir -p` | safe repeatable tree creation |
| ✅ | `find` verification | proves structure, not assumptions |
| ✅ | journal root under `/root` | persistence across reboot |

### 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| Journal directories | `find /root/rhcsa_journal -maxdepth 2 -type d` | proves durable lab artifact root |
| Evidence log append | `tail -n 1 /root/rhcsa_journal/evidence/lab00a.log` | confirms write path works |

### 🧹 Cleanup

```bash
# Keep /root/rhcsa_journal on purpose (prerequisite for all b-labs)
echo "No teardown: journal must persist."
echo "exit was: $?"
```

### Troubleshoot table

| Symptom | Fix |
|---|---|
| `Permission denied` under `/root` | run as root (`sudo -i`) |
| `find` missing expected path | rerun `mkdir -p` with exact path |

---

Lab `00a` complete. Continue to `lab-00b-ansible-control-node-setup-ansible`.
# Lab 00a: Ansible Control Node Setup (RHCSA) — `dnf install ansible-core` + collections

- **Series:** linux-ops-mastery — Foundations
- **Trilogy:** `00a` (RHCSA hand-typed install) → [`00b`](../lab-00b-ansible-control-node-setup-ansible/) (Ansible — first idempotent playbook) → [`00c`](../lab-00c-ansible-control-node-setup-verify/) (Verify capstone — audit + persistence)
- **Career arcs covered:** RHCSA EX200 (package install + service start patterns), RHCE EX294 (this is the prerequisite — every Task 4 in every lab depends on Lab 00 being green), DevOps (controller bring-up), SRE (reproducible automation host)
- **Prerequisite:** A running RHEL 9/10 (or Rocky 9/10) host with sudo access and internet OR a configured local repo
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = `dnf install ansible-core` + verify · Task 2 = `ansible-galaxy collection install` + first localhost ping with `${USER}` weave)
- **Practice Directory (rotation #06):** `/etc`
- **Sandbox (Tier B per Section 1.5):** `/tmp/lab00a` with `USER=labuser_00_setup`, `GROUP=labgrp_00_setup`, `USER_HOME=/tmp/lab00a/home_labuser_00_setup`. Built in Lab-Wide Setup; torn down + audited in **Lab Closeout** after Task 2.
- **Traps rehearsed this lab:** **T00-A** (installing `ansible` instead of `ansible-core` — pulls EPEL on RHEL, ungraded fork) · **T00-B** (forgetting collections — `ansible.posix`, `community.general` not in core; FQCN tasks fail) · **T00-C** (missing `~/.ansible.cfg` — every command needs `-i`/`--connection` flags) · **T39** (repo missing `enabled=1`/`gpgcheck=1` — install fails silently) · **T44** (cleanup-left-orphan-user — Lab Closeout audit must finish clean)

> **This lab's practice directory is: `/etc`** — `/etc` holds every system-wide config: `dnf` reads `/etc/yum.repos.d/`, Ansible reads `/etc/ansible/ansible.cfg` (and `~/.ansible.cfg`), every service we'll automate keeps its config here. RHCSA loves `/etc`.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T00-A T00-B T00-C T39"
echo "📁  PRACTICE DIR: /etc"
echo ""
echo "💡 /etc context (config files we'll touch):"
ls -ld /etc /etc/yum.repos.d
ls /etc/yum.repos.d 2>/dev/null | head -n 5
echo "Shell version: $BASH_VERSION"
```

> **STOP — paste header output before running setup. If `getenforce` returns `Disabled`, Lab 00 still works but Ansible's `selinux` module won't.**

---

## Objective

Install and verify the Ansible control plane that every later lab's Task 4 depends on:

1. Install `ansible-core` from RHEL/Rocky's AppStream — **not** the EPEL `ansible` fork.
2. Install the two collections every RHCSA-adjacent lab needs: `ansible.posix` (selinux, mount, acl, etc.) and `community.general` (lvol, sefcontext, archive, etc.).
3. Write `~/.ansible.cfg` and `~/inventory` so future commands work without `-i 'localhost,'`.
4. Prove the controller works with `ansible -m ping localhost` AS `${USER}` (Tier B weave).

By the end you can run `ansible-playbook /path/playbook.yml` from any directory and it just works.

---

## Concept: ansible-core vs ansible — Why It Matters

```
ansible-core   ← shipped in RHEL AppStream / Rocky AppStream
               ← Red Hat–graded; matches RHCE EX294 environment
               ← contains only ansible.builtin modules
               ← collections (ansible.posix, community.general) installed separately

ansible        ← legacy "everything-bundled" package on EPEL/PyPI
               ← NOT in RHEL AppStream; needs EPEL on RHEL
               ← bundles ~150 collections — most you'll never use
               ← ungraded on RHCE; install path graders don't expect
```

**Always `dnf install ansible-core`** on RHEL/Rocky. Add the specific collections you need with `ansible-galaxy collection install <fqcn>`.

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=00
export LAB_SLUG=setup
export SANDBOX=/tmp/lab00a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-00a/task1
mkdir -p /root/rhcsa_journal/lab-00a/task2

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
Practice directory: /etc
/etc holds every system-wide config file. dnf reads /etc/yum.repos.d/.
Ansible reads /etc/ansible/ansible.cfg (and ~/.ansible.cfg, which we
will create today). Every service we automate from here on keeps its
config in /etc. Backing up /etc is backing up the system's identity.
EOF

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd \
    -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id     "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /etc /etc/yum.repos.d
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste setup output before Task 1.**

---

## Task 1 — Install `ansible-core` and verify version

**Practice directory this task:** `/etc/yum.repos.d` (read), `/usr/bin/ansible*` (write via dnf), `${SANDBOX}` (Tier B writes).

### 🔁 Warm-Up

```bash
dnf repolist enabled                                    2>&1 | tee /tmp/lab00a/warmup.txt
rpm -q ansible-core 2>/dev/null || echo "ansible-core: not installed"
rpm -q ansible      2>/dev/null || echo "ansible (legacy): not installed"
which ansible 2>/dev/null || echo "no ansible in PATH yet"
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Install `ansible-core` from AppStream, confirm the binary lands at `/usr/bin/ansible`, and capture version evidence.

### 🧵 WEAVE TRACE

| Warm-up command | Role inside Task 1 |
|---|---|
| `dnf repolist enabled` | Confirms AppStream is configured before install |
| `rpm -q ansible-core` | Pre-state — we want this to flip from "not installed" to a version |
| `rpm -q ansible` (legacy) | T00-A trap detector — must remain "not installed" |
| `which ansible` | Final confirmation the binary is on PATH |

### Main command block

```bash
TASKLOG=/tmp/lab00a/task1.txt

echo "═══ Part A: install ansible-core ═══"               2>&1 | tee $TASKLOG
dnf install -y ansible-core                              2>&1 | tee -a $TASKLOG

echo "═══ Part B: verify package + binary ═══"            | tee -a $TASKLOG
rpm -q ansible-core                                      | tee -a $TASKLOG
rpm -qi ansible-core | head -n 8                         | tee -a $TASKLOG
which ansible ansible-playbook ansible-galaxy            | tee -a $TASKLOG
ansible --version | head -n 5                            | tee -a $TASKLOG

echo "═══ Part C: trap T00-A check (no legacy 'ansible') ═══" | tee -a $TASKLOG
if rpm -q ansible >/dev/null 2>&1; then
    echo "❌ legacy 'ansible' package present — uninstall it"  | tee -a $TASKLOG
    rpm -q ansible                                       | tee -a $TASKLOG
else
    echo "✅ legacy 'ansible' package not installed — T00-A clean" | tee -a $TASKLOG
fi
```

### Human-readable breakdown

1. `dnf install -y ansible-core` pulls the Red Hat–graded package from AppStream. `-y` accepts prompts non-interactively.
2. `rpm -q` confirms the install; `rpm -qi | head` shows the package metadata (signed by Red Hat).
3. `which` confirms the three binaries are on PATH.
4. T00-A check — `rpm -q ansible` (without `-core`) must NOT return a version. If it does, EPEL crept in.

### Expected output

```text
═══ Part A: install ansible-core ═══
...
Installed:
  ansible-core-2.16.x.el9.noarch  ...
═══ Part B: verify package + binary ═══
ansible-core-2.16.x-1.el9.noarch
Name        : ansible-core
Version     : 2.16.x
...
/usr/bin/ansible
/usr/bin/ansible-playbook
/usr/bin/ansible-galaxy
ansible [core 2.16.x]
  config file = None
  ...
═══ Part C: trap T00-A check (no legacy 'ansible') ═══
✅ legacy 'ansible' package not installed — T00-A clean
```

### Switches

| Token | Meaning |
|---|---|
| `dnf install -y PKG` | Install package non-interactively |
| `rpm -q PKG` | Query: is package installed? |
| `rpm -qi PKG` | Query: full package info (vendor, license, signature) |
| `which BIN` | Print the first BIN found on PATH |
| `ansible --version` | Core version + config file path + collections paths |

### 🧠 Concept Card

| Concept | What it does |
|---|---|
| `ansible-core` package | Red Hat–graded base — only `ansible.builtin` modules |
| AppStream repo | RHEL/Rocky default — no EPEL needed for `ansible-core` |
| `ansible --version` `config file = None` | Expected pre-Task-2 — we'll create `~/.ansible.cfg` next |
| **🪤 Trap Risk T00-A** | Installing legacy `ansible` from EPEL. **Fix:** always `ansible-core`. |
| **🪤 Trap Risk T39** | Repo missing `enabled=1`/`gpgcheck=1`. **Fix:** `dnf repolist enabled` shows AppStream BEFORE install. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| ansible-core installed | `rpm -q ansible-core` returns version | Survives reboot — RPM database |
| binary on PATH | `which ansible` returns `/usr/bin/ansible` | Future labs can run `ansible` without absolute path |
| no legacy ansible | `rpm -q ansible \| grep "not installed"` | T00-A clean |

### Journal write

```bash
LAB=lab-00a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab00a/task1.txt "$JDIR/evidence.txt"
ansible --version > "$JDIR/ansible-version.txt"
rpm -qi ansible-core > "$JDIR/rpm-qi.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
LAB_USER: ${USER}
LAB_GROUP: ${GROUP}
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    dnf install ansible-core; verify version + binary; T00-A trap check
COMMANDS: dnf install -y, rpm -q, rpm -qi, which, ansible --version
TRAPS:    T00-A rehearsed; T39 noted
NEXT:     task2 — collections + ~/.ansible.cfg + first ping AS USER
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup (per-task — leaves Tier B sandbox AND ansible-core intact)

```bash
rm -f /tmp/lab00a/warmup.txt /tmp/lab00a/task1.txt
getent passwd "${USER}"  >/dev/null && echo "✅ ${USER} still present"
getent group  "${GROUP}" >/dev/null && echo "✅ ${GROUP} still present"
rpm -q ansible-core      && echo "✅ ansible-core still installed"
ls /tmp/lab00a
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `No match for argument: ansible-core` | AppStream not enabled — `subscription-manager repos --enable rhel-9-for-x86_64-appstream-rpms` (RHEL) or `dnf repolist` (Rocky) |
| `ansible --version` shows `epel` in path | T00-A — `dnf remove ansible` then reinstall `ansible-core` |
| `Permission denied (sudo)` | You forgot `sudo -i` at Lab-Wide Setup |
| Repo `Status disabled` | T39 — `dnf config-manager --set-enabled <repo>` |

> **STOP — paste the `rpm -q ansible-core` line and the T00-A `✅` line before Task 2.**

---

## Task 2 — Install collections, write `~/.ansible.cfg` and `~/inventory`, ping AS `${USER}`

**Practice directory this task:** `/root` (root's `~/.ansible.cfg`) and `${USER_HOME}` (lab user's `~/.ansible.cfg`).

### 🔁 Warm-Up

```bash
ansible --version | grep -E 'config|collection'         2>&1 | tee /tmp/lab00a/warmup2.txt
ansible-galaxy collection list 2>/dev/null | head -n 10
test -f ~/.ansible.cfg && echo "exists" || echo "no root .ansible.cfg yet"
sudo -u "${USER}" bash -c 'test -f ~/.ansible.cfg && echo exists || echo no'
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

1. Install `ansible.posix` and `community.general` collections (system-wide).
2. Write a minimal `~/.ansible.cfg` and `~/inventory` for both root AND `${USER}`.
3. Run `ansible -m ping localhost` as both root and `${USER}`. Both must return `pong`.

### 🧵 WEAVE TRACE

| Warm-up command | Role inside Task 2 |
|---|---|
| `ansible --version \| grep config` | Pre-state: `config file = None` flips to a path after we write `.ansible.cfg` |
| `ansible-galaxy collection list` | Pre-state: empty; flips to `ansible.posix` + `community.general` |
| `sudo -u ${USER} ...` | Tier B pattern reused for the final ping |

### Main command block

```bash
TASKLOG=/tmp/lab00a/task2.txt

echo "═══ Part A: install collections (system-wide) ═══"  2>&1 | tee $TASKLOG
ansible-galaxy collection install ansible.posix community.general \
    --collections-path /usr/share/ansible/collections    2>&1 | tee -a $TASKLOG

echo "═══ Part B: list installed collections ═══"         | tee -a $TASKLOG
ansible-galaxy collection list                           | tee -a $TASKLOG

echo "═══ Part C: write root's ~/.ansible.cfg + inventory ═══" | tee -a $TASKLOG
cat > /root/.ansible.cfg <<'EOF'
[defaults]
inventory       = /root/inventory
host_key_checking = False
retry_files_enabled = False
collections_paths = /usr/share/ansible/collections
stdout_callback = yaml
EOF

cat > /root/inventory <<'EOF'
localhost ansible_connection=local
EOF

ls -l /root/.ansible.cfg /root/inventory                | tee -a $TASKLOG

echo "═══ Part D: write ${USER}'s ~/.ansible.cfg + inventory ═══" | tee -a $TASKLOG
mkdir -p "${USER_HOME}"
cat > "${USER_HOME}/.ansible.cfg" <<'EOF'
[defaults]
inventory       = ~/inventory
host_key_checking = False
retry_files_enabled = False
stdout_callback = yaml
EOF

cat > "${USER_HOME}/inventory" <<'EOF'
localhost ansible_connection=local
EOF

chown -R "${USER}:${GROUP}" "${USER_HOME}"
ls -l "${USER_HOME}/.ansible.cfg" "${USER_HOME}/inventory" | tee -a $TASKLOG

echo "═══ Part E: ping localhost as root ═══"             | tee -a $TASKLOG
ansible -m ping localhost                                | tee -a $TASKLOG

echo "═══ Part F: ping localhost AS ${USER} (Tier B) ═══" | tee -a $TASKLOG
sudo -u "${USER}" -H bash -c 'cd ~ && ansible -m ping localhost' \
                                                         | tee -a $TASKLOG

grep -q 'pong' /tmp/lab00a/task2.txt \
    && echo "✅ ping returned pong (control node alive)" \
    || echo "❌ ping did not return pong" \
    | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. **Part A** — `ansible-galaxy collection install` with `--collections-path /usr/share/ansible/collections` makes the collections visible to every user on the host.
2. **Part B** — `collection list` confirms both collections appear under the system path.
3. **Part C/D** — `~/.ansible.cfg` tells Ansible where the inventory is, disables host-key checking for localhost, and uses YAML output. Both root and `${USER}` get their own.
4. **Part E** — `ansible -m ping localhost` runs the `ping` module against `localhost` (defined in `~/inventory`). Returns `pong` on success.
5. **Part F** — same ping, but as `${USER}`. The `-H` flag makes `sudo` set `HOME=${USER_HOME}` so Ansible reads `${USER}`'s `.ansible.cfg`. This is the Tier B weave.

### Expected output

```text
═══ Part A: install collections (system-wide) ═══
Starting galaxy collection install process
Process install dependency map
...
Installing 'ansible.posix:1.5.4' to '/usr/share/ansible/collections/...'
Installing 'community.general:8.x' to '/usr/share/ansible/collections/...'
═══ Part B: list installed collections ═══
Collection         Version
------------------ -------
ansible.posix      1.5.4
community.general  8.x
...
═══ Part C: write root's ~/.ansible.cfg + inventory ═══
-rw-r--r--. 1 root root  ... /root/.ansible.cfg
-rw-r--r--. 1 root root  ... /root/inventory
═══ Part D: write labuser_00_setup's ~/.ansible.cfg + inventory ═══
-rw-r--r--. 1 labuser_00_setup labgrp_00_setup ... /tmp/lab00a/home_labuser_00_setup/.ansible.cfg
═══ Part E: ping localhost as root ═══
localhost | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
═══ Part F: ping localhost AS labuser_00_setup (Tier B) ═══
localhost | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
✅ ping returned pong (control node alive)
```

### Switches

| Token | Meaning |
|---|---|
| `ansible-galaxy collection install NAME` | Install a collection by FQCN-prefix |
| `--collections-path PATH` | Where to install (system-wide vs `~/.ansible/collections`) |
| `~/.ansible.cfg` | Per-user Ansible config (read before `/etc/ansible/ansible.cfg`) |
| `inventory` line `host ansible_connection=local` | Ansible runs as a subprocess, no SSH |
| `ansible -m ping HOST` | One-shot module invocation (no playbook) |
| `sudo -u USER -H bash -c '...'` | Run as USER with USER's `$HOME` |

### 🧠 Concept Card

| Concept | What it does |
|---|---|
| `ansible-core` + collections model | Core ships modules in `ansible.builtin`; everything else lives in collections |
| `ansible.posix` collection | `selinux`, `mount`, `acl`, `sysctl`, `synchronize` modules |
| `community.general` collection | `lvol`, `archive`, `sefcontext`, `timezone`, etc. |
| `~/.ansible.cfg` | Per-user controller config — survives reboot |
| `inventory` file | Lists hosts; `localhost ansible_connection=local` for self-managed |
| `ping` module | Returns `pong` if the controller can run modules on the target |
| **🪤 Trap Risk T00-B** | Forgetting collections — FQCN tasks fail with `couldn't resolve module`. **Fix:** install both collections in Part A. |
| **🪤 Trap Risk T00-C** | No `~/.ansible.cfg` — every command needs `-i 'localhost,'` and `--connection=local`. **Fix:** write the cfg+inventory once, never type those flags again. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Collections installed | `ansible-galaxy collection list \| grep -E 'posix\|general'` | Survives reboot — files in `/usr/share/ansible/collections` |
| Root config | `ansible --version \| grep "config file"` shows `/root/.ansible.cfg` | Future Task 4 in every lab uses this |
| User config | `sudo -u ${USER} -H ansible --version \| grep config` shows USER's path | Tier B ping works |
| Both pings work | `grep -c pong /tmp/lab00a/task2.txt` returns 2 | Both identities can run modules |

### Journal write

```bash
LAB=lab-00a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab00a/task2.txt "$JDIR/evidence.txt"
cp /root/.ansible.cfg    "$JDIR/root.ansible.cfg"
cp /root/inventory       "$JDIR/root.inventory"
cp "${USER_HOME}/.ansible.cfg" "$JDIR/user.ansible.cfg"
cp "${USER_HOME}/inventory"    "$JDIR/user.inventory"
ansible-galaxy collection list > "$JDIR/collections.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
LAB_USER: ${USER}
LAB_GROUP: ${GROUP}
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    collections install; ~/.ansible.cfg + inventory for root + USER; ping pong twice
COMMANDS: ansible-galaxy collection install, ansible -m ping, sudo -u ${USER} -H
TRAPS:    T00-B rehearsed (collections); T00-C rehearsed (config)
TIER B:   USER has own .ansible.cfg + inventory; ping returned pong as USER
NEXT:     lab-00b — first idempotent playbook; lab-00c — verify capstone
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup (per-task — leaves Ansible install + configs intact for 00b/00c)

```bash
rm -f /tmp/lab00a/warmup2.txt /tmp/lab00a/task2.txt
# Keep /root/.ansible.cfg, /root/inventory, ${USER_HOME}/.ansible.cfg — needed by 00b/00c
ls /tmp/lab00a
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `couldn't resolve module/action 'ansible.posix.X'` | T00-B — collection not installed; rerun Part A |
| `ERROR! the role 'X' was not found` | Inventory or cfg missing — rerun Part C/D |
| `localhost \| UNREACHABLE` | `~/.ansible.cfg` not pointing at the inventory; check Part C ls output |
| Ping works as root, fails as `${USER}` | `sudo -u ${USER}` without `-H` — `$HOME` not set, USER's cfg not read |

> **STOP — paste both `pong` lines (root + ${USER}) before Lab Closeout.**

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# 1) Mount layer (no-op for Lab 00)
awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts \
    | tac | xargs -r -n1 umount -l 2>/dev/null

# 2) User / group teardown
if getent passwd "${USER}" >/dev/null 2>&1; then
    userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
    groupdel "${GROUP}"  2>/dev/null
fi

# 3) Sandbox dir
rm -rf "${SANDBOX}"

# 4) Audit
echo "── Lab 00a cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
rpm -q ansible-core >/dev/null      && echo "✅ ansible-core preserved" || echo "❌ ansible-core gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste four `✅` audit lines. ansible-core stays installed (it is the prerequisite for every other lab).**

---

## Lab 00a Checklist (2 tasks + closeout)

- [ ] Lab-Wide Setup — Tier B sandbox built; `/etc` context file created
- [ ] Task 1 — `ansible-core` installed; T00-A clean (no legacy `ansible`)
- [ ] Task 2 — collections installed; root + `${USER}` `.ansible.cfg` written; both pings return `pong`
- [ ] Lab Closeout — four `✅` audit lines; `ansible-core` preserved

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 00b** — First Idempotent Playbook | Uses the controller built here |
| **Lab 00c** — Verify Capstone | Audits this lab's artifacts |
| **Every Lab N b/Task 4** | Depends on Lab 00 being green |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
