# lab-01a — stdout redirection — RHCSA

Hand-typed RHCSA muscle memory for the everyday stdout redirection
operators: `>`, `>>`, `<`, `|`, and `tee -a`. ("stdout" = *standard
output*, the normal text a command prints to your screen.) Built per the
rules in `cursor-adhd-lab-prompt.txt` (sections 0–20). Two tasks, no more.

This README is written to read like a book for someone who has never
touched these operators before. Every command block has a plain-English
"what we're about to do" line in front of it, and every single line of
syntax is explained one sentence at a time underneath. If a word looks
like jargon, it gets defined the first time it appears.

Task 1 is the canonical correct form — the safe, everyday way to write,
append, count, and log text. Task 2 is the contrast: the silent-overwrite
trap, the `set -o noclobber` safety net, and the `sudo -u` redirection
gotcha that catches everyone exactly once.

---

## LAB HEADER (confirm or correct before Task 1)

**In plain English:** This little block records the machine you're sitting
at, so we both agree on the environment before touching anything. Four of
the lines have `$(...)` in them, which means "run this and paste its
answer here" — the shell runs the command inside the parentheses and
substitutes the result.

```
ENV:   BAREMETAL
DISK:  /dev/sda
NIC:   ens3
SE:    $(getenforce 2>/dev/null || echo n/a)
OS:    $(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"')
TIME:  $(date -Is)
USER:  $(whoami)@$(hostname -s)

TRAPS THIS LAB: T41 T44
PRACTICE DIR:   /tmp — sandbox scratch space; cleared on reboot; safe to write without sudo
```

Line by line:

- `ENV: BAREMETAL` — Note that this is running on real hardware, not a
  virtual machine.
- `DISK: /dev/sda` — The name Linux gives the first disk; just a label
  here.
- `NIC: ens3` — The name of the network card; just a label here.
- `SE: $(getenforce 2>/dev/null || echo n/a)` — Ask SELinux (a security
  system) what mode it's in; `2>/dev/null` throws away any error message,
  and `||` means "or else" — so if the command fails, print `n/a`
  instead.
- `OS: $(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"')` —
  Find the human-readable OS name: `grep` pulls the matching line, the
  `|` (pipe) hands that line to `cut` which keeps only the part after the
  `=`, and `tr -d '"'` deletes the quote marks.
- `TIME: $(date -Is)` — Print the current date and time; `-Is` formats it
  in the tidy ISO standard down to the second.
- `USER: $(whoami)@$(hostname -s)` — Show who you are logged in as
  (`whoami`) and the short name of this machine (`hostname -s`, where
  `-s` means "short name only, no domain").
- `TRAPS THIS LAB: T41 T44` — The two known mistakes this lab trains you
  to avoid (persistence reasoning and orphan cleanup).
- `PRACTICE DIR: /tmp` — Where we'll do our scribbling; `/tmp` is wiped on
  reboot and doesn't need `sudo` (administrator powers) to write to.

Run the four `$()` substitutions in your shell to fill in the live
values, then paste the resolved block back so we agree on the
environment.

---

## LAB-WIDE SETUP (run once before Task 1; paste output)

**In plain English:** Before any task, we build a private little workspace:
a folder to play in, a throwaway group and user account that owns it, and
a note file describing the folder. We save a few names in variables first
so we never have to retype them. Run this whole block once.

```bash
export LAB_NUM=01
export LAB_SLUG=stdout-redirection
export SANDBOX=/tmp/labsandbox_${LAB_NUM}
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
# Never use USER= — bash reserves it; sudo -i resets it to root silently
export LAB_USER=labuser_${LAB_NUM}_${LAB_SLUG}
export LAB_USER_HOME=${SANDBOX}/home_${LAB_USER}

mkdir -p "${SANDBOX}" "${LAB_USER_HOME}"
getent group  "${GROUP}"    >/dev/null || groupadd "${GROUP}"
getent passwd "${LAB_USER}" >/dev/null || useradd \
    -d "${LAB_USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${LAB_USER}"
chown -R "${LAB_USER}:${GROUP}" "${SANDBOX}"
id    "${LAB_USER}"
ls -ld "${SANDBOX}" "${LAB_USER_HOME}"

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
/tmp is sandbox scratch space; cleared on reboot.
RHCSA labs use it because nothing here survives reboot and no sudo is needed to write.
EOF

echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

Line by line:

- `export LAB_NUM=01` — Save the number `01` so we can reuse it everywhere
  instead of retyping it. (`export` makes the variable visible to other
  commands you run.)
- `export LAB_SLUG=stdout-redirection` — Save a short text label for this
  topic the same way.
- `export SANDBOX=/tmp/labsandbox_${LAB_NUM}` — Build the path to our
  playground folder; `${LAB_NUM}` pastes in the `01` we saved above.
- `export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}` — Save the name of the
  throwaway group that will own our files.
- `# Never use USER= ...` — A comment (the `#` means "ignore this line")
  warning that `USER` is a name bash treats specially, so we avoid it.
- `export LAB_USER=labuser_${LAB_NUM}_${LAB_SLUG}` — Save the name of the
  throwaway user account for this lab.
- `export LAB_USER_HOME=${SANDBOX}/home_${LAB_USER}` — Save the path to
  that user's home folder, placed inside the sandbox.
- `mkdir -p "${SANDBOX}" "${LAB_USER_HOME}"` — Create both folders; `-p`
  means "don't error if it already exists, and make parent folders as
  needed."
- `getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"` — Check if
  the group exists; if it doesn't, create it. (`>/dev/null` = "hide normal
  output"; `||` = "or else, do the right side.")
- `getent passwd "${LAB_USER}" >/dev/null || useradd \` — Check if the
  user exists; if not, create it. The `\` at the end means "this command
  continues on the next line."
- `-d "${LAB_USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${LAB_USER}"` —
  The options for `useradd`: `-d` sets the home folder, `-M` means "don't
  actually create a home directory for me," `-s` sets the login shell to
  `/bin/bash`, and `-g` sets the user's main group.
- `chown -R "${LAB_USER}:${GROUP}" "${SANDBOX}"` — Hand ownership of the
  sandbox (and everything inside) to our user and group; `-R` means
  "recursively, apply to every file and subfolder too."
- `id "${LAB_USER}"` — Print the user's ID numbers and group memberships
  so we can confirm it was made correctly.
- `ls -ld "${SANDBOX}" "${LAB_USER_HOME}"` — List the two folders; `-l`
  means "long format with owner and permissions," and `-d` means "show
  the folder itself, not the files inside it."
- `cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'` — Start a *heredoc* (a
  way to type several lines of text straight into a file); everything
  until the matching `EOF` gets written into `THIS_DIRECTORY.txt`, and the
  quotes around `'EOF'` mean "write the text exactly, don't substitute
  variables."
- the two text lines — The actual contents of the note file.
- `EOF` — The end marker that closes the heredoc.
- `echo "Sandbox built by $(whoami) at $(date -Is)"` — Print a friendly
  confirmation, pasting in your username and the current time.
- `echo "exit was: $?"` — Print the *exit status* (the success/failure
  code the last command left behind; `0` means success, anything else
  means failure) of the previous line.

**New words in this step:**
- **stdout** — the normal text output a command prints to the screen.
- **persistence** — whether a file or account *survives a reboot* (stays
  around) or disappears.
- **heredoc** — a block of text typed inline that gets fed into a command
  or file, ending at a marker word like `EOF`.
- **exit status** — the number a command leaves behind to say if it
  worked (`0`) or failed (non-zero).

---

## TASK 1 of 2 — Canonical stdout redirection

**In plain English:** This task teaches the four safe, everyday moves:
write a file, add to it, count its lines, and log a line while still
seeing it on screen. Nothing here destroys data.

```
LAB:   lab-01a — stdout redirection
TASK:  1 of 2 — > and >> create and append cleanly
TRAPS: T44 (cleanup orphan audit, validated by Task 1 cleanup)
```

### Quiz warm-up (entry baseline — no previous task in this topic)

- **Q1:** After `false`, what does `$?` show?
- **Q2:** What do you think `>` does when you run `echo hi > file.txt`?

Type your answers. I confirm or correct, then we proceed.

---

### Step 1 of 2 — Write a file, append to it, then read it back

**In plain English:** We're going to create a brand-new text file with one
line, then add a second line to the bottom of it, then read the whole
thing back to prove both lines are there. This is the single most common
thing you'll ever do with redirection.

Run this:

```bash
echo "first line"  >  "${SANDBOX}/notes.txt"
echo "second line" >> "${SANDBOX}/notes.txt"
cat                   "${SANDBOX}/notes.txt"
echo "exit was: $?"
```

Before I explain — what do you think the difference between `>` and `>>`
is? (Type your guess or "unsure.")

**After you've answered, line by line:**

- `echo "first line" > "${SANDBOX}/notes.txt"` — Print `first line` but
  send it into the file instead of the screen; `>` *truncates* the file
  (empties it to zero bytes) and then writes, creating the file fresh if
  it didn't exist.
- `echo "second line" >> "${SANDBOX}/notes.txt"` — Print `second line` and
  *append* it (add to the bottom) of the same file; `>>` (two of them)
  means "append without erasing what's already there."
- `cat "${SANDBOX}/notes.txt"` — Read the whole file out to the screen so
  we can see both lines.
- `echo "exit was: $?"` — Print the exit status of `cat`; `0` means it
  read the file fine.

The key danger to feel right now: `>` erases first, `>>` keeps what's
there. Typing one `>` when you meant two silently wipes the file — that's
the classic stdout-redirection trap (we trigger it on purpose in Task 2).

You should see `first line`, `second line`, then `exit was: 0`.

**New words in this step:**
- **truncate** — to instantly empty a file down to zero bytes (what a
  single `>` does before it writes).

Paste your output.

---

### Step 2 of 2 — Count the lines, then log-and-show with `tee -a`

**In plain English:** First we'll count how many lines the file has using a
clean trick that prints just the number. Then we'll add a third line in a
special way that writes it to the file *and* shows it on screen at the same
time — the standard move for "log this but let me watch it too."

Run this:

```bash
wc -l < "${SANDBOX}/notes.txt"
echo "third line" | tee -a "${SANDBOX}/notes.txt"
echo "exit was: $?"
```

Before I explain — what do you think `< file` does, and what does the `|`
between `echo` and `tee` do? (Type your guess.)

**After you've answered, line by line:**

- `wc -l < "${SANDBOX}/notes.txt"` — Count the lines in the file; `wc`
  means "word count," `-l` tells it "count lines only," and `<` feeds the
  file in as if you'd typed it, so the output is just the bare number with
  no filename attached.
- `echo "third line" | tee -a "${SANDBOX}/notes.txt"` — Print `third line`,
  then `|` (the *pipe*, which hands one command's output to the next)
  sends it to `tee`, which writes it to the file AND echoes it back to
  your screen; `-a` means "append" (without `-a`, `tee` would erase the
  file first — the same trap as `>` vs `>>`).
- `echo "exit was: $?"` — Print the exit status of the `tee` command.

You should see `2` (the line count before we added the third line), then
`third line` printed on screen, then `exit was: 0`.

**New words in this step:**
- **pipe (`|`)** — a connector that feeds the output of the command on the
  left straight into the command on the right.
- **`tee`** — a tool that splits output two ways: into a file and onto the
  screen at the same time (named after a T-shaped pipe fitting).

Paste your output.

---

### Concept card (Task 1)

This table is your cheat sheet. The "what it does" column is the plain
meaning; the "exam trap" column is the mistake graders love to catch.

| Concept | What it does | Exam trap |
|---------|--------------|-----------|
| `>` | truncate-then-write stdout to file | silently destroys prior contents |
| `>>` | append stdout to file | one `>` instead of two = data loss |
| `<` | redirect file to stdin | `wc -l < f` prints just the number |
| `\|` | pipe stdout to next command | only stdout flows; stderr does not (Lab 02 territory) |
| `tee -a` | duplicate stdin to terminal AND file (append) | without `-a`, tee truncates |
| `wc -l` | count newline-terminated lines | unterminated final line is not counted |
| `$?` | exit status of previous command | non-zero = Section 8 blocker |
| `${SANDBOX}` | per-lab safe scratch dir under /tmp | use this, never `$HOME` or bare `/tmp` |

Drill mapping: every row above → `--category io`.

---

### Persistence check

**In plain English:** "Persistence" is just the question *would this file
still be here after a reboot?* We check where `/tmp` actually lives to
answer it.

```bash
findmnt /tmp
ls -ld "${SANDBOX}"
```

Line by line:

- `findmnt /tmp` — Show what kind of storage `/tmp` is mounted on,
  including a `FSTYPE` (filesystem type) column.
- `ls -ld "${SANDBOX}"` — Long-list the sandbox folder itself so we can
  see it exists right now.

Paste the output and read the `FSTYPE` column of `findmnt`:

- If FSTYPE is `tmpfs`, `/tmp` is RAM-backed → `notes.txt` is gone on
  reboot.
- If FSTYPE is something else (xfs / ext4), the file lives on disk but
  `systemd-tmpfiles` will clean `/tmp` on next boot anyway.

Either way the answer is: it does NOT survive. `/tmp` is the right home
for sandbox state precisely because of this. Storing real configuration
here is T41 in disguise.

---

### Journal write (run before cleanup)

**In plain English:** Before we tear the sandbox down, we write a small
"I finished this" record into a durable folder under `/root` (which *does*
survive reboot). This is your study log.

```bash
LAB=lab01
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cat > "$JDIR/done.txt" <<EOF
LAB:    lab-01a-stdout-redirection-rhcsa
TASK:   1 of 2 — > and >> create and append cleanly
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname -s)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    stdout redirection — > / >> / | / tee / wc / <
COMMANDS: echo, cat, wc -l, tee -a, findmnt, ls
TRAPS:    T44 (cleanup orphan audit, validated by next block)
MISSED:   [list any quiz question you got wrong, or "none"]
NEXT:     task2 — contrast: silent-overwrite trap + sudo -u LAB_USER + stat
EOF

echo "Journal written: $(ls -la $JDIR)"
echo "exit was: $?"
```

Line by line:

- `LAB=lab01` — Save a short label for which lab this is.
- `TASK=task1` — Save a short label for which task this is.
- `JDIR="/root/rhcsa_journal/${LAB}/${TASK}"` — Build the path to this
  task's journal folder under `/root`.
- `mkdir -p "$JDIR"` — Create that folder, making parents as needed and
  not erroring if it's already there.
- `cat > "$JDIR/done.txt" <<EOF` — Open a heredoc and write the completion
  record into `done.txt`; this `EOF` has no quotes, so `$(date -Is)` and
  the other `$(...)` *do* run and get pasted in.
- the `done.txt` lines — The actual record: which lab/task, the timestamp,
  who you are, and a COMPLETE status.
- `cat > "$JDIR/notes.txt" <<EOF` — Open another heredoc to write your
  study notes for this task into `notes.txt`.
- the `notes.txt` lines — Topic, the commands you practiced, the traps,
  any quiz misses, and what comes next.
- `echo "Journal written: $(ls -la $JDIR)"` — Confirm it worked by listing
  the journal folder (`ls -la` = long format including hidden files).
- `echo "exit was: $?"` — Print the exit status of that listing.

Paste output.

---

### Cleanup (Section 6 teardown — run at end of every task)

**In plain English:** Now we put everything back the way we found it: remove
any leftover containers, unmount anything we mounted, delete the lab user
and group, delete the sandbox, and then *audit* (double-check) that nothing
got left behind. A leftover account or folder is called an "orphan," and
leaving one is the T44 mistake.

```bash
set +e

podman ps -aq --filter "name=^${CTR}$" 2>/dev/null \
    | xargs -r podman rm -f >/dev/null 2>&1

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts \
    | tac | xargs -r -n1 umount -l 2>/dev/null

if vgs "${VG}" >/dev/null 2>&1; then
    lvremove -fy  "${VG}"          2>/dev/null
    vgremove -fy  "${VG}"          2>/dev/null
fi

losetup -j "${SANDBOX}/disk.img" 2>/dev/null \
    | cut -d: -f1 | xargs -r losetup -d 2>/dev/null

if getent passwd "${LAB_USER}" >/dev/null 2>&1; then
    userdel -r "${LAB_USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
    groupdel "${GROUP}"  2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── cleanup audit ──"
getent passwd "${LAB_USER}"  && echo "user remains (FAIL)"   || echo "user gone (OK)"
getent group  "${GROUP}"     && echo "group remains (FAIL)"  || echo "group gone (OK)"
test -d "${SANDBOX}"         && echo "sandbox remains (FAIL)" || echo "sandbox gone (OK)"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

Line by line:

- `set +e` — Turn OFF "stop on first error" so the cleanup keeps running
  even if one step has nothing to remove.
- `podman ps -aq --filter "name=^${CTR}$" ... | xargs -r podman rm -f ...`
  — List any container named like our lab container and force-remove it;
  `xargs -r` means "only run the removal if the list isn't empty," and the
  `>/dev/null 2>&1` hides all output.
- `awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l ...`
  — Find anything mounted under the sandbox and unmount it; `tac` reverses
  the list so nested mounts come off in the right order, and `umount -l`
  is a "lazy" unmount that detaches even if busy.
- `if vgs "${VG}" >/dev/null 2>&1; then` — If an LVM volume group from this
  lab exists, do the steps inside.
- `lvremove -fy "${VG}"` / `vgremove -fy "${VG}"` — Force-remove the
  logical volumes and then the volume group; `-fy` means "force, and
  answer yes to prompts."
- `losetup -j "${SANDBOX}/disk.img" ... | cut -d: -f1 | xargs -r losetup -d ...`
  — Find any loop device backed by our disk image and detach it (`-d`).
- `if getent passwd "${LAB_USER}" ...; then userdel -r "${LAB_USER}"` — If
  the lab user exists, delete it; `-r` also removes its home directory.
- `if getent group "${GROUP}" ...; then groupdel "${GROUP}"` — If the lab
  group exists, delete it.
- `rm -rf "${SANDBOX}"` — Delete the sandbox folder and everything in it;
  `-r` = recursive, `-f` = force (no prompts, no error if missing).
- `echo "── cleanup audit ──"` — Print a header for the verification lines.
- `getent passwd "${LAB_USER}" && echo "user remains (FAIL)" || echo "user gone (OK)"`
  — Check for the user again; if it's still found print FAIL, or else
  print OK (we *want* OK here, meaning it's gone).
- the group and sandbox audit lines — Same pass/fail check for the group
  and the folder; `test -d` asks "is this a directory that still exists?"
- `set -e` — Turn "stop on first error" back on for normal work.
- `echo "Cleanup complete ..."` / `echo "exit was: $?"` — Print a
  confirmation and the final exit status.

Paste the audit lines. Every row must say `(OK)`. Any `(FAIL)` is a
Section 8 mistake — fix it before continuing.

**STOP.** Task 2 is below. Do not look at it until you have pasted the two
step outputs, the persistence check, the journal write, and all three
audit `(OK)` rows.

---

## TASK 2 of 2 — Contrast: silent-overwrite trap, noclobber, and sudo redirection

**In plain English:** This task is the "feel the pain" half. We build a file
correctly, then *deliberately* destroy it with a single `>` so you see how
silent the damage is. Then we turn on a safety net (`noclobber`) and learn
the one `sudo` redirection gotcha that fools everybody once.

This task DELIBERATELY destroys data so you feel why `>` versus `>>`
matters. It also exposes the `sudo -u user cmd > file` gotcha that makes a
file end up root-owned even though you ran the command "as" the user.

```
LAB:   lab-01a — stdout redirection
TASK:  2 of 2 — silent-overwrite + noclobber + sudo redirection + stat
TRAPS: T41 (persistence reasoning), T44 (cleanup orphan audit)
```

### Quiz warm-up (from Task 1)

- **Q1:** What does `tee -a` do that plain `tee` does not?
- **Q2:** What does `<` do in `wc -l < file`?

Confirm or correct before we proceed.

---

### Prerequisite — re-run the lab-wide setup

The Task 1 cleanup tore down `${LAB_USER}`, `${GROUP}`, and `${SANDBOX}`.
Re-run the **LAB-WIDE SETUP** block at the top of this file before Step 1.
Paste the same `Sandbox built by ...` line as proof.

---

### Step 1 of 2 — Build it right, then break it on purpose

**In plain English:** First we build a clean three-line file the correct way
(one `>` to start fresh, then `>>` to add). Then we run a single `>` against
it and read it back to watch two of the three lines vanish without any
warning. This is the trap, demonstrated live.

Run this:

```bash
echo "alpha"   >  "${SANDBOX}/notes.txt"
echo "bravo"   >> "${SANDBOX}/notes.txt"
echo "charlie" >> "${SANDBOX}/notes.txt"
cat               "${SANDBOX}/notes.txt"
```

Before I explain — three of these lines used `>>`, the first used `>`. Why
does the first one HAVE to be `>` and not `>>`? (Type your guess.)

**After you've answered, line by line:**

- `echo "alpha" > "${SANDBOX}/notes.txt"` — Start the file fresh with
  `alpha`; the single `>` truncates first, guaranteeing no stale leftovers
  from an old run.
- `echo "bravo" >> "${SANDBOX}/notes.txt"` — Append `bravo` to the bottom
  without erasing `alpha`.
- `echo "charlie" >> "${SANDBOX}/notes.txt"` — Append `charlie` the same
  way.
- `cat "${SANDBOX}/notes.txt"` — Read the file back; you should see all
  three lines in order.

The first line *must* be `>`: if you used `>>` for line 1, you'd append
`alpha` onto whatever junk the file already held from a previous run.
"`>` first, then `>>`" is the canonical "build a file from scratch" idiom.

Now break it on purpose. This WILL destroy the file — that is the point:

```bash
echo "newest" > "${SANDBOX}/notes.txt"
cat              "${SANDBOX}/notes.txt"
```

Before I explain — predict what `cat` shows now. (Type your guess.)

**After you've answered, line by line:**

- `echo "newest" > "${SANDBOX}/notes.txt"` — A single `>` truncates the
  file to empty and writes only `newest`; `alpha`, `bravo`, and `charlie`
  are gone instantly.
- `cat "${SANDBOX}/notes.txt"` — Read it back to confirm the damage.

You see ONLY `newest`. There was no warning. There is no recycle bin. This
is the canonical "I meant `>>` and typed `>`" data-loss event. On a real
system this is how people wipe log files, configs, and
`~/.ssh/authorized_keys`.

Paste both outputs.

---

### Step 2 of 2 — Protect it (noclobber + `>|`), then the sudo ownership gotcha

**In plain English:** First we switch on a safety net called `noclobber` that
makes the shell *refuse* to overwrite an existing file with `>`, and we learn
the "I really mean it" override `>|`. Then we meet the famous `sudo`
redirection gotcha: running a command "as" another user but ending up with a
root-owned file, and the `| tee` trick that fixes it. We finish by auditing
ownership with `stat`.

Run this:

```bash
set -o noclobber
echo "this should fail" > "${SANDBOX}/notes.txt"
echo "exit was: $?"
```

Before I explain — what do you think `set -o noclobber` does? (Type your
guess.)

**After you've answered, line by line:**

- `set -o noclobber` — Turn on the shell safety setting that refuses to let
  `>` overwrite a file that already exists.
- `echo "this should fail" > "${SANDBOX}/notes.txt"` — Try to overwrite the
  existing file; the shell blocks it and the data is preserved.
- `echo "exit was: $?"` — Print the exit status; it's non-zero (usually
  `1`) because the overwrite was refused.

You should see `bash: ...notes.txt: cannot overwrite existing file` and
`exit was: 1`.

Now force the overwrite, for when you genuinely mean it:

```bash
echo "intentional overwrite" >| "${SANDBOX}/notes.txt"
cat                             "${SANDBOX}/notes.txt"
set +o noclobber
```

Line by line:

- `echo "intentional overwrite" >| "${SANDBOX}/notes.txt"` — `>|` is the
  "force overwrite even with noclobber on" operator; use it only when you
  truly want to truncate.
- `cat "${SANDBOX}/notes.txt"` — Read it back to confirm the forced write
  took.
- `set +o noclobber` — Turn the protection back off (the `+o` undoes the
  `-o`).

Now the `sudo` gotcha. First, the naive way that does NOT do what you'd
expect:

```bash
sudo -u "${LAB_USER}" echo "owned by labuser?" > "${SANDBOX}/labuser_note.txt"
stat -c '%U:%G %a %n' "${SANDBOX}/labuser_note.txt"
```

Before I explain — predict who ends up owning `labuser_note.txt`. (Type
your guess.)

**After you've answered, line by line:**

- `sudo -u "${LAB_USER}" echo "owned by labuser?" > "${SANDBOX}/labuser_note.txt"`
  — `sudo -u USER` means "run this command as USER," but the shell sets up
  the `>` redirection in *your* (root) shell *before* `sudo` even runs — so
  root opens and owns the file, and only then does `echo` run as the lab
  user and feed its text into the already-root-owned file.
- `stat -c '%U:%G %a %n' "${SANDBOX}/labuser_note.txt"` — Audit the file's
  owner; `stat` reads file metadata and `-c '%U:%G %a %n'` prints only the
  user owner, group owner, permission mode in octal, and the filename.

The owner is `root`, NOT `${LAB_USER}` — surprising but logical once you
know the shell handles `>` first.

Now the right way — let the privileged tool do the writing:

```bash
echo "owned by labuser" | sudo -u "${LAB_USER}" tee "${SANDBOX}/labuser_note.txt" >/dev/null
stat -c '%U:%G %a %n' "${SANDBOX}/labuser_note.txt"
```

Line by line:

- `echo "owned by labuser" | sudo -u "${LAB_USER}" tee "${SANDBOX}/labuser_note.txt" >/dev/null`
  — Pipe the text to `tee` *running as the lab user*, so `tee` opens the
  file with the lab user's identity and the lab user owns the bytes;
  `>/dev/null` throws away tee's screen echo because we don't need to see
  it.
- `stat -c '%U:%G %a %n' "${SANDBOX}/labuser_note.txt"` — Audit ownership
  again to confirm the fix.

Finally, a combined audit of both files:

```bash
stat -c '%U:%G %a %n' "${SANDBOX}/labuser_note.txt" \
                      "${SANDBOX}/notes.txt"
ls -lZ "${SANDBOX}/" 2>/dev/null || ls -l "${SANDBOX}/"
echo "exit was: $?"
```

Line by line:

- `stat -c '%U:%G %a %n' ... labuser_note.txt notes.txt` — Print the
  owner/group/mode/name for both files at once (the `\` just continues the
  command on the next line).
- `ls -lZ "${SANDBOX}/" 2>/dev/null || ls -l "${SANDBOX}/"` — Long-list the
  folder with the SELinux security context column (`-Z`); if `-Z` isn't
  supported, the `||` ("or else") falls back to a plain `ls -l`.
- `echo "exit was: $?"` — Print the final exit status.

The first `stat` should show `root:root`, the second should show
`labuser_01_stdout-redirection:labgrp_01_stdout-redirection`.

**New words in this step:**
- **noclobber** — a shell setting that blocks `>` from overwriting an
  existing file ("clobber" = overwrite).
- **`stat`** — a tool that prints a file's metadata (owner, group,
  permissions, timestamps).

Paste all output.

---

### Concept card (Task 2 contrast — adds to Task 1's card)

| Concept | What it does | Exam trap |
|---------|--------------|-----------|
| `>` then `>>` | canonical "build from scratch" idiom | using `>>` first appends to stale data |
| accidental `>` | silently truncates | data-loss event, no warning, no undo |
| `set -o noclobber` | refuse `>` on existing files | OFF by default — has to be enabled per shell |
| `>\|` | force overwrite under noclobber | only meaningful when noclobber is on |
| `sudo -u USER cmd > file` | redirection runs in the OUTER shell | file ends up root-owned, not USER-owned |
| `\| sudo -u USER tee file` | redirection runs as USER | file ends up USER-owned (correct) |
| `stat -c '%U:%G %a %n'` | one-line audit of ownership and mode | the RHCSA-canonical inspection format |
| `${LAB_USER}` sandbox identity | per-lab user, dies on cleanup | never use bash's `$USER` for this |

Drill mapping: every row above → `--category io`.

---

### Persistence check

**In plain English:** Same reboot question as before, but now there are two
things to reason about: the file (volatile) and the lab *user account*
(which lives in a real file on disk and would survive). That difference is
exactly why cleanup is mandatory.

```bash
findmnt /tmp
getent passwd "${LAB_USER}"
```

Line by line:

- `findmnt /tmp` — Show what `/tmp` is mounted on; same reading as Task 1,
  so the file is gone on reboot either way.
- `getent passwd "${LAB_USER}"` — Look the lab user up in the account
  database; if it prints a line, the user really exists on disk.

Reading:

- `findmnt /tmp` — tmpfs or filesystem-with-cleanup; either way the file is
  gone on reboot.
- `getent passwd ${LAB_USER}` — the user IS in `/etc/passwd` (a real file
  on disk), so the user account WOULD survive reboot. That is exactly why
  the cleanup block at the end of every task is mandatory: T44 = leaving an
  orphan `${LAB_USER}` on the box, which the next lab inherits. The
  cleanup-audit `(OK)`/`(FAIL)` rows are the only proof.

**New words in this step:**
- **orphan** — a leftover user, group, or folder that cleanup forgot to
  remove.

---

### Journal write (run before cleanup)

**In plain English:** Same study-log routine as Task 1, recording what you
practiced in Task 2 into the durable `/root` journal.

```bash
LAB=lab01
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cat > "$JDIR/done.txt" <<EOF
LAB:    lab-01a-stdout-redirection-rhcsa
TASK:   2 of 2 — silent-overwrite + noclobber + sudo redirection + stat
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname -s)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    stdout redirection traps — silent overwrite, noclobber, sudo redirection
COMMANDS: echo, cat, set -o noclobber, >|, sudo -u, tee, stat, ls -lZ
TRAPS:    T41 (persistence — /tmp volatile but ${LAB_USER} survives)
          T44 (cleanup orphan ${LAB_USER}/${GROUP} audit)
MISSED:   [list any quiz question or step you got wrong, or "none"]
NEXT:     lab-01b-stdout-redirection-trapdrill (Section 18 boundary lab)
EOF

echo "Journal written: $(ls -la $JDIR)"
echo "exit was: $?"
```

Line by line:

- `LAB=lab01` / `TASK=task2` — Save short labels for this lab and task.
- `JDIR="/root/rhcsa_journal/${LAB}/${TASK}"` — Build the journal folder
  path for Task 2.
- `mkdir -p "$JDIR"` — Create it, making parents as needed.
- `cat > "$JDIR/done.txt" <<EOF` plus its lines — Write the completion
  record (the unquoted `EOF` lets `$(date -Is)` and friends run).
- `cat > "$JDIR/notes.txt" <<EOF` plus its lines — Write your Task 2 study
  notes, including the traps and what's next.
- `echo "Journal written: $(ls -la $JDIR)"` — Confirm by listing the
  folder.
- `echo "exit was: $?"` — Print the exit status.

Paste output.

---

### Cleanup (Section 6 teardown — final, full audit)

**In plain English:** Same teardown-and-audit as Task 1. Tear it all down and
confirm every `(OK)`. No orphans allowed.

```bash
set +e

podman ps -aq --filter "name=^${CTR}$" 2>/dev/null \
    | xargs -r podman rm -f >/dev/null 2>&1

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts \
    | tac | xargs -r -n1 umount -l 2>/dev/null

if vgs "${VG}" >/dev/null 2>&1; then
    lvremove -fy  "${VG}"          2>/dev/null
    vgremove -fy  "${VG}"          2>/dev/null
fi

losetup -j "${SANDBOX}/disk.img" 2>/dev/null \
    | cut -d: -f1 | xargs -r losetup -d 2>/dev/null

if getent passwd "${LAB_USER}" >/dev/null 2>&1; then
    userdel -r "${LAB_USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
    groupdel "${GROUP}"  2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── cleanup audit ──"
getent passwd "${LAB_USER}"  && echo "user remains (FAIL)"   || echo "user gone (OK)"
getent group  "${GROUP}"     && echo "group remains (FAIL)"  || echo "group gone (OK)"
test -d "${SANDBOX}"         && echo "sandbox remains (FAIL)" || echo "sandbox gone (OK)"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

Line by line: identical to the Task 1 cleanup above — `set +e` disables
stop-on-error, the middle block removes any container/mount/LVM/loop
device/user/group and then `rm -rf` deletes the sandbox, the three audit
lines verify each thing is gone (we want `(OK)`), and `set -e` re-enables
stop-on-error before the final confirmation.

Paste the audit lines. Every row must say `(OK)`.

---

### Drill (run AFTER cleanup audit shows all OK)

**In plain English:** Run the practice quiz for this category to lock the
muscle memory in.

```bash
python3 ~/scripts/rhcsa_drill.py --category io
```

- `python3 ~/scripts/rhcsa_drill.py --category io` — Run the drill script,
  limited to the input/output (`io`) question category.

Paste your score. If <80%, drill `--category io` again before starting
lab-01b. Per Section 20, this score gate is mandatory.

---

### Rotation tracker update (last step of the lab)

**In plain English:** We keep a tiny file noting which practice directory we
just used, so the next lab knows to rotate to a different one.

```bash
echo "last_used=01" > /root/rhcsa_journal/dir_rotation.txt
cat                  /root/rhcsa_journal/dir_rotation.txt
```

- `echo "last_used=01" > /root/rhcsa_journal/dir_rotation.txt` — Write the
  marker `last_used=01` into the rotation tracker file (overwriting it).
- `cat /root/rhcsa_journal/dir_rotation.txt` — Read it back to confirm.

Next lab's practice directory will be `/etc` (rotation slot 02).

**STOP — lab-01a complete.** Begin lab-01b only after the drill score is
pasted. lab-01b is a TRAP DRILL LAB per Section 18 of the prompt: Task 1 is
a wrong-way demo of the primary stdout-redirection trap, Task 2 is the
`ansible.builtin.shell:` boundary statement.
