# Lab: Scheduling Jobs with systemd Timers (Mon–Fri 2 AM)

**Series:** linux-ops-mastery — RHCSA / RHCE Scheduled Tasks
**Subjects covered:** `.service` units, `.timer` units, `OnCalendar=`, monotonic vs. realtime timers, `User=`, `Persistent=`, `AccuracySec=`, `RandomizedDelaySec=`, `systemctl daemon-reload`, `systemctl list-timers`, `systemd-analyze calendar`, `journalctl -u`, `logger`
**Career arcs covered:** RHCSA (Scheduled Tasks objective), RHCE (Ansible `systemd_unit` module), SRE (modern alternative to cron), DevOps (replacing legacy crontabs in container images)
**Prerequisite:** Linux user/group basics, comfort with `systemctl` start/stop/enable
**Time Estimate:** 60 to 90 minutes
**Difficulty arc:** Tasks 1–6 foundation · 7–13 building the unit pair · 14–18 making it production-grade · 19–20 RHCSA exam-realistic capstone

---

## Objective

Build the **systemd timer mental model** by hand so you can replace any cron job with the modern, dependency-aware, journald-logged, user-scoped equivalent. By the end of this lab you can write a `.timer` + `.service` unit pair from a blank file in under 5 minutes, prove it fires on schedule, prove it fires *as the right user*, and verify the log line landed exactly where you expect.

The capstone is the **sandervongut exam scenario**: a systemd timer that writes `"hello folks"` to syslog every Monday through Friday at 2 AM, executed as user `chisha`.

---

## Concept: A Timer Is a Unit That Triggers Another Unit

A systemd timer is **not** the thing that runs your command. It is a separate unit whose only job is to **activate a sibling service unit on a schedule**. The work is always done by the `.service`; the `.timer` is the alarm clock.

```
hellofolks.timer  ──schedules──▶  hellofolks.service  ──runs──▶  logger "hello folks"
   (the alarm)                       (the worker)                    (the actual work)
```

That separation is the single biggest difference from cron. In cron, the schedule and the command live on one line. In systemd, they live in two files — and that decoupling is what unlocks every superpower below: dependencies, user scoping, journald logging, accuracy modifiers, and `systemctl status` for "did my last run succeed?"

> **Why this matters:** Modern RHEL ships with **systemd timers replacing most of the historical cron jobs** (`logrotate.timer`, `dnf-makecache.timer`, `man-db.timer`, …). Reading the RHEL 9 system already trains your eye for the conventions you'll write on the exam.

---

## 📜 Why systemd Timers Exist — The Story

Cron has run Linux scheduled jobs since **1975**. It is small, fast, and has lived inside System V init, BSD init, Upstart, and now systemd. So why did Red Hat invent another scheduler?

### The cron pain points (1975–2010)

- **No dependencies.** A cron job that needs `network.target` will silently run before the NIC is up. Cron has no way to say "wait until the network is online."
- **No service boundary.** Cron forks a shell, the shell forks your command, the command's stdout/stderr lands wherever the user's mail spool happens to point. Lose mail delivery and you lose the only audit trail.
- **No persistence semantics.** If the machine is off at 2 AM Tuesday, cron does *nothing*. The job is silently skipped forever. You only notice the missing run when the report you were generating is empty.
- **No user-friendly status.** "Did my 02:00 job run?" requires reading `/var/log/cron`, `/var/spool/mail/root`, and praying.
- **Per-user crontabs are invisible.** A nightly job in `bob`'s `crontab -e` is unfindable unless you `crontab -l -u bob` for every user on the box.

### The systemd answer (2010 onward)

systemd timers were designed by Lennart Poettering with five explicit goals:

1. **Reuse the unit-file ecosystem.** A `.timer` is a unit. It can declare `Requires=`, `After=`, `Wants=`, `Conflicts=` — same vocabulary as every other unit on the system. *A timer can depend on `network-online.target`.*
2. **Decouple schedule from work.** The `.timer` schedules; the `.service` runs. You can unit-test the service by hand (`systemctl start hellofolks.service`) without waiting for 2 AM.
3. **Centralize logging.** Every run goes to journald. `journalctl -u hellofolks.service` shows every invocation, every exit code, every byte of stdout/stderr — forever (or until log rotation), no mail spool required.
4. **Add `Persistent=true`.** Missed your 2 AM run because the laptop was asleep? With `Persistent=true`, systemd notices on wake/boot and runs the job *right then* to catch up.
5. **Make user-scoped timers first-class.** Users can run `systemctl --user enable mytimer.timer` to schedule jobs that only live as long as their login session — impossible with cron without root.

### When cron is still fine

Don't oversell timers. If you have a one-line nightly cleanup job on a long-lived server and you are not preparing for RHCSA, cron is fine. Timers shine when:

- The job has dependencies (network, mount points, other services)
- You need exact "did it run?" auditing
- You want catch-up behavior after downtime
- You're shipping the job inside a container or an Ansible role
- You're on a RHEL exam and the question asks for "a systemd timer"

> **The point of the story:** Every feature you'll fight for in this lab — `OnCalendar`, `Persistent=`, `User=`, `AccuracySec=` — exists because somebody at Red Hat got paged at 3 AM by a cron job that silently skipped, ran as the wrong user, or had no log entry. The pain you'll feel learning this syntax is the price of never repeating that incident.

---

## 👪 The systemd Timer Family — Who Lives There

Not all timers are the same. There are two big families and several specialized members.

### By trigger type

| Family member | Directive | Fires based on | Use case |
|---|---|---|---|
| **Realtime (calendar) timer** | `OnCalendar=` | A wall-clock schedule (`Mon..Fri *-*-* 02:00:00`) | RHCSA exam, nightly reports, weekday cleanups — *the lab capstone* |
| **Monotonic timer** | `OnBootSec=` | Seconds since boot | Run "X minutes after every boot" |
| **Monotonic timer** | `OnStartupSec=` | Seconds since systemd was started | Same as `OnBootSec` for most cases; differs on user managers |
| **Monotonic timer** | `OnActiveSec=` | Seconds since the timer itself became active | One-shot delays after enabling |
| **Monotonic timer** | `OnUnitActiveSec=` | Seconds since the associated unit last activated | Repeating "every 5 minutes after the last run" |
| **Monotonic timer** | `OnUnitInactiveSec=` | Seconds since the associated unit last deactivated | Repeating "5 minutes after the last finish" |

You'll almost always reach for `OnCalendar=` for exam tasks. Monotonic timers shine for "every N minutes" loops where exact wall-clock time doesn't matter.

### By scope

| Scope | How you enable it | Where the unit lives | Runs as |
|---|---|---|---|
| **System timer** | `sudo systemctl enable --now foo.timer` | `/etc/systemd/system/foo.timer` (or `/usr/lib/...`) | Root by default; use `User=` to drop privileges |
| **User timer** | `systemctl --user enable --now foo.timer` | `~/.config/systemd/user/foo.timer` | The user; needs `loginctl enable-linger USER` to run when not logged in |

For the sandervongut exam scenario, **system timer with `User=chisha`** is the right answer — it auto-starts at boot without depending on chisha being logged in.

### Tuning modifiers

| Directive | What it does | When to use |
|---|---|---|
| `Persistent=true` | If the system was off at fire time, run the job on next boot to catch up | Nightly reports you can't miss |
| `AccuracySec=` | How sloppy the firing can be (default 1 min). Lower = more precise = more wakeups | `1s` for exam precision; `1h` for laptops to save battery |
| `RandomizedDelaySec=` | Add a random delay up to N seconds | Spread out load across a fleet (e.g. 100 servers all running at 02:00) |
| `WakeSystem=true` | Wake the system from suspend to fire | Rare; mostly laptops |

### The associated `.service` family

A timer must point at a service. The service can be:

| Type | Behavior | Use case |
|---|---|---|
| `Type=oneshot` | systemd waits for it to exit before considering it "done"; doesn't keep it active | **The default for timer-driven jobs** — perfect for the lab |
| `Type=simple` | Treated as long-running; systemd considers it "started" once the process is alive | Daemons, not scheduled tasks |
| `Type=exec` | Like `simple` but waits for `execve()` to succeed | Rarely needed |
| `Type=forking` | The classic SysV-style double-fork daemon | Legacy software |
| `Type=notify` | The service tells systemd "I'm ready" via sd_notify | Modern daemons |

For our capstone, `hellofolks.service` will be `Type=oneshot` because `logger` runs, prints, and exits in milliseconds.

> **The point of the family tree:** When you read an exam question that says "every Monday at 2 AM," you should immediately think *realtime timer with `OnCalendar=`, system scope, `Type=oneshot` service, `User=` directive, `Persistent=true` for safety.* Five directives. Memorize the family and the question almost answers itself.

---

## 🔬 The Anatomy of a `.timer` Unit — In One Diagram

### What a complete `.timer` file looks like

```
# /etc/systemd/system/hellofolks.timer
[Unit]                                          ◀── Section: unit metadata
Description=Greet folks Mon–Fri at 02:00        ◀── Human-readable name; shows up in `systemctl status`
Requires=hellofolks.service                     ◀── Hard dependency: pulls the service into the transaction

[Timer]                                         ◀── Section: scheduling rules (the heart of the file)
OnCalendar=Mon..Fri *-*-* 02:00:00              ◀── Realtime schedule. Read as: "Monday through Friday, any year-month-day, at 02:00:00."
Persistent=true                                 ◀── Catch up missed runs after downtime
AccuracySec=1s                                  ◀── Fire within ±1s of the calendar moment
Unit=hellofolks.service                         ◀── What to start when the alarm fires (default: same basename + .service)

[Install]                                       ◀── Section: how `systemctl enable` should wire it in
WantedBy=timers.target                          ◀── Pulled in when systemd reaches the timers target during boot
```

Every `.timer` file follows this 3-section shape. The `[Unit]` and `[Install]` sections are shared with every other unit type; the `[Timer]` section is where the actual scheduling magic happens.

### What a matching `.service` file looks like

```
# /etc/systemd/system/hellofolks.service
[Unit]
Description=Write "hello folks" to syslog
After=network.target syslog.target              ◀── Don't fire until syslog is up (otherwise the log line vanishes)

[Service]
Type=oneshot                                    ◀── Run once, exit, don't linger
User=chisha                                     ◀── Drop privileges before exec
ExecStart=/usr/bin/logger "hello folks"         ◀── The actual command. ALWAYS use absolute paths in unit files.

# No [Install] section because this is started by the timer, not by `systemctl enable`
```

### Reading an `OnCalendar=` expression

```
OnCalendar=Mon..Fri *-*-* 02:00:00
          └──┬──┘ └─┬─┘ └───┬────┘
             │      │       └─ Time: HH:MM:SS (24-hour)
             │      └─ Date: YYYY-MM-DD ; `*` means "any"
             └─ Day-of-week list. `..` is a range; `,` is enumeration (`Mon,Wed,Fri`)
```

Some equivalent expressions you'll see in the wild:

```
OnCalendar=*-*-* 03:00:00                  Every day at 3 AM
OnCalendar=Mon *-*-* 09:00:00              Mondays at 9 AM
OnCalendar=*-*-01 00:00:00                 First of every month, midnight
OnCalendar=hourly                          Shortcut: every hour on the hour
OnCalendar=daily                           Shortcut: every day at midnight
OnCalendar=weekly                          Shortcut: Mondays at midnight
OnCalendar=monthly                         Shortcut: 1st of the month, midnight
```

When in doubt, always test your expression with `systemd-analyze calendar 'YOUR_EXPRESSION'` — it'll show the next 5 firings so you can sanity-check.

---

## 📚 systemd Timer Reference Table

| Task | Cron equivalent | systemd timer equivalent |
|---|---|---|
| Every Mon–Fri 2 AM | `0 2 * * 1-5 cmd` | `OnCalendar=Mon..Fri *-*-* 02:00:00` |
| Every day at midnight | `0 0 * * * cmd` | `OnCalendar=daily` (or `*-*-* 00:00:00`) |
| Every 15 min | `*/15 * * * * cmd` | `OnUnitActiveSec=15min` + `OnBootSec=15min` |
| First of every month | `0 0 1 * * cmd` | `OnCalendar=*-*-01 00:00:00` |
| Catch up missed runs | (impossible) | `Persistent=true` |
| Run as another user | `su - user -c cmd` in root crontab | `User=username` in the `.service` |
| Auditing what ran | `/var/log/cron` + mail | `journalctl -u myjob.service` |
| Show next firing | (none) | `systemctl list-timers` |
| Test a schedule string | (none) | `systemd-analyze calendar 'EXPR'` |
| Random spread for fleet | `sleep $((RANDOM % 600))` | `RandomizedDelaySec=10min` |

> **Rule one of timer debugging:** if a timer "didn't fire," 90% of the time it's one of (a) you forgot `systemctl daemon-reload`, (b) you forgot `WantedBy=timers.target` in `[Install]`, or (c) you ran `systemctl enable` instead of `systemctl enable --now` and never started it.

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | "Schedule a recurring task" is a near-guaranteed exam question. The 2024+ exam favors systemd timers over crontabs. |
| **RHCE candidate** | The Ansible `ansible.builtin.systemd` module manages these units; you'll write playbooks that drop `.timer` files into `/etc/systemd/system/`. |
| **SRE / Platform** | Replacing legacy crontabs in container images with systemd timers (or `cron`-free alternatives like Kubernetes CronJob) is a routine migration. |
| **DevOps** | Every `dnf-automatic`, `logrotate`, `mlocate`, and `man-db` job on a modern RHEL box is already a systemd timer. Reading them trains you to write your own. |
| **AI / MLOps** | Scheduled retraining, log aggregation, and model-drift checks all run on timers on the underlying RHEL or Ubuntu host. |

---

## 🔧 The 20 Tasks

> Each task is structured for maximum understanding, not just maximum typing. After the **Purpose** and the code, every task includes:
>
> - **Human-Readable Breakdown** — a conversational "Hey systemd, here's what I want you to do" walkthrough of the whole snippet in one paragraph.
> - **Reading it left to right** — a token-by-token gloss so you can read every symbol like an English sentence.
> - **The story** — the *why* behind the pattern: when you'll reach for it in real ops work, what bug class it prevents.
> - **Analogy** — a one-line metaphor to anchor the concept in something physical.
> - **Expected output** — exactly what you should see in your terminal.
> - **Switches / Output decoded / Troubleshoot** — three small reference tables.

---

### Task 1 — Set up the lab workspace

**Purpose:** Confirm you have root, a working systemd, and the `logger` binary that the capstone service will eventually call.

```bash
sudo -i
hostnamectl
systemctl --version | head -1
which logger
mkdir -p /root/timer-lab && cd /root/timer-lab
```

**Human-Readable Breakdown:**
> "Become root for the whole lab. Confirm I'm on a RHEL-like box. Confirm systemd is alive and on version 250 or newer. Confirm `logger` is installed at `/usr/bin/logger` — we'll reference its absolute path in the unit file later. Make a working directory under `/root` so I have a clean place to draft units before I copy them into `/etc/systemd/system/`."

**Reading it left to right:**
- `sudo -i` → "open a root login shell. Use a real root environment so `PATH` and `HOME` are set the way root expects."
- `hostnamectl` → "print system info: hostname, OS, kernel, virtualization. Sanity check the box."
- `systemctl --version | head -1` → "first line of the systemd version banner. RHEL 9 ships systemd 252."
- `which logger` → "show the absolute path to `logger`. We'll need this exact path inside `ExecStart=` later."
- `mkdir -p /root/timer-lab && cd /root/timer-lab` → "draft directory; `-p` won't error if it exists."

**The story:** Every systemd unit-file lab starts with the same ritual — confirm you're root, confirm the system is alive, confirm the binaries you'll reference exist at the paths you expect. Unit files **do not** consult `$PATH`. If you write `ExecStart=logger ...` instead of `ExecStart=/usr/bin/logger ...`, the service will fail at boot with `Failed to locate executable logger: No such file or directory` and you'll spend twenty minutes wondering why a binary on your shell's `PATH` "doesn't exist." This task makes you write the absolute path on a Post-it before you ever open a unit file.

**Analogy:** Like an electrician confirming the breaker is on, the multimeter reads 120V, and the wire is the right gauge — *before* they start splicing. Lab discipline saves debug hours.

**Expected output:**

```
   Static hostname: rhcsa1.example.com
         Icon name: computer-vm
           Chassis: vm
  Operating System: Red Hat Enterprise Linux 9.3 (Plow)
            Kernel: Linux 5.14.0-362.el9.x86_64
systemd 252 (252-18.el9)
/usr/bin/logger
```

**Switches**

| Token | Meaning |
|---|---|
| `sudo -i` | Open a real root shell (loads root's profile) |
| `hostnamectl` | Print machine identity |
| `systemctl --version` | Print systemd's own version |
| `which logger` | Find the absolute path of a binary on `$PATH` |
| `mkdir -p` | Make directory; don't error if it exists |

**Output decoded**

| Line | Meaning |
|---|---|
| `Red Hat Enterprise Linux 9.x` | You're on a system whose default scheduler is systemd timers |
| `systemd 252` | Modern enough; `OnCalendar`, `Persistent`, `AccuracySec` all supported |
| `/usr/bin/logger` | The exact string you'll put in `ExecStart=` |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `sudo: command not found` | Log in as root directly with `su -` |
| `logger: command not found` | Install with `dnf install -y util-linux` |
| `hostnamectl` shows wrong hostname | Set it: `hostnamectl set-hostname rhcsa1.example.com` |

---

### Task 2 — Survey the timers already running on the system

**Purpose:** RHEL ships with ~10 system timers out of the box. Reading them teaches you the conventions before you write your own.

```bash
systemctl list-timers --all
```

**Human-Readable Breakdown:**
> "Hey systemd, show me every timer you know about — active, inactive, all of them. For each one tell me when it'll next fire, when it last fired, what service it triggers, and whether it's currently enabled."

**Reading it left to right:**
- `systemctl` → "the front-end command for talking to systemd."
- `list-timers` → "subcommand that walks every loaded `.timer` unit and prints scheduling info."
- `--all` → "include disabled and inactive timers, not just the active ones."

**The story:** Before you write your first `.timer` unit, read fifteen real ones. RHEL 9 ships timers for `dnf-makecache`, `logrotate`, `man-db`, `mlocate-updatedb`, `systemd-tmpfiles-clean`, and friends. Each is a working example of the exact syntax you're about to use. The columns also show you the **firing convention everyone follows**: human-readable description, monotonic-friendly schedule for system housekeeping, `Persistent=true` for the ones that mustn't be skipped.

**Analogy:** Like watching a chef work the line before you take a station. You'll absorb conventions in five minutes that no documentation will teach you in five hours.

**Expected output:**

```
NEXT                        LEFT      LAST                        PASSED      UNIT                       ACTIVATES
Sat 2026-05-23 00:00:00 EDT 12h left  Fri 2026-05-22 00:00:00 EDT 11h ago     logrotate.timer            logrotate.service
Sat 2026-05-23 01:43:21 EDT 14h left  Fri 2026-05-22 01:43:21 EDT 9h ago      dnf-makecache.timer        dnf-makecache.service
Sun 2026-05-24 03:35:09 EDT 1 day     Sun 2026-05-17 03:35:09 EDT 4 days ago  man-db.timer               man-db.service
...
8 timers listed.
```

**Switches**

| Token | Meaning |
|---|---|
| `list-timers` | List loaded timer units |
| `--all` | Include inactive/disabled timers in the output |

**Output decoded**

| Column | Meaning |
|---|---|
| `NEXT` / `LEFT` | When the timer will fire and how long from now |
| `LAST` / `PASSED` | When it last fired and how long ago |
| `UNIT` | The `.timer` filename |
| `ACTIVATES` | The `.service` that gets started when the timer fires |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `0 timers listed` | systemd isn't PID 1 (you're in a container without systemd). Test on a real VM. |

---

### Task 3 — Read an existing timer unit to learn the conventions

**Purpose:** Reading a known-good `.timer` is the fastest way to internalize the file shape.

```bash
systemctl cat logrotate.timer
```

**Human-Readable Breakdown:**
> "Hey systemd, dump the full text of the `logrotate.timer` unit — and include every drop-in override that might be layered on top of it. I want to see the exact `[Unit]`, `[Timer]`, and `[Install]` sections so I can copy the conventions."

**Reading it left to right:**
- `systemctl cat` → "subcommand that prints a unit's source plus any drop-in `*.conf` files, in the exact order systemd applies them."
- `logrotate.timer` → "the unit name. Note the literal `.timer` extension — systemd needs it to disambiguate from `logrotate.service`."

**The story:** Every RHEL admin reads `systemctl cat` before writing their first unit, and most reach for it again every time they need a syntactic reminder six months later. The output shows you exactly what fields Red Hat themselves use, in exactly the order they use them. Beats Googling.

**Analogy:** Reading a working novel before you write your own short story. You absorb pacing, vocabulary, and section breaks without thinking about them.

**Expected output:**

```ini
# /usr/lib/systemd/system/logrotate.timer
[Unit]
Description=Daily rotation of log files
Documentation=man:logrotate(8) man:logrotate.conf(5)

[Timer]
OnCalendar=daily
AccuracySec=1h
Persistent=true

[Install]
WantedBy=timers.target
```

**Switches**

| Token | Meaning |
|---|---|
| `systemctl cat UNIT` | Show the source of a unit + any drop-in overrides |
| `Documentation=` | Pointers to the relevant man pages |
| `OnCalendar=daily` | Shortcut for `*-*-* 00:00:00` |

**Output decoded**

| Line | Meaning |
|---|---|
| `AccuracySec=1h` | Sloppy by 1 hour — Red Hat doesn't care exactly *when* logs rotate, only that they do |
| `Persistent=true` | If the box was off at midnight, rotate on next boot |
| `WantedBy=timers.target` | Pulled in by `systemctl enable` because timers.target is in the default dependency graph |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `No files found for logrotate.timer` | Install `logrotate`: `dnf install -y logrotate` |

---

### Task 4 — Read the matching service unit

**Purpose:** Confirm your mental model that the `.timer` triggers a sibling `.service`.

```bash
systemctl cat logrotate.service
```

**Human-Readable Breakdown:**
> "Show me the service unit that `logrotate.timer` actually starts. I want to see how it links the schedule (timer) to the work (service), what `Type=` it uses, what command it runs, and what dependencies it declares."

**Reading it left to right:**
- `systemctl cat` → "same dump-the-unit subcommand as before."
- `logrotate.service` → "this time the `.service` sibling. Note the *same basename* — that's the default convention that lets the timer find it without an explicit `Unit=` line."

**The story:** Timer/service pairs almost always share a basename (`foo.timer` ↔ `foo.service`). systemd assumes this by default — you only need an explicit `Unit=` directive in the timer if you want to break the convention. Reading the pair side-by-side confirms how the schedule and the work decouple.

**Analogy:** Reading the doorbell wiring (timer) and then the chime (service). One triggers the other through a single named wire.

**Expected output:**

```ini
# /usr/lib/systemd/system/logrotate.service
[Unit]
Description=Rotate log files
Documentation=man:logrotate(8) man:logrotate.conf(5)
ConditionACPower=true

[Service]
Type=oneshot
ExecStart=/usr/sbin/logrotate /etc/logrotate.conf
```

**Switches**

| Token | Meaning |
|---|---|
| `Type=oneshot` | Run once, exit, don't keep alive |
| `ExecStart=` | The command to run; **must be an absolute path** |
| `ConditionACPower=true` | Skip if running on battery (laptop courtesy) |

**Output decoded**

| Line | Meaning |
|---|---|
| No `[Install]` section | Correct — this service is started by the timer, not by `systemctl enable` |
| `Type=oneshot` | The exact pattern we'll mirror in `hellofolks.service` |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Confused about `Type=` choices | `oneshot` for scheduled jobs; `simple` is for daemons that stay alive |

---

### Task 5 — Create the target user `chisha`

**Purpose:** The exam scenario says the job runs *as user chisha*. Create the account so `User=chisha` in the service will work.

```bash
id chisha 2>/dev/null || useradd -m -s /bin/bash chisha
id chisha
```

**Human-Readable Breakdown:**
> "Hey shell, check whether user `chisha` already exists by trying to print her UID/GID. Suppress the error if she doesn't. If the `id` command failed (meaning no such user), run `useradd` to create her with a home directory and a real shell. Finally print her account info to confirm she exists now."

**Reading it left to right:**
- `id chisha` → "print UID, GID, and group memberships for user chisha. Returns non-zero if user doesn't exist."
- `2>/dev/null` → "redirect stderr to the bit bucket — we don't want the `id: 'chisha': no such user` error cluttering the terminal."
- `||` → "logical OR — only run the next command if the previous one *failed*."
- `useradd -m -s /bin/bash chisha` → "create user; `-m` makes the home directory at `/home/chisha`; `-s /bin/bash` sets her login shell."
- `id chisha` (final) → "print confirmation."

**The story:** Idempotent user creation is a daily Ansible/Bash idiom. The `id user || useradd user` pattern means "if she's already there, leave her alone; otherwise create her." You'll write this exact pattern in dozens of provisioning scripts. The `2>/dev/null` muffles the noise from the `id` failure so the script output stays clean.

**Analogy:** Like `mkdir -p` for users — it's the "create if missing, otherwise no-op" idiom of the user-management world.

**Expected output:**

```
uid=1001(chisha) gid=1001(chisha) groups=1001(chisha)
```

**Switches**

| Token | Meaning |
|---|---|
| `id USER` | Print account identity; exits non-zero if missing |
| `useradd -m` | Create home directory at `/home/USER` |
| `useradd -s` | Set login shell |
| `2>/dev/null` | Discard standard error |
| `\|\|` | Run next command only if previous failed |

**Output decoded**

| Field | Meaning |
|---|---|
| `uid=1001` | First non-system UID on a fresh RHEL box |
| `gid=1001` | Primary group with the same name as the user (RHEL convention) |
| No secondary groups | We didn't add `-G`; chisha isn't a member of `wheel` or any other group |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `useradd: user 'chisha' already exists` | The `id` check should prevent this; if it appears, somebody removed `2>/dev/null` |
| `Permission denied` | You forgot `sudo -i` in Task 1 |

---

### Task 6 — Draft the service unit file

**Purpose:** Write the `.service` unit that performs the actual work. Get this right before adding the timer on top.

```bash
cat > /etc/systemd/system/hellofolks.service <<'EOF'
[Unit]
Description=Write "hello folks" to syslog as user chisha
After=syslog.target

[Service]
Type=oneshot
User=chisha
ExecStart=/usr/bin/logger "hello folks"
EOF
```

**Human-Readable Breakdown:**
> "Hey shell, write a new file at `/etc/systemd/system/hellofolks.service`. Stuff it with a `[Unit]` section describing what it does and telling systemd not to run it until syslog is up. Add a `[Service]` section that says 'run once and exit (`Type=oneshot`), drop privileges to user `chisha` (`User=chisha`), and the command to run is `logger \"hello folks\"`.' No `[Install]` section — this service is started by a timer, not by `systemctl enable`."

**Reading it left to right:**
- `cat >` → "redirect the heredoc that follows into the file path on the left."
- `/etc/systemd/system/hellofolks.service` → "the canonical path for admin-defined system units. `/usr/lib/...` is for packages; `/etc/...` is for admins. systemd loads `/etc/...` *with higher priority* than `/usr/lib/...`."
- `<<'EOF' ... EOF` → "heredoc with **quoted** delimiter. The single quotes around `'EOF'` disable variable expansion inside, so `$LOGNAME` stays literal if we ever wanted it."
- `[Unit] / Description= / After=` → "metadata + scheduling constraint: don't start until `syslog.target` is reached."
- `[Service] / Type=oneshot / User=chisha / ExecStart=` → "the service body. `oneshot` = run-and-exit. `User=` = drop privileges. `ExecStart=` = absolute path to the binary plus its arguments."

**The story:** Three rules every admin learns on their first systemd unit, in order: (1) **absolute paths or it won't work** — systemd doesn't consult `$PATH`. (2) **`User=` lives in `[Service]`, not `[Unit]`** — privilege dropping is a service-level concept. (3) **No `[Install]` section on timer-driven services** — they're activated by the timer, not by `systemctl enable`. Putting `[Install]` here would just be dead code, and if you then run `systemctl enable hellofolks.service` it would try to start at boot instead of waiting for the timer.

**Analogy:** Writing the recipe before you set the timer. The recipe (`hellofolks.service`) says *what* to cook; the timer says *when* to cook it. You can rehearse the recipe by hand before automating the schedule.

**Expected output:**

The `cat` command produces no output; the file exists silently. Verify with:

```bash
cat /etc/systemd/system/hellofolks.service
```

**Switches**

| Token | Meaning |
|---|---|
| `cat > path <<'EOF' ... EOF` | Write a heredoc to a file, literally (no expansion) |
| `After=syslog.target` | Soft ordering: run after syslog is up |
| `Type=oneshot` | Run once and exit |
| `User=chisha` | Drop privileges before exec |
| `ExecStart=` | Absolute path to the binary |

**Output decoded**

| File | Meaning |
|---|---|
| `/etc/systemd/system/hellofolks.service` | Admin-defined unit. Higher priority than `/usr/lib/...` |
| No `[Install]` section | Correct — started by timer, not by `enable` |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Heredoc captured a literal `$LOGNAME` | That's the quoting working as intended; use unquoted `<<EOF` for expansion |
| `Permission denied` writing to `/etc/systemd/system/` | Need root; rerun under `sudo -i` |

---

### Task 7 — Test the service by hand before adding the timer

**Purpose:** Always unit-test the service in isolation. If it doesn't work manually, the timer can't fix it.

```bash
systemctl daemon-reload
systemctl start hellofolks.service
systemctl status hellofolks.service --no-pager
```

**Human-Readable Breakdown:**
> "Hey systemd, re-read the unit files from disk because I just added a new one. Then manually start `hellofolks.service` one time — don't wait for any timer. Print its status so I can see whether it succeeded and what its exit code was."

**Reading it left to right:**
- `systemctl daemon-reload` → "rescan `/etc/systemd/system/` and `/usr/lib/systemd/system/`. **Every new or edited unit file requires this** or systemd serves you a stale cached version."
- `systemctl start hellofolks.service` → "manually fire the service. For `Type=oneshot`, this command blocks until the service exits."
- `systemctl status hellofolks.service` → "show: is it loaded, is it active, when did it last run, what was the exit code, last 10 log lines."
- `--no-pager` → "don't pipe through `less`; print straight to stdout. Lab-friendly."

**The story:** `systemctl daemon-reload` is the single most-forgotten command in systemd. Edit a unit, run `systemctl restart` without reloading, and you'll see the *old* unit fire. Burned-in habit: every time you save a `.service` or `.timer` file, immediately `daemon-reload`. The second discipline: **always test the service alone before adding the timer.** If `systemctl start hellofolks.service` fails for any reason — typo in path, missing user, SELinux denial — adding a timer doesn't make it work. It just makes the failure happen on a schedule.

**Analogy:** Testing the light bulb works before you wire it to the motion sensor. Verify the simplest possible path first.

**Expected output:**

```
● hellofolks.service - Write "hello folks" to syslog as user chisha
     Loaded: loaded (/etc/systemd/system/hellofolks.service; static)
     Active: inactive (dead) since Fri 2026-05-22 12:31:05 EDT; 1s ago
   Main PID: 14823 (code=exited, status=0/SUCCESS)
        CPU: 12ms

May 22 12:31:05 rhcsa1.example.com systemd[1]: Starting Write "hello folks" to syslog as user chisha...
May 22 12:31:05 rhcsa1.example.com logger[14823]: hello folks
May 22 12:31:05 rhcsa1.example.com systemd[1]: hellofolks.service: Deactivated successfully.
May 22 12:31:05 rhcsa1.example.com systemd[1]: Finished Write "hello folks" to syslog as user chisha.
```

**Switches**

| Token | Meaning |
|---|---|
| `daemon-reload` | Re-read all unit files from disk |
| `start` | Manually activate a unit |
| `status` | Show loaded/active/last-run/recent-logs |
| `--no-pager` | Print without piping through `less` |

**Output decoded**

| Line | Meaning |
|---|---|
| `Loaded: loaded` | systemd found and parsed the file |
| `Active: inactive (dead) since ...` | Correct for `Type=oneshot` — it ran and exited |
| `status=0/SUCCESS` | Exit code 0 |
| `logger[PID]: hello folks` | The actual work happened |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Failed to start: Unit not found` | Forgot `daemon-reload` |
| `status=217/USER` | The `User=` value doesn't match a real account (Task 5) |
| `Failed to locate executable logger` | Used a non-absolute path in `ExecStart=` |

---

### Task 8 — Confirm the log line landed in journald

**Purpose:** The whole point of the job is that "hello folks" reaches syslog. Verify it.

```bash
journalctl -u hellofolks.service --since "5 minutes ago" --no-pager
journalctl _COMM=logger --since "5 minutes ago" --no-pager | tail -5
```

**Human-Readable Breakdown:**
> "Hey journald, show me every log entry from the `hellofolks.service` unit in the last 5 minutes. Then separately show me the last 5 entries where the originating command was `logger` — that's the second, independent way to confirm the log line landed."

**Reading it left to right:**
- `journalctl -u UNIT` → "filter the journal by the systemd unit that produced the entry."
- `--since "5 minutes ago"` → "natural-language time filter."
- `--no-pager` → "lab-friendly direct output."
- `_COMM=logger` → "**journald field filter**: only entries where the command name (`/proc/PID/comm`) is `logger`."
- `tail -5` → "last 5 lines."

**The story:** journald is queryable in two complementary ways: by **unit** (`-u hellofolks.service`) or by **field** (`_COMM=logger`, `_UID=1001`, `PRIORITY=3`). Using both gives you cross-verification. If the unit query finds the line but the `_COMM=logger` query doesn't, something weird is happening. If neither finds it, your unit didn't actually execute `logger`. This kind of cross-check is how senior admins debug "the timer says it fired but I don't see the result."

**Analogy:** Like checking a delivery on the company tracking system *and* on the courier's portal. Either alone could lie; together they prove the package arrived.

**Expected output:**

```
May 22 12:31:05 rhcsa1.example.com systemd[1]: Starting Write "hello folks" to syslog as user chisha...
May 22 12:31:05 rhcsa1.example.com logger[14823]: hello folks
May 22 12:31:05 rhcsa1.example.com systemd[1]: hellofolks.service: Deactivated successfully.
May 22 12:31:05 rhcsa1.example.com systemd[1]: Finished Write "hello folks" to syslog as user chisha.

May 22 12:31:05 rhcsa1.example.com logger[14823]: hello folks
```

**Switches**

| Token | Meaning |
|---|---|
| `-u UNIT` | Filter by systemd unit |
| `--since "5 minutes ago"` | Natural-language time window |
| `_COMM=logger` | journald metadata field filter |
| `tail -5` | Last 5 lines |

**Output decoded**

| Line | Meaning |
|---|---|
| `Starting ... / Finished` | systemd's own lifecycle log entries |
| `logger[PID]: hello folks` | The actual payload — the line we wanted to write |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| No entries | Run Task 7 again — service didn't fire |
| `-- No entries --` even after start | `User=chisha` might be writing to chisha's user journal; try `journalctl _UID=$(id -u chisha)` |

---

### Task 9 — Draft the timer unit file

**Purpose:** Write the `.timer` that schedules the already-working service.

```bash
cat > /etc/systemd/system/hellofolks.timer <<'EOF'
[Unit]
Description=Trigger hellofolks.service Mon–Fri at 02:00

[Timer]
OnCalendar=Mon..Fri *-*-* 02:00:00
Persistent=true
Unit=hellofolks.service

[Install]
WantedBy=timers.target
EOF
```

**Human-Readable Breakdown:**
> "Hey shell, write a new file at `/etc/systemd/system/hellofolks.timer`. Give it a `[Unit]` section describing what it does. Give it a `[Timer]` section with the canonical 'Monday through Friday at 2:00 AM' calendar expression, plus `Persistent=true` so it catches up after downtime, plus an explicit `Unit=hellofolks.service` (which is the default anyway, but being explicit documents intent). Finally a `[Install]` section so `systemctl enable` knows to wire it into `timers.target` at boot."

**Reading it left to right:**
- `[Unit] / Description=` → "metadata."
- `[Timer]` → "the scheduling section."
- `OnCalendar=Mon..Fri *-*-* 02:00:00` → "the schedule. Day-of-week list (Mon through Fri), any date, exact time 02:00:00."
- `Persistent=true` → "if the box was off at 02:00, run it on next boot to catch up."
- `Unit=hellofolks.service` → "explicit target. The default would have been the same — `<basename>.service` — but writing it out is good documentation."
- `[Install] / WantedBy=timers.target` → "tells `systemctl enable` to symlink this into `timers.target.wants/`. Without this section, `enable` will refuse to do anything."

**The story:** The three-section shape (`[Unit]`, `[Timer]`, `[Install]`) is universal across every timer you'll ever write. The `[Install]` section is the one beginners forget — leave it out and `systemctl enable hellofolks.timer` returns "The unit has no installation config." Memorize: **every timer needs `WantedBy=timers.target`** unless you have a specific reason otherwise. `Persistent=true` is the second beginner gotcha — without it, jobs missed during downtime are gone forever, which violates the whole reason you switched from cron.

**Analogy:** Writing the alarm clock spec sheet: when to fire (`OnCalendar`), what to ring (`Unit=`), whether to make up missed alarms (`Persistent=`), and how to install it on the bedside table at boot (`WantedBy=`).

**Expected output:**

No output; the file is written silently. Verify with `cat /etc/systemd/system/hellofolks.timer`.

**Switches**

| Token | Meaning |
|---|---|
| `OnCalendar=Mon..Fri *-*-* 02:00:00` | Day-of-week range + date wildcard + exact time |
| `Persistent=true` | Catch up missed runs after downtime |
| `Unit=foo.service` | Target service (default is matching basename) |
| `WantedBy=timers.target` | Install dependency so `enable` works |

**Output decoded**

| Line | Meaning |
|---|---|
| `[Timer]` section present | systemd recognizes this as a timer unit |
| `[Install]` section present | `systemctl enable` will succeed |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `The unit has no installation config` on `enable` | Missing or empty `[Install]` section |
| Timer never fires | Forgot `daemon-reload` after creating it, or forgot `--now` on `enable` |

---

### Task 10 — Validate the calendar expression with `systemd-analyze`

**Purpose:** Confirm the schedule string parses and prints the next firings *before* enabling the timer.

```bash
systemd-analyze calendar 'Mon..Fri *-*-* 02:00:00' --iterations=5
```

**Human-Readable Breakdown:**
> "Hey systemd-analyze, parse this calendar expression as if it were inside an `OnCalendar=` line. Tell me whether it's valid, normalize it to canonical form, show me what timezone you'd use, and project the next 5 firings as actual wall-clock timestamps."

**Reading it left to right:**
- `systemd-analyze calendar` → "subcommand specifically for parsing/testing `OnCalendar=` expressions."
- `'Mon..Fri *-*-* 02:00:00'` → "the expression in quotes so the shell doesn't try to glob `*`."
- `--iterations=5` → "project the next 5 fire times."

**The story:** Every expression you write should be validated this way *before* you put it in a file. It catches typos ("Mon..Fir" → "Failed to parse calendar specification") instantly, and shows you the exact wall-clock moments — which is invaluable when the exam clock is ticking and you want to be sure you didn't accidentally schedule for AM-vs-PM. Senior admins use this every time they touch a calendar expression. There is no faster sanity check.

**Analogy:** Like running a regex through a regex tester before shipping it to production. Five seconds of validation saves an hour of "the cron job didn't fire" debugging.

**Expected output:**

```
  Original form: Mon..Fri *-*-* 02:00:00
Normalized form: Mon..Fri *-*-* 02:00:00
    Next elapse: Mon 2026-05-25 02:00:00 EDT
       (in UTC): Mon 2026-05-25 06:00:00 UTC
       From now: 2 days left
    Iter. #2: Tue 2026-05-26 02:00:00 EDT
    Iter. #3: Wed 2026-05-27 02:00:00 EDT
    Iter. #4: Thu 2026-05-28 02:00:00 EDT
    Iter. #5: Fri 2026-05-29 02:00:00 EDT
```

**Switches**

| Token | Meaning |
|---|---|
| `systemd-analyze calendar` | Calendar-expression parser/projector |
| `--iterations=N` | Project N future firings |

**Output decoded**

| Line | Meaning |
|---|---|
| `Original form` / `Normalized form` | Confirms parser accepted and shows canonical form |
| `Next elapse` | Exact wall-clock moment of the very next fire |
| Iter. #2..N | Subsequent fires; confirms the pattern repeats correctly |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Failed to parse calendar specification` | Typo. Check `Mon..Fri` (two dots, no spaces), `*-*-*` (three stars, two dashes) |
| Wrong timezone | Set with `timedatectl set-timezone America/New_York` |

---

### Task 11 — Reload systemd and enable the timer

**Purpose:** Wire the timer into systemd's active state.

```bash
systemctl daemon-reload
systemctl enable --now hellofolks.timer
```

**Human-Readable Breakdown:**
> "Hey systemd, re-read the unit files because I added a new `.timer`. Then enable it (so it survives a reboot) **and** start it right now (the `--now` flag) so I don't have to wait for the next boot to see it scheduled."

**Reading it left to right:**
- `systemctl daemon-reload` → "rescan unit files."
- `systemctl enable` → "create the symlink `/etc/systemd/system/timers.target.wants/hellofolks.timer -> /etc/systemd/system/hellofolks.timer`. Survives reboot."
- `--now` → "additionally start the timer immediately. Equivalent to `enable && start`."
- `hellofolks.timer` → "the unit name with explicit `.timer` extension."

**The story:** `enable` and `start` are *two different things* and beginners conflate them constantly. **`enable`** makes the unit start *at next boot*; **`start`** makes it active *right now*. The `--now` shortcut does both in one command and is the conventional way to bring a timer online. Forget it and your timer is installed but inert until you reboot — a confusing failure mode where `list-timers` shows nothing.

**Analogy:** `enable` is "wire the doorbell to the breaker." `start` is "flip the breaker on." `--now` is "wire it *and* flip it" in one motion.

**Expected output:**

```
Created symlink /etc/systemd/system/timers.target.wants/hellofolks.timer → /etc/systemd/system/hellofolks.timer.
```

**Switches**

| Token | Meaning |
|---|---|
| `enable` | Make the unit start at boot (creates a symlink in `*.wants/`) |
| `--now` | Also start it immediately |
| `disable --now` | Stop and remove from boot |

**Output decoded**

| Line | Meaning |
|---|---|
| `Created symlink ... → ...` | The `[Install]` section's `WantedBy=` was honored |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `The unit files have no installation config` | Missing `[Install]` section in the timer (Task 9) |
| `Unit hellofolks.timer not found` | Forgot `daemon-reload` |

---

### Task 12 — Verify the timer appears in `list-timers`

**Purpose:** Confirm systemd has accepted the schedule and queued the next firing.

```bash
systemctl list-timers hellofolks.timer --no-pager
```

**Human-Readable Breakdown:**
> "Hey systemd, just show me the timer I care about — `hellofolks.timer` — and tell me when it'll next fire, when it last fired (probably never), what service it triggers, and that it's currently active."

**Reading it left to right:**
- `systemctl list-timers` → "subcommand for the timer-overview table."
- `hellofolks.timer` → "filter to just this one."
- `--no-pager` → "direct stdout."

**The story:** This is the **exam-day proof line.** If `list-timers` shows your unit with a sensible `NEXT` column, you can hand the exam over. If it shows nothing or `n/a`, you have a real problem and need to debug before moving on. Many candidates skip this step and find out at boot that their timer is dead.

**Analogy:** The receipt printer at the end of a fast-food order. Until you see your order on the screen, you don't actually know the cashier punched it in.

**Expected output:**

```
NEXT                        LEFT      LAST PASSED UNIT               ACTIVATES
Mon 2026-05-25 02:00:00 EDT 2 days    -    -      hellofolks.timer   hellofolks.service

1 timers listed.
```

**Switches**

| Token | Meaning |
|---|---|
| `list-timers UNIT` | Filter to a single timer |

**Output decoded**

| Column | Meaning |
|---|---|
| `NEXT` | Next wall-clock firing |
| `LEFT` | Time until next firing |
| `LAST` / `PASSED` | `-` because the timer has never fired yet |
| `ACTIVATES` | Confirms the timer points at `hellofolks.service` |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `0 timers listed` | Timer isn't active. Re-run `enable --now`. |
| `NEXT` shows `n/a` | Calendar expression didn't parse. Re-validate with Task 10. |

---

### Task 13 — Manually fire the timer-driven service to test the wiring

**Purpose:** Don't wait until Monday 2 AM to find out the wiring is wrong. Trigger the service through the timer's chain by starting the service directly.

```bash
systemctl start hellofolks.service
sleep 1
journalctl -u hellofolks.service --since "1 minute ago" --no-pager
```

**Human-Readable Breakdown:**
> "Hey systemd, simulate the timer firing by starting `hellofolks.service` directly. Wait a second for journald to flush. Then dump the last minute of log entries for that unit so I can read the result."

**Reading it left to right:**
- `systemctl start hellofolks.service` → "manually do what the timer will do at 02:00 Monday."
- `sleep 1` → "give journald a moment to commit. Sub-second flushes are journald's default."
- `journalctl -u hellofolks.service --since "1 minute ago" --no-pager` → "tail the journal scoped to this unit."

**The story:** The cardinal rule of timer development: **always rehearse the service path by hand.** If the service fails when you start it directly, the timer will fail at 2 AM exactly the same way — only you'll be asleep. By rehearsing now, you catch the failure on your timescale instead of systemd's.

**Analogy:** A fire drill. You run through the motions on a calm Tuesday morning so the real-fire response on a chaotic Saturday night is muscle memory.

**Expected output:**

```
May 22 12:45:02 rhcsa1.example.com systemd[1]: Starting Write "hello folks" to syslog as user chisha...
May 22 12:45:02 rhcsa1.example.com logger[15102]: hello folks
May 22 12:45:02 rhcsa1.example.com systemd[1]: hellofolks.service: Deactivated successfully.
May 22 12:45:02 rhcsa1.example.com systemd[1]: Finished Write "hello folks" to syslog as user chisha.
```

**Switches**

| Token | Meaning |
|---|---|
| `systemctl start UNIT` | Manually activate |
| `journalctl -u UNIT` | Filter journal by unit |
| `sleep 1` | Wait 1 second |

**Output decoded**

| Line | Meaning |
|---|---|
| `logger[PID]: hello folks` | The payload was written |
| `Deactivated successfully` | `Type=oneshot` exited cleanly |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Service starts but no `hello folks` line | `logger` ran but as wrong user; check `User=` |
| `status=1/FAILURE` | Check `journalctl -u hellofolks.service -p err` for the cause |

---

### Task 14 — Confirm the service ran as `chisha`, not root

**Purpose:** `User=` is the most error-prone directive. Prove it actually dropped privileges.

```bash
journalctl _UID=$(id -u chisha) --since "5 minutes ago" --no-pager | tail -3
```

**Human-Readable Breakdown:**
> "Hey journald, show me only the journal entries whose originating process ran as user `chisha`'s UID — and just the last three of them. If our `hello folks` line appears here, `User=chisha` worked. If it doesn't, the service silently ran as root."

**Reading it left to right:**
- `_UID=$(id -u chisha)` → "journald field filter on user ID. `id -u chisha` returns `1001`; the shell substitutes it in."
- `journalctl _UID=1001` → "give me only entries from UID 1001."
- `--since` / `--no-pager` → "scope and lab-friendly output."
- `tail -3` → "last 3 entries."

**The story:** The infamous `User=` mistake is to put it in `[Unit]` instead of `[Service]`. systemd silently ignores it because `User=` isn't a `[Unit]` directive, and your job quietly runs as root. The only way to catch this is to filter the journal by the *actual* UID of the running process. Make this verification a habit on every privilege-dropping service you write.

**Analogy:** Checking the badge of the person who signed for your package. The shipping label said "deliver to Alice," but the only proof Alice got it is the signature.

**Expected output:**

```
May 22 12:45:02 rhcsa1.example.com logger[15102]: hello folks
```

**Switches**

| Token | Meaning |
|---|---|
| `_UID=N` | journald field filter on user ID |
| `id -u USER` | Print numeric UID of a user |
| `$(...)` | Command substitution; shell inlines the output |

**Output decoded**

| Line | Meaning |
|---|---|
| Line appears | `User=chisha` was honored; `logger` ran as UID 1001 |
| Empty output | The service ran as root; `User=` is in the wrong section |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| No output | Move `User=chisha` from `[Unit]` to `[Service]` and `daemon-reload` |
| `id: 'chisha': no such user` | Re-run Task 5 |

---

### Task 15 — Add `Persistent=true` and prove catch-up behavior

**Purpose:** A scheduled job you can't trust to run after downtime is worse than no job at all. Prove `Persistent=true` does what it says.

```bash
grep -q '^Persistent=' /etc/systemd/system/hellofolks.timer \
  || sed -i '/^OnCalendar=/a Persistent=true' /etc/systemd/system/hellofolks.timer

systemctl daemon-reload
systemctl restart hellofolks.timer
systemctl cat hellofolks.timer
```

**Human-Readable Breakdown:**
> "Hey shell, check whether the timer file already has a `Persistent=` line. If not, add `Persistent=true` on the line right after `OnCalendar=`. Then reload systemd's view of unit files, restart the timer to pick up the change, and re-print the unit so I can confirm the line is now there."

**Reading it left to right:**
- `grep -q '^Persistent='` → "quietly check (`-q` = no output, just exit code) whether a line starting with `Persistent=` already exists."
- `||` → "logical OR — only run the next command if the grep *failed*."
- `sed -i '/^OnCalendar=/a Persistent=true'` → "in-place edit (`-i`); `a` is the append command; insert `Persistent=true` *after* the line matching `^OnCalendar=`."
- `systemctl daemon-reload` → "rescan unit files."
- `systemctl restart hellofolks.timer` → "stop and re-start the timer so the new schedule takes effect."
- `systemctl cat hellofolks.timer` → "verify."

**The story:** `Persistent=true` is the single most important option that differentiates systemd timers from cron. Cron is fire-and-forget — if the machine was off, the run is gone. systemd remembers the last run time on disk; on next boot if a calendar event was missed, it runs it then. The idempotent-edit idiom (`grep -q || sed`) is also worth memorizing — it's the Bash version of "ensure this config line exists" and you'll write it a hundred times in shell scripts.

**Analogy:** A snooze button on the alarm clock. Cron has no snooze — if you slept through 6 AM, the alarm is just gone. systemd timers say "I'll go off the moment you wake up, sorry I missed you."

**Expected output:**

```ini
# /etc/systemd/system/hellofolks.timer
[Unit]
Description=Trigger hellofolks.service Mon–Fri at 02:00

[Timer]
OnCalendar=Mon..Fri *-*-* 02:00:00
Persistent=true
Unit=hellofolks.service

[Install]
WantedBy=timers.target
```

**Switches**

| Token | Meaning |
|---|---|
| `grep -q PATTERN FILE` | Quiet match; exit 0 if found, 1 otherwise |
| `sed -i '/MATCH/a TEXT' FILE` | After lines matching MATCH, insert TEXT |
| `\|\|` | OR; run next command if previous failed |
| `systemctl restart UNIT` | Stop + start to pick up new config |

**Output decoded**

| Line | Meaning |
|---|---|
| `Persistent=true` present | Catch-up enabled |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `sed: -e expression #1, char 0: unmatched '{'` | Typo in the sed expression; copy exactly |
| `Persistent=` line duplicated | The `grep -q` guard failed somehow; remove duplicates by hand |

---

### Task 16 — Tighten the firing accuracy

**Purpose:** Default `AccuracySec=1min` is fine for housekeeping but loose for exam scenarios. Lower it.

```bash
grep -q '^AccuracySec=' /etc/systemd/system/hellofolks.timer \
  || sed -i '/^Persistent=/a AccuracySec=1s' /etc/systemd/system/hellofolks.timer

systemctl daemon-reload
systemctl restart hellofolks.timer
systemctl list-timers hellofolks.timer --no-pager
```

**Human-Readable Breakdown:**
> "Hey shell, idempotently add `AccuracySec=1s` to the timer unit so it fires within one second of `02:00:00` — not the default one-minute window. Reload, restart, and confirm the timer reschedules."

**Reading it left to right:**
- Same `grep -q || sed -i` idempotent-add idiom.
- `AccuracySec=1s` → "fire within ±1 second of the calendar moment."
- `daemon-reload` / `restart` → "pick up the change."
- `list-timers ...` → "confirm `NEXT` is still sensible."

**The story:** Default `AccuracySec=1min` exists because systemd tries to batch timer wakeups across the system to save power. For a laptop, that's the right tradeoff. For a production server running an exam-style scheduled job, you want predictability — set `1s` and accept the tiny extra power cost. Many real-world production timers use `AccuracySec=1s` for the same reason.

**Analogy:** Choosing between a quartz watch (`1s`) and a sundial (`1h`). Quartz costs a tiny bit more energy; you almost always want it for the precision.

**Expected output:**

```
NEXT                        LEFT      LAST PASSED UNIT               ACTIVATES
Mon 2026-05-25 02:00:00 EDT 2 days    -    -      hellofolks.timer   hellofolks.service

1 timers listed.
```

**Switches**

| Token | Meaning |
|---|---|
| `AccuracySec=1s` | Fire within ±1 second |
| `AccuracySec=1h` | Fire within ±1 hour (default for `logrotate`) |

**Output decoded**

| Line | Meaning |
|---|---|
| `NEXT` unchanged | Schedule still correct after the edit |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `NEXT` becomes `n/a` | Accidentally broke `OnCalendar` — re-read `systemctl cat hellofolks.timer` |

---

### Task 17 — Inspect the unit's full effective configuration

**Purpose:** `systemctl show` dumps every field systemd computed, including defaults you didn't set. Great for diffing two units.

```bash
systemctl show hellofolks.timer | grep -E '^(OnCalendar|Persistent|AccuracySec|Unit|RandomizedDelaySec|WakeSystem)='
```

**Human-Readable Breakdown:**
> "Hey systemd, dump every internal property of `hellofolks.timer` — including the ones I didn't set (those use defaults). Pipe to `grep` and filter to just the directives I actually care about, so I don't have to read 200 lines of irrelevant defaults."

**Reading it left to right:**
- `systemctl show UNIT` → "print every property as `Key=Value` pairs, ~200 lines for a typical unit."
- `\|` → "pipe stdout into the next command."
- `grep -E PATTERN` → "extended regex grep."
- `^(A\|B\|C)=` → "match lines starting with any of the listed property names followed by `=`."

**The story:** `systemctl show` is the **authoritative source** of "what is this unit actually configured to do." `systemctl cat` shows what you *wrote*; `systemctl show` shows what systemd *parsed and applied*, including defaults. When two engineers disagree about why a timer is misbehaving, `systemctl show | diff` is the tiebreaker.

**Analogy:** `cat` shows your recipe card; `show` shows what the chef actually heard, including the salt they added by reflex.

**Expected output:**

```
OnCalendar=Mon..Fri *-*-* 02:00:00
Persistent=yes
AccuracySec=1s
Unit=hellofolks.service
RandomizedDelaySec=0
WakeSystem=no
```

**Switches**

| Token | Meaning |
|---|---|
| `systemctl show UNIT` | Dump every parsed property |
| `grep -E '^(A\|B)='` | Filter to specific properties |

**Output decoded**

| Line | Meaning |
|---|---|
| `Persistent=yes` | systemd canonicalizes `true` to `yes` |
| `RandomizedDelaySec=0` | Default — no jitter |
| `WakeSystem=no` | Default — won't wake from suspend |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Properties don't match what you put in `cat` | You forgot `daemon-reload` after edit |

---

### Task 18 — Inspect the timer's recent history with `--since` boundaries

**Purpose:** Every real ops question after deploying a timer is "did it run yesterday/last week/last month?"

```bash
journalctl -u hellofolks.service --since "1 hour ago" --until "now" --no-pager
journalctl -u hellofolks.timer   --since "1 hour ago" --until "now" --no-pager
```

**Human-Readable Breakdown:**
> "Hey journald, show me everything that happened to `hellofolks.service` in the last hour, and separately show everything that happened to `hellofolks.timer`. The service log tells me what work ran; the timer log tells me when systemd kicked it."

**Reading it left to right:**
- `journalctl -u hellofolks.service` → "scope to the service."
- `--since "1 hour ago" --until "now"` → "explicit time window."
- Same for `-u hellofolks.timer` → "scope to the timer."

**The story:** Each `.timer` *and* its `.service` produce their own journal entries. The timer logs "I fired at 02:00:00"; the service logs the actual run. When troubleshooting "the job didn't happen," check both: if the timer log is empty, the schedule isn't firing; if the timer fired but the service log is empty, the wiring between them is broken.

**Analogy:** Two cameras at the same event — one on the doorbell, one on the chime. Watch both to figure out which link in the chain broke.

**Expected output:**

```
-- Logs begin at Fri 2026-05-22 12:00:00 EDT, end at Fri 2026-05-22 13:00:00 EDT --
May 22 12:45:02 rhcsa1.example.com systemd[1]: Starting hellofolks.service...
May 22 12:45:02 rhcsa1.example.com logger[15102]: hello folks
May 22 12:45:02 rhcsa1.example.com systemd[1]: hellofolks.service: Deactivated successfully.

May 22 12:42:00 rhcsa1.example.com systemd[1]: Started Trigger hellofolks.service Mon–Fri at 02:00.
```

**Switches**

| Token | Meaning |
|---|---|
| `--since "TIME"` | Lower bound |
| `--until "TIME"` | Upper bound |

**Output decoded**

| Section | Meaning |
|---|---|
| Service block | Per-firing logs of the work |
| Timer block | Per-firing logs of the schedule itself |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Service log empty but timer log shows fires | The timer's `Unit=` points at the wrong service |
| Both logs empty | Calendar string never matched a moment in your window |

---

### Task 19 — Clean teardown for re-runs

**Purpose:** Be able to disable, remove, and reinstall the timer cleanly so the lab is repeatable.

```bash
systemctl disable --now hellofolks.timer
rm -f /etc/systemd/system/hellofolks.timer
rm -f /etc/systemd/system/hellofolks.service
systemctl daemon-reload
systemctl reset-failed
systemctl list-timers hellofolks.timer --no-pager 2>&1 | head -2
```

**Human-Readable Breakdown:**
> "Hey systemd, stop the timer right now and remove it from the boot sequence (`disable --now`). Delete both the timer and service files from disk. Re-scan unit files. Clear any lingering 'failed' state. Then ask if the timer is still known — it shouldn't be."

**Reading it left to right:**
- `systemctl disable --now hellofolks.timer` → "stop and unlink from `timers.target.wants/`."
- `rm -f /etc/systemd/system/hellofolks.timer` → "remove the timer file. `-f` so it won't error if it's already gone."
- `rm -f /etc/systemd/system/hellofolks.service` → "remove the service file too."
- `systemctl daemon-reload` → "rescan so systemd forgets the units."
- `systemctl reset-failed` → "clear any 'failed' indicators in systemd's state machine."
- `list-timers hellofolks.timer 2>&1 \| head -2` → "ask one more time; should show 0 timers."

**The story:** Teardown discipline matters in production — every lab eventually becomes a production deployment script, and the deployment script must be re-runnable. The four-step pattern `disable --now → rm → daemon-reload → reset-failed` is the canonical "remove this unit cleanly" sequence. Skip any step and weird remnants persist.

**Analogy:** Erasing a whiteboard before the next class. If you only erase the words and leave the diagram, the next teacher will get confused.

**Expected output:**

```
Removed /etc/systemd/system/timers.target.wants/hellofolks.timer.

0 timers listed.
```

**Switches**

| Token | Meaning |
|---|---|
| `disable --now` | Stop and remove from boot |
| `rm -f` | Force-remove; ignore if missing |
| `reset-failed` | Clear any failed-state markers |
| `2>&1` | Merge stderr into stdout |

**Output decoded**

| Line | Meaning |
|---|---|
| `Removed ... wants/...` | Symlink torn down |
| `0 timers listed` | systemd no longer knows about the unit |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Failed to disable unit: Unit hellofolks.timer not loaded` | Already gone; safe to ignore |
| `1 timers listed` after rm | Forgot `daemon-reload` |

---

### Task 20 — Capstone: full sandervongut exam scenario, end-to-end

**Task statement:** *"Schedule a systemd timer job that writes 'hello folks' to syslog every Monday through Friday at 2 AM. Make sure this job is executed as the user chisha."*

```bash
id chisha 2>/dev/null || useradd -m -s /bin/bash chisha

cat > /etc/systemd/system/hellofolks.service <<'EOF'
[Unit]
Description=Write "hello folks" to syslog as chisha
After=syslog.target

[Service]
Type=oneshot
User=chisha
ExecStart=/usr/bin/logger "hello folks"
EOF

cat > /etc/systemd/system/hellofolks.timer <<'EOF'
[Unit]
Description=Trigger hellofolks.service Mon–Fri at 02:00

[Timer]
OnCalendar=Mon..Fri *-*-* 02:00:00
Persistent=true
AccuracySec=1s
Unit=hellofolks.service

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now hellofolks.timer

systemd-analyze calendar 'Mon..Fri *-*-* 02:00:00' --iterations=3
systemctl list-timers hellofolks.timer --no-pager
systemctl start hellofolks.service
journalctl _UID=$(id -u chisha) --since "1 minute ago" --no-pager | tail -1
```

**Human-Readable Breakdown:**
> "End-to-end exam answer in one block. Idempotently create user `chisha`. Write a fresh `hellofolks.service` that runs `/usr/bin/logger \"hello folks\"` as `chisha`. Write a fresh `hellofolks.timer` that fires Mon–Fri at exactly 02:00:00 with catch-up and 1-second accuracy. Reload systemd. Enable and start the timer. Verify the schedule with `systemd-analyze calendar`. Verify the timer is queued with `list-timers`. Manually fire the service to rehearse. Confirm via journald that `logger` ran as `chisha`."

**Reading it left to right:**

| Block | What it does |
|---|---|
| `id chisha 2>/dev/null \|\| useradd ...` | Create chisha if absent |
| `cat > .../hellofolks.service <<'EOF' ... EOF` | Write the service unit |
| `cat > .../hellofolks.timer <<'EOF' ... EOF` | Write the timer unit |
| `systemctl daemon-reload` | Re-scan unit files |
| `systemctl enable --now hellofolks.timer` | Install + start the timer |
| `systemd-analyze calendar 'Mon..Fri ...'` | Confirm the schedule parses to next 3 Mondays/etc. |
| `systemctl list-timers hellofolks.timer` | Confirm `NEXT` is set |
| `systemctl start hellofolks.service` | Rehearse the work path now |
| `journalctl _UID=$(id -u chisha) ...` | Cross-verify the log line was written by chisha |

**The story:** This is the **5-minute exam answer.** Memorize the structure of these two unit files; everything else (`grep -q || sed -i`, `Persistent=`, `AccuracySec=`, `systemd-analyze calendar`) is polish that you add on top once the bones are right. If you can type this block from memory in under 5 minutes, every "schedule a recurring task" exam question is a freebie.

**Analogy:** Like memorizing the closing chord progression of a classical piece. Every variation builds on the same three chords; once you can play the spine, the embellishments come for free.

**Expected output (last line is the proof):**

```
  Original form: Mon..Fri *-*-* 02:00:00
Normalized form: Mon..Fri *-*-* 02:00:00
    Next elapse: Mon 2026-05-25 02:00:00 EDT
       From now: 2 days left
    Iter. #2: Tue 2026-05-26 02:00:00 EDT
    Iter. #3: Wed 2026-05-27 02:00:00 EDT

NEXT                        LEFT      LAST PASSED UNIT               ACTIVATES
Mon 2026-05-25 02:00:00 EDT 2 days    -    -      hellofolks.timer   hellofolks.service

1 timers listed.
May 22 13:05:11 rhcsa1.example.com logger[15310]: hello folks
```

**Verification checklist**

| Step | Expected |
|---|---|
| `systemctl is-enabled hellofolks.timer` | `enabled` |
| `systemctl is-active hellofolks.timer` | `active` (waiting) |
| `systemctl list-timers hellofolks.timer` | Shows next Monday 02:00 |
| `journalctl _UID=$(id -u chisha)` | Shows `hello folks` |

**Cleanup**

```bash
systemctl disable --now hellofolks.timer
rm -f /etc/systemd/system/hellofolks.{service,timer}
systemctl daemon-reload
userdel -r chisha
```

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Mon..Fir` typo in `OnCalendar` | Re-read Task 10; use `systemd-analyze calendar` to validate |
| Service runs as root not chisha | `User=` is in `[Unit]` instead of `[Service]` — move it |
| Job missed and not caught up | Add `Persistent=true` (Task 15) |
| Timer fires but service log is empty | `Unit=` points at the wrong service basename |

---

## 🔍 Cron vs. systemd Timer Decision Guide

```
Got a scheduled job to write?
  │
  ├── Job has dependencies (network, mounts, other services)?
  │       └── ✅ Use a systemd timer with After= / Wants=
  │
  ├── Need to audit "did it run?" easily?
  │       └── ✅ systemd timer — journalctl -u <unit>
  │
  ├── Need to catch up missed runs after downtime?
  │       └── ✅ systemd timer with Persistent=true
  │
  ├── Need to run as a specific non-root user?
  │       └── ✅ systemd timer with User= in [Service]
  │       └── (cron works too, but systemd is cleaner)
  │
  ├── Single-line nightly job on a long-lived server?
  │       └── ⚖️  Cron is fine if you're not on the RHEL exam
  │
  └── RHEL exam question says "systemd timer"?
          └── ✅ Always answer with a timer; cron is a wrong answer here
```

---

## ✅ Lab Checklist (20 Tasks)

- [ ] 01 Verify lab environment + `logger` absolute path
- [ ] 02 Survey existing timers with `list-timers --all`
- [ ] 03 Read `logrotate.timer` with `systemctl cat`
- [ ] 04 Read `logrotate.service`
- [ ] 05 Create user `chisha` idempotently
- [ ] 06 Draft `/etc/systemd/system/hellofolks.service`
- [ ] 07 `daemon-reload` + test service manually
- [ ] 08 Cross-verify log line in journald
- [ ] 09 Draft `/etc/systemd/system/hellofolks.timer`
- [ ] 10 Validate the `OnCalendar=` string
- [ ] 11 `enable --now` the timer
- [ ] 12 Verify `list-timers` shows next firing
- [ ] 13 Rehearse-fire the service through the chain
- [ ] 14 Prove it ran as chisha via `_UID=` filter
- [ ] 15 Add `Persistent=true` idempotently
- [ ] 16 Add `AccuracySec=1s`
- [ ] 17 Inspect effective config with `systemctl show`
- [ ] 18 Read journalctl history of both units
- [ ] 19 Clean teardown
- [ ] 20 Capstone — full sandervongut scenario end-to-end

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Forgot `systemctl daemon-reload` after edit | Old behavior persists, "Unit not found" | Always `daemon-reload` after writing a unit file |
| Forgot `--now` on `enable` | `is-active` says `inactive`; `list-timers` empty | `systemctl enable --now UNIT` |
| Missing `[Install]` section | `enable` says "no installation config" | Add `[Install] / WantedBy=timers.target` |
| `User=` in `[Unit]` instead of `[Service]` | Job silently runs as root | Move it to `[Service]` |
| Non-absolute path in `ExecStart=` | `status=203/EXEC` | Use the full path (e.g. `/usr/bin/logger`) |
| Forgot `Persistent=true` | Missed runs after reboot are gone forever | Add it (Task 15) |
| `OnCalendar=Mon..Fir` typo | `Failed to parse calendar specification` | Validate with `systemd-analyze calendar` |
| Edited unit then `restart` without `daemon-reload` | Restart picks up old config | Reload first |
| Used `journalctl` without `-u` | Drowning in unrelated entries | Always scope to your unit |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- "Schedule a recurring task" is a near-guaranteed exam question on the EX200. Memorize the Task 20 capstone block — you should be able to type it from scratch in 5 minutes without a reference.

**RHCE candidate**
- The Ansible `ansible.builtin.systemd_service` and `ansible.builtin.copy` modules let you ship these unit files via a playbook. Practice writing a playbook that deploys `hellofolks.timer` and `hellofolks.service` to a fleet.

**SRE / Platform interview**
- Be ready to explain *why* systemd timers replaced cron: dependency-awareness, journald integration, catch-up via `Persistent=`, and exact "did it run?" status via `systemctl status`.

**DevOps**
- Know that container images intended for systemd (`registry.access.redhat.com/ubi9-init`) ship a working systemd PID 1 — your timers will work in containers if you use those base images.

**AI / MLOps**
- Scheduled retraining triggers, log aggregation, S3 sync, and model-drift checks are all natural fits for systemd timers on the underlying host. Anything you'd put in a Kubernetes CronJob outside the cluster.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| [Configure NTP Time Source](https://github.com/kelvintechnical/configure-ntp) | Timers rely on accurate wall-clock time — set NTP first |
| Lab — Create LV `lvol1` (ext4, 280MB) | Sibling RHCSA scheduled-tasks vs. storage exam question |
| Schedule Tasks with cron *(coming soon)* | The thing systemd timers replace |
| Configure Persistent Journal Logs *(coming soon)* | Required infra for `journalctl --since` to work after reboots |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
