# Lab: Query Logs with `journalctl` — `-u`, `-p`, `--since`, `--until`, `-b`, `-f`, `-x`, `-k`, `-o`

- **Series:** linux-ops-mastery — RHCSA Log Management
- **Subjects covered:** the systemd journal vs traditional syslog files, `journalctl` invocation grammar, unit filtering (`-u`), priority filtering (`-p`), time-window filtering (`--since`/`--until`), boot filtering (`-b`), follow-mode tailing (`-f`), explanation messages (`-x`), kernel-only logs (`-k`), output formatting (`-o`), reverse order (`-r`), pager control (`--no-pager`), filtering by PID/UID, and combining filters for triage
- **Career arcs covered:** RHCSA (EX200 — "find the most recent SSHD failure from this morning"), RHCE (Ansible `command:` with `journalctl --since` capture), SRE (centralized log triage and incident timelines), DevOps (CI failure forensics on ephemeral build VMs), AI/MLOps (GPU training-job failure post-mortems)
- **Prerequisite:** A RHEL 9 (or RHEL-compatible) VM with `systemd-journald` running, `sudo` or root, basic vocabulary for systemd units (`service`, `target`, `unit`)
- **Time Estimate:** 45 to 60 minutes
- **Difficulty arc:** Tasks 1–3 foundation (journal location, basic invocation, unit filter) · Tasks 4–6 priority + time-window + boot filtering · Tasks 7–8 follow mode + explanation messages · Task 9 output format and structured fields · Task 10 capstone investigation + cleanup

---

## Objective

Stop hunting for the right text file. By the end of this lab you can answer **"what went wrong, on which service, between which two timestamps, on which boot, at what priority?"** with one `journalctl` command — and pipe the result into a ticket without leaving the shell. You will also learn how to **tail** the journal in real time, how to render entries in machine-readable JSON for scripts, and how to scope queries to one boot, one unit, or one priority floor at a time.

The pattern this lab installs in your hands — **start broad → narrow by unit → narrow by priority → narrow by time** — is the same pattern SREs run during a "the website went down at 3:42 AM and recovered at 3:47 AM, what happened?" incident.

*The capstone is the engineer-realistic prompt: "Capture every error-or-worse log message produced by the `sshd` service since yesterday, on the current boot, in JSON, and write a one-paragraph summary to disk."*

> **Lab safety note:** This lab only reads from the journal — nothing is destroyed. Task 10 cleans up the artifacts it created under `/root/journal-lab`.

---

## Concept: The Journal Is a Single Indexed Store, Not a Text File

Pre-systemd RHEL relied on **rsyslog** writing plain text into `/var/log/messages`, `/var/log/secure`, `/var/log/cron`, `/var/log/maillog`, and friends. Each file was a flat append-only stream — fine for `tail -f`, painful for "show me only SSH errors between 02:00 and 02:30 last Tuesday." You had to know which file, parse timestamps with `awk`, grep by priority text, and pray nothing was rotated out.

systemd shipped `systemd-journald` in 2010. It writes **one binary, indexed, structured store** — by default ephemeral in `/run/log/journal` (lost on reboot), persistent in `/var/log/journal` once you create that directory (Lab 102). Every entry carries dozens of fields: `_SYSTEMD_UNIT`, `PRIORITY`, `_BOOT_ID`, `_PID`, `_UID`, `MESSAGE`, `SYSLOG_IDENTIFIER`, etc. `journalctl` is the indexed query tool over that store.

```
   ┌───────────────────────────────────────────────────────────────┐
   │  Kernel  ──►  /dev/kmsg                                       │
   │                  │                                            │
   │  Services ──►  systemd-journald  ──► /run/log/journal/ (RAM)   │
   │                  │                  └► /var/log/journal/ (disk)│
   │                  │                                            │
   │                  └─► rsyslog (optional)  ──► /var/log/messages │
   │                                            ──► /var/log/secure │
   │                                                                │
   │  journalctl                                                    │
   │     ├── -u  UNIT       (filter by .service / .socket / .target)│
   │     ├── -p  PRIORITY   (emerg..debug or 0..7)                  │
   │     ├── --since / --until   (time window — humans or ISO)      │
   │     ├── -b  [N]        (current boot, or N back: -0,-1,-2,...) │
   │     ├── -f             (follow — like tail -f)                 │
   │     ├── -x             (add "explanatory" catalog text)        │
   │     ├── -k             (kernel only)                           │
   │     ├── -o FORMAT      (short/verbose/json/cat/...)            │
   │     └── -r             (reverse — newest first)                │
   └───────────────────────────────────────────────────────────────┘
```

> **Why this matters:** Every RHCSA "find the log message about X" question is a `journalctl` filter combination. If you reach for `grep /var/log/messages`, you will sometimes win — but you cannot filter by priority or boot index without writing a parser. `journalctl` already did the indexing.

---

## 📜 Why `journalctl` Exists — The Story

Before systemd, RHEL log management was the **rsyslog universe**: a config file (`/etc/rsyslog.conf`), a daemon (`rsyslogd`), and a fan of plain-text files under `/var/log`. The split between "kernel messages" (in `dmesg` / `/var/log/dmesg`) and "service messages" (scattered across `messages`, `secure`, `cron`, `maillog`) meant a single incident often spanned three files with mismatched timestamps.

**Lennart Poettering and Kay Sievers** introduced `systemd-journald` in 2011 to fix four specific problems:

1. **One sink.** All services (and the kernel via `/dev/kmsg`) write into one place.
2. **Structured fields.** Every message carries a fixed schema — `PRIORITY`, `_SYSTEMD_UNIT`, `_PID`, `_BOOT_ID`, etc. — not just a free-form string.
3. **Indexed queries.** Time, boot, unit, and priority are indexes you can combine without grepping.
4. **Cryptographic forward integrity.** With `Seal=yes`, journals can be sealed so tampering after the fact is detectable.

The trade-off was **binary format**. You cannot `cat` a journal file or `tail -f /var/log/journal/...`. You must go through `journalctl`. Once you accept that, every other query that used to take five pipes becomes one flag.

> **The point of the story:** `journalctl` exists because syslog won the 1980s and lost the 2010s. Once services started caring about boot IDs and structured fields, a text grep was no longer enough. RHEL 7 (2014) made `journalctl` first-class; RHEL 8/9 still ship rsyslog *alongside* the journal — but `journalctl` is the truth.

---

## 👪 The `journalctl` Family — Who Lives Where

```
Storage
├── /run/log/journal/<MACHINE-ID>/*.journal     ← volatile (default if /var/log/journal is missing)
└── /var/log/journal/<MACHINE-ID>/*.journal      ← persistent (Lab 102 creates this)

Daemon and config
├── systemd-journald.service                     ← writes journal entries
├── /etc/systemd/journald.conf                   ← Storage=, SystemMaxUse=, MaxRetentionSec=
└── /etc/systemd/journald.conf.d/*.conf          ← drop-ins

Reader
└── journalctl                                   ← the only supported way to read the binary store

Companion text files (still written by rsyslog)
├── /var/log/messages                            ← general
├── /var/log/secure                              ← auth (Lab 104)
├── /var/log/cron                                ← cron
├── /var/log/maillog                             ← mail
└── /var/log/boot.log                            ← early boot
```

### Boot identifiers

| Token | Meaning |
|---|---|
| `-b` or `-b 0` | The **current** boot |
| `-b -1` | The **previous** boot |
| `-b -2` | Two boots ago |
| `--list-boots` | Show every boot the journal still remembers, indexed by negative offset and full boot ID |

### Priorities (RFC 5424, same as syslog)

| # | Name | When systemd uses it |
|---|---|---|
| 0 | `emerg` | System is unusable |
| 1 | `alert` | Action must be taken immediately |
| 2 | `crit` | Critical conditions |
| 3 | `err` | Error conditions |
| 4 | `warning` | Warning conditions |
| 5 | `notice` | Normal but significant |
| 6 | `info` | Informational |
| 7 | `debug` | Debug-level messages |

> **Reading rule:** `-p N` means **N and lower** (i.e. more severe). `-p 3` returns `err`, `crit`, `alert`, `emerg` — not just `err`. If you want only one priority, use `-p N..N` (range syntax: `-p err..err`).

---

## 📚 `journalctl` Reference Table

| Goal | Command | Notes |
|---|---|---|
| All journal (paged) | `journalctl` | Defaults to current boot **only if persistent** — otherwise everything in `/run` |
| Disable pager | `journalctl --no-pager` | Required for `tee`, `head`, scripts |
| Newest first | `journalctl -r` | Reverse order — great with `head` |
| Tail last N lines | `journalctl -n 50` | Like `tail -n` |
| Follow live | `journalctl -f` | Like `tail -f` |
| Specific unit | `journalctl -u sshd.service` | Unit can be `.service`, `.socket`, `.target`, `.timer` |
| Multiple units | `journalctl -u sshd -u httpd` | Repeat the flag |
| Priority floor | `journalctl -p err` | Returns `err` and worse (`crit`/`alert`/`emerg`) |
| Priority range | `journalctl -p warning..err` | Inclusive both ends |
| Since human time | `journalctl --since "2 hours ago"` | Accepts `today`, `yesterday`, `09:00`, ISO 8601 |
| Until human time | `journalctl --until "10 min ago"` | Same syntax |
| Current boot only | `journalctl -b` or `-b 0` | Useful after a crash to filter out old noise |
| Previous boot | `journalctl -b -1` | Requires persistent journal (Lab 102) |
| List all boots | `journalctl --list-boots` | Index, boot ID, first/last timestamp |
| Kernel only | `journalctl -k` | Equivalent to `dmesg` but indexed |
| Explanation messages | `journalctl -xe` | Adds `man:systemd.catalog(7)` help text |
| JSON output | `journalctl -o json` | One JSON object per line |
| JSON pretty | `journalctl -o json-pretty` | Human-readable JSON |
| Short timestamps | `journalctl -o short-iso` | ISO timestamps instead of syslog-style |
| Cat-style (no metadata) | `journalctl -o cat` | Just MESSAGE field |
| Filter by PID | `journalctl _PID=1234` | Field=value syntax |
| Filter by UID | `journalctl _UID=1000` | Field=value syntax |
| Filter by executable | `journalctl /usr/sbin/sshd` | Absolute path |
| Filter by syslog tag | `journalctl SYSLOG_IDENTIFIER=cron` | Field=value |
| Disk usage | `journalctl --disk-usage` | How much storage the journal consumes |
| Verify integrity | `journalctl --verify` | Checks file format and seals |

> **Rule of triage:** start with `-u`, narrow by `-p`, then bound with `--since`/`--until`. Reach for `-b` last to limit to the current boot. Most "show me X" exam questions are a combination of these four switches.

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | EX200 will absolutely ask you to "view error-priority entries from `sshd` since this morning." `journalctl -u sshd -p err --since today` is the answer pattern. |
| **RHCE candidate** | Ansible roles capture `journalctl -u UNIT --since` output with `command:` modules to assert that a deployment did not generate errors. |
| **SRE / Platform** | Incident timelines are built from `journalctl --since "T-15m" --until "T+5m"` filtered by the affected unit. |
| **DevOps** | CI runners on ephemeral VMs: `journalctl -u my-build.service -p warning -b` is the canonical "what blew up?" command before the VM is torn down. |
| **AI / MLOps** | When a training job's systemd-managed CUDA service segfaults, `journalctl -u training.service -p err -b -1` is the post-mortem starting point. |

---

## 🔧 The 10 Tasks

> Ten exam-realistic phases that build the **invoke → filter by unit → filter by priority → filter by time → follow → explain → format → combine** habit.

---

### Task 1 — Set up the sandbox and confirm `journalctl` is available

**Purpose:** Build a small scratch directory for artifacts, confirm the journal is running, and capture baseline storage info.

```bash
sudo -i
mkdir -p /root/journal-lab && cd /root/journal-lab

which journalctl
journalctl --version | head -n 1
systemctl is-active systemd-journald.service

journalctl --disk-usage | tee 01-disk-usage.txt
```

**Human-Readable Breakdown:** Become root for consistent permissions, create a working directory under `/root`, confirm the binary is on `PATH`, print its version, prove the daemon is running, and record how much disk the journal is consuming.

**Reading it left to right:** `which` proves `journalctl` is on `PATH`. `--version` confirms the systemd version (RHEL 9 ships v252 or newer). `systemctl is-active` returns `active` for a running daemon. `--disk-usage` is the cheapest way to measure how much journal data you have to query.

**The story:** The journal is **always** active in modern RHEL — even when `/var/log/journal` does not exist (so the store is volatile in `/run`), `journalctl` still works. `--disk-usage` is a quick sanity check: a fresh cloud VM might report 8.0M while a long-running host reports 1.0G. The difference tells you how many boots of history you can query.

**Expected output:**

```text
/usr/bin/journalctl
systemd 252 (252-32.el9_4)
active
Archived and active journals take up 56.0M in the file system.
```

**Switches**

| Token | Meaning |
|---|---|
| `which CMD` | First match on `PATH` |
| `journalctl --version` | systemd version |
| `systemctl is-active UNIT` | `active`/`inactive`/`failed` |
| `journalctl --disk-usage` | Total bytes consumed by the journal |
| `tee FILE` | Duplicate stdout into a file |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `command not found: journalctl` | `dnf install systemd` (should already be present) |
| `inactive` daemon | `systemctl start systemd-journald.service` |
| `Failed to get bus connection` | Run as root or with `sudo` |
| `--disk-usage` reports a few megabytes only | Volatile journal — see Lab 102 for persistence |

---

### Task 2 — Read recent logs and learn the default invocation

**Purpose:** See what `journalctl` returns with no filters, learn pager behavior, and capture the last 50 lines for the artifact set.

```bash
cd /root/journal-lab

journalctl --no-pager | tail -n 20 | tee 02-default-tail20.txt
journalctl -n 50 --no-pager | tee 02-last50.txt
journalctl -r --no-pager | head -n 10 | tee 02-newest-first.txt
```

**Human-Readable Breakdown:** Print the journal without a pager (so `tail`/`head` work), then ask for explicit "last 50 entries" with `-n 50`, then ask for reverse order so the newest line is line 1.

**Reading it left to right:** `--no-pager` disables the `less`-like pager so stdout flows into the pipe. `tail -n 20` keeps the bottom 20 lines of the natural (oldest → newest) order. `-n 50` is the `journalctl`-native way to get the last 50 (works inside scripts). `-r` reverses the whole stream so `head -n 10` returns the **10 newest** entries — which is what you usually want.

**The story:** Without `--no-pager`, `journalctl` will hand its output to `less` and your pipe never sees it. Newcomers think the command "did nothing" because they hit `q` to escape the pager. Always remember `--no-pager` when scripting. `-r` + `head` is the classic pattern for "what just happened?"

**Expected output (excerpt):**

```text
Jan 14 09:01:11 host1 sshd[1820]: Accepted publickey for root from 10.0.0.5 port 51422 ssh2
Jan 14 09:01:11 host1 systemd[1]: Started Session 7 of User root.
Jan 14 09:01:11 host1 systemd-logind[932]: New session 7 of user root.
... 17 more lines ...
Jan 14 09:01:11 host1 systemd-logind[932]: New session 7 of user root.
Jan 14 09:01:11 host1 systemd[1]: Started Session 7 of User root.
Jan 14 09:01:11 host1 sshd[1820]: Accepted publickey for root from 10.0.0.5 port 51422 ssh2
... 7 more reverse lines ...
```

**Switches**

| Token | Meaning |
|---|---|
| `--no-pager` | Disable interactive pager |
| `-n N` | Print last N entries (analogous to `tail -n`) |
| `-r` | Reverse — newest first |
| `head -n N` | First N lines (used after `-r` for newest-N) |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Command appears to hang | You hit the pager — press `q`, then add `--no-pager` |
| `-n 50` returns less than 50 | Volatile journal is small — proceed anyway |
| Output is identical with and without `-r` | Single-line buffer — try a wider range |

---

### Task 3 — Filter by unit with `-u`

**Purpose:** Restrict output to one specific unit and learn how to combine multiple units.

```bash
cd /root/journal-lab

journalctl -u sshd.service --no-pager -n 20 | tee 03-sshd-tail.txt
journalctl -u sshd.service -u systemd-logind.service --no-pager -n 30 | tee 03-sshd-and-logind.txt
journalctl -u 'systemd-*' --no-pager -n 20 | tee 03-systemd-glob.txt
```

**Human-Readable Breakdown:** Filter to just `sshd.service`, then to two units at once by repeating `-u`, then use a glob pattern (`systemd-*`) to capture every unit starting with `systemd-`.

**Reading it left to right:** `-u sshd.service` matches the unit name exactly. Repeating `-u UNIT` combines filters with OR semantics — every line is from at least one of those units. The single-quoted glob `'systemd-*'` is expanded by `journalctl`, not by the shell — so you must quote it to prevent shell globbing against current-directory filenames.

**The story:** `-u` is the single most powerful filter. Real triage starts with "which service?" and `-u UNIT` is how you ask. Globs are useful for "everything systemd-related" or "every getty" without typing each name. Note: `-u` matches the unit, not the executable — so `journalctl -u sshd` catches all sshd lines, but `journalctl /usr/sbin/sshd` catches only those tagged with that exe.

**Expected output (excerpt):**

```text
Jan 14 09:01:11 host1 sshd[1820]: Accepted publickey for root from 10.0.0.5 port 51422 ssh2
Jan 14 09:01:11 host1 sshd[1820]: pam_unix(sshd:session): session opened for user root(uid=0)
Jan 14 09:00:33 host1 sshd[1801]: Server listening on 0.0.0.0 port 22.
Jan 14 09:00:33 host1 sshd[1801]: Server listening on :: port 22.
...
```

**Switches**

| Token | Meaning |
|---|---|
| `-u UNIT` | Filter to one unit |
| `-u UNIT -u UNIT2` | OR multiple units |
| `-u 'GLOB*'` | Glob match (quote to protect from shell) |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| No output | Unit name typo — list with `systemctl list-units --type=service` |
| Returns too much | Add `-p err` or `--since today` |
| Glob expands in shell to filenames | Single-quote the pattern |

---

### Task 4 — Filter by priority with `-p` (and the range form)

**Purpose:** Narrow output to entries at or above a severity floor, and learn the range form for a single priority.

```bash
cd /root/journal-lab

journalctl -p err --no-pager -n 20 | tee 04-err-and-worse.txt
journalctl -p warning..err --no-pager -n 20 | tee 04-warn-to-err.txt
journalctl -p err..emerg --no-pager -n 20 | tee 04-err-to-emerg.txt
journalctl -p 3 --no-pager -n 5 | tee 04-numeric-3.txt
```

**Human-Readable Breakdown:** Use `-p err` to get error and worse, then ranges to get exact bands, then prove that numeric priorities (0–7) work identically.

**Reading it left to right:** `-p err` means "priority `err` (3) or **lower number** (more severe)" — so you get `err`, `crit`, `alert`, `emerg`. `-p warning..err` is an inclusive range from priority 4 to 3 — so just `warning` and `err`. Numeric is equivalent: `-p 3` == `-p err`.

**The story:** This is the single biggest **gotcha** of `journalctl`: `-p err` is **not "only errors"** — it is **"errors and worse."** If you want only `err` and not `crit`, use the range form `-p err..err`. Examiners love this question because it tests whether you've read the man page.

**Expected output (excerpt):**

```text
Jan 14 08:55:02 host1 sssd[be[implicit_files]][1023]: Could not connect: Connection refused
Jan 14 08:50:11 host1 systemd[1]: cups.service: Failed with result 'exit-code'.
Jan 14 08:50:11 host1 systemd[1]: cups.service: Main process exited, code=exited, status=1/FAILURE
...
```

**Switches**

| Token | Meaning |
|---|---|
| `-p err` | Errors and worse (`err`, `crit`, `alert`, `emerg`) |
| `-p N..M` | Inclusive priority range |
| `-p 3` | Numeric equivalent of `err` |
| `0..7` | `emerg=0` → `debug=7` |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| No output at `-p err` | Healthy system or short journal — try `--since yesterday` |
| `-p warning` returns crit/err too | Expected — use range `warning..warning` |
| Range syntax rejected | systemd too old — RHEL 7 needs the modern syntax `-p warning..err` (works from systemd v210+) |

---

### Task 5 — Bound a time window with `--since` and `--until`

**Purpose:** Restrict output to a specific timeframe using human-friendly and ISO 8601 forms.

```bash
cd /root/journal-lab

journalctl --since "today" --no-pager -n 10 | tee 05-since-today.txt
journalctl --since "1 hour ago" --no-pager -n 10 | tee 05-since-1h.txt
journalctl --since "yesterday" --until "today" --no-pager | head -n 10 | tee 05-yesterday-window.txt
journalctl --since "$(date -u -d '15 minutes ago' '+%Y-%m-%d %H:%M:%S')" --no-pager -n 10 | tee 05-iso-window.txt
```

**Human-Readable Breakdown:** Use "today" (midnight to now), "1 hour ago" (relative offset), an explicit `--since`/`--until` window, and finally a programmatic ISO 8601 timestamp from `date -d`.

**Reading it left to right:** `--since "today"` means "today's local midnight." `--since "1 hour ago"` is a relative offset. `--since "yesterday" --until "today"` is a closed window — yesterday midnight to today's midnight. `date -u -d '15 minutes ago' ...` produces a UTC ISO timestamp; pair `--since` with ISO when you need second-level precision.

**The story:** Time filtering is what makes incident timelines work. **"Show me everything between 03:00 and 03:15 from yesterday"** is one `--since "yesterday 03:00" --until "yesterday 03:15"`. Most other log tools require timestamp grep + awk. `journalctl` parses these strings natively.

**Expected output:**

```text
Jan 14 00:01:11 host1 systemd-tmpfiles[2310]: ...
Jan 14 00:01:13 host1 systemd[1]: systemd-tmpfiles-clean.service: Succeeded.
...
```

**Switches**

| Token | Meaning |
|---|---|
| `--since "today"` | Today at 00:00 |
| `--since "yesterday"` | Yesterday at 00:00 |
| `--since "N hour(s) ago"` | Relative offset |
| `--since "YYYY-MM-DD HH:MM:SS"` | Explicit ISO |
| `--until` | Same syntax, upper bound |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Failed to parse timestamp` | Quote the string — the space matters |
| Window returns nothing | Clock is off — `timedatectl status` |
| ISO ignored | Use the form `YYYY-MM-DD HH:MM:SS` without `T` |

---

### Task 6 — Limit to the current and previous boot with `-b` and `--list-boots`

**Purpose:** Filter by boot index and prove `journalctl` remembers prior boots when persistence is on.

```bash
cd /root/journal-lab

journalctl --list-boots | tee 06-list-boots.txt
journalctl -b --no-pager -n 5 | tee 06-current-boot-tail5.txt
journalctl -b -0 --no-pager -n 5 | tee 06-b0-tail5.txt
journalctl -b -1 --no-pager -n 5 2>&1 | tee 06-b-prev-tail5.txt
journalctl -b -p err --no-pager | tee 06-current-boot-errors.txt
```

**Human-Readable Breakdown:** List every boot the journal still remembers (with offsets and boot IDs), then look at the most recent five lines for the current boot, then the previous boot. End with the practical combination: "errors on the current boot."

**Reading it left to right:** `--list-boots` prints a table of offset/boot-id/first-time/last-time — useful for picking a boot to query. `-b` defaults to `-b 0` (the current boot). `-b -1` is the previous boot. `-b -1` returns nothing on volatile journals — that is a feature, not a bug, and the cue to do Lab 102.

**The story:** Boot filtering is what makes "did this fail before this reboot?" tractable. On a host with a persistent journal, `-b -1` shows the last shutdown sequence — usually where the problem was. Without persistence, the journal forgets every reboot, so combine this lab with Lab 102.

**Expected output (excerpt):**

```text
-2 9e1ad2e8d6e54b6cb9d1f2bf8cb52f01 Mon 2026-01-13 08:00:11 EST—Mon 2026-01-13 18:42:55 EST
-1 ab8c87d1a47749d2bd9e1c3a85ce9f00 Mon 2026-01-13 18:43:11 EST—Tue 2026-01-14 07:20:01 EST
 0 c0d911f2b56a4f5cb0e2a1f9b7c63d22 Tue 2026-01-14 07:20:33 EST—Wed 2026-01-14 09:42:55 EST
```

**Switches**

| Token | Meaning |
|---|---|
| `--list-boots` | All known boots with offsets |
| `-b` / `-b 0` | Current boot |
| `-b -1` | Previous boot |
| `-b BOOT_ID` | Boot by full ID |
| `-b -N -p err` | Errors only, on boot N back |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `--list-boots` shows only one boot | No persistence — Lab 102 |
| `-b -1` returns "No such boot" | Same — volatile journal |
| Wrong number of boots remembered | Tune `MaxRetentionSec` in `journald.conf` |

---

### Task 7 — Tail the journal in real time with `-f`

**Purpose:** Use follow mode to watch new entries land — the systemd equivalent of `tail -f /var/log/messages`.

```bash
cd /root/journal-lab

journalctl -u sshd.service -f --no-pager &
JOBPID=$!
sleep 2

# Generate one fresh sshd log entry, in a way safe in any lab
logger -p auth.notice -t sshd-test "journalctl follow demo $(date -Iseconds)"
sleep 2

kill $JOBPID 2>/dev/null
wait $JOBPID 2>/dev/null

journalctl -t sshd-test --no-pager | tee 07-follow-evidence.txt
```

**Human-Readable Breakdown:** Start `journalctl -f` filtered to `sshd.service` in the background, write a fake `sshd-test` log line via `logger`, then prove the entry made it into the journal (we use the `-t` tag filter at the end since `logger` does not actually attach to `sshd.service`).

**Reading it left to right:** `&` backgrounds the follow. `$!` captures the PID so we can kill it later. `logger -p PRI -t TAG MSG` is the simplest way to inject a journal entry from the shell. `-t TAG` then `-t sshd-test` filters the journal by the `SYSLOG_IDENTIFIER` we used.

**The story:** `-f` is the everyday SRE habit — you start it in one tmux pane and watch incidents land in real time. Pair it with `-u UNIT` and `-p err` to make a focused alert pane: `journalctl -u httpd -p err -f`. To exit, `Ctrl+C`.

**Expected output:**

```text
Jan 14 09:43:01 host1 sshd-test[2842]: journalctl follow demo 2026-01-14T09:43:01-05:00
```

**Switches**

| Token | Meaning |
|---|---|
| `-f` | Follow — print new entries as they arrive |
| `&` | Background the command in the shell |
| `logger -p auth.notice -t TAG MSG` | Inject a journal entry from userspace |
| `-t TAG` | Filter by `SYSLOG_IDENTIFIER` |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Nothing arrives | The unit is idle — generate traffic |
| Background process won't die | `kill -9 $JOBPID` |
| `logger: command not found` | `dnf install util-linux` (should already be present) |

---

### Task 8 — Add explanation messages with `-x` (and the `-xe` shortcut)

**Purpose:** Render the **catalog** text that systemd ships with each well-known message — designed for "what does this error mean?" triage.

```bash
cd /root/journal-lab

journalctl -p err -x --no-pager -n 30 | tee 08-explained-errors.txt
journalctl -xe --no-pager | tail -n 40 | tee 08-xe-recent.txt
journalctl --catalog --no-pager | head -n 5 | tee 08-catalog-header.txt
```

**Human-Readable Breakdown:** Show errors with `-x` (catalog explanations interleaved), use the popular `-xe` shortcut for "explain + jump to end," and finally peek at the catalog header to see what `-x` is consuming.

**Reading it left to right:** `-x` adds catalog hints (paragraphs of text from `journal-catalog(7)`) below recognized messages. `-xe` is `--catalog --pager-end` — open the pager at the bottom. `--catalog` is the long form of `-x`. The catalog ships in `/usr/lib/systemd/catalog/`.

**The story:** `journalctl -xe` is the #1 instruction in `systemctl status` failure output: "See `systemctl status NAME.service` and `journalctl -xeu NAME.service` for details." The `-x` hints often quote the upstream doc that mentions the actual exit code or behavior. They are not always useful, but when present, they save 10 minutes of Googling.

**Expected output (excerpt):**

```text
Jan 14 08:50:11 host1 systemd[1]: cups.service: Main process exited, code=exited, status=1/FAILURE
-- Subject: Unit failed
-- Defined-By: systemd
-- Support: https://access.redhat.com/support
--
-- The unit cups.service has entered the 'failed' state with result 'exit-code'.
```

**Switches**

| Token | Meaning |
|---|---|
| `-x` / `--catalog` | Append catalog explanations |
| `-xe` | `--catalog` + jump to end of pager |
| `-xeu UNIT` | `-x` + `-e` + `-u UNIT` |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| No `-- Subject:` blocks | Message has no catalog entry — normal |
| `--catalog` unknown | systemd too old |
| `-xe` flips to the pager | Add `--no-pager` if scripting |

---

### Task 9 — Control output format and access structured fields with `-o`

**Purpose:** Render entries in JSON for scripts, in `cat` for clean text, and learn how to filter by structured fields (`_PID`, `_UID`, `_SYSTEMD_UNIT`).

```bash
cd /root/journal-lab

journalctl -u sshd.service -n 3 -o short-iso --no-pager | tee 09-short-iso.txt
journalctl -u sshd.service -n 3 -o cat --no-pager | tee 09-cat.txt
journalctl -u sshd.service -n 1 -o json-pretty --no-pager | tee 09-json-pretty.txt
journalctl _PID=1 -n 5 --no-pager | tee 09-pid1.txt
journalctl _SYSTEMD_UNIT=sshd.service -n 5 --no-pager | tee 09-field-filter.txt
journalctl /usr/sbin/sshd -n 5 --no-pager 2>&1 | tee 09-exec-filter.txt
```

**Human-Readable Breakdown:** Render the same entries in three formats — `short-iso` for ISO timestamps, `cat` for message-only output (great for pipes), and `json-pretty` for scripts. Then filter by structured fields: PID 1, the `sshd.service` unit field, and the absolute path to the executable.

**Reading it left to right:** `-o short-iso` swaps the default syslog timestamp for ISO 8601. `-o cat` drops every field except `MESSAGE`. `-o json-pretty` emits one JSON object per entry, formatted for humans. `_PID=1` filters to entries whose process ID was 1 (systemd). `_SYSTEMD_UNIT=sshd.service` is the structured-field equivalent of `-u sshd.service`. An absolute path filters by the executable that produced the entry.

**The story:** JSON output is the bridge between `journalctl` and any modern log pipeline — ship it to Loki, Splunk, Datadog, anything. Field filters are how scripts ask precise questions without parsing free-form text. Memorize `_PID`, `_UID`, `_SYSTEMD_UNIT`, `SYSLOG_IDENTIFIER`, `MESSAGE`, `PRIORITY`, `_BOOT_ID`, `_COMM` (process name).

**Expected output (excerpt):**

```text
2026-01-14T09:01:11-0500 host1 sshd[1820]: Accepted publickey for root from 10.0.0.5 port 51422 ssh2
Accepted publickey for root from 10.0.0.5 port 51422 ssh2
{
    "__CURSOR" : "s=...",
    "__REALTIME_TIMESTAMP" : "1736866871123456",
    "_PID" : "1820",
    "_UID" : "0",
    "_SYSTEMD_UNIT" : "sshd.service",
    "SYSLOG_IDENTIFIER" : "sshd",
    "MESSAGE" : "Accepted publickey for root from 10.0.0.5 port 51422 ssh2",
    "PRIORITY" : "6"
}
```

**Switches**

| Token | Meaning |
|---|---|
| `-o short-iso` | Default + ISO timestamps |
| `-o cat` | `MESSAGE` only — strip metadata |
| `-o verbose` | Every field on its own line |
| `-o json` | One JSON object per line |
| `-o json-pretty` | Pretty-printed JSON |
| `FIELD=value` | Field filter (any structured key) |
| `/abs/path` | Filter by executable path |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `-o json` produces nothing | No matches — drop the filters and retry |
| Field name unknown | `journalctl -o verbose -n 1` to list every field |
| Lower-case vs underscore confusion | Trusted-source fields are prefixed with `_` (kernel can't be forged); user fields are not |

---

### Task 10 — Capstone: investigate `sshd` errors since yesterday on the current boot, in JSON

**Task statement:** *"Capture every error-or-worse log message produced by the `sshd` service since yesterday, on the current boot, in JSON format. Write a one-paragraph summary to `/root/journal-lab/10-sshd-incident.txt` citing the timestamp of the first event and the total count, then clean up every artifact this lab created."*

**Purpose:** Combine every prior task into a single multi-filter invocation, build a report, and remove every artifact.

```bash
cd /root/journal-lab

journalctl \
  -u sshd.service \
  -p err \
  --since "yesterday" \
  -b \
  -o json \
  --no-pager > 10-sshd-incident.json

COUNT=$(wc -l < 10-sshd-incident.json)
FIRST_TS=$(head -n 1 10-sshd-incident.json | grep -oE '"__REALTIME_TIMESTAMP"[^"]*"[0-9]+"' | grep -oE '[0-9]+' || echo "")
FIRST_HUMAN=""
if [ -n "$FIRST_TS" ]; then
  FIRST_HUMAN=$(date -d @$((FIRST_TS / 1000000)) -Iseconds 2>/dev/null)
fi

cat > 10-sshd-incident.txt <<EOF
sshd incident summary — $(hostname) — $(date -Iseconds)

Query: journalctl -u sshd.service -p err --since "yesterday" -b -o json
Total matching JSON entries: ${COUNT}
First event timestamp (ISO):  ${FIRST_HUMAN:-none}

Notes:
  - 'priority err' includes err, crit, alert, emerg (Task 4 gotcha).
  - '-b' restricts to the current boot — to query the previous boot use '-b -1'
    after enabling persistent journals (see Lab 102).
  - JSON output is one object per line — '__REALTIME_TIMESTAMP' is microseconds since epoch.
EOF

cat 10-sshd-incident.txt
```

**Human-Readable Breakdown:** Build the canonical "errors on sshd since yesterday on this boot, as JSON" command. Count matching entries with `wc -l`. Parse the first event's microsecond timestamp out of the JSON, convert to ISO. Write a self-contained text report. Finally, clean up.

**Layer stack you built:**

```text
10-sshd-incident.txt   ← the deliverable a reader will consume
  ├── 10-sshd-incident.json   ← raw JSON evidence
  ├── 03-sshd-tail.txt        ← which unit we focused on
  ├── 04-err-and-worse.txt    ← which priority floor
  ├── 05-since-today.txt      ← which time window
  └── 06-current-boot-errors.txt ← which boot
```

**The story:** This pattern is the entire reason `journalctl` exists. Five filters — unit, priority, since, boot, format — combine into one safe, scriptable query that answers a real engineer question. The `wc -l` count gives a single number a manager can quote. The ISO timestamp is the timeline anchor for an incident report.

**Expected verification output:**

```text
sshd incident summary — host1 — 2026-01-14T09:55:12-05:00

Query: journalctl -u sshd.service -p err --since "yesterday" -b -o json
Total matching JSON entries: 0
First event timestamp (ISO):  none

Notes:
  - 'priority err' includes err, crit, alert, emerg (Task 4 gotcha).
  - '-b' restricts to the current boot — to query the previous boot use '-b -1'
    after enabling persistent journals (see Lab 102).
  - JSON output is one object per line — '__REALTIME_TIMESTAMP' is microseconds since epoch.
```

**Cleanup**

```bash
cd /root
rm -rf /root/journal-lab
ls -ld /root/journal-lab 2>&1 | head -n 1
exit
```

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `wc -l` reports 0 but you expected errors | Healthy system — try a longer window with `--since "3 days ago"` |
| `__REALTIME_TIMESTAMP` missing | You used `-o cat` — switch to `-o json` |
| `date -d @SECONDS` returns wrong year | You forgot the `/ 1000000` division (microseconds vs seconds) |
| `rm -rf` complains about open files | `cd` out of the lab dir first |

---

## 🔍 Journal Triage Decision Guide

```
"What went wrong?"
  │
  ├── "I don't know which service yet"
  │       └── ✅ journalctl -p err -b --no-pager | head
  │
  ├── "It's this service — sshd"
  │       └── ✅ journalctl -u sshd.service -p err --no-pager
  │
  ├── "It happened around 03:42 this morning"
  │       └── ✅ journalctl -u UNIT --since "03:30" --until "03:50"
  │
  ├── "It happened before this reboot"
  │       └── ✅ journalctl -u UNIT -b -1 -p err
  │             (requires persistent journal — Lab 102)
  │
  ├── "I want to watch it as it happens"
  │       └── ✅ journalctl -u UNIT -f
  │
  ├── "I need to ship this to Loki/Splunk"
  │       └── ✅ journalctl -u UNIT -o json
  │
  └── "I want the cryptic systemd error explained"
          └── ✅ journalctl -xeu UNIT
```

---

## ✅ Lab Checklist (10 Tasks)

- [ ] 01 Set up `/root/journal-lab` and capture `--disk-usage`
- [ ] 02 Default invocation, `-n`, `-r`, `--no-pager`
- [ ] 03 Filter by unit with `-u` (and globs / multi-unit)
- [ ] 04 Filter by priority with `-p` (including range form)
- [ ] 05 Bound by time with `--since`/`--until`
- [ ] 06 Limit to a boot with `-b` and inspect `--list-boots`
- [ ] 07 Tail in real time with `-f` (and inject with `logger`)
- [ ] 08 Add catalog explanations with `-x` / `-xe`
- [ ] 09 Render `-o short-iso`, `-o cat`, `-o json-pretty`, and field filters
- [ ] 10 Capstone JSON capture + report + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Forgetting `--no-pager` in scripts | Output never appears | Always `--no-pager` in pipes |
| Believing `-p err` is "only err" | Missing crit/alert/emerg events | It is `err and worse` — use `-p err..err` for only-err |
| Using `-b -1` without persistence | "No such boot" error | Enable `/var/log/journal` (Lab 102) |
| `tail -f /var/log/messages` for journald-only entries | Some entries never reach rsyslog | Use `journalctl -f` |
| Unquoted glob to `-u` | Shell expands to local filenames | Single-quote `'unit-*'` |
| Confusing `_PID` with `PID` | Field filter returns nothing | Use the underscore-prefixed trusted field |
| Mixing `--since "Jan 14 09:00"` and locale | Parser rejects | Use `YYYY-MM-DD HH:MM:SS` |
| Using `journalctl -k` for service errors | Returns kernel only | Drop `-k`, use `-u` |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- Memorize the four big filters: `-u`, `-p`, `--since`, `-b`. Exam tasks like "show me sshd errors from this morning" are one-liners.

**RHCE candidate**
- In Ansible: `command: journalctl -u {{ unit }} -p err --since "1 hour ago" -o json` with `register: log` and `failed_when: log.stdout_lines | length > 0` is the idempotent "no new errors" gate.

**SRE / Platform interview**
- Be ready to explain why `journalctl` is not a syslog file. The expected answer covers structured fields, boot-aware indexing, and JSON.

**DevOps**
- CI debug pattern: `journalctl -u build.service -b -p warning --no-pager > build.log` is your "last 5 minutes of the runner" artifact.

**AI / MLOps**
- `journalctl -u training.service -o json --since "$(date -d '30 min ago' -Iseconds)"` feeds an incident pipeline that triages CUDA OOM, NCCL timeouts, and DataLoader stalls.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 100 — `systemd-analyze` Boot Performance | Pairs with `journalctl -b -p err` after a slow boot |
| Lab 102 — Persistent Journal Logs | Enables `-b -1` for prior-boot queries |
| Lab 103 — Understand Log Routing (`/etc/rsyslog.conf`) | Where `journalctl` and rsyslog diverge |
| Lab 104 — Monitor Authentication Logs (`/var/log/secure`) | rsyslog twin of `journalctl -u sshd` |
| Lab 105 — Filter Journals by Priority | Deep dive on `-p` numeric/range forms |
| Lab 106 — Service-Specific Journal Logs | Deep dive on `-u UNIT` |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
