# Lab 05: Directory Navigation — `pwd`, `cd`, relative paths, `cd -`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Career arcs covered:** RHCSA EX200 (shell movement, FHS literacy), RHCE EX294 (Ansible Boundary — control-flow that does not belong in a playbook), CKA (kubectl context vs shell cwd), RHCA — RH342 (forensic cwd inspection of running processes)
- **Prerequisite:** Lab 00 (Ansible control node) + Lab 04 (redirection)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 5 (ADHD 3-1-1 spec — 3 RHCSA + 1 Ansible Boundary + 1 Verification capstone)
- **Practice Directory (lab-wide rotation #05):** `/usr`
- **Sandbox:** `/tmp/nav-lab`
- **Traps rehearsed this lab:** **T41** (`cd` with no argument silently jumps to `$HOME` — easy to miss in scripts) · **T42** (`pwd -P` vs `pwd -L` returns different paths when a symlink is in play) · **T43** (Ansible has no `cd` — `chdir:` is per-task only)

> **This lab's practice directory is: `/usr`** — every task references it in at least two commands.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T41 T42 T43"
echo "📁  PRACTICE DIR: /usr"
echo ""
echo "💡 /usr top-level (read-only inspection):"
ls -d /usr /usr/* 2>/dev/null | head -10
```

> **STOP — paste header output before running setup.**

---

## 🎯 Objective

Move through the filesystem without leaving a single ambiguous step behind. By the end you will know:

- The difference between `pwd -L` (logical) and `pwd -P` (physical, resolved)
- How `cd ..`, `cd .`, `cd ~`, `cd -`, and `cd` (no arg) each behave
- Why `/usr` is the right rotation directory for this lab (FHS Layer 2 — distro-managed files)
- Why Ansible has no `cd` and what `chdir:` is for
- How to prove with RHCSA inspection commands that a navigation step succeeded

---

## 🛠️ Setup — run once before Task 1

```bash
mkdir -p /tmp/nav-lab/{a/b/c,parallel}
echo "fileA" > /tmp/nav-lab/a/file.txt
echo "fileB" > /tmp/nav-lab/a/b/file.txt
echo "fileC" > /tmp/nav-lab/a/b/c/file.txt
ln -sfn /tmp/nav-lab/a/b/c /tmp/nav-lab/symlink-to-c
sudo mkdir -p /root/rhcsa_journal/lab05
ls -lR /tmp/nav-lab
```

---

## Task 1 — Orient Yourself with `pwd` and `/usr`

**Practice directory this task:** `/usr`

`/usr` stores distro-shipped commands, libraries, docs, and shared data. It is the **right answer** to the question "where do package-managed files live?" Every command you have run in Labs 01–04 came from `/usr/bin/`. This task proves where you are, walks into `/usr`, and saves evidence.

### 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/nav-lab
sudo mkdir -p /root/rhcsa_journal/lab05/task1
date -Is | sudo tee /root/rhcsa_journal/lab05/task1/start.txt
echo "user=$(whoami) host=$(hostname) kernel=$(uname -r)" | sudo tee -a /root/rhcsa_journal/lab05/task1/start.txt
ls /usr 2>/dev/null | wc -l | sudo tee -a /root/rhcsa_journal/lab05/task1/start.txt
echo "exit was: $?"
```

### Purpose

Print the current working directory, walk into `/usr`, list its top-level entries, then return to `$HOME`. Save the transcript.

### Main Command Block

```bash
pwd                              # logical cwd
pwd -P                           # physical cwd (resolves symlinks)
cd /usr
pwd
ls -d /usr/*/                    # top-level subdirs of /usr
type ls                          # proves ls lives under /usr/bin (or /bin → /usr/bin)
cd                               # back to $HOME (T41: silent jump)
pwd

# Capture
{
  echo "=== before ===";   pwd
  echo "=== into /usr ===";cd /usr; pwd; ls -d /usr/*/
  echo "=== home ===";     cd;     pwd
} 2>&1 | sudo tee /root/rhcsa_journal/lab05/task1/transcript.txt
```

### Human-Readable Breakdown

`pwd` prints the current working directory the way the shell records it. On RHEL 9, `/bin` is a symlink to `/usr/bin`, so if you ever `cd /bin` and `pwd`, you stay logically in `/bin` — but `pwd -P` resolves the symlink and returns `/usr/bin`. That's the `-L` vs `-P` distinction.

`cd /usr` is an **absolute path** — it starts with `/`, so it doesn't care where you were. `cd` with no argument is a special case: it silently jumps to `$HOME`. In a script, this is **Trap T41**: someone reads `cd` and thinks "no-op," when in fact you just left whatever directory the script was working in.

### Reading It Left to Right

`cd /usr`

- `cd` — change directory builtin
- `/usr` — absolute path (begins with `/`); the shell does NOT consult `$PWD`

`pwd -P`

- `pwd` — print working directory builtin
- `-P` — print the **physical** path with symlinks resolved (RHEL: `/bin` → `/usr/bin`)

### The Story

A grader on the exam types `cd /usr; ls` to inspect distro-shipped commands. You should be able to type that without thinking. The interesting move is `pwd -P` — that's the diagnostic when a script behaves oddly because some user `cd`'d into a symlink earlier.

### Expected Output

```
$ pwd
/root
$ pwd -P
/root
$ cd /usr
$ pwd
/usr
$ ls -d /usr/*/
/usr/bin/  /usr/games/  /usr/include/  /usr/lib/  /usr/lib64/  /usr/libexec/  /usr/local/  /usr/sbin/  /usr/share/  /usr/src/  /usr/tmp/
$ type ls
ls is aliased to `ls --color=auto'
```

### Switches Table

| Switch | Meaning | Why it matters |
|---|---|---|
| `pwd -L` | Logical pwd (default) | Honours symlinks in `$PWD` |
| `pwd -P` | Physical pwd | Resolves symlinks — the **truth** |
| `cd` (no arg) | Jump to `$HOME` | T41 — silent in scripts |
| `cd -` | Jump back to `$OLDPWD` | Task 3 deep-dive |
| `type CMD` | Show whether CMD is a builtin, alias, or external | RHCSA "is this from /usr/bin?" diagnostic |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| `/usr` | Distro-managed files — packages install here, not in `/` directly |
| `pwd -P` | The physical truth, after symlink resolution |
| `cd` (no arg) | Jumps to `$HOME` — never silently in a script |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| **T41** | A script calls `cd` with no args and silently lands in `$HOME` instead of staying put | Always pass an explicit argument; reserve bare `cd` for interactive shells |
| **T42** | `pwd` shows `/bin/...` but the actual file is `/usr/bin/...` | Use `pwd -P` when chasing a path bug |

### 🔁 Persistence Check

```bash
test -f /root/rhcsa_journal/lab05/task1/transcript.txt && echo "transcript ok"
grep -c '/usr' /root/rhcsa_journal/lab05/task1/transcript.txt
```

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab05/task1/done.txt > /dev/null <<EOF
lab=05 task=1
when=$(date -Is)
practice_dir=/usr
home=$HOME
transcript=/root/rhcsa_journal/lab05/task1/transcript.txt
EOF
cat /root/rhcsa_journal/lab05/task1/done.txt
```

### 🧹 Cleanup

Nothing to clean — we only navigated and printed.

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `pwd` returns `/root` after `cd /usr` | A previous command silently `cd`'d — re-run `cd /usr; pwd` |
| `ls -d /usr/*/` returns empty | `/usr` not mounted — run `mount \| grep /usr` |

> **STOP — confirm transcript.txt contains `/usr` before Task 2.**

---

## Task 2 — Relative Paths: `..`, `.`, `~`, and Nested Movement

**Practice directory this task:** `/usr` (and `/tmp/nav-lab/a/b/c` as the leaf)

### 🔁 Warm-Up — Commands from Previous Labs

```bash
sudo mkdir -p /root/rhcsa_journal/lab05/task2
date -Is | sudo tee /root/rhcsa_journal/lab05/task2/start.txt
pwd | sudo tee -a /root/rhcsa_journal/lab05/task2/start.txt
ls -d /usr 2>/dev/null | sudo tee -a /root/rhcsa_journal/lab05/task2/start.txt
echo "exit was: $?"
```

### Purpose

Move through a 3-deep tree using only relative paths, return with `..`, and contrast `cd ~` (HOME) with `cd /usr/share` (absolute). Save the cwd at each step.

### Main Command Block

```bash
cd /tmp/nav-lab
pwd
cd ./a/b/c            # explicit "current dir then descend"
pwd
cat ./file.txt        # ./ = "this directory" — explicit current-dir read

cd ..                  # up one level
pwd
cd ../..               # up two more
pwd
cd ~                   # to $HOME
pwd
cd /usr/share          # absolute path
pwd
cd -                   # back to $OLDPWD (which was ~)
pwd

# Capture
{
  cd /tmp/nav-lab && pwd
  cd ./a/b/c && pwd && cat ./file.txt
  cd .. && pwd
  cd ../.. && pwd
  cd ~ && pwd
  cd /usr/share && pwd
} 2>&1 | sudo tee /root/rhcsa_journal/lab05/task2/transcript.txt
```

### Human-Readable Breakdown

A **relative path** is one that does NOT start with `/`. The shell resolves it by prepending `$PWD`. `./a/b/c` is identical to `a/b/c` — the `./` is just an explicit "this directory" marker that's required only when running an executable (`./script.sh`) where the shell would otherwise search `$PATH`.

`..` means "parent directory." `cd ..` goes up one level. `cd ../..` goes up two — strung together with `/` between. `cd ../sibling` is the classic move: up one, then down into a sibling tree.

`~` is shell-expanded to `$HOME` before `cd` even sees it. `cd ~user` jumps to *that user's* home (read from `/etc/passwd`).

### Reading It Left to Right

`cd ../..`

- `cd` — change directory
- `..` — parent directory
- `/` — path separator
- `..` — parent of the parent

`cat ./file.txt`

- `cat` — print file
- `./` — "current directory" explicit marker (here optional — just `file.txt` works)
- `file.txt` — file name

### The Story

In an exam scenario you're often dropped at `/root` and told to inspect `/etc/httpd/conf.d/*.conf`. You can `cd /etc/httpd/conf.d && ls`, or you can `ls /etc/httpd/conf.d/*.conf`. Either works. The trap is when a question says "from inside `/var/www/html`, edit the parent's index file" — that's `vim ../index.html`, not `vim /var/www/index.html` (which doesn't exist). Reading relative paths fluently is the skill.

### Expected Output

```
/tmp/nav-lab
/tmp/nav-lab/a/b/c
fileC
/tmp/nav-lab/a/b
/tmp/nav-lab
/root
/usr/share
/root
```

### Switches Table

| Token | Meaning | Why it matters |
|---|---|---|
| `.` | "this directory" | Required when running a script (`./script.sh`) |
| `..` | parent directory | The whole point of relative paths |
| `~` | `$HOME` | Shell-expanded BEFORE the command runs |
| `~user` | that user's `$HOME` | Read from `/etc/passwd` |
| `-` (with cd) | `$OLDPWD` | Toggle between two directories |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| Relative path | Does not start with `/`; resolved against `$PWD` |
| Absolute path | Starts with `/`; ignores `$PWD` |
| `./` prefix | Explicit "current dir"; required for running an executable that isn't in `$PATH` |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| **T42** | `cd ..` when `$PWD` is a symlinked dir — you land somewhere unexpected | `pwd -P` before navigating relatively |
| Tilde-expansion | Quoting `~` (`cd '~'`) suppresses expansion — you get the literal `~` directory | Never quote `~` for path arguments |

### 🔁 Persistence Check

```bash
grep -c '/tmp/nav-lab' /root/rhcsa_journal/lab05/task2/transcript.txt
grep -c '/usr/share'    /root/rhcsa_journal/lab05/task2/transcript.txt
```

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab05/task2/done.txt > /dev/null <<EOF
lab=05 task=2
when=$(date -Is)
practice_dir=/usr
last_pwd=$(pwd)
EOF
cat /root/rhcsa_journal/lab05/task2/done.txt
```

### 🧹 Cleanup

Nothing to clean — only navigation.

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `cd ..` did not change `$PWD` | You were at `/`; `..` of `/` is still `/` |
| `cd ~user`: "No such user" | Check `getent passwd user` — the account doesn't exist |

> **STOP — confirm `transcript.txt` shows the expected sequence of `pwd` outputs.**

---

## Task 3 — `cd -`, `$OLDPWD`, and the Two-Directory Toggle

**Practice directory this task:** `/usr` (`/usr/share/doc` as a real target)

### 🔁 Warm-Up — Commands from Previous Labs

```bash
sudo mkdir -p /root/rhcsa_journal/lab05/task3
date -Is | sudo tee /root/rhcsa_journal/lab05/task3/start.txt
pwd | sudo tee -a /root/rhcsa_journal/lab05/task3/start.txt
echo "OLDPWD=${OLDPWD:-unset}" | sudo tee -a /root/rhcsa_journal/lab05/task3/start.txt
echo "exit was: $?"
```

### Purpose

Use `cd -` (and the `$OLDPWD` variable behind it) to bounce between two directories quickly. Show the difference between `cd -` (changes cwd, prints the destination) and `echo $OLDPWD` (just reads).

### Main Command Block

```bash
cd /usr/share/doc
pwd
cd /etc
pwd
cd -                          # back to /usr/share/doc, prints it
pwd
cd -                          # back to /etc again
pwd

echo "OLDPWD is now: $OLDPWD"
echo "PWD    is now: $PWD"

# Capture
{
  cd /usr/share/doc && pwd
  cd /etc          && pwd
  cd -             # toggles, prints
  cd -             # toggles back
  echo "OLDPWD=$OLDPWD"
  echo "PWD=$PWD"
} 2>&1 | sudo tee /root/rhcsa_journal/lab05/task3/transcript.txt
```

### Human-Readable Breakdown

The shell keeps **two** path variables: `$PWD` (where you are) and `$OLDPWD` (where you just came from). Every `cd` updates them as a pair. `cd -` is shorthand for "swap them" — it changes `$PWD` to whatever `$OLDPWD` was, and prints the new `$PWD`. You can toggle between two directories indefinitely.

This matters on the exam because you might be editing a file in `/etc/httpd/conf.d/` and verifying logs in `/var/log/httpd/` — `cd -` is faster than re-typing either path.

### Reading It Left to Right

`cd -`

- `cd` — change directory builtin
- `-` — special argument meaning "use `$OLDPWD`" (and print the destination)

`echo "PWD=$PWD"`

- `echo` — print
- `"..."` — double-quote: keeps `$PWD` expanded
- `$PWD` — the current working directory variable

### The Story

If a question says "compare the SELinux contexts in `/etc/X` and `/var/lib/X`," your fastest path is `cd /etc/X; ls -Z; cd /var/lib/X; ls -Z; cd -; cd -`. Each `cd -` toggles you back. A grader doesn't care that you used `cd -` — but you finished the task in half the keystrokes.

### Expected Output

```
/usr/share/doc
/etc
/usr/share/doc       <-- printed by cd -
/etc                 <-- printed by cd -
OLDPWD is now: /usr/share/doc
PWD    is now: /etc
```

### Switches Table

| Token | Meaning | Why it matters |
|---|---|---|
| `cd -` | Toggle with `$OLDPWD` | Two-directory workflow |
| `$OLDPWD` | The previous cwd | Read-only inspection of where you came from |
| `$PWD` | The current cwd | Faster than calling `pwd` in a script |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| `$OLDPWD` | The directory `cd` last left |
| `cd -` | Jump back; prints the new `$PWD` |
| Two-toggle | Faster than absolute paths when working between exactly two directories |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| **T43** | A script calls `cd -` expecting toggle, but a sub-shell or `pushd`/`popd` mutated `$OLDPWD` in between | Use explicit `pushd dir1` / `popd` for stack-style nav in scripts |

### 🔁 Persistence Check

```bash
grep -c '/usr/share/doc' /root/rhcsa_journal/lab05/task3/transcript.txt
grep -c '/etc'           /root/rhcsa_journal/lab05/task3/transcript.txt
```

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab05/task3/done.txt > /dev/null <<EOF
lab=05 task=3
when=$(date -Is)
practice_dir=/usr
last_oldpwd=$OLDPWD
last_pwd=$PWD
EOF
cat /root/rhcsa_journal/lab05/task3/done.txt
```

### 🧹 Cleanup

Nothing to clean.

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `cd -` says "OLDPWD not set" | Fresh shell — do one `cd` first, then `cd -` works |
| `cd -` prints the wrong directory | A subshell mutated state — open a fresh shell and retry |

> **STOP — confirm transcript shows the toggle.**

---

## Task 4 — Ansible Boundary: Why There Is No `cd` in a Playbook

**Practice directory this task:** `/usr` (referenced from the playbook via `chdir:`)

> **This is an Ansible Boundary task.** There is no honest Ansible equivalent to `cd`. We will explain why, demonstrate the closest substitute (`chdir:` on `ansible.builtin.command`), and document the RHCE failure mode of pretending otherwise.

### 🔁 Warm-Up — Commands from Previous Labs

```bash
sudo mkdir -p /root/rhcsa_journal/lab05/task4/playbooks
date -Is | sudo tee /root/rhcsa_journal/lab05/task4/start.txt
ansible --version | head -1 | sudo tee -a /root/rhcsa_journal/lab05/task4/start.txt
ansible -m ping localhost 2>&1 | grep '"ping"' | sudo tee -a /root/rhcsa_journal/lab05/task4/start.txt
echo "exit was: $?"
```

If `ansible --version` or the ping fails, **go back to Lab 00**. Do not attempt Task 4 without a working control node.

### Purpose

Show, with a real playbook, that:

1. Ansible has **no** module called `cd` because every task is stateless — there is no persistent cwd between tasks
2. The closest substitute is `chdir:` on `ansible.builtin.command` (or `ansible.builtin.shell`), which sets cwd **for that one task only**
3. Wrapping `cd` in `command: cd /usr` would FAIL because `cd` is a shell *builtin*, not an executable

### Main Command Block

Write the boundary-demonstration playbook:

```bash
sudo tee /root/rhcsa_journal/lab05/task4/playbooks/nav-boundary.yml > /dev/null <<'EOF'
---
- name: Lab 05 Task 4 — Ansible Boundary for cd / navigation
  hosts: localhost
  become: true
  gather_facts: false
  tasks:

    - name: STEP A — chdir replaces cd for ONE task only
      ansible.builtin.command:
        cmd: pwd
        chdir: /usr
      register: chdir_result

    - name: STEP A.echo — print the pwd we observed inside /usr
      ansible.builtin.debug:
        msg: "chdir:/usr saw pwd = {{ chdir_result.stdout }}"

    - name: STEP B — the NEXT task does NOT remember /usr
      ansible.builtin.command:
        cmd: pwd
      register: next_task_result

    - name: STEP B.echo — proof of stateless cwd
      ansible.builtin.debug:
        msg: "next task pwd = {{ next_task_result.stdout }} (NOT /usr)"

    - name: STEP C — what NOT to do — wrapping cd as a command
      ansible.builtin.command:
        cmd: cd /usr
      register: bad_cd
      ignore_errors: true

    - name: STEP C.echo — confirm cd-as-command fails
      ansible.builtin.debug:
        msg: "cd-as-command rc={{ bad_cd.rc }} stderr={{ bad_cd.stderr }}"
EOF
```

Check-mode first (will skip command modules but parse syntax):

```bash
ansible-playbook --check --diff /root/rhcsa_journal/lab05/task4/playbooks/nav-boundary.yml \
  2>&1 | sudo tee /root/rhcsa_journal/lab05/task4/check.log
```

Apply:

```bash
ansible-playbook /root/rhcsa_journal/lab05/task4/playbooks/nav-boundary.yml \
  2>&1 | sudo tee /root/rhcsa_journal/lab05/task4/apply.log
```

### Human-Readable Breakdown

**Why no `cd` module:**

Ansible's job is to declare *state*. `cd` is not a state — it's a transient property of the shell running you. If two consecutive tasks both need to operate from `/usr`, they each say so via `chdir: /usr`. There is no `cd` module because there is no persistent cwd between tasks. Each module call gets a fresh process.

**STEP A** uses `ansible.builtin.command` with `chdir:` set to `/usr`. Inside that single task, the command runs as if you had `cd /usr` first. `pwd` prints `/usr`.

**STEP B** is the next task. It also runs `pwd`. It returns `/` (or whatever the user's launching cwd is) — NOT `/usr`. That's the proof of statelessness.

**STEP C** demonstrates the wrong instinct: `command: cd /usr`. This fails because `cd` is a **shell builtin** (it has to be — only the shell itself can change its own cwd). `ansible.builtin.command` runs executables via `exec()`, which only finds files in `$PATH`. There is no `/usr/bin/cd` binary. The task errors with `rc != 0`.

### Reading It Left to Right

```yaml
ansible.builtin.command:
  cmd: pwd
  chdir: /usr
```

- `ansible.builtin.command:` — FQCN of the command module
- `cmd:` — the executable to run (NOT a shell command — no globbing, no pipes)
- `chdir:` — change to this directory before running; ONLY for this task

```yaml
ignore_errors: true
```

- `ignore_errors:` — keep the play going even if this task fails
- Used here because we WANT the bad `cd /usr` task to fail so we can show its error

### The Story

The RHCE failure mode for navigation is to write `command: cd /usr && ls`. A grader reading that thinks: "this candidate doesn't understand that `&&` inside `command:` doesn't work because `command:` is exec, not a shell." So they switch to `shell:` (no `&&` problem there) — and now the grader sees `shell: cd /usr && ls` and thinks: "this candidate used `shell` instead of a real module — partial credit at best."

The right answer when you genuinely need to operate in `/usr` from Ansible is either:

- `chdir:` on `ansible.builtin.command` / `ansible.builtin.shell` for one task, OR
- Use a module that takes an absolute `path:` (`ansible.builtin.file`, `ansible.builtin.copy`, `ansible.posix.firewalld --service=...`) — no cwd ever needed

### Expected Output

```
TASK [STEP A — chdir replaces cd for ONE task only] ***
changed: [localhost]
TASK [STEP A.echo] ***
ok: [localhost] => msg: "chdir:/usr saw pwd = /usr"

TASK [STEP B — the NEXT task does NOT remember /usr] ***
changed: [localhost]
TASK [STEP B.echo] ***
ok: [localhost] => msg: "next task pwd = / (NOT /usr)"

TASK [STEP C — what NOT to do] ***
fatal: [localhost]: FAILED! => {"rc": 2, "stderr": "[Errno 2] No such file or directory: b'cd'"}
...ignoring
TASK [STEP C.echo] ***
ok: [localhost] => msg: "cd-as-command rc=2 stderr=[Errno 2] No such file or directory: b'cd'"

PLAY RECAP ***
localhost : ok=6 changed=2 unreachable=0 failed=0 (ignored=1)
```

### Switches Table

| Switch / Key | Meaning | Why it matters |
|---|---|---|
| `ansible.builtin.command` | Run an executable directly (no shell) | The right module 95% of the time |
| `ansible.builtin.shell` | Run a string through `/bin/sh -c` | Required when you need `\|`, `>`, `&&`, builtins |
| `chdir: PATH` | Change to PATH before running the command | The only "cd" Ansible has |
| `ignore_errors: true` | Continue play on task failure | Used here to demonstrate the bad path |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| Ansible task statelessness | Every task is a fresh process; no cwd, no env, no $OLDPWD between tasks |
| `chdir:` | Per-task cwd override for `command`/`shell` only |
| Why `command: cd /usr` fails | `cd` is a shell builtin; not an executable in `/usr/bin/` |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| **T43** | Writing `command: cd /usr && ls` expecting it to behave like a shell | Use `chdir: /usr` and split the operation, OR use a real module that takes `path:` |
| Wrapper-instinct | Reaching for `shell:` because `command:` "doesn't work" | First ask: is there a real module? `ansible.builtin.file`, `ansible.builtin.copy`, `ansible.posix.mount` ... |
| **Boundary** | Treating Task 4 of this lab as proof Ansible can do navigation | This is the **boundary** — Ansible does NOT do navigation. RHCE answer is to call modules with absolute paths |

### 🔁 Persistence Check

```bash
test -f /root/rhcsa_journal/lab05/task4/playbooks/nav-boundary.yml && echo "playbook ok"
grep -c 'chdir:/usr saw pwd = /usr' /root/rhcsa_journal/lab05/task4/apply.log
grep -c 'next task pwd = /'         /root/rhcsa_journal/lab05/task4/apply.log
grep -c 'cd-as-command rc=2'        /root/rhcsa_journal/lab05/task4/apply.log
```

All three greps must return `1`. That is the proof that:

1. `chdir:` works for one task
2. The next task forgets it
3. `cd` cannot be run as a command

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab05/task4/done.txt > /dev/null <<EOF
lab=05 task=4
when=$(date -Is)
boundary=ansible-has-no-cd
playbook=/root/rhcsa_journal/lab05/task4/playbooks/nav-boundary.yml
proof_chdir=$(grep -c 'pwd = /usr' /root/rhcsa_journal/lab05/task4/apply.log)
proof_stateless=$(grep -c 'pwd = /' /root/rhcsa_journal/lab05/task4/apply.log)
proof_cd_fails=$(grep -c 'cd-as-command rc=2' /root/rhcsa_journal/lab05/task4/apply.log)
EOF
cat /root/rhcsa_journal/lab05/task4/done.txt
```

### 🧹 Cleanup

The playbook stays as a permanent demonstration of the boundary. Nothing else to clean.

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| Apply errors on STEP A | Check `become: true` and that `chdir:` is `/usr` (absolute path) |
| STEP C does NOT fail | You're on a system where `cd` is a shim in PATH — re-test with `/usr/bin/cd` (still fails) |

> **STOP — confirm all three `grep -c` checks return 1 before Task 5.**

---

## Task 5 — RHCSA Verification Capstone: Prove the Boundary

**Practice directory this task:** `/usr`

### 🔁 Warm-Up — Commands from Previous Labs

```bash
sudo mkdir -p /root/rhcsa_journal/lab05/task5
date -Is | sudo tee /root/rhcsa_journal/lab05/task5/start.txt
pwd | sudo tee -a /root/rhcsa_journal/lab05/task5/start.txt
echo "exit was: $?"
```

### Purpose

Use **only** RHCSA inspection commands (no `ansible` CLI, no playbook execution) to prove:

1. The system's idea of "where am I" matches what we expect after each navigation
2. The Task 4 playbook file persists on disk and is readable
3. The journal evidence from Tasks 1–4 is intact

### Main Command Block

Three RHCSA inspection commands:

```bash
# 1) Filesystem inspection — /usr exists, is a real directory, package-managed
ls -ld /usr
stat -c 'mode=%a owner=%U group=%G type=%F' /usr
mount | grep -E ' on /usr ' || echo "(no separate /usr mount — normal for RHEL 9)"

# 2) Path-resolution inspection — pwd -L vs pwd -P near a known symlink
ls -ld /bin
readlink /bin
cd /bin && pwd && pwd -P
cd /usr/bin && pwd && pwd -P
cd

# 3) Playbook + journal inspection — Task 4 artifact still on disk
ls -l /root/rhcsa_journal/lab05/task4/playbooks/nav-boundary.yml
cat /root/rhcsa_journal/lab05/task4/playbooks/nav-boundary.yml | head -5
ls -l /root/rhcsa_journal/lab05/task*/done.txt

# Capture combined evidence
{
  echo "=== /usr metadata ===";       ls -ld /usr; stat -c 'mode=%a owner=%U' /usr
  echo "=== /bin symlink ===";        ls -ld /bin; readlink /bin
  echo "=== pwd -L vs pwd -P ===";    cd /bin && pwd; pwd -P; cd
  echo "=== playbook persists ==="; ls -l /root/rhcsa_journal/lab05/task4/playbooks/nav-boundary.yml
  echo "=== journal trail ===";       ls -l /root/rhcsa_journal/lab05/task*/done.txt
} 2>&1 | sudo tee /root/rhcsa_journal/lab05/task5/evidence.txt
```

### Human-Readable Breakdown

A grader's audit of "navigation" looks like this:

1. `ls -ld /usr` — does the directory exist and is it a directory? (`d` first char of mode column)
2. `readlink /bin` — is `/bin` a symlink? On RHEL 9, yes — to `usr/bin`. That's the proof of T42
3. `cd /bin && pwd -P` — `pwd -P` returns `/usr/bin`, not `/bin`. That's the symlink resolution
4. `ls -l playbook.yml` — the Task 4 artifact still exists, with whatever mode you saved it as

You did NOT run `ansible-playbook` in Task 5. The auditor seat is hand-typed RHCSA only.

### Reading It Left to Right

`stat -c 'mode=%a owner=%U group=%G type=%F' /usr`

- `stat` — file metadata
- `-c` — custom format
- `%a` — octal access mode
- `%U` — owner username
- `%G` — group name
- `%F` — file type as a word ("directory", "symbolic link", ...)

`readlink /bin`

- `readlink` — print the target of a symlink (errors on non-symlinks)
- `/bin` — the symlink itself

### The Story

You're handing a grader a single text file (`evidence.txt`) that, read top-to-bottom, proves: "I know where `/usr` is, I know `/bin` is a symlink to `/usr/bin`, I demonstrated `pwd -L` ≠ `pwd -P`, I kept my Ansible playbook, and I journaled each step." That's an RHCSA + RHCE-shaped answer for a navigation lab.

### Expected Output

```
drwxr-xr-x. 13 root root 167 May 10 09:14 /usr
mode=755 owner=root group=root type=directory
(no separate /usr mount — normal for RHEL 9)
lrwxrwxrwx. 1 root root 7 May 10 09:14 /bin -> usr/bin
usr/bin
/bin
/usr/bin
/usr/bin
/usr/bin
-rw-r--r--. 1 root root 1234 May 27 15:04 /root/rhcsa_journal/lab05/task4/playbooks/nav-boundary.yml
```

### Switches Table

| Switch | Meaning | Why it matters |
|---|---|---|
| `ls -ld` | Long listing of a directory itself (not its contents) | RHCSA inspection of `/usr` |
| `stat -c FMT` | Custom format | Mode + owner + type in one line |
| `readlink PATH` | Print symlink target | Proves `/bin` → `usr/bin` (T42) |
| `pwd -L` vs `pwd -P` | Logical vs physical cwd | The whole point of this lab |

### 🧠 Concept Card

| Concept | One-Line |
|---|---|
| RHCSA navigation audit | `ls -ld`, `stat`, `readlink`, `pwd -P` |
| Reboot reasoning | Navigation doesn't persist — but the playbook file in `/root/` does |
| Ansible Boundary proof | The boundary is documented in the playbook + apply.log; the system state itself didn't change |

| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| Auditor-skip | Trusting "the playbook ran fine, I'm done" without running RHCSA inspection | Always do `ls -ld`, `stat`, `readlink` in Task 5 |
| **T42** | Believing `pwd` always returns the physical truth | `pwd -P` is the truth; `pwd -L` is what the shell remembers |

### 🔁 Persistence Check (Reboot Reasoning)

```bash
echo "REBOOT REASONING:"                                                       | sudo tee /root/rhcsa_journal/lab05/task5/reboot.txt
echo "1. Navigation itself does not persist — every shell starts at $HOME."   | sudo tee -a /root/rhcsa_journal/lab05/task5/reboot.txt
echo "2. The Task 4 playbook persists because it lives in /root/, not /tmp/." | sudo tee -a /root/rhcsa_journal/lab05/task5/reboot.txt
echo "3. The /bin → usr/bin symlink is a distro fact; survives reboot."       | sudo tee -a /root/rhcsa_journal/lab05/task5/reboot.txt
test -f /root/rhcsa_journal/lab05/task4/playbooks/nav-boundary.yml && echo "playbook persists" | sudo tee -a /root/rhcsa_journal/lab05/task5/reboot.txt
readlink /bin | sudo tee -a /root/rhcsa_journal/lab05/task5/reboot.txt
```

### 📓 Journal Write

```bash
sudo tee /root/rhcsa_journal/lab05/task5/done.txt > /dev/null <<EOF
lab=05 task=5
when=$(date -Is)
evidence=/root/rhcsa_journal/lab05/task5/evidence.txt
reboot=/root/rhcsa_journal/lab05/task5/reboot.txt
status=lab05-complete
EOF
cat /root/rhcsa_journal/lab05/task5/done.txt
```

### 🧹 Cleanup

```bash
# Sandbox cleanup
sudo rm -rf /tmp/nav-lab
ls -d /tmp/nav-lab 2>&1 | grep -q "No such" && echo "sandbox cleaned"

# Journal stays — that's the whole point
ls /root/rhcsa_journal/lab05/
```

### Troubleshoot Table

| Symptom | Fix |
|---|---|
| `readlink /bin` says "not a symlink" | You're on a non-RHEL system where `/bin` is a real dir — that's fine; note it in evidence.txt |
| `cd /bin && pwd -P` returns `/bin` | Same as above — system uses real `/bin` |
| `cat done.txt` fails | Re-run the Journal Write block for that task |

> **STOP — confirm `status=lab05-complete` in `done.txt`. Lab 05 is finished.**

---

## ✅ Lab 05 Complete When

```bash
ls /root/rhcsa_journal/lab05/task{1,2,3,4,5}/done.txt
grep -l 'lab05-complete' /root/rhcsa_journal/lab05/task5/done.txt
test -f /root/rhcsa_journal/lab05/task4/playbooks/nav-boundary.yml
```

All three checks must succeed. The Ansible Boundary is documented; you understand that `cd`/`pwd` are RHCSA-only concepts and Ansible navigates by passing absolute paths to real modules.
