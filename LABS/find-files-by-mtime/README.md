# Lab: Find Files by Modification Time and Act on Them

**Series:** linux-ops-mastery — RHCSA File & Search Operations
**Subjects covered:** `find` mental model, mtime / atime / ctime trio, `-mtime` numeric arithmetic (`+N`, `-N`, `N`), `-newer` reference files, `-printf` formatting, `-exec` vs xargs, copying matches with `cp -t`, archiving with `tar --files-from`, `stat` for verification
**Career arcs covered:** RHCSA (Find Files objective — guaranteed exam question), RHCE (Ansible `ansible.builtin.find` module + when-filters), SRE (log rotation + retention scripts), DevOps (CI cache pruning), Forensics (timeline reconstruction)
**Prerequisite:** Comfort with `ls -l`, basic shell redirection, the difference between an absolute path and a relative path
**Time Estimate:** 30 to 50 minutes
**Difficulty arc:** Task 1 foundation · 2–4 the `find -mtime` pipeline · 5 the action step (`-exec` / copy / archive) · 6 RHCSA exam-realistic capstone

---

## Objective

Build the **time-anchored `find`** muscle memory so you can answer any RHCSA "find files modified in the last N days" question in one line. By the end of this lab you can take a sprawling directory tree and produce an exact list — or an archive — of every file whose mtime falls in any window you choose.

The capstone is the **RHCSA sample exam task**: *"Find every file under `/etc` modified in the last 7 days and copy them, preserving directory structure, into `/root/recent-etc`."*

> **Lab safety note:** This lab works on a self-contained sandbox at `/root/find-lab` populated with files whose timestamps we set ourselves. Once the muscle memory is built, the exact same commands run unchanged against `/etc`, `/var/log`, or `/home`.

---

## Concept: `find` Is a Stream Processor for Filesystem Metadata

`find` does not, despite its name, "search" in the way `grep` or `locate` do. It walks a directory tree, and for every entry it visits it asks a series of **tests** ("is this a regular file?", "was it modified in the last week?", "is it bigger than 10 MB?"). For every entry that passes all the tests, it performs an **action** (`-print` by default, but optionally `-exec`, `-delete`, `-printf`, etc.).

```
   ┌─────────────────────────────────────────────────────────────┐
   │  find  STARTING-PATH(S)   [GLOBAL OPTIONS]  TESTS  ACTIONS  │
   │        └──────┬──────┘    └──────┬──────┘  └─┬─┘  └───┬───┘ │
   │               │                  │           │        │     │
   │     where to walk            -maxdepth   -mtime    -print   │
   │     (e.g. /etc)              -xdev       -size     -exec    │
   │                              -mindepth   -type     -delete  │
   │                                          -newer    -printf  │
   │                                          -name              │
   └─────────────────────────────────────────────────────────────┘
```

Three things to remember about `find`:

- **Order matters.** Tests are evaluated left to right and short-circuit. Put the cheap tests (like `-type f`) before the expensive ones (like `-exec grep`).
- **Defaults are sane.** With no action specified, `find` prints matches one per line. That stream is shell-pipeline-ready.
- **The mtime arithmetic is the surprise.** `-mtime N` doesn't mean "exactly N days ago." It means "in the 24-hour window centered on N days ago," and `+N` means "more than," `-N` means "less than." We'll drill this until the off-by-one bugs stop happening.

> **Why this matters:** The exam phrasing is almost always *"find files modified in the last 7 days under /etc"*. The correct answer is `find /etc -mtime -7` — but the off-by-one trap (`-7` vs `7` vs `+7`) is exactly what trips up under-rehearsed candidates.

---

## 📜 Why `find` Exists — The Story

`find` is older than most of the languages people learn it with. Dennis Ritchie's team shipped it in **Version 1 Unix (1971)**, three years before `grep`. The reason it predates almost every other shell tool is that early Unix needed a way to recurse a directory tree and *do something* with every file — back up a project, clean tmp, audit permissions — and there was no other primitive that did it.

### The pain `find` was invented to solve

- **Recursion was hard.** Pre-`find`, you wrote tree-walking by hand in C for every job. `find` factored recursion into one program everyone could use.
- **Timeline questions are everywhere.** "What changed last night?" "Which files haven't been touched in 90 days?" "Show me everything older than the kernel rebuild." Without `-mtime` / `-atime` / `-ctime`, every one of these requires a custom script.
- **Combining tests is a graph problem.** "Files bigger than 1 GB *and* older than 30 days *but not* in `/var/log`" is an expression tree, and `find`'s test-combinator syntax (`-a`, `-o`, `!`, parentheses) is exactly that.

### The killer feature most beginners miss: `-printf` and `-newer`

- **`-printf "%T+ %p\n"`** prints a sortable ISO-ish timestamp followed by the path. Pipe that through `sort` and you have a free filesystem timeline.
- **`-newer REFFILE`** finds everything modified after the reference file's mtime. Touch a marker file at job start, run the job, then `find /target -newer /tmp/marker` gives you exactly what changed. This is the heart of many backup and CI-incremental strategies.

### Why exam-day still drills the basics

RHCSA leans on `-mtime` and `-name` because those are 80% of the daily uses. Master those two and `-exec` for the action half of the command. Snapshots, `-printf`, and `-newer` come later — but they're worth knowing because every senior admin uses them weekly.

> **The point of the story:** Every "what changed?" question in ops, every retention policy, every audit, eventually becomes a `find -mtime` one-liner. Get the off-by-one trio (`+N`, `-N`, `N`) into your fingers and you've bought yourself a lifetime of fast answers.

---

## 👪 The `find -mtime` Family — Who Lives There

`find` has three time tests and three "in units of minutes" cousins.

### The three timestamps every file carries

| Stamp | Updated when | `find` flag | `stat` field |
|---|---|---|---|
| **mtime** (modify) | The file's **contents** change | `-mtime` | `Modify:` |
| **atime** (access) | The file's contents are **read** | `-atime` | `Access:` |
| **ctime** (status change) | The **inode metadata** changes (permissions, owner, link count) | `-ctime` | `Change:` |

`mtime` is by far the most useful — and the only one the RHCSA usually tests. `atime` is unreliable on modern systems because most filesystems mount with `relatime` or `noatime` to avoid the write storm. `ctime` is the forensics-level test: even renaming or `chmod`-ing a file bumps it.

### The numeric syntax — the part that trips people up

| Spelling | Means | Equivalent in words |
|---|---|---|
| `-mtime N` | Exactly N days ago | The 24-hour window from N×24 to (N+1)×24 hours back |
| `-mtime +N` | More than N days ago | Older than N × 24 hours |
| `-mtime -N` | Less than N days ago | Newer than N × 24 hours (= "in the last N days") |
| `-mmin N` | Same idea, in **minutes** | `+N`, `-N`, `N` all work |
| `-newer FILE` | Modified after FILE's mtime | Reference-file form — no day boundaries |

> **The mental rule:** Think of `-mtime` as comparing against a number line that runs from "now" backward. `+N` is "to the *left* of N days ago" (older). `-N` is "to the *right* of N days ago" (newer). `N` with no sign is "the day-boundary slot itself."

### The action side

| Action | Behavior | Use case |
|---|---|---|
| `-print` (default) | Prints matching path, one per line | Default; pipeline-ready |
| `-printf 'FMT'` | Like `printf` for find — supports `%p` (path), `%T+` (mtime), `%s` (size), `%u` (owner) | Custom report formats |
| `-exec CMD {} \;` | Run CMD once per match. `{}` is the path. **Quote the path properly.** | One-off per-file action |
| `-exec CMD {} +` | Run CMD with *many* matches at once (like xargs) | Efficient bulk action |
| `-delete` | Unlink each match. **Order-sensitive — must come last.** | Cleanup. *Always* dry-run with `-print` first. |
| `\| xargs CMD` | Same idea via pipe (older idiom) | When you need to combine with non-find pipelines |

### By common combination

| Pattern | What it answers |
|---|---|
| `find PATH -type f -mtime -7` | Files modified in the last week |
| `find PATH -type f -mtime +30 -delete` | Cleanup: delete anything older than 30 days |
| `find PATH -newer /tmp/marker` | Everything that changed since the marker was created |
| `find PATH -mmin -15` | Files modified in the last 15 minutes (handy mid-deploy) |
| `find PATH -mtime -7 -printf '%T+ %p\n' \| sort` | A timeline of recent changes |

> **The point of the family tree:** Every "find by time" question on the exam reduces to *"which sign on `-mtime`?"* and *"do I need an action other than `-print`?"* If you can answer those two, you're done.

---

## 🔬 The Anatomy of a `find -mtime` Command — In One Diagram

```
$ find /etc -type f -mtime -7 -printf '%T+ %p\n'
       └─┬─┘ └───┬──┘ └────┬───┘ └─────┬──────┘
         │       │         │           │
         │       │         │           └─ Action: print "<ISO mtime> <path>", one per line
         │       │         └─ Test 2: mtime is **less than** 7 days ago
         │       │             (newer than 7×24h back; sign is the trap)
         │       └─ Test 1: only regular files (skip dirs, symlinks, sockets)
         └─ Starting path: walk this tree depth-first
```

> **Reading rule:** Walk the command left to right. Anything before the first test is a starting path or a global option. Anything after is tests-then-actions, evaluated in order. If a `find` command doesn't behave the way you expected, the bug is almost always in the *order*.

---

## 📚 `find` Quick Reference

| Task | Command | Notes |
|---|---|---|
| Files modified in the last week | `find /etc -type f -mtime -7` | `-7` = "newer than 7 days" |
| Files modified more than 30 days ago | `find /var/log -type f -mtime +30` | `+30` = "older than 30 days" |
| Files modified in the last 15 minutes | `find /etc -mmin -15` | Minute resolution |
| Files newer than a marker | `find /etc -newer /tmp/marker` | Build the marker with `touch -d '2026-05-15 00:00' /tmp/marker` |
| Print mtime + path, timeline-sorted | `find /etc -mtime -7 -printf '%T+ %p\n' \| sort` | `%T+` = ISO timestamp |
| Copy matches preserving paths | `find /etc -mtime -7 -type f -exec cp --parents {} /root/dst \;` | `--parents` keeps the relative path |
| Archive matches into a tar | `find /etc -mtime -7 -type f -print0 \| tar --null --files-from=- -czf out.tgz` | NUL-safe pipeline |
| Delete matches older than 90 days | `find /tmp -type f -mtime +90 -delete` | *Always* dry-run with `-print` first |
| Count matches | `find /etc -type f -mtime -7 \| wc -l` | One line per match |
| Restrict to top level only | `find /etc -maxdepth 1 -mtime -7` | No recursion below depth 1 |
| Stay on one filesystem | `find / -xdev -mtime -1` | Don't cross into `/proc`, `/mnt`, etc. |

> **Rule one of `find`:** Always `-print` first, then change the action. A `find -delete` you didn't dry-run is a career-shortening event.

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | "Find files modified in the last N days and copy/archive them" is a near-guaranteed Search & Locate objective. |
| **RHCE candidate** | `ansible.builtin.find` exposes the same arguments (`age`, `age_stamp`, `recurse`). Knowing the CLI maps perfectly. |
| **SRE / Platform** | Log retention scripts, "what changed in the last incident window?" queries, and CI cache pruning all live here. |
| **DevOps** | Build-cache eviction, Dockerfile `find -delete` cleanup steps, and image-scan exclusion lists. |
| **Forensics / Security** | Timeline reconstruction after a breach: `find / -newer /tmp/last-known-good -ls` is the canonical first move. |

---

## 🔧 The 6 Tasks

> Each task is structured for maximum understanding. After the **Purpose** and the code, every task includes:
>
> - **Human-Readable Breakdown** — conversational walkthrough.
> - **Reading it left to right** — token-by-token gloss.
> - **The story** — the *why* behind the pattern.
> - **Analogy** — a one-line metaphor.
> - **Expected output** — exactly what you should see.
> - **Switches / Output decoded / Troubleshoot** — three small reference tables.

---

### Task 1 — Build a sandbox with files of known mtimes

**Purpose:** Construct a deterministic test bed so we can verify every later command against files whose ages we set on purpose.

**Command block:**

```bash
sudo -i
mkdir -p /root/find-lab/{recent,medium,ancient}
cd /root/find-lab

touch -d "$(date -d 'today 09:00')"          recent/today.log
touch -d "$(date -d '2 days ago 09:00')"     recent/two-days.log
touch -d "$(date -d '6 days ago 09:00')"     recent/six-days.log
touch -d "$(date -d '10 days ago 09:00')"    medium/ten-days.log
touch -d "$(date -d '45 days ago 09:00')"    medium/fortyfive-days.log
touch -d "$(date -d '120 days ago 09:00')"   ancient/four-months.log
touch -d "$(date -d '400 days ago 09:00')"   ancient/over-a-year.log

ls -lR
```

**Human-Readable Breakdown:**
> "Become root. Make three subdirectories — `recent`, `medium`, `ancient` — then plant seven empty files into them with explicit modification times spanning today, two days ago, six days ago, ten days ago, forty-five days ago, four months ago, and over a year ago. Every later test in this lab will use this exact tree, so we know which files *should* match every `-mtime` query."

**Reading it left to right:**
- `sudo -i` → "interactive root login shell — `touch -d` needs to set mtimes; root avoids permission quirks."
- `mkdir -p /root/find-lab/{...}` → "brace expansion makes three sibling subdirs in one syscall; `-p` makes the parent at the same time."
- `touch -d "$(date -d 'N days ago 09:00')" FILE` → "set the file's mtime to that absolute moment. `date -d` parses human-friendly relative times into a date string `touch -d` accepts."
- `ls -lR` → "long, recursive listing — confirms each file's timestamp before we test."

**The story:** Real systems don't hand you a clean test bed; their files have whatever mtimes ops gave them. For practice, *build* the test bed yourself with `touch -d`. The `date -d 'N days ago'` idiom is one of the most useful shell tricks in existence — you can compose any human relative time (`'last Friday'`, `'3 weeks ago'`, `'2025-11-01 14:30'`) and `touch -d` will set the file's mtime to exactly that. Get this trick into your muscle memory and every "schedule something for N days from now" problem gets easier too.

**Analogy:** Setting clocks to known times before testing a watch repair. You can't tell if the watch is accurate against an unknown reference.

**Expected output:**

```
/root/find-lab:
total 0
drwxr-xr-x. 2 root root 46 May 22 09:00 ancient
drwxr-xr-x. 2 root root 25 May 22 09:00 medium
drwxr-xr-x. 2 root root 64 May 22 09:00 recent

/root/find-lab/ancient:
total 0
-rw-r--r--. 1 root root 0 Jan 22 09:00 four-months.log
-rw-r--r--. 1 root root 0 Apr 18 2025 over-a-year.log

/root/find-lab/medium:
total 0
-rw-r--r--. 1 root root 0 Apr  7 09:00 fortyfive-days.log
-rw-r--r--. 1 root root 0 May 12 09:00 ten-days.log

/root/find-lab/recent:
total 0
-rw-r--r--. 1 root root 0 May 16 09:00 six-days.log
-rw-r--r--. 1 root root 0 May 20 09:00 two-days.log
-rw-r--r--. 1 root root 0 May 22 09:00 today.log
```

**Switches table:**

| Token | Meaning |
|---|---|
| `mkdir -p` | Create directory and missing parents; no error if exists |
| `{a,b,c}` | Brace expansion — one command, three dirs |
| `touch -d STR` | Set mtime to the moment parsed from STR |
| `$(date -d 'N days ago HH:MM')` | Generate an absolute date string from a relative spec |
| `ls -lR` | Long format, recursive |

**Output decoded table:**

| Field | Meaning |
|---|---|
| File year missing on recent rows | `ls` hides the year when the file is in the current year (display quirk only) |
| `over-a-year.log` shows `2025` | mtime crossed a year boundary, so `ls` shows the year instead of `HH:MM` |
| Permissions `-rw-r--r--` | Default `umask 022` from root |

**Troubleshoot table:**

| Symptom | Fix |
|---|---|
| `touch: invalid date format` | Old `coreutils`; use `touch -t YYYYMMDDhhmm FILE` instead |
| All mtimes show today's date | The `$(...)` substitution didn't run — check for stray quotes or backticks |
| `mkdir: cannot create directory` | Not root, or `/root` doesn't exist (you're on the wrong account) |

---

### Task 2 — Inspect timestamps with `stat` and `ls --time=mtime`

**Purpose:** Before filtering by time, prove you can *read* the time. `stat` is the ground truth; `ls` is the human view.

**Command block:**

```bash
stat recent/today.log recent/six-days.log ancient/over-a-year.log
ls -l --time=mtime --full-time recent/ medium/ ancient/
find /root/find-lab -type f -printf '%T+  %p\n' | sort
```

**Human-Readable Breakdown:**
> "Hey `stat`, show me the inode details — including all three timestamps — for three sample files chosen from each age bucket. Then ask `ls` for a long listing with full timestamps (down to nanoseconds) so I can read mtimes side-by-side with file names. Finally use `find -printf` to produce a sortable `<mtime> <path>` listing of *every* file in the lab and pipe through `sort` to get a chronological timeline."

**Reading it left to right:**
- `stat FILE1 FILE2 FILE3` → "show inode info — size, blocks, permissions, atime/mtime/ctime — for each path."
- `ls -l --time=mtime --full-time DIR/` → "long format; pick mtime as the sort/display time (the default); `--full-time` swaps the abbreviated `May 16 09:00` for `2026-05-16 09:00:00.000000000 -0400`."
- `find /root/find-lab -type f -printf '%T+  %p\n'` → "for every regular file under the lab, print *just* `<mtime> <path>`."
- `%T+` → "ISO-ish mtime in `YYYY-MM-DD+HH:MM:SS.NNNNNNNNN` format — sortable as plain text."
- `| sort` → "sort ASCII-ascending, which because of `%T+`'s format is also chronological."

**The story:** `stat` is unambiguous; `ls` is a UI. When you're debugging a `-mtime` query that's returning the wrong files, *always drop back to `stat`* — it shows the timestamp to the nanosecond, so you'll see immediately when an mtime is on the wrong side of a 24-hour boundary. The `find -printf '%T+ %p\n' | sort` idiom is a free filesystem timeline; it's worth committing to muscle memory because it answers *"what's been changing here lately?"* in one line.

**Analogy:** Reading a stopwatch (`stat`) versus reading a wall clock (`ls`). The wall clock is friendlier; the stopwatch is the truth.

**Expected output:**

```
  File: recent/today.log
  Size: 0           Blocks: 0          IO Block: 4096   regular empty file
Device: 253,0       Inode: 17385237    Links: 1
Access: 2026-05-22 09:00:00.000000000 -0400
Modify: 2026-05-22 09:00:00.000000000 -0400
Change: 2026-05-22 18:24:11.142000000 -0400
 Birth: 2026-05-22 18:24:11.142000000 -0400
…
-rw-r--r--. 1 root root 0 2026-04-07 09:00:00.000000000 -0400 fortyfive-days.log
-rw-r--r--. 1 root root 0 2026-05-12 09:00:00.000000000 -0400 ten-days.log
…
2025-04-18+09:00:00.0000000000  /root/find-lab/ancient/over-a-year.log
2026-01-22+09:00:00.0000000000  /root/find-lab/ancient/four-months.log
2026-04-07+09:00:00.0000000000  /root/find-lab/medium/fortyfive-days.log
2026-05-12+09:00:00.0000000000  /root/find-lab/medium/ten-days.log
2026-05-16+09:00:00.0000000000  /root/find-lab/recent/six-days.log
2026-05-20+09:00:00.0000000000  /root/find-lab/recent/two-days.log
2026-05-22+09:00:00.0000000000  /root/find-lab/recent/today.log
```

**Switches table:**

| Token | Meaning |
|---|---|
| `stat FILE` | Verbose inode info |
| `ls --time=mtime` | Use mtime for display/sort (default) |
| `ls --full-time` | Nanosecond timestamps, full year, timezone |
| `find -printf '%T+  %p\n'` | Custom output: `<ISO mtime> <path>` |
| `\| sort` | ASCII-ascending; works as chronological for `%T+` strings |

**Output decoded table:**

| Field | Meaning |
|---|---|
| `Access:` line | atime — when the file's contents were last read |
| `Modify:` line | **mtime** — what `-mtime` filters on |
| `Change:` line | ctime — when the inode metadata last changed (file creation here) |
| `Birth:` line | Creation time (only on filesystems that record it — most modern ones do) |
| Sorted timeline | Oldest first; the lab's seven files in chronological order |

**Troubleshoot table:**

| Symptom | Fix |
|---|---|
| `stat: cannot stat` | Wrong path or you're not root |
| `--time-style` errors on older `ls` | Use `ls -l` plain; resort to `stat` for nanosecond precision |
| Sort order looks scrambled | The `%T+` format is exact; if it's wrong, you have files outside the lab — re-check the path |

---

### Task 3 — Find files modified in the last 7 days (`-mtime -7`)

**Purpose:** The headline RHCSA pattern. Drill it until the *minus sign* is automatic.

**Command block:**

```bash
find /root/find-lab -type f -mtime -7
find /root/find-lab -type f -mtime -7 -printf '%T+  %p\n' | sort
find /root/find-lab -type f -mtime -7 | wc -l
```

**Human-Readable Breakdown:**
> "Hey `find`, walk `/root/find-lab` and print every regular file whose mtime is **less than** seven days ago — that is, anything modified in the last week. Then run the same query but with a sortable `<mtime>  <path>` output so I can eyeball the timeline. Finally count the matches so I have a number I can sanity-check against the sandbox."

**Reading it left to right:**
- `find /root/find-lab` → "starting path — walk this tree (and only this tree)."
- `-type f` → "test: keep only regular files (skip dirs, symlinks)."
- `-mtime -7` → "test: keep only files whose mtime is **less than** 7 days back from now. **The minus sign is the trap. `-7` ≠ `7`.**"
- `-printf '%T+  %p\n'` → "action: print `<ISO mtime>  <path>` for each match."
- `\| sort` → "chronological because `%T+` is ASCII-sortable."
- `\| wc -l` → "line count = match count."

**The story:** Memorize the **sign rule**: minus means "newer than," plus means "older than," bare number means "exactly that day-slot." Forty percent of `find` bugs are someone typing `7` when they meant `-7`. The exam typically asks *"in the last N days"*, which is always `-N`. Drill three queries every time you sit down — `-mtime -7`, `-mtime +30`, `-mtime 1` — until your fingers won't type them wrong. The `-printf '%T+ %p\n' | sort` chaser is a free debugging aid: when the result looks wrong, the sorted timeline tells you instantly which side of the boundary your edge cases landed on.

**Analogy:** A bouncer at a club checking IDs. `-mtime -7` is *"under 7 days old, come in."* `-mtime +30` is *"over 30 days old, you're banned."* `-mtime 7` is *"exactly seven days old — show me your birth certificate to confirm the day-slot."*

**Expected output:**

```
/root/find-lab/recent/six-days.log
/root/find-lab/recent/two-days.log
/root/find-lab/recent/today.log

2026-05-16+09:00:00.0000000000  /root/find-lab/recent/six-days.log
2026-05-20+09:00:00.0000000000  /root/find-lab/recent/two-days.log
2026-05-22+09:00:00.0000000000  /root/find-lab/recent/today.log
3
```

**Switches table:**

| Token | Meaning |
|---|---|
| `-type f` | Regular files only |
| `-mtime -N` | Modified **less than** N×24 hours ago ("newer than") |
| `-mtime +N` | Modified **more than** N×24 hours ago ("older than") |
| `-mtime N` | Modified exactly in the Nth-day slot back |
| `-printf` | Custom action — `%T+` mtime, `%p` path, `\n` newline |
| `wc -l` | Count lines |

**Output decoded table:**

| Line | Meaning |
|---|---|
| Three paths from `recent/` | These are within the last 7 days ✅ |
| No `medium/` or `ancient/` paths | Their mtimes are older than 7 days, correctly excluded |
| Count = `3` | Matches the three rows above |

**Troubleshoot table:**

| Symptom | Fix |
|---|---|
| Returns *too many* files | You forgot the minus sign: `-mtime 7` matches only the exact 7-day slot, but `-mtime +7` would mean older than 7 days, etc. Re-read Task 3's "story" |
| Returns *zero* files | Your sandbox mtimes didn't take — `stat` one of them to verify |
| Includes directories | Add `-type f`; without it, `find` matches dirs too |
| `find: paths must precede expression` | A test came before the starting path; reorder so path is first |

---

### Task 4 — Find files older than N days and use a `-newer` reference file

**Purpose:** The *other* half of the time-test space: `+N` for old files, and the `-newer FILE` form for boundary-precise queries.

**Command block:**

```bash
find /root/find-lab -type f -mtime +30
touch -d "$(date -d '7 days ago 00:00')" /tmp/seven-days-marker
find /root/find-lab -type f -newer /tmp/seven-days-marker -printf '%T+  %p\n' | sort
find /root/find-lab -type f ! -newer /tmp/seven-days-marker -printf '%T+  %p\n' | sort
```

**Human-Readable Breakdown:**
> "First show me every file in the lab older than thirty days — the canonical 'old log' query. Then build a *marker* file dated exactly seven days ago at midnight, and use `-newer` against that marker to produce a precise 'modified since' list. Then flip the test with `!` to get the *inverse*: everything modified at or before the marker."

**Reading it left to right:**
- `find ... -mtime +30` → "older than 30 × 24 hours."
- `touch -d "$(date -d '7 days ago 00:00')" /tmp/seven-days-marker` → "create a marker file whose mtime is exactly seven days ago at midnight."
- `-newer /tmp/seven-days-marker` → "test: file's mtime is *strictly greater than* the marker's mtime."
- `! -newer /tmp/seven-days-marker` → "the logical NOT. Matches everything *not* newer than the marker — i.e. older or equal."

**The story:** `-newer` is the *boundary-precise* alternative to `-mtime`. The trouble with `-mtime -7` is that "seven days" rounds to whole 24-hour windows. If you need *"modified since 2026-05-15 00:00 exactly"*, you can't say that with `-mtime`. You can with `-newer`: build a marker, point `-newer` at it. Backup systems use this constantly — they `touch /var/backups/last-run` after a successful backup, and the next run is `find / -newer /var/backups/last-run` for a perfect incremental. The `!` operator is the second half of the same idea — flip any test to get its negation, no separate command needed.

**Analogy:** `-mtime` is a calendar week. `-newer FILE` is a stopwatch — you decide the exact moment "zero" was, by setting the marker file.

**Expected output:**

```
/root/find-lab/medium/fortyfive-days.log
/root/find-lab/ancient/four-months.log
/root/find-lab/ancient/over-a-year.log

2026-05-16+09:00:00.0000000000  /root/find-lab/recent/six-days.log
2026-05-20+09:00:00.0000000000  /root/find-lab/recent/two-days.log
2026-05-22+09:00:00.0000000000  /root/find-lab/recent/today.log

2025-04-18+09:00:00.0000000000  /root/find-lab/ancient/over-a-year.log
2026-01-22+09:00:00.0000000000  /root/find-lab/ancient/four-months.log
2026-04-07+09:00:00.0000000000  /root/find-lab/medium/fortyfive-days.log
2026-05-12+09:00:00.0000000000  /root/find-lab/medium/ten-days.log
```

**Switches table:**

| Token | Meaning |
|---|---|
| `-mtime +N` | Older than N × 24 hours |
| `-newer FILE` | mtime strictly greater than FILE's mtime |
| `! TEST` | Logical NOT — invert the test |
| `touch -d 'TIME' MARKER` | Plant a reference file with a specific mtime |

**Output decoded table:**

| Line | Meaning |
|---|---|
| Three paths from `medium/` and `ancient/` | Mtimes are > 30 days; correctly matched by `-mtime +30` |
| Three paths from `recent/` for `-newer` | All within the last 7 days, so newer than the marker ✅ |
| Four paths for `! -newer` | The four files older than 7 days, neatly partitioned by the marker |

**Troubleshoot table:**

| Symptom | Fix |
|---|---|
| `-newer` returns everything | The marker's mtime is *older* than every file you wanted to exclude — re-`touch` it |
| `! -newer` returns nothing | The marker's mtime is in the future — `stat /tmp/seven-days-marker` to verify |
| Mismatch by one day | Daylight Saving Time changed since the marker — rebuild it with `touch -d` |

---

### Task 5 — Act on matches: copy with `cp --parents`, archive with `tar --files-from`

**Purpose:** The exam's *real* phrasing is rarely "list them" — it's "copy them," "archive them," or "delete them." Drill the action half.

**Command block:**

```bash
mkdir -p /root/recent-find
find /root/find-lab -type f -mtime -7 -exec cp --parents -t /root/recent-find {} +
ls -lR /root/recent-find

find /root/find-lab -type f -mtime -7 -print0 \
  | tar --null --files-from=- -czf /root/recent-find.tgz
tar -tzf /root/recent-find.tgz
```

**Human-Readable Breakdown:**
> "First make a destination directory, then use `find ... -exec cp --parents -t DEST {} +` to copy every recent file into it — preserving the relative directory structure so the original tree shape is mirrored. Verify with a recursive `ls`. Then do the same job as a *tar archive* instead of a copy: NUL-separate the `find` output for safety, pipe it into `tar --files-from=-`, and produce a gzipped tarball you can ship. List the archive to confirm."

**Reading it left to right:**
- `mkdir -p /root/recent-find` → "destination dir; `-p` makes parents and doesn't error on existing."
- `find ... -exec CMD {} +` → "**`+` form** of `-exec` — pass *many* matches to one `cp` invocation. Faster than `\;` which forks one `cp` per file."
- `cp --parents -t DEST FILES` → "`--parents` keeps the source's relative path (so `/root/find-lab/recent/today.log` lands at `/root/recent-find/root/find-lab/recent/today.log`). `-t DEST` means **target dir first**, files after — needed by `-exec ... {} +`."
- `-print0` and `tar --null --files-from=-` → "NUL-delimited list; survives filenames with spaces, newlines, etc. **Use this idiom whenever a filename you don't control hits a pipeline.**"
- `tar -czf FILE` → "**c**reate, g**z**ipped, into **f**ile FILE."

**The story:** Two patterns to memorize. **First, `-exec ... {} +`** is the modern, fast form — it batches matches into one invocation per command, like xargs but without the extra pipe. **Second, `find -print0 | tar --null --files-from=-`** is the bulletproof archive idiom: NULs can't appear in filenames on Linux, so they're the only safe delimiter for filename lists. The exam often phrases the task as *"copy these to /root/somewhere"* — `cp --parents -t DEST` is the one-liner answer. (Some graders accept rsync; both are fine.) The tar variant is for *"archive these to a tarball"* — same query, different action.

**Analogy:** `find` gives you a guest list. `-exec cp` is hand-delivering each invitation; `tar --files-from` is stuffing every invitation into one envelope and mailing the bundle.

**Expected output:**

```
/root/recent-find:
total 0
drwxr-xr-x. 3 root root 16 May 22 18:30 root

/root/recent-find/root:
total 0
drwxr-xr-x. 3 root root 26 May 22 18:30 find-lab

/root/recent-find/root/find-lab:
total 0
drwxr-xr-x. 2 root root 64 May 22 09:00 recent

/root/recent-find/root/find-lab/recent:
total 0
-rw-r--r--. 1 root root 0 May 16 09:00 six-days.log
-rw-r--r--. 1 root root 0 May 20 09:00 two-days.log
-rw-r--r--. 1 root root 0 May 22 09:00 today.log

root/find-lab/recent/six-days.log
root/find-lab/recent/two-days.log
root/find-lab/recent/today.log
```

**Switches table:**

| Token | Meaning |
|---|---|
| `-exec CMD {} +` | Run CMD once for *many* matches (xargs-style batching) |
| `-exec CMD {} \;` | Run CMD once per match (slower, but fine for low counts) |
| `cp --parents` | Preserve the source's relative path structure |
| `cp -t DEST FILES` | Target dir first, files after — pairs with `-exec {} +` |
| `-print0` | NUL-separate filenames (instead of newline) |
| `tar --null --files-from=-` | Read NUL-separated filename list from stdin |
| `tar -czf FILE` | Create gzipped archive |
| `tar -tzf FILE` | List a gzipped archive |

**Output decoded table:**

| Line | Meaning |
|---|---|
| `recent-find/root/find-lab/recent/...` | `--parents` rebuilt the source path under the destination |
| Three files, same mtimes as source | `cp` copied content + preserved timestamps by default (`-p` would force it) |
| Tar listing shows relative paths | The archive can be unpacked anywhere without absolute-path conflicts |

**Troubleshoot table:**

| Symptom | Fix |
|---|---|
| `cp: missing destination file` | `-t DEST` not supplied, or `{}` came before `-t` — order matters with `+` form |
| `find: -exec: no terminating ;` | You used `\;` then `+` together, or one of them is unquoted |
| `tar: Cowardly refusing to create an empty archive` | The `find` query returned zero matches — re-check `-mtime` sign |
| Spaces/newlines in filenames mangle the archive | You used `\n`-separated piping; switch to `-print0` + `--null` |

---

### Task 6 — Capstone: RHCSA-style "find under /etc, copy preserving structure"

**Purpose:** Run the full RHCSA-style sequence from a blank slate: find every file under `/etc` modified in the last 7 days, copy them while preserving directory structure, capture a sortable timeline, and verify the result.

**Command block:**

```bash
# 0. Clean slate (idempotent)
rm -rf /root/recent-etc /root/recent-etc-timeline.txt
mkdir -p /root/recent-etc

# 1. The headline find: regular files, modified in the last 7 days, under /etc
#    Copy preserving path structure into /root/recent-etc.
find /etc -type f -mtime -7 -exec cp --parents -t /root/recent-etc {} +

# 2. Companion timeline: <ISO mtime>  <path>, oldest first
find /etc -type f -mtime -7 -printf '%T+  %p\n' \
  | sort \
  | tee /root/recent-etc-timeline.txt

# 3. Verify
echo "---- counts ----"
find /etc           -type f -mtime -7 | wc -l
find /root/recent-etc -type f          | wc -l
echo "---- top of timeline ----"
head -5 /root/recent-etc-timeline.txt
echo "---- spot-check a copied file ----"
SAMPLE=$(find /etc -type f -mtime -7 | head -1)
diff -q "$SAMPLE" "/root/recent-etc${SAMPLE}" && echo "Sample bytes match."
```

**Human-Readable Breakdown:**
> "End-to-end exam answer in one block. Wipe any previous run. Make the destination. Run the headline `find ... -mtime -7 -exec cp --parents -t DEST {} +` against `/etc`. Build a sortable timeline of the same matches with `-printf '%T+ %p\n' | sort | tee`. Then verify with three checks: source-side match count equals destination-side file count, the timeline file has reasonable content, and a byte-for-byte `diff` of one copied sample proves the copy was faithful."

**Reading it left to right:**

| Block | What it does |
|---|---|
| `rm -rf ...` + `mkdir -p ...` | Idempotent reset of the destination tree |
| `find /etc -type f -mtime -7 -exec cp --parents -t /root/recent-etc {} +` | The headline command — copy every match preserving relative paths |
| `find ... -printf '%T+  %p\n' \| sort \| tee /root/recent-etc-timeline.txt` | Build & save a chronological timeline of the matches |
| `find /etc ... \| wc -l` and `find /root/recent-etc ... \| wc -l` | Count match: source vs copy must agree |
| `SAMPLE=$(find ... \| head -1)` + `diff -q` | Byte-level proof for at least one file |

**The story:** This is the **2-minute exam answer.** Memorize the spine: `find /etc -type f -mtime -7 -exec cp --parents -t /root/DEST {} +`. Everything else is verification. The three checks at the end mirror what a careful grader will run: do counts match, is the timeline sane, are the bytes identical? If you can type the spine from memory and run the three checks, every "find by time" question on the exam is a freebie. Substitute `+30` for `-7`, `tar` for `cp`, `/var/log` for `/etc`, and the same answer template covers every variant.

**Analogy:** The closing argument of a courtroom speech you've rehearsed a hundred times. The bones don't change — only the names and numbers.

**Expected output (representative — counts vary by system):**

```
---- counts ----
142
142
---- top of timeline ----
2026-05-16+04:32:01.0000000000  /etc/aliases.db
2026-05-16+04:32:01.0000000000  /etc/postfix/main.cf
2026-05-17+11:08:44.0000000000  /etc/ssh/sshd_config
2026-05-18+02:11:09.0000000000  /etc/sudoers.d/cloud-init
2026-05-22+09:14:33.0000000000  /etc/hostname
---- spot-check a copied file ----
Sample bytes match.
```

**Switches table:**

| Token | Meaning |
|---|---|
| `rm -rf` | Remove previous destination state |
| `mkdir -p` | Create destination directory |
| `find /etc -type f -mtime -7` | Match regular files modified in the last seven days |
| `-exec cp --parents -t DEST {} +` | Copy matches in batches while preserving path structure |
| `-printf '%T+  %p\n'` | Print sortable mtime plus path |
| `tee FILE` | Save timeline while displaying it |
| `diff -q` | Quiet byte-for-byte comparison |

**Output decoded table:**

| Step | Expected |
|---|---|
| Source vs destination file counts equal | Every matched source file was copied |
| Timeline file is non-empty and chronologically sorted | `-printf '%T+'` and `sort` worked |
| `diff -q` prints no difference | Sample copy is byte-identical |
| Destination tree mirrors `/etc` shape | `cp --parents` preserved directories |
| No permission-denied errors | Running as root had enough access |

**Troubleshoot table:**

| Symptom | Fix |
|---|---|
| Counts differ between source and destination | A path under `/etc` was unreadable; re-run as root, or add `2>/dev/null` if you want to ignore permission errors |
| `cp: missing destination file` | `-t /root/recent-etc` missing or in the wrong position relative to `{} +` |
| Timeline is empty | Your `/etc` genuinely had no changes in 7 days (rare on a working server); widen to `-mtime -30` |
| `diff` reports differences on the sample | The source changed between the `find` and the `diff` — re-run on a quiescent system |
| `find: ‘/etc/...’: Permission denied` | You're not root; rerun under `sudo -i` |

---

## 🔍 `find -mtime` Decision Guide

```
Got a "find by time" task to solve?
  │
  ├── "Files modified in the last N days"
  │       └── ✅ find PATH -type f -mtime -N
  │
  ├── "Files older than N days" (cleanup, retention)
  │       └── ✅ find PATH -type f -mtime +N         (verify with -print first!)
  │
  ├── "Files modified since exact moment T"
  │       └── ✅ touch -d 'T' /tmp/marker
  │       │   find PATH -type f -newer /tmp/marker
  │
  ├── "Files modified in the last N minutes" (mid-deploy)
  │       └── ✅ find PATH -type f -mmin -N
  │
  ├── "Copy matches preserving directory structure"
  │       └── ✅ find ... -exec cp --parents -t DEST {} +
  │
  ├── "Archive matches into a tarball"
  │       └── ✅ find ... -print0 \| tar --null --files-from=- -czf out.tgz
  │
  └── "Delete matches"
          └── ⚠️ Always -print first to dry-run, then -delete (or pipe to xargs rm)
```

---

## Lab Checklist (6 Tasks)

- [ ] 01 Build the sandbox with `touch -d "$(date -d ...)"` and seven known mtimes
- [ ] 02 Inspect with `stat`, `ls --full-time`, and `find -printf '%T+ %p\n' | sort`
- [ ] 03 The headline: `find PATH -type f -mtime -7` (drill the minus sign)
- [ ] 04 Older-than (`+N`) and boundary-precise (`-newer FILE`, with `!` inversion)
- [ ] 05 Act on matches — `cp --parents -t DEST` and `tar --null --files-from=-`
- [ ] 06 Capstone — end-to-end RHCSA "copy recent /etc files with structure"

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `-mtime 7` when meaning `-mtime -7` | Returns only the 24-hour slot 7 days back, not the week | Always think *sign first*: `-N` for "in the last N," `+N` for "older than N" |
| Forgot `-type f` | Matches directories too; `cp` then errors with "omitting directory" | Add `-type f` whenever you `-exec cp` |
| `-exec ... \;` instead of `... +` | Slow on big trees (one fork per match) | Use `+` for batching when the command accepts multiple args |
| Newline-piping filenames with spaces | `xargs` mangles them | `-print0` + `xargs -0` (or `tar --null --files-from=-`) |
| `-delete` before dry-run | Career-shortening event | *Always* `-print` first, then change the action |
| Test before path | `find: paths must precede expression` | Path → tests → actions, in that order |
| atime-based query on `relatime` FS | Always returns "no recent reads" | Use `-mtime` (or remount `strictatime`, which you almost never want) |
| Searched `/` without `-xdev` | Walks into `/proc`, `/sys`, `/mnt` and slows to a crawl | Add `-xdev` to stay on one filesystem |
| `cp --parents` without target dir | `cp` errors "missing destination file operand" | Pair with `-t DEST` and the `{} +` form of `-exec` |
| Timestamps shift across DST | Off-by-one-hour boundary surprises | Prefer `-newer` against an explicit marker for date-precise jobs |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- "Find files under /etc modified in the last 7 days and copy them preserving structure to /root/somewhere" is the canonical exam phrasing. Memorize Task 6's spine: `find /etc -type f -mtime -7 -exec cp --parents -t /root/recent-etc {} +`.

**RHCE candidate**
- The equivalent Ansible task uses `ansible.builtin.find` with `age: -7d`, then `ansible.builtin.copy` in a loop. Practice converting the CLI one-liner to a playbook.

**SRE / Platform interview**
- "Last incident was last Tuesday — what changed under /etc and /opt around then?" Use a `-newer` marker plus `-printf '%T+ %p\n' | sort` to produce an incident-window timeline.

**DevOps**
- CI caches and build artifacts need eviction. `find /var/cache/build -type f -mtime +14 -delete` (dry-run first!) is the universal one-liner.

**Forensics / Security**
- The first command in any breach investigation is a `find / -xdev -newer /tmp/last-known-good -ls` timeline. The patterns you learn here transfer one-to-one.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lock User Account & Capture with Regex *(coming soon)* | Sibling RHCSA "report on system state" objective |
| User-Level Cronjob Using find -exec *(coming soon)* | Schedules a `find -mtime` cleanup on a cadence |
| Install Dev Tools & Capture Output *(coming soon)* | Same `tee` capture pattern, different action |
| Apply Recursive SELinux Contexts *(coming soon)* | Pairs `find` style recursion with `restorecon -R` |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
