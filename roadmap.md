# 🗺️ Roadmap — linux-ops-mastery

> The full curriculum. Every lab that exists, is in progress, or is planned — organized by certification track and exam objective, **with the full path to every lab** so you can jump straight from this page to whatever you want to work on next.
>
> Looking for the day-one starting point? See the **[Suggested Learning Path](README.md#-suggested-learning-path)** in the main README. Looking for what's already built? Jump to **[Currently Built](#-currently-built)** below.

---

## 📊 Counts at a Glance

Every row below counts **every lab visible across this repo** — the in-repo labs in [`labs/`](labs/), the external companion repos linked from the main [README](README.md), **and** every future lab listed in [`future_labs.txt`](future_labs.txt). Order matches the curriculum flow: **RHCSA → RHCE → CKA → CKAD → Ansible**.

| Track | ✅ Done | 🚧 In Progress | 📅 Planned | Total |
|---|---:|---:|---:|---:|
| RHCSA EX200 | 120 | 115 | 121 | 356 |
| RHCE EX294 (sample-exam scenarios) | 0 | 0 | 20 | 20 |
| CKA (Kubernetes Administrator) | 0 | 16 | 20 | 36 |
| CKAD (Kubernetes App Developer) | 0 | 0 | 22 | 22 |
| Ansible (Mastering Ansible 4th Ed. + RHCE companion repos) | 13 | 2 | 73 | 88 |
| **Total** | **133** | **133** | **256** | **522** |

> **How counts are derived.** ✅ Done = full content exists (either an in-repo `labs/<slug>/` README with concept + tasks + capstone, **or** an external companion repo linked from the main [README](README.md)). 🚧 In Progress = a placeholder is checked in (either an in-repo `labs/<slug>/` skeleton with task definition, **or** a `*(coming soon)*` row in the main [README](README.md) with the exam objective scoped but no walkthrough written). 📅 Planned = lab is only listed in [`future_labs.txt`](future_labs.txt) — exam-accurate task definition, no page started.

> **Note on the 257 in `future_labs.txt`.** The summary block at the bottom of [`future_labs.txt`](future_labs.txt) reports 257 future labs across all four certifications. That same 257 is distributed in the 📅 Planned column above as: **121 RHCSA** (11 from samplerhcsa2 + 13 from samplerhcsa3/4 + 97 from PerfectScorerPracticeExams) + **20 RHCE** + **20 CKA** + **23 CKAD** + **73 Mastering Ansible** = 257. The 22 CKAD figure used in the table above drops one duplicate noted in `future_labs.txt`.

---

## 🔑 Status Legend

| Symbol | Meaning |
|---|---|
| ✅ **Done** | Full lab README — in this repo OR in an external companion repo — with concept, tasks, troubleshooting, and capstone |
| 🚧 **In Progress** | Placeholder lab page (in-repo skeleton OR `*(coming soon)*` row in the main [README](README.md)) with title + task details scoped; full walkthrough being written |
| 📅 **Planned** | Listed in [`future_labs.txt`](future_labs.txt); task definition is exam-accurate, but no page has been started yet |

---

## 🏷️ ID Prefix System

Each planned lab gets a stable per-category identifier so cross-referencing survives renumbering. The `-F` suffix in every ID below stands for "Future"; once a lab is built and promoted, its `-F` is dropped.

| Prefix | Category |
|---|---|
| `LVM-F##` | LVM (Logical Volume Management) |
| `STOR-F##` | Storage Management (partitions, fstab, mounts) |
| `SEL-F##` | SELinux |
| `NET-F##` | Networking (interfaces, hostname, /etc/hosts) |
| `PKG-F##` | Package Management & Repositories |
| `FW-F##` | Firewall (firewalld) |
| `SSH-F##` | Remote Administration & SSH |
| `WEB-F##` | Web Services (Apache) |
| `USER-F##` | User & Group Management |
| `PERM-F##` | Permissions, Special Bits & ACLs |
| `SUDO-F##` | Sudo & Privilege |
| `NFS-F##` | NFS & AutoFS / Filesystem Mounts |
| `CRON-F##` | Scheduled Tasks (cron, at, systemd timers) |
| `FILES-F##` | Essential Tools & File Operations |
| `TEXT-F##` | Text File Management |
| `ARCH-F##` | Archives & Compression |
| `TIME-F##` | System Time & Locale |
| `BOOT-F##` | Boot Process & GRUB |
| `SYSD-F##` | Systemd & Services |
| `PERF-F##` | System Performance & Tuning |
| `CON-F##` | Containers & Flatpak |
| `SCRIPT-F##` | Shell Scripting & Automation |
| `PROC-F##` | Process Management |
| `DOC-F##` | Documentation Tools |
| `ENV-F##` | Environment & Shell Configuration |
| `RHCE-F##` | RHCE / Ansible (sample-exam scenario labs) |
| `CKA-F##` | CKA (Cluster Administrator) |
| `CKAD-DES-F##` | CKAD — Application Design and Build |
| `CKAD-DEP-F##` | CKAD — Application Deployment |
| `CKAD-OBS-F##` | CKAD — Observability and Maintenance |
| `CKAD-ENV-F##` | CKAD — Environment, Config & Security |
| `CKAD-NET-F##` | CKAD — Services and Networking |
| `ANS-CH1-F##` | Ansible — Ch 1: System Architecture & Design |
| `ANS-CH2-F##` | Ansible — Ch 2: Collections / FQCNs / Migration |
| `ANS-CH7-F##` | Ansible — Ch 7: Task Conditions, Loops, Rescue |
| `ANS-CH8-F##` | Ansible — Ch 8: Roles, Includes, ansible-galaxy |
| `ANS-CH13-F##` | Ansible — Ch 13: Network Automation |

---

## ✨ Currently Built

The 13 labs with full or placeholder content in **this** repository today (under [`labs/`](labs/)), plus links straight to the file. External companion repos linked from the main [README](README.md) are listed by track below.

| Status | Lab | Location |
|---|---|---|
| ✅ | Create LV `lvol1` (ext4, 280 MB) and Mount Persistently | [`labs/lvm-create-lvol1-ext4/`](labs/lvm-create-lvol1-ext4/) |
| ✅ | Create LV with XFS Filesystem | [`labs/lvm-create-lv1-xfs/`](labs/lvm-create-lv1-xfs/) |
| ✅ | Scheduling Jobs with systemd Timers | [`labs/scheduling-jobs-systemd-timer/`](labs/scheduling-jobs-systemd-timer/) |
| ✅ | Find Files by Modification Time and Act on Them | [`labs/find-files-by-mtime/`](labs/find-files-by-mtime/) |
| ✅ | Lock User Account and Capture Regex Evidence | [`labs/user-lock-capture-regex/`](labs/user-lock-capture-regex/) |
| 🚧 | Online Extend an LV and Its Filesystem Without Unmounting | [`labs/lvm-online-extend-xfs/`](labs/lvm-online-extend-xfs/) |
| 🚧 | Create a Swap Partition by UUID | [`labs/storage-swap-partition-uuid/`](labs/storage-swap-partition-uuid/) |
| 🚧 | Create an Ext4 Partition Mounted by LABEL | [`labs/storage-ext4-partition-label/`](labs/storage-ext4-partition-label/) |
| 🚧 | Apply Recursive SELinux Contexts to a New Directory | [`labs/selinux-recursive-contexts-direct01/`](labs/selinux-recursive-contexts-direct01/) |
| 🚧 | User-Level Cron Job with `find -exec` | [`labs/cron-user-find-exec-coredir/`](labs/cron-user-find-exec-coredir/) |
| 🚧 | Install Development Tools Package Group with Output Capture | [`labs/dnf-install-dev-tools-capture/`](labs/dnf-install-dev-tools-capture/) |
| 🚧 | Bidirectional Bash Script with Argument Logic | [`labs/bash-bidirectional-arg-script/`](labs/bash-bidirectional-arg-script/) |
| 🚧 | Rootless Container with Bind Mount and systemd Auto-Start | [`labs/podman-rootless-bind-mount-systemd/`](labs/podman-rootless-bind-mount-systemd/) |

---

## 🎯 RHCSA Track (EX200)

The RHCSA curriculum has three buckets:

1. **External companion repos** — the 227+ numbered labs in the main [README](README.md). Each row below links straight to the repo. Where a row reads `*(coming soon — see Lab #NN in README)*`, the lab number is scoped in the main README but no companion repo exists yet.
2. **In-repo labs** under [`labs/`](labs/) — listed inline in the relevant section.
3. **Future planned labs** — the `*-F##`-tagged entries from [`future_labs.txt`](future_labs.txt), grouped by category.

### 🖥 Shells, Terminals & Redirection (README Labs 01–04)

| Status | # | Lab | Full Path |
|---|---|---|---|
| ✅ | 01 | Standard Output Redirection | <https://github.com/kelvintechnical/stdout-redirection> |
| ✅ | 02 | Standard Error Redirection | <https://github.com/kelvintechnical/stderr-redirection> |
| ✅ | 03 | Pipe Text Streams | <https://github.com/kelvintechnical/pipe-text-streams> |
| ✅ | 04 | Capture Both Output and Error | <https://github.com/kelvintechnical/capture-both-output-error> |

---

### 🔧 Essential Tools & File Operations (README Labs 05–18)

| Status | # | Lab | Full Path |
|---|---|---|---|
| ✅ | 05 | Directory Navigation | <https://github.com/kelvintechnical/directory-nav> |
| ✅ | 06 | Listing Files and SELinux Contexts | <https://github.com/kelvintechnical/listing-files-selinux> |
| ✅ | 07 | Creating Empty Files and Timestamps | <https://github.com/kelvintechnical/touch-timestamps> |
| ✅ | 08 | Copying Files and Directories | <https://github.com/kelvintechnical/copying-files-directories> |
| ✅ | 09 | Hard and Soft Links | <https://github.com/kelvintechnical/hard-and-soft-links> |
| ✅ | 10 | Moving and Renaming Files | <https://github.com/kelvintechnical/moving-renaming-files> |
| ✅ | 11 | Safe Deletion of Files and Directories | <https://github.com/kelvintechnical/safe-deletion> |
| ✅ | 12 | Creating Nested Directories | <https://github.com/kelvintechnical/creating-nested-directories> |
| ✅ | 13 | Creating Command Aliases | <https://github.com/kelvintechnical/creating-command-aliases> |
| ✅ | 14 | File Searching with find | <https://github.com/kelvintechnical/searching-with-find> |
| ✅ | 15 | Instant File Searching with locate | <https://github.com/kelvintechnical/searching-with-locate> |
| ✅ | 16 | Search for a String and Save Output | <https://github.com/kelvintechnical/search-string-save-output> |
| ✅ | 17 | Find and Save Config Files | <https://github.com/kelvintechnical/find-save-config-files> |
| ✅ | 18 | Locate Command Documentation | <https://github.com/kelvintechnical/locate-command-docs> |
| ✅ | — | Find Files by Modification Time and Act on Them (in-repo) | [`labs/find-files-by-mtime/`](labs/find-files-by-mtime/) |

**Future Labs (planned — from [`future_labs.txt`](future_labs.txt)):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | FILES-F01 | Find Files by Size Range and Copy Preserving All Attributes | `find /etc -type f -size +5M -size -10M -exec cp --preserve=ownership,mode,timestamps,context {} /find/largefiles/ \;` — prove with `stat -c '%A %U:%G %y'` |
| 📅 | FILES-F02 | Find Files Owned by a User Within a Size Range | `find / -xdev -user linda -type f -size +3M -size -50M 2>/dev/null -exec cp -a {} /root/linda-files/ \;` — suppresses permission-denied noise |
| 📅 | FILES-F03 | Find Configuration Files by Name and Owner | `find /etc -type f -name '*.conf' -user root > /root/config_files` — verify with `wc -l` and spot-check |
| 📅 | FILES-F04 | Find Files Modified More Than 30 Days Ago and Copy with Hierarchy | `find /etc -type f -mtime +30 -exec cp --parents --preserve=all {} /tmp/etc_backup/ \;` — `--parents` preserves the directory layout |
| 📅 | FILES-F05 | Find Directories with the SUID Bit Set + Copy with Attributes | `find / -xdev -type d -perm -4000 2>/dev/null -exec cp -a {} /security_backup/ \;` — security audits and forensic copies |
| 📅 | FILES-F06 | Find Directories by Size Range and Save Long Listing | `find / -xdev -type d -size +50k -size -100k 2>/dev/null \| xargs ls -ld > /root/moderate_dir_list.txt` — note `find` reports *directory entry size*, not recursive contents size |
| 📅 | FILES-F07 | Hard and Symbolic Link Lifecycle Demonstration | `touch report.txt`, `ln report.txt report_hard.txt`, `ln -s report.txt report_symlink.txt`, `rm report.txt` — hard link still has data but symlink is now dangling |

---

### 📄 Text File Management (README Labs 19–27)

| Status | # | Lab | Full Path |
|---|---|---|---|
| ✅ | 19 | Concatenating Files with cat | <https://github.com/kelvintechnical/concactenating-files-with-cat> |
| ✅ | 20 | Scrolling Through Large Files | <https://github.com/kelvintechnical/less-more-scrolling> |
| ✅ | 21 | Monitoring Live Log Files | <https://github.com/kelvintechnical/tail-f-live-logs> |
| ✅ | 22 | Filtering Text with grep and Regex | <https://github.com/kelvintechnical/grep-regex> |
| ✅ | 23 | Comparing File Differences with diff | <https://github.com/kelvintechnical/diff-comparing-files> |
| ✅ | 24 | Stream Editing with sed | <https://github.com/kelvintechnical/sed-stream-editor> |
| ✅ | 25 | Extracting Columns with awk | <https://github.com/kelvintechnical/awk-columns> |
| ✅ | 26 | Command Mode and Insert Mode in vi | <https://github.com/kelvintechnical/vi-editor> |
| ✅ | 27 | Safely Editing System Databases | <https://github.com/kelvintechnical/vipw-vigr-safe-editing> |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | TEXT-F01 | Extract Lines Containing a String Preserving Order | `grep 'bin' /etc/passwd > /root/bin_lines` — prove line order matches source with `grep -n` |
| 📅 | TEXT-F02 | Find Exact Word Matches with `grep -w` | `grep -wE 'bin' /etc/passwd > /root/bin_users.txt` — `-w` prevents matches inside `sbin`, `binary`, `roundbin` |
| 📅 | TEXT-F03 | Search Apache Configuration for Listen Directives | `grep '^Listen' /etc/httpd/conf/httpd.conf > /root/httpd_listen.txt` — `^` excludes commented-out lines |

---

### 📖 Documentation Tools (README Labs 28–30)

| Status | # | Lab | Full Path |
|---|---|---|---|
| ✅ | 28 | Exploring Manual Pages | <https://github.com/kelvintechnical/man-pages-exploration> |
| ✅ | 29 | Searching Manuals by Keyword | <https://github.com/kelvintechnical/whatis-apropos-keyword-search> |
| ✅ | 30 | Navigating info Pages | <https://github.com/kelvintechnical/info-pages-navigation> |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | DOC-F01 | Locate Command Documentation Under `/usr/share/doc` | `find /usr/share/doc -iname '*passwd*'`, display path of one matching file, `less`/`cat` to confirm, prove package owns it with `rpm -qf` |

---

### 🌐 Networking (README Labs 31–39)

| Status | # | Lab | Full Path |
|---|---|---|---|
| ✅ | 31 | Configure a Static IP Address | <https://github.com/kelvintechnical/static-ip-address> |
| ✅ | 32 | Check Network Connectivity | <https://github.com/kelvintechnical/network-connectivity-check> |
| ✅ | 33 | Display IP and Routing Info | <https://github.com/kelvintechnical/ip-and-routing-info> |
| ✅ | 34 | Inspecting Listening Sockets | <https://github.com/kelvintechnical/listening-sockets> |
| ✅ | 35 | Text-Based Network Config nmtui | <https://github.com/kelvintechnical/nmtui-network-config> |
| ✅ | 36 | Command-Line Network Config nmcli | <https://github.com/kelvintechnical/nmcli-network-config> |
| ✅ | 37 | Configuring Local Host Resolution | <https://github.com/kelvintechnical/local-host-resolution> |
| ✅ | 38 | Configuring DNS Servers | <https://github.com/kelvintechnical/dns-servers-config> |
| ✅ | 39 | Configure SSH and Key-Based Auth | <https://github.com/kelvintechnical/ssh-key-based-auth> |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | NET-F01 | Manual Hostname Configuration by Editing `/etc/hostname` | Set the hostname *without* `hostnamectl`: write the FQDN directly into `/etc/hostname`, refresh the shell prompt, verify after reboot |
| 📅 | NET-F02 | Manual Network Configuration by Editing Connection Files | Hand-edit the keyfile under `/etc/NetworkManager/system-connections/` or `/etc/sysconfig/network-scripts/ifcfg-*`, `nmcli connection reload`, prove persistence |
| 📅 | NET-F03 | Configure Static IPv4 with Specific Host Address | `nmcli con mod ens-XX ipv4.addresses 192.168.50.10/24`, `ipv4.gateway 192.168.50.1`, `ipv4.dns "8.8.8.8 8.8.4.4"`, `ipv4.method manual`, `connection.autoconnect yes` |
| 📅 | NET-F04 | Configure Static IPv6 Address with DNS Search Domain | `ipv6.addresses fd02::42/64`, `ipv6.gateway fd02::1`, `ipv6.dns fd02::222`, `ipv6.dns-search example.local`, hostname `node1.example.local` |
| 📅 | NET-F05 | Dual-Stack IPv4 + IPv6 with Local Host Resolution | Both `192.168.56.25/24` and `fd12:3456:789a:1::25/64` on one interface, hostname `node1.lab3.example.net`, `/etc/hosts` entry so short + FQDN both resolve |

---

### 🔒 Permissions, Special Bits & ACLs (README Labs 40–54)

| Status | # | Lab | Full Path |
|---|---|---|---|
| ✅ | 40 | Standard File Permissions | <https://github.com/kelvintechnical/standard-file-permissions> |
| ✅ | 41 | Changing Ownership | <https://github.com/kelvintechnical/changing-file-ownership> |
| ✅ | 42 | SUID Executables | <https://github.com/kelvintechnical/suid-executables> |
| ✅ | 43 | Configure SGID and Sticky Bit | <https://github.com/kelvintechnical/sgid-sticky-bit> |
| ✅ | 44 | Immutable File Attribute | <https://github.com/kelvintechnical/immutable-file-attribute> |
| ✅ | 45 | Append-Only File Attribute | <https://github.com/kelvintechnical/append-only-file-attribute> |
| ✅ | 46 | Identifying File Attributes | <https://github.com/kelvintechnical/identifying-file-attributes> |
| ✅ | 47 | Check ACL Support | <https://github.com/kelvintechnical/acl-support-check> |
| ✅ | 48 | Viewing ACLs | <https://github.com/kelvintechnical/viewing-acls> |
| ✅ | 49 | Modifying ACLs | <https://github.com/kelvintechnical/modifying-acls> |
| ✅ | 50 | Denying Access via ACLs | <https://github.com/kelvintechnical/acl-deny-access> |
| ✅ | 51 | Default Directory ACLs | <https://github.com/kelvintechnical/default-directory-acls> |
| ✅ | 52 | ACL Masks | <https://github.com/kelvintechnical/acl-masks> |
| ✅ | 53 | Removing ACLs | <https://github.com/kelvintechnical/removing-acls> |
| ✅ | 54 | NFSv4 ACLs | <https://github.com/kelvintechnical/nfsv4-acls> |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | PERM-F01 | Collaborative SGID Directory with Multi-User Write Test | `mkdir /sdata`, `chown root:group30`, `chmod 2770`, add `user60` + `user80` to `group30`, prove a file created by `user60` can be edited *and* not deleted by `user80` |
| 📅 | PERM-F02 | File Copy with Combined Ownership + Permissions + ACL + Future-User Safety | `cp /etc/fstab /var/tmp`, `chown root:admins`, `chmod 644`, `setfacl -m u:harry:rw,u:bruce:r,u:natasha:---`, prove "other" still has read so future users automatically get access |
| 📅 | PERM-F03 | ACL with Mixed Read/Write/Read-Only Per User | `cp /etc/hosts /srv/project/hosts_copy`, `setfacl u:emma:rw,u:liam:rw,u:sophie:r,m::rw`, default ACL on parent dir for inheritance, verify with `getfacl` and `sudo -u sophie tee` test |
| 📅 | PERM-F04 | Per-User Default umask via `~/.bashrc` | `echo 'umask 0577' >> /home/bruce/.bashrc` — files become `-r--------`, directories `dr-x------` for owner only, prove with `touch ~/test && stat -c '%a' ~/test` showing 400 |
| 📅 | PERM-F05 | Collaborative Group Directory with SGID + Sticky Bit | `mkdir /data/engineers`, `chown root:engineers`, `chmod 3770` — SGID for group inheritance, sticky for owner-only delete |
| 📅 | PERM-F06 | Restricted Directory Where Owner Has chmod But No rwx | `mkdir /data/engineers`, `chown tom:engineers`, `chmod g+rwx,o-rwx,u-rwx` — prove tom can still `chmod` because owner even though he cannot read or write |

---

### 🔥 Firewall (firewalld) (README Labs 55–67)

| Status | # | Lab | Full Path |
|---|---|---|---|
| ✅ | 55 | Inspecting iptables | <https://github.com/kelvintechnical/inspecting-iptables> |
| ✅ | 56 | Exploring firewalld Zones | <https://github.com/kelvintechnical/firewalld-zones> |
| ✅ | 57 | Changing Default Firewall Zone | <https://github.com/kelvintechnical/default-firewall-zone> |
| ✅ | 58 | Adding Services to Zones | <https://github.com/kelvintechnical/firewalld-add-services> |
| ✅ | 59 | Opening Custom Ports | <https://github.com/kelvintechnical/firewalld-custom-ports> |
| ✅ | 60 | Inspect Active Firewall Zones | <https://github.com/kelvintechnical/active-firewall-zones> |
| ✅ | 61 | Reassign Interfaces to Zones | <https://github.com/kelvintechnical/reassign-interfaces-zones> |
| ✅ | 62 | Allow Services Through Firewall | <https://github.com/kelvintechnical/firewall-allow-services> |
| ✅ | 63 | Configure IP Masquerading NAT | <https://github.com/kelvintechnical/ip-masquerading-nat> |
| ✅ | 64 | Configure IP Forwarding | <https://github.com/kelvintechnical/ip-forwarding> |
| ✅ | 65 | Configure Rich Rules | <https://github.com/kelvintechnical/firewalld-rich-rules> |
| ✅ | 66 | Setup Port Forwarding DNAT | <https://github.com/kelvintechnical/port-forwarding-dnat> |
| ✅ | 67 | Configure ICMP Filters | <https://github.com/kelvintechnical/icmp-filters> |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | FW-F01 | Open Multiple Services at Once for Web Hosting | `firewall-cmd --permanent --add-service={ssh,http,https}`, reload, verify with `--list-services`, prove external connectivity from a second host |
| 📅 | FW-F02 | Open a Non-Standard SSH Port + Move SSH There | `firewalld --add-port=88/tcp --permanent`, then `sshd_config Port 88`, `semanage port -a -t ssh_port_t -p tcp 88`, restart sshd, prove `ssh -p 88` works while port 22 is closed |

---

### 🔐 TCP Wrappers & PAM (README Labs 68–77)

| Status | # | Lab | Full Path |
|---|---|---|---|
| ✅ | 68 | Verify TCP Wrappers Support | <https://github.com/kelvintechnical/tcp-wrappers-support> |
| ✅ | 69 | Restrict Access via hosts.deny | <https://github.com/kelvintechnical/hosts-deny-restrictions> |
| ✅ | 70 | Allow Specific Access via hosts.allow | <https://github.com/kelvintechnical/hosts-allow-access> |
| ✅ | 71 | Configure TCP Wrappers for FTP | <https://github.com/kelvintechnical/tcp-wrappers-ftp> |
| ✅ | 72 | Explore PAM Config Files | <https://github.com/kelvintechnical/pam-config-files> |
| ✅ | 73 | Read PAM Module Documentation | <https://github.com/kelvintechnical/pam-module-docs> |
| ✅ | 74 | Implement Password Complexity | <https://github.com/kelvintechnical/password-complexity-pam> |
| ✅ | 75 | Configure PAM to Limit root Access | <https://github.com/kelvintechnical/pam-limit-root-access> |
| ✅ | 76 | Use PAM to Limit User Access | <https://github.com/kelvintechnical/pam-limit-user-access> |
| ✅ | 77 | Restrict Service Access by User List | <https://github.com/kelvintechnical/pam-restrict-by-user-list> |

---

### 🛡 SELinux (README Labs 78–84)

| Status | # | Lab | Full Path |
|---|---|---|---|
| ✅ | 78 | Managing SELinux Modes | <https://github.com/kelvintechnical/selinux-modes-management> |
| ✅ | 79 | Viewing SELinux Contexts | <https://github.com/kelvintechnical/selinux-viewing-contexts> |
| ✅ | 80 | Temporary Context Changes | <https://github.com/kelvintechnical/selinux-temporary-contexts> |
| ✅ | 81 | Persistent Context Restoration | <https://github.com/kelvintechnical/selinux-persistent-contexts> |
| ✅ | 82 | Toggling SELinux Booleans | <https://github.com/kelvintechnical/selinux-booleans> |
| ✅ | 83 | SELinux User Mapping | <https://github.com/kelvintechnical/selinux-user-mapping> |
| ✅ | 84 | Troubleshooting SELinux | <https://github.com/kelvintechnical/selinux-troubleshooting> |
| 🚧 | — | Apply Recursive SELinux Contexts to a New Directory (in-repo) | [`labs/selinux-recursive-contexts-direct01/`](labs/selinux-recursive-contexts-direct01/) |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | SEL-F02 | Add a Custom HTTP Port to the SELinux Policy Database | `semanage port -a -t http_port_t -p tcp 8300`, verify with `semanage port -l \| grep http_port_t`, prove the change survives a relabel |
| 📅 | SEL-F03 | Set SELinux to Permissive Mode Persistently | Edit `/etc/selinux/config: SELINUX=permissive`, `setenforce 0`, prove with `getenforce` and reboot to verify persistence |
| 📅 | SEL-F04 | Apply Recursive SELinux Context from a Reference Directory | `mkdir /dir && mkdir /dir/subdir{1,2}`, `semanage fcontext -a -e /etc /dir`, `restorecon -RFv /dir`, prove with `ls -Zd /dir/subdir1` matching `/etc/skel` exactly |
| 📅 | SEL-F05 | Configure Apache to Serve from a Non-Default Directory | `mkdir /web`, drop `practice.html`, `semanage fcontext -a -t httpd_sys_content_t '/web(/.*)?'`, `restorecon -Rv /web`, prove `ls -Z` and `curl http://localhost/web/practice.html` |
| 📅 | SEL-F06 | Toggle the `httpd_can_network_connect` Boolean Persistently | `setsebool -P httpd_can_network_connect on`, prove `getsebool` shows on, reboot and re-verify |

---

### 🥾 Boot Process & GRUB (README Labs 85–89)

| Status | # | Lab | Full Path |
|---|---|---|---|
| ✅ | 85 | Modify GRUB Timeout | <https://github.com/kelvintechnical/grub-timeout> |
| ✅ | 86 | Enable Verbose Kernel Messages | <https://github.com/kelvintechnical/verbose-kernel-messages> |
| ✅ | 87 | Generate New GRUB Config | <https://github.com/kelvintechnical/grub-mkconfig> |
| ✅ | 88 | Reset Root Password via Boot | <https://github.com/kelvintechnical/reset-root-password-boot> |
| ✅ | 89 | Chroot into Rescue Filesystem | <https://github.com/kelvintechnical/chroot-rescue-filesystem> |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | BOOT-F01 | Enable Verbose Boot by Removing `quiet` and `rhgb` | Edit `/etc/default/grub`, remove `quiet rhgb` from `GRUB_CMDLINE_LINUX`, `grub2-mkconfig -o /boot/grub2/grub.cfg`, reboot and watch the verbose systemd boot log |

---

### ⚙️ Systemd & Services (README Labs 90–99)

| Status | # | Lab | Full Path |
|---|---|---|---|
| ✅ | 90 | Check Default Boot Target | <https://github.com/kelvintechnical/default-boot-target> |
| ✅ | 91 | Change Default Boot Target | <https://github.com/kelvintechnical/change-default-boot-target> |
| ✅ | 92 | System Reboots and Shutdowns | <https://github.com/kelvintechnical/reboot-shutdown-systemd> |
| ✅ | 93 | List All System Units | <https://github.com/kelvintechnical/list-system-units> |
| ✅ | 94 | Check Service Status | <https://github.com/kelvintechnical/service-status-check> |
| ✅ | 95 | Start and Stop Services | <https://github.com/kelvintechnical/start-stop-services> |
| ✅ | 96 | Enable Services at Boot | <https://github.com/kelvintechnical/enable-services-at-boot> |
| ✅ | 97 | Disable Services at Boot | <https://github.com/kelvintechnical/disable-services-at-boot> |
| ✅ | 98 | Mask System Services | <https://github.com/kelvintechnical/mask-system-services> |
| ✅ | 99 | Create and Manage systemd Unit Files | <https://github.com/kelvintechnical/systemd-unit-files> |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | SYSD-F01 | Set the Default Boot Target to `multi-user.target` | `systemctl set-default multi-user.target`, `systemctl isolate multi-user.target` for immediate effect, prove with `systemctl get-default` + reboot |

---

### 📋 Log Management (README Labs 100–106)

| Status | # | Lab | Full Path |
|---|---|---|---|
| ✅ | 100 | Analyze Boot Performance | <https://github.com/kelvintechnical/analyze-boot-performance> |
| 🚧 | 101 | Query Logs with journalctl | *(coming soon — see Lab #101 in [README](README.md#-log-management))* |
| 🚧 | 102 | Configure Persistent Journal Logs | *(coming soon — see Lab #102 in [README](README.md#-log-management))* |
| 🚧 | 103 | Understand Log Routing | *(coming soon — see Lab #103 in [README](README.md#-log-management))* |
| 🚧 | 104 | Monitor Authentication Logs | *(coming soon — see Lab #104 in [README](README.md#-log-management))* |
| 🚧 | 105 | Filter systemd Journals by Priority | *(coming soon — see Lab #105 in [README](README.md#-log-management))* |
| 🚧 | 106 | Service-Specific Journal Logs | *(coming soon — see Lab #106 in [README](README.md#-log-management))* |

---

### ⏰ System Time & Locale (README Labs 107–109)

| Status | # | Lab | Full Path |
|---|---|---|---|
| ✅ | 107 | Configure Timezone and Time Synchronization | <https://github.com/kelvintechnical/Configure-Timezone-and-Time-Synchronization> |
| 🚧 | 108 | Check NTP Sync Status | *(coming soon — see Lab #108 in [README](README.md#-system-time--locale))* |
| ✅ | 109 | Configure NTP Time Source | <https://github.com/kelvintechnical/configure-ntp> |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | TIME-F01 | Set System Timezone via `timedatectl` | `timedatectl set-timezone Europe/London` — also practice America/New_York and Asia/Tokyo; verify with `timedatectl` and `date` |
| 📅 | TIME-F02 | Configure Chrony with a Specific NTP Server | Edit `/etc/chrony.conf`: comment out default pool, add `server utility.ntp.org iburst`, restart chronyd, `chronyc sources -v` showing `^*` reachability |

---

### 💾 Storage Management (README Labs 110–120)

| Status | # | Lab | Full Path |
|---|---|---|---|
| 🚧 | 110 | Inspect Filesystems | *(coming soon — see Lab #110 in [README](README.md#-storage-management))* |
| 🚧 | 111 | Display Partition Tables | *(coming soon — see Lab #111 in [README](README.md#-storage-management))* |
| 🚧 | 112 | Create MBR Partition with fdisk | *(coming soon — see Lab #112 in [README](README.md#-storage-management))* |
| 🚧 | 113 | Change Partition Types in fdisk | *(coming soon — see Lab #113 in [README](README.md#-storage-management))* |
| 🚧 | 114 | Create GPT Partition with gdisk | *(coming soon — see Lab #114 in [README](README.md#-storage-management))* |
| 🚧 | 115 | Command-Line Partitioning with parted | *(coming soon — see Lab #115 in [README](README.md#-storage-management))* |
| 🚧 | 116 | Format Partition with XFS | *(coming soon — see Lab #116 in [README](README.md#-storage-management))* |
| 🚧 | 117 | Format Partition with Ext4 | *(coming soon — see Lab #117 in [README](README.md#-storage-management))* |
| 🚧 | 118 | Check Filesystem Consistency | *(coming soon — see Lab #118 in [README](README.md#-storage-management))* |
| 🚧 | 119 | Inspect Filesystem Features | *(coming soon — see Lab #119 in [README](README.md#-storage-management))* |
| 🚧 | 120 | Create and Activate Swap Space | *(coming soon — see Lab #120 in [README](README.md#-storage-management))* |
| 🚧 | — | Create a Swap Partition by UUID (in-repo) | [`labs/storage-swap-partition-uuid/`](labs/storage-swap-partition-uuid/) |
| 🚧 | — | Create an Ext4 Partition Mounted by LABEL (in-repo) | [`labs/storage-ext4-partition-label/`](labs/storage-ext4-partition-label/) |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | STOR-F03 | Create an MBR Partition with ext4 Mounted by LABEL | `parted /dev/vdb mklabel msdos`, `mkpart primary ext4 1MiB 2GiB`, `mkfs.ext4 -L MYDEV`, fstab `LABEL=MYDEV /mnt/dev ext4 defaults 0 2`, prove persistence after reboot |
| 📅 | STOR-F04 | Create a Companion LVM-Type Partition on the Same Disk | `parted /dev/vdb mkpart primary 2GiB 7GiB`, `set 2 lvm on`, prove with `fdisk -l` showing partition type `Linux LVM` — preps the disk for an LVM lab |

---

### 🗂 LVM (Logical Volume Management) (README Labs 121–130)

| Status | # | Lab | Full Path |
|---|---|---|---|
| 🚧 | 121 | Initialize Physical Volumes | *(coming soon — see Lab #121 in [README](README.md#-lvm-logical-volume-management))* |
| 🚧 | 122 | Display Physical Volumes | *(coming soon — see Lab #122 in [README](README.md#-lvm-logical-volume-management))* |
| 🚧 | 123 | Create Volume Group | *(coming soon — see Lab #123 in [README](README.md#-lvm-logical-volume-management))* |
| 🚧 | 124 | Display Volume Groups | *(coming soon — see Lab #124 in [README](README.md#-lvm-logical-volume-management))* |
| 🚧 | 125 | Create Logical Volume | *(coming soon — see Lab #125 in [README](README.md#-lvm-logical-volume-management))* |
| 🚧 | 126 | Display Logical Volumes | *(coming soon — see Lab #126 in [README](README.md#-lvm-logical-volume-management))* |
| 🚧 | 127 | Extend Volume Group | *(coming soon — see Lab #127 in [README](README.md#-lvm-logical-volume-management))* |
| 🚧 | 128 | Extend Logical Volume | *(coming soon — see Lab #128 in [README](README.md#-lvm-logical-volume-management))* |
| 🚧 | 129 | Resize Filesystem After Extend | *(coming soon — see Lab #129 in [README](README.md#-lvm-logical-volume-management))* |
| 🚧 | 130 | Remove LVM Components | *(coming soon — see Lab #130 in [README](README.md#-lvm-logical-volume-management))* |
| ✅ | LAB | Create LV `lvol1` (ext4, 280 MB) | <https://github.com/kelvintechnical/lvm-create-lvol1-ext4> ([also `labs/lvm-create-lvol1-ext4/`](labs/lvm-create-lvol1-ext4/)) |
| ✅ | — | Create LV with XFS Filesystem (in-repo) | [`labs/lvm-create-lv1-xfs/`](labs/lvm-create-lv1-xfs/) |
| 🚧 | — | Online Extend an LV and Its Filesystem Without Unmounting (in-repo) | [`labs/lvm-online-extend-xfs/`](labs/lvm-online-extend-xfs/) |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | LVM-F02 | Create an LVM VDO Volume with Thin Provisioning | `vdo create --name=vdo1 --device=/dev/sdb --vdoLogicalSize=20G`; mount with ext4 and XFS variants; persistent fstab with `_netdev,x-systemd.requires=vdo.service` |
| 📅 | LVM-F03 | LV by Extent Count in a VG with Custom PE Size (ext4 variant) | `vgcreate -s 8M vgstore /dev/vdb1`, `lvcreate -l 50 -n lvdata vgstore` (= 400 MiB LV), mkfs.ext4, persistent mount on `/mnt/data` |
| 📅 | LVM-F04 | LV Sized as a Percentage of the VG with XFS + UUID Mount | `lvcreate -l 50%VG -n mylv myvg`, mkfs.xfs, capture UUID with `blkid`, fstab UUID entry on `/mnt/mylv` |
| 📅 | LVM-F05 | LV Sized as a Percentage of Free Space with XFS | `lvcreate -l 75%FREE -n lvstore vgdata`, mkfs.xfs, fstab UUID entry on `/mnt/lvm` |
| 📅 | LVM-F06 | LV with Extent Count + Reserved Free Extents Constraint | `vgcreate -s 16M team_vg /dev/sdb1`, `lvcreate -l 40 -n team_lv team_vg` while leaving at least 10 free extents |
| 📅 | LVM-F07 | Online Resize LV to a New Total Extent Count + Grow ext4 | `lvresize -l 85 /dev/vgstore/lvdata && resize2fs ...`; `-l 85` means "exactly 85 extents total," not "add 85" |
| 📅 | LVM-F08 | Add Extents to an Existing LV + Grow XFS Online | `lvextend -l +8 /dev/team_vg/team_lv && xfs_growfs /mnt/team_lv` |
| 📅 | LVM-F09 | Create Swap from Remaining VG Free Space | `lvcreate -L 500M -n swap_lv team_vg`, `mkswap`, `swapon`, fstab UUID entry `swap swap defaults 0 0` |

---

### 📁 Filesystem Mounts (README Labs 131–136)

| Status | # | Lab | Full Path |
|---|---|---|---|
| 🚧 | 131 | Mount Filesystem Manually | *(coming soon — see Lab #131 in [README](README.md#-filesystem-mounts))* |
| 🚧 | 132 | Retrieve Filesystem UUIDs | *(coming soon — see Lab #132 in [README](README.md#-filesystem-mounts))* |
| 🚧 | 133 | Configure Persistent Mounts fstab | *(coming soon — see Lab #133 in [README](README.md#-filesystem-mounts))* |
| 🚧 | 134 | Mount Network CIFS Shares | *(coming soon — see Lab #134 in [README](README.md#-filesystem-mounts))* |
| 🚧 | 135 | Remount with New Options | *(coming soon — see Lab #135 in [README](README.md#-filesystem-mounts))* |
| 🚧 | 136 | Manage Autofs Service | *(coming soon — see Lab #136 in [README](README.md#-filesystem-mounts))* |

**NFS & AutoFS Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | NFS-F01 | NFS Server + AutoFS Direct Map | Export `/rh_share` on server; client `/etc/auto.master.d/direct.autofs` + `/etc/auto.direct` map mounts share on demand at `/mnt/rh_share` |
| 📅 | NFS-F02 | NFS Home-Directory Export with AutoFS Indirect Map on Login | Server exports `/home/user60`; client indirect map under `/nfsdir` mounts home dir automatically first login; prove unmount-on-idle |
| 📅 | NFS-F03 | NFS Static Export with Persistent `/etc/fstab` Mount | `exportfs -rav` on server, `server:/share5 /share6 nfs _netdev,defaults 0 0` in fstab on client, `mount -a`, prove survives reboot |
| 📅 | NFS-F04 | Configure a Node as an NFS Server (companion lab) | `dnf install nfs-utils`, `mkdir /exports/home`, `/etc/exports` `/exports/home *(rw,sync,no_root_squash)`, `exportfs -rav`, `systemctl enable --now nfs-server`, `firewall-cmd --add-service={nfs,mountd,rpc-bind}` |
| 📅 | NFS-F05 | AutoFS Indirect Map for Remote Home Dirs with 60s Timeout | `auto.master.d/homes.autofs` entry `/homes/remote /etc/auto.homes --timeout=60`, `/etc/auto.homes` with `* server.example.com:/exports/home/&` |
| 📅 | NFS-F06 | AutoFS Direct Map for `/mnt/shared` with 5-Minute Timeout | `auto.master.d/direct.autofs` `/- /etc/auto.direct --timeout=300`, `/etc/auto.direct` `/mnt/shared -rw server.example.com:/srv/shared` |

---

### 📦 Package Management & Repositories (README Labs 137–161)

| Status | # | Lab | Full Path |
|---|---|---|---|
| 🚧 | 137 | Install Local RPM Package | *(coming soon — see Lab #137 in [README](README.md#-package-management--repositories))* |
| 🚧 | 138 | Upgrade RPM Package | *(coming soon — see Lab #138 in [README](README.md#-package-management--repositories))* |
| 🚧 | 139 | Install New Kernel Safely | *(coming soon — see Lab #139 in [README](README.md#-package-management--repositories))* |
| 🚧 | 140 | Uninstall Package rpm -e | *(coming soon — see Lab #140 in [README](README.md#-package-management--repositories))* |
| 🚧 | 141 | Query All Installed Packages | *(coming soon — see Lab #141 in [README](README.md#-package-management--repositories))* |
| 🚧 | 142 | Query Specific Package Info | *(coming soon — see Lab #142 in [README](README.md#-package-management--repositories))* |
| 🚧 | 143 | List Files Within Package | *(coming soon — see Lab #143 in [README](README.md#-package-management--repositories))* |
| 🚧 | 144 | Identify File Owner | *(coming soon — see Lab #144 in [README](README.md#-package-management--repositories))* |
| 🚧 | 145 | Query Uninstalled RPMs | *(coming soon — see Lab #145 in [README](README.md#-package-management--repositories))* |
| 🚧 | 146 | Verify Package Integrity | *(coming soon — see Lab #146 in [README](README.md#-package-management--repositories))* |
| 🚧 | 147 | System-Wide Verification | *(coming soon — see Lab #147 in [README](README.md#-package-management--repositories))* |
| 🚧 | 148 | Import GPG Key | *(coming soon — see Lab #148 in [README](README.md#-package-management--repositories))* |
| 🚧 | 149 | Check Package Signatures | *(coming soon — see Lab #149 in [README](README.md#-package-management--repositories))* |
| ✅ | 150 | Configure Repository Access | <https://github.com/kelvintechnical/Configure-Repository-Access-> |
| 🚧 | 151 | Install Packages with dnf | *(coming soon — see Lab #151 in [README](README.md#-package-management--repositories))* |
| 🚧 | 152 | Remove Packages with dnf | *(coming soon — see Lab #152 in [README](README.md#-package-management--repositories))* |
| 🚧 | 153 | Update System dnf update | *(coming soon — see Lab #153 in [README](README.md#-package-management--repositories))* |
| 🚧 | 154 | Search for Software | *(coming soon — see Lab #154 in [README](README.md#-package-management--repositories))* |
| 🚧 | 155 | Find File Providers | *(coming soon — see Lab #155 in [README](README.md#-package-management--repositories))* |
| 🚧 | 156 | List dnf Packages | *(coming soon — see Lab #156 in [README](README.md#-package-management--repositories))* |
| 🚧 | 157 | Display Enabled Repositories | *(coming soon — see Lab #157 in [README](README.md#-package-management--repositories))* |
| 🚧 | 158 | View Package Group Info | *(coming soon — see Lab #158 in [README](README.md#-package-management--repositories))* |
| ✅ | 159 | Install Package Groups | <https://github.com/kelvintechnical/install-package-group> |
| 🚧 | 160 | Create Custom YUM Repository | *(coming soon — see Lab #160 in [README](README.md#-package-management--repositories))* |
| ✅ | 161 | Managing Flatpak | <https://github.com/kelvintechnical/Managing-Flatpak> |
| 🚧 | — | Install Development Tools Package Group with Output Capture (in-repo) | [`labs/dnf-install-dev-tools-capture/`](labs/dnf-install-dev-tools-capture/) |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | PKG-F02 | Configure Local Repository from Installation ISO Media | Mount RHEL 9 ISO at `/repo` with a persistent loop entry in `/etc/fstab`, create `/etc/yum.repos.d/local-baseos.repo` + `local-appstream.repo` pointing at `file:///repo/BaseOS` and `/repo/AppStream` with `gpgcheck=0` |
| 📅 | PKG-F03 | Configure Two HTTP-Hosted Repositories from a Network Source | BaseOS and AppStream `.repo` files pointing at `http://repo.example.com/rhel9/{BaseOS,AppStream}` with `enabled=1`, prove with `dnf repolist enabled` + `dnf install -y httpd` |

---

### 👥 User & Group Management (README Labs 162–183)

| Status | # | Lab | Full Path |
|---|---|---|---|
| 🚧 | 162 | Inspect Password Database | *(coming soon — see Lab #162 in [README](README.md#-user--group-management))* |
| 🚧 | 163 | Analyze Shadow File | *(coming soon — see Lab #163 in [README](README.md#-user--group-management))* |
| 🚧 | 164 | Modify Default Password Aging | *(coming soon — see Lab #164 in [README](README.md#-user--group-management))* |
| ✅ | 165 | User & Group Management / Permissions | <https://github.com/kelvintechnical/User-Group-Management-Permissions> |
| 🚧 | 166 | Modify Existing Account | *(coming soon — see Lab #166 in [README](README.md#-user--group-management))* |
| 🚧 | 167 | Advanced Group Management | *(coming soon — see Lab #167 in [README](README.md#-user--group-management))* |
| 🚧 | 168 | Force Password Changes | *(coming soon — see Lab #168 in [README](README.md#-user--group-management))* |
| 🚧 | 169 | Safely Delete Users | *(coming soon — see Lab #169 in [README](README.md#-user--group-management))* |
| ✅ | 170 | Disable User Login Without Removing the Account | <https://github.com/kelvintechnical/disable-user-login> |
| 🚧 | 171 | Validate User and Group Creation | *(coming soon — see Lab #171 in [README](README.md#-user--group-management))* |
| 🚧 | 172 | Proper Use of su vs su - | *(coming soon — see Lab #172 in [README](README.md#-user--group-management))* |
| 🚧 | 173 | Limit Access to su PAM | *(coming soon — see Lab #173 in [README](README.md#-user--group-management))* |
| 🚧 | 174 | Configure Custom Administrators | *(coming soon — see Lab #174 in [README](README.md#-user--group-management))* |
| 🚧 | 175 | Granular sudo Privileges | *(coming soon — see Lab #175 in [README](README.md#-user--group-management))* |
| 🚧 | 176 | Limit root Logins | *(coming soon — see Lab #176 in [README](README.md#-user--group-management))* |
| 🚧 | 177 | Restrict Root to Single Console | *(coming soon — see Lab #177 in [README](README.md#-user--group-management))* |
| 🚧 | 178 | Populate Directory Templates | *(coming soon — see Lab #178 in [README](README.md#-user--group-management))* |
| 🚧 | 179 | Manage Shell Environments | *(coming soon — see Lab #179 in [README](README.md#-user--group-management))* |
| 🚧 | 180 | Alter Global Default umask | *(coming soon — see Lab #180 in [README](README.md#-user--group-management))* |
| 🚧 | 181 | Distribute Documentation via Skel | *(coming soon — see Lab #181 in [README](README.md#-user--group-management))* |
| 🚧 | 182 | Control Group Ownership SGID | *(coming soon — see Lab #182 in [README](README.md#-user--group-management))* |
| 🚧 | 183 | Set Up Group-Managed Directory | *(coming soon — see Lab #183 in [README](README.md#-user--group-management))* |
| ✅ | — | Lock User Account and Capture Regex Evidence (in-repo) | [`labs/user-lock-capture-regex/`](labs/user-lock-capture-regex/) |

**User & Group Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | USER-F01 | Group with Fixed GID + User with Primary/Secondary Groups | `groupadd -g 3500 admins`, `groupadd users`, `useradd -u 3455 -g admins -G users harry`, prove with `id harry` |
| 📅 | USER-F02 | User Without Interactive Shell (`nologin`) That Still Authenticates | `useradd -s /sbin/nologin sarah`, set password, prove SSH login rejected but PAM-level password auth succeeds for password-only services |
| 📅 | USER-F03 | User With Explicit (Hand-Built) Home Directory | `useradd -M bruce`, `mkdir /home/bruce`, `cp -av /etc/skel/. /home/bruce`, `chown -R bruce:bruce`, `chmod 700` |
| 📅 | USER-F04 | Force Password Change at Next Login | `passwd --expire liam` (or `chage -d 0 liam`), prove with `chage -l liam`, then ssh in and observe the forced-change prompt |
| 📅 | USER-F05 | Set Hard Account Expiry Date | `chage -E 2029-01-01 lina`, or `chage -E $(date -d '+7 days' +%Y-%m-%d) marvin` for relative expiry, prove with `chage -l USER` |
| 📅 | USER-F06 | Welcome.txt Auto-Created for Every New User via `/etc/skel` | `echo "Welcome Onboard!" > /etc/skel/Welcome.txt`, useradd a new user, verify Welcome.txt appears with right ownership and mode |
| 📅 | USER-F07 | Configure System-Wide Password Aging Policy | Edit `/etc/login.defs`: `PASS_MAX_DAYS 30`, `PASS_MIN_LEN 9`; prove the policy applies only to users created *after* the edit |
| 📅 | USER-F08 | Reset Root Password from GRUB Boot Menu (`rd.break` Path) | Edit GRUB at boot, append `rd.break`, ctrl-x, `mount -o remount,rw /sysroot`, `chroot /sysroot`, `passwd root`, `touch /.autorelabel`, two `exit`s, reboot |

**Sudo & Privilege Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | SUDO-F01 | Full Sudo for a User + NOPASSWD for an Entire Group | `visudo`: `john ALL=(ALL) ALL` + `%admins ALL=(ALL) NOPASSWD: ALL`, prove via `sudo -l` per user |
| 📅 | SUDO-F02 | Granular Sudo: Allow `passwd` Except Root Password Changes | `visudo`: `brian ALL=(ALL) /usr/bin/passwd [A-Za-z]*, !/usr/bin/passwd root, !/usr/bin/passwd ""` |
| 📅 | SUDO-F03 | Privileged User with Account Expiry | `useradd -u 4545 marvin`, `passwd marvin`, add to wheel, `chage -E $(date -d '+7 days' +%F) marvin` |

---

### 🔄 Process Management (README Labs 184–192)

| Status | # | Lab | Full Path |
|---|---|---|---|
| 🚧 | 184 | Audit All Running Processes | *(coming soon — see Lab #184 in [README](README.md#-process-management))* |
| 🚧 | 185 | Identify Process Details | *(coming soon — see Lab #185 in [README](README.md#-process-management))* |
| 🚧 | 186 | View SELinux Process Contexts | *(coming soon — see Lab #186 in [README](README.md#-process-management))* |
| 🚧 | 187 | Real-Time Process Monitoring | *(coming soon — see Lab #187 in [README](README.md#-process-management))* |
| 🚧 | 188 | Adjust Process Priority | *(coming soon — see Lab #188 in [README](README.md#-process-management))* |
| 🚧 | 189 | Start Processes with Custom Priority | *(coming soon — see Lab #189 in [README](README.md#-process-management))* |
| 🚧 | 190 | Terminate Processes Gracefully | *(coming soon — see Lab #190 in [README](README.md#-process-management))* |
| 🚧 | 191 | Force Kill Unresponsive Processes | *(coming soon — see Lab #191 in [README](README.md#-process-management))* |
| 🚧 | 192 | Kill Processes by Name | *(coming soon — see Lab #192 in [README](README.md#-process-management))* |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | PROC-F01 | Start a Background Process with a Specific nice Value | `nice -n 10 sleep 3600 &`, capture `$!` into a variable, verify nice value with `ps -o pid,ni,cmd $!` |
| 📅 | PROC-F02 | Renice a Running Process to a Higher Priority | `renice -n -5 -p $PID` — requires root for negative niceness, prove with `ps -o pid,ni` before and after |
| 📅 | PROC-F03 | Lowest-Priority Background Task on User Login | As `lina`: in `~/.bash_profile` add `nice -n 19 sleep infinity &`, verify with `ps -o pid,ni -u lina` showing `19` |
| 📅 | PROC-F04 | Clean Termination of a Background Process | `kill $PID` for SIGTERM first, verify exit, fall back to `kill -9` only on hung processes |

---

### 🗜 Archives & Compression (README Labs 193–198)

| Status | # | Lab | Full Path |
|---|---|---|---|
| ✅ | 193 | Standard File Compression with gzip | <https://github.com/kelvintechnical/standard-file-compression> |
| ✅ | 194 | High-Ratio Compression with bzip2 | <https://github.com/kelvintechnical/high-ratio-compression> |
| ✅ | 195 | Create Standard Archives with tar | <https://github.com/kelvintechnical/create-standard-archives> |
| 🚧 | 196 | Create Compressed Archives | *(coming soon — see Lab #196 in [README](README.md#-archives--compression))* |
| 🚧 | 197 | Extract Archives | *(coming soon — see Lab #197 in [README](README.md#-archives--compression))* |
| 🚧 | 198 | Preserve Security Contexts in Archives | *(coming soon — see Lab #198 in [README](README.md#-archives--compression))* |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | ARCH-F01 | Create an xz-Compressed Tar Archive | `tar -cJvf /archives/config_backup.tar.xz /etc`, restore with `tar -xJvf` into `/restore` — highest-compression-ratio option |
| 📅 | ARCH-F02 | Create an Uncompressed Standard Tar Archive | `tar -cvf /root/etc_opt.bak.tar /etc /opt` — the no-compression variant for streaming to other compressors |
| 📅 | ARCH-F03 | Restore a Tar Archive into a Specific Destination Directory | `mkdir -p /root/restored_tmp && tar -xzvf /root/tmp.tgz -C /root/restored_tmp`, prove with `find /root/restored_tmp -maxdepth 2` |

---

### 🕐 Scheduled Tasks (README Labs 199–207)

| Status | # | Lab | Full Path |
|---|---|---|---|
| 🚧 | 199 | Review System-Wide cron Jobs | *(coming soon — see Lab #199 in [README](README.md#-scheduled-tasks))* |
| 🚧 | 200 | Schedule Tasks with cron | *(coming soon — see Lab #200 in [README](README.md#-scheduled-tasks))* |
| 🚧 | 201 | Remove User cron Jobs | *(coming soon — see Lab #201 in [README](README.md#-scheduled-tasks))* |
| 🚧 | 202 | Schedule One-Time Task with at | *(coming soon — see Lab #202 in [README](README.md#-scheduled-tasks))* |
| 🚧 | 203 | Limit Access to cron | *(coming soon — see Lab #203 in [README](README.md#-scheduled-tasks))* |
| 🚧 | 204 | Limit Access to at | *(coming soon — see Lab #204 in [README](README.md#-scheduled-tasks))* |
| 🚧 | 205 | Review the Anacron System | *(coming soon — see Lab #205 in [README](README.md#-scheduled-tasks))* |
| 🚧 | 206 | Create a Specific cron Job | *(coming soon — see Lab #206 in [README](README.md#-scheduled-tasks))* |
| 🚧 | 207 | Schedule Software Audit with at | *(coming soon — see Lab #207 in [README](README.md#-scheduled-tasks))* |
| ✅ | LAB | Scheduling Jobs (systemd timer, Mon–Fri 2 AM) | <https://github.com/kelvintechnical/scheduling-jobs-systemd-timer> ([also `labs/scheduling-jobs-systemd-timer/`](labs/scheduling-jobs-systemd-timer/)) |
| 🚧 | — | User-Level Cron Job with `find -exec` (in-repo) | [`labs/cron-user-find-exec-coredir/`](labs/cron-user-find-exec-coredir/) |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CRON-F02 | User Cron Job at 12:45 AM Daily | As `bruce`: `crontab -e` `45 0 * * * /usr/bin/echo "EX200 Practice Test!" >> $HOME/cron.log` |
| 📅 | CRON-F03 | Recurring User Cron Job Every 2 Minutes | As `linda`: `*/2 * * * * logger "RHCSA EX200 Practice Test 2 In Progress!"` |
| 📅 | CRON-F04 | Weekday-Only Cron Job at 5:45 AM | As `emma`: `45 5 * * 1-5 logger "Good morning! Work day about to start."` |
| 📅 | CRON-F05 | Midnight-Weekend Root Cron Job to Clean Empty Files in `/tmp` | Root crontab: `0 0 * * 6,0 find /tmp -maxdepth 1 -type f -empty -delete` |
| 📅 | CRON-F06 | One-Time `at` Job for a Specific Wall-Clock Time | As `russ`: `echo 'echo "EX200 Mock Practice 1 Complete!" >> $HOME/practice.log' \| at 21:30` |
| 📅 | CRON-F07 | One-Time `at` Job One Hour from Now Writing to journald | As `alina`: `echo 'logger "Making Progress with EX200!"' \| at now + 1 hour` |

---

### 🔐 GPG Encryption (README Labs 208–211)

| Status | # | Lab | Full Path |
|---|---|---|---|
| 🚧 | 208 | Generate a GPG Key Pair | *(coming soon — see Lab #208 in [README](README.md#-gpg-encryption))* |
| 🚧 | 209 | Encrypt a File with GPG | *(coming soon — see Lab #209 in [README](README.md#-gpg-encryption))* |
| 🚧 | 210 | Decrypt a GPG File | *(coming soon — see Lab #210 in [README](README.md#-gpg-encryption))* |
| 🚧 | 211 | Share and Verify Public Keys | *(coming soon — see Lab #211 in [README](README.md#-gpg-encryption))* |

---

### 🔗 Remote Administration & Network Tools (README Labs 212–215)

| Status | # | Lab | Full Path |
|---|---|---|---|
| 🚧 | 212 | SSH and SCP File Transfer | *(coming soon — see Lab #212 in [README](README.md#-remote-administration--network-tools))* |
| 🚧 | 213 | Network Troubleshooting | *(coming soon — see Lab #213 in [README](README.md#-remote-administration--network-tools))* |
| ✅ | 214 | Command-Line Web and FTP Testing | <https://github.com/kelvintechnical/elinks-iftp> |
| ✅ | 215 | Command-Line Email Testing | <https://github.com/kelvintechnical/mutt-mail-smtp> |

**SSH Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | SSH-F01 | Configure SSH to Listen on a Custom Port | `sshd_config Port 88`, SELinux `semanage port -a -t ssh_port_t -p tcp 88`, `firewall-cmd --add-port=88/tcp --permanent`, restart sshd |
| 📅 | SSH-F02 | Permit Root SSH Login with Authentication-Failure Lockout | `sshd_config PermitRootLogin yes` + `MaxAuthTries 3`, demonstrate the 4th failed attempt is rejected and earlier produce auth-failure lines |
| 📅 | SSH-F03 | Passwordless SSH from Root to Remote Root | `ssh-keygen -t ed25519 -N ""` on Node1, `ssh-copy-id root@Node2`, verify with `ssh root@Node2 hostname` |
| 📅 | SSH-F04 | Key-Based SSH from a User to a Remote Root on a Custom Port | As `marvin` on Node2: `ssh-keygen`, `ssh-copy-id -p 88 root@Node1`, prove `ssh -p 88 root@Node1` succeeds without a password |
| 📅 | SSH-F05 | Configure Local `/etc/hosts` Name Resolution | Add `192.168.56.25 node1.lab3.example.net node1` so `ping node1` resolves locally, persists across reboots, and `ssh node1` works without DNS |
| 📅 | SSH-F06 | Secure File Transfer with `scp` Preserving Attributes | `scp -p /etc/fstab user@host:~/` — `-p` preserves timestamps and mode but NOT ownership across users; for ownership use `rsync -avz --chown` |

---

### 🛡 Security Administration (README Labs 216–220)

| Status | # | Lab | Full Path |
|---|---|---|---|
| 🚧 | 216 | Service Isolation Bastion Host | *(coming soon — see Lab #216 in [README](README.md#-security-administration))* |
| 🚧 | 217 | Monitor Security Updates | *(coming soon — see Lab #217 in [README](README.md#-security-administration))* |
| 🚧 | 218 | Build a Bastion Server | *(coming soon — see Lab #218 in [README](README.md#-security-administration))* |
| 🚧 | 219 | Comprehensive firewalld Setup | *(coming soon — see Lab #219 in [README](README.md#-security-administration))* |
| 🚧 | 220 | PAM and SELinux with FTP | *(coming soon — see Lab #220 in [README](README.md#-security-administration))* |

---

### 🌍 Web Services (Apache) (README Labs 221–224)

| Status | # | Lab | Full Path |
|---|---|---|---|
| ✅ | 221 | Configure Apache to Serve Default and Custom Web Content | <https://github.com/kelvintechnical/apache-custom-content> |
| 🚧 | 222 | Password-Protect a Directory | *(coming soon — see Lab #222 in [README](README.md#-web-services-apache))* |
| 🚧 | 223 | Deploy Name-Based Virtual Hosts | *(coming soon — see Lab #223 in [README](README.md#-web-services-apache))* |
| 🚧 | 224 | Configure Secure Virtual Hosts HTTPS | *(coming soon — see Lab #224 in [README](README.md#-web-services-apache))* |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | WEB-F01 | Apache Listening on a Non-Standard TCP Port | `Listen 85` in `/etc/httpd/conf.d/port.conf` drop-in, `semanage port -a -t http_port_t -p tcp 85`, `firewall-cmd --add-port=85/tcp --permanent`, `curl http://localhost:85` |
| 📅 | WEB-F02 | Apache Default Page + Custom Content Directory | Modify `/var/www/html/index.html`, create `/web/practice.html`, `Require all granted`, `semanage fcontext httpd_sys_content_t` for `/web(/.*)?`, `restorecon -Rv /web` |
| 📅 | WEB-F03 | Apache Subdirectory Routing with SELinux Inheritance | `mkdir /var/www/html/route_station`, drop index.html, confirm inherited `httpd_sys_content_t` from parent, curl `http://Node1/route_station/index.html` |
| 📅 | WEB-F04 | Password-Protected Apache Directory with htpasswd | `htpasswd -c /etc/httpd/.htpasswd alice`, `AuthType Basic` + `AuthUserFile` + `Require valid-user`, prove anonymous returns HTTP 401 |
| 📅 | WEB-F05 | Apache SSL Virtual Host with Self-Signed Certificate | `openssl req -x509 -newkey rsa:2048 -nodes -keyout ... -out ... -days 365`, ssl.conf `SSLCertificateFile`/`SSLCertificateKeyFile`, `firewall-cmd --add-service=https` |

---

### ⚡ System Performance & Tuning (README Lab 225)

| Status | # | Lab | Full Path |
|---|---|---|---|
| ✅ | 225 | Enable Recommended Tuning Profile | <https://github.com/kelvintechnical/tuning-profile> |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | PERF-F01 | Apply the `virtual-guest` Tuning Profile | `tuned-adm profile virtual-guest` — virtualization-efficiency profile for VMs, verify with `tuned-adm active` |
| 📅 | PERF-F02 | Apply a Power-Saving / Virtualization-Balanced Profile | `tuned-adm profile balanced-battery` or `virtual-guest-powersave`, compare with `tuned-adm recommend`, prove active profile changed |

---

### 📜 Shell Scripting & Automation (README Labs 226–227)

| Status | # | Lab | Full Path |
|---|---|---|---|
| ✅ | 226 | Argument-Based Conditional Script | <https://github.com/kelvintechnical/argument-script> |
| 🚧 | 227 | Use for Loops for Iteration | *(coming soon — see Lab #227 in [README](README.md#-shell-scripting--automation))* |
| 🚧 | — | Bidirectional Bash Script with Argument Logic (in-repo) | [`labs/bash-bidirectional-arg-script/`](labs/bash-bidirectional-arg-script/) |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | SCRIPT-F02 | Bash Script: Find Files Matching a Pattern and Print stat | Loop over `/usr/bin/ac*`, `[ -f $f ]` guard to exclude directories, run `stat $f` for each match, redirect to `/var/tmp/acstats.out` |
| 📅 | SCRIPT-F03 | Bash Script: Create a User Whose Name Comes from a Variable | Declare `ENV1=book1`, `useradd "$ENV1"`, set default password from stdin, verify `id "$ENV1"` |
| 📅 | SCRIPT-F04 | Countdown Timer Script with Argument or Interactive Prompt | If `$# -eq 1`, `COUNT=$1`; else `read -p`; `while [ $COUNT -gt 0 ]; do echo "$COUNT seconds remaining..."; sleep 1; ((COUNT--)); done` |
| 📅 | SCRIPT-F05 | Sum of an Unknown Number of Integer Arguments | `$# -eq 0` → exit 1; else `for n in "$@"; do ((total+=n)); done; echo "Sum is $total"` |
| 📅 | SCRIPT-F06 | Find Users by Login Shell and Save the List | `getent passwd \| awk -F: '$7=="/bin/bash" {print $1}' > /root/bash_users.txt`, chmod +x, re-runnable so file is always current |
| 📅 | SCRIPT-F07 | Extract Login Shells of the Last 5 Users in `/etc/passwd` | `tail -5 /etc/passwd \| awk -F: '{printf "User %s has login shell %s\n", $1, $7}'` |
| 📅 | SCRIPT-F08 | Per-User Login Script via `.bash_profile` | As `john`: append `grep bash /etc/passwd > ~/bash-users.txt` to `~/.bash_profile` — every interactive login refreshes the file |
| 📅 | SCRIPT-F09 | Three-Way Argument-Based Script with Multi-Arg Rejection | `team.sh`: `$# > 1` → exit 5; `$1 == "ops"` → message; `$1 == "dev"` → different message; else usage |

---

### 🐳 Containers & Runtime Management (README LAB row)

| Status | # | Lab | Full Path |
|---|---|---|---|
| ✅ | LAB | Launch Named Root Container with Port Mapping | <https://github.com/kelvintechnical/Launch-Named-Root-Container-with-Port-Mapping> |
| 🚧 | — | Rootless Container with Bind Mount and systemd Auto-Start (in-repo) | [`labs/podman-rootless-bind-mount-systemd/`](labs/podman-rootless-bind-mount-systemd/) |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CON-F02 | Build a Custom Container Image with a Containerfile | Write a Containerfile FROM ubi8/ubi9, RUN/COPY a small script printing `ls` + `pwd`, `podman build -t custom:latest`, push to local registry, run as named rootless container under `user60` |
| 📅 | CON-F03 | Rootless Container with Port Mapping + systemd Auto-Start | As `user60`: `podman run -d --name web -p 10000:80 ubi8`, `podman generate systemd --new --files`, copy to `~/.config/systemd/user/`, `loginctl enable-linger` |
| 📅 | CON-F04 | Rootless Container with Bind Mount + Env Vars + Port Mapping | `podman run` as `user60` with `-v /host_data01:/container_data01`, `-e ENVIRON=Exam`, `-e KERN=$(uname -r)`, `-p 1050:1050`, ubi9; user-level systemd unit with linger |
| 📅 | CON-F05 | Authenticated Pull from `registry.redhat.io` | `podman login registry.redhat.io` with developer credentials, pull `ubi9/ubi`, prove with `podman images` |
| 📅 | CON-F06 | Build a UBI Image from a Single-Line Containerfile | Containerfile with just `FROM registry.redhat.io/ubi8/ubi-init`, `podman build -t ubigreeter`, podman run --rm |
| 📅 | CON-F07 | Rootless HTTP Container with Bind-Mounted DocumentRoot | `podman run -d --name webcon -p 8080:80 -v /var/www/html:/usr/local/apache2/htdocs:Z docker.io/library/httpd`, echo content > index.html, `curl localhost:8080` |
| 📅 | CON-F08 | Rootless Database Container with Env Vars + Persistent Data | As `ray`: `podman run -d --name inventorydb -p 3308:3306 -e MYSQL_ROOT_PASSWORD=InvPass123 -v /home/ray/inventory_data:/var/lib/mysql:Z registry.redhat.io/rhel9/mariadb-1011` |
| 📅 | CON-F09 | Rootless Nginx with Custom Config + DocumentRoot Mounts | As `david`: `podman run -d --name mynginx -p 8080:80 -v /srv/nginx/html:/usr/share/nginx/html:Z -v /srv/nginx/conf:/etc/nginx/conf.d:Z docker.io/library/nginx` |
| 📅 | CON-F10 | Multi-Mount Rootless Container with Two Bind Mounts + Port | `podman run -d --name ubicon -p 8089:8089 -v /opt/out:/opt/in:Z -v /opt/send:/opt/receive:Z registry.redhat.io/ubi9/ubi sleep infinity` |
| 📅 | CON-F11 | Add Both Flathub and RHEL Flatpak Remotes | `flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo`, `flatpak remote-add --if-not-exists rhel https://flatpaks.redhat.io/rhel.flatpakrepo` |
| 📅 | CON-F12 | Install Flatpak Applications (Firefox + VLC + GIMP) | `flatpak search firefox`, `flatpak install -y flathub org.mozilla.firefox`, repeat for VLC and GIMP |
| 📅 | CON-F13 | User-Scoped vs System-Wide Flatpak Installation | Compare `flatpak install --user flathub org.mozilla.firefox` vs root `flatpak install --system` |
| 📅 | CON-F14 | Remove Flatpak Apps, Prune Runtimes, Remove Remote | `flatpak uninstall -y org.videolan.VLC org.gimp.GIMP`, `flatpak uninstall --unused -y`, `flatpak remote-delete flathub` |

---

### 🌱 Environment & Shell Configuration (Future Labs only)

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | ENV-F01 | System-Wide Environment Variable via `/etc/profile.d` | `cat > /etc/profile.d/sys_tag.sh <<'EOF' \nexport SYS_TAG="RHCSA v9 EX200 PRACTICE EXAMS COMPLETED!"\nEOF`, chmod +x, prove every new shell has the variable with `printenv SYS_TAG` |

---

## 🎯 RHCE Track (EX294)

> Sample-exam scenario labs (Sander van Vugt-style end-to-end Ansible playbooks). All entries below are 📅 Planned — they're the "build an entire control project" tier, distinct from the chapter-grained Ansible labs in the [Ansible Track](#-ansible-track-mastering-ansible-4th-ed--rhce-companion-repos) section. The Foundation labs share inventory + repo-server setup across all three sample-exam paths.

### Foundation (Common Tasks across all sample exams)

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | RHCE-F01 | Build an RHCE Ansible Control Project | `/home/ansible`, `ansible.cfg`, static inventory, groups `test/dev/prod/servers`, FQDN + short-name resolution |
| 📅 | RHCE-F02 | Bootstrap Managed Hosts with Ad-Hoc Commands | `setuphosts.sh`: install Python, create `ansible` user, write sudoers drop-in, ping module to verify |
| 📅 | RHCE-F03 | Configure a Repository Server with an Ansible Playbook | `setupreposerver.yml`: loop-mount RHEL ISO to `/var/ftp/repo`, disable firewalld, enable vsftpd with anonymous access |
| 📅 | RHCE-F04 | Configure Managed Repo Clients with Ad-Hoc Commands | Disable existing repos, add BaseOS + AppStream from `control.example.com` via `dnf config-manager` |

### Exam Practice 1 specifics

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | RHCE-F05 | HTTP Server and Client Playbooks with `site.yml` | `webserver.yml` installs httpd, `webclient.yml` installs curl, shared `vars/web.yml`, `templates/httpd.j2`, handler restarts httpd, `site.yml` ties them together |
| 📅 | RHCE-F06 | Convert HTTP Playbooks Into an Ansible Role | Refactor webserver tasks into a role with `defaults/main.yml`, `tasks/main.yml`, `templates/`, `handlers/`, then call from a new top-level play |
| 📅 | RHCE-F07 | Ansible Storage Role for `/web` with SELinux Contexts | `parted gpt mkpart 1MiB 100%`, mount `/web`, `semanage fcontext httpd_sys_content_t`, deploy `/web/index.html` with welcome message |

### Exam Practice 2 specifics

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | RHCE-F08 | Default Roles Path in `ansible.cfg` | Set `roles_path = /home/ansible/roles` while preserving system role locations as fallbacks |
| 📅 | RHCE-F09 | `setupstorage.yml` — Conditional LVM Playbook | Only on hosts with a second disk: 5GiB partition, `vgdata` with 8MiB PEs, `lvdata` 1GiB, ext3 format, `/data` persistent mount |
| 📅 | RHCE-F10 | `packagefacts.yml` — Package Version Report | Gather package facts, format kernel/bash/glibc as `packagename=version` into `/root/packages.txt` |
| 📅 | RHCE-F11 | Ansible Vault Credentials Workflow | `cloudpass.yml` with `CLOUDID` and `CLOUDPASS` encrypted, vault password file `vaultpass.txt`, `usevault.yml` reads vars and writes `/root/cloudcreds.txt` |
| 📅 | RHCE-F12 | Install Galaxy Roles from `requirements.yml` | `geerlingguy.nginx` + `geerlingguy.docker` into `/home/ansible/roles`, then `start-galaxy-roles.yml` plays both |
| 📅 | RHCE-F13 | Apache Role with Custom Template Showing HOSTNAME/IPADDRESS | Role enables httpd, opens firewall, deploys templated index.html using `ansible_facts.hostname` and `ansible_default_ipv4.address`; `runweb.yml` runs it on `test` group |
| 📅 | RHCE-F14 | Create Users from YAML Input with SHA256 Passwords | Read `users_pass.yml`; on `prod` create only users whose `department=profs`, set department as secondary group, hash passwords with `password_hash('sha512')` |

### Exam Practice 3 specifics

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | RHCE-F15 | Conditional Package Installation by Host Group | perl/php on dev/test/prod, "Virtualization Host" group on prod only, `dnf upgrade` on prod |
| 📅 | RHCE-F16 | Conditional LVM Playbook with Failure Messages | `vgdata` 2GiB only on prod; if missing print "vgprod does not exist"; if <1GiB free print "insufficient disk space available" |
| 📅 | RHCE-F17 | `sysreport.yml` — Hardware Report from a Template | Generate `hwtemplate.txt`, copy to `/root/report.txt` on each managed host, populate `NAME`, `IPADDRESS`, `TOTAL_MEMORY`, `NIC_NAME`, `SECOND_NIC_NAME=NONE` if absent |
| 📅 | RHCE-F18 | Ansible Vault Password Rotation | Create `anspass.txt` with `devpass` + `prodpass` under password `vaultpass`, then rekey to `myvaultpass` and confirm the file is still readable |
| 📅 | RHCE-F19 | RHEL Time Sync System Role (`rhel-system-roles.timesync`) | `settime.yml` uses `control.example.com` as time source with `makestep` enabled; verify `chronyc tracking`; print failure message if not synchronized |
| 📅 | RHCE-F20 | `runwebserver.yml` — Web Content with Symlink and Group Vars | Create `/webcontent/index.html` with welcome message, `USERNAME=anna` sourced from a `group_vars/prod` file, symlink `/var/www/html/index.html` to it, prove remote access |

---

## 🎯 CKA Track (Kubernetes Administrator)

### README Labs 01–16 (placeholder rows in main README)

| Status | # | Lab | Full Path |
|---|---|---|---|
| 🚧 | 01 | Explore Cluster Components | *(coming soon — see CKA Lab #01 in [README](README.md#-cluster-architecture))* |
| 🚧 | 02 | Install a Cluster with kubeadm | *(coming soon — see CKA Lab #02 in [README](README.md#-cluster-architecture))* |
| 🚧 | 03 | Deploy and Manage Pods | *(coming soon — see CKA Lab #03 in [README](README.md#-workloads))* |
| 🚧 | 04 | Create and Scale Deployments | *(coming soon — see CKA Lab #04 in [README](README.md#-workloads))* |
| 🚧 | 05 | Configure DaemonSets and Jobs | *(coming soon — see CKA Lab #05 in [README](README.md#-workloads))* |
| 🚧 | 06 | Expose Applications with Services | *(coming soon — see CKA Lab #06 in [README](README.md#-kubernetes-networking))* |
| 🚧 | 07 | Configure Ingress | *(coming soon — see CKA Lab #07 in [README](README.md#-kubernetes-networking))* |
| 🚧 | 08 | Apply NetworkPolicy | *(coming soon — see CKA Lab #08 in [README](README.md#-kubernetes-networking))* |
| 🚧 | 09 | Create PersistentVolumes and PVCs | *(coming soon — see CKA Lab #09 in [README](README.md#-kubernetes-storage))* |
| 🚧 | 10 | Configure StorageClasses | *(coming soon — see CKA Lab #10 in [README](README.md#-kubernetes-storage))* |
| 🚧 | 11 | Configure RBAC | *(coming soon — see CKA Lab #11 in [README](README.md#-kubernetes-security))* |
| 🚧 | 12 | Manage Secrets and ServiceAccounts | *(coming soon — see CKA Lab #12 in [README](README.md#-kubernetes-security))* |
| 🚧 | 13 | Upgrade a Kubernetes Cluster | *(coming soon — see CKA Lab #13 in [README](README.md#-cluster-maintenance))* |
| 🚧 | 14 | Back Up and Restore etcd | *(coming soon — see CKA Lab #14 in [README](README.md#-cluster-maintenance))* |
| 🚧 | 15 | Troubleshoot Pods and Deployments | *(coming soon — see CKA Lab #15 in [README](README.md#-kubernetes-troubleshooting))* |
| 🚧 | 16 | Troubleshoot Node and Cluster Failures | *(coming soon — see CKA Lab #16 in [README](README.md#-kubernetes-troubleshooting))* |

### Future Labs Planned (from [`future_labs.txt`](future_labs.txt))

**Cluster Architecture, Installation, Configuration**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKA-F01 | Highly Available Control Plane with kubeadm | Stacked-etcd HA topology with `kubeadm init --control-plane-endpoint`, three control planes behind a VIP/LB, `kubeadm join --control-plane` |
| 📅 | CKA-F02 | Install Cluster Components with Helm | `helm repo add`, `helm install`, `helm upgrade --atomic`, `helm rollback`, inspect `helm history` |
| 📅 | CKA-F03 | Manage Configs with Kustomize | `base/` + `overlays/dev/` + `overlays/prod/`, `kubectl apply -k`, `kustomize edit set image`, `SecretGenerator` and `ConfigMapGenerator` |
| 📅 | CKA-F04 | Container Runtime and Extension Interfaces | CRI: `crictl ps` with containerd; CNI: install Calico or Cilium and inspect `/etc/cni/net.d`; CSI: deploy a CSI driver and validate StorageClass |
| 📅 | CKA-F05 | Install and Configure an Operator with a CRD | Install Operator Lifecycle Manager or a vendor operator, define a CRD, create a custom resource, watch the controller reconcile |

**Workloads and Scheduling**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKA-F06 | Perform a Rolling Update and Rollback | `kubectl set image deployment/web app=v2`, `kubectl rollout status`, `kubectl rollout undo`, control `maxSurge`/`maxUnavailable` |
| 📅 | CKA-F07 | Configure Pods with ConfigMaps | `kubectl create configmap --from-file` and `--from-literal`, project as env vars vs volume mounts, demonstrate hot reload limits |
| 📅 | CKA-F08 | Horizontal Pod Autoscaling | Deploy metrics-server, create HPA targeting CPU, hey/wrk load generator, watch `kubectl get hpa` scale up and back down |
| 📅 | CKA-F09 | ReplicaSet Self-Healing Demonstration | Delete a pod backed by a ReplicaSet, observe recreation; cordon/drain a node and observe reschedule |
| 📅 | CKA-F10 | Resource Limits and LimitRanges | Set requests/limits on a Pod, apply a LimitRange to the namespace, watch admission rejections when exceeded |
| 📅 | CKA-F11 | Resource Quotas at Namespace Scope | ResourceQuota for cpu, memory, pods, pvcs; prove rejection of pods that exceed quota |
| 📅 | CKA-F12 | Node Affinity and Anti-Affinity Scheduling | `requiredDuringSchedulingIgnoredDuringExecution` vs preferred; labels on nodes; podAntiAffinity with `topologyKey=kubernetes.io/hostname` |
| 📅 | CKA-F13 | Taints and Tolerations | `kubectl taint node ... NoSchedule`, matching tolerations on workloads, NoExecute eviction and `tolerationSeconds` |
| 📅 | CKA-F14 | Pod Topology Spread Constraints | Spread pods across zones with `maxSkew`, `topologyKey`, `whenUnsatisfiable=DoNotSchedule` |

**Storage**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKA-F15 | Volume Access Modes and Reclaim Policies | RWO vs RWX vs ROX, `persistentVolumeReclaimPolicy` Retain vs Delete vs Recycle, demonstrate each state transition |

**Servicing and Networking**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKA-F16 | Use Gateway API for Ingress Traffic | Install Gateway API CRDs, define a GatewayClass, Gateway, and HTTPRoute, replace a classic Ingress resource |
| 📅 | CKA-F17 | Use CoreDNS for Service Discovery | Inspect kube-system coredns ConfigMap, add a custom stub-domain, validate DNS resolution from a debug pod with `nslookup` |

**Troubleshooting**

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKA-F18 | Monitor Cluster with `kubectl top` and Metrics Server | Deploy metrics-server, `kubectl top nodes`, `kubectl top pods --containers`, identify hot pods |
| 📅 | CKA-F19 | Manage Container Output Streams | `kubectl logs --previous`, `--tail`, `--since`, `-f` to follow, sidecar logging patterns |
| 📅 | CKA-F20 | Troubleshoot Services and Networking | `kubectl get endpoints`, validate Service selectors, debug from within the cluster using netshoot or busybox, trace via `iptables -t nat -L KUBE-SERVICES` |

---

## 🎯 CKAD Track (Kubernetes Application Developer)

> All entries below are 📅 Planned — sourced from the CKAD Study Guide Appendix B (all five curriculum domains).

### Application Design and Build

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKAD-DES-F01 | Build a Container Image from a Dockerfile/Containerfile | Write a Dockerfile FROM `python:3.12-slim`, COPY app.py, CMD `python app.py`; `podman build -t myapp:1.0`, push to local registry, `kubectl run myapp --image=...`, verify with `kubectl describe pod` |
| 📅 | CKAD-DES-F02 | Run a Kubernetes Job (One-Shot Batch Task) | `kind: Job` spec with `completions: 5`, `parallelism: 2`, `backoffLimit: 4`, container command runs to completion; verify with `kubectl get jobs` and `kubectl logs job/myjob` |
| 📅 | CKAD-DES-F03 | Schedule a Kubernetes CronJob | `kind: CronJob` with `schedule: "*/5 * * * *"`, jobTemplate runs `date` and echoes to stdout, prove with `kubectl get cronjob` and `kubectl get jobs --watch` |
| 📅 | CKAD-DES-F04 | Multi-Container Pod: Sidecar Logging Pattern | Main container writes to `/var/log/app.log`; sidecar `busybox` runs `tail -F /var/log/app.log`; shared emptyDir at `/var/log`; verify with `kubectl logs POD -c sidecar` |
| 📅 | CKAD-DES-F05 | Multi-Container Pod: Init Container for Pre-Start Setup | `initContainers` run `wget` to fetch a config file into a shared emptyDir; main container starts only after init succeeds; verify with `kubectl describe pod` |
| 📅 | CKAD-DES-F06 | Persistent Volume + PVC Workflow End-to-End | StorageClass-backed PV or static hostPath PV, PVC with `ReadWriteOnce` + `1Gi`; Pod consumes the claim; write a file; delete Pod; new Pod with same PVC sees the file |
| 📅 | CKAD-DES-F07 | Ephemeral Volume Shared Between Containers (emptyDir) | Pod with two containers + emptyDir volume mounted at `/shared` in both; one writes, the other reads; verify emptyDir does NOT survive Pod deletion |

### Application Deployment

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKAD-DEP-F01 | Canary Deployment with One Service + Two Deployments | Deployment v1 `replicas: 9` + label `version: v1`, Deployment v2 `replicas: 1` + label `version: v2`, Service selector matches only `app: web` so traffic splits ~90/10 |
| 📅 | CKAD-DEP-F02 | Blue-Green Deployment via Service Selector Switch | Two Deployments labelled `color: blue` and `color: green`, Service starts on `color: blue`, deploy green, smoke-test via debug Pod, `kubectl patch svc` to flip selector |
| 📅 | CKAD-DEP-F03 | Deploy an Application via Helm Chart with Custom Values | `helm repo add bitnami`, `helm install myapp bitnami/nginx --set service.type=NodePort,replicaCount=3`, prove with `helm list` + `kubectl get all -l app.kubernetes.io/instance=myapp` |

### Application Observability and Maintenance

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKAD-OBS-F01 | Configure Liveness + Readiness + Startup Probes Together | Deployment with three probe types at `/healthz`: livenessProbe httpGet, readinessProbe tcpSocket, startupProbe with `failureThreshold: 30`; break `/healthz` and watch kubelet restart |
| 📅 | CKAD-OBS-F02 | Identify Deprecated API Versions and Migrate Manifests | Run `kubectl api-resources` and `kubectl api-versions`, identify apps using removed APIs like `extensions/v1beta1`, rewrite to current `apps/v1` |
| 📅 | CKAD-OBS-F03 | Debug a Failing Pod End-to-End | `kubectl get pods` shows CrashLoopBackOff; `kubectl describe pod` for events; `kubectl logs --previous`; `kubectl exec -it POD -- sh`; ephemeral debug via `kubectl debug` for distroless |

### Application Environment, Configuration, and Security

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKAD-ENV-F01 | Define a Custom Resource Definition and a Custom Resource | `kind: CustomResourceDefinition` with group, names, versions, openAPIV3Schema validation; create a custom resource of that kind; verify with `kubectl get crd` |
| 📅 | CKAD-ENV-F02 | RBAC: Role + RoleBinding for a ServiceAccount | ServiceAccount `read-only`, Role with verbs `[get, list, watch]` on pods, RoleBinding wiring SA to Role; Pod with `serviceAccountName: read-only` can list pods but not create them via `kubectl auth can-i` |
| 📅 | CKAD-ENV-F03 | Pod Resource Requests and Limits (CPU + Memory) | `resources.requests.cpu: 100m`, `requests.memory: 128Mi`, `limits.cpu: 500m`, `limits.memory: 256Mi`; deploy a stress-test Pod that exceeds memory and watch OOMKilled event |
| 📅 | CKAD-ENV-F04 | ConfigMap Injection: env vs envFrom vs Volume Mount | One ConfigMap with three keys; demonstrate `env.valueFrom.configMapKeyRef`, `envFrom.configMapRef`, and `volumes.configMap` + `volumeMounts`; show all three patterns in one Pod manifest |
| 📅 | CKAD-ENV-F05 | Secret Patterns: Env Injection vs Mounted File | `kubectl create secret generic db --from-literal=password=s3cret`, inject via `envFrom.secretRef`, also mount at `/etc/db`; observe base64 is decoded at injection |
| 📅 | CKAD-ENV-F06 | Custom ServiceAccount with Pod Binding | `kubectl create sa myapp-sa`, `kubectl create token myapp-sa`, Pod spec with `serviceAccountName: myapp-sa`, verify projected token works against the API |
| 📅 | CKAD-ENV-F07 | SecurityContext: runAsUser, fsGroup, Capabilities, ROFS | Pod-level securityContext with `runAsUser: 1000`, `runAsGroup: 1000`, `fsGroup: 2000`, `readOnlyRootFilesystem: true`, `capabilities.drop: ["ALL"]`, `capabilities.add: ["NET_BIND_SERVICE"]` |

### Services and Networking

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKAD-NET-F01 | NetworkPolicy: Default-Deny + Allow Specific Ingress | NetworkPolicy with `podSelector: {}` + `policyTypes: [Ingress]` blocks ALL ingress; second NetworkPolicy allows ingress from pods with `role: frontend`; verify with `kubectl exec` and `curl` |
| 📅 | CKAD-NET-F02 | Service Types: ClusterIP vs NodePort vs LoadBalancer vs ExternalName | Deploy same backend, expose via four Service types in turn, verify reachability for each |
| 📅 | CKAD-NET-F03 | Ingress with Path-Based Routing and TLS Termination | Deploy NGINX Ingress Controller or Traefik, Ingress with two backends `/api → backend1`, `/web → backend2`, provision self-signed cert + Secret `kubernetes.io/tls`, attach via `spec.tls` |

---

## 🎯 Ansible Track (Mastering Ansible 4th Ed. + RHCE Companion Repos)

> Two layers stacked here:
> 1. **Currently Built — RHCE Ansible Companion Repos** (15 standalone repos that already exist; numbering matches the main [README](README.md#-rhce-ex294-labs))
> 2. **Future Labs Planned — Mastering Ansible 4th Edition** (73 labs across chapters 1, 2, 7, 8, 13, sourced from [`future_labs.txt`](future_labs.txt))
>
> For the scenario-based RHCE labs (build the whole control project, run sample-exam playbooks end-to-end), see the [RHCE Track (EX294)](#-rhce-track-ex294) section above.

### Currently Built — RHCE Ansible Companion Repos

| Status | # / Ch | Lab | Full Path |
|---|---|---|---|
| ✅ | 01 / Ch 1 | Ansible Architecture & Inventory | <https://github.com/kelvintechnical/ansible-architecture-and-inventory> |
| ✅ | 02 / Ch 2 | Ansible Collections & Migration | <https://github.com/kelvintechnical/ansible-collections-and-migration> |
| ✅ | 03 / Ch 7 | Task Conditions, Blocks & Loops | <https://github.com/kelvintechnical/ansible-task-conditions-loops> |
| 🚧 | 04 | Write Your First Playbook | *(coming soon — see RHCE Lab #04 in [README](README.md#-ansible-playbooks))* |
| ✅ | 05 / Ch 8 | Ansible Roles | <https://github.com/kelvintechnical/ansible-roles> |
| 🚧 | 06 | Use Roles from Ansible Galaxy | *(coming soon — see RHCE Lab #06 in [README](README.md#-ansible-roles))* |
| ✅ | 07 / Ch 6 | Jinja2 Templates in Ansible | <https://github.com/kelvintechnical/ansible-jinja2-templates> |
| ✅ | 08 / Ch 3 | Ansible Vault — Secrets at Rest | <https://github.com/kelvintechnical/ansible-vault-secrets> |
| ✅ | 09 / Ch 9 | Troubleshooting Ansible | <https://github.com/kelvintechnical/ansible-troubleshooting> |
| ✅ | 10 / Ch 4 | Windows Automation | <https://github.com/kelvintechnical/ansible-windows-automation> |
| ✅ | 11 / Ch 5 | AWX / Tower | <https://github.com/kelvintechnical/ansible-awx-tower> |
| ✅ | 12 / Ch 10 | Extending Ansible with Modules and Plugins | <https://github.com/kelvintechnical/ansible-extending-modules-plugins> |
| ✅ | 13 / Ch 11 | Rolling Deployments | <https://github.com/kelvintechnical/ansible-rolling-deployments> |
| ✅ | 14 / Ch 12 | Infrastructure Provisioning | <https://github.com/kelvintechnical/ansible-infrastructure-provisioning> |
| ✅ | 15 / Ch 13 | Network Automation | <https://github.com/kelvintechnical/ansible-network-automation> |

### Future Labs Planned — Mastering Ansible, 4th Edition

#### 🗂 Ch 1 — System Architecture & Design (25 labs)

**Inventory Architecture**

| Status | ID | Lab |
|---|---|---|
| 📅 | ANS-CH1-F01 | Static INI Inventory with Groups, Children, and Group-Vars |
| 📅 | ANS-CH1-F02 | Behavioral Inventory Variables Cheat-Sheet Playbook |
| 📅 | ANS-CH1-F03 | Inventory Ordering: inventory / reverse_inventory / sorted / reverse_sorted / shuffle |
| 📅 | ANS-CH1-F04 | AWS EC2 Dynamic Inventory Plugin Bring-Up |
| 📅 | ANS-CH1-F05 | Runtime Inventory Additions with `ansible.builtin.add_host` |
| 📅 | ANS-CH1-F06 | Inventory Limiting with `--limit` + Cross-Host hostvars Access |
| 📅 | ANS-CH1-F07 | YAML vs INI Inventory Equivalence Audit |
| 📅 | ANS-CH1-F08 | Static + Dynamic Inventory Combined (Directory-Based Inventory) |

**Playbook Parsing & Execution Order**

| Status | ID | Lab |
|---|---|---|
| 📅 | ANS-CH1-F09 | Strict Play Order: pre_tasks → roles → tasks → post_tasks → handlers |
| 📅 | ANS-CH1-F10 | Handler Flushing with `meta: flush_handlers` |
| 📅 | ANS-CH1-F11 | Relative Path Resolution for vars_files and include |
| 📅 | ANS-CH1-F12 | Linear vs Free vs Debug Execution Strategies |
| 📅 | ANS-CH1-F13 | Host Pattern Selection: groups, wildcards, regex, &, ! |
| 📅 | ANS-CH1-F14 | Play and Task Names with Variables — When Templating Works |

**Variable Precedence & Magic Variables**

| Status | ID | Lab |
|---|---|---|
| 📅 | ANS-CH1-F15 | Variable Precedence Pyramid: prove all 21 levels |
| 📅 | ANS-CH1-F16 | Magic Variables Tour: inventory_hostname / group_names / hostvars / play_hosts / ansible_play_batch |
| 📅 | ANS-CH1-F17 | `ansible_group_priority` for Conflict Resolution |
| 📅 | ANS-CH1-F18 | Hash Merge vs Replace via `hash_behavior` |
| 📅 | ANS-CH1-F19 | Lookup Plugins: file / env / pipe / password / dnstxt |
| 📅 | ANS-CH1-F20 | vars_prompt for Interactive Variable Capture |

**Module Transport, Performance & Safety**

| Status | ID | Lab |
|---|---|---|
| 📅 | ANS-CH1-F21 | SSH ControlPersist + Pipelining Performance Benchmark |
| 📅 | ANS-CH1-F22 | Ansible Forks Tuning |
| 📅 | ANS-CH1-F23 | Module Discovery Path Order (role library → playbook library → ANSIBLE_LIBRARY → /usr/share/ansible) |
| 📅 | ANS-CH1-F24 | Module Blacklisting with plugin_filters.yml |
| 📅 | ANS-CH1-F25 | Module Argument Formats: free-form vs key=value vs YAML hash |

#### 📦 Ch 2 — Migration / Collections / FQCNs (11 labs)

| Status | ID | Lab |
|---|---|---|
| 📅 | ANS-CH2-F01 | Clean Reinstall: Remove Ansible 2.9 / 3.x, Install Ansible 4.3 |
| 📅 | ANS-CH2-F02 | Pip + virtualenv: Two Side-by-Side Ansible Versions |
| 📅 | ANS-CH2-F03 | Build Your First Custom Collection (`masterybook.demo`) |
| 📅 | ANS-CH2-F04 | Install Your Custom Collection Locally via `collections_paths` |
| 📅 | ANS-CH2-F05 | FQCN vs Short Module Names — Shadowing Demo |
| 📅 | ANS-CH2-F06 | Collection Installation from Git URL |
| 📅 | ANS-CH2-F07 | Bulk Collection Install via requirements.yml |
| 📅 | ANS-CH2-F08 | Semantic Versioning Walk-Through for Ansible Packages |
| 📅 | ANS-CH2-F09 | Discover All Modules in a Collection via `ansible-doc -l` |
| 📅 | ANS-CH2-F10 | Force-Install a Pre-Release / Dev Collection Version |
| 📅 | ANS-CH2-F11 | Publish a Collection to Ansible Galaxy |

#### 🎛 Ch 7 — Task Conditions, Error Recovery, Loops (12 labs)

| Status | ID | Lab |
|---|---|---|
| 📅 | ANS-CH7-F01 | `ignore_errors: true` on a Deliberately-Failing URI Task |
| 📅 | ANS-CH7-F02 | `failed_when` for iscsiadm Exit Code Tolerance |
| 📅 | ANS-CH7-F03 | Multi-Condition `failed_when` as YAML List (Git Branch Delete) |
| 📅 | ANS-CH7-F04 | `changed_when` to Suppress False-Positive Changes |
| 📅 | ANS-CH7-F05 | `creates` / `removes` for Command-Family Idempotency |
| 📅 | ANS-CH7-F06 | Pure Data-Gathering Tasks with `changed_when: false` |
| 📅 | ANS-CH7-F07 | `block` + `rescue` for Graceful Cleanup |
| 📅 | ANS-CH7-F08 | `block` + `rescue` + `always` (Three-Section Block) |
| 📅 | ANS-CH7-F09 | `ignore_unreachable: true` Against an Inventory of Dead Hosts |
| 📅 | ANS-CH7-F10 | Modern `loop:` vs Legacy `with_items:` Equivalence |
| 📅 | ANS-CH7-F11 | `until` / `retries` / `delay` Loop Waiting for /tmp/flag |
| 📅 | ANS-CH7-F12 | Nested Loops with `product` Filter and `loop_control.loop_var` |

#### 🧱 Ch 8 — Roles, Includes & ansible-galaxy (15 labs)

| Status | ID | Lab |
|---|---|---|
| 📅 | ANS-CH8-F01 | Basic Task Inclusion with `ansible.builtin.include` |
| 📅 | ANS-CH8-F02 | Passing Variables Inline to Included Tasks |
| 📅 | ANS-CH8-F03 | Passing Complex Hash Data to Included Tasks via dict2items |
| 📅 | ANS-CH8-F04 | Conditional Include with `when: item \| bool` |
| 📅 | ANS-CH8-F05 | Tagged Task Includes for Selective Execution |
| 📅 | ANS-CH8-F06 | Looping Over a Task Include with `loop_control: loop_var` |
| 📅 | ANS-CH8-F07 | Handler Inclusion with `when` on the Include Statement |
| 📅 | ANS-CH8-F08 | `vars_files` Static Inclusion vs `include_vars` Dynamic Inclusion |
| 📅 | ANS-CH8-F09 | `include_vars` with `with_first_found` for OS-Specific Vars |
| 📅 | ANS-CH8-F10 | Loading Extra Vars from a File via `-e @file.yaml` |
| 📅 | ANS-CH8-F11 | `import_playbook` for Composing Multi-Playbook Workflows |
| 📅 | ANS-CH8-F12 | Build a Role From Scratch with `ansible-galaxy role init` |
| 📅 | ANS-CH8-F13 | Role Dependencies with Variables + Tags + Conditionals |
| 📅 | ANS-CH8-F14 | pre_tasks / roles / tasks / post_tasks Handler-Flush Ordering |
| 📅 | ANS-CH8-F15 | Install Roles from Ansible Galaxy + Git + tarball + requirements.yml |

#### 🌐 Ch 13 — Network Automation (10 labs)

| Status | ID | Lab |
|---|---|---|
| 📅 | ANS-CH13-F01 | Choosing the Right Connection Protocol: local vs network_cli vs netconf vs httpapi |
| 📅 | ANS-CH13-F02 | Inventory for Cisco IOS via `ansible.netcommon.network_cli` |
| 📅 | ANS-CH13-F03 | Save Running Config on Cisco IOS with `cisco.ios.ios_config` |
| 📅 | ANS-CH13-F04 | Bring Up an Arista vEOS Switch from Zero |
| 📅 | ANS-CH13-F05 | Configure Arista EOS Interfaces with `arista.eos.eos_interfaces` |
| 📅 | ANS-CH13-F06 | Configure Cumulus Linux Layer-2 Bridge with `community.network.nclu` |
| 📅 | ANS-CH13-F07 | Multi-Vendor Inventory with `[switches:children]` Grouping |
| 📅 | ANS-CH13-F08 | Conditional Fact-Gathering for Different Network OSes |
| 📅 | ANS-CH13-F09 | Jump Host / Bastion via `ansible_ssh_common_args` ProxyCommand |
| 📅 | ANS-CH13-F10 | Raw-Command Fallback for Unsupported Devices via `ansible.builtin.raw` |

---

## 📈 Summary by Category

### RHCSA EX200 (356 labs)

> README columns count only the labs visible in the main [README](README.md) (companion-repo URLs + `*(coming soon)*` placeholders). **In-Repo** counts labs that live in [`labs/<slug>/`](labs/). **Future** counts labs from [`future_labs.txt`](future_labs.txt) that have a `*-F##` ID but no page yet.

| Category | ✅ README | 🚧 README | In-Repo | 📅 Future | Total |
|---|---:|---:|---:|---:|---:|
| Shells, Terminals & Redirection (01–04) | 4 | 0 | 0 | 0 | 4 |
| Essential Tools & File Operations (05–18) | 14 | 0 | 1 | 7 | 22 |
| Text File Management (19–27) | 9 | 0 | 0 | 3 | 12 |
| Documentation Tools (28–30) | 3 | 0 | 0 | 1 | 4 |
| Networking (31–39) | 9 | 0 | 0 | 5 | 14 |
| Permissions, Special Bits & ACLs (40–54) | 15 | 0 | 0 | 6 | 21 |
| Firewall (firewalld) (55–67) | 13 | 0 | 0 | 2 | 15 |
| TCP Wrappers & PAM (68–77) | 10 | 0 | 0 | 0 | 10 |
| SELinux (78–84) | 7 | 0 | 1 | 5 | 13 |
| Boot Process & GRUB (85–89) | 5 | 0 | 0 | 1 | 6 |
| Systemd & Services (90–99) | 10 | 0 | 0 | 1 | 11 |
| Log Management (100–106) | 1 | 6 | 0 | 0 | 7 |
| System Time & Locale (107–109) | 2 | 1 | 0 | 2 | 5 |
| Storage Management (110–120) | 0 | 11 | 2 | 2 | 15 |
| LVM (121–130) | 1 | 9 | 2 | 8 | 20 |
| Filesystem Mounts (NFS/AutoFS) (131–136) | 0 | 6 | 0 | 6 | 12 |
| Package Management & Repositories (137–161) | 3 | 22 | 1 | 2 | 28 |
| User & Group Management (162–183) | 2 | 20 | 1 | 8 | 31 |
| Sudo & Privilege | 0 | 0 | 0 | 3 | 3 |
| Process Management (184–192) | 0 | 9 | 0 | 4 | 13 |
| Archives & Compression (193–198) | 3 | 3 | 0 | 3 | 9 |
| Scheduled Tasks (199–207) | 1 | 9 | 1 | 6 | 17 |
| GPG Encryption (208–211) | 0 | 4 | 0 | 0 | 4 |
| Remote Administration & SSH (212–215) | 2 | 2 | 0 | 6 | 10 |
| Security Administration (216–220) | 0 | 5 | 0 | 0 | 5 |
| Web Services (Apache) (221–224) | 1 | 3 | 0 | 5 | 9 |
| System Performance & Tuning (225) | 1 | 0 | 0 | 2 | 3 |
| Shell Scripting & Automation (226–227) | 1 | 1 | 1 | 8 | 11 |
| Containers & Flatpak (LAB row) | 1 | 0 | 1 | 13 | 15 |
| Environment & Shell Configuration | 0 | 0 | 0 | 1 | 1 |
| **Total** | **118** | **111** | **13** | **121** | **356**\* |

> \* Note: in-repo labs that are *also* listed as a "LAB" row in the README (3 labs: `lvm-create-lvol1-ext4`, `scheduling-jobs-systemd-timer`, plus the Container LAB row pointing to an external repo) are counted in the In-Repo column to avoid double-counting against the README columns; the README "LAB" row count is separately ✅ when its companion repo exists.

### RHCE EX294 (20 labs)

| Section | 📅 Planned |
|---|---:|
| Foundation (common tasks) | 4 |
| Exam Practice 1 | 3 |
| Exam Practice 2 | 7 |
| Exam Practice 3 | 6 |

### CKA (36 labs)

| Section | 🚧 README | 📅 Future | Total |
|---|---:|---:|---:|
| Cluster Architecture | 2 | 5 | 7 |
| Workloads & Scheduling | 3 | 9 | 12 |
| Networking | 3 | 2 | 5 |
| Storage | 2 | 1 | 3 |
| Security | 2 | 0 | 2 |
| Cluster Maintenance | 2 | 0 | 2 |
| Troubleshooting | 2 | 3 | 5 |

### CKAD (22 labs)

| Section | 📅 Planned |
|---|---:|
| Application Design & Build | 7 |
| Application Deployment | 3 |
| Observability & Maintenance | 3 |
| Environment, Config & Security | 7 |
| Services & Networking | 3 |

### Ansible (88 labs)

| Section | ✅ Done | 🚧 README | 📅 Future | Total |
|---|---:|---:|---:|---:|
| RHCE README Companion Repos | 13 | 2 | 0 | 15 |
| Mastering Ansible Ch 1 — System Architecture & Design | 0 | 0 | 25 | 25 |
| Mastering Ansible Ch 2 — Migration / Collections / FQCNs | 0 | 0 | 11 | 11 |
| Mastering Ansible Ch 7 — Task Conditions, Loops, Rescue | 0 | 0 | 12 | 12 |
| Mastering Ansible Ch 8 — Roles, Includes, ansible-galaxy | 0 | 0 | 15 | 15 |
| Mastering Ansible Ch 13 — Network Automation | 0 | 0 | 10 | 10 |

---

## 🔄 How This Maps Back to the README

The main [README](README.md) is organized by RHCSA EX200 exam objective with globally numbered labs (01, 02, 03...). This roadmap takes the same content and adds four things the README intentionally omits:

1. **Status visibility** — ✅/🚧/📅 lets a visitor see at a glance what's built vs planned, without scrolling.
2. **Full paths to every lab** — companion-repo URLs are written out in plain text, in-repo `labs/<slug>/` paths are linked, and "coming soon" placeholders point back to the specific README section by lab number so you can always find the source.
3. **Future-lab prefixes** — `LVM-F##`, `NET-F##`, `ANS-CH1-F##`, etc. are stable identifiers that survive renumbering when labs get built and slotted into the main README's global sequence.
4. **The non-RHCSA tracks** — the README is RHCSA-first; this roadmap surfaces the parallel RHCE / CKA / CKAD / Ansible curricula so the whole multi-cert arc is visible in one place.

When a 📅 lab becomes a real lab in [`labs/<slug>/`](labs/), its row in this roadmap is updated to 🚧 (placeholder shipped) or ✅ (full content shipped), and a new row gets added to the main [README](README.md) with the next free global number (e.g. `228`, `229`...).

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
