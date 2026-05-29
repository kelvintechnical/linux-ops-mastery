# Lab 00a: Ansible Control Node — RHCSA Prerequisites (`dnf`, journal tree, package verification)

- **Series:** linux-ops-mastery — Prerequisite Trilogy (run BEFORE Lab 01)
- **Trilogy:** **`00a` (RHCSA — you are here)** → `00b` (Ansible) → `00c` (Verify)
- **Career arcs covered:** RHCSA EX200 (`dnf install`, `rpm -qi`, `which`, `stat`, journal discipline), RHCE EX294 (the difference between `ansible-core` and the fat `ansible` package), SRE / DevOps (package provenance + persistent change-log on /root)
- **Prerequisite:** A running RHEL/Rocky/AlmaLinux 9 box where you can `sudo dnf install`
- **Time Estimate:** 20–25 minutes
- **Tasks:** 2 (Task 1 = install + verify package, Task 2 = build the persistent journal tree)
- **Practice Directory (rotation #00):** `/root/rhcsa_journal`
- **Sandbox:** `/root/rhcsa_journal/lab00`
- **Traps rehearsed this lab:** **T00-A** (Installing the wrong package — `ansible` (fat, EPEL) vs `ansible-core` (slim, AppStream — the RHCE-shaped choice))

> **This lab's practice directory is: `/root/rhcsa_journal`** — every task references it in at least two commands. Unlike most labs in this series, the practice directory is intentionally on the persistent root partition, not `/tmp` — because the whole point of Lab 00a is to lay down a journal tree that survives reboot.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T00-A"
echo "📁  PRACTICE DIR: /root/rhcsa_journal/lab-00a"
echo ""
echo "🔍 Pre-install package state (must be empty — we install ansible-core in Task 1):"
rpm -q ansible-core 2>/dev/null || echo "  ansible-core not yet installed (expected)"
rpm -q ansible 2>/dev/null && echo "  ⚠️ fat ansible package detected — this is the T00-A trap; remove it before Task 1"
which ansible 2>/dev/null || echo "  ansible binary not on PATH (expected pre-install)"
```

> **STOP — paste header output before starting Task 1.**

---

## 🎯 Objective

Lay down the RHCSA half of the Ansible control node. By the end of Lab 00a you will have:

1. `ansible-core` installed from the AppStream repo (not the fat `ansible` package from EPEL)
2. `rpm -qi ansible-core` proving the package came from the expected source with the expected version
3. `which ansible`, `which ansible-playbook`, `which ansible-galaxy` all returning `/usr/bin/...`
4. A persistent journal tree at `/root/rhcsa_journal/lab-00a/{task1,task2}/` ready to receive evidence from this lab and every lab after it
5. The install transcript saved into the journal so weeks from now you can answer "when did I install ansible-core, and which version?"

Lab 00b will install collections + write `~/.ansible.cfg`. Lab 00c will verify the whole stack. Lab 00a is the foundation those depend on — get the package right, get the journal right, and the rest of the trilogy walks itself.

---

## 🧠 Concept: `ansible-core` vs `ansible` — Why the Package Name Matters

`ansible-core` is the **engine** (modules under `ansible.builtin.*` + the runtime). `ansible` (the fat package, historically from EPEL or PyPI) bundles `ansible-core` plus ~80 community collections preinstalled. They are not the same package, and the difference is the entire reason the RHCE exam grades the way it does.

```
   ┌───────────────────────────────────────────────────────────────┐
   │   dnf install ansible-core    ← AppStream (RHEL/Rocky/Alma)    │
   │   ├── engine + ansible.builtin.* modules only                  │
   │   └── collections you need? You install them deliberately.     │
   │                                                                │
   │   dnf install ansible         ← EPEL / external repo           │
   │   ├── engine + ~80 community collections preloaded             │
   │   └── convenient at home, NOT the RHCE-shaped install.         │
   └───────────────────────────────────────────────────────────────┘
```

The RHCE exam expects you to **declare** the collections you need (`ansible.posix`, `community.general`) by running `ansible-galaxy collection install` on the control node — which is exactly what Lab 00b does. A grader who sees `dnf install ansible` on an exam VM raises an eyebrow; `dnf install ansible-core` is the right shape. That is **Trap T00-A**.

The journal tree at `/root/rhcsa_journal/` is the other half of this lab. `/tmp` is tmpfs on most RHEL 9 layouts — it evaporates on reboot, which is fine for sandboxes but useless for evidence. Every later lab writes its `done.txt`, `notes.txt`, and command transcripts into `/root/rhcsa_journal/lab-NN/taskN/`. Lab 00c proves that tree survives a simulated reboot.

---

## 📚 Install + Inspection Reference (everything for Tasks 1–2)

| Token | Meaning | Why an RHCSA candidate needs it |
|---|---|---|
| `dnf install -y PKG` | Install package, assume yes to prompts | Scripted installs and CI runs |
| `dnf reinstall -y PKG` | Reinstall to repair a damaged install | Recovery from "command not found" |
| `rpm -q PKG` | Is PKG installed? Print NEVRA or "not installed" | First diagnostic command |
| `rpm -qi PKG` | Show install metadata: version, repo, install date, signer | RHCSA "prove the package came from where it should" |
| `rpm -ql PKG` | List every file the package owns | Locate where a binary actually lives |
| `which CMD` | First match for CMD on `$PATH` | "Why isn't ansible running?" — wrong shell, hash cache |
| `hash -r` | Forget the shell's command cache | Required after install/move of a binary |
| `stat -c '%a %U:%G %n'` | Mode + owner + group + name | The auditor's one-line metadata snapshot |
| `mkdir -p PATH` | Create PATH and all missing parents, idempotent | Build the journal tree without `-p` typos |
| `tee FILE` | Tee stdout to FILE while still printing | Capture an install transcript without losing the screen |

> **Rule of Lab 00a:** Every command's output that proves something gets piped through `tee` into the journal. Nothing is "just run it and trust your memory."

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i

# We are about to make /root/rhcsa_journal — the persistent journal tree
# every subsequent lab writes into. This sets up the lab-00a directory
# specifically; lab-00b and lab-00c will create their own siblings later.
test -d /root || { echo "no /root — are you logged in as root?"; exit 1; }
mkdir -p /root/rhcsa_journal/lab-00a
cd /root/rhcsa_journal/lab-00a

# Verify we are on a supported OS (RHEL/Rocky/Alma 9 or compatible)
grep -E 'PLATFORM_ID|VERSION_ID' /etc/os-release
dnf repolist 2>&1 | grep -Ei 'appstream|baseos' | head -n 2
ls -ld /root/rhcsa_journal /root/rhcsa_journal/lab-00a
echo "exit was: $?"
```

> **STOP — paste the `grep PLATFORM_ID` line and the `appstream`/`baseos` repo list before starting Task 1.**

---

## Task 1 — Install `ansible-core` and prove the binary + package metadata

**Practice directory this task:** `/root/rhcsa_journal` · the persistent root-partition journal — every artifact in this task lands under `/root/rhcsa_journal/lab-00a/task1/` so it survives reboot.

### 🔁 Warm-Up — commands woven into Task 1

```bash
mkdir -p /root/rhcsa_journal/lab-00a/task1
cd /root/rhcsa_journal/lab-00a/task1
date -Is                                            2>&1 | tee start.txt
echo "user=$(whoami) host=$(hostname) os=$(grep PRETTY_NAME /etc/os-release)" \
                                                    2>&1 | tee -a start.txt
rpm -q ansible-core                                 2>&1 | tee -a start.txt
which ansible                                       2>&1 | tee -a start.txt
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> No prior lab to carry from — this **is** the prior lab. The warm-up captures the **pre-install** state into `start.txt` so the diff against the post-install state in `done.txt` is unambiguous evidence that we changed something.

### Purpose

Install `ansible-core` from AppStream (not the fat `ansible` package from EPEL), then prove the install with three independent checks: `rpm -q`, `rpm -qi`, and `which`. Capture the install transcript so weeks from now you can answer "what version did I install, when, and from which repo?"

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `rpm -q ansible-core` | The **pre-install snapshot** in `start.txt` (expected: "not installed") AND the **post-install proof** at the end of the task |
| `which ansible` | Same pattern — pre-install returns empty/missing, post-install returns `/usr/bin/ansible` |
| `date -Is` | Stamps both `start.txt` and `done.txt` so the journal records when the install actually happened |
| `2>&1 \| tee` | Captures both stderr and stdout so a failed install is **not** silently invisible |
| `set -o pipefail` | Catches the case where `dnf` failed but the `tee` chain swallowed the non-zero exit |
| `$(grep PRETTY_NAME ...)` | Records the OS so the install evidence is correlated with a specific RHEL/Rocky/Alma version |

### Main command block

```bash
cd /root/rhcsa_journal/lab-00a/task1

# 1. Install ansible-core (NOT ansible — that is T00-A). AppStream, no EPEL needed.
dnf install -y ansible-core                         2>&1 | tee install.log

# 2. Prove the install with three independent checks
rpm -q ansible-core                                 2>&1 | tee version.txt
rpm -qi ansible-core                                2>&1 | tee -a version.txt
which ansible ansible-playbook ansible-galaxy       2>&1 | tee paths.txt

# 3. Engine self-report (this is the line you grep for in every later Task 4)
ansible --version                                   2>&1 | tee ansible-version.txt

# 4. Sanity: every binary above must answer --help without error
ansible --help | head -n 2
ansible-playbook --help | head -n 2
ansible-galaxy --help | head -n 2
echo "exit was: $?"
```

### Human-readable breakdown

1. `dnf install -y ansible-core` — install the slim engine package from AppStream. The `-y` flag is mandatory in scripted installs and CI; nothing in this series ever runs interactively. The full transcript lands in `install.log`.
2. `rpm -q ansible-core` returns the **NEVRA** (name, epoch, version, release, arch) — e.g., `ansible-core-2.14.x-1.el9.noarch`. This is the auditor's "yes, it is installed" line.
3. `rpm -qi ansible-core` prints install metadata: version, release, build date, **install date**, vendor, and the repo it came from (`From repo: appstream`). The "From repo" line is the RHCE-grade proof you used AppStream, not EPEL.
4. `which ansible ansible-playbook ansible-galaxy` returns the resolved path for each binary. All three should be `/usr/bin/...` after an `ansible-core` install.
5. `ansible --version` is the **first diagnostic command** in every later Task 4 — it prints the engine version, the config file in use (currently `None`, Lab 00b fixes that), and the Python interpreter the engine is bound to.

### Reading it left to right

`dnf install -y ansible-core`

- `dnf` — RHEL 9 package manager
- `install` — subcommand verb
- `-y` — assume yes to confirmation prompts (required in scripts)
- `ansible-core` — package name. **Not** `ansible` — different package, different repo, different RHCE expectation.

`rpm -qi ansible-core`

- `rpm` — the low-level RPM database tool
- `-q` — query mode (does not install or modify)
- `-i` — info mode: print full metadata
- `ansible-core` — package name to query

`which ansible ansible-playbook ansible-galaxy`

- `which` — print first match for each argument on `$PATH`
- three binaries on one line — three lookups, three answers

### The story

Senior engineers install packages **and** verify them in the same shell session. The pattern `dnf install → rpm -q → rpm -qi → which → --version` takes 15 seconds and produces five independent lines of evidence that the install actually happened. The opposite pattern — `dnf install -y X` followed by "now let's move on" — is the one that produces "but I installed it on Monday, why doesn't `ansible` work?" tickets two weeks later when somebody else removed the package and nobody journaled the install date.

For the RHCSA exam specifically: when the prompt says "install X and verify," the grader is checking that the package is **installed from the right repo** and that the **binary is on PATH**. `rpm -qi` plus `which` is the canonical two-command proof.

### Expected output

```text
# Pre-install state (start.txt):
2026-05-28T19:50:01-04:00
user=root host=node01 os=PRETTY_NAME="Red Hat Enterprise Linux 9.4 (Plow)"
package ansible-core is not installed
(no output from which ansible)

# install.log (last few lines):
Installed:
  ansible-core-2.14.17-1.el9.noarch
Complete!

# version.txt:
ansible-core-2.14.17-1.el9.noarch
Name        : ansible-core
Version     : 2.14.17
Release     : 1.el9
...
From repo   : appstream
Summary     : SSH-based configuration management, deployment, and task execution system

# paths.txt:
/usr/bin/ansible
/usr/bin/ansible-playbook
/usr/bin/ansible-galaxy

# ansible-version.txt:
ansible [core 2.14.17]
  config file = None
  configured module search path = ['/root/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
  ansible python module location = /usr/lib/python3.9/site-packages/ansible
  executable location = /usr/bin/ansible
  python version = 3.9.x ...
```

Two facts to notice: `From repo : appstream` (T00-A satisfied — we did **not** install from EPEL) and `config file = None` (expected — Lab 00b writes `~/.ansible.cfg`).

### Switches

| Switch | Meaning | Why it matters |
|---|---|---|
| `dnf install -y` | Assume yes | Required for scripted installs |
| `dnf reinstall -y` | Reinstall over existing | Recovery from a corrupt install |
| `rpm -q` | Quiet query (NEVRA only) | The "is it installed?" one-liner |
| `rpm -qi` | Info query (metadata) | "From repo" line is RHCE-grade evidence |
| `rpm -ql` | List files | Where did the binaries actually land? |
| `which` | First match on PATH | "Why won't `ansible` run?" — shell hash cache |
| `hash -r` | Forget shell command cache | After install/move of a binary |
| `ansible --version` | Engine self-report | First diagnostic in every later Task 4 |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | `ansible-core` | Slim engine + `ansible.builtin.*` modules — RHCE-shaped install |
|   | `ansible` (fat) | Engine + ~80 community collections — convenient at home, not RHCE-shaped |
|   | `rpm -qi` "From repo" line | RHCE-grade proof of where the package came from |
|   | `which` vs `command -v` | Both find a binary; `command -v` is POSIX, `which` is more familiar |
|   | `config file = None` | You have not written `~/.ansible.cfg` yet — Lab 00b will |
|   | `tee FILE` | Capture transcript without losing the screen |
| 🪤 | **Trap Risk T00-A** | `dnf install ansible` (the fat EPEL package) instead of `dnf install ansible-core`. Refused on RHCE grading; the "From repo" line will say `epel`, not `appstream`. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Package installed | `rpm -q ansible-core` | Returns NEVRA — survives reboot because the RPM database is persistent |
| Binaries on PATH | `which ansible ansible-playbook ansible-galaxy` | All three resolve to `/usr/bin/...` after reboot |
| Install transcript | `wc -l /root/rhcsa_journal/lab-00a/task1/install.log` | The auditable record of when the package landed |
| Version evidence | `head -n 1 /root/rhcsa_journal/lab-00a/task1/version.txt` | The NEVRA recorded in the journal for cross-checking against future installs |

> **Reboot reasoning:** The RPM database lives at `/var/lib/rpm/` on the root partition — packages survive reboot trivially. The journal lives at `/root/rhcsa_journal/` on the same partition — also persistent. Nothing in this task is in `/tmp`, so nothing evaporates. That is **why** Lab 00 uses `/root/` as the practice directory while every other lab uses `/tmp`.

### Journal write — BEFORE cleanup

```bash
LAB=lab-00a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
PKG:    $(rpm -q ansible-core)
REPO:   $(rpm -qi ansible-core | awk -F': ' '/From repo/ {print $2}')
ANSIBLE_VERSION: $(ansible --version | head -n 1)
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Install ansible-core from AppStream; prove with rpm + which + --version
COMMANDS: dnf install -y ansible-core, rpm -q, rpm -qi, which, ansible --version
TRAPS:    T00-A rehearsed (we installed ansible-core NOT ansible; "From repo" says appstream)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — build the persistent journal tree and document the /root vs /tmp choice
EOF

ls -la "$JDIR"
cat "$JDIR/done.txt"
echo "exit was: $?"
```

### 🧹 Cleanup

Nothing to clean. The install is intentionally persistent and so are the journal artifacts — they will be referenced by every lab in this series and re-verified in Lab 00c.

### Troubleshoot

| Symptom | Fix |
|---|---|
| `Unable to find a match: ansible-core` | RHEL: `sudo subscription-manager repos --enable=rhel-9-appstream`. Rocky/Alma: `sudo dnf repolist` — AppStream should already be present; if not, install `rocky-release` / `almalinux-release`. |
| `ansible: command not found` immediately after install | The shell cached the old (missing) lookup. Run `hash -r` or open a new shell. |
| `rpm -qi` shows `From repo: epel` | T00-A triggered: you installed the fat `ansible` package. Run `dnf remove -y ansible && dnf install -y ansible-core`. |
| `ansible --version` shows a different Python than expected | Lab 00b will pin `ansible_python_interpreter=/usr/bin/python3` in the inventory; ignore for now. |

> **STOP — paste `cat $JDIR/done.txt` and the `which ansible ansible-playbook ansible-galaxy` output before starting Task 2.**

---

## Task 2 — Build the persistent journal tree at `/root/rhcsa_journal/`

**Practice directory this task:** `/root/rhcsa_journal` · the journal tree we are about to construct lives on the root partition — that is the entire point of this task. The contrast with `/tmp` (tmpfs, ephemeral) is the lesson.

### 🔁 Warm-Up — commands woven into Task 2

```bash
mkdir -p /root/rhcsa_journal/lab-00a/task2
cd /root/rhcsa_journal/lab-00a/task2
date -Is                                            2>&1 | tee start.txt
stat -c '%n mountpoint=%m fs-survives-reboot?' /tmp /root /root/rhcsa_journal \
                                                    2>&1 | tee -a start.txt
df -hT /tmp /root                                   2>&1 | tee -a start.txt
test -d /root/rhcsa_journal/lab-00a/task1 && echo "task1 journal exists — good"
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: `set -o pipefail` and the `2>&1 | tee` capture pattern persist into Task 2. The `start.txt` snapshot now includes the mount-point evidence of **why** `/root` survives reboot but `/tmp` does not.

### Purpose

Build the canonical `/root/rhcsa_journal/lab-00a/` tree, set ownership/mode explicitly, then prove with `stat -c` and `df -hT` that the tree is on the persistent root partition — not on `tmpfs`. This is the structural answer to "where do I put evidence I want to survive a reboot?" — every later lab depends on this directory being here and being persistent.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `stat -c '%m'` | The **structural** proof: `/root` shows mount `/`, `/tmp` shows mount `/tmp` (likely tmpfs). The mount point is **why** persistence works. |
| `df -hT /tmp /root` | Cross-check on the filesystem type: `tmpfs` for `/tmp`, `xfs`/`ext4` for `/root`. |
| `mkdir -p` | Idempotent directory creation — running this task twice does not error |
| `test -d` | Guards every later check — "the directory we are about to chmod must actually exist" |
| `2>&1 \| tee` | Captures the full evidence into `task2/evidence.txt` for the journal |
| `$(date -Is)` | Stamps `start.txt` and `done.txt` for the audit timeline |

### Main command block

```bash
cd /root/rhcsa_journal/lab-00a/task2

# 1. Build the canonical journal tree
mkdir -p /root/rhcsa_journal/lab-00a/{task1,task2}
mkdir -p /root/rhcsa_journal/_evidence

# 2. Set ownership/mode explicitly (RHCSA: never leave permissions implicit)
chown -R root:root /root/rhcsa_journal
chmod 0750 /root/rhcsa_journal
chmod 0750 /root/rhcsa_journal/lab-00a
chmod 0750 /root/rhcsa_journal/lab-00a/task1
chmod 0750 /root/rhcsa_journal/lab-00a/task2

# 3. Prove the mode + ownership + mount point (the auditor's three lines)
stat -c 'mode=%a owner=%U:%G mount=%m path=%n' \
  /root/rhcsa_journal \
  /root/rhcsa_journal/lab-00a \
  /root/rhcsa_journal/lab-00a/task1 \
  /root/rhcsa_journal/lab-00a/task2                2>&1 | tee /root/rhcsa_journal/lab-00a/task2/evidence.txt

# 4. Capture df + lsblk evidence — the structural why
echo "── df -hT for /tmp and /root ──" \
  | tee -a /root/rhcsa_journal/lab-00a/task2/evidence.txt
df -hT /tmp /root                                   2>&1 | tee -a /root/rhcsa_journal/lab-00a/task2/evidence.txt

echo "── findmnt for the journal mount ──" \
  | tee -a /root/rhcsa_journal/lab-00a/task2/evidence.txt
findmnt -T /root/rhcsa_journal                      2>&1 | tee -a /root/rhcsa_journal/lab-00a/task2/evidence.txt

# 5. Persistence reasoning — record it as text we can read again later
cat > /root/rhcsa_journal/lab-00a/task2/why-root-not-tmp.txt <<'EOF'
/tmp  is on tmpfs on most RHEL 9 layouts (or it is cleared by systemd-tmpfiles
      on boot — either way, contents do NOT survive reboot).

/root is on the root partition (xfs/ext4). Files written under /root persist
      across reboot — they are on durable storage, not RAM, and no init service
      clears them.

The journal at /root/rhcsa_journal/ is therefore the correct location for
ANY evidence we want to read again after a reboot. Sandboxes for the lab
exercises themselves can still live under /tmp (Labs 01+ do this), but the
done.txt + notes.txt + transcripts go under /root.

This is the structural reason Lab 00a's practice directory is /root and
every later lab's practice directory is /tmp.
EOF

cat /root/rhcsa_journal/lab-00a/task2/why-root-not-tmp.txt
echo "exit was: $?"
```

### Human-readable breakdown

1. `mkdir -p` builds the lab-00a tree (`task1/`, `task2/`) and a shared `_evidence/` directory next to it. `-p` is idempotent — running this task twice does not error and does not overwrite.
2. `chown -R root:root` + `chmod 0750` sets ownership and mode explicitly. The RHCSA habit is **never** leave permissions implicit on directories you will keep — the next person to read the journal needs to know they are looking at a controlled tree, not whatever the umask happened to be that day.
3. `stat -c 'mode=%a owner=%U:%G mount=%m path=%n'` is the auditor's one-line metadata snapshot. The `%m` is the structural proof of persistence — the mount point that contains the path.
4. `df -hT` shows the filesystem type for `/tmp` and `/root` — `tmpfs` vs `xfs`/`ext4`. This is the **why** behind the mount point difference.
5. The `why-root-not-tmp.txt` file is the prose version, written into the journal so a future reader (or future you) does not have to re-derive the reasoning.

### Reading it left to right

`mkdir -p /root/rhcsa_journal/lab-00a/{task1,task2}`

- `mkdir` — make directories
- `-p` — create parents as needed; do not error if path already exists
- `/root/rhcsa_journal/lab-00a/{task1,task2}` — brace expansion creates **two** paths: `.../task1` and `.../task2`

`chmod 0750 PATH`

- `chmod` — change mode
- `0750` — octal mode: `7` for owner (rwx), `5` for group (r-x), `0` for others (no access). The leading `0` is conventional and harmless.
- `PATH` — the directory to update

`stat -c 'mode=%a owner=%U:%G mount=%m path=%n' PATH`

- `stat` — file metadata tool
- `-c FMT` — custom format string
- `%a` — octal access mode (e.g., `750`)
- `%U` — owner name (e.g., `root`)
- `%G` — group name (e.g., `root`)
- `%m` — **mount point** containing the file (the persistence-critical field)
- `%n` — file name
- `PATH` — file or directory to stat

### The story

The first time you reboot the lab VM, the difference between `/root/rhcsa_journal/` and `/tmp/rm-lab/` will be brutal. The `/tmp` sandbox is gone — fine, that was the design. But if the journal had also been in `/tmp`, every `done.txt` from every prior task would be gone too. A grader (or a future you) opens the system, asks "what state is this in?", and the only honest answer is "I don't know, the journal evaporated."

`/root/rhcsa_journal/` is the structural answer to that. Lab 00c proves it by literally wiping `/tmp` and re-running the audit using **only** journal files from `/root/`. Lab 00a's job is to build the tree correctly **before** any other lab needs it.

The 0750 mode is the RHCSA habit. 0755 would be fine too — but 0750 says "only root and the root group can list this directory," which is the right posture for an evidence tree. Cattle-grade laxness (0777) is the RHCSA cardinal sin and graders mark it down.

### Expected output

```text
2026-05-28T19:55:14-04:00
/tmp mountpoint=/tmp fs-survives-reboot?
/root mountpoint=/ fs-survives-reboot?
/root/rhcsa_journal mountpoint=/ fs-survives-reboot?
Filesystem     Type   Size  Used Avail Use% Mounted on
tmpfs          tmpfs  3.8G  1.2M  3.8G   1% /tmp
/dev/mapper/rhel-root xfs   17G  4.1G   13G  25% /
task1 journal exists — good

mode=750 owner=root:root mount=/ path=/root/rhcsa_journal
mode=750 owner=root:root mount=/ path=/root/rhcsa_journal/lab-00a
mode=750 owner=root:root mount=/ path=/root/rhcsa_journal/lab-00a/task1
mode=750 owner=root:root mount=/ path=/root/rhcsa_journal/lab-00a/task2
── df -hT for /tmp and /root ──
Filesystem            Type   Size  Used Avail Use% Mounted on
tmpfs                 tmpfs  3.8G  1.2M  3.8G   1% /tmp
/dev/mapper/rhel-root xfs    17G  4.1G   13G  25% /
── findmnt for the journal mount ──
TARGET SOURCE                FSTYPE OPTIONS
/      /dev/mapper/rhel-root xfs    rw,relatime,attr2,inode64,...
exit was: 0
```

> Read the `mount=` column carefully: every journal path resolves to mount point `/` (the root partition, persistent). `/tmp` resolves to its own tmpfs mount — that is the structural reason the journal goes under `/root/`.

### Switches

| Token | Meaning |
|---|---|
| `mkdir -p PATH` | Create PATH and missing parents; idempotent |
| `mkdir -p A/{B,C}` | Brace expansion — creates A/B and A/C in one call |
| `chown -R USER:GRP PATH` | Recursive ownership change |
| `chmod 0750 PATH` | Mode 750: owner rwx, group r-x, others none |
| `stat -c '%m'` | Mount point that contains the file — the persistence field |
| `stat -c '%a'` | Octal access mode (e.g., `750`) |
| `df -hT PATH` | Human-readable disk usage + filesystem type |
| `findmnt -T PATH` | Find the mount that backs PATH |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | `/root/` is persistent | Stored on the root partition (xfs/ext4) — survives reboot |
|   | `/tmp/` is ephemeral | Stored on tmpfs (or cleared by systemd-tmpfiles) — does NOT survive reboot |
|   | `stat -c '%m'` | The mount-point field — exposes **why** a path is persistent |
|   | 0750 on evidence | Owner + root-group readable; nobody else listed — RHCSA-shaped permission |
|   | `mkdir -p` idempotence | Running this task twice does not error — same end state regardless |
|   | Explicit chown/chmod after mkdir | Never trust umask for evidence directories |
| 🪤 | **Trap Risk T00-A (reinforced)** | If `rpm -qi` showed `From repo: epel` in Task 1, the journal will document the trap — fix it before running Lab 00b. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Journal tree exists | `test -d /root/rhcsa_journal/lab-00a/task1 && test -d /root/rhcsa_journal/lab-00a/task2 && echo OK` | Both subdirectories must be present |
| Correct mode | `stat -c '%a %n' /root/rhcsa_journal/lab-00a` | Must print `750 /root/rhcsa_journal/lab-00a` |
| Correct mount | `findmnt -T /root/rhcsa_journal -no SOURCE,FSTYPE` | Must show a real block device + xfs/ext4 — NOT tmpfs |
| Evidence captured | `wc -l /root/rhcsa_journal/lab-00a/task2/evidence.txt` | Must be > 0 — proves the auditor commands ran and were saved |
| Reasoning preserved | `cat /root/rhcsa_journal/lab-00a/task2/why-root-not-tmp.txt` | The prose version of "why /root not /tmp" — survives so future-you remembers |

> **Reboot reasoning:** Everything in this task is on the root partition. After a reboot, `df -hT /root` still shows the same xfs/ext4 mount, and every file under `/root/rhcsa_journal/lab-00a/` is still there. That is the structural foundation Lab 00c will exercise — wipe `/tmp`, prove the journal still works.

### Journal write — BEFORE cleanup

```bash
LAB=lab-00a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
JOURNAL_ROOT: /root/rhcsa_journal
MODE:   $(stat -c '%a' /root/rhcsa_journal/lab-00a)
OWNER:  $(stat -c '%U:%G' /root/rhcsa_journal/lab-00a)
MOUNT:  $(stat -c '%m' /root/rhcsa_journal/lab-00a)
FSTYPE: $(findmnt -T /root/rhcsa_journal -no FSTYPE)
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Build the persistent journal tree; prove /root is durable, /tmp is not
COMMANDS: mkdir -p, chown -R, chmod 0750, stat -c '%m', df -hT, findmnt
TRAPS:    T00-A reinforced via the journal "From repo" record from Task 1
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-00b — install collections, write ~/.ansible.cfg + ~/inventory, run first playbook
EOF

ls -la "$JDIR"
cat "$JDIR/done.txt"
echo "exit was: $?"
```

### 🧹 Cleanup

Nothing to clean. The journal tree is intentionally persistent — Lab 00b and Lab 00c both depend on it, and so does every later lab in this series.

### Troubleshoot

| Symptom | Fix |
|---|---|
| `mkdir: cannot create directory '/root/rhcsa_journal'` | You are not root. Run `sudo -i` and retry. |
| `stat -c '%m'` not supported | Old `coreutils` — install `coreutils >= 8.30`. On RHEL 9 it is current. |
| `findmnt: command not found` | Install `util-linux`. RHEL 9 ships it by default. |
| Mode shown as `755` not `750` | The explicit `chmod 0750` did not run; rerun the chmod block. |
| `df -hT /tmp` shows the same filesystem as `/root` | `/tmp` is not separately mounted on this layout. It still clears on reboot if `systemd-tmpfiles` is enabled. Run `systemctl is-enabled systemd-tmpfiles-clean.timer` to confirm. |

> **STOP — paste the `stat -c 'mode=%a ... mount=%m path=%n'` block (showing mount=/ for every journal path) and `cat $JDIR/notes.txt` before completing Lab 00a.**

---

## Lab 00a Checklist (2 tasks)

- [ ] Task 1 — `dnf install -y ansible-core` (AppStream, not EPEL), verified with `rpm -q` + `rpm -qi` + `which` + `ansible --version` + transcript in journal
- [ ] Task 2 — `/root/rhcsa_journal/lab-00a/{task1,task2}` created with mode 0750, owner root:root, mount point proven to be the root partition (not tmpfs), + reasoning written to `why-root-not-tmp.txt`

---

## 🔗 Related Labs in the Trilogy

| Lab | Connection |
|---|---|
| **Lab 00b** — Ansible Control Node — Collections, Config & First Playbook | The Ansible half — installs `ansible.posix` + `community.general`, writes `~/.ansible.cfg` and `~/inventory`, runs the first `--check --diff` playbook |
| **Lab 00c** — Ansible Control Node — Verification Capstone & Persistence Proof | The auditor seat — three-tool audit (`rpm -qi`, `ansible-galaxy collection list`, `ansible -m ping`) + simulated-reboot persistence proof |
| Lab 01a — `stdout`, `>`, `>>` (Output Redirection RHCSA) | The next foundational lab — Lab 00 trilogy sets up the control node so Lab 01a can begin teaching the actual shell craft |
| Every later Lab N — Task 4 (Ansible) | Depends on the package install from Task 1 here and on the collections + config from Lab 00b |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
