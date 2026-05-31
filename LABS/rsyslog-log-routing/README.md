# Lab: Understand Log Routing — `/etc/rsyslog.conf`, Facilities, Priorities, Rules, and Drop-ins

- **Series:** linux-ops-mastery — RHCSA Log Management
- **Subjects covered:** the syslog model (facility.priority pairs), `/etc/rsyslog.conf` legacy and RainerScript syntax, drop-ins under `/etc/rsyslog.d/`, the canonical RHEL log file map (`/var/log/messages`, `/var/log/secure`, `/var/log/cron`, `/var/log/maillog`, `/var/log/boot.log`), reading rules with `rsyslogd -N1` config-check, sending messages with `logger -p`, the `imjournal` module that ingests journald into rsyslog, remote forwarding (`@host` UDP / `@@host` TCP), restarting `rsyslog.service`, comparing rsyslog vs journald responsibilities
- **Career arcs covered:** RHCSA (EX200 — "ensure cron messages go to /var/log/cron"), RHCE (Ansible `rsyslog.d/` drop-in template), SRE (centralized log forwarders), DevOps (CI agent log collection), AI / MLOps (per-job log routing for training pipelines)
- **Prerequisite:** Labs 101 and 102 (journalctl basics and persistence)
- **Time Estimate:** 35 to 50 minutes
- **Difficulty arc:** Tasks 1–2 baseline (inventory, syntax) · Tasks 3–4 read facility.priority rules · Task 5 generate and trace a test message · Tasks 6–7 add a custom drop-in rule · Task 8 validate with `rsyslogd -N1` · Task 9 remote forwarding concept (`@`/`@@`) · Task 10 capstone audit + cleanup

---

## Objective

Stop wondering "which file gets which message?" By the end of this lab you can read `/etc/rsyslog.conf` and any drop-in under `/etc/rsyslog.d/`, predict exactly where a given facility-and-priority pair lands, prove your prediction with `logger -p`, and add a new routing rule via a drop-in without touching the canonical file. You will also understand how rsyslog and `systemd-journald` coexist on RHEL — they are not duplicates; one feeds the other.

The capstone is the **engineer-realistic prompt:** *"Audit log routing on this RHEL 9 host: identify which facility lands in which file, add a drop-in that captures `local3.*` to `/var/log/myapp.log`, prove a `logger` test message lands in that file, and write a one-paragraph routing report. Then revert the drop-in."*

> **Lab safety note:** Everything in this lab is reversible. We touch only `/etc/rsyslog.d/` drop-ins and a new `/var/log/myapp.log` — both removed in Task 10.

---

## Concept: Syslog Is `facility.priority → destination`

Every syslog message carries two labels (and the application can pick both):

1. **Facility** — what kind of subsystem produced this (`auth`, `cron`, `daemon`, `kern`, `local0..7`, `mail`, `syslog`, `user`...).
2. **Priority** — how serious (`emerg`, `alert`, `crit`, `err`, `warning`, `notice`, `info`, `debug`).

`rsyslog` reads rules of the form `facility.priority  destination` and writes matching messages to that destination — usually a file under `/var/log/`, sometimes a remote host, sometimes a pipe to a script.

```
   ┌──────────────────────────────────────────────────────────────┐
   │  Application                                                 │
   │       │                                                      │
   │       └─►  syslog(3)  or  /dev/log  or  logger(1)            │
   │                  │                                           │
   │                  ▼                                           │
   │            systemd-journald  ──►  /var/log/journal/...       │
   │                  │ (imjournal module)                        │
   │                  ▼                                           │
   │              rsyslogd                                        │
   │                  │   matches facility.priority               │
   │                  ▼                                           │
   │   /var/log/messages   /var/log/secure   /var/log/cron        │
   │   /var/log/maillog    /var/log/boot.log                      │
   │   @log.example.com    /var/log/myapp.log   ...               │
   └──────────────────────────────────────────────────────────────┘
```

> **Why this matters:** Every RHCSA "which file?" question is a facility.priority lookup. Once you know the rule grammar — and where the RHEL defaults live — you can answer in seconds without grep.

---

## 📜 Why `rsyslog.conf` Exists — The Story

Syslog dates back to **Eric Allman** in 4.2BSD (1980s) — text logs, UDP transport, facility/priority labeling. Linux adopted it; `syslogd` became universal. As Linux grew, the original syslogd ran out of room: no TCP, no TLS, no queueing, no per-rule filtering. **Rainer Gerhards** built **rsyslog** in 2004 as a modern drop-in replacement: same config grammar by default, but a new "RainerScript" for advanced rules, modular outputs, reliable TCP/TLS forwarding, and built-in queues.

When systemd arrived (2010-2011), it brought `systemd-journald` — a different log architecture. RHEL had to choose: keep rsyslog only? Use only journald? **Red Hat chose to keep both**, with journald as the front door and rsyslog as a configurable consumer behind it. journald owns the binary indexed store; rsyslog (via `imjournal`) reads from that store and writes the classic `/var/log/*` text files that countless scripts and humans expect.

This is why RHEL 9 still has `/var/log/messages` even though `journalctl` is the modern tool. The two coexist on purpose — and Lab 103 teaches you the rsyslog half.

> **The point of the story:** rsyslog is not "old syslog still hanging around." It is the **configurable text-file half** of a deliberate two-layer log architecture on RHEL.

---

## 👪 The rsyslog Family — Who Lives Where

```
Daemon
├── rsyslog.service                       ← systemd unit
└── /usr/sbin/rsyslogd                    ← binary

Config
├── /etc/rsyslog.conf                     ← canonical
└── /etc/rsyslog.d/*.conf                 ← drop-ins (preferred for changes)

Default log files (created by rsyslog rules)
├── /var/log/messages                     ← *.info;mail.none;authpriv.none;cron.none
├── /var/log/secure                       ← authpriv.*
├── /var/log/cron                         ← cron.*
├── /var/log/maillog                      ← mail.*
└── /var/log/boot.log                     ← local7.*

Modules (loaded in rsyslog.conf)
├── imjournal                              ← reads from systemd-journald
├── imuxsock                              ← /dev/log socket
├── imklog                                ← kernel ring buffer
├── omfile                                ← write to file
├── omfwd                                 ← forward TCP/UDP to remote
└── omkafka, omelasticsearch, ...          ← optional outputs

Tooling
├── rsyslogd -N1                          ← validate config without reload
├── logger                                 ← inject a syslog message
└── systemctl restart rsyslog              ← apply changes
```

### Default RHEL 9 routing rules (paraphrased from `/etc/rsyslog.conf`)

| Rule | Destination | What it captures |
|---|---|---|
| `*.info;mail.none;authpriv.none;cron.none` | `/var/log/messages` | Most info-or-worse messages |
| `authpriv.*` | `/var/log/secure` | SSH, sudo, login, PAM |
| `mail.*` | `/var/log/maillog` | Postfix, sendmail, dovecot |
| `cron.*` | `/var/log/cron` | crond, anacron, atd |
| `*.emerg` | `:omusrmsg:*` | Wall to every logged-in user |
| `uucp,news.crit` | `/var/log/spooler` | Legacy |
| `local7.*` | `/var/log/boot.log` | Boot phase |

### Facility & priority quick reference

| Facility | Typical sender |
|---|---|
| `auth`, `authpriv` | login, sshd, sudo |
| `cron` | crond |
| `daemon` | generic daemons |
| `kern` | kernel (via `imklog`) |
| `local0..7` | reserved for site / app use |
| `mail` | mail servers |
| `news` | (historical) |
| `syslog` | syslog itself |
| `user` | default for `logger` |

| Priority | When |
|---|---|
| `emerg` (0) | System unusable |
| `alert` (1) | Immediate action |
| `crit` (2) | Critical |
| `err` (3) | Error |
| `warning` (4) | Warning |
| `notice` (5) | Significant but normal |
| `info` (6) | Informational |
| `debug` (7) | Debug |

> **Reading rule:** `facility.priority` matches that priority **and worse** by default. `facility.=priority` matches **exactly** that priority (note the `=`). `facility.!priority` excludes it. `*.none` excludes the whole facility.

---

## 📚 rsyslog Reference Table

| Goal | Command / line | Notes |
|---|---|---|
| Validate config | `sudo rsyslogd -N1` | Parse-check with verbosity level 1 |
| Restart daemon | `sudo systemctl restart rsyslog.service` | Apply config changes |
| Reload (HUP) | `sudo kill -HUP $(pidof rsyslogd)` | Soft reload — flushes open files |
| Status | `systemctl status rsyslog.service` | Confirm running |
| Inject test | `logger -p facility.priority -t TAG "MSG"` | Bypass apps, send straight to syslog |
| Tail messages | `tail -f /var/log/messages` | Live view of the default file |
| Per-facility file | `tail -f /var/log/secure` | authpriv goes here |
| Drop-in path | `/etc/rsyslog.d/NAME.conf` | Numbered drop-ins (e.g., `30-myapp.conf`) |
| Module load | `module(load="imjournal")` | RainerScript |
| Legacy file rule | `local3.*    /var/log/myapp.log` | classic syntax — still valid |
| RainerScript file | `local3.* action(type="omfile" file="/var/log/myapp.log")` | modern equivalent |
| Forward UDP | `*.* @log.example.com:514` | One `@` = UDP |
| Forward TCP | `*.* @@log.example.com:514` | Two `@` = TCP |
| journald input | `module(load="imjournal" StateFile="imjournal.state")` | RHEL default |
| Show effective merged config | `rsyslogd -N1 -f /etc/rsyslog.conf` | Validation also dumps include order |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | EX200 phrasing: "Route facility X to file Y." Drop-in + restart + `logger` smoke test. |
| **RHCE candidate** | Ansible: `template` drop-ins to `/etc/rsyslog.d/`, handler restart, idempotent. |
| **SRE / Platform** | Multi-tenant fleets forward all `*.*` over `@@` TCP/TLS to a central collector. |
| **DevOps** | Ephemeral CI runners need rsyslog forwarding to a remote endpoint before tear-down. |
| **AI / MLOps** | Per-job training services tag with `local3..7` and route to per-tenant files. |

---

## 🔧 The 10 Tasks

> Ten phases that build the **inventory → read facility rule → predict file → prove with logger → write drop-in → validate → restart → re-prove** habit.

---

### Task 1 — Set up the sandbox and confirm `rsyslog` is running

**Purpose:** Build a workspace, confirm the rsyslog daemon is active, and capture the unit's status output for the artifact set.

```bash
sudo -i
mkdir -p /root/rsyslog-lab && cd /root/rsyslog-lab

which rsyslogd
rsyslogd -v 2>&1 | head -n 2 | tee 01-rsyslogd-version.txt
systemctl is-active rsyslog.service | tee 01-rsyslog-active.txt
systemctl status rsyslog.service --no-pager | head -n 10 | tee 01-rsyslog-status.txt
```

**Human-Readable Breakdown:** Become root, create a workspace, confirm the binary exists, capture the version string, confirm the service is `active`, and save the first 10 lines of `systemctl status` for the artifact set.

**Reading it left to right:** `rsyslogd -v` is the version flag. `systemctl is-active` returns `active`/`inactive`/`failed`. `systemctl status --no-pager` keeps the output flowing into the pipe.

**The story:** Rsyslog is enabled by default on RHEL 9. If it is `inactive`, someone has explicitly disabled it — confirm with the user before re-enabling. Most "logs are missing" tickets are actually "rsyslog is not running."

**Expected output:**

```text
/sbin/rsyslogd
rsyslogd 8.2102.0-117.el9
active
● rsyslog.service - System Logging Service
     Loaded: loaded (/usr/lib/systemd/system/rsyslog.service; enabled; preset: enabled)
     Active: active (running) since Tue 2026-01-14 09:00:11 EST; 1h ago
       Docs: man:rsyslogd(8)
             https://www.rsyslog.com/doc/
```

**Switches**

| Token | Meaning |
|---|---|
| `rsyslogd -v` | Version + build info |
| `systemctl is-active UNIT` | Active state only |
| `--no-pager` | Disable pager for pipes |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `rsyslogd: command not found` | `dnf install rsyslog` |
| `inactive` | `systemctl enable --now rsyslog` |
| Status shows `failed` | `journalctl -u rsyslog -p err -n 30` |

---

### Task 2 — Read `/etc/rsyslog.conf` and inventory drop-ins

**Purpose:** See exactly what RHEL ships, including the canonical file and any drop-ins under `/etc/rsyslog.d/`.

```bash
cd /root/rsyslog-lab

ls -l /etc/rsyslog.conf /etc/rsyslog.d/ | tee 02-files.txt
grep -nE '^\s*[a-z][a-z*\.,;!=0-9_-]+\s+[-/@]' /etc/rsyslog.conf | tee 02-rules-canonical.txt
grep -nE '^\s*module\(' /etc/rsyslog.conf | tee 02-modules.txt
wc -l /etc/rsyslog.conf /etc/rsyslog.d/*.conf 2>/dev/null | tee 02-line-counts.txt
```

**Human-Readable Breakdown:** List the canonical file and drop-in directory, then grep for rule lines (a left side that looks like `facility.priority` and a right side that begins with `/`, `-/`, or `@`), then count lines.

**Reading it left to right:** The regex `^\s*[a-z][a-z*\.,;!=0-9_-]+\s+[-/@]` captures lines that start with a facility expression and continue to a destination. `module(` lines are RainerScript module-load statements.

**The story:** The canonical file rarely needs editing. The drop-in directory is where 99% of customization happens. Reading the canonical file once teaches you the default routing; then you forget about it.

**Expected output (excerpt):**

```text
-rw-r--r--. 1 root root 3000 Jan 13 19:00 /etc/rsyslog.conf
/etc/rsyslog.d/:
total 4
-rw-r--r--. 1 root root 150 Jan 13 19:00 listen.conf
40:*.info;mail.none;authpriv.none;cron.none                /var/log/messages
44:authpriv.*                                              /var/log/secure
48:mail.*                                                  -/var/log/maillog
52:cron.*                                                  /var/log/cron
56:*.emerg                                                 :omusrmsg:*
60:uucp,news.crit                                          /var/log/spooler
64:local7.*                                                /var/log/boot.log
```

**Switches**

| Token | Meaning |
|---|---|
| `ls -l DIR/` | Long listing |
| `grep -nE` | Number + extended regex |
| `wc -l` | Line counts |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `/etc/rsyslog.d/` does not exist | `mkdir /etc/rsyslog.d` — package install creates it |
| No matches in canonical | RHEL 9 ships ~6 rules; check the file directly |
| Regex matches comments | Refine with `^[^#]` prefix |

---

### Task 3 — Decode each default rule: facility → priority → destination

**Purpose:** Translate the canonical rules into human English so you can predict where a message will land.

```bash
cd /root/rsyslog-lab

cat <<'EOF' | tee 03-decoded-rules.txt
RULE                                                  MEANING
*.info;mail.none;authpriv.none;cron.none /var/log/messages
  Match every facility at info-or-worse priority,
  except mail, authpriv, and cron (those have their own files).
authpriv.* /var/log/secure
  Every authpriv message (sshd, login, sudo, PAM) → secure.
mail.* -/var/log/maillog
  Every mail message → maillog. The leading '-' disables fsync per write
  (faster, slightly less crash-safe).
cron.* /var/log/cron
  Every cron message → cron.
*.emerg :omusrmsg:*
  Every emergency-priority message → wall to every logged-in user.
uucp,news.crit /var/log/spooler
  Legacy uucp/news critical messages → spooler.
local7.* /var/log/boot.log
  All local7 messages (boot phase) → boot.log.
EOF
cat 03-decoded-rules.txt
```

**Human-Readable Breakdown:** Spend three minutes producing the cheat sheet you'll consult for the rest of the lab. Save it as an artifact so future-you doesn't re-derive it.

**Reading it left to right:** The `*` wildcard on the left side matches all facilities; `none` excludes a facility from a multi-facility rule; the leading `-` on a destination disables fsync (write-cached). `:omusrmsg:*` is the legacy `wall` output module.

**The story:** Senior engineers internalize this table. Junior engineers grep `/etc/rsyslog.conf`. RHCSA candidates should be able to predict, before running `logger`, exactly which file will see the message.

**Expected output:** the heredoc itself.

**Switches**

| Operator | Meaning |
|---|---|
| `*` | Wildcard (all facilities or all priorities) |
| `;` | Combine multiple selectors on one rule |
| `,` | List multiple facilities |
| `.=PRIO` | Exact priority match (legacy) |
| `.!PRIO` | Exclude this priority (legacy) |
| `.none` | Exclude this facility |
| Leading `-` on path | Skip fsync |
| `@host[:port]` | UDP forward |
| `@@host[:port]` | TCP forward |
| `:omusrmsg:*` | Write to all logged-in users |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Predicted file but message went elsewhere | A drop-in overrides — `grep -r facility /etc/rsyslog.d/` |
| Confused by `.none` | Read as "exclude this facility from this aggregate rule" |

---

### Task 4 — Identify which file should receive each facility

**Purpose:** Walk every common facility and assert the destination file from the rules in Task 3.

```bash
cd /root/rsyslog-lab

cat <<'EOF' | tee 04-facility-to-file.txt
FACILITY        EXAMPLE SENDER                         DEFAULT FILE
authpriv        sshd, sudo, login, su                  /var/log/secure
cron            crond, anacron, atd                    /var/log/cron
mail            postfix, dovecot                       /var/log/maillog
local7          systemd boot, GRUB-related             /var/log/boot.log
*.emerg         any                                    wall (every TTY)
daemon          systemd, NetworkManager                /var/log/messages
kern            kernel                                 /var/log/messages
user            'logger' default                       /var/log/messages
local0..6       custom apps                            /var/log/messages (no specific file)
EOF
cat 04-facility-to-file.txt
```

**Human-Readable Breakdown:** Produce the second cheat sheet — for each facility, name a real-world sender and the file it lands in by default on RHEL 9.

**Reading it left to right:** This is reference content; no command parses it. The point is to memorize it.

**The story:** Combine Tasks 3 and 4 and you can answer any "where will this message land?" exam question. The exception is `local0..6` which are deliberately uncovered — Task 6 adds a rule for `local3`.

**Switches**

| Concept | Value |
|---|---|
| Why `local*` exists | Site-/app-specific use |
| Why most go to messages | The catch-all `*.info` rule |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `authpriv` messages in `/var/log/messages` | Drop-in changed the rule — grep `/etc/rsyslog.d/` |

---

### Task 5 — Generate a test message with `logger` and trace it

**Purpose:** Use `logger` to inject a message at a chosen facility.priority and prove which file received it.

```bash
cd /root/rsyslog-lab

logger -p authpriv.notice -t lab103 "test message to /var/log/secure"
logger -p cron.info -t lab103 "test message to /var/log/cron"
logger -p mail.warning -t lab103 "test message to /var/log/maillog"
logger -p user.info -t lab103 "test message to /var/log/messages"

sleep 1
for F in /var/log/secure /var/log/cron /var/log/maillog /var/log/messages; do
  echo "--- $F ---"
  grep 'lab103' "$F" 2>/dev/null | tail -n 3
done | tee 05-traced-messages.txt
```

**Human-Readable Breakdown:** Send four messages, one per facility — `authpriv`, `cron`, `mail`, `user` — then grep each expected file for the tag `lab103` to prove the routing worked.

**Reading it left to right:** `logger -p FACILITY.PRIORITY -t TAG MSG` is the syslog-equivalent of writing a log line by hand. The tag becomes the `SYSLOG_IDENTIFIER` field. The `for` loop walks the four files and shows the last three matching lines.

**The story:** This is the *fastest* way to learn rsyslog routing. Take a rule from `/etc/rsyslog.conf`, predict the destination, and prove it with `logger`. Repeat until every default rule is intuitive.

**Expected output:**

```text
--- /var/log/secure ---
Jan 14 09:50:11 host1 lab103[2901]: test message to /var/log/secure
--- /var/log/cron ---
Jan 14 09:50:11 host1 lab103[2902]: test message to /var/log/cron
--- /var/log/maillog ---
Jan 14 09:50:11 host1 lab103[2903]: test message to /var/log/maillog
--- /var/log/messages ---
Jan 14 09:50:11 host1 lab103[2904]: test message to /var/log/messages
```

**Switches**

| Token | Meaning |
|---|---|
| `-p F.P` | Facility.Priority |
| `-t TAG` | Set syslog tag (identifier) |
| (positional) MSG | Message body |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Message in `/var/log/messages` instead of expected file | Drop-in override — grep `/etc/rsyslog.d/` |
| No message anywhere | `rsyslog.service` not running — `systemctl restart` |
| Tag is `(root)` | Forgot `-t` flag |

---

### Task 6 — Add a drop-in: route `local3.*` to `/var/log/myapp.log`

**Purpose:** Add a new routing rule via a drop-in (the proper place for site changes), restart, and prove with `logger`.

```bash
cd /root/rsyslog-lab

cat <<'EOF' | sudo tee /etc/rsyslog.d/30-myapp.conf >/dev/null
# Route local3.* to /var/log/myapp.log
local3.*    /var/log/myapp.log
EOF

cat /etc/rsyslog.d/30-myapp.conf | tee 06-dropin.txt

sudo touch /var/log/myapp.log
sudo chown root:root /var/log/myapp.log
sudo chmod 600 /var/log/myapp.log

sudo systemctl restart rsyslog.service
sleep 1

logger -p local3.info -t lab103 "first myapp message"
logger -p local3.warning -t lab103 "second myapp warning"

sleep 1
sudo tail -n 5 /var/log/myapp.log | tee 06-myapp-tail.txt
```

**Human-Readable Breakdown:** Drop a small file in `/etc/rsyslog.d/` numbered `30-myapp.conf` (so it merges after the canonical `*.info` rule), pre-create the destination file with safe permissions, restart rsyslog, inject two `local3` messages, and tail the new file to confirm.

**Reading it left to right:** `30-` controls merge order — lower numbers load first. `local3.*` matches any priority of facility `local3`. The destination is an absolute path. Pre-creating the file with `chmod 600` keeps the messages root-readable only.

**The story:** Drop-ins are the **only** place you should add rules in production. Never edit `/etc/rsyslog.conf` directly — vendor updates may overwrite it. The drop-in pattern survives package upgrades cleanly.

**Expected output:**

```text
# Route local3.* to /var/log/myapp.log
local3.*    /var/log/myapp.log
Jan 14 09:53:11 host1 lab103[2950]: first myapp message
Jan 14 09:53:11 host1 lab103[2951]: second myapp warning
```

**Switches**

| Token | Meaning |
|---|---|
| `tee -a FILE` | Append instead of overwrite |
| `chmod 600 FILE` | Owner read/write only |
| `30-` prefix on drop-in name | Merge order before/after defaults |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| File never appears | `rsyslog` not restarted — `systemctl restart` |
| File exists but empty | Wrong facility — verify `logger -p` matches the rule |
| Permission denied tailing | `chmod 600` requires `sudo tail` |

---

### Task 7 — Confirm the new rule with both legacy and RainerScript

**Purpose:** Show the equivalent RainerScript form — useful when the rest of the file uses it.

```bash
cd /root/rsyslog-lab

cat <<'EOF' | sudo tee /etc/rsyslog.d/30-myapp.conf >/dev/null
# Legacy form:
#   local3.*    /var/log/myapp.log
#
# Equivalent RainerScript form:
local3.* action(type="omfile" file="/var/log/myapp.log" fileCreateMode="0600" fileOwner="root" fileGroup="root")
EOF

cat /etc/rsyslog.d/30-myapp.conf | tee 07-dropin-rainerscript.txt

sudo systemctl restart rsyslog.service
sleep 1
logger -p local3.notice -t lab103 "rainerscript test message"
sleep 1
sudo tail -n 3 /var/log/myapp.log | tee 07-myapp-tail.txt
```

**Human-Readable Breakdown:** Rewrite the drop-in using the modern RainerScript `action()` call with explicit file creation properties, restart, inject a test message, and confirm.

**Reading it left to right:** `action(type="omfile" ...)` is RainerScript's way to declare an output action. `omfile` is the file-output module. Properties like `fileCreateMode` and `fileOwner` are set inline, removing the need for `chmod`/`chown` separately.

**The story:** New RHEL deployments increasingly use RainerScript exclusively. Both syntaxes coexist — pick the one that matches the surrounding file's style. RainerScript is more verbose but more powerful (per-action queue settings, retries, TLS, etc.).

**Expected output:**

```text
local3.* action(type="omfile" file="/var/log/myapp.log" fileCreateMode="0600" fileOwner="root" fileGroup="root")
Jan 14 09:54:55 host1 lab103[2970]: rainerscript test message
```

**Switches**

| Token | Meaning |
|---|---|
| `action(type="omfile" ...)` | Modern file output |
| `fileCreateMode="0600"` | Create with mode |
| `fileOwner=` / `fileGroup=` | Ownership at create |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Syntax error on restart | `rsyslogd -N1` — typo in action() |
| File mode wrong | Pre-existing file overrides `fileCreateMode` — delete and re-test |

---

### Task 8 — Validate config with `rsyslogd -N1`

**Purpose:** Parse-check before restart. The single most valuable rsyslog debugging trick.

```bash
cd /root/rsyslog-lab

sudo rsyslogd -N1 2>&1 | tee 08-N1-output.txt

cat <<'EOF' | sudo tee /etc/rsyslog.d/99-broken.conf >/dev/null
local3.* /var/log/myapp.log :::: this line is intentionally bad
EOF
sudo rsyslogd -N1 2>&1 | tee 08-N1-broken.txt
sudo rm /etc/rsyslog.d/99-broken.conf
sudo rsyslogd -N1 2>&1 | head -n 5 | tee 08-N1-fixed.txt
```

**Human-Readable Breakdown:** Run a parse-check on the current config and save it, intentionally break a drop-in to see the error format, then remove the broken file and re-validate.

**Reading it left to right:** `rsyslogd -N1` parses configs at verbosity level 1 and exits — no restart. Errors print to stderr; `2>&1` brings them into the captured stream. Verbosity levels go up to N6 for deep debugging.

**The story:** `rsyslogd -N1` before `systemctl restart rsyslog` is the same discipline as `nginx -t` before `nginx -s reload`. It catches typos that would otherwise restart-bounce the daemon and lose log entries.

**Expected output:**

```text
rsyslogd: version 8.2102.0, config validation run (level 1), master config /etc/rsyslog.conf
rsyslogd: End of config validation run. Bye.
rsyslogd: error during parsing file /etc/rsyslog.d/99-broken.conf, on or before line 1: ...
rsyslogd: version 8.2102.0, config validation run (level 1), master config /etc/rsyslog.conf
rsyslogd: End of config validation run. Bye.
```

**Switches**

| Token | Meaning |
|---|---|
| `-N1` | Validate, verbosity 1 |
| `-N3..N6` | Deeper trace |
| `2>&1` | Capture stderr |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `parsing file ... line N` | Edit that exact line |
| Old error after fix | Re-run `-N1` |

---

### Task 9 — Remote forwarding concept: `@host` vs `@@host`

**Purpose:** Show, but do not enable, the forwarding pattern so you can identify it in real configs and explain it on exams.

```bash
cd /root/rsyslog-lab

cat <<'EOF' | tee 09-forwarding-snippets.txt
# UDP forward (lossy, no ACK) — single @
*.*  @log.example.com:514

# TCP forward (reliable, queueable) — double @@
*.*  @@log.example.com:514

# RainerScript TCP + TLS forward
action(
  type="omfwd"
  Target="log.example.com"
  Port="6514"
  Protocol="tcp"
  StreamDriver="gtls"
  StreamDriverMode="1"
  StreamDriverAuthMode="x509/name"
  StreamDriverPermittedPeers="log.example.com"
)
EOF
cat 09-forwarding-snippets.txt
```

**Human-Readable Breakdown:** Document the three forwarding shapes — legacy UDP `@`, legacy TCP `@@`, and modern TLS — so you recognize them when reading enterprise configs.

**Reading it left to right:** `@host:port` = UDP; `@@host:port` = TCP. The TLS form requires module `omfwd` with stream driver parameters. Port 514 is the unencrypted default; 6514 is the rsyslog-over-TLS convention.

**The story:** Centralized logging is a non-negotiable in any environment beyond a single host. Knowing how rsyslog forwards is enough to read most "logs to log server" deployments. Lab does not enable forwarding because there is no remote receiver on a single VM.

**Expected output:** the heredoc itself.

**Switches**

| Form | Protocol |
|---|---|
| `@host` | UDP |
| `@@host` | TCP |
| `omfwd ... StreamDriver=gtls` | TCP + TLS |
| Port `514` | Cleartext |
| Port `6514` | TLS |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `@` vs `@@` confusion | One-`@` UDP, two-`@@` TCP |
| Forwarding adds latency | Enable rsyslog queue + DiskAction queueing |

---

### Task 10 — Capstone: audit report + cleanup revert

**Task statement:** *"Produce a one-paragraph audit report of routing on this host (which facility lands where), confirm the `local3 → /var/log/myapp.log` drop-in works, then revert the drop-in and remove `/var/log/myapp.log`."*

**Purpose:** Combine prior tasks into a deliverable, then clean every artifact.

```bash
cd /root/rsyslog-lab

DROPINS=$(ls -1 /etc/rsyslog.d/*.conf 2>/dev/null | wc -l)
MYAPP_COUNT=$(sudo wc -l < /var/log/myapp.log 2>/dev/null || echo 0)
RULES=$(grep -hE '^\s*[a-z*][a-z*\.,;!=0-9_-]+\s+[-/@]' /etc/rsyslog.conf /etc/rsyslog.d/*.conf 2>/dev/null | wc -l)

cat > 10-report.txt <<EOF
rsyslog routing audit — $(hostname) — $(date -Iseconds)

Daemon:          $(rsyslogd -v | head -n 1)
Config files:    /etc/rsyslog.conf + ${DROPINS} drop-ins in /etc/rsyslog.d/
Active rules:    ~${RULES}

Default routing summary:
  authpriv.*  → /var/log/secure
  cron.*      → /var/log/cron
  mail.*      → /var/log/maillog
  local7.*    → /var/log/boot.log
  *.info;...  → /var/log/messages
  *.emerg     → wall

Lab drop-in:
  local3.*    → /var/log/myapp.log   (lines: ${MYAPP_COUNT})

Revert:
  sudo rm /etc/rsyslog.d/30-myapp.conf
  sudo systemctl restart rsyslog
  sudo rm /var/log/myapp.log
EOF

cat 10-report.txt
```

**Layer stack you built:**

```text
10-report.txt                       ← deliverable
  ├── /etc/rsyslog.d/30-myapp.conf  ← new drop-in
  ├── /var/log/myapp.log            ← new destination file
  └── 01..09 artifact files          ← evidence
```

**Cleanup**

```bash
sudo rm /etc/rsyslog.d/30-myapp.conf
sudo systemctl restart rsyslog.service
sudo rm -f /var/log/myapp.log

cd /root
rm -rf /root/rsyslog-lab
ls -ld /root/rsyslog-lab 2>&1 | head -n 1
exit
```

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Report shows `lines: 0` | Re-run Task 6 — restart did not flush |
| Drop-in still present after cleanup | Verify with `ls /etc/rsyslog.d/` |
| `/var/log/myapp.log` recreated by next `logger` | You forgot to restart rsyslog after `rm` |

---

## 🔍 Log Routing Decision Guide

```
"Where will this message land?"
  │
  ├── facility = authpriv → /var/log/secure
  ├── facility = cron     → /var/log/cron
  ├── facility = mail     → /var/log/maillog
  ├── facility = local7   → /var/log/boot.log
  ├── priority = emerg    → wall (all TTYs)
  ├── facility = local0..6 → /var/log/messages (catch-all)
  └── any drop-in match    → drop-in destination wins

"Where should I add a new rule?"
  └── /etc/rsyslog.d/NN-name.conf   (never the canonical file)

"How do I prove it?"
  └── logger -p facility.priority -t TAG MSG → tail destination
```

---

## Lab Checklist (10 Tasks)

- [ ] 01 Confirm `rsyslog.service` running
- [ ] 02 Inventory canonical + drop-ins
- [ ] 03 Decode every default rule
- [ ] 04 Map facility → file
- [ ] 05 Inject `logger` messages and trace
- [ ] 06 Add `local3 → /var/log/myapp.log` drop-in
- [ ] 07 RainerScript equivalent
- [ ] 08 Validate with `rsyslogd -N1`
- [ ] 09 Document forwarding (`@` vs `@@`)
- [ ] 10 Audit report + cleanup revert

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Editing `/etc/rsyslog.conf` directly | Vendor updates blow away change | Use drop-ins |
| `local3.* /var/log/myapp.log` without restart | File never created | `systemctl restart rsyslog` |
| Drop-in named `myapp.conf` (no leading number) | Merge order ambiguous | Prefix with `NN-` |
| `logger -p local3 ...` with no priority | Defaults to `notice` | Always `facility.priority` |
| Confusing `@` and `@@` | Wrong transport | One-`@` UDP, two-`@@` TCP |
| `tail -f /var/log/messages` to debug authpriv | Messages go to `/var/log/secure` | Use the right file |
| Killing rsyslog with `-9` | Loses queued messages | Use `systemctl restart` |
| Permissions on `/var/log/myapp.log` | App cannot read | `chmod 644` if multiple readers |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- "Where does cron log?" — `/var/log/cron`. "How do I send local3 to its own file?" — drop-in + restart.

**RHCE candidate**
- Templated drop-ins to `/etc/rsyslog.d/` with `notify: restart rsyslog`.

**SRE / Platform interview**
- Be ready to explain queueing: `omfwd` with `queue.type="LinkedList"` and `queue.fileName=` provides reliable delivery during collector outages.

**DevOps**
- Forward `*.* @@central:6514` in base AMIs; per-app logs from CI runners flow into a single index.

**AI / MLOps**
- Tag training-job logs with `local3..6`, route per-tenant into per-bucket files, then ship to object storage.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 101 — `journalctl` query | Same messages, different reader |
| Lab 102 — Persistent journal | journald is rsyslog's input (imjournal) |
| Lab 104 — `/var/log/secure` | Watch authpriv rule fire |
| Lab 105 — Filter by priority | journalctl mirror of `*.priority` syntax |
| Lab 106 — Service-specific journals | `-u UNIT` is the journald equivalent of `programname == "UNIT"` filtering |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
