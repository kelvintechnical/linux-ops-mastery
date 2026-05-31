# Lab: Monitor Authentication Logs — `/var/log/secure`, `last`, `lastb`, `lastlog`, `aulast`, `journalctl _COMM=sshd`

- **Series:** linux-ops-mastery — RHCSA Log Management
- **Subjects covered:** the `authpriv` syslog facility, `/var/log/secure` line grammar (sshd Accepted/Failed, sudo COMMAND, su BAD SU, login PAM messages), `last` (current successful logins from `/var/log/wtmp`), `lastb` (failed login attempts from `/var/log/btmp`), `lastlog` (per-user last login time from `/var/log/lastlog`), `aulast` (audit-driven login history), correlating `/var/log/secure` with `journalctl _SYSTEMD_UNIT=sshd.service`, grep regexes for "failed password from", `tail -F` for live watching, log rotation in `/etc/logrotate.d/syslog`, IP and username extraction with `awk`/`grep -oP`, building a brute-force candidate list, threshold alert via `wc -l`
- **Career arcs covered:** RHCSA (EX200 — "find when user foo last logged in"), RHCE (Ansible report job), SRE (intrusion candidate triage), DevOps (CI runner auth audit), AI / MLOps (multi-user shared GPU host auth review)
- **Prerequisite:** Labs 101–103
- **Time Estimate:** 35 to 50 minutes
- **Difficulty arc:** Tasks 1–2 baseline (file location, permissions) · Tasks 3–4 read sshd Accepted vs Failed lines · Task 5 sudo / su lines · Tasks 6–7 `last`, `lastb`, `lastlog` triad · Task 8 correlate with journalctl · Task 9 brute-force candidate report · Task 10 capstone summary + safe cleanup

---

## Objective

Stop reading raw log files line by line. By the end of this lab you can answer **"who logged in (or tried) on this host, from where, when, and was it successful?"** in three commands. You will read `/var/log/secure` fluently, run the `last`/`lastb`/`lastlog` triad without looking up syntax, cross-reference with `journalctl`, and produce a brute-force candidate list ranked by failed-attempt count.

The capstone is the **engineer-realistic prompt:** *"Audit authentication activity on this RHEL 9 host over the last 24 hours. List the top 5 source IPs by failed-password attempts, the most recent 5 successful root logins, and the per-user last-login table. Write a one-paragraph security summary."*

> **Lab safety note:** This lab only reads existing logs and writes a report. It does not modify accounts, lock users, or change firewall rules.

---

## Concept: `authpriv` Goes to `/var/log/secure`, Period

When `sshd`, `sudo`, `su`, `login`, `pam_unix`, or any PAM-aware service logs a message, it tags the message with the `authpriv` facility (or sometimes `auth` for very old apps). The default RHEL rsyslog rule is:

```
authpriv.*    /var/log/secure
```

So **every** authentication event lands in `/var/log/secure`. Failed sshd password attempts, successful key logins, sudo invocations, `su` to root — all of it. This is the file every security audit starts with.

```
   ┌─────────────────────────────────────────────────────────────┐
   │  sshd  ──┐                                                  │
   │  sudo  ──┤                                                  │
   │  su    ──┼──► syslog(LOG_AUTHPRIV, ...)  ──► /var/log/secure │
   │  login ──┤                                                  │
   │  PAM   ──┘                                                  │
   │                                                             │
   │  Companion files (parallel sources of truth):               │
   │     /var/log/wtmp     ← binary; read with 'last'            │
   │     /var/log/btmp     ← binary, failed logins; 'lastb'      │
   │     /var/log/lastlog  ← per-user last login; 'lastlog'      │
   │     audit log         ← /var/log/audit/audit.log; 'aulast'  │
   └─────────────────────────────────────────────────────────────┘
```

> **Why this matters:** Most successful-login questions can be answered with `last`. Most failed-attempt questions can be answered with `lastb` or `grep "Failed password" /var/log/secure`. RHCSA exam tasks pattern-match these three sources of truth.

---

## 📜 Why `/var/log/secure` Exists — The Story

Unix `syslog` reserved two facilities for authentication: `auth` and `authpriv`. The difference is **read permissions** on the resulting file. `auth` is world-readable on some BSDs; `authpriv` is **restricted** — owner `root`, group `root`, mode `600` — so non-root users cannot see other users' login attempts (which would leak usernames, IPs, and timing).

When Linux distros standardized, **RHEL/CentOS/Fedora** routed `authpriv.*` to `/var/log/secure`; **Debian/Ubuntu** routed `auth,authpriv.*` to `/var/log/auth.log`. Different filename, same purpose. Both are mode `600`, owned by `root`.

Meanwhile, the **utmp/wtmp/btmp** family is a parallel-but-different log of *who is, was, and tried to be* logged in, in a binary format read by `who`, `w`, `last`, `lastb`. `/var/log/lastlog` is a third file, per-user indexed, read by `lastlog`. The three are kept separate because they answer slightly different questions.

> **The point of the story:** RHCSA exam questions test whether you know **which file/tool** answers a given question. You will not have time to read raw text — you must reach for `last`, `lastb`, or `lastlog` instinctively.

---

## 👪 The Auth-Log Family — Who Lives Where

```
Text logs
└── /var/log/secure         ← sshd, sudo, su, login, PAM messages (rsyslog rule)

Binary records (utmp family)
├── /var/run/utmp            ← who is logged in NOW          (read by who, w)
├── /var/log/wtmp            ← successful login history       (read by last)
├── /var/log/btmp            ← failed-login history           (read by lastb)
└── /var/log/lastlog          ← per-user last login            (read by lastlog)

Audit subsystem (separate from syslog)
├── /var/log/audit/audit.log ← every USER_LOGIN / USER_AUTH event
├── ausearch                  ← query audit log
├── aulast                    ← like 'last', but driven by audit records
└── auditctl                 ← audit rules

journald
├── journalctl -u sshd.service   ← same data, indexed
├── journalctl _COMM=sshd        ← every sshd process, even subprocesses
└── journalctl _UID=N -p notice  ← per-uid activity
```

### `/var/log/secure` line shapes you must recognize

| Shape | What it means |
|---|---|
| `Accepted publickey for USER from IP port PORT ssh2: KEYTYPE FP` | Successful key login |
| `Accepted password for USER from IP port PORT ssh2` | Successful password login |
| `Failed password for USER from IP port PORT ssh2` | Failed password (real user) |
| `Failed password for invalid user USER from IP port PORT ssh2` | Failed password (no such user) |
| `Invalid user USER from IP port PORT` | Username does not exist |
| `Disconnected from authenticating user USER IP port PORT [preauth]` | Connection dropped during auth |
| `sudo:   USER : TTY=...  PWD=... USER=root ; COMMAND=...` | sudo invocation |
| `su:  pam_unix(su:session): session opened for user root by USER(uid=N)` | su to root |
| `pam_unix(sshd:auth): authentication failure; ...` | PAM-level auth failure |

### Useful regex bites

| Goal | Regex / awk |
|---|---|
| Count failed passwords | `grep -c "Failed password" /var/log/secure` |
| List source IPs | `grep "Failed password" /var/log/secure \| grep -oE 'from [0-9.]+' \| sort \| uniq -c \| sort -rn` |
| Successful key logins | `grep "Accepted publickey" /var/log/secure` |
| sudo commands by user | `grep " sudo:" /var/log/secure \| awk '{print $5,$6}' \| sort \| uniq -c \| sort -rn` |

---

## 📚 Auth-Log Reference Table

| Goal | Command | Notes |
|---|---|---|
| All current logins | `who` | Reads `/var/run/utmp` |
| All current logins w/ load | `w` | Adds idle time + activity |
| Login history | `last` | Reads `/var/log/wtmp`, newest first |
| Last N logins | `last -n 10` | Limit count |
| Logins on a date | `last -s "2026-01-13 00:00"` | Time-bounded |
| Failed login history | `lastb` | Reads `/var/log/btmp` (root only) |
| Failed by user | `lastb \| grep USER` | Filter |
| Last login per user | `lastlog` | One row per account in `/etc/passwd` |
| Last login for one user | `lastlog -u USER` | Targeted |
| Audit-driven login table | `aulast` | Equivalent to `last`, uses audit records |
| sshd messages (live) | `tail -F /var/log/secure` | `-F` follows + reopens after rotation |
| sshd messages (journald) | `journalctl -u sshd.service` | Same data via index |
| sshd by process name | `journalctl _COMM=sshd` | Includes children |
| Errors only | `journalctl -u sshd.service -p err` | Per-priority |
| Today only | `journalctl -u sshd.service --since today` | Time-window |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | EX200 wording: "When did user X last log in?" → `lastlog -u X`. "How many failed logins happened today?" → `lastb` + grep. |
| **RHCE candidate** | Ansible: `command: lastb` + `register:` + report job that emails the count daily. |
| **SRE / Platform** | Brute-force candidate lists drive fail2ban / sshguard rules. |
| **DevOps** | Per-build auth audit on the runner before tearing down — proves no unauthorized SSH while build was active. |
| **AI / MLOps** | Shared GPU hosts with many users: `lastlog` shows who actually uses the box. |

---

## 🔧 The 10 Tasks

> Ten phases that build the **read /var/log/secure → last/lastb/lastlog → correlate with journald → produce IP/user reports** habit.

---

### Task 1 — Set up the sandbox and confirm `/var/log/secure` exists and is mode `0600`

**Purpose:** Build a scratch directory and capture the file metadata that proves rsyslog is doing its job.

```bash
sudo -i
mkdir -p /root/secure-lab && cd /root/secure-lab

ls -l /var/log/secure /var/log/wtmp /var/log/btmp /var/log/lastlog 2>/dev/null | tee 01-perms.txt
sudo wc -l /var/log/secure | tee 01-line-count.txt
```

**Human-Readable Breakdown:** Become root, create a workspace, list metadata for all four auth-related files in one call, and count `/var/log/secure` lines for the baseline.

**Reading it left to right:** `ls -l FILE FILE FILE` lists multiple files in one command. `2>/dev/null` suppresses errors if a file does not exist (some are not created until first use). `wc -l` counts lines.

**The story:** `/var/log/secure` must be mode `0600` owned by `root:root`. If it is world-readable, someone has bumped the permissions and you should reset them. `/var/log/wtmp` is mode `0664` (group `utmp` readable) so `last` works for normal users.

**Expected output:**

```text
-rw-------. 1 root root  12842 Jan 14 09:50 /var/log/secure
-rw-rw-r--. 1 root utmp   4992 Jan 14 09:50 /var/log/wtmp
-rw-------. 1 root utmp    768 Jan 14 09:00 /var/log/btmp
-rw-r--r--. 1 root root 291960 Jan 14 09:50 /var/log/lastlog
164
```

**Switches**

| Token | Meaning |
|---|---|
| `ls -l FILE...` | Long listing for multiple files |
| `wc -l FILE` | Count newline-terminated lines |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Permission denied` on `/var/log/secure` | Need `sudo` |
| File is mode `0644` | `sudo chmod 0600 /var/log/secure` |
| File missing | `systemctl restart rsyslog` and `logger -p authpriv.notice "test"` |

---

### Task 2 — Read recent successful and failed sshd lines

**Purpose:** Distinguish the four most common sshd line shapes by grep alone.

```bash
cd /root/secure-lab

sudo grep -E 'Accepted (password|publickey)' /var/log/secure | tail -n 5 | tee 02-accepted.txt
sudo grep -E 'Failed password' /var/log/secure | tail -n 5 | tee 02-failed.txt
sudo grep -E 'Invalid user' /var/log/secure | tail -n 5 | tee 02-invalid-user.txt
sudo grep -E 'Disconnected from authenticating' /var/log/secure | tail -n 5 | tee 02-disconnected.txt
```

**Human-Readable Breakdown:** Pull the last five lines of each of the four most common shapes — accepted, failed, invalid user, disconnected — and save them as artifacts.

**Reading it left to right:** `grep -E PATTERN FILE` uses extended regex; `|` is the alternation operator. `tail -n 5` keeps the newest five.

**The story:** This is the **first** lens you reach for in any auth audit. Before fancy reports, just *see* the shape of recent traffic. If `Failed password` is dominating the file, you have a brute-force candidate; if it is empty, the host is quiet.

**Expected output (excerpt):**

```text
Jan 14 09:01:11 host1 sshd[1820]: Accepted publickey for root from 10.0.0.5 port 51422 ssh2: ED25519 SHA256:xxxx
Jan 14 09:30:33 host1 sshd[2002]: Accepted password for kelvin from 10.0.0.6 port 52001 ssh2
Jan 14 09:32:11 host1 sshd[2010]: Failed password for kelvin from 198.51.100.7 port 60002 ssh2
Jan 14 09:32:12 host1 sshd[2010]: Failed password for invalid user admin from 198.51.100.7 port 60002 ssh2
Jan 14 09:32:13 host1 sshd[2010]: Invalid user admin from 198.51.100.7 port 60002
Jan 14 09:32:14 host1 sshd[2010]: Disconnected from authenticating user kelvin 198.51.100.7 port 60002 [preauth]
```

**Switches**

| Token | Meaning |
|---|---|
| `grep -E` | Extended regex |
| `grep -c` | Count matches |
| `tail -n N` | Last N lines |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `grep: /var/log/secure: Permission denied` | Use `sudo` |
| No `Accepted` lines | Single-user lab — log in via SSH first |
| Date format different | Locale — usually fine |

---

### Task 3 — Find sudo and su events

**Purpose:** Distinguish privilege-escalation lines from raw sshd lines and produce a sudo-by-user count.

```bash
cd /root/secure-lab

sudo grep ' sudo: ' /var/log/secure | tail -n 5 | tee 03-sudo-tail.txt
sudo grep ' su\[' /var/log/secure | tail -n 5 | tee 03-su-tail.txt

sudo grep ' sudo: ' /var/log/secure \
  | awk -F'[ :]+' '{print $5}' \
  | sort | uniq -c | sort -rn | tee 03-sudo-by-user.txt
```

**Human-Readable Breakdown:** Show recent sudo and su lines, then group sudo events by invoking username and rank by count.

**Reading it left to right:** `grep ' sudo: '` looks for the literal program name with spaces. `awk -F'[ :]+' '{print $5}'` splits on runs of spaces/colons and prints the 5th field, which is the invoking username. `sort | uniq -c | sort -rn` is the canonical "count and rank descending" pipeline.

**The story:** `sudo` lines are the audit trail for elevated commands. The user, target, TTY, working directory, and full command are all on one line. Pair with `journalctl -u sshd` for a per-session view.

**Expected output (excerpt):**

```text
Jan 14 09:35:22 host1 sudo:  kelvin : TTY=pts/0 ; PWD=/home/kelvin ; USER=root ; COMMAND=/bin/systemctl restart httpd
Jan 14 09:36:01 host1 su[2099]: pam_unix(su:session): session opened for user root by kelvin(uid=1000)
      4 kelvin
      1 ec2-user
```

**Switches**

| Token | Meaning |
|---|---|
| `awk -F'SEP'` | Field separator |
| `sort -rn` | Reverse numeric sort |
| `uniq -c` | Prefix unique lines with count |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Empty `03-sudo-by-user.txt` | Nobody used sudo — run `sudo whoami` to seed |
| `awk` returns numbers | Field separator wrong — adjust to `'-F[ :]+'` |

---

### Task 4 — Count failed-password attempts per source IP

**Purpose:** Produce the canonical brute-force candidate list.

```bash
cd /root/secure-lab

sudo grep 'Failed password' /var/log/secure \
  | grep -oE 'from [0-9.]+' \
  | awk '{print $2}' \
  | sort | uniq -c | sort -rn | head -n 10 | tee 04-top-failed-ips.txt
```

**Human-Readable Breakdown:** Take every `Failed password` line, extract the source IP via regex, sort and count, keep the top 10.

**Reading it left to right:** `grep 'Failed password'` filters lines. `grep -oE 'from [0-9.]+'` extracts only the matching `from IP` substring (`-o` = only). `awk '{print $2}'` keeps the IP. The count/sort pipeline ranks descending. `head -n 10` is the top 10.

**The story:** This is the single command every incident-responder runs first. If the top entry shows hundreds of failed attempts, you have a brute-force candidate. Hand it to firewalld / fail2ban / a security ticket.

**Expected output:**

```text
    412 198.51.100.7
     38 203.0.113.22
     12 10.0.0.99
      1 192.0.2.5
```

**Switches**

| Token | Meaning |
|---|---|
| `grep -o` | Only the matching substring |
| `-E` | Extended regex |
| `head -n N` | Top N lines |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Empty output | No failed logins (good) |
| IPs include port numbers | Refine to `from [0-9.]+ port` and adjust awk |

---

### Task 5 — `last` — successful login history from `/var/log/wtmp`

**Purpose:** Read the binary `/var/log/wtmp` with `last` for the canonical successful-login history.

```bash
cd /root/secure-lab

last -n 10 | tee 05-last-n10.txt
last -F | head -n 10 | tee 05-last-F.txt
last root | head -n 5 | tee 05-last-root.txt
last -s "yesterday" | head -n 10 | tee 05-last-since-yesterday.txt
```

**Human-Readable Breakdown:** Show the last 10 logins, then with full timestamps (`-F`), then filter to user `root`, then bound by time.

**Reading it left to right:** `last -n 10` limits to 10 entries. `-F` switches the timestamp format from "Tue Jan 14 09:01" to a fully-resolved date. `last USER` filters by username. `-s "yesterday"` includes only entries from yesterday onwards.

**The story:** `last` is faster than grepping `/var/log/secure` because the file is indexed. Use `last` for "did this user log in?" and `grep` only when you need lines for context.

**Expected output:**

```text
root     pts/0        10.0.0.5         Tue Jan 14 09:01   still logged in
kelvin   pts/1        10.0.0.6         Tue Jan 14 09:30 - 09:45  (00:15)
root     pts/0        10.0.0.5         Mon Jan 13 18:00 - 19:00  (01:00)
...
root     pts/0        10.0.0.5         Tue Jan 14 09:01:11 2026   still logged in
```

**Switches**

| Token | Meaning |
|---|---|
| `-n N` | Limit count |
| `-F` | Full timestamps |
| `-a` | Hostname column last (wider IPs) |
| `-s "DATE"` | Show since DATE |
| `-t "DATE"` | Show until DATE |
| `last USER` | Filter by user |
| `last TTY` | Filter by terminal |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `last: /var/log/wtmp: No such file` | Touch it: `sudo touch /var/log/wtmp` |
| Some users missing | rsyslog rotation cleared older history — see `/var/log/wtmp-*` |
| Times in UTC | `timedatectl status` to confirm |

---

### Task 6 — `lastb` — failed-login history from `/var/log/btmp`

**Purpose:** Read the failed-login binary log.

```bash
cd /root/secure-lab

sudo lastb -n 10 | tee 06-lastb-n10.txt
sudo lastb -F | head -n 10 | tee 06-lastb-F.txt
sudo lastb | awk '{print $3}' | sort | uniq -c | sort -rn | head -n 10 | tee 06-lastb-by-ip.txt
```

**Human-Readable Breakdown:** Show the last 10 failed logins, with full timestamps, then group by source IP (column 3 of the `lastb` output).

**Reading it left to right:** `lastb` requires root because `/var/log/btmp` is mode `0600`. The output columns mirror `last`: USER, TTY, FROM, TIME. The awk picks the third column.

**The story:** `lastb` is the complement to `last`. Both come from binary logs that PAM and login programs update directly — they are not parsed from `/var/log/secure`, so they capture events even if rsyslog is down.

**Expected output:**

```text
admin    ssh:notty    198.51.100.7     Tue Jan 14 09:32 - 09:32  (00:00)
root     ssh:notty    198.51.100.7     Tue Jan 14 09:32 - 09:32  (00:00)
...
    412 198.51.100.7
     38 203.0.113.22
```

**Switches**

| Token | Meaning |
|---|---|
| `lastb -n N` | Limit count |
| `-F` | Full timestamps |
| `-s` / `-t` | Time bounds |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `lastb: cannot open /var/log/btmp` | Run with `sudo` |
| `btmp begins ...` only | No failed logins (good) |
| Mismatch vs `/var/log/secure` | btmp is closer to truth — rsyslog can miss messages |

---

### Task 7 — `lastlog` — per-user last login

**Purpose:** One row per account in `/etc/passwd`, showing the most recent login time (or "Never").

```bash
cd /root/secure-lab

lastlog | head -n 20 | tee 07-lastlog-top20.txt
lastlog -u root | tee 07-lastlog-root.txt
lastlog -b 30 | tee 07-lastlog-before-30d.txt
lastlog -t 7 | tee 07-lastlog-within-7d.txt
```

**Human-Readable Breakdown:** Show the per-user table, then for one specific user, then for accounts that logged in **before** the last 30 days, then for those **within** the last 7 days.

**Reading it left to right:** `lastlog` reads `/var/log/lastlog`. `-u USER` filters by username. `-b N` shows logins **older** than N days. `-t N` shows logins **within** N days.

**The story:** `lastlog` is the inventory question: "who has actually used this box?" Accounts that show **"Never logged in"** are candidates for `usermod -L` or deletion. On a multi-user shared host, this is your monthly review tool.

**Expected output:**

```text
Username         Port     From             Latest
root             pts/0    10.0.0.5         Tue Jan 14 09:01:11 -0500 2026
bin                                       **Never logged in**
daemon                                    **Never logged in**
...
kelvin           pts/1    10.0.0.6         Tue Jan 14 09:30:33 -0500 2026
```

**Switches**

| Token | Meaning |
|---|---|
| `-u USER` | Single user |
| `-b N` | Older than N days |
| `-t N` | Within last N days |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `lastlog -t 7` empty | Nobody logged in this week |
| Wrong column count | Long usernames push columns — pipe through `column` |

---

### Task 8 — Correlate `/var/log/secure` with `journalctl -u sshd.service`

**Purpose:** Same data, two indexes. Pick the right one for the job.

```bash
cd /root/secure-lab

sudo grep 'sshd' /var/log/secure | tail -n 10 | tee 08-secure-sshd.txt
journalctl -u sshd.service --since today --no-pager | tee 08-journal-sshd.txt | head -n 10
journalctl _COMM=sshd --since today --no-pager | tail -n 10 | tee 08-journal-comm.txt

LINES_SECURE=$(sudo grep -c 'sshd' /var/log/secure)
LINES_JOURNAL=$(journalctl -u sshd.service --since today --no-pager | wc -l)
echo "secure: $LINES_SECURE   journal: $LINES_JOURNAL" | tee 08-count-compare.txt
```

**Human-Readable Breakdown:** Pull recent sshd lines from `/var/log/secure`, from the journal by unit, and from the journal by `_COMM=sshd` (which includes worker subprocesses). Then count each to see how the indexes compare.

**Reading it left to right:** `journalctl -u sshd.service` filters by systemd unit. `journalctl _COMM=sshd` filters by process command name — a superset since `sshd` forks per-connection. `grep -c` counts lines.

**The story:** rsyslog and journald see the same `authpriv` traffic but expose different filters. Use `/var/log/secure` for plain `grep` audits; use `journalctl` for time-bounded or priority-bounded queries.

**Expected output (excerpt):**

```text
Jan 14 09:30:33 host1 sshd[2002]: Accepted password for kelvin from 10.0.0.6 port 52001 ssh2
Jan 14 09:30:33 host1 sshd[2002]: pam_unix(sshd:session): session opened for user kelvin(uid=1000)
Jan 14 09:30:33 host1 systemd[1]: Started Session 12 of User kelvin.
secure: 24   journal: 28
```

**Switches**

| Token | Meaning |
|---|---|
| `journalctl -u UNIT` | Filter by systemd unit |
| `journalctl _COMM=NAME` | Filter by process command name |
| `--since today` | Today at 00:00 onward |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Counts very different | journald sees session/login lines from `systemd[1]` too |
| `_COMM=` returns nothing | Quote the name; it's `sshd` not `sshd.service` |

---

### Task 9 — Build a brute-force candidate report

**Purpose:** Produce a single text file ranking the top 5 source IPs by failed-password count, with the most recent attempt timestamp for each.

```bash
cd /root/secure-lab

sudo grep 'Failed password' /var/log/secure \
  | grep -oE 'from [0-9.]+' \
  | awk '{print $2}' \
  | sort | uniq -c | sort -rn | head -n 5 > 09-top5-ips-count.txt

cat 09-top5-ips-count.txt

> 09-top5-with-timestamps.txt
while read -r COUNT IP; do
  LAST=$(sudo grep "from ${IP} " /var/log/secure | grep 'Failed password' | tail -n 1 | awk '{print $1,$2,$3}')
  printf "%6s  %-15s  last: %s\n" "$COUNT" "$IP" "$LAST" >> 09-top5-with-timestamps.txt
done < 09-top5-ips-count.txt

cat 09-top5-with-timestamps.txt
```

**Human-Readable Breakdown:** First pipeline produces "count IP" pairs; the `while` loop walks those pairs and adds the most recent timestamp for each IP.

**Reading it left to right:** `read -r COUNT IP` assigns the first column to `COUNT` and the second to `IP`. `printf "%6s  %-15s  ..."` formats the output in fixed-width columns for readability. `tail -n 1` grabs the most recent matching line.

**The story:** This is the canonical "brute-force candidate" report — count, IP, last seen. Hand it to firewalld (`firewall-cmd --add-rich-rule='rule family=ipv4 source address=IP/32 drop'`) or fail2ban. On exam day, RHCSA tasks like "find the IP that tried the most failed logins" are this exact pipeline.

**Expected output:**

```text
    412 198.51.100.7
     38 203.0.113.22
     12 10.0.0.99
      1 192.0.2.5
   412  198.51.100.7    last: Jan 14 09:32:14
    38  203.0.113.22    last: Jan 14 03:11:00
    12  10.0.0.99       last: Jan 13 22:45:11
     1  192.0.2.5       last: Jan 12 10:00:33
```

**Switches**

| Token | Meaning |
|---|---|
| `read -r` | Read without backslash processing |
| `printf "%6s"` | Right-align width-6 |
| `printf "%-15s"` | Left-align width-15 |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Empty report | No `Failed password` in `/var/log/secure` (good) |
| Wrong timestamp parser | Adjust `awk '{print $1,$2,$3}'` to match locale |

---

### Task 10 — Capstone: 24-hour auth audit + cleanup

**Task statement:** *"Produce a one-paragraph security audit citing top 5 brute-force IPs, most recent 5 successful root logins, and the per-user last-login table over the last 24 hours."*

**Purpose:** Combine prior tasks into a single deliverable and clean up.

```bash
cd /root/secure-lab

TOP_IPS=$(cat 09-top5-with-timestamps.txt)
ROOT_LOGINS=$(last root -F | head -n 5)
USER_TABLE=$(lastlog -t 1)

cat > 10-audit-report.txt <<EOF
Auth audit — $(hostname) — last 24 hours — $(date -Iseconds)

== Top 5 brute-force candidate IPs ==
${TOP_IPS:-(none)}

== Most recent 5 successful root logins ==
${ROOT_LOGINS:-(none)}

== Users who logged in within the last 24 hours (lastlog -t 1) ==
${USER_TABLE:-(none)}

Source files:
  /var/log/secure   (text, rsyslog from authpriv.*)
  /var/log/wtmp     (binary, read by 'last')
  /var/log/btmp     (binary, read by 'lastb')
  /var/log/lastlog  (binary, read by 'lastlog')
  journalctl -u sshd.service (systemd journal)
EOF

cat 10-audit-report.txt
```

**Layer stack you built:**

```text
10-audit-report.txt           ← deliverable
  ├── 02-failed.txt            ← raw failed lines
  ├── 04-top-failed-ips.txt    ← brute-force count
  ├── 05-last-n10.txt          ← last successful logins
  ├── 06-lastb-n10.txt         ← last failed logins
  ├── 07-lastlog-top20.txt     ← per-user table
  └── 08-count-compare.txt     ← rsyslog vs journald sanity
```

**Cleanup**

```bash
cd /root
rm -rf /root/secure-lab
ls -ld /root/secure-lab 2>&1 | head -n 1
exit
```

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Empty TOP_IPS | Healthy host — quote `(none)` in the report |
| `lastlog -t 1` empty | Lab VM with no users today — pick a wider window |
| Report fields garbled | Re-run after expanding `$TOP_IPS` in same shell |

---

## 🔍 Auth Triage Decision Guide

```
"Who logged in successfully?"     → last  (or journalctl -u sshd 'Accepted')
"Who failed to log in?"           → lastb (or grep 'Failed password' /var/log/secure)
"When did user X last log in?"    → lastlog -u X
"Show me sudo activity"           → grep 'sudo:' /var/log/secure
"Show me su activity"             → grep 'su\[' /var/log/secure
"Live watch incoming SSH"         → tail -F /var/log/secure | grep sshd
"Brute-force candidate IPs"       → grep 'Failed password' | awk + sort | uniq -c | sort -rn
"Same data, indexed by time"      → journalctl -u sshd.service --since "..."
```

---

## Lab Checklist (10 Tasks)

- [ ] 01 Confirm `/var/log/secure` perms + counts
- [ ] 02 Recognize Accepted / Failed / Invalid / Disconnected shapes
- [ ] 03 Extract sudo and su events
- [ ] 04 Rank failed-password source IPs
- [ ] 05 `last` — successful login history
- [ ] 06 `lastb` — failed login history
- [ ] 07 `lastlog` — per-user last login
- [ ] 08 Correlate with `journalctl -u sshd.service`
- [ ] 09 Build the brute-force candidate report
- [ ] 10 Capstone 24-hour audit + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Reading `/var/log/secure` without `sudo` | Permission denied | `sudo grep ...` |
| `last` shows nothing on fresh VM | `/var/log/wtmp` empty | Log in via SSH at least once |
| `grep "Failed password"` only — missing IPv6 | Misses some attempts | Add `[0-9a-f:.]+` regex |
| Mismatched `secure` and journal counts | journald sees `systemd[1]` Session lines too | Expected — interpret carefully |
| `lastlog` shows wrong dates | `/var/log/lastlog` is sparse — large file, small data | Use `lastlog` not `cat` |
| Confusing `last` and `lastlog` | One is history, other is per-user | Two different files |
| Ignoring `_COMM=sshd` workers | Miss subprocess messages | Combine `-u sshd.service` + `_COMM=sshd` |
| Putting brute-force candidate IPs in a chat | Leaks sensitive data | Use redacted forms in tickets when needed |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- "When did `userX` last log in?" → `lastlog -u userX`. "How many failed logins from 1.2.3.4?" → `lastb | grep 1.2.3.4 | wc -l`.

**RHCE candidate**
- Daily cron job that runs Task 9's pipeline and emails the top 5 IPs to root.

**SRE / Platform interview**
- Be ready to explain the difference between `/var/log/secure`, `/var/log/wtmp`, and `/var/log/audit/audit.log` — and which one a malicious user could most easily tamper with (`secure` and `wtmp` are mutable; `audit.log` is kernel-protected when properly configured).

**DevOps**
- CI runner auth audit per build: `last -s "$BUILD_START" -t "$BUILD_END"` should be empty unless the build legitimately SSHed.

**AI / MLOps**
- Multi-user GPU hosts: weekly `lastlog -b 30` review identifies stale accounts to disable, freeing shared resources.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 101 — `journalctl` query | Same data via a different index |
| Lab 103 — Log Routing | Where the `authpriv.*` rule lives |
| Lab 75 — PAM securetty | Restricts who can reach `/var/log/secure` |
| Lab 165 — User & Group Management | Username/UID context for `/var/log/secure` lines |
| Lab 75 — Limit root access via PAM | Drives lines you'll see during the audit |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
