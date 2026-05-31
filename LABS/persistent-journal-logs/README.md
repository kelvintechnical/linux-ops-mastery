# Lab: Configure Persistent Journal Logs — `/var/log/journal`, `journald.conf`, `Storage=`

- **Series:** linux-ops-mastery — RHCSA Log Management
- **Subjects covered:** systemd-journald storage modes (`volatile`, `persistent`, `auto`, `none`), `/var/log/journal` directory semantics, `/etc/systemd/journald.conf` and drop-ins under `/etc/systemd/journald.conf.d/`, `SystemMaxUse=`, `SystemKeepFree=`, `MaxRetentionSec=`, `MaxFileSec=`, sealing (`Seal=`), `systemd-tmpfiles --create`, ACLs on `/var/log/journal` (`systemd-journal` group), validating with `journalctl --disk-usage` / `--list-boots` / `--verify`, rotating with `journalctl --rotate` and `--vacuum-size=`/`--vacuum-time=`
- **Career arcs covered:** RHCSA (EX200 — "ensure journal survives reboot"), RHCE (Ansible idempotent journald.conf drop-ins), SRE (incident timelines that span multiple boots), DevOps (CI image bake step that pre-creates `/var/log/journal`), AI / MLOps (preserving GPU-node crash history through autoscaler restarts)
- **Prerequisite:** Lab 101 (Query Logs with `journalctl`)
- **Time Estimate:** 30 to 45 minutes
- **Difficulty arc:** Tasks 1–2 baseline (what's there now) · Tasks 3–4 create the directory and validate · Task 5 first reboot proof · Tasks 6–7 size and retention tuning via drop-ins · Task 8 sealing + verify · Task 9 manual rotation and vacuum · Task 10 capstone (Ansible-style report + cleanup with a safe revert)

---

## Objective

Stop losing logs on reboot. By the end of this lab you can turn a volatile RHEL journal into a **persistent, size-capped, retention-bound, sealed** journal that survives reboots, automatically rotates, and exposes its history to `journalctl -b -1`. You will also know how to revert without losing data, how to reload `journald.conf` without restarting the host, and how to verify integrity after an unclean shutdown.

The capstone is the **engineer-realistic prompt:** *"Make this RHEL 9 host's journal persistent, cap it at 1 GiB total / 200 MiB per file, retain at least 14 days, enable forward-secure sealing, prove it survives a reboot, and write a one-paragraph report. Then leave a clean revert path."*

> **Lab safety note:** Everything in this lab is reversible. Task 10 documents the revert path. The only filesystem write outside `/etc/systemd/` is creating `/var/log/journal/` itself, which is harmless even if you decide to undo it.

---

## Concept: Volatile vs Persistent — One Directory Flips the Switch

`systemd-journald` decides where to store journals at startup based on three signals: the `Storage=` directive in `journald.conf`, whether `/var/log/journal/` exists, and whether `/run/log/journal/` exists. The default `Storage=auto` means "**persistent if `/var/log/journal/` exists, otherwise volatile in `/run/log/journal/`.**"

```
  ┌────────────────────────────────────────────────────────────┐
  │ Storage= directive in /etc/systemd/journald.conf           │
  │   ├── volatile   → always /run/log/journal (RAM, lost on   │
  │   │                 reboot)                                │
  │   ├── persistent → always /var/log/journal (disk; create   │
  │   │                 if missing)                            │
  │   ├── auto       → /var/log/journal if it exists, else    │
  │   │                 /run/log/journal  (DEFAULT)            │
  │   └── none       → discard everything                      │
  │                                                            │
  │ Path semantics                                             │
  │   /var/log/journal/<MACHINE-ID>/system.journal             │
  │   /var/log/journal/<MACHINE-ID>/user-<UID>.journal         │
  │                                                            │
  │ Group / ACL                                                │
  │   owner root, group systemd-journal, mode 2755             │
  │   members of 'adm' or 'systemd-journal' read non-root      │
  └────────────────────────────────────────────────────────────┘
```

> **Why this matters:** A volatile journal is fine on an idempotent immutable VM that re-streams logs to a remote sink, but on a stand-alone server or a lab box you will lose every clue the moment something OOM-kills the host. **Persistent + size cap + retention** is the production baseline.

---

## 📜 Why Persistent Journal Exists — The Story

When `systemd-journald` was introduced (2011), the default `Storage=auto` was a compromise: RAM-only storage avoided breaking systems that did not have spare disk, but it also meant *log evidence vanished at every reboot*. Operators who'd just spent a decade with `/var/log/messages` on disk hit this wall and complained loudly. The fix was deliberately **opt-in**: create `/var/log/journal/`, and the daemon notices and flips to disk-backed storage on the next start (or `kill -USR1` of `journald`).

This is unusual. Most Linux daemons read a single config flag — `journald` lets the **filesystem layout** of `/var/log` itself act as the switch. The motivation was that distros could ship the default off (saving small embedded systems disk) while making the persistent toggle a single `mkdir`. RHEL 9's installer also adds the directory automatically for server installs; lab/cloud images often skip it. Whether yours has it is a one-`ls` check, and Lab 102 fixes the gap.

> **The point of the story:** Persistence is a directory and a tiny config drop-in. The configuration is small. The benefits — `journalctl -b -1`, `--verify`, multi-boot incident timelines — are huge. RHCSA exam day will absolutely include "make journals survive reboot."

---

## 👪 The Persistence Family — Who Lives Where

```
Config
├── /etc/systemd/journald.conf                ← single canonical file
├── /etc/systemd/journald.conf.d/*.conf        ← drop-ins (preferred for changes)
└── /usr/lib/systemd/journald.conf.d/*.conf    ← distro defaults

Storage
├── /run/log/journal/<MACHINE-ID>/             ← volatile (RAM)
└── /var/log/journal/<MACHINE-ID>/             ← persistent (disk)

Tooling
├── journalctl --disk-usage                    ← total bytes
├── journalctl --list-boots                    ← visible boot history
├── journalctl --verify                        ← integrity + seal check
├── journalctl --rotate                        ← roll active file
├── journalctl --vacuum-size=SIZE              ← shrink archive to SIZE
├── journalctl --vacuum-time=AGE               ← drop archives older than AGE
└── systemctl kill -s USR1 systemd-journald    ← flush to /var/log/journal manually
```

### `journald.conf` directives that matter

| Directive | Default | Notes |
|---|---|---|
| `Storage=` | `auto` | `persistent` is the explicit form |
| `Compress=` | `yes` | LZ4 in transit, ~3-10x on text |
| `Seal=` | `yes` (when FSS key exists) | Forward-secure sealing — tamper-evident |
| `SystemMaxUse=` | 10% of FS, capped 4G | Total bytes for the persistent store |
| `SystemKeepFree=` | 15% of FS | Always leave at least this free |
| `SystemMaxFileSize=` | 1/8 of `SystemMaxUse=` | Per active journal file size |
| `SystemMaxFiles=` | 100 | Max number of archived files |
| `MaxRetentionSec=` | unset (no time cap) | Drop files older than this |
| `MaxFileSec=` | 1month | Rotate active file at this age |
| `ForwardToSyslog=` | `no` (RHEL default) | Tee to rsyslog |
| `RuntimeMaxUse=` | 10% of `/run` | Volatile equivalent |

> **Reading rule:** `SystemMaxUse` is a *cap*, not a target. The journal grows up to that cap, then deletes oldest files. `MaxRetentionSec` adds a time-based drop. Combine both for predictable storage.

---

## 📚 Persistence Reference Table

| Goal | Command | Notes |
|---|---|---|
| Read current storage mode | `systemd-analyze cat-config systemd/journald.conf` | Merged view across all drop-ins |
| Create the persistence directory | `sudo install -d -g systemd-journal -m 2755 /var/log/journal` | systemd-tmpfiles also does this |
| Apply tmpfiles snippet | `sudo systemd-tmpfiles --create --prefix /var/log/journal` | Creates with correct mode/ownership |
| Flush volatile to persistent | `sudo killall -USR1 systemd-journald` *or* `systemctl kill -s USR1 systemd-journald` | Triggers move from `/run` to `/var` |
| Reload config without restart | `sudo systemctl kill -s SIGUSR2 systemd-journald` (rotate) + `sudo systemctl restart systemd-journald` | journald does not honor `reload` — restart it |
| Verify integrity / seal | `sudo journalctl --verify` | Checks every journal file |
| Vacuum to size | `sudo journalctl --vacuum-size=200M` | Drop oldest archives |
| Vacuum by time | `sudo journalctl --vacuum-time=14d` | Drop entries older than 14 days |
| Show on-disk size | `journalctl --disk-usage` | One-line summary |
| Show retained boots | `journalctl --list-boots` | Proves persistence works |
| Disable persistence | Set `Storage=volatile` and `rm -rf /var/log/journal` | Reversible |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | EX200 will absolutely ask you to "configure journals to survive reboot." `mkdir /var/log/journal` + `systemctl restart systemd-journald` is the canonical answer. |
| **RHCE candidate** | Ansible: a `community.general.ini_file` task that writes `/etc/systemd/journald.conf.d/00-retention.conf` with idempotent directives, plus a handler to restart `systemd-journald`. |
| **SRE / Platform** | Persistent journals are the **only** local source of truth across reboots. Without them, post-mortems start with "we lost the logs." |
| **DevOps** | Bake `/var/log/journal/` into base AMIs so freshly provisioned hosts log persistently from second one. |
| **AI / MLOps** | When a training node OOMs and the autoscaler replaces it, persistent journals on a snapshot let you replay the last 30 minutes of CUDA and NCCL messages. |

---

## 🔧 The 10 Tasks

> Ten phases that build the **inspect → create directory → tune retention → seal → vacuum → verify across reboots** habit.

---

### Task 1 — Set up the sandbox and capture the volatile baseline

**Purpose:** Build a scratch directory, capture the current `Storage=` value, journal location, and disk usage so you can prove the persistence flip in Task 5.

```bash
sudo -i
mkdir -p /root/journal-persist-lab && cd /root/journal-persist-lab

ls -ld /var/log/journal 2>&1 | tee 01-var-journal-before.txt
ls -ld /run/log/journal 2>&1 | tee 01-run-journal-before.txt
systemd-analyze cat-config systemd/journald.conf | tee 01-journald-conf.txt
grep -E '^#?\s*Storage=' /etc/systemd/journald.conf | tee 01-storage-line.txt
journalctl --disk-usage | tee 01-disk-usage-before.txt
journalctl --list-boots | tee 01-list-boots-before.txt
```

**Human-Readable Breakdown:** Become root, create the workspace, capture whether `/var/log/journal/` exists (probably not), confirm `/run/log/journal/` exists (it does on every running RHEL), dump the merged `journald.conf`, isolate the `Storage=` line, and snapshot disk usage and boot history.

**Reading it left to right:** `ls -ld DIR` shows the directory's metadata without descending into it; the trailing `2>&1` captures the "No such file or directory" output as part of the baseline. `systemd-analyze cat-config` prints the **merged** view across `/usr/lib/`, `/etc/`, and drop-ins — important because `Storage=` may be set in a drop-in you didn't notice. `journalctl --list-boots` is the cleanest proof of persistence: a volatile journal lists only one boot.

**The story:** Half of the lab is **proof artifacts**. Snapshot the "before" state on disk in files so the capstone report can quote real numbers. Most RHCSA candidates get the technical changes right but lose points on "show your work" — these `tee` files are your evidence.

**Expected output:**

```text
ls: cannot access '/var/log/journal': No such file or directory
drwxr-sr-x. 3 root systemd-journal 60 Jan 14 09:00 /run/log/journal
# /usr/lib/systemd/journald.conf
[Journal]
#Storage=auto
#Compress=yes
#Seal=yes
...
#Storage=auto
Archived and active journals take up 8.0M in the file system.
-0 c0d911f2b56a4f5cb0e2a1f9b7c63d22 Tue 2026-01-14 09:00:11 EST—Tue 2026-01-14 09:30:18 EST
```

**Switches**

| Token | Meaning |
|---|---|
| `ls -ld DIR` | Show directory entry, not contents |
| `systemd-analyze cat-config FILE` | Merge `/usr/lib`, `/etc`, drop-ins |
| `journalctl --list-boots` | Visible boot history |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `/var/log/journal/` exists already | Persistence already on — go to Task 2 to confirm |
| `systemd-analyze` not found | Install `systemd` (always present on RHEL 9) |
| `--list-boots` shows many boots already | Persistence already on — adjust the lab plan |

---

### Task 2 — Read the effective `Storage=` value and the related directives

**Purpose:** Be precise about what `Storage=auto` means on this host *right now*, and which other directives are inherited from defaults.

```bash
cd /root/journal-persist-lab

grep -E '^\s*(Storage|Compress|Seal|SystemMaxUse|SystemKeepFree|MaxRetentionSec|MaxFileSec|ForwardToSyslog)=' \
  /etc/systemd/journald.conf /etc/systemd/journald.conf.d/*.conf /usr/lib/systemd/journald.conf.d/*.conf 2>/dev/null \
  | tee 02-effective-directives.txt

systemctl show systemd-journald.service -p Storage -p StateDirectory -p StateDirectoryMode 2>/dev/null | tee 02-unit-fields.txt
```

**Human-Readable Breakdown:** Grep every relevant directive across all known config locations (canonical file, system-wide drop-ins, distro drop-ins) so we know what is actually in effect — not just what's in the headline file.

**Reading it left to right:** `grep -E` enables extended regex. The pipe of file paths combines three search locations. `2>/dev/null` silences "No such file" if drop-in directories are empty. `systemctl show UNIT -p PROP` queries individual unit properties — not always useful for `journald.conf` values, but the habit is useful elsewhere.

**The story:** Read every drop-in before changing anything. Vendor packages and cloud images often add `/usr/lib/systemd/journald.conf.d/` drop-ins that override the `journald.conf` defaults. Edit those at your peril — your changes belong in `/etc/systemd/journald.conf.d/`.

**Expected output:**

```text
/etc/systemd/journald.conf:#Storage=auto
/etc/systemd/journald.conf:#Compress=yes
/etc/systemd/journald.conf:#Seal=yes
/etc/systemd/journald.conf:#SystemMaxUse=
/etc/systemd/journald.conf:#SystemKeepFree=
/etc/systemd/journald.conf:#MaxRetentionSec=
/etc/systemd/journald.conf:#MaxFileSec=1month
/etc/systemd/journald.conf:#ForwardToSyslog=no
```

**Switches**

| Token | Meaning |
|---|---|
| `grep -E` | Extended regex |
| Multiple paths to grep | One pass across canonical + drop-ins |
| `2>/dev/null` | Hide missing-path errors |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Every directive is commented out | That is normal — defaults apply |
| A drop-in overrides your expectation | Edit drop-in or override in `/etc/systemd/journald.conf.d/` |
| `systemctl show` returns empty `Storage` | systemd does not expose that property — read the file directly |

---

### Task 3 — Create `/var/log/journal/` with the correct ownership and mode

**Purpose:** Make the directory that flips `Storage=auto` from volatile to persistent. Use the **canonical** method (`install` or `systemd-tmpfiles`) — not a bare `mkdir`.

```bash
cd /root/journal-persist-lab

sudo install -d -g systemd-journal -m 2755 /var/log/journal
ls -ld /var/log/journal | tee 03-after-mkdir.txt

cat <<'EOF' | sudo tee /etc/tmpfiles.d/journal.conf >/dev/null
d /var/log/journal 2755 root systemd-journal - -
EOF
sudo systemd-tmpfiles --create /etc/tmpfiles.d/journal.conf
ls -ld /var/log/journal | tee 03-after-tmpfiles.txt
```

**Human-Readable Breakdown:** Create `/var/log/journal/` with mode `2755` (the SGID bit ensures new files inherit the `systemd-journal` group) and the `systemd-journal` group. Then write a small `tmpfiles.d` snippet so the directory is recreated on every boot if something deletes it.

**Reading it left to right:** `install -d` creates a directory with the specified `-g GROUP` and `-m MODE` in one call (safer than `mkdir + chgrp + chmod`). `2755` = `setgid + rwxr-xr-x` — the leading `2` is critical; without SGID, new journal files would be created with whatever group the user has. `systemd-tmpfiles --create` consumes `/etc/tmpfiles.d/journal.conf` and ensures the directory exists with the declared attributes.

**The story:** `mkdir -p /var/log/journal` works **technically**, but you'll lose the SGID bit and journals will inherit the wrong group. `install -d -m 2755 -g systemd-journal` is the one-liner Red Hat documents. The `tmpfiles.d` snippet is the **insurance policy** — if a backup-restore process or someone's `rm -rf` removes the directory, systemd recreates it on next boot.

**Expected output:**

```text
drwxr-sr-x. 2 root systemd-journal 6 Jan 14 09:31 /var/log/journal
drwxr-sr-x. 2 root systemd-journal 6 Jan 14 09:31 /var/log/journal
```

**Switches**

| Token | Meaning |
|---|---|
| `install -d` | Create directory with mode/owner/group |
| `-g GROUP` | Set group |
| `-m MODE` | Set mode (octal) |
| `2755` | SGID + rwxr-xr-x |
| `systemd-tmpfiles --create` | Apply tmpfiles snippet |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `install: cannot change ownership` | Re-run as root with `sudo` |
| Mode shows `0755` not `2755` | Re-run `install -d -m 2755 ...` — the SGID bit is critical |
| `systemd-journal` group missing | `getent group systemd-journal` — re-install `systemd` if missing |

---

### Task 4 — Restart `systemd-journald` and confirm it switches to persistent

**Purpose:** Force journald to notice the new directory and start writing into `/var/log/journal/<MACHINE-ID>/`. Validate with `journalctl --disk-usage` against `/var`.

```bash
cd /root/journal-persist-lab

sudo systemctl restart systemd-journald.service
sleep 1
sudo systemd-tmpfiles --create
ls /var/log/journal | tee 04-machine-id-dirs.txt
ls -lh /var/log/journal/*/system.journal 2>/dev/null | tee 04-system-journal.txt

journalctl --disk-usage | tee 04-disk-usage-after.txt
journalctl --list-boots | tee 04-list-boots-after.txt
```

**Human-Readable Breakdown:** Restart the daemon so it re-evaluates `/var/log/journal/`, list the `<MACHINE-ID>` subdirectory it created, and re-run the disk-usage and list-boots commands. Both should now reference disk paths and a growing on-disk size.

**Reading it left to right:** `systemctl restart` is the only way to get journald to re-read its storage decision — there is no `reload`. `ls /var/log/journal` shows the per-machine subdirectory journald created. `system.journal` is the active file. `journalctl --disk-usage` now reports on `/var/log/journal/` size, and `--list-boots` still shows a single boot — until you reboot in Task 5.

**The story:** The directory existed at start time; journald saw it; persistence is now on. But you have not actually **proved** persistence yet — that requires a reboot. Task 5 is the proof step.

**Expected output:**

```text
9e1ad2e8d6e54b6cb9d1f2bf8cb52f01
-rw-r-----+ 1 root systemd-journal 8.0M Jan 14 09:33 /var/log/journal/9e1ad.../system.journal
Archived and active journals take up 8.0M in the file system.
-0 c0d911f2b56a4f5cb0e2a1f9b7c63d22 Tue 2026-01-14 09:00:11 EST—Tue 2026-01-14 09:33:18 EST
```

**Switches**

| Token | Meaning |
|---|---|
| `systemctl restart UNIT` | Restart (no reload available) |
| `ls -lh DIR/*/system.journal` | Confirm active file exists |
| `journalctl --disk-usage` | Now reports `/var/log/journal/` size |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `/var/log/journal/` still empty after restart | `Storage=volatile` is set somewhere — grep drop-ins again |
| Daemon refused to restart | `journalctl -u systemd-journald` — usually a config typo |
| `system.journal` file too small | Wait a few seconds — journald hasn't flushed yet |

---

### Task 5 — Reboot and prove `journalctl -b -1` works

**Purpose:** Reboot, log back in, and prove that the previous boot is now queryable — the canonical test of persistence.

```bash
cd /root/journal-persist-lab

uname -r > 05-kernel-pre.txt
date -Iseconds > 05-time-pre.txt
journalctl --list-boots | tee 05-list-boots-pre.txt

echo "About to reboot. After login, cd /root/journal-persist-lab and run:"
echo "  journalctl --list-boots | tee 05-list-boots-post.txt"
echo "  journalctl -b -1 -p err --no-pager | head -n 5 | tee 05-prev-boot-errors.txt"
echo "  journalctl --disk-usage | tee 05-disk-usage-post.txt"

sudo systemctl reboot
```

After login:

```bash
cd /root/journal-persist-lab

journalctl --list-boots | tee 05-list-boots-post.txt
journalctl -b -1 -p err --no-pager | head -n 5 | tee 05-prev-boot-errors.txt
journalctl --disk-usage | tee 05-disk-usage-post.txt
diff 05-list-boots-pre.txt 05-list-boots-post.txt || true
```

**Human-Readable Breakdown:** Snapshot kernel version and time, capture the current boot list (one entry), reboot, then on next login re-list boots — there should now be at least two entries.

**Reading it left to right:** `--list-boots` is the indicator: one row pre-reboot, two rows post-reboot. `-b -1` queries the previous boot (which is the one we recorded before the reboot). If that query returns lines, persistence is proven.

**The story:** This is the moment the lab "becomes real." Without persistence, `-b -1` returns "No such boot." With it, you can now triage anything that happened before this reboot. This is also the moment most exam questions land — "show me errors from the previous boot."

**Expected output (post-reboot):**

```text
-1 c0d911f2b56a4f5cb0e2a1f9b7c63d22 Tue 2026-01-14 09:00:11 EST—Tue 2026-01-14 09:42:11 EST
 0 d12e34f4c89b4c7da3f6c2e0a8d743f3 Tue 2026-01-14 09:42:38 EST—Tue 2026-01-14 09:43:55 EST
Archived and active journals take up 24.0M in the file system.
Jan 14 09:42:01 host1 kernel: ...
```

**Switches**

| Token | Meaning |
|---|---|
| `systemctl reboot` | Reboot through systemd |
| `journalctl -b -1` | Previous boot |
| `--list-boots` | All known boots |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Only one boot listed after reboot | `Storage=` overridden — re-check drop-ins |
| `-b -1` says "No such boot" | Same — re-check Task 2 grep |
| Can't log back in | Use console; `Storage=` changes never block login |

---

### Task 6 — Cap size and retention with a drop-in under `/etc/systemd/journald.conf.d/`

**Purpose:** Avoid the journal eating the whole partition. Use a drop-in so vendor `journald.conf` stays intact.

```bash
cd /root/journal-persist-lab

sudo mkdir -p /etc/systemd/journald.conf.d
cat <<'EOF' | sudo tee /etc/systemd/journald.conf.d/00-persist-retention.conf >/dev/null
[Journal]
Storage=persistent
Compress=yes
SystemMaxUse=1G
SystemKeepFree=500M
SystemMaxFileSize=200M
MaxRetentionSec=2week
MaxFileSec=1week
ForwardToSyslog=no
EOF

cat /etc/systemd/journald.conf.d/00-persist-retention.conf | tee 06-dropin.txt
systemd-analyze cat-config systemd/journald.conf | tee 06-effective-conf.txt
sudo systemctl restart systemd-journald.service
journalctl --disk-usage | tee 06-disk-usage-tuned.txt
```

**Human-Readable Breakdown:** Create `/etc/systemd/journald.conf.d/`, write a drop-in that sets persistent storage, compression, a 1 GiB cap, 500 MiB keep-free, 200 MiB per file, 2-week retention, and 1-week file rotation. Re-render the merged config with `systemd-analyze cat-config`, restart journald, and recheck disk usage.

**Reading it left to right:** Drop-in files in `/etc/systemd/journald.conf.d/*.conf` are merged with the canonical `/etc/systemd/journald.conf` at runtime. Numbering files (`00-...conf`) controls merge order — lower numbers load first. `SystemMaxUse=1G` is the **upper bound**; the journal grows up to it then deletes oldest. `MaxRetentionSec=2week` drops entries older than two weeks regardless of size. Both can coexist; whichever triggers first wins.

**The story:** This is the **production-grade** journal config. 1 GiB / 14 days is a sensible default for most RHEL servers. CI runners want 200 MiB / 24h. Database hosts want 10 GiB / 30 days. The shape of the directives is identical — just the numbers change.

**Expected output:**

```text
[Journal]
Storage=persistent
Compress=yes
SystemMaxUse=1G
SystemKeepFree=500M
SystemMaxFileSize=200M
MaxRetentionSec=2week
MaxFileSec=1week
ForwardToSyslog=no
...
Archived and active journals take up 24.0M in the file system.
```

**Switches**

| Directive | Effect |
|---|---|
| `Storage=persistent` | Always use `/var/log/journal` |
| `Compress=yes` | LZ4 entries (~5-10x ratio) |
| `SystemMaxUse=` | Total cap (suffix `K`, `M`, `G`) |
| `SystemKeepFree=` | Free-space reserve |
| `SystemMaxFileSize=` | Per-file cap |
| `MaxRetentionSec=` | Age-based drop (`1month`, `2week`, `7d`) |
| `MaxFileSec=` | Rotation interval |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `systemctl restart` failed | `systemd-analyze verify` — usually a typo in suffix |
| Drop-in ignored | Wrong path — must be `/etc/systemd/journald.conf.d/*.conf` |
| Sizes not honored | journald deletes lazily — `--vacuum-size=` forces it |

---

### Task 7 — Reload by restart and re-check effective values

**Purpose:** Confirm the drop-in is in effect; show how to read the merged values from the kernel-side view (file metadata after rotation).

```bash
cd /root/journal-persist-lab

sudo systemctl restart systemd-journald.service
sleep 1
ls -lh /var/log/journal/*/ | tee 07-files-after-restart.txt
journalctl --disk-usage | tee 07-disk-usage.txt

stat -c '%n %s %y' /var/log/journal/*/system.journal | tee 07-active-journal-stat.txt
```

**Human-Readable Breakdown:** Restart again so journald rotates the active file with the new sizing, then list every file under the per-machine directory. Use `stat` to print the active file's exact size and last-modified time.

**Reading it left to right:** `ls -lh /var/log/journal/*/` lists each `<MACHINE-ID>` directory's files in human-readable sizes. `stat -c '%n %s %y'` prints filename + bytes + mtime in one line — easier than parsing `ls`.

**The story:** Every config change becomes "real" after a restart. journald does **not** support `reload`. The restart is fast (sub-second) and never loses queued messages — they are buffered through the restart.

**Expected output:**

```text
-rw-r-----+ 1 root systemd-journal  16M Jan 14 09:45 system.journal
-rw-r-----+ 1 root systemd-journal 8.0M Jan 14 09:44 user-0.journal
/var/log/journal/9e1ad.../system.journal 16777216 2026-01-14 09:45:33.000000000 -0500
```

**Switches**

| Token | Meaning |
|---|---|
| `ls -lh DIR/` | Long, human-readable |
| `stat -c FMT FILE` | Custom-format stat |
| `%n` | Filename |
| `%s` | Size in bytes |
| `%y` | Modification time |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| File sizes do not change | Journal still flushing — wait a minute |
| Many tiny files | `SystemMaxFiles=` cap or `MaxFileSec=` too short |
| Permission errors with `ls` | `getfacl` to confirm ACL — root should always see |

---

### Task 8 — Verify integrity and (optional) seal the journal

**Purpose:** Use `journalctl --verify` to detect corruption, and demonstrate sealing for forward-secure tamper detection.

```bash
cd /root/journal-persist-lab

sudo journalctl --verify | tee 08-verify.txt

sudo journalctl --setup-keys --interval=30day 2>&1 | tee 08-setup-keys.txt || true
ls /var/log/journal/*/fss 2>/dev/null | tee 08-fss-file.txt || true
sudo journalctl --verify --quiet && echo "verify-quiet: OK" | tee -a 08-verify.txt
```

**Human-Readable Breakdown:** Run the integrity check on every journal file, then attempt to set up Forward-Secure Sealing keys with a 30-day rotation interval. The keys file lives at `/var/log/journal/<MACHINE-ID>/fss`. `--verify --quiet` returns exit 0 on success.

**Reading it left to right:** `--verify` walks every file, checking hashes and (if sealed) cryptographic seals. `--setup-keys` generates the FSS key pair — the verification key is printed once for you to record offline. `--interval=30day` controls how often a new seal is computed.

**The story:** Sealing makes the journal **tamper-evident** — an attacker with root cannot edit history without leaving cryptographic evidence. The cost is one-time key setup and a small ongoing CPU hit. Most server fleets do not enable sealing because they ship logs to a centralized store that already has integrity guarantees; some compliance-driven workloads (PCI, HIPAA) require it.

**Expected output:**

```text
PASS: /var/log/journal/9e1ad.../system.journal
PASS: /var/log/journal/9e1ad.../user-0.journal
Forward-secure sealing key pair set up:
  ...secret displayed once...
The key pair has been written to:
  /var/log/journal/9e1ad.../fss
verify-quiet: OK
```

**Switches**

| Token | Meaning |
|---|---|
| `--verify` | Walk and verify every file |
| `--setup-keys` | Generate FSS key pair |
| `--interval=` | Seal regeneration interval |
| `--quiet` | Exit code only |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `--verify` reports `FAIL` | Likely after unclean shutdown — `journalctl --rotate` then re-verify |
| `--setup-keys` already done | Existing key is in `fss` — recording the secret is one-shot |
| No `fss` file | Lab VM probably skipped key setup — that's fine; sealing is optional |

---

### Task 9 — Manual rotation and vacuum

**Purpose:** Force a rotation now, then shrink the archive set by size and by age. These are the two recovery commands when disk fills unexpectedly.

```bash
cd /root/journal-persist-lab

journalctl --disk-usage | tee 09-before-vacuum.txt
sudo journalctl --rotate
ls -lh /var/log/journal/*/ | tee 09-after-rotate.txt
sudo journalctl --vacuum-size=200M | tee 09-vacuum-size.txt
sudo journalctl --vacuum-time=7d | tee 09-vacuum-time.txt
journalctl --disk-usage | tee 09-after-vacuum.txt
```

**Human-Readable Breakdown:** Record disk usage, force the active journal to rotate (the current file becomes archived and a new active file is created), shrink the archive set to 200 MiB total, drop archives older than 7 days, then record disk usage again.

**Reading it left to right:** `--rotate` is non-destructive — it just rolls the active file. `--vacuum-size=` deletes oldest archived files until the total fits the size. `--vacuum-time=` drops archives whose newest entry is older than the duration. Suffixes: `K`, `M`, `G`, and `s`, `m`, `h`, `d`, `week`, `month`, `year`.

**The story:** These are your emergency tools. "Disk full!" → `journalctl --vacuum-size=500M` reclaims space in seconds without restarting any service. Used regularly via cron or a systemd timer, they keep retention bounded even if `SystemMaxUse=` somehow falls behind.

**Expected output:**

```text
Archived and active journals take up 1.0G in the file system.
-rw-r-----+ 1 root systemd-journal 200M Jan 14 09:50 system@xxxxx.journal
-rw-r-----+ 1 root systemd-journal  8.0M Jan 14 09:51 system.journal
Deleted archived journal /var/log/journal/9e1ad.../system@xxxxx.journal (...).
Vacuuming done, freed 800.0M of archived journals from /var/log/journal/9e1ad...
Archived and active journals take up 208.0M in the file system.
```

**Switches**

| Token | Meaning |
|---|---|
| `--rotate` | Roll active to archived |
| `--vacuum-size=N` | Keep at most N bytes |
| `--vacuum-time=DUR` | Drop older than DUR |
| `--vacuum-files=N` | Keep at most N files |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Vacuum reports `freed 0B` | Already under cap — nothing to delete |
| Active file not rotated | `--rotate` rotates only archived; active is rotated by `MaxFileSec=` |
| Vacuum deletes too aggressively | Increase `--vacuum-size=` argument |

---

### Task 10 — Capstone: persistence + retention report and clean revert path

**Task statement:** *"Confirm `/var/log/journal/` is in place, `journalctl -b -1` works, the drop-in caps storage at 1 GiB / 14 days, and the integrity verify returns PASS. Write a one-paragraph report. Then document and pre-stage a safe revert path."*

**Purpose:** Combine all prior tasks into a deliverable, then show how to undo every change in case the user wants to roll back.

```bash
cd /root/journal-persist-lab

BOOTS=$(journalctl --list-boots | wc -l)
USAGE=$(journalctl --disk-usage | head -n 1)
VERIFY=$(sudo journalctl --verify --quiet && echo "PASS" || echo "FAIL")
DROPIN=$(grep -E '^(Storage|SystemMaxUse|MaxRetentionSec)=' /etc/systemd/journald.conf.d/00-persist-retention.conf | paste -sd '; ')

cat > 10-report.txt <<EOF
Persistent journal report — $(hostname) — $(date -Iseconds)

Directory /var/log/journal/  ........... present ($(ls -ld /var/log/journal | awk '{print $1, $3, $4}'))
Drop-in /etc/systemd/journald.conf.d/00-persist-retention.conf
  Effective directives: ${DROPIN}
Visible boots:  ${BOOTS}
Disk usage:     ${USAGE}
Integrity:      ${VERIFY}

Revert plan (not executed):
  1) sudo rm /etc/systemd/journald.conf.d/00-persist-retention.conf
  2) sudo rm /etc/tmpfiles.d/journal.conf
  3) sudo systemctl restart systemd-journald
  4) (optional) sudo rm -rf /var/log/journal      # discards archived journals
EOF

cat 10-report.txt
```

**Human-Readable Breakdown:** Pull four numbers from the live system — visible boots, disk usage, verify result, and the salient directives from the drop-in — and write a report. The bottom of the report documents but does **not run** the revert plan, so a future engineer can roll back deliberately.

**Layer stack you built:**

```text
10-report.txt                              ← deliverable
  ├── /var/log/journal/                    ← persistence directory (Task 3)
  ├── /etc/tmpfiles.d/journal.conf         ← reapply on boot (Task 3)
  ├── /etc/systemd/journald.conf.d/...     ← retention drop-in (Task 6)
  ├── /var/log/journal/*/fss               ← optional seal keys (Task 8)
  └── 01..09 artifact files                ← evidence
```

**The story:** A persistent journal is **one directory + one drop-in + one restart**. The proof is `journalctl -b -1` returning lines. The revert is `rm` of two files and a restart. The professional habit is to leave the revert plan documented in the report.

**Expected output:**

```text
Persistent journal report — host1 — 2026-01-14T09:55:12-05:00

Directory /var/log/journal/  ........... present (drwxr-sr-x root systemd-journal)
Drop-in /etc/systemd/journald.conf.d/00-persist-retention.conf
  Effective directives: Storage=persistent; SystemMaxUse=1G; MaxRetentionSec=2week
Visible boots:  2
Disk usage:     Archived and active journals take up 208.0M in the file system.
Integrity:      PASS

Revert plan (not executed):
  1) sudo rm /etc/systemd/journald.conf.d/00-persist-retention.conf
  2) sudo rm /etc/tmpfiles.d/journal.conf
  3) sudo systemctl restart systemd-journald
  4) (optional) sudo rm -rf /var/log/journal      # discards archived journals
```

**Cleanup (lab only — does *not* discard existing journals)**

```bash
cd /root
rm -rf /root/journal-persist-lab
ls -ld /root/journal-persist-lab 2>&1 | head -n 1
exit
```

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Report shows `Visible boots: 1` | You haven't rebooted yet — re-do Task 5 |
| Report shows `Integrity: FAIL` | `journalctl --rotate` then re-verify |
| Empty `DROPIN` | Drop-in file was deleted — recreate from Task 6 |

---

## 🔍 Persistence Decision Guide

```
Do I need persistent journals?
  │
  ├── Production server (any kind)        → YES — persistent + retention cap
  ├── CI runner (ephemeral, short-lived)  → MAYBE — only if you must triage failures
  ├── Immutable AMI shipping to S3        → NO — volatile, ship at exit
  └── Embedded / small disk               → CAREFUL — set SystemMaxUse low

Persistence is OFF when…
  ├── /var/log/journal does NOT exist     → mkdir to enable
  └── Storage=volatile is set somewhere    → search drop-ins

Persistence is ON when…
  ├── /var/log/journal exists              → and Storage=auto OR persistent
  └── --list-boots shows ≥ 2 boots         → after a reboot
```

---

## Lab Checklist (10 Tasks)

- [ ] 01 Baseline: capture pre-change state
- [ ] 02 Read effective `Storage=` and related directives
- [ ] 03 Create `/var/log/journal/` with `install -d -m 2755 -g systemd-journal`
- [ ] 04 Restart `systemd-journald` and confirm files appear under `/var/log/journal/`
- [ ] 05 Reboot and verify `journalctl -b -1` works
- [ ] 06 Drop-in: `SystemMaxUse=1G`, `MaxRetentionSec=2week`
- [ ] 07 Restart and confirm effective rotation
- [ ] 08 `journalctl --verify` (and optional `--setup-keys`)
- [ ] 09 Manual `--rotate`, `--vacuum-size=`, `--vacuum-time=`
- [ ] 10 Report and documented revert plan

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `mkdir /var/log/journal` (no mode/group) | Wrong perms; new files own wrong group | `install -d -g systemd-journal -m 2755` |
| Edited `journald.conf` directly | Vendor patch wipes change | Use a drop-in in `journald.conf.d/` |
| `Storage=volatile` set in vendor drop-in | Persistence appears not to work | Override in `/etc/systemd/journald.conf.d/` |
| No reboot before claiming success | `-b -1` returns "No such boot" | Reboot, then `journalctl --list-boots` |
| `journalctl reload` | "Unit not found" | journald only supports `restart` |
| `SystemMaxUse=` with no suffix | Treated as bytes | Always use `M`, `G` |
| `MaxRetentionSec=` of `30` | Means 30 *seconds* | Use `30d`, `2week`, `1month` |
| Setting up seals but losing the verification key | Tamper detection works once, then is unverifiable | Record key offline immediately |
| `rm -rf /var/log/journal/*` to free space | Loses history | `journalctl --vacuum-size=` instead |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- One sentence answer: "I create `/var/log/journal`, restart `systemd-journald`, and verify with `journalctl --list-boots`." Memorize the `install -d -m 2755 -g systemd-journal` form.

**RHCE candidate**
- Ansible pattern: `community.general.ini_file` writing to `/etc/systemd/journald.conf.d/00-retention.conf` with `notify: restart journald`. Idempotent, no full file template.

**SRE / Platform interview**
- Be prepared to explain how `SystemMaxUse=`, `MaxRetentionSec=`, and `SystemMaxFileSize=` interact, and why the journal can grow above `SystemMaxUse=` briefly (lazy deletion).

**DevOps**
- Bake the directory and drop-in into the base image. Persistent logs are the difference between "build #4231 failed" and "build #4231 failed because cpuset OOM at 03:42:11."

**AI / MLOps**
- On training fleets, set `SystemMaxUse=8G` + `MaxRetentionSec=30d`. NCCL and CUDA failures often only show up two reboots later, when nobody remembers what changed.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 101 — Query Logs with `journalctl` | Persistence makes `-b -1` and `--list-boots` useful |
| Lab 103 — Understand Log Routing | rsyslog rules complement (but do not replace) the journal |
| Lab 104 — Monitor Authentication Logs | `/var/log/secure` is rsyslog's twin of `journalctl -u sshd` |
| Lab 105 — Filter Journals by Priority | Sealed + persistent + priority filter is the incident-response loop |
| Lab 100 — `systemd-analyze` Boot Performance | Persistent journal lets you compare boots over time |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
