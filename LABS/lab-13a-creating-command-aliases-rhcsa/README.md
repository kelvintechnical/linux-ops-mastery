# Lab 13a: Creating Command Aliases (RHCSA) — `alias`, `unalias`, `~/.bashrc`, `/etc/profile.d/`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `13a` (RHCSA) → `13b` (Ansible) → `13c` (Verify)
- **Career arcs covered:** RHCSA EX200 (occasional "set up this shortcut" tasks), RHCE EX294 (`ansible.builtin.blockinfile` / `template` to manage shell-init files), SRE (bastion-host quality-of-life aliases like `k='kubectl'`), DevOps (developer-experience defaults), AI/MLOps (`alias jl='jupyter lab --no-browser'` notebook server shortcuts)
- **Prerequisite:** Lab 12 trilogy (`mkdir -p` underlies `/etc/profile.d/` setup)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = transient + per-user persistence, Task 2 = system-wide + the sudo trailing-space trick)
- **Practice Directory (rotation #13):** `/srv`
- **Sandbox:** `/etc/profile.d/lab13-*.sh` (writes there) + `~/.bashrc` (per-user persistence)
- **Traps rehearsed this lab:** **T13-A** (aliases don't expand in non-interactive scripts — `bash -c 'alias-name'` fails) · **T13-B** (forgetting the trailing space in `alias sudo='sudo '` — breaks `sudo NAME` expansion)

> **This lab's practice directory is: `/srv`** — every task references it (we model "shortcut for service-related directories" using `/srv` paths).

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
echo "⚠️  TRAP REMINDERS THIS LAB: T13-A T13-B"
echo "📁  PRACTICE DIR: /srv"
echo ""
echo "💡 /srv occupants (we read /srv; we write into /etc/profile.d/ and ~/.bashrc):"
ls -ld /srv 2>/dev/null
ls /srv 2>/dev/null | head -n 5
echo "Shell version: $BASH_VERSION"
```

> **STOP — paste header output before running setup.**

---

## Objective

Stop typing the same long command 20 times a day. Make aliases that **survive logouts**, work with `sudo`, and are deployable to every user on the system via `/etc/profile.d/`. By the end of this lab you also understand WHY aliases work only as the **first word** of a command — and when an alias should be promoted into a function or a script.

---

## Concept: An Alias Is First-Word Text Substitution

When bash sees a command line, before executing it, bash checks whether the **first word** is the name of an alias. If yes, bash replaces that word with the alias body, then **re-parses** the command line, then executes. It is text substitution at the parse level — not a function call, not a wrapper script.

```
   alias ll='ls -lhA --color=auto'
   ll /srv
       │
       └── bash sees `ll` as the first word
           bash substitutes:  ls -lhA --color=auto /srv
           bash re-parses and executes
```

Only the **first word** is checked. `sudo ll` does NOT expand `ll` because `ll` is the second word — `sudo` is the first.

> **The escape hatch:** if `alias sudo='sudo '` ends with a **trailing space**, bash documented rule kicks in: "If the last character of the value of the alias is a blank, then the next command word following the alias is also checked for alias expansion." That trailing space is what makes `sudo ll` work. Forgetting it is T13-B.

---

## Alias Reference

| Task | Command | Notes |
|---|---|---|
| Create alias | `alias NAME='BODY'` | Quote the body |
| List all aliases | `alias` | No arguments |
| List one alias | `alias NAME` | |
| Remove alias | `unalias NAME` | This shell only |
| Remove all aliases | `unalias -a` | This shell only |
| Bypass alias once | `\NAME args...` | Or `command NAME` |
| Make `sudo` honor aliases | `alias sudo='sudo '` | TRAILING SPACE — that's the magic |
| Inspect what NAME resolves to | `type NAME` | Reports alias / function / builtin / external |
| Persistent per-user | Append to `~/.bashrc` | New interactive shells get it |
| Persistent system-wide | New file in `/etc/profile.d/*.sh` | All interactive shells get it |
| Reload current shell | `source FILE` or `. FILE` | Or open a new terminal |

---

## Where Aliases Live

| File | Scope |
|---|---|
| `~/.bashrc` | Per-user, interactive shells |
| `~/.bash_profile` | Per-user, login shells (less common for aliases) |
| `/etc/bashrc` | System-wide, interactive shells |
| `/etc/profile.d/*.sh` | System-wide, sourced by `/etc/profile` (login) and `/etc/bashrc` (interactive) |

**Rule:** Per-user goes in `~/.bashrc`. System-wide goes in `/etc/profile.d/<name>.sh`. Editing `/etc/bashrc` for personal preferences is wrong — that affects every user.

---

## Lab-Wide Setup

```bash
sudo -i

# Backup user's .bashrc so we can restore at end
cp -a ~/.bashrc ~/.bashrc.bak.lab13.$(date +%F-%H%M)

ls -la /srv
ls -la /etc/profile.d/ | head -n 10
test -f ~/.bashrc && echo ".bashrc backed up"
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

## Task 1 — Transient alias + per-user persistence in `~/.bashrc`

**Practice directory this task:** `/srv` · we create shortcut aliases that target `/srv` paths (a typical use case: `alias web='cd /srv/www'`).

### Warm-Up

```bash
echo "Shell version: $BASH_VERSION"
ls -la /srv                                          2>&1 | tee /tmp/lab13a-warmup.txt
alias | wc -l
type ls
test -f ~/.bashrc.bak.lab13.* && echo "backup OK"
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 12: `test -f` guard pattern — refuse to proceed if the backup file is missing.

### Purpose

Define an alias in the current shell, observe first-word substitution, inspect with `type`, remove with `unalias`. Then **persist** two aliases by appending to `~/.bashrc`, source the file, and verify in a **fresh interactive subshell** with `bash -ic` — the only honest test that the alias survives the parent shell.

### WEAVE TRACE

| Warm-up command | Role inside Task 1 |
|---|---|
| `alias \| wc -l` | Counts aliases BEFORE and AFTER — proves the new ones were added |
| `type NAME` | The inspection primitive used three times: before define, after define, after unalias |
| `test -f ~/.bashrc.bak.*` | Guards the bashrc-append step — refuses to edit unless backup exists |
| `2>&1 \| tee` | Captures the transcript to `/tmp/lab13a-task1.txt` for the journal |
| `ls -la /srv` | Real-world target the aliases will reference (`alias web='cd /srv/www'`) |
| `$(date -Is)` | Stamps the journal `notes.txt` |

### Main command block

```bash
mkdir -p /srv/www /srv/ftp
mkdir -p /tmp/lab13a
TASKLOG=/tmp/lab13a/task1.txt

ALIASES_BEFORE=$(alias | wc -l)
echo "aliases before: $ALIASES_BEFORE"                  2>&1 | tee $TASKLOG

# ── Part A: transient — define, use, inspect, remove ─────────────────
alias web='cd /srv/www'
alias ftp='cd /srv/ftp'
alias greet='echo hello'

alias web ftp greet                                     2>&1 | tee -a $TASKLOG
type web                                                2>&1 | tee -a $TASKLOG

# Bypass the alias for one call
\type ls                                                2>&1 | tee -a $TASKLOG    # \type bypasses any 'type' alias (defensive)
command ls /srv | head -n 3                             2>&1 | tee -a $TASKLOG    # 'command' skips alias lookup

unalias greet
alias greet 2>&1 | head -n 1                            | tee -a $TASKLOG          # error proves removal

# ── Part B: per-user persistence in ~/.bashrc ────────────────────────
cat >> ~/.bashrc <<'EOF'

# === Lab 13a aliases (per-user) ===
alias web='cd /srv/www'
alias ftp='cd /srv/ftp'
alias ll='ls -lhA --color=auto'
alias ..='cd ..'
# === end Lab 13a aliases ===
EOF

# Reload current shell
source ~/.bashrc
type web ll ..                                          2>&1 | tee -a $TASKLOG

# Verify in a FRESH interactive subshell — this is the honest test
bash -ic 'type web; type ll; type ..'                   2>&1 | tee -a $TASKLOG

ALIASES_AFTER=$(alias | wc -l)
echo "aliases after: $ALIASES_AFTER  delta=$(( ALIASES_AFTER - ALIASES_BEFORE ))" | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

**Part A — transient.** Define three aliases (`web`, `ftp`, `greet`). Inspect with `alias NAME` and `type NAME` (two different inspection tools — `type` is more authoritative because it shows what name resolves to **including** alias/function/builtin distinction). Use the `\NAME` and `command NAME` bypass forms (escape hatches when an alias misbehaves). Remove `greet` with `unalias` and confirm the removal by trying to display it (the error message proves absence).

**Part B — per-user persistence.** Append a labeled block of aliases to `~/.bashrc`. Source the file to load them into the current shell. Verify with `type` in the current shell. **Then verify in a fresh `bash -ic 'cmd'` subshell** — `bash -i` forces interactive mode (otherwise aliases are not expanded), `-c` runs a single command. This is the honest test: if the alias appears in `bash -ic`, it will appear for every new terminal the user opens.

### Reading it left to right

- `alias NAME='BODY'` — register a substitution. Single quotes prevent early variable expansion in the body.
- `type NAME` — reports `NAME is aliased to 'BODY'` for aliases, `NAME is a function` for functions, `NAME is /usr/bin/NAME` for external commands.
- `\NAME` — backslash before the name disables alias lookup for ONE invocation only.
- `command NAME` — built-in that skips alias and function lookup; preferred in scripts.
- `cat >> ~/.bashrc <<'EOF' ... EOF` — append a heredoc. `'EOF'` (quoted) prevents `$variable` expansion inside the heredoc body (which we want — the alias body has no variables to expand).
- `source FILE` (or `. FILE`) — execute FILE in the **current** shell so its side effects (variable assignments, alias definitions, function definitions) persist.
- `bash -ic 'CMD'` — `-i` = interactive (without it, aliases would not expand); `-c` = run this single command.

### The story

`type` is more authoritative than `alias` for inspection because `type` tells you what bash would actually do when you type the name — whether it resolves to a builtin (like `cd`), a function, an alias, or an external command on `$PATH`. Senior engineers run `type COMMAND` whenever a command "behaves weird" — it instantly reveals whether something has been shimmed.

The `bash -ic` verification trick is the single most important habit in this lab. `~/.bashrc` is sourced by interactive shells only — running `bash -c 'type web'` (without `-i`) would show "command not found" even though the alias is correctly defined. The interactive mode flag is what triggers the rc-file sourcing. If you forget `-i`, you will conclude your persistence is broken when it isn't, and waste an hour debugging.

### Expected output

```text
GNU bash, version 5.1.8(1)-release ...
total 16
drwxr-xr-x.  2 root root 6 ... /srv
9
ls is aliased to `ls --color=auto'
backup OK
aliases before: 9
alias web='cd /srv/www'
alias ftp='cd /srv/ftp'
alias greet='echo hello'
web is aliased to `cd /srv/www'
type is a shell builtin
ftp  www
bash: alias: greet: not found
web is aliased to `cd /srv/www'
ll is aliased to `ls -lhA --color=auto'
.. is aliased to `cd ..'
web is aliased to `cd /srv/www'
ll is aliased to `ls -lhA --color=auto'
.. is aliased to `cd ..'
aliases after: 13  delta=4
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| `alias NAME=BODY` | Create alias |
| `alias NAME` | Inspect single alias |
| `unalias NAME` | Remove this shell only |
| `\NAME` | Bypass alias for one invocation |
| `command NAME` | Bypass alias and function lookup |
| `type NAME` | What does NAME resolve to (alias / function / builtin / external) |
| `cat >> FILE <<'EOF'` | Append heredoc, no `$` expansion |
| `source FILE` / `. FILE` | Re-execute FILE in current shell |
| `bash -ic 'CMD'` | Fresh interactive subshell |

### Concept Card

| Concept | What it does |
|---|---|
| First-word substitution | Only the first word of a command is checked for alias expansion |
| `type` over `alias` | More authoritative — shows resolution path (alias/function/builtin/external) |
| Bypass forms `\NAME` and `command NAME` | Defensive escape hatches when alias misbehavior is suspected |
| Heredoc with quoted EOF | Literal text, no shell expansion in body |
| `bash -ic` fresh-subshell test | The honest persistence verification — without `-i`, aliases never expand |
| **🪤 Trap Risk T13-A** | Putting aliases in scripts: non-interactive shells don't expand aliases. Use functions or full commands in scripts. |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Aliases in ~/.bashrc | `grep '^alias' ~/.bashrc \| wc -l` | Counts persisted alias lines |
| Fresh-shell visible | `bash -ic 'type web; type ll'` | The honest interactive-shell test |
| Backup exists | `ls ~/.bashrc.bak.lab13.*` | Recovery path if .bashrc breaks |

> **Reboot reasoning:** `~/.bashrc` is on the root partition (under `/home/USER/`). Survives reboot. After reboot, every new terminal sources `~/.bashrc` automatically — the aliases are immediately available. Without rc-file persistence (Part A's transient aliases), the reboot kills them.

### Journal write

```bash
LAB=lab-13a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab13a/task1.txt "$JDIR/evidence.txt"
cp ~/.bashrc "$JDIR/bashrc-snapshot.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Transient alias + per-user persistence in ~/.bashrc
COMMANDS: alias, unalias, type, \\NAME, command NAME, source, bash -ic
TRAPS:    T13-A rehearsed (we verified bash -ic specifically, not bare bash -c)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — system-wide via /etc/profile.d/ + sudo trailing-space trick (T13-B)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup

```bash
# Remove the Lab 13a block from ~/.bashrc (we'll re-deploy via /etc/profile.d in Task 2)
sed -i '/=== Lab 13a aliases/,/=== end Lab 13a aliases ===/d' ~/.bashrc
rm -rf /tmp/lab13a /srv/www /srv/ftp
grep -c "Lab 13a" ~/.bashrc || echo "block removed cleanly"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `bash: alias: not found` | Running `sh` or `dash` instead of `bash`. Switch shells. |
| Alias body has unexpected `$VAR` value | Used double quotes — `$VAR` expanded at definition time. Use single quotes. |
| New shell does not have alias | Test with `bash -ic` not bare `bash -c`. Interactive flag is required. |
| `source ~/.bashrc` errors | Syntax error in your edits. Restore from backup: `cp ~/.bashrc.bak.lab13.* ~/.bashrc` |
| `unalias` says not found in current shell but new shell has it | Alias is also defined in an rc file — also remove from there |

> **STOP — paste `bash -ic 'type web; type ll'` output before Task 2.**

---

## Task 2 — System-wide via `/etc/profile.d/` + the sudo trailing-space trick (T13-B)

**Practice directory this task:** `/srv` · we deploy system-wide aliases that target `/srv` and verify they're visible to **every** user logging in.

### Warm-Up

```bash
ls -la /etc/profile.d/ | head -n 10                       2>&1 | tee /tmp/lab13a-warmup-t2.txt
type sudo
alias sudo 2>/dev/null || echo "no sudo alias currently"
test -d /etc/profile.d && echo "profile.d OK"
stat -c '%n mode=%a owner=%U:%G' /etc/profile.d
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: `type NAME` is still our authoritative inspection primitive. Now used cross-user via `su - USER -c '...'`.

### Purpose

Deploy a system-wide alias file at `/etc/profile.d/lab13-admin-aliases.sh` and verify every user gets the aliases on login. Then demonstrate the `alias sudo='sudo '` trailing-space trick — explain why `sudo ll` fails without it (first-word substitution rule) and works with it.

### WEAVE TRACE

| Warm-up command | Role inside Task 2 |
|---|---|
| `ls /etc/profile.d/` | Verifies the deployment target directory; we add our file to this listing |
| `stat -c '%a owner=%U:%G'` | Captures the deployed file's mode and ownership — must be `0644 root:root` for all users to read |
| `type sudo` | Inspection before and after the trailing-space trick |
| `2>&1 \| tee` | Captures the deployment + verification transcript |
| `set -o pipefail` | Catches a silent failure in the cross-user verification chain |

### Main command block

```bash
sudo -i
TASKLOG=/tmp/lab13a/task2.txt
mkdir -p /tmp/lab13a

# ── Part A: deploy system-wide alias file ─────────────────────────────
cat > /etc/profile.d/lab13-admin-aliases.sh <<'EOF'
# System-wide aliases — lab 13a (RHCSA capstone)
alias ll='ls -lhA --color=auto'
alias svc='systemctl --no-pager status'
alias listen='ss -tunap'
alias srv='cd /srv'
EOF

chmod 0644 /etc/profile.d/lab13-admin-aliases.sh
restorecon -v /etc/profile.d/lab13-admin-aliases.sh   2>&1 | tee -a $TASKLOG
ls -lZ /etc/profile.d/lab13-admin-aliases.sh          2>&1 | tee -a $TASKLOG

# Source for current root shell
source /etc/profile.d/lab13-admin-aliases.sh
type ll svc listen srv                                 2>&1 | tee -a $TASKLOG

# Cross-user verify in a fresh login shell as ec2-user
# (skip gracefully if the user doesn't exist on this box)
if id ec2-user >/dev/null 2>&1; then
  su - ec2-user -c 'bash -lc "type ll svc listen srv"' 2>&1 | tee -a $TASKLOG
else
  echo "(ec2-user not on this host — skipping cross-user check)" | tee -a $TASKLOG
fi

# ── Part B: T13-B — the sudo trailing-space trick ─────────────────────
echo ""                                                | tee -a $TASKLOG
echo "─── T13-B demonstration: sudo + aliases ───"     | tee -a $TASKLOG

# First, without the trick — sudo ll FAILS because ll is second word
unalias sudo 2>/dev/null || true
sudo ll /root 2>&1 | head -n 1                         | tee -a $TASKLOG

# Now add the trailing-space alias (THE MAGIC IS THE SPACE)
alias sudo='sudo '
type sudo                                              2>&1 | tee -a $TASKLOG
sudo ll /root 2>&1 | head -n 3                         | tee -a $TASKLOG

# Visually inspect: the trailing space is what bash uses to trigger
# "also check the next word for alias expansion"
alias sudo | cat -A                                    2>&1 | tee -a $TASKLOG    # cat -A shows the $ at line end; you'll see ' '$ marker before $

echo "exit was: $?"
```

### Human-readable breakdown

**Part A — system-wide deployment.** Become root. Write a single-purpose `/etc/profile.d/lab13-admin-aliases.sh` that defines four aliases (`ll`, `svc`, `listen`, `srv`). Set mode to `0644` (world-readable). Restore SELinux context with `restorecon` (RHEL needs `bin_t` for sourced scripts in `/etc`). Source for the current root shell. **Cross-user verify** by spawning a fresh login shell as `ec2-user` and running `type` for each alias — they should all be visible because `/etc/profile.d/*.sh` is sourced by every interactive login shell.

**Part B — T13-B demonstration.** Without the trailing-space trick: `sudo ll` reports "command not found" because bash's first-word rule means it doesn't check `ll` (which is the second word). Add `alias sudo='sudo '` (with the literal trailing space inside the quotes). Now `sudo ll` works because bash's documented rule kicks in: "If the last character of the value of the alias is a blank, the next command word following the alias is also checked for alias expansion."

### Reading it left to right

- `cat > FILE <<'EOF' ... EOF` — write FILE from a heredoc; `'EOF'` quoted prevents `$variable` interpolation in the body.
- `chmod 0644` — world-readable so all users can source; owner-writable for root.
- `restorecon -v PATH` — restore the SELinux context per policy. Without this, sourced files may be labeled wrong and refused (rare but possible).
- `ls -lZ` — `Z` flag shows SELinux context.
- `su - USER -c 'CMD'` — `-` resets environment to USER's defaults (login shell), `-c` runs the command. `bash -lc` inside forces a login shell explicitly.
- `cat -A FILE` — show ALL whitespace and end-of-line markers: `$` at line end, `^I` for tab, `M-^X` for high bytes. We use it to **see** the trailing space in `alias sudo`.

### The story

`/etc/profile.d/*.sh` is the canonical fleet-wide alias deployment mechanism. Every operator who logs into the system inherits the file — no per-user `~/.bashrc` editing required. Configuration management tools (Ansible, Puppet, Salt) all converge on this pattern. The mode is `0644` (every user readable); the SELinux context must be the default (`bin_t` for the path) — `restorecon` enforces it.

The trailing-space trick (T13-B) is the most under-taught bash feature in the world. Once you discover it, you wonder why nobody taught it to you on day one. Without it, every `sudo NAME` invocation fails for aliased names. With it, the entire alias system extends naturally to elevated commands.

### Expected output

```text
total 36
-rw-r--r--. 1 root root 195 Apr ... 256term.csh
-rw-r--r--. 1 root root 199 Apr ... 256term.sh
...
sudo is /usr/bin/sudo
no sudo alias currently
profile.d OK
/etc/profile.d mode=755 owner=root:root
Relabeled /etc/profile.d/lab13-admin-aliases.sh from unconfined_u:object_r:user_tmp_t:s0 to ...
-rw-r--r--. 1 root root system_u:object_r:bin_t:s0 ... /etc/profile.d/lab13-admin-aliases.sh
ll is aliased to `ls -lhA --color=auto'
svc is aliased to `systemctl --no-pager status'
listen is aliased to `ss -tunap'
srv is aliased to `cd /srv'
ll is aliased to `ls -lhA --color=auto'
svc is aliased to `systemctl --no-pager status'
listen is aliased to `ss -tunap'
srv is aliased to `cd /srv'

─── T13-B demonstration: sudo + aliases ───
sudo: ll: command not found
sudo is aliased to `sudo '
total 28K
drwx------.  4 root root 4096 ... .
drwxr-xr-x. 19 root root 4096 ... ..
-rw-r--r--.  1 root root   18 ... .bash_logout
alias sudo='sudo '$
exit was: 0
```

> The last line `alias sudo='sudo '$` (from `cat -A`) shows the trailing space visually — note the space before `'$`. That space is what enables `sudo NAME` expansion.

### Switches

| Token | Meaning |
|---|---|
| `chmod 0644` | World-readable, owner-writable |
| `restorecon -v PATH` | Restore default SELinux context |
| `ls -lZ` | Long listing with SELinux context |
| `su - USER -c 'CMD'` | Run CMD as USER in a fresh login shell |
| `bash -lc 'CMD'` | Force login shell; reads /etc/profile and rc files |
| `alias sudo='sudo '` | Trailing-space trick — enables next-word alias expansion |
| `cat -A FILE` | Show invisible whitespace and line endings |

### Concept Card

| Concept | What it does |
|---|---|
| `/etc/profile.d/*.sh` | Canonical system-wide deployment for shell init |
| Mode `0644` for system files | World-readable, owner-writable — every user can source |
| `restorecon` for SELinux | Ensures the file gets the right context (`bin_t` for `/etc`) |
| Cross-user verification | `su - USER -c 'bash -lc "..."'` is the honest fleet-wide test |
| `cat -A` for invisible chars | Reveals trailing whitespace, tabs, line endings |
| **🪤 Trap Risk T13-B** | Forgetting the trailing space in `alias sudo='sudo '`. The space is the entire feature. |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| System-wide file deployed | `ls -lZ /etc/profile.d/lab13-admin-aliases.sh` | File mode + SELinux context |
| Aliases visible cross-user | `su - ec2-user -c 'bash -lc "type ll"'` (if user exists) | Fleet-wide test |
| Trailing space confirmed | `alias sudo \| cat -A \| grep "' \\\$"` | Visible whitespace check (escaping varies by shell) |
| File survives reboot | `stat -c '%y' /etc/profile.d/lab13-admin-aliases.sh` | Mtime; file is on root partition |

> **Reboot reasoning:** `/etc/profile.d/` is on the root partition, not tmpfs. The file survives reboot. Every new login shell re-sources it automatically — that is the whole reason `/etc/profile.d/` exists.

### Journal write

```bash
LAB=lab-13a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab13a/task2.txt "$JDIR/evidence.txt"
cp /etc/profile.d/lab13-admin-aliases.sh "$JDIR/profile.d-snapshot.sh"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    System-wide aliases via /etc/profile.d/ + sudo trailing-space trick
COMMANDS: /etc/profile.d/*.sh, restorecon, su - USER -c, bash -lc, alias sudo='sudo '
TRAPS:    T13-B rehearsed (demonstrated WITHOUT trick fails; WITH trick succeeds; cat -A confirms space)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-13b — Ansible blockinfile manages the same /etc/profile.d/ file
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup

```bash
rm -f /etc/profile.d/lab13-admin-aliases.sh
rm -rf /tmp/lab13a
test -f /etc/profile.d/lab13-admin-aliases.sh || echo "system-wide file removed"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Aliases not visible to other users | File mode wrong (must be 0644) or filename doesn't end `.sh` |
| Aliases visible only after re-login | Expected — `/etc/profile.d` is sourced on login |
| SELinux denies sourcing | `restorecon -v /etc/profile.d/FILE.sh` |
| `sudo ll` still says command not found | Trailing space is missing inside the quotes. Verify with `alias sudo \| cat -A`. |
| `su - ec2-user` fails | User doesn't exist on this host. The check `if id ec2-user` skips gracefully. |

> **STOP — paste the cross-user `type ll svc listen srv` output and the `cat -A` line showing the trailing space before moving to Lab 13b.**

---

## Lab 13a Checklist (2 tasks)

- [ ] Task 1 — Transient alias, `type` inspection, bypass with `\NAME`, persist in `~/.bashrc`, verify with `bash -ic`
- [ ] Task 2 — Deploy `/etc/profile.d/lab13-admin-aliases.sh`, cross-user verify, T13-B trailing-space trick

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 13b** — Aliases via Ansible | `ansible.builtin.blockinfile` manages the same `/etc/profile.d/` file declaratively |
| **Lab 13c** — Verifying Aliases | Auditor seat: `type` + cross-user shell + simulated reboot re-source |
| Lab 12 — Creating Nested Directories | `mkdir -p` underlies `/etc/profile.d/` if it ever needs to be created from scratch |
| Lab 11 — Safe Deletion | `unalias -a` and `sed -i '/marker/,/marker/d' ~/.bashrc` are the alias removals |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
