# Lab: Service-Specific Journal Logs — `journalctl -u UNIT`, `-t TAG`, `_SYSTEMD_UNIT=`, `_COMM=`

- **Series:** linux-ops-mastery — RHCSA Log Management
- **Subjects covered:** `journalctl -u UNIT` (filter by systemd unit), glob patterns `journalctl -u 'foo-*'`, multi-unit OR (`-u httpd -u sshd`), `journalctl -t TAG` for syslog-identifier filtering, field filters (`_SYSTEMD_UNIT=`, `_COMM=`, `_PID=`, `_UID=`, `SYSLOG_IDENTIFIER=`), `-xeu UNIT` shortcut for explained errors of one unit, `--user-unit` for user-scope units, follow mode `-fu UNIT`, capturing structured output with `-o json` and `_SYSTEMD_UNIT`, distinguishing `_SYSTEMD_UNIT` (trusted) from `UNIT` (user-supplied), troubleshooting "unit not in journal" cases
- **Career arcs covered:** RHCSA (EX200 — "show me httpd messages for the last hour"), RHCE (Ansible per-unit assertion), SRE (per-service triage in incident timelines), DevOps (CI build service logs), AI / MLOps (per-training-job log scoping)
- **Prerequisite:** Labs 101–105
- **Time Estimate:** 30 to 40 minutes
- **Difficulty arc:** Tasks 1–2 baseline + listing units · Task 3 single-unit filter · Tasks 4–5 multi-unit and glob · Task 6 tag and field filters · Task 7 follow mode · Task 8 `-xeu` for errors · Task 9 user-scope units · Task 10 capstone unit-by-priority report + cleanup

---

## Objective

Stop scrolling through 18,000 lines to find the 12 from `httpd.service`. By the end of this lab you can scope `journalctl` to **one** service, **multiple** services, a **glob** of services, an arbitrary **tag**, or a structured **field** like `_PID=` or `_COMM=` — and combine those with the time, priority, and boot filters from earlier labs to produce surgical queries.

The capstone is the engineer-realistic prompt: *"For the units `httpd.service`, `sshd.service`, and `chronyd.service`, capture every error-or-worse entry on the current boot. Write a per-unit count to a report file, and the worst single message per unit. Then clean up."*

> **Lab safety note:** Read-only. The only writes are into `/root/journal-svc-lab/` plus `logger` test events.

---

## Concept: A "Unit" in `journalctl` Is a Trusted Field

When systemd starts a service, every entry that service emits is tagged with the structured field `_SYSTEMD_UNIT=NAME.service` by `journald` — **not by the service itself**. Because journald derives the tag from the cgroup membership, you cannot forge it from userspace. That makes `_SYSTEMD_UNIT` a **trusted** field (prefixed with `_`).

There is also a **user-supplied** `UNIT=` field that comes from the message itself (most importantly the lines that `systemd[1]` prints about other services). Both exist, and `journalctl -u UNIT` matches **either**.

```
   ┌──────────────────────────────────────────────────────────────┐
   │ Source                  Field                                │
   │ ----------------------- ------------------------------------ │
   │ journald (cgroup-derived) _SYSTEMD_UNIT  ← trusted            │
   │ systemd[1] message body   UNIT           ← what systemd1 said │
   │ application syslog tag    SYSLOG_IDENTIFIER                   │
   │ binary path               _EXE / _COMM                        │
   │                                                              │
   │ journalctl -u NAME    →  matches BOTH _SYSTEMD_UNIT=NAME      │
   │                          AND UNIT=NAME                        │
   │ journalctl _SYSTEMD_UNIT=NAME → trusted only                  │
   │ journalctl _COMM=name → process command name                  │
   │ journalctl -t TAG     → SYSLOG_IDENTIFIER=TAG                 │
   └──────────────────────────────────────────────────────────────┘
```

> **Why this matters:** `-u sshd.service` is the easy answer for "show me sshd messages." But when triaging, the journal often shows `systemd[1]: Started ssh.service` lines — those are tagged `UNIT=sshd.service`, not `_SYSTEMD_UNIT=sshd.service`. `-u` matches both; `_SYSTEMD_UNIT=` is stricter. Knowing the difference is the difference between "I see everything about sshd" and "I see only what sshd itself emitted."

---

## 📜 Why Per-Unit Filtering Exists — The Story

`journald` was designed in 2010-2011 with **structured fields** in mind. From the beginning, each entry carried metadata: the cgroup (`_SYSTEMD_CGROUP`), the unit (`_SYSTEMD_UNIT`), the binary (`_EXE`), the boot ID (`_BOOT_ID`), and many more. The `_`-prefixed fields are **trusted** because journald sets them from kernel-provided cgroup membership, not from anything the process said.

The `-u UNIT` shortcut was added because operators kept typing `_SYSTEMD_UNIT=foo.service` and wanted a friendlier form. But the shortcut also needed to match the `UNIT=` field used by `systemd[1]` itself when narrating its own actions ("Started X", "Failed Y"). So `-u` matches **both** fields — a small convenience that prevents the surprise of missing your service's own start/stop log lines.

> **The point of the story:** `-u` is your everyday tool. `_SYSTEMD_UNIT=` is the strict tool. RHCSA tests only `-u`, but a senior engineer knows both.

---

## 👪 The Unit-Filter Family — Who Lives Where

```
Most-used filters
├── -u UNIT                     ← service, socket, timer, target
├── -u 'GLOB'                   ← glob match across units
├── -t TAG                      ← SYSLOG_IDENTIFIER
└── -xeu UNIT                   ← explained + jump to end + unit

Field filters (advanced)
├── _SYSTEMD_UNIT=foo.service   ← trusted unit
├── _COMM=cmdname               ← process command name (15 char max)
├── _EXE=/abs/path              ← absolute exe path
├── _PID=N                      ← PID filter
├── _UID=N                      ← UID filter
├── _GID=N                      ← GID filter
├── _CMDLINE=...                ← command line
└── SYSLOG_IDENTIFIER=tag       ← same as -t TAG

User-scope
├── --user                       ← read your own user journal
├── --user-unit=NAME             ← unit in your user manager
└── -M MACHINE                   ← logs from a container/VM machined

List helpers
├── journalctl --output=verbose -n 1   ← see EVERY field of one entry
├── journalctl -F _SYSTEMD_UNIT        ← list every unique value of a field
└── journalctl --list-boots            ← all boots
```

---

## 📚 Service-Specific Filter Reference Table

| Goal | Command | Notes |
|---|---|---|
| One unit | `journalctl -u sshd.service` | Matches `_SYSTEMD_UNIT` and `UNIT` |
| Multiple units (OR) | `journalctl -u sshd -u httpd` | Repeat the flag |
| Glob | `journalctl -u 'systemd-*'` | Quote to protect from shell |
| Follow live | `journalctl -fu sshd.service` | `-f` + `-u` combined |
| Errors + explained | `journalctl -xeu sshd.service` | `-x` + `-e` + `-u` |
| Trusted unit only | `journalctl _SYSTEMD_UNIT=sshd.service` | Stricter than `-u` |
| By tag | `journalctl -t sudo` | matches `SYSLOG_IDENTIFIER` |
| By PID | `journalctl _PID=1234` | One process |
| By UID | `journalctl _UID=1000` | All processes of a user |
| By exe | `journalctl /usr/sbin/sshd` | Absolute path filter |
| By command | `journalctl _COMM=sshd` | Includes subprocesses |
| User journal | `journalctl --user` | Your own user manager |
| User unit | `journalctl --user-unit=NAME.service` | User scope |
| List all units in journal | `journalctl -F _SYSTEMD_UNIT` | Distinct values |
| List all tags | `journalctl -F SYSLOG_IDENTIFIER` | Distinct values |
| List boots | `journalctl --list-boots` | Per-boot summary |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | "Show me messages from `httpd` for the last hour." → `journalctl -u httpd --since "1 hour ago"`. |
| **RHCE candidate** | Ansible: register output of `journalctl -u app.service --since "1 hour ago" -o json`, fail if errors present. |
| **SRE / Platform** | Per-service timeline view = `journalctl -u UNIT -p warning --since "...T-15m" --until "...T+5m"`. |
| **DevOps** | CI logs scoped to the build service unit before tear-down. |
| **AI / MLOps** | Per-job systemd-managed training units; `journalctl -u training-job-42.service` is the post-mortem starting point. |

---

## 🔧 The 10 Tasks

> Ten phases that build the **list → single unit → multi-unit → glob → tag → field → follow → explain → user-scope** habit.

---

### Task 1 — Set up the sandbox and inventory available units

**Purpose:** Build the workspace and list every distinct unit currently visible in the journal.

```bash
sudo -i
mkdir -p /root/journal-svc-lab && cd /root/journal-svc-lab

journalctl -F _SYSTEMD_UNIT | sort | tee 01-units.txt | head -n 20
journalctl -F SYSLOG_IDENTIFIER | sort | tee 01-tags.txt | head -n 20
wc -l 01-units.txt 01-tags.txt
```

**Human-Readable Breakdown:** Use `-F FIELD` to list every distinct value of a structured field — first units, then syslog identifiers (tags). Save both lists and count them.

**Reading it left to right:** `-F _SYSTEMD_UNIT` enumerates every unique unit name in the journal. `-F SYSLOG_IDENTIFIER` does the same for tags. Both are essential for "what is on this host?" inventory questions.

**The story:** Before filtering, know what is filterable. On a fresh RHEL 9 VM you'll see ~30-50 units; on a production server, hundreds. This list is your menu.

**Expected output (excerpt):**

```text
NetworkManager.service
NetworkManager-wait-online.service
auditd.service
chronyd.service
crond.service
dbus-broker.service
dnf-makecache.service
firewalld.service
getty@tty1.service
kdump.service
... 
audit
chronyd
crond
dbus-daemon
dhclient
firewalld
journal
kernel
NetworkManager
sshd
sudo
systemd
```

**Switches**

| Token | Meaning |
|---|---|
| `-F FIELD` | List distinct values |
| `sort` | Alphabetical |
| `head -n N` | First N |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Empty `-F` | Volatile + tiny journal — generate some activity |
| `field not found` | Wrong case — case matters |

---

### Task 2 — Read the most recent messages for one unit

**Purpose:** The canonical first filter.

```bash
cd /root/journal-svc-lab

journalctl -u sshd.service --no-pager -n 20 | tee 02-sshd-tail20.txt
journalctl -u sshd.service --no-pager --since today -p info -n 20 | tee 02-sshd-today.txt
journalctl -u sshd.service -o cat --no-pager -n 5 | tee 02-sshd-cat.txt
```

**Human-Readable Breakdown:** Three views of `sshd.service` — last 20 entries, today's info-or-worse, and the same entries with just the MESSAGE field (`-o cat`).

**Reading it left to right:** `-u sshd.service` is the unit filter. `-n N` limits count. `-o cat` strips metadata.

**The story:** This is the **most-used** `journalctl` invocation in the world. Memorize the four variations: tail (`-n N`), bound (`--since today`), priority (`-p err`), and pretty (`-o cat`).

**Expected output (excerpt):**

```text
Jan 14 09:01:11 host1 sshd[1820]: Accepted publickey for root from 10.0.0.5 port 51422 ssh2
Jan 14 09:01:11 host1 systemd[1]: Started OpenSSH per-connection server daemon (10.0.0.5:51422).
...
Accepted publickey for root from 10.0.0.5 port 51422 ssh2
Started OpenSSH per-connection server daemon (10.0.0.5:51422).
```

**Switches**

| Token | Meaning |
|---|---|
| `-u UNIT` | Filter to one unit |
| `-n N` | Last N entries |
| `-o cat` | MESSAGE only |
| `-p info` | Priority floor info |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Empty | Unit name typo — confirm with `systemctl list-units` |
| Includes lines about other units | Expected — `-u` also matches `UNIT=` from `systemd[1]` |

---

### Task 3 — Multiple units with repeated `-u`

**Purpose:** OR-combine two or more units.

```bash
cd /root/journal-svc-lab

journalctl -u sshd.service -u chronyd.service --no-pager -n 20 | tee 03-multi.txt
journalctl -u sshd.service -u chronyd.service -u firewalld.service -o json --no-pager -n 5 \
  | grep -oE '"_SYSTEMD_UNIT":"[^"]+"' | sort | uniq -c | tee 03-multi-distinct.txt
```

**Human-Readable Breakdown:** Filter for three units in one call, then confirm the result includes entries from all three.

**Reading it left to right:** Each `-u UNIT` extends the filter set with OR semantics. The grep + uniq counts which units actually contributed entries.

**The story:** Use this when triaging an incident that spans services — "give me everything from `chronyd`, `sshd`, and `firewalld` for the last hour." Skip the intermediate `grep | grep | grep`.

**Expected output:**

```text
      3 "_SYSTEMD_UNIT":"chronyd.service"
      1 "_SYSTEMD_UNIT":"firewalld.service"
      1 "_SYSTEMD_UNIT":"sshd.service"
```

**Switches**

| Token | Meaning |
|---|---|
| `-u A -u B -u C` | OR three units |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| One unit dominates | Expected on busy hosts — add `--since` or `-p` |
| `-u 'A,B'` rejected | Comma-separated not supported; repeat the flag |

---

### Task 4 — Glob match: `-u 'systemd-*'`

**Purpose:** Filter by a wildcard pattern.

```bash
cd /root/journal-svc-lab

journalctl -u 'systemd-*' --no-pager -n 20 | tee 04-systemd-glob.txt
journalctl -u 'systemd-*' -o json --no-pager -n 100 \
  | grep -oE '"_SYSTEMD_UNIT":"[^"]+"' | sort | uniq -c | sort -rn | tee 04-systemd-glob-counts.txt
```

**Human-Readable Breakdown:** Single-quote the glob so the shell does not expand it, then count which units actually matched.

**Reading it left to right:** `'systemd-*'` is interpreted by `journalctl`, not the shell. Common matches include `systemd-journald.service`, `systemd-logind.service`, `systemd-udevd.service`, etc.

**The story:** Globs are useful for "all this family of services" without typing each name. Don't forget the quotes — bare `systemd-*` would expand against filenames in the current directory and produce a confusing error.

**Expected output:**

```text
     12 "_SYSTEMD_UNIT":"systemd-logind.service"
      8 "_SYSTEMD_UNIT":"systemd-journald.service"
      4 "_SYSTEMD_UNIT":"systemd-udevd.service"
```

**Switches**

| Token | Meaning |
|---|---|
| `'PATTERN*'` | Glob match |
| `'?'` | Single-char wildcard |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `No such file or directory: foo-*` | Forgot to quote |
| Glob matches nothing | Pattern too specific — try shorter |

---

### Task 5 — Tag filter `-t TAG` and `SYSLOG_IDENTIFIER=`

**Purpose:** Filter by syslog tag (the program name that `syslog(3)` calls itself).

```bash
cd /root/journal-svc-lab

journalctl -t sudo --no-pager -n 10 | tee 05-by-tag.txt
journalctl SYSLOG_IDENTIFIER=sudo --no-pager -n 10 | tee 05-by-field.txt
diff 05-by-tag.txt 05-by-field.txt || echo "(identical)"

logger -t lab106 -p user.notice "tag filter demo"
sleep 1
journalctl -t lab106 --no-pager | tee 05-injected.txt
```

**Human-Readable Breakdown:** Show `-t sudo` and the equivalent field filter, prove they produce identical output, then inject a custom tag with `logger` and prove the filter sees it.

**Reading it left to right:** `-t TAG` is shorthand for `SYSLOG_IDENTIFIER=TAG`. Most syslog-aware apps (sudo, cron, sshd, postfix) set this field deliberately so operators can filter by it.

**The story:** Tags are useful when a program writes to the journal but is **not** a systemd service (or is too generic). Custom scripts that call `logger -t myscript` are the easiest example.

**Expected output:**

```text
Jan 14 09:55:11 host1 sudo:    kelvin : TTY=pts/0 ; PWD=/home/kelvin ; ...
(identical)
Jan 14 09:55:55 host1 lab106[2950]: tag filter demo
```

**Switches**

| Token | Meaning |
|---|---|
| `-t TAG` | SYSLOG_IDENTIFIER filter |
| `SYSLOG_IDENTIFIER=TAG` | Equivalent field form |
| `logger -t TAG` | Set tag when injecting |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Tag filter empty | The app doesn't set `SYSLOG_IDENTIFIER` — try `-u UNIT` |
| `diff` shows differences | Field filter is stricter — `-t` may match more |

---

### Task 6 — Field filters: `_PID=`, `_UID=`, `_COMM=`, exe path

**Purpose:** Filter by structured trusted fields when `-u` is not enough.

```bash
cd /root/journal-svc-lab

journalctl _PID=1 --no-pager -n 5 | tee 06-pid1.txt
MY_UID=$(id -u)
journalctl _UID=$MY_UID --no-pager -n 5 | tee 06-my-uid.txt
journalctl _COMM=sshd --no-pager -n 10 | tee 06-comm-sshd.txt
journalctl /usr/sbin/sshd --no-pager -n 5 | tee 06-exe-sshd.txt
```

**Human-Readable Breakdown:** Filter by `_PID=1` (systemd itself), by the running user's UID, by command name (`sshd` and its workers), and by absolute exe path.

**Reading it left to right:** `_PID=N`, `_UID=N`, `_COMM=NAME` are field filters. The exe path filter is a shortcut for `_EXE=/abs/path`. `_COMM` is limited to 15 characters by the kernel.

**The story:** Field filters answer "all processes of user X" or "all messages from any process named `sshd`" — questions `-u` cannot answer. The exe path is the strictest filter because it binds to a literal binary, not a unit name.

**Expected output (excerpt):**

```text
Jan 14 09:00:11 host1 systemd[1]: Reached target Multi-User System.
Jan 14 09:00:33 host1 systemd[1]: Started OpenSSH server daemon.
...
Jan 14 09:30:33 host1 sshd[2002]: Accepted password for kelvin ...
...
```

**Switches**

| Token | Meaning |
|---|---|
| `_PID=N` | PID filter |
| `_UID=N` | UID filter |
| `_COMM=NAME` | Process command name (15 chars) |
| `/abs/path` | Executable path |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `_COMM=sshd-session` rejected | Trim to 15 chars |
| Empty UID filter | UID was logged differently — try `_AUDIT_LOGINUID` |

---

### Task 7 — Follow live with `-fu UNIT`

**Purpose:** Tail a single unit in real time.

```bash
cd /root/journal-svc-lab

journalctl -fu sshd.service --no-pager &
JOBPID=$!
sleep 2

logger -p auth.info -t sshd "tail demo $(date -Iseconds)"
sleep 1

kill $JOBPID 2>/dev/null
wait $JOBPID 2>/dev/null
journalctl -t sshd --no-pager -n 3 | tee 07-tail-evidence.txt
```

**Human-Readable Breakdown:** Start `journalctl -fu sshd.service` in the background, inject a tagged log line, kill the follower, and confirm the message landed.

**Reading it left to right:** `-fu UNIT` combines `-f` (follow) and `-u UNIT` into one short flag string — systemd accepts it as two flags. `&` backgrounds; `$!` captures the PID for cleanup.

**The story:** This is the everyday SRE habit — a tmux pane with `journalctl -fu critical-service.service`. When the service hiccups, you see it.

**Expected output:**

```text
Jan 14 09:56:01 host1 sshd[2999]: tail demo 2026-01-14T09:56:01-05:00
```

**Switches**

| Token | Meaning |
|---|---|
| `-fu UNIT` | `-f` + `-u` combined |
| `&` | Background |
| `$!` | Last background PID |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Background process won't die | `kill -9 $JOBPID` |
| Nothing arrives | Unit idle — generate traffic |

---

### Task 8 — Explained errors for one unit with `-xeu`

**Purpose:** The famous `-xeu UNIT` shortcut for "what's wrong with this service?"

```bash
cd /root/journal-svc-lab

journalctl -xeu sshd.service --no-pager | tail -n 40 | tee 08-xeu-sshd.txt
journalctl -xeu chronyd.service --no-pager | tail -n 40 | tee 08-xeu-chronyd.txt
```

**Human-Readable Breakdown:** Use the three flags together — `-x` adds catalog explanations, `-e` jumps to the end (most recent), `-u UNIT` filters by unit — and save the last 40 lines per service.

**Reading it left to right:** `-xeu` is a habit. It is exactly what `systemctl status` recommends in its closing line: *"See `journalctl -xeu UNIT.service` for details."*

**The story:** This is the **single most popular** `journalctl` invocation among RHEL administrators. When a service fails, run `-xeu` and read.

**Expected output (excerpt):**

```text
Jan 14 09:00:33 host1 sshd[1801]: Server listening on 0.0.0.0 port 22.
Jan 14 09:00:33 host1 systemd[1]: Started OpenSSH server daemon.
-- Subject: Unit succeeded
-- Defined-By: systemd
-- The unit sshd.service has successfully entered the 'dead' state.
...
```

**Switches**

| Token | Meaning |
|---|---|
| `-x` | `--catalog` |
| `-e` | Jump to end |
| `-u UNIT` | Unit filter |
| `-xeu UNIT` | All three together |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| No catalog lines | Most messages have no catalog entry |
| `-e` invoked pager | Add `--no-pager` if scripting |

---

### Task 9 — User-scope units with `--user` and `--user-unit`

**Purpose:** Read the per-user journal (services running under a user's `systemd --user` manager).

```bash
cd /root/journal-svc-lab

journalctl --user --no-pager -n 10 2>&1 | tee 09-user-journal.txt
journalctl --user-unit=pulseaudio.service --no-pager -n 5 2>&1 | tee 09-user-unit.txt
journalctl --user-unit='*' --no-pager -n 5 2>&1 | tee 09-user-glob.txt
```

**Human-Readable Breakdown:** Read the current user's journal, then a specific user-unit, then every user-unit.

**Reading it left to right:** `--user` switches to the per-user journal namespace. `--user-unit=NAME` is the equivalent of `-u NAME` but in that namespace. On servers without user services, output may be empty.

**The story:** RHCSA labs don't usually exercise user-units, but RHCE Ansible playbooks that manage `systemd --user` services need this filter. Desktop installs use it for `pulseaudio`, `pipewire`, etc.

**Expected output (excerpt):**

```text
-- No entries --
-- No entries --
```

(empty on minimal server installs is fine)

**Switches**

| Token | Meaning |
|---|---|
| `--user` | User journal |
| `--user-unit NAME` | Filter user-unit |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Failed to read journal: Permission denied` | Re-run as the target user, not root |
| Empty even after enabling | No user services on this host |

---

### Task 10 — Capstone: per-unit error report + cleanup

**Task statement:** *"For three units — `sshd.service`, `chronyd.service`, `firewalld.service` — count error-or-worse entries on the current boot. Capture the worst single message per unit. Write a one-paragraph report. Then clean up."*

```bash
cd /root/journal-svc-lab

UNITS="sshd.service chronyd.service firewalld.service"
> 10-per-unit-errors.txt
> 10-worst-per-unit.txt

for U in $UNITS; do
  COUNT=$(journalctl -u "$U" -p err -b --no-pager | wc -l)
  WORST=$(journalctl -u "$U" -p err -b --no-pager -o cat | head -n 1)
  printf "%-25s  %5d  %s\n" "$U" "$COUNT" "${WORST:-(none)}" | tee -a 10-per-unit-errors.txt
done

cat > 10-report.txt <<EOF
Per-unit error audit — $(hostname) — boot 0 — $(date -Iseconds)

Units inspected:   ${UNITS}
Priority floor:    err

== Per-unit error counts and worst single line ==
$(cat 10-per-unit-errors.txt)

How to reproduce:
  for U in ${UNITS}; do
    journalctl -u "\$U" -p err -b --no-pager | wc -l
  done
EOF

cat 10-report.txt
```

**Layer stack you built:**

```text
10-report.txt                  ← deliverable
  ├── 01-units.txt              ← inventory
  ├── 02..09-*.txt              ← evidence per task
  └── 10-per-unit-errors.txt    ← raw count table
```

**Cleanup**

```bash
cd /root
rm -rf /root/journal-svc-lab
ls -ld /root/journal-svc-lab 2>&1 | head -n 1
exit
```

**Troubleshoot**

| Symptom | Fix |
|---|---|
| All counts 0 | Healthy host — report `(none)` |
| Spaces in unit names break the loop | Quote `"$U"` (we did) |
| Worst line empty | Unit emitted no error on this boot |

---

## 🔍 Service Triage Decision Guide

```
"Show me one service"             → journalctl -u UNIT
"Multiple services"               → journalctl -u A -u B -u C
"Family of services"              → journalctl -u 'PATTERN*'
"By tag (script using logger)"    → journalctl -t TAG
"By PID"                          → journalctl _PID=N
"All processes of a user"         → journalctl _UID=N
"Trust me this is sshd"           → journalctl _SYSTEMD_UNIT=sshd.service
"Errors of one service, explained"→ journalctl -xeu UNIT
"Watch live"                      → journalctl -fu UNIT
"User-scope (systemctl --user)"   → journalctl --user --user-unit=NAME
```

---

## ✅ Lab Checklist (10 Tasks)

- [ ] 01 Inventory units and tags
- [ ] 02 Single-unit query (`-u UNIT`)
- [ ] 03 Multi-unit (repeated `-u`)
- [ ] 04 Glob (`-u 'foo-*'`)
- [ ] 05 Tag filter (`-t TAG` and `SYSLOG_IDENTIFIER=`)
- [ ] 06 Field filters (`_PID`, `_UID`, `_COMM`, exe)
- [ ] 07 Follow mode (`-fu UNIT`)
- [ ] 08 Explained errors (`-xeu UNIT`)
- [ ] 09 User-scope (`--user --user-unit`)
- [ ] 10 Capstone per-unit error report + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Unquoted glob | Shell expands locally | Quote `'foo-*'` |
| `-u service` missing `.service` | Usually still matches | Be explicit when scripts depend on it |
| Confusing `_SYSTEMD_UNIT` and `UNIT` | `-u` matches both; field form matches one | Use field form for strictness |
| `_COMM` over 15 chars | Filter never matches | Trim to first 15 chars |
| `journalctl --user` as root | No user journal | Run as the target user |
| `-fu UNIT --no-pager` then can't kill | Background process hangs | `kill $!` from same shell |
| `-xeu UNIT` in a pipe with no `--no-pager` | Pager swallows output | Add `--no-pager` |
| `-t sudo` missing entries | Some sudo lines have different tag | Try `-u sudo.service` instead |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- "Show me httpd messages from the last hour." → `journalctl -u httpd.service --since "1 hour ago"`.

**RHCE candidate**
- Ansible: `command: journalctl -u {{ unit }} --since "{{ ansible_date_time.iso8601 }}" -p err -o json` with `failed_when: result.stdout_lines | length > 0`.

**SRE / Platform interview**
- Be ready to explain why `-u UNIT` matches more than `_SYSTEMD_UNIT=UNIT` (systemd[1] lines about the unit are tagged `UNIT=`, not `_SYSTEMD_UNIT=`).

**DevOps**
- Capture `journalctl -u build-runner.service -b --no-pager > build.log` on every CI tear-down for forensic retention.

**AI / MLOps**
- Per-job systemd-managed units: `journalctl -u training-job-${RUN_ID}.service` is the canonical post-mortem starting point.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 101 — Query Logs with `journalctl` | `-u` lives there as one filter among many |
| Lab 102 — Persistent Journal | Persistence is required for `-u UNIT -b -1` |
| Lab 105 — Filter by Priority | Pair `-u UNIT` with `-p PRIORITY` |
| Lab 104 — Auth Logs | `-u sshd.service` is the journald twin of `/var/log/secure` |
| Lab 99 — Systemd Unit Files | Knowing the unit name is a prerequisite |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
