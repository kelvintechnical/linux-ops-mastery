# 🗺️ Roadmap — linux-ops-mastery

> The full curriculum. Every lab that exists, is in progress, or is planned — organized by certification track and exam objective, **with the full path to every lab** so you can jump straight from this page to whatever you want to work on next.
>
> Looking for the day-one starting point? See the **[Suggested Learning Path](README.md#-suggested-learning-path)** in the main README. Looking for what's already built? Jump to **[Currently Built](#-currently-built)** below.

---

## 📊 Counts at a Glance

Every lab in this roadmap is currently marked **not completed**. The entire curriculum is being rebuilt using the ADHD-friendly lab methodology — no previously shipped work is being treated as complete until it is re-authored under the new format. Order matches the curriculum flow: **RHCSA → RHCE → CKA → CKAD → Ansible**.

| Track | Not Completed | Total |
|---|---:|---:|
| RHCSA EX200 | 356 | 356 |
| RHCE EX294 (sample-exam scenarios) | 20 | 20 |
| CKA (Kubernetes Administrator) | 36 | 36 |
| CKAD (Kubernetes App Developer) | 22 | 22 |
| Ansible (Mastering Ansible 4th Ed. + RHCE companion repos) | 88 | 88 |
| **Total** | **522** | **522** |

> **About these counts.** Every row counts every lab visible across this repo — the in-repo labs in [`labs/`](labs/), the external companion repos linked from the main [README](README.md), **and** every future lab listed in [`future_labs.txt`](future_labs.txt). All 522 are being re-authored under the ADHD-method format.

---

## 🔑 Status Legend

| Status | Meaning |
|---|---|
| `not completed` | This lab is part of the ADHD-method revamp. No previously shipped content is being treated as complete until the lab is re-authored under the new format. |

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

The **13** labs with full or placeholder content in **this** repository today (under [`labs/`](labs/)), plus links straight to the file. External companion repos linked from the main [README](README.md) are listed by track below.

| Status | Lab | Location |
|---|---|---|
| not completed | Create LV `lvol1` (ext4, 280 MB) and Mount Persistently | [`labs/lvm-create-lvol1-ext4/`](labs/lvm-create-lvol1-ext4/) |
| not completed | Create LV with XFS Filesystem | [`labs/lvm-create-lv1-xfs/`](labs/lvm-create-lv1-xfs/) |
| not completed | Scheduling Jobs with systemd Timers | [`labs/scheduling-jobs-systemd-timer/`](labs/scheduling-jobs-systemd-timer/) |
| not completed | Find Files by Modification Time and Act on Them | [`labs/find-files-by-mtime/`](labs/find-files-by-mtime/) |
| not completed | Lock User Account and Capture Regex Evidence | [`labs/user-lock-capture-regex/`](labs/user-lock-capture-regex/) |
| not completed | Online Extend an LV and Its Filesystem Without Unmounting | [`labs/lvm-online-extend-xfs/`](labs/lvm-online-extend-xfs/) |
| not completed | Create a Swap Partition by UUID | [`labs/storage-swap-partition-uuid/`](labs/storage-swap-partition-uuid/) |
| not completed | Create an Ext4 Partition Mounted by LABEL | [`labs/storage-ext4-partition-label/`](labs/storage-ext4-partition-label/) |
| not completed | Apply Recursive SELinux Contexts to a New Directory | [`labs/selinux-recursive-contexts-direct01/`](labs/selinux-recursive-contexts-direct01/) |
| not completed | User-Level Cron Job with `find -exec` | [`labs/cron-user-find-exec-coredir/`](labs/cron-user-find-exec-coredir/) |
| not completed | Install Development Tools Package Group with Output Capture | [`labs/dnf-install-dev-tools-capture/`](labs/dnf-install-dev-tools-capture/) |
| not completed | Bidirectional Bash Script with Argument Logic | [`labs/bash-bidirectional-arg-script/`](labs/bash-bidirectional-arg-script/) |
| not completed | Rootless Container with Bind Mount and systemd Auto-Start | [`labs/podman-rootless-bind-mount-systemd/`](labs/podman-rootless-bind-mount-systemd/) |

---

## 🎯 RHCSA Track (EX200)

The RHCSA curriculum has three buckets:

1. **External companion repos** — the 227+ numbered labs in the main [README](README.md). Each row below links straight to the repo. Where a row reads `*(coming soon — see Lab #NN in README)*`, the lab number is scoped in the main README but no companion repo exists yet.
2. **In-repo labs** under [`labs/`](labs/) — listed inline in the relevant section.
3. **Future planned labs** — the `*-F##`-tagged entries from [`future_labs.txt`](future_labs.txt), grouped by category.

### 📋 Complete Labs in This Order

Foundation → advanced. Each step locks in prerequisites for the next. Mirrors the [Suggested Learning Path](README.md#-suggested-learning-path) in the main README and folds the `*-F##` future labs into the matching module. Every lab listed below — built, in-progress, or planned — appears in the exact order you should work through it.

> **Exam-prep order?** Jump to **[Complete Labs by RHCSA v10 Objective (EX200)](#-complete-labs-by-rhcsa-v10-objective-ex200)** below — every RHCSA lab grouped under official objectives **1 → 10** in the order Red Hat publishes them for EX200.
>
> **About this order:** within each module, labs are sequenced foundation → advanced. Across modules, prerequisites flow forward — you can't fully grok LVM (Step 6) until you have `find`/`grep` from Step 1, and you can't do SELinux (Step 4) until you've configured standard permissions in Step 3. **Skip at your own risk.**

#### Step 1: Shells & Text Fluency

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 1 | not completed | 01 | Standard Output Redirection | `>`, `>>`, `cat` — direct stdout into a new file or append |
| 2 | not completed | 02 | Standard Error Redirection | `2>`, `2>/dev/null` — capture or discard the error stream |
| 3 | not completed | 03 | Pipe Text Streams | `\|`, `less`, `grep`, `tee`, `wc -l` — chain commands stdout→stdin |
| 4 | not completed | 04 | Capture Both Output and Error | `&>`, `2>&1` — combine stdout + stderr into one stream |
| 5 | not completed | 05 | Directory Navigation | `cd`, `pwd`, `ls` — absolute paths, `..`, `~` |
| 6 | not completed | 06 | Listing Files and SELinux Contexts | `ls -l`, `ls -Z` — long listings + SELinux contexts |
| 7 | not completed | 07 | Creating Empty Files and Timestamps | `touch` — create files, update mtime |
| 8 | not completed | 08 | Copying Files and Directories | `cp`, `cp -R`, `cp -a` — copy files + trees, preserve attrs |
| 9 | not completed | 09 | Hard and Soft Links | `ln`, `ln -s` — inode link vs symlink |
| 10 | not completed | 10 | Moving and Renaming Files | `mv` — rename locally + move across dirs |
| 11 | not completed | 11 | Safe Deletion of Files and Directories | `rm`, `rmdir`, `rm -rf` — delete files + trees |
| 12 | not completed | 12 | Creating Nested Directories | `mkdir -p` — make full directory paths in one shot |
| 13 | not completed | 13 | Creating Command Aliases | `alias` — map custom shortcuts, override defaults |
| 14 | not completed | 14 | File Searching with find | `find` — search by name from any directory |
| 15 | not completed | 15 | Instant File Searching with locate | `locate`, `updatedb` — fast indexed lookups |
| 16 | not completed | 16 | Search for a String and Save Output | [16a RHCSA](lab-16a-grep-search-save-output-rhcsa/) · [16b Ansible](lab-16b-grep-search-save-output-ansible/) · [16c Verify](lab-16c-grep-search-save-output-verify/) — `grep`, `tee`, `>` |
| 17 | not completed | 17 | Find and Save Config Files | [17a RHCSA](lab-17a-find-save-config-files-rhcsa/) · [17b Ansible](lab-17b-find-save-config-files-ansible/) · [17c Verify](lab-17c-find-save-config-files-verify/) — `find -type f -name -user`, `2>/dev/null` |
| 18 | not completed | 18 | Locate Command Documentation | [18a RHCSA](lab-18a-locate-command-docs-rhcsa/) · [18b Ansible](lab-18b-locate-command-docs-ansible/) · [18c Verify](lab-18c-locate-command-docs-verify/) — `find /usr/share/doc`, `rpm -qf`, `rpm -qd` |
| 19 | not completed | in-repo | Find Files by Modification Time and Act on Them | `find / -mtime -30`, `-exec`, `tar --files-from` — mtime predicates |
| 20 | not completed | 19 | Concatenating Files with cat | [19a RHCSA](lab-19a-cat-concatenate-files-rhcsa/) · [19b Ansible](lab-19b-cat-concatenate-files-ansible/) · [19c Verify](lab-19c-cat-concatenate-files-verify/) — `cat` |
| 21 | not completed | 20 | Scrolling Through Large Files | [20a RHCSA](lab-20a-less-more-scrolling-rhcsa/) · [20b Ansible](lab-20b-less-more-scrolling-ansible/) · [20c Verify](lab-20c-less-more-scrolling-verify/) — `less`, `more`, `/` + `?` search |
| 22 | not completed | 21 | Monitoring Live Log Files | [21a RHCSA](lab-21a-tail-f-live-logs-rhcsa/) · [21b Ansible](lab-21b-tail-f-live-logs-ansible/) · [21c Verify](lab-21c-tail-f-live-logs-verify/) — `tail -f` |
| 23 | not completed | 22 | Filtering Text with grep and Regex | [22a RHCSA](lab-22a-grep-regex-rhcsa/) · [22b Ansible](lab-22b-grep-regex-ansible/) · [22c Verify](lab-22c-grep-regex-verify/) — `grep`, regex inside config files |
| 24 | not completed | 23 | Comparing File Differences with diff | [23a RHCSA](lab-23a-diff-comparing-files-rhcsa/) · [23b Ansible](lab-23b-diff-comparing-files-ansible/) · [23c Verify](lab-23c-diff-comparing-files-verify/) — `diff` |
| 25 | not completed | 24 | Stream Editing with sed | [24a RHCSA](lab-24a-sed-stream-editor-rhcsa/) · [24b Ansible](lab-24b-sed-stream-editor-ansible/) · [24c Verify](lab-24c-sed-stream-editor-verify/) — `sed` |
| 26 | not completed | 25 | Extracting Columns with awk | [25a RHCSA](lab-25a-awk-columns-rhcsa/) · [25b Ansible](lab-25b-awk-columns-ansible/) · [25c Verify](lab-25c-awk-columns-verify/) — `awk` |
| 27 | not completed | 26 | Command Mode and Insert Mode in vi | [26a RHCSA](lab-26a-vi-editor-rhcsa/) · [26b Ansible](lab-26b-vi-editor-ansible/) · [26c Verify](lab-26c-vi-editor-verify/) — `vi`, `:wq` |
| 28 | not completed | 27 | Safely Editing System Databases | [27a RHCSA](lab-27a-vipw-vigr-safe-editing-rhcsa/) · [27b Ansible](lab-27b-vipw-vigr-safe-editing-ansible/) · [27c Verify](lab-27c-vipw-vigr-safe-editing-verify/) — `vipw`, `vigr` |
| 29 | not completed | FILES-F01 | Find Files by Size Range and Copy Preserving All Attributes | `find /etc -size +5M -size -10M -exec cp --preserve=all` |
| 30 | not completed | FILES-F02 | Find Files Owned by a User Within a Size Range | `find / -xdev -user linda -size +3M -size -50M 2>/dev/null` |
| 31 | not completed | FILES-F03 | Find Configuration Files by Name and Owner | `find /etc -name '*.conf' -user root > /root/config_files` |
| 32 | not completed | FILES-F04 | Find Files Modified More Than 30 Days Ago and Copy with Hierarchy | `find /etc -mtime +30 -exec cp --parents --preserve=all` |
| 33 | not completed | FILES-F05 | Find Directories with the SUID Bit Set + Copy with Attributes | `find / -type d -perm -4000 2>/dev/null -exec cp -a` |
| 34 | not completed | FILES-F06 | Find Directories by Size Range and Save Long Listing | `find -type d -size +50k -size -100k \| xargs ls -ld` |
| 35 | not completed | FILES-F07 | Hard and Symbolic Link Lifecycle Demonstration | `ln`, `ln -s`, delete original, observe dangling symlink |
| 36 | not completed | TEXT-F01 | Extract Lines Containing a String Preserving Order | `grep 'bin' /etc/passwd > /root/bin_lines` |
| 37 | not completed | TEXT-F02 | Find Exact Word Matches with `grep -w` | `grep -wE 'bin'` — prevents `sbin`/`binary` matches |
| 38 | not completed | TEXT-F03 | Search Apache Configuration for Listen Directives | `grep '^Listen' /etc/httpd/conf/httpd.conf` |

#### Step 2: Documentation & Networking

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 1 | not completed | 28 | Exploring Manual Pages | [28a RHCSA](lab-28a-man-pages-rhcsa/) · [28b Ansible](lab-28b-man-pages-ansible/) · [28c Verify](lab-28c-man-pages-verify/) — `man` |
| 2 | not completed | 29 | Searching Manuals by Keyword | [29a RHCSA](lab-29a-apropos-whatis-rhcsa/) · [29b Ansible](lab-29b-apropos-whatis-ansible/) · [29c Verify](lab-29c-apropos-whatis-verify/) — `whatis`, `apropos` |
| 3 | not completed | 30 | Navigating info Pages | [30a RHCSA](lab-30a-info-pages-rhcsa/) · [30b Ansible](lab-30b-info-pages-ansible/) · [30c Verify](lab-30c-info-pages-verify/) — `info` |
| 4 | not completed | DOC-F01 | Locate Command Documentation Under `/usr/share/doc` | `find /usr/share/doc -iname '*passwd*'`, `rpm -qf` owner |
| 5 | not completed | 31 | Configure a Static IP Address | [31a RHCSA](lab-31a-static-ip-nmcli-rhcsa/) · [31b Ansible](lab-31b-static-ip-nmcli-ansible/) · [31c Verify](lab-31c-static-ip-nmcli-verify/) — `nmcli con mod`, `ip addr`, `ip route` |
| 6 | not completed | 32 | Check Network Connectivity | [32a RHCSA](lab-32a-ping-traceroute-rhcsa/) · [32b Ansible](lab-32b-ping-traceroute-ansible/) · [32c Verify](lab-32c-ping-traceroute-verify/) — `ping`, `traceroute` |
| 7 | not completed | 33 | Display IP and Routing Info | [33a RHCSA](lab-33a-ip-addr-route-show-rhcsa/) · [33b Ansible](lab-33b-ip-addr-route-show-ansible/) · [33c Verify](lab-33c-ip-addr-route-show-verify/) — `ip addr show`, `ip route show` |
| 8 | not completed | 34 | Inspecting Listening Sockets | [34a RHCSA](lab-34a-ss-listening-sockets-rhcsa/) · [34b Ansible](lab-34b-ss-listening-sockets-ansible/) · [34c Verify](lab-34c-ss-listening-sockets-verify/) — `ss -tuna4` |
| 9 | not completed | 35 | Text-Based Network Config nmtui | [35a RHCSA](lab-35a-nmtui-tui-config-rhcsa/) · [35b Ansible](lab-35b-nmtui-tui-config-ansible/) · [35c Verify](lab-35c-nmtui-tui-config-verify/) — `nmtui` |
| 10 | not completed | 36 | Command-Line Network Config nmcli | [36a RHCSA](lab-36a-nmcli-cli-config-rhcsa/) · [36b Ansible](lab-36b-nmcli-cli-config-ansible/) · [36c Verify](lab-36c-nmcli-cli-config-verify/) — `nmcli` |
| 11 | not completed | 37 | Configuring Local Host Resolution | [37a RHCSA](lab-37a-etc-hosts-resolution-rhcsa/) · [37b Ansible](lab-37b-etc-hosts-resolution-ansible/) · [37c Verify](lab-37c-etc-hosts-resolution-verify/) — `/etc/hosts` |
| 12 | not completed | 38 | Configuring DNS Servers | [38a RHCSA](lab-38a-resolv-conf-dns-rhcsa/) · [38b Ansible](lab-38b-resolv-conf-dns-ansible/) · [38c Verify](lab-38c-resolv-conf-dns-verify/) — `/etc/resolv.conf` |
| 13 | not completed | 39 | Configure SSH and Key-Based Auth | [39a RHCSA](lab-39a-ssh-key-auth-rhcsa/) · [39b Ansible](lab-39b-ssh-key-auth-ansible/) · [39c Verify](lab-39c-ssh-key-auth-verify/) — `ssh-keygen`, `ssh-copy-id` |
| 14 | not completed | NET-F01 | Manual Hostname Configuration by Editing `/etc/hostname` | Write FQDN to `/etc/hostname`, no `hostnamectl`, persist on reboot |
| 15 | not completed | NET-F02 | Manual Network Configuration by Editing Connection Files | Hand-edit `/etc/NetworkManager/system-connections/`, `nmcli connection reload` |
| 16 | not completed | NET-F03 | Configure Static IPv4 with Specific Host Address | `nmcli con mod ipv4.addresses/gateway/dns/method manual`, `autoconnect yes` |
| 17 | not completed | NET-F04 | Configure Static IPv6 Address with DNS Search Domain | `ipv6.addresses fd02::42/64`, `ipv6.gateway`, `ipv6.dns-search example.local` |
| 18 | not completed | NET-F05 | Dual-Stack IPv4 + IPv6 with Local Host Resolution | Both `192.168.56.25/24` + `fd12:3456:789a:1::25/64`, `/etc/hosts` short + FQDN |

#### Step 3: Permissions, ACLs, Firewall

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 1 | not completed | 40 | Standard File Permissions | [40a RHCSA](lab-40a-chmod-standard-perms-rhcsa/) · [40b Ansible](lab-40b-chmod-standard-perms-ansible/) · [40c Verify](lab-40c-chmod-standard-perms-verify/) — `chmod` |
| 2 | not completed | 41 | Changing Ownership | [41a RHCSA](lab-41a-chown-chgrp-ownership-rhcsa/) · [41b Ansible](lab-41b-chown-chgrp-ownership-ansible/) · [41c Verify](lab-41c-chown-chgrp-ownership-verify/) — `chown`, `chgrp` |
| 3 | not completed | 42 | SUID Executables | [42a RHCSA](lab-42a-suid-executable-rhcsa/) · [42b Ansible](lab-42b-suid-executable-ansible/) · [42c Verify](lab-42c-suid-executable-verify/) — `chmod u+s`, `ls -l` |
| 4 | not completed | 43 | Configure SGID and Sticky Bit | [43a RHCSA](lab-43a-sgid-sticky-bit-rhcsa/) · [43b Ansible](lab-43b-sgid-sticky-bit-ansible/) · [43c Verify](lab-43c-sgid-sticky-bit-verify/) — `chmod g+s`, `chmod +t`, `ls -ld` |
| 5 | not completed | 44 | Immutable File Attribute | [44a RHCSA](lab-44a-chattr-immutable-rhcsa/) · [44b Ansible](lab-44b-chattr-immutable-ansible/) · [44c Verify](lab-44c-chattr-immutable-verify/) — `chattr +i`, `lsattr` |
| 6 | not completed | 45 | Append-Only File Attribute | [45a RHCSA](lab-45a-chattr-append-only-rhcsa/) · [45b Ansible](lab-45b-chattr-append-only-ansible/) · [45c Verify](lab-45c-chattr-append-only-verify/) — `chattr +a` |
| 7 | not completed | 46 | Identifying File Attributes | [46a RHCSA](lab-46a-lsattr-extended-attrs-rhcsa/) · [46b Ansible](lab-46b-lsattr-extended-attrs-ansible/) · [46c Verify](lab-46c-lsattr-extended-attrs-verify/) — `lsattr` |
| 8 | not completed | 47 | Check ACL Support | [47a RHCSA](lab-47a-acl-mount-option-rhcsa/) · [47b Ansible](lab-47b-acl-mount-option-ansible/) · [47c Verify](lab-47c-acl-mount-option-verify/) — `mount`, `acl` option |
| 9 | not completed | 48 | Viewing ACLs | [48a RHCSA](lab-48a-getfacl-view-acl-rhcsa/) · [48b Ansible](lab-48b-getfacl-view-acl-ansible/) · [48c Verify](lab-48c-getfacl-view-acl-verify/) — `getfacl` |
| 10 | not completed | 49 | Modifying ACLs | [49a RHCSA](lab-49a-setfacl-modify-rhcsa/) · [49b Ansible](lab-49b-setfacl-modify-ansible/) · [49c Verify](lab-49c-setfacl-modify-verify/) — `setfacl -m` |
| 11 | not completed | 50 | Denying Access via ACLs | [50a RHCSA](lab-50a-setfacl-deny-rhcsa/) · [50b Ansible](lab-50b-setfacl-deny-ansible/) · [50c Verify](lab-50c-setfacl-deny-verify/) — `setfacl` |
| 12 | not completed | 51 | Default Directory ACLs | [51a RHCSA](lab-51a-default-acl-inherit-rhcsa/) · [51b Ansible](lab-51b-default-acl-inherit-ansible/) · [51c Verify](lab-51c-default-acl-inherit-verify/) — `setfacl -d` |
| 13 | not completed | 52 | ACL Masks | [52a RHCSA](lab-52a-acl-masks-rhcsa/) · [52b Ansible](lab-52b-acl-masks-ansible/) · [52c Verify](lab-52c-acl-masks-verify/) — `setfacl -m m::` |
| 14 | not completed | 53 | Removing ACLs | `setfacl -x`, `setfacl -b` — strip specific or all ACL entries |
| 15 | not completed | 54 | NFSv4 ACLs | `nfs4_getfacl`, `nfs4_setfacl` — edit NFSv4 share permissions |
| 16 | not completed | PERM-F01 | Collaborative SGID Directory with Multi-User Write Test | `chmod 2770 /sdata`, prove cross-user edit + no-delete |
| 17 | not completed | PERM-F02 | File Copy with Combined Ownership + Permissions + ACL + Future-User Safety | `cp /etc/fstab /var/tmp`, `chown root:admins`, `setfacl` mix |
| 18 | not completed | PERM-F03 | ACL with Mixed Read/Write/Read-Only Per User | `setfacl u:emma:rw,u:liam:rw,u:sophie:r,m::rw`, default ACL on parent |
| 19 | not completed | PERM-F04 | Per-User Default umask via `~/.bashrc` | `echo 'umask 0577' >> ~/.bashrc`, files become 400 |
| 20 | not completed | PERM-F05 | Collaborative Group Directory with SGID + Sticky Bit | `chmod 3770 /data/engineers` — SGID + sticky combo |
| 21 | not completed | PERM-F06 | Restricted Directory Where Owner Has chmod But No rwx | `chmod g+rwx,o-rwx,u-rwx` — owner keeps chmod, loses rwx |
| 22 | not completed | 55 | Inspecting iptables | `iptables -L` — review default chains + rules |
| 23 | not completed | 56 | Exploring firewalld Zones | `firewall-cmd --get-default-zone`, `--list-all` |
| 24 | not completed | 57 | Changing Default Firewall Zone | `firewall-cmd --set-default-zone` — reassign interface |
| 25 | not completed | 58 | Adding Services to Zones | `firewall-cmd --add-service`, `--permanent` |
| 26 | not completed | 59 | Opening Custom Ports | `firewall-cmd --add-port` — non-standard port to zone |
| 27 | not completed | 60 | Inspect Active Firewall Zones | `firewall-cmd --get-default-zone`, `--list-all` |
| 28 | not completed | 61 | Reassign Interfaces to Zones | `firewall-cmd --change-interface` — move interface zones |
| 29 | not completed | 62 | Allow Services Through Firewall | `firewall-cmd --permanent --add-service` for web/FTP |
| 30 | not completed | 63 | Configure IP Masquerading NAT | `firewall-cmd --add-masquerade` — outbound NAT |
| 31 | not completed | 64 | Configure IP Forwarding | `/etc/sysctl.conf`, `net.ipv4.ip_forward=1`, `sysctl -p` |
| 32 | not completed | 65 | Configure Rich Rules | `firewall-cmd --add-rich-rule` — deny specific host |
| 33 | not completed | 66 | Setup Port Forwarding DNAT | `firewall-cmd` rich rules — redirect port 80→8008 |
| 34 | not completed | 67 | Configure ICMP Filters | `firewall-cmd --add-icmp-block echo-request` — drop pings |
| 35 | not completed | FW-F01 | Open Multiple Services at Once for Web Hosting | `--add-service={ssh,http,https}`, `--list-services` |
| 36 | not completed | FW-F02 | Open a Non-Standard SSH Port + Move SSH There | `--add-port=88/tcp`, `sshd_config Port 88`, `semanage port` |

#### Step 4: TCP Wrappers, PAM, SELinux

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 1 | not completed | 68 | Verify TCP Wrappers Support | `ldd /usr/sbin/sshd \| grep libwrap` |
| 2 | not completed | 69 | Restrict Access via hosts.deny | `/etc/hosts.deny` `ALL : ALL` — default deny |
| 3 | not completed | 70 | Allow Specific Access via hosts.allow | `/etc/hosts.allow` — explicit SSH allows |
| 4 | not completed | 71 | Configure TCP Wrappers for FTP | `vsftpd`, `/etc/hosts.deny` — deny specific IP |
| 5 | not completed | 72 | Explore PAM Config Files | `/etc/pam.d/` — types + control flags |
| 6 | not completed | 73 | Read PAM Module Documentation | `/usr/share/doc/pam-*/txts/` — `pam_securetty.so` docs |
| 7 | not completed | 74 | Implement Password Complexity | `pam_pwquality.so`, `system-auth` — enforce password rules |
| 8 | not completed | 75 | Configure PAM to Limit root Access | `pam_securetty.so` — root only on tty6 |
| 9 | not completed | 76 | Use PAM to Limit User Access | `/etc/nologin` — block regular users with custom message |
| 10 | not completed | 77 | Restrict Service Access by User List | `pam_listfile.so` — deny per text-file user list |
| 11 | not completed | 78 | Managing SELinux Modes | `sestatus`, `setenforce` — enforcing vs permissive |
| 12 | not completed | 79 | Viewing SELinux Contexts | `ls -Z`, `ps -eZ` — file + process contexts |
| 13 | not completed | 80 | Temporary Context Changes | `chcon` — non-persistent context change |
| 14 | not completed | 81 | Persistent Context Restoration | `semanage fcontext`, `restorecon` — persistent rules + apply |
| 15 | not completed | 82 | Toggling SELinux Booleans | `getsebool`, `setsebool -P` |
| 16 | not completed | 83 | SELinux User Mapping | `semanage login` — map Linux user to `guest_u`/`staff_u` |
| 17 | not completed | 84 | Troubleshooting SELinux | `audit.log`, `sealert` — diagnose denials |
| 18 | not completed | in-repo | Apply Recursive SELinux Contexts to a New Directory | `semanage fcontext -a -e`, `restorecon -RFv` reference-dir contexts |
| 19 | not completed | SEL-F02 | Add a Custom HTTP Port to the SELinux Policy Database | `semanage port -a -t http_port_t -p tcp 8300` |
| 20 | not completed | SEL-F03 | Set SELinux to Permissive Mode Persistently | `/etc/selinux/config: SELINUX=permissive`, `setenforce 0` |
| 21 | not completed | SEL-F04 | Apply Recursive SELinux Context from a Reference Directory | `semanage fcontext -a -e /etc /dir`, `restorecon -RFv` |
| 22 | not completed | SEL-F05 | Configure Apache to Serve from a Non-Default Directory | `semanage fcontext -t httpd_sys_content_t '/web(/.*)?'` |
| 23 | not completed | SEL-F06 | Toggle the `httpd_can_network_connect` Boolean Persistently | `setsebool -P httpd_can_network_connect on`, reboot-verify |

#### Step 5: Boot, Systemd, Logging

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 1 | not completed | 85 | Modify GRUB Timeout | `/etc/default/grub`, `GRUB_TIMEOUT` |
| 2 | not completed | 86 | Enable Verbose Kernel Messages | `GRUB_CMDLINE_LINUX` — remove `quiet` keyword |
| 3 | not completed | 87 | Generate New GRUB Config | `grub2-mkconfig -o /boot/grub2/grub.cfg` |
| 4 | not completed | 88 | Reset Root Password via Boot | GRUB `rd.break`, `chroot`, `passwd`, `.autorelabel` |
| 5 | not completed | 89 | Chroot into Rescue Filesystem | `chroot /mnt/sysimage` — repairs to installed system |
| 6 | not completed | BOOT-F01 | Enable Verbose Boot by Removing `quiet` and `rhgb` | Edit `/etc/default/grub`, `grub2-mkconfig`, observe verbose boot |
| 7 | not completed | 90 | Check Default Boot Target | `systemctl get-default` |
| 8 | not completed | 91 | Change Default Boot Target | `systemctl set-default` — permanent text-mode boot |
| 9 | not completed | 92 | System Reboots and Shutdowns | `systemctl reboot`, `systemctl poweroff` |
| 10 | not completed | 93 | List All System Units | `systemctl list-units --all` |
| 11 | not completed | 94 | Check Service Status | `systemctl status` — PID + recent logs |
| 12 | not completed | 95 | Start and Stop Services | `systemctl start`, `systemctl stop` |
| 13 | not completed | 96 | Enable Services at Boot | `systemctl enable` — link to default target |
| 14 | not completed | 97 | Disable Services at Boot | `systemctl disable` — block auto-start |
| 15 | not completed | 98 | Mask System Services | `systemctl mask` — block accidental start |
| 16 | not completed | 99 | Create and Manage systemd Unit Files | Unit file syntax, `systemctl daemon-reload` |
| 17 | not completed | SYSD-F01 | Set the Default Boot Target to `multi-user.target` | `systemctl set-default`, `isolate`, reboot-verify |
| 18 | not completed | 100 | Analyze Boot Performance | `systemd-analyze blame` — slowest boot services |
| 19 | not completed | 101 | Query Logs with journalctl | `journalctl -u`, `-p`, `--since`, `--until` |
| 20 | not completed | 102 | Configure Persistent Journal Logs | `/var/log/journal` — force on-disk journal |
| 21 | not completed | 103 | Understand Log Routing | `/etc/rsyslog.conf` — kernel + system message routing |
| 22 | not completed | 104 | Monitor Authentication Logs | `/var/log/secure` — logins, SSH, failed auth |
| 23 | not completed | 105 | Filter systemd Journals by Priority | `journalctl -p alert` — high-priority errors |
| 24 | not completed | 106 | Service-Specific Journal Logs | `journalctl -u httpd` — daemon-scoped journal |

#### Step 6: Storage, LVM, Mounts

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 1 | not completed | 107 | Configure Timezone and Time Synchronization | `timedatectl`, `systemctl enable --now chronyd` |
| 2 | not completed | 108 | Check NTP Sync Status | `ntpq -p`, `chronyc tracking` |
| 3 | not completed | 109 | Configure NTP Time Source | `/etc/chrony.conf`, `chronyc sources`, `iburst` |
| 4 | not completed | TIME-F01 | Set System Timezone via `timedatectl` | `timedatectl set-timezone Europe/London` |
| 5 | not completed | TIME-F02 | Configure Chrony with a Specific NTP Server | `/etc/chrony.conf` `server utility.ntp.org iburst`, `chronyc sources -v` |
| 6 | not completed | 110 | Inspect Filesystems | `df -h`, `findmnt` |
| 7 | not completed | 111 | Display Partition Tables | `fdisk -l` — all attached drives |
| 8 | not completed | 112 | Create MBR Partition with fdisk | `fdisk /dev/vdb` — `n`, `p`, `w` |
| 9 | not completed | 113 | Change Partition Types in fdisk | `t` command — `83` Linux, `8e` LVM |
| 10 | not completed | 114 | Create GPT Partition with gdisk | `gdisk` — GPT partition table |
| 11 | not completed | 115 | Command-Line Partitioning with parted | `parted`, `mklabel`, `mkpart` |
| 12 | not completed | 116 | Format Partition with XFS | `mkfs.xfs` — default RHEL filesystem |
| 13 | not completed | 117 | Format Partition with Ext4 | `mkfs.ext4` — journaling filesystem |
| 14 | not completed | 118 | Check Filesystem Consistency | `fsck.ext4` — integrity of unmounted ext partition |
| 15 | not completed | 119 | Inspect Filesystem Features | `dumpe2fs -h \| grep features` |
| 16 | not completed | 120 | Create and Activate Swap Space | `mkswap`, `swapon`, `swapoff`, `/etc/fstab` |
| 17 | not completed | STOR-F03 | Create an MBR Partition with ext4 Mounted by LABEL | `parted mklabel msdos`, `mkfs.ext4 -L MYDEV`, fstab LABEL= |
| 18 | not completed | STOR-F04 | Create a Companion LVM-Type Partition on the Same Disk | `parted mkpart`, `set 2 lvm on`, prove with `fdisk -l` |
| 19 | not completed | in-repo | Create a Swap Partition by UUID | `mkswap`, `blkid`, fstab `UUID=... swap sw 0 0`, `swapon -a` |
| 20 | not completed | in-repo | Create an Ext4 Partition Mounted by LABEL | `mkfs.ext4 -L`, fstab `LABEL=... ext4 defaults 0 2` |
| 21 | not completed | in-repo | Initialize Physical Volumes | [`labs/lvm-pvcreate-initialize-pv/`](labs/lvm-pvcreate-initialize-pv/) — `pvcreate`, `pvremove`, loopback practice |
| 22 | not completed | in-repo | Display Physical Volumes | [`labs/lvm-display-physical-volumes/`](labs/lvm-display-physical-volumes/) — `pvs`, `pvdisplay`, `pvscan` |
| 23 | not completed | in-repo | Create Volume Group | [`labs/lvm-create-volume-group/`](labs/lvm-create-volume-group/) — `vgcreate`, `-s` PE size |
| 24 | not completed | in-repo | Display Volume Groups | [`labs/lvm-display-volume-groups/`](labs/lvm-display-volume-groups/) — `vgs`, `vgdisplay` |
| 25 | not completed | in-repo | Create Logical Volume | [`labs/lvm-create-logical-volume/`](labs/lvm-create-logical-volume/) — `lvcreate -L`, `-l`, `100%FREE` |
| 26 | not completed | in-repo | Display Logical Volumes | [`labs/lvm-display-logical-volumes/`](labs/lvm-display-logical-volumes/) — `lvs`, `lvdisplay`, `lv_attr` |
| 27 | not completed | in-repo | Extend Volume Group | [`labs/lvm-extend-volume-group/`](labs/lvm-extend-volume-group/) — `vgextend` |
| 28 | not completed | in-repo | Extend Logical Volume | [`labs/lvm-extend-logical-volume/`](labs/lvm-extend-logical-volume/) — `lvextend` |
| 29 | not completed | in-repo | Resize Filesystem After Extend | [`labs/lvm-resize-filesystem-after-extend/`](labs/lvm-resize-filesystem-after-extend/) — `xfs_growfs`, `resize2fs` |
| 30 | not completed | in-repo | Remove LVM Components | [`labs/lvm-remove-components/`](labs/lvm-remove-components/) — `lvremove`, `vgremove`, `pvremove` |
| 31 | not completed | in-repo (LAB) | Create LV `lvol1` (ext4, 280 MB) | `pvcreate`, `vgcreate`, `lvcreate -L 280M -n lvol1`, mkfs.ext4, UUID fstab on `/mnt/mnt1` |
| 32 | not completed | in-repo | Create LV with XFS Filesystem | `lvcreate -l 10 -n lv1 vg1` (8 MB PE × 10 LE), mkfs.xfs, persistent mount `/mnt/lvfs1` |
| 33 | not completed | in-repo | Online Extend an LV and Its Filesystem Without Unmounting | `lvextend -L +64M`, `xfs_growfs` while mounted |
| 34 | not completed | LVM-F02 | Create an LVM VDO Volume with Thin Provisioning | `vdo create --vdoLogicalSize=20G`, ext4 + XFS variants |
| 35 | not completed | LVM-F03 | LV by Extent Count in a VG with Custom PE Size (ext4 variant) | `vgcreate -s 8M`, `lvcreate -l 50` = 400 MiB, mkfs.ext4 |
| 36 | not completed | LVM-F04 | LV Sized as a Percentage of the VG with XFS + UUID Mount | `lvcreate -l 50%VG`, mkfs.xfs, fstab UUID |
| 37 | not completed | LVM-F05 | LV Sized as a Percentage of Free Space with XFS | `lvcreate -l 75%FREE -n lvstore vgdata` |
| 38 | not completed | LVM-F06 | LV with Extent Count + Reserved Free Extents Constraint | `vgcreate -s 16M`, `lvcreate -l 40` leaving ≥10 free |
| 39 | not completed | LVM-F07 | Online Resize LV to a New Total Extent Count + Grow ext4 | `lvresize -l 85` (exact total), `resize2fs` |
| 40 | not completed | LVM-F08 | Add Extents to an Existing LV + Grow XFS Online | `lvextend -l +8`, `xfs_growfs /mnt/team_lv` |
| 41 | not completed | LVM-F09 | Create Swap from Remaining VG Free Space | `lvcreate -L 500M -n swap_lv`, `mkswap`, fstab swap entry |
| 42 | not completed | 131 | Mount Filesystem Manually | `mount` — attach partition or LV to directory |
| 43 | not completed | 132 | Retrieve Filesystem UUIDs | `blkid` — UUID for persistent mounting |
| 44 | not completed | 133 | Configure Persistent Mounts fstab | `/etc/fstab` — UUID + mount point + fs type |
| 45 | not completed | 134 | Mount Network CIFS Shares | `mount.cifs` — Windows/Samba share |
| 46 | not completed | 135 | Remount with New Options | `mount -o remount` — modify options live |
| 47 | not completed | 136 | Manage Autofs Service | `systemctl` — automounter at boot |
| 48 | not completed | NFS-F01 | NFS Server + AutoFS Direct Map | Export `/rh_share`, client `/etc/auto.master.d/direct.autofs` |
| 49 | not completed | NFS-F02 | NFS Home-Directory Export with AutoFS Indirect Map on Login | Server exports `/home/user60`, client indirect map mounts at first login |
| 50 | not completed | NFS-F03 | NFS Static Export with Persistent `/etc/fstab` Mount | `exportfs -rav`, `_netdev,defaults` fstab entry |
| 51 | not completed | NFS-F04 | Configure a Node as an NFS Server (companion lab) | `nfs-utils`, `/etc/exports`, `exportfs -rav`, firewall `nfs,mountd,rpc-bind` |
| 52 | not completed | NFS-F05 | AutoFS Indirect Map for Remote Home Dirs with 60s Timeout | `/homes/remote /etc/auto.homes --timeout=60` |
| 53 | not completed | NFS-F06 | AutoFS Direct Map for `/mnt/shared` with 5-Minute Timeout | `/etc/auto.master.d/direct.autofs`, `--timeout=300` |

#### Step 7: Packages, Users, Sudo

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 1 | not completed | 137 | Install Local RPM Package | `rpm -ivh` — install from local file |
| 2 | not completed | 138 | Upgrade RPM Package | `rpm -U`, `rpm -F` — upgrade existing |
| 3 | not completed | 139 | Install New Kernel Safely | `rpm -ivh` — install kernel side-by-side |
| 4 | not completed | 140 | Uninstall Package rpm -e | `rpm -e` — remove a package |
| 5 | not completed | 141 | Query All Installed Packages | `rpm -qa` — list all installed |
| 6 | not completed | 142 | Query Specific Package Info | `rpm -qi` — package metadata |
| 7 | not completed | 143 | List Files Within Package | `rpm -ql` — what files a package installed |
| 8 | not completed | 144 | Identify File Owner | `rpm -qf` — which package owns a file |
| 9 | not completed | 145 | Query Uninstalled RPMs | `rpm -p` — inspect an RPM file pre-install |
| 10 | not completed | 146 | Verify Package Integrity | `rpm -V` — verify against RPM database |
| 11 | not completed | 147 | System-Wide Verification | `rpm -Va` — verify all packages |
| 12 | not completed | 148 | Import GPG Key | `rpm --import` — public GPG into RPM DB |
| 13 | not completed | 149 | Check Package Signatures | `rpm -K` — verify signature before installing |
| 14 | not completed | 150 | Configure Repository Access | `dnf`, `tee`, `/etc/yum.repos.d/` |
| 15 | not completed | 151 | Install Packages with dnf | `dnf install` — auto-resolve dependencies |
| 16 | not completed | 152 | Remove Packages with dnf | `dnf remove` — uninstall + orphan removal |
| 17 | not completed | 153 | Update System dnf update | `dnf update` — package or system |
| 18 | not completed | 154 | Search for Software | `dnf search` — find packages by keyword |
| 19 | not completed | 155 | Find File Providers | `dnf whatprovides` — which package ships a file |
| 20 | not completed | 156 | List dnf Packages | `dnf list` — installed + available |
| 21 | not completed | 157 | Display Enabled Repositories | `dnf repolist all` |
| 22 | not completed | 158 | View Package Group Info | `dnf group list`, `dnf group info` |
| 23 | not completed | 159 | Install Package Groups | `dnf groupinstall`, `dnf groupremove` |
| 24 | not completed | 160 | Create Custom YUM Repository | `createrepo` — local repo with XML metadata |
| 25 | not completed | 161 | Managing Flatpak | `flatpak remote-add`, `flatpak install --user`, `flatpak list` |
| 26 | not completed | in-repo | Install Development Tools Package Group with Output Capture | `dnf group install 'Development Tools'`, capture before/after with `dnf list installed` |
| 27 | not completed | PKG-F02 | Configure Local Repository from Installation ISO Media | Loop-mount ISO at `/repo`, fstab entry, `.repo` files for BaseOS + AppStream |
| 28 | not completed | PKG-F03 | Configure Two HTTP-Hosted Repositories from a Network Source | `http://repo.example.com/rhel9/{BaseOS,AppStream}`, `dnf install -y httpd` |
| 29 | not completed | 162 | Inspect Password Database | `/etc/passwd` — usernames, UIDs, GIDs, home |
| 30 | not completed | 163 | Analyze Shadow File | `/etc/shadow` — hashed passwords + aging |
| 31 | not completed | 164 | Modify Default Password Aging | `/etc/login.defs` `PASS_MAX_DAYS` etc. |
| 32 | not completed | 165 | User & Group Management / Permissions | `useradd`, `groupadd`, `chown`, `chmod`, `id`, `getent` |
| 33 | not completed | 166 | Modify Existing Account | `usermod -L/-U/-aG` — lock/unlock/append group |
| 34 | not completed | 167 | Advanced Group Management | `groupadd`, `gpasswd`, `groupmod` |
| 35 | not completed | 168 | Force Password Changes | `chage` — view aging + force next-login change |
| 36 | not completed | 169 | Safely Delete Users | `userdel -r` — remove user + home + mail spool |
| 37 | not completed | 170 | Disable User Login Without Removing the Account | `usermod -s /sbin/nologin`, `getent passwd` |
| 38 | not completed | 171 | Validate User and Group Creation | `/etc/group`, `/etc/shadow` — verify primary groups |
| 39 | not completed | 172 | Proper Use of su vs su - | `su` vs `su -` — env var differences |
| 40 | not completed | 173 | Limit Access to su PAM | PAM `wheel` group restriction |
| 41 | not completed | 174 | Configure Custom Administrators | `visudo`, `/etc/sudoers` — full admin grant |
| 42 | not completed | 175 | Granular sudo Privileges | `visudo`, `Cmnd_Alias` — specific-command grants |
| 43 | not completed | 176 | Limit root Logins | `/etc/securetty` — which TTYs root can use |
| 44 | not completed | 177 | Restrict Root to Single Console | `/etc/securetty` — root only on `tty6` |
| 45 | not completed | 178 | Populate Directory Templates | `/etc/skel` — auto-files on user creation |
| 46 | not completed | 179 | Manage Shell Environments | `.bash_profile`, `.bashrc` — persistent env + aliases |
| 47 | not completed | 180 | Alter Global Default umask | `/etc/bashrc`, `/etc/profile` — system-wide umask |
| 48 | not completed | 181 | Distribute Documentation via Skel | `/etc/skel` — docs auto-distributed to new users |
| 49 | not completed | 182 | Control Group Ownership SGID | `chmod g+s` — group inheritance on shared dir |
| 50 | not completed | 183 | Set Up Group-Managed Directory | `chmod 2770 /home/galley` — 4-user shared dir |
| 51 | not completed | in-repo | Lock User Account and Capture Regex Evidence | `passwd -l`, `chage -E 0`, grep `/etc/shadow` for lock marker |
| 52 | not completed | USER-F01 | Group with Fixed GID + User with Primary/Secondary Groups | `groupadd -g 3500 admins`, `useradd -u 3455 -g admins -G users harry` |
| 53 | not completed | USER-F02 | User Without Interactive Shell (`nologin`) That Still Authenticates | `useradd -s /sbin/nologin sarah`, PAM password auth still works |
| 54 | not completed | USER-F03 | User With Explicit (Hand-Built) Home Directory | `useradd -M`, `mkdir + cp -av /etc/skel/.`, `chmod 700` |
| 55 | not completed | USER-F04 | Force Password Change at Next Login | `passwd --expire liam` or `chage -d 0` |
| 56 | not completed | USER-F05 | Set Hard Account Expiry Date | `chage -E 2029-01-01 lina`, or `$(date -d '+7 days')` |
| 57 | not completed | USER-F06 | Welcome.txt Auto-Created for Every New User via `/etc/skel` | `echo > /etc/skel/Welcome.txt`, new user inherits |
| 58 | not completed | USER-F07 | Configure System-Wide Password Aging Policy | `/etc/login.defs PASS_MAX_DAYS 30`, applies to new users |
| 59 | not completed | USER-F08 | Reset Root Password from GRUB Boot Menu (`rd.break` Path) | GRUB + `rd.break`, `chroot /sysroot`, `passwd`, `.autorelabel` |
| 60 | not completed | SUDO-F01 | Full Sudo for a User + NOPASSWD for an Entire Group | `john ALL=(ALL) ALL` + `%admins ALL=(ALL) NOPASSWD: ALL` |
| 61 | not completed | SUDO-F02 | Granular Sudo: Allow `passwd` Except Root Password Changes | `brian ALL=(ALL) /usr/bin/passwd [A-Za-z]*, !/usr/bin/passwd root` |
| 62 | not completed | SUDO-F03 | Privileged User with Account Expiry | `useradd -u 4545 marvin`, wheel + `chage -E $(date -d '+7 days')` |

#### Step 8: Processes, Archives, Cron

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 1 | not completed | 184 | Audit All Running Processes | `ps aux` — CPU + memory usage |
| 2 | not completed | 185 | Identify Process Details | `ps axl` — PPIDs + nice values |
| 3 | not completed | 186 | View SELinux Process Contexts | `ps -Z` — SELinux contexts of running daemons |
| 4 | not completed | 187 | Real-Time Process Monitoring | `top` — load, tasks, memory, swap |
| 5 | not completed | 188 | Adjust Process Priority | `renice` — change priority of running process |
| 6 | not completed | 189 | Start Processes with Custom Priority | `nice` — launch with predefined priority |
| 7 | not completed | 190 | Terminate Processes Gracefully | `kill` (SIGTERM) |
| 8 | not completed | 191 | Force Kill Unresponsive Processes | `kill -9` (SIGKILL) |
| 9 | not completed | 192 | Kill Processes by Name | `killall` — kill multiple by name |
| 10 | not completed | PROC-F01 | Start a Background Process with a Specific nice Value | `nice -n 10 sleep 3600 &`, capture `$!`, `ps -o pid,ni` |
| 11 | not completed | PROC-F02 | Renice a Running Process to a Higher Priority | `renice -n -5 -p $PID` — root needed for negative niceness |
| 12 | not completed | PROC-F03 | Lowest-Priority Background Task on User Login | `~/.bash_profile`: `nice -n 19 sleep infinity &` |
| 13 | not completed | PROC-F04 | Clean Termination of a Background Process | SIGTERM first, SIGKILL only on hung processes |
| 14 | not completed | 193 | Standard File Compression with gzip | `gzip`, `gunzip`, `zcat` |
| 15 | not completed | 194 | High-Ratio Compression with bzip2 | `bzip2`, `bunzip2`, `bzcat` |
| 16 | not completed | 195 | Create Standard Archives with tar | `tar -cvf`, `-tvf`, `-xvf` |
| 17 | not completed | 196 | Create Compressed Archives | `tar -czf`, `-cjf`, `-cJf`, `xz` |
| 18 | not completed | 197 | Extract Archives | `tar -xvf` — extract to specific directory |
| 19 | not completed | 198 | Preserve Security Contexts in Archives | `tar --selinux` — preserve contexts + ACLs |
| 20 | not completed | ARCH-F01 | Create an xz-Compressed Tar Archive | `tar -cJvf /archives/config_backup.tar.xz /etc` |
| 21 | not completed | ARCH-F02 | Create an Uncompressed Standard Tar Archive | `tar -cvf /root/etc_opt.bak.tar /etc /opt` |
| 22 | not completed | ARCH-F03 | Restore a Tar Archive into a Specific Destination Directory | `tar -xzvf /root/tmp.tgz -C /root/restored_tmp` |
| 23 | not completed | 199 | Review System-Wide cron Jobs | `/etc/crontab` — m h dom mon dow format |
| 24 | not completed | 200 | Schedule Tasks with cron | `crontab -e`, `/etc/cron.d/` |
| 25 | not completed | 201 | Remove User cron Jobs | `crontab -l`, `crontab -r` |
| 26 | not completed | 202 | Schedule One-Time Task with at | `at` — one-shot scheduling |
| 27 | not completed | 203 | Limit Access to cron | `/etc/cron.deny` |
| 28 | not completed | 204 | Limit Access to at | `/etc/at.allow`, `/etc/at.deny` |
| 29 | not completed | 205 | Review the Anacron System | `/etc/anacrontab` — catch up missed jobs |
| 30 | not completed | 206 | Create a Specific cron Job | `crontab -e` — 1:05 PM Mondays in January |
| 31 | not completed | 207 | Schedule Software Audit with at | `at` — `rpm -qa > /root/rpms.txt` in 5 minutes |
| 32 | not completed | in-repo (LAB) | Scheduling Jobs (systemd timer, Mon–Fri 2 AM) | `.timer` + `.service`, `OnCalendar=Mon..Fri *-*-* 02:00:00` |
| 33 | not completed | in-repo | User-Level Cron Job with `find -exec` | `crontab -e` as user, `find -exec` into core directory |
| 34 | not completed | CRON-F02 | User Cron Job at 12:45 AM Daily | `45 0 * * * /usr/bin/echo ... >> $HOME/cron.log` |
| 35 | not completed | CRON-F03 | Recurring User Cron Job Every 2 Minutes | `*/2 * * * * logger "..."` |
| 36 | not completed | CRON-F04 | Weekday-Only Cron Job at 5:45 AM | `45 5 * * 1-5 logger "Good morning!"` |
| 37 | not completed | CRON-F05 | Midnight-Weekend Root Cron Job to Clean Empty Files in `/tmp` | `0 0 * * 6,0 find /tmp -maxdepth 1 -type f -empty -delete` |
| 38 | not completed | CRON-F06 | One-Time `at` Job for a Specific Wall-Clock Time | `echo 'cmd' \| at 21:30` |
| 39 | not completed | CRON-F07 | One-Time `at` Job One Hour from Now Writing to journald | `echo 'logger "..."' \| at now + 1 hour` |

#### Step 9: GPG, Remote Admin, Security

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 1 | not completed | 208 | Generate a GPG Key Pair | `gpg --gen-key` — RSA pub/priv + passphrase |
| 2 | not completed | 209 | Encrypt a File with GPG | `gpg --recipient --encrypt` |
| 3 | not completed | 210 | Decrypt a GPG File | `gpg --decrypt` |
| 4 | not completed | 211 | Share and Verify Public Keys | `gpg --export -a`, `scp`, `gpg --import` |
| 5 | not completed | 212 | SSH and SCP File Transfer | `ssh`, `scp` |
| 6 | not completed | 213 | Network Troubleshooting | `telnet`, `nmap` — port scans + service checks |
| 7 | not completed | 214 | Command-Line Web and FTP Testing | `elinks -dump`, `lftp`, `get`/`put` |
| 8 | not completed | 215 | Command-Line Email Testing | `mail -s`, `mutt -f`, `postfix`, `/var/mail/` |
| 9 | not completed | 216 | Service Isolation Bastion Host | `systemctl disable` — SSH-only minimal VM |
| 10 | not completed | 217 | Monitor Security Updates | `dnf update` — Red Hat Errata fixes |
| 11 | not completed | 218 | Build a Bastion Server | minimal install, `systemctl` — SSH active, others disabled |
| 12 | not completed | 219 | Comprehensive firewalld Setup | `firewall-cmd` — HTTP+SSH, ICMP block, masq + rich rules |
| 13 | not completed | 220 | PAM and SELinux with FTP | `vsftpd`, `ftp_home_dir` boolean, PAM blocks root FTP |
| 14 | not completed | SSH-F01 | Configure SSH to Listen on a Custom Port | `Port 88`, `semanage port -a -t ssh_port_t`, firewall port 88/tcp |
| 15 | not completed | SSH-F02 | Permit Root SSH Login with Authentication-Failure Lockout | `PermitRootLogin yes` + `MaxAuthTries 3` |
| 16 | not completed | SSH-F03 | Passwordless SSH from Root to Remote Root | `ssh-keygen -t ed25519 -N ""`, `ssh-copy-id` |
| 17 | not completed | SSH-F04 | Key-Based SSH from a User to a Remote Root on a Custom Port | `ssh-copy-id -p 88 root@Node1`, prove `ssh -p 88` works |
| 18 | not completed | SSH-F05 | Configure Local `/etc/hosts` Name Resolution | Add `192.168.56.25 node1.lab3.example.net` for DNS-free SSH |
| 19 | not completed | SSH-F06 | Secure File Transfer with `scp` Preserving Attributes | `scp -p` (preserves timestamps + mode) vs `rsync --chown` |

#### Step 10: Web, Tuning, Scripting, Containers

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 1 | not completed | 221 | Configure Apache to Serve Default and Custom Web Content | `httpd`, `semanage fcontext`, `restorecon`, `curl` |
| 2 | not completed | 222 | Password-Protect a Directory | `htpasswd`, `AuthType Basic`, `Require user` |
| 3 | not completed | 223 | Deploy Name-Based Virtual Hosts | `<VirtualHost *:80>`, `/etc/httpd/conf.d/` |
| 4 | not completed | 224 | Configure Secure Virtual Hosts HTTPS | `ssl.conf`, `SSLCertificateFile`, `genkey` |
| 5 | not completed | WEB-F01 | Apache Listening on a Non-Standard TCP Port | `Listen 85`, `semanage port -a -t http_port_t`, firewall 85/tcp |
| 6 | not completed | WEB-F02 | Apache Default Page + Custom Content Directory | `/web/practice.html`, `semanage fcontext httpd_sys_content_t '/web(/.*)?'` |
| 7 | not completed | WEB-F03 | Apache Subdirectory Routing with SELinux Inheritance | `/var/www/html/route_station`, inherited context |
| 8 | not completed | WEB-F04 | Password-Protected Apache Directory with htpasswd | `htpasswd -c`, `AuthType Basic`, `Require valid-user` |
| 9 | not completed | WEB-F05 | Apache SSL Virtual Host with Self-Signed Certificate | `openssl req -x509`, ssl.conf, firewall `--add-service=https` |
| 10 | not completed | 225 | Enable Recommended Tuning Profile | `tuned-adm recommend`, `tuned-adm profile`, `tuned-adm active` |
| 11 | not completed | PERF-F01 | Apply the `virtual-guest` Tuning Profile | `tuned-adm profile virtual-guest` for VMs |
| 12 | not completed | PERF-F02 | Apply a Power-Saving / Virtualization-Balanced Profile | `tuned-adm profile balanced-battery` or `virtual-guest-powersave` |
| 13 | not completed | 226 | Argument-Based Conditional Script | `$1`, `$#`, `if/elif/else`, `exit 5`, `chmod +x` |
| 14 | not completed | 227 | Use for Loops for Iteration | `for`, `getent passwd` |
| 15 | not completed | in-repo | Bidirectional Bash Script with Argument Logic | `$#` validation, exit codes, two-way arg handling |
| 16 | not completed | SCRIPT-F02 | Bash Script: Find Files Matching a Pattern and Print stat | Loop `/usr/bin/ac*`, `[ -f $f ]`, `stat`, redirect to `/var/tmp/acstats.out` |
| 17 | not completed | SCRIPT-F03 | Bash Script: Create a User Whose Name Comes from a Variable | `ENV1=book1`, `useradd "$ENV1"`, `id "$ENV1"` |
| 18 | not completed | SCRIPT-F04 | Countdown Timer Script with Argument or Interactive Prompt | `$# -eq 1` arg vs `read -p`, `while [ $COUNT -gt 0 ]` |
| 19 | not completed | SCRIPT-F05 | Sum of an Unknown Number of Integer Arguments | `$# -eq 0` → exit 1, `for n in "$@"; do ((total+=n)); done` |
| 20 | not completed | SCRIPT-F06 | Find Users by Login Shell and Save the List | `getent passwd \| awk -F: '$7=="/bin/bash"' > /root/bash_users.txt` |
| 21 | not completed | SCRIPT-F07 | Extract Login Shells of the Last 5 Users in `/etc/passwd` | `tail -5 /etc/passwd \| awk -F: '{printf...}'` |
| 22 | not completed | SCRIPT-F08 | Per-User Login Script via `.bash_profile` | Append refresh-command to `~/.bash_profile`, every login refreshes a file |
| 23 | not completed | SCRIPT-F09 | Three-Way Argument-Based Script with Multi-Arg Rejection | `$# > 1` → exit 5, two valid args + usage fallback |
| 24 | not completed | ENV-F01 | System-Wide Environment Variable via `/etc/profile.d` | `/etc/profile.d/sys_tag.sh`, `export SYS_TAG=...`, `printenv` |
| 25 | not completed | LAB | Launch Named Root Container with Port Mapping | `podman run`, `docker run`, `-p`, `--name`, `-it` (8-part lab) |
| 26 | not completed | in-repo | Rootless Container with Bind Mount and systemd Auto-Start | rootless podman, bind mount, user-level systemd unit + linger |
| 27 | not completed | CON-F02 | Build a Custom Container Image with a Containerfile | `podman build -t custom:latest`, push to local registry, rootless run |
| 28 | not completed | CON-F03 | Rootless Container with Port Mapping + systemd Auto-Start | `podman generate systemd --new --files`, `loginctl enable-linger` |
| 29 | not completed | CON-F04 | Rootless Container with Bind Mount + Env Vars + Port Mapping | `-v /host_data01:/container_data01`, `-e ENVIRON=Exam`, `-e KERN=$(uname -r)` |
| 30 | not completed | CON-F05 | Authenticated Pull from `registry.redhat.io` | `podman login registry.redhat.io`, pull `ubi9/ubi` |
| 31 | not completed | CON-F06 | Build a UBI Image from a Single-Line Containerfile | `FROM registry.redhat.io/ubi8/ubi-init`, `podman build -t ubigreeter` |
| 32 | not completed | CON-F07 | Rootless HTTP Container with Bind-Mounted DocumentRoot | `-v /var/www/html:/usr/local/apache2/htdocs:Z` |
| 33 | not completed | CON-F08 | Rootless Database Container with Env Vars + Persistent Data | `MYSQL_ROOT_PASSWORD`, `-v /home/ray/inventory_data:/var/lib/mysql:Z` |
| 34 | not completed | CON-F09 | Rootless Nginx with Custom Config + DocumentRoot Mounts | Two bind mounts: `:Z` html + conf dirs |
| 35 | not completed | CON-F10 | Multi-Mount Rootless Container with Two Bind Mounts + Port | `-v /opt/out:/opt/in:Z -v /opt/send:/opt/receive:Z` |
| 36 | not completed | CON-F11 | Add Both Flathub and RHEL Flatpak Remotes | `flatpak remote-add flathub`, `flatpak remote-add rhel` |
| 37 | not completed | CON-F12 | Install Flatpak Applications (Firefox + VLC + GIMP) | `flatpak install -y flathub org.mozilla.firefox` etc. |
| 38 | not completed | CON-F13 | User-Scoped vs System-Wide Flatpak Installation | `--user` vs `--system` install comparison |
| 39 | not completed | CON-F14 | Remove Flatpak Apps, Prune Runtimes, Remove Remote | `flatpak uninstall`, `--unused`, `remote-delete` |

---

### 📋 Complete Labs by RHCSA v10 Objective (EX200)

> **Exam-prep order.** Every RHCSA lab — README companion repos, in-repo labs under [`labs/`](labs/), and `*-F##` future labs — grouped under the **official Red Hat RHCSA v10 (EX200) objective** it satisfies. Work through objectives **1 → 10** in order; within each objective, labs run foundation → advanced. Items tagged `.RHEL8` / `.RHEL9` are version-scoped variants on the same exam blueprint.
>
> Cross-reference: [Official RHCSA v10 Objectives Index](./rhcsa-v10-exam-objectives.md#official-rhcsa-v10-objectives-index) · [Suggested Learning Path (prerequisite flow)](README.md#-suggested-learning-path)

#### Objective 1: Understand and use essential tools

| # | Status | ID / # | Full Lab Name | Objective |
|---|---|---|---|---|
| 1 | not completed | 01 | Standard Output Redirection | **1.b** I/O redirection |
| 2 | not completed | 02 | Standard Error Redirection | **1.b** I/O redirection |
| 3 | not completed | 03 | Pipe Text Streams | **1.b** I/O redirection |
| 4 | not completed | 04 | Capture Both Output and Error | **1.b** I/O redirection |
| 5 | not completed | 05 | Directory Navigation | **1.a** Shell prompt and correct syntax |
| 6 | not completed | 06 | Listing Files and SELinux Contexts | **1.a** Shell prompt and correct syntax |
| 7 | not completed | 07 | Creating Empty Files and Timestamps | **1.h** Create, delete, copy, and move files and directories |
| 8 | not completed | 08 | Copying Files and Directories | **1.h** Create, delete, copy, and move files and directories |
| 9 | not completed | 09 | Hard and Soft Links | **1.i** Create hard and soft links |
| 10 | not completed | 10 | Moving and Renaming Files | **1.h** Create, delete, copy, and move files and directories |
| 11 | not completed | 11 | Safe Deletion of Files and Directories | **1.h** Create, delete, copy, and move files and directories |
| 12 | not completed | 12 | Creating Nested Directories | **1.h** Create, delete, copy, and move files and directories |
| 13 | not completed | 13 | Creating Command Aliases | **1.a** Shell prompt and correct syntax |
| 14 | not completed | 14 | File Searching with find | **1.a** Shell prompt and correct syntax |
| 15 | not completed | 15 | Instant File Searching with locate | **1.a** Shell prompt and correct syntax |
| 16 | not completed | 16 | Search for a String and Save Output | **1.c** Use grep and regular expressions |
| 17 | not completed | 17 | Find and Save Config Files | **1.c** Use grep and regular expressions |
| 18 | not completed | 18 | Locate Command Documentation | **1.k** Locate, read, and use system documentation |
| 19 | not completed | in-repo | Find Files by Modification Time and Act on Them | **1.a** Shell prompt and correct syntax |
| 20 | not completed | 19 | Concatenating Files with cat | **1.a** Shell prompt and correct syntax |
| 21 | not completed | 20 | Scrolling Through Large Files | **1.a** Shell prompt and correct syntax |
| 22 | not completed | 21 | Monitoring Live Log Files | **1.a** Shell prompt and correct syntax |
| 23 | not completed | 22 | Filtering Text with grep and Regex | **1.c** Use grep and regular expressions |
| 24 | not completed | 23 | Comparing File Differences with diff | **1.a** Shell prompt and correct syntax |
| 25 | not completed | 24 | Stream Editing with sed | **1.a** Shell prompt and correct syntax |
| 26 | not completed | 25 | Extracting Columns with awk | **1.a** Shell prompt and correct syntax |
| 27 | not completed | 26 | Command Mode and Insert Mode in vi | **1.g** Create and edit text files |
| 28 | not completed | 27 | Safely Editing System Databases | **1.g** Create and edit text files |
| 29 | not completed | 28 | Exploring Manual Pages | **1.k** Locate, read, and use system documentation |
| 30 | not completed | 29 | Searching Manuals by Keyword | **1.k** Locate, read, and use system documentation |
| 31 | not completed | 30 | Navigating info Pages | **1.k** Locate, read, and use system documentation |
| 32 | not completed | DOC-F01 | Locate Command Documentation Under `/usr/share/doc` | **1.k** Locate, read, and use system documentation |
| 33 | not completed | 39 | Configure SSH and Key-Based Auth | **1.d** Access remote systems using SSH |
| 34 | not completed | 172 | Proper Use of su vs su - | **1.e** Log in and switch users in multiuser targets |
| 35 | not completed | 193 | Standard File Compression with gzip | **1.f** Archive, compress, unpack, and uncompress files |
| 36 | not completed | 194 | High-Ratio Compression with bzip2 | **1.f** Archive, compress, unpack, and uncompress files |
| 37 | not completed | 195 | Create Standard Archives with tar | **1.f** Archive, compress, unpack, and uncompress files |
| 38 | not completed | 196 | Create Compressed Archives | **1.f** Archive, compress, unpack, and uncompress files |
| 39 | not completed | 197 | Extract Archives | **1.f** Archive, compress, unpack, and uncompress files |
| 40 | not completed | 198 | Preserve Security Contexts in Archives | **1.f** Archive, compress, unpack, and uncompress files |
| 41 | not completed | 40 | Standard File Permissions | **1.j** List, set, and change standard ugo/rwx permissions |
| 42 | not completed | 41 | Changing Ownership | **1.j** List, set, and change standard ugo/rwx permissions |
| 43 | not completed | 42 | SUID Executables | **1.j** List, set, and change standard ugo/rwx permissions |
| 44 | not completed | 43 | Configure SGID and Sticky Bit | **1.j** List, set, and change standard ugo/rwx permissions |
| 45 | not completed | 44 | Immutable File Attribute | **1.j** List, set, and change standard ugo/rwx permissions |
| 46 | not completed | 45 | Append-Only File Attribute | **1.j** List, set, and change standard ugo/rwx permissions |
| 47 | not completed | 46 | Identifying File Attributes | **1.j** List, set, and change standard ugo/rwx permissions |
| 48 | not completed | 180 | Alter Global Default umask | **1.j** List, set, and change standard ugo/rwx permissions |
| 49 | not completed | PERM-F04 | Per-User Default umask via `~/.bashrc` | **1.j** List, set, and change standard ugo/rwx permissions |
| 50 | not completed | FILES-F01 | Find Files by Size Range and Copy Preserving All Attributes | **1.a** Shell prompt and correct syntax |
| 51 | not completed | FILES-F02 | Find Files Owned by a User Within a Size Range | **1.a** Shell prompt and correct syntax |
| 52 | not completed | FILES-F03 | Find Configuration Files by Name and Owner | **1.a** Shell prompt and correct syntax |
| 53 | not completed | FILES-F04 | Find Files Modified More Than 30 Days Ago and Copy with Hierarchy | **1.a** Shell prompt and correct syntax |
| 54 | not completed | FILES-F05 | Find Directories with the SUID Bit Set + Copy with Attributes | **1.a** Shell prompt and correct syntax |
| 55 | not completed | FILES-F06 | Find Directories by Size Range and Save Long Listing | **1.a** Shell prompt and correct syntax |
| 56 | not completed | FILES-F07 | Hard and Symbolic Link Lifecycle Demonstration | **1.i** Create hard and soft links |
| 57 | not completed | TEXT-F01 | Extract Lines Containing a String Preserving Order | **1.c** Use grep and regular expressions |
| 58 | not completed | TEXT-F02 | Find Exact Word Matches with `grep -w` | **1.c** Use grep and regular expressions |
| 59 | not completed | TEXT-F03 | Search Apache Configuration for Listen Directives | **1.c** Use grep and regular expressions |
| 60 | not completed | ARCH-F01 | Create an xz-Compressed Tar Archive | **1.f** Archive, compress, unpack, and uncompress files |
| 61 | not completed | ARCH-F02 | Create an Uncompressed Standard Tar Archive | **1.f** Archive, compress, unpack, and uncompress files |
| 62 | not completed | ARCH-F03 | Restore a Tar Archive into a Specific Destination Directory | **1.f** Archive, compress, unpack, and uncompress files |

#### Objective 2: Create simple shell scripts

| # | Status | ID / # | Full Lab Name | Objective |
|---|---|---|---|---|
| 1 | not completed | 226 | Argument-Based Conditional Script | **2.a** Conditionally execute code |
| 2 | not completed | 227 | Use for Loops for Iteration | **2.b** Use looping constructs |
| 3 | not completed | in-repo | Bidirectional Bash Script with Argument Logic | **2.a** Conditionally execute code |
| 4 | not completed | SCRIPT-F02 | Bash Script: Find Files Matching a Pattern and Print stat | **2.b** Use looping constructs |
| 5 | not completed | SCRIPT-F03 | Bash Script: Create a User Whose Name Comes from a Variable | **2.c** Process script inputs |
| 6 | not completed | SCRIPT-F04 | Countdown Timer Script with Argument or Interactive Prompt | **2.a** Conditionally execute code |
| 7 | not completed | SCRIPT-F05 | Sum of an Unknown Number of Integer Arguments | **2.c** Process script inputs |
| 8 | not completed | SCRIPT-F06 | Find Users by Login Shell and Save the List | **2.d** Processing output of shell commands within a script |
| 9 | not completed | SCRIPT-F07 | Extract Login Shells of the Last 5 Users in `/etc/passwd` | **2.d** Processing output of shell commands within a script |
| 10 | not completed | SCRIPT-F08 | Per-User Login Script via `.bash_profile` | **2.d** Processing output of shell commands within a script |
| 11 | not completed | SCRIPT-F09 | Three-Way Argument-Based Script with Multi-Arg Rejection | **2.a** Conditionally execute code |
| 12 | not completed | ENV-F01 | System-Wide Environment Variable via `/etc/profile.d` | **2.d** Processing output of shell commands within a script |

#### Objective 3: Operate running systems

| # | Status | ID / # | Full Lab Name | Objective |
|---|---|---|---|---|
| 1 | not completed | 85 | Modify GRUB Timeout | **3.c** Interrupt the boot process to gain access |
| 2 | not completed | 86 | Enable Verbose Kernel Messages | **3.c** Interrupt the boot process to gain access |
| 3 | not completed | 87 | Generate New GRUB Config | **3.c** Interrupt the boot process to gain access |
| 4 | not completed | 88 | Reset Root Password via Boot | **3.c** Interrupt the boot process to gain access |
| 5 | not completed | 89 | Chroot into Rescue Filesystem | **3.c** Interrupt the boot process to gain access |
| 6 | not completed | BOOT-F01 | Enable Verbose Boot by Removing `quiet` and `rhgb` | **3.c** Interrupt the boot process to gain access |
| 7 | not completed | USER-F08 | Reset Root Password from GRUB Boot Menu (`rd.break` Path) | **3.c** Interrupt the boot process to gain access |
| 8 | not completed | 90 | Check Default Boot Target | **3.b** Boot systems into different targets manually |
| 9 | not completed | 91 | Change Default Boot Target | **3.b** Boot systems into different targets manually |
| 10 | not completed | 92 | System Reboots and Shutdowns | **3.a** Boot, reboot, and shut down a system normally |
| 11 | not completed | SYSD-F01 | Set the Default Boot Target to `multi-user.target` | **3.b** Boot systems into different targets manually |
| 12 | not completed | 93 | List All System Units | **3.i** Start, stop, and check the status of network services |
| 13 | not completed | 94 | Check Service Status | **3.i** Start, stop, and check the status of network services |
| 14 | not completed | 95 | Start and Stop Services | **3.i** Start, stop, and check the status of network services |
| 15 | not completed | 96 | Enable Services at Boot | **3.i** Start, stop, and check the status of network services |
| 16 | not completed | 97 | Disable Services at Boot | **3.i** Start, stop, and check the status of network services |
| 17 | not completed | 98 | Mask System Services | **3.i** Start, stop, and check the status of network services |
| 18 | not completed | 99 | Create and Manage systemd Unit Files | **3.i** Start, stop, and check the status of network services |
| 19 | not completed | 184 | Audit All Running Processes | **3.d** Identify CPU/memory intensive processes, renice, kill |
| 20 | not completed | 185 | Identify Process Details | **3.d** Identify CPU/memory intensive processes, renice, kill |
| 21 | not completed | 186 | View SELinux Process Contexts | **3.d** Identify CPU/memory intensive processes, renice, kill |
| 22 | not completed | 187 | Real-Time Process Monitoring | **3.d** Identify CPU/memory intensive processes, renice, kill |
| 23 | not completed | 188 | Adjust Process Priority | **3.d** Identify CPU/memory intensive processes, renice, kill |
| 24 | not completed | 189 | Start Processes with Custom Priority | **3.e** Adjust process scheduling |
| 25 | not completed | 190 | Terminate Processes Gracefully | **3.d** Identify CPU/memory intensive processes, renice, kill |
| 26 | not completed | 191 | Force Kill Unresponsive Processes | **3.d** Identify CPU/memory intensive processes, renice, kill |
| 27 | not completed | 192 | Kill Processes by Name | **3.d** Identify CPU/memory intensive processes, renice, kill |
| 28 | not completed | PROC-F01 | Start a Background Process with a Specific nice Value | **3.e** Adjust process scheduling |
| 29 | not completed | PROC-F02 | Renice a Running Process to a Higher Priority | **3.d** Identify CPU/memory intensive processes, renice, kill |
| 30 | not completed | PROC-F03 | Lowest-Priority Background Task on User Login | **3.e** Adjust process scheduling |
| 31 | not completed | PROC-F04 | Clean Termination of a Background Process | **3.d** Identify CPU/memory intensive processes, renice, kill |
| 32 | not completed | 225 | Enable Recommended Tuning Profile | **3.f** Manage tuning profiles |
| 33 | not completed | PERF-F01 | Apply the `virtual-guest` Tuning Profile | **3.f** Manage tuning profiles |
| 34 | not completed | PERF-F02 | Apply a Power-Saving / Virtualization-Balanced Profile | **3.f** Manage tuning profiles |
| 35 | not completed | 100 | Analyze Boot Performance | **3.g** Locate and interpret system log files and journals |
| 36 | not completed | 101 | Query Logs with journalctl | **3.g** Locate and interpret system log files and journals |
| 37 | not completed | 102 | Configure Persistent Journal Logs | **3.h** Preserve system journals |
| 38 | not completed | 103 | Understand Log Routing | **3.g** Locate and interpret system log files and journals |
| 39 | not completed | 104 | Monitor Authentication Logs | **3.g** Locate and interpret system log files and journals |
| 40 | not completed | 105 | Filter systemd Journals by Priority | **3.g** Locate and interpret system log files and journals |
| 41 | not completed | 106 | Service-Specific Journal Logs | **3.g** Locate and interpret system log files and journals |
| 42 | not completed | 212 | SSH and SCP File Transfer | **3.j** Securely transfer files between systems |
| 43 | not completed | SSH-F06 | Secure File Transfer with `scp` Preserving Attributes | **3.j** Securely transfer files between systems |

#### Objective 4: Configure local storage

| # | Status | ID / # | Full Lab Name | Objective |
|---|---|---|---|---|
| 1 | not completed | 110 | Inspect Filesystems | **4.a** List, create, delete partitions on MBR and GPT disks |
| 2 | not completed | 111 | Display Partition Tables | **4.a** List, create, delete partitions on MBR and GPT disks |
| 3 | not completed | 112 | Create MBR Partition with fdisk | **4.a** List, create, delete partitions on MBR and GPT disks |
| 4 | not completed | 113 | Change Partition Types in fdisk | **4.a** List, create, delete partitions on MBR and GPT disks |
| 5 | not completed | 114 | Create GPT Partition with gdisk | **4.a** List, create, delete partitions on MBR and GPT disks |
| 6 | not completed | 115 | Command-Line Partitioning with parted | **4.a** List, create, delete partitions on MBR and GPT disks |
| 7 | not completed | 116 | Format Partition with XFS | **4.f** Add new partitions, logical volumes, and swap non-destructively |
| 8 | not completed | 117 | Format Partition with Ext4 | **4.f** Add new partitions, logical volumes, and swap non-destructively |
| 9 | not completed | 118 | Check Filesystem Consistency | **4.f** Add new partitions, logical volumes, and swap non-destructively |
| 10 | not completed | 119 | Inspect Filesystem Features | **4.f** Add new partitions, logical volumes, and swap non-destructively |
| 11 | not completed | 120 | Create and Activate Swap Space | **4.f** Add new partitions, logical volumes, and swap non-destructively |
| 12 | not completed | STOR-F03 | Create an MBR Partition with ext4 Mounted by LABEL | **4.a** List, create, delete partitions on MBR and GPT disks |
| 13 | not completed | STOR-F04 | Create a Companion LVM-Type Partition on the Same Disk | **4.a** List, create, delete partitions on MBR and GPT disks |
| 14 | not completed | in-repo | Create a Swap Partition by UUID | **4.f** Add new partitions, logical volumes, and swap non-destructively |
| 15 | not completed | in-repo | Create an Ext4 Partition Mounted by LABEL | **4.a** List, create, delete partitions on MBR and GPT disks |
| 16 | not completed | in-repo | Initialize Physical Volumes | **4.b** Create and remove physical volumes |
| 17 | not completed | in-repo | Display Physical Volumes | **4.b** Create and remove physical volumes |
| 18 | not completed | in-repo | Create Volume Group | **4.c** Assign physical volumes to volume groups |
| 19 | not completed | in-repo | Display Volume Groups | **4.c** Assign physical volumes to volume groups |
| 20 | not completed | in-repo | Create Logical Volume | **4.d** Create and delete logical volumes |
| 21 | not completed | in-repo | Display Logical Volumes | **4.d** Create and delete logical volumes |
| 22 | not completed | in-repo | Extend Volume Group | **4.c** Assign physical volumes to volume groups |
| 23 | not completed | in-repo | Extend Logical Volume | **4.d** Create and delete logical volumes |
| 24 | not completed | in-repo | Resize Filesystem After Extend | **4.f** Add new partitions, logical volumes, and swap non-destructively |
| 25 | not completed | in-repo | Remove LVM Components | **4.b** Create and remove physical volumes |
| 26 | not completed | in-repo (LAB) | Create LV `lvol1` (ext4, 280 MB) | **4.d** Create and delete logical volumes |
| 27 | not completed | in-repo | Create LV with XFS Filesystem | **4.d** Create and delete logical volumes |
| 28 | not completed | in-repo | Online Extend an LV and Its Filesystem Without Unmounting | **4.f** Add new partitions, logical volumes, and swap non-destructively |
| 29 | not completed | LVM-F02 | Create an LVM VDO Volume with Thin Provisioning | **4.f** Add new partitions, logical volumes, and swap non-destructively |
| 30 | not completed | LVM-F03 | LV by Extent Count in a VG with Custom PE Size (ext4 variant) | **4.d** Create and delete logical volumes |
| 31 | not completed | LVM-F04 | LV Sized as a Percentage of the VG with XFS + UUID Mount | **4.d** Create and delete logical volumes |
| 32 | not completed | LVM-F05 | LV Sized as a Percentage of Free Space with XFS | **4.d** Create and delete logical volumes |
| 33 | not completed | LVM-F06 | LV with Extent Count + Reserved Free Extents Constraint | **4.d** Create and delete logical volumes |
| 34 | not completed | LVM-F07 | Online Resize LV to a New Total Extent Count + Grow ext4 | **4.f** Add new partitions, logical volumes, and swap non-destructively |
| 35 | not completed | LVM-F08 | Add Extents to an Existing LV + Grow XFS Online | **4.f** Add new partitions, logical volumes, and swap non-destructively |
| 36 | not completed | LVM-F09 | Create Swap from Remaining VG Free Space | **4.f** Add new partitions, logical volumes, and swap non-destructively |
| 37 | not completed | 131 | Mount Filesystem Manually | **4.e** Configure systems to mount file systems at boot by UUID or label |
| 38 | not completed | 132 | Retrieve Filesystem UUIDs | **4.e** Configure systems to mount file systems at boot by UUID or label |
| 39 | not completed | 133 | Configure Persistent Mounts fstab | **4.e** Configure systems to mount file systems at boot by UUID or label |

#### Objective 5: Create and configure file systems

| # | Status | ID / # | Full Lab Name | Objective |
|---|---|---|---|---|
| 1 | not completed | 116 | Format Partition with XFS | **5.a** Create, mount, unmount, and use vfat, ext4, and xfs file systems |
| 2 | not completed | 117 | Format Partition with Ext4 | **5.a** Create, mount, unmount, and use vfat, ext4, and xfs file systems |
| 3 | not completed | in-repo | Create an Ext4 Partition Mounted by LABEL | **5.a** Create, mount, unmount, and use vfat, ext4, and xfs file systems |
| 4 | not completed | in-repo | Create LV with XFS Filesystem | **5.a** Create, mount, unmount, and use vfat, ext4, and xfs file systems |
| 5 | not completed | 131 | Mount Filesystem Manually | **5.a** Create, mount, unmount, and use vfat, ext4, and xfs file systems |
| 6 | not completed | 133 | Configure Persistent Mounts fstab | **5.a** Create, mount, unmount, and use vfat, ext4, and xfs file systems |
| 7 | not completed | 135 | Remount with New Options | **5.a** Create, mount, unmount, and use vfat, ext4, and xfs file systems |
| 8 | not completed | 134 | Mount Network CIFS Shares | **5.b** Mount and unmount network file systems using NFS |
| 9 | not completed | NFS-F01 | NFS Server + AutoFS Direct Map | **5.b** Mount and unmount network file systems using NFS |
| 10 | not completed | NFS-F02 | NFS Home-Directory Export with AutoFS Indirect Map on Login | **5.b** Mount and unmount network file systems using NFS |
| 11 | not completed | NFS-F03 | NFS Static Export with Persistent `/etc/fstab` Mount | **5.b** Mount and unmount network file systems using NFS |
| 12 | not completed | NFS-F04 | Configure a Node as an NFS Server (companion lab) | **5.b** Mount and unmount network file systems using NFS |
| 13 | not completed | 136 | Manage Autofs Service | **5.c.RHEL9** Configure Autofs |
| 14 | not completed | NFS-F05 | AutoFS Indirect Map for Remote Home Dirs with 60s Timeout | **5.c.RHEL9** Configure Autofs |
| 15 | not completed | NFS-F06 | AutoFS Direct Map for `/mnt/shared` with 5-Minute Timeout | **5.c.RHEL9** Configure Autofs |
| 16 | not completed | in-repo | Online Extend an LV and Its Filesystem Without Unmounting | **5.d** Extend existing logical volumes |
| 17 | not completed | LVM-F07 | Online Resize LV to a New Total Extent Count + Grow ext4 | **5.d** Extend existing logical volumes |
| 18 | not completed | LVM-F08 | Add Extents to an Existing LV + Grow XFS Online | **5.d** Extend existing logical volumes |
| 19 | not completed | 43 | Configure SGID and Sticky Bit | **5.e** Create and configure set-GID directories for collaboration |
| 20 | not completed | 182 | Control Group Ownership SGID | **5.e** Create and configure set-GID directories for collaboration |
| 21 | not completed | 183 | Set Up Group-Managed Directory | **5.e** Create and configure set-GID directories for collaboration |
| 22 | not completed | PERM-F01 | Collaborative SGID Directory with Multi-User Write Test | **5.e** Create and configure set-GID directories for collaboration |
| 23 | not completed | PERM-F05 | Collaborative Group Directory with SGID + Sticky Bit | **5.e** Create and configure set-GID directories for collaboration |
| 24 | not completed | LVM-F02 | Create an LVM VDO Volume with Thin Provisioning | **5.e.RHEL8** Configure disk compression |
| 25 | not completed | PERM-F02 | File Copy with Combined Ownership + Permissions + ACL + Future-User Safety | **5.g** Diagnose and correct file permission problems |
| 26 | not completed | PERM-F03 | ACL with Mixed Read/Write/Read-Only Per User | **5.g** Diagnose and correct file permission problems |
| 27 | not completed | PERM-F06 | Restricted Directory Where Owner Has chmod But No rwx | **5.g** Diagnose and correct file permission problems |

#### Objective 6: Deploy, configure, and maintain systems

| # | Status | ID / # | Full Lab Name | Objective |
|---|---|---|---|---|
| 1 | not completed | 199 | Review System-Wide cron Jobs | **6.a** Schedule tasks using at and cron |
| 2 | not completed | 200 | Schedule Tasks with cron | **6.a** Schedule tasks using at and cron |
| 3 | not completed | 201 | Remove User cron Jobs | **6.a** Schedule tasks using at and cron |
| 4 | not completed | 202 | Schedule One-Time Task with at | **6.a** Schedule tasks using at and cron |
| 5 | not completed | 203 | Limit Access to cron | **6.a** Schedule tasks using at and cron |
| 6 | not completed | 204 | Limit Access to at | **6.a** Schedule tasks using at and cron |
| 7 | not completed | 205 | Review the Anacron System | **6.a** Schedule tasks using at and cron |
| 8 | not completed | 206 | Create a Specific cron Job | **6.a** Schedule tasks using at and cron |
| 9 | not completed | 207 | Schedule Software Audit with at | **6.a** Schedule tasks using at and cron |
| 10 | not completed | in-repo (LAB) | Scheduling Jobs (systemd timer, Mon–Fri 2 AM) | **6.a** Schedule tasks using at and cron |
| 11 | not completed | in-repo | User-Level Cron Job with `find -exec` | **6.a** Schedule tasks using at and cron |
| 12 | not completed | CRON-F02 | User Cron Job at 12:45 AM Daily | **6.a** Schedule tasks using at and cron |
| 13 | not completed | CRON-F03 | Recurring User Cron Job Every 2 Minutes | **6.a** Schedule tasks using at and cron |
| 14 | not completed | CRON-F04 | Weekday-Only Cron Job at 5:45 AM | **6.a** Schedule tasks using at and cron |
| 15 | not completed | CRON-F05 | Midnight-Weekend Root Cron Job to Clean Empty Files in `/tmp` | **6.a** Schedule tasks using at and cron |
| 16 | not completed | CRON-F06 | One-Time `at` Job for a Specific Wall-Clock Time | **6.a** Schedule tasks using at and cron |
| 17 | not completed | CRON-F07 | One-Time `at` Job One Hour from Now Writing to journald | **6.a** Schedule tasks using at and cron |
| 18 | not completed | 93 | List All System Units | **6.b** Start/stop services and configure services to start automatically at boot |
| 19 | not completed | 94 | Check Service Status | **6.b** Start/stop services and configure services to start automatically at boot |
| 20 | not completed | 95 | Start and Stop Services | **6.b** Start/stop services and configure services to start automatically at boot |
| 21 | not completed | 96 | Enable Services at Boot | **6.b** Start/stop services and configure services to start automatically at boot |
| 22 | not completed | 97 | Disable Services at Boot | **6.b** Start/stop services and configure services to start automatically at boot |
| 23 | not completed | 98 | Mask System Services | **6.b** Start/stop services and configure services to start automatically at boot |
| 24 | not completed | 99 | Create and Manage systemd Unit Files | **6.b** Start/stop services and configure services to start automatically at boot |
| 25 | not completed | 90 | Check Default Boot Target | **6.c** Configure systems to boot into a specific target automatically |
| 26 | not completed | 91 | Change Default Boot Target | **6.c** Configure systems to boot into a specific target automatically |
| 27 | not completed | SYSD-F01 | Set the Default Boot Target to `multi-user.target` | **6.c** Configure systems to boot into a specific target automatically |
| 28 | not completed | 107 | Configure Timezone and Time Synchronization | **6.d** Configure time service clients |
| 29 | not completed | 108 | Check NTP Sync Status | **6.d** Configure time service clients |
| 30 | not completed | 109 | Configure NTP Time Source | **6.d** Configure time service clients |
| 31 | not completed | TIME-F01 | Set System Timezone via `timedatectl` | **6.d** Configure time service clients |
| 32 | not completed | TIME-F02 | Configure Chrony with a Specific NTP Server | **6.d** Configure time service clients |
| 33 | not completed | 137 | Install Local RPM Package | **6.e** Install and update software packages |
| 34 | not completed | 138 | Upgrade RPM Package | **6.e** Install and update software packages |
| 35 | not completed | 139 | Install New Kernel Safely | **6.e** Install and update software packages |
| 36 | not completed | 140 | Uninstall Package rpm -e | **6.e** Install and update software packages |
| 37 | not completed | 141 | Query All Installed Packages | **6.e** Install and update software packages |
| 38 | not completed | 142 | Query Specific Package Info | **6.e** Install and update software packages |
| 39 | not completed | 143 | List Files Within Package | **6.e** Install and update software packages |
| 40 | not completed | 144 | Identify File Owner | **6.e** Install and update software packages |
| 41 | not completed | 145 | Query Uninstalled RPMs | **6.e** Install and update software packages |
| 42 | not completed | 146 | Verify Package Integrity | **6.e** Install and update software packages |
| 43 | not completed | 147 | System-Wide Verification | **6.e** Install and update software packages |
| 44 | not completed | 148 | Import GPG Key | **6.e** Install and update software packages |
| 45 | not completed | 149 | Check Package Signatures | **6.e** Install and update software packages |
| 46 | not completed | 150 | Configure Repository Access | **6.e** Install and update software packages |
| 47 | not completed | 151 | Install Packages with dnf | **6.e** Install and update software packages |
| 48 | not completed | 152 | Remove Packages with dnf | **6.e** Install and update software packages |
| 49 | not completed | 153 | Update System dnf update | **6.e** Install and update software packages |
| 50 | not completed | 154 | Search for Software | **6.e** Install and update software packages |
| 51 | not completed | 155 | Find File Providers | **6.e** Install and update software packages |
| 52 | not completed | 156 | List dnf Packages | **6.e** Install and update software packages |
| 53 | not completed | 157 | Display Enabled Repositories | **6.e** Install and update software packages |
| 54 | not completed | 158 | View Package Group Info | **6.e** Install and update software packages |
| 55 | not completed | 159 | Install Package Groups | **6.e** Install and update software packages |
| 56 | not completed | 160 | Create Custom YUM Repository | **6.e** Install and update software packages |
| 57 | not completed | 161 | Managing Flatpak | **6.e** Install and update software packages |
| 58 | not completed | in-repo | Install Development Tools Package Group with Output Capture | **6.e** Install and update software packages |
| 59 | not completed | PKG-F02 | Configure Local Repository from Installation ISO Media | **6.e** Install and update software packages |
| 60 | not completed | PKG-F03 | Configure Two HTTP-Hosted Repositories from a Network Source | **6.e** Install and update software packages |
| 61 | not completed | 85 | Modify GRUB Timeout | **6.g** Modify the system bootloader |
| 62 | not completed | 86 | Enable Verbose Kernel Messages | **6.g** Modify the system bootloader |
| 63 | not completed | 87 | Generate New GRUB Config | **6.g** Modify the system bootloader |
| 64 | not completed | BOOT-F01 | Enable Verbose Boot by Removing `quiet` and `rhgb` | **6.g** Modify the system bootloader |

#### Objective 7: Manage basic networking

| # | Status | ID / # | Full Lab Name | Objective |
|---|---|---|---|---|
| 1 | not completed | 31 | Configure a Static IP Address | **7.a** Configure IPv4 and IPv6 addresses |
| 2 | not completed | 32 | Check Network Connectivity | **7.a** Configure IPv4 and IPv6 addresses |
| 3 | not completed | 33 | Display IP and Routing Info | **7.a** Configure IPv4 and IPv6 addresses |
| 4 | not completed | 34 | Inspecting Listening Sockets | **7.a** Configure IPv4 and IPv6 addresses |
| 5 | not completed | 35 | Text-Based Network Config nmtui | **7.a** Configure IPv4 and IPv6 addresses |
| 6 | not completed | 36 | Command-Line Network Config nmcli | **7.a** Configure IPv4 and IPv6 addresses |
| 7 | not completed | NET-F01 | Manual Hostname Configuration by Editing `/etc/hostname` | **7.b** Configure hostname resolution |
| 8 | not completed | NET-F02 | Manual Network Configuration by Editing Connection Files | **7.a** Configure IPv4 and IPv6 addresses |
| 9 | not completed | NET-F03 | Configure Static IPv4 with Specific Host Address | **7.a** Configure IPv4 and IPv6 addresses |
| 10 | not completed | NET-F04 | Configure Static IPv6 Address with DNS Search Domain | **7.a** Configure IPv4 and IPv6 addresses |
| 11 | not completed | NET-F05 | Dual-Stack IPv4 + IPv6 with Local Host Resolution | **7.a** Configure IPv4 and IPv6 addresses |
| 12 | not completed | 37 | Configuring Local Host Resolution | **7.b** Configure hostname resolution |
| 13 | not completed | 38 | Configuring DNS Servers | **7.b** Configure hostname resolution |
| 14 | not completed | SSH-F05 | Configure Local `/etc/hosts` Name Resolution | **7.b** Configure hostname resolution |
| 15 | not completed | 96 | Enable Services at Boot | **7.c** Configure network services to start automatically at boot |
| 16 | not completed | 55 | Inspecting iptables | **7.d** Restrict network access using firewall-cmd / firewall |
| 17 | not completed | 56 | Exploring firewalld Zones | **7.d** Restrict network access using firewall-cmd / firewall |
| 18 | not completed | 57 | Changing Default Firewall Zone | **7.d** Restrict network access using firewall-cmd / firewall |
| 19 | not completed | 58 | Adding Services to Zones | **7.d** Restrict network access using firewall-cmd / firewall |
| 20 | not completed | 59 | Opening Custom Ports | **7.d** Restrict network access using firewall-cmd / firewall |
| 21 | not completed | 60 | Inspect Active Firewall Zones | **7.d** Restrict network access using firewall-cmd / firewall |
| 22 | not completed | 61 | Reassign Interfaces to Zones | **7.d** Restrict network access using firewall-cmd / firewall |
| 23 | not completed | 62 | Allow Services Through Firewall | **7.d** Restrict network access using firewall-cmd / firewall |
| 24 | not completed | 63 | Configure IP Masquerading NAT | **7.d** Restrict network access using firewall-cmd / firewall |
| 25 | not completed | 64 | Configure IP Forwarding | **7.d** Restrict network access using firewall-cmd / firewall |
| 26 | not completed | 65 | Configure Rich Rules | **7.d** Restrict network access using firewall-cmd / firewall |
| 27 | not completed | 66 | Setup Port Forwarding DNAT | **7.d** Restrict network access using firewall-cmd / firewall |
| 28 | not completed | 67 | Configure ICMP Filters | **7.d** Restrict network access using firewall-cmd / firewall |
| 29 | not completed | FW-F01 | Open Multiple Services at Once for Web Hosting | **7.d** Restrict network access using firewall-cmd / firewall |
| 30 | not completed | FW-F02 | Open a Non-Standard SSH Port + Move SSH There | **7.d** Restrict network access using firewall-cmd / firewall |
| 31 | not completed | 219 | Comprehensive firewalld Setup | **7.d** Restrict network access using firewall-cmd / firewall |

#### Objective 8: Manage users and groups

| # | Status | ID / # | Full Lab Name | Objective |
|---|---|---|---|---|
| 1 | not completed | 162 | Inspect Password Database | **8.a** Create, delete, and modify local user accounts |
| 2 | not completed | 163 | Analyze Shadow File | **8.a** Create, delete, and modify local user accounts |
| 3 | not completed | 165 | User & Group Management / Permissions | **8.a** Create, delete, and modify local user accounts |
| 4 | not completed | 166 | Modify Existing Account | **8.a** Create, delete, and modify local user accounts |
| 5 | not completed | 169 | Safely Delete Users | **8.a** Create, delete, and modify local user accounts |
| 6 | not completed | 170 | Disable User Login Without Removing the Account | **8.a** Create, delete, and modify local user accounts |
| 7 | not completed | 171 | Validate User and Group Creation | **8.a** Create, delete, and modify local user accounts |
| 8 | not completed | 178 | Populate Directory Templates | **8.a** Create, delete, and modify local user accounts |
| 9 | not completed | 179 | Manage Shell Environments | **8.a** Create, delete, and modify local user accounts |
| 10 | not completed | 181 | Distribute Documentation via Skel | **8.a** Create, delete, and modify local user accounts |
| 11 | not completed | in-repo | Lock User Account and Capture Regex Evidence | **8.a** Create, delete, and modify local user accounts |
| 12 | not completed | USER-F01 | Group with Fixed GID + User with Primary/Secondary Groups | **8.a** Create, delete, and modify local user accounts |
| 13 | not completed | USER-F02 | User Without Interactive Shell (`nologin`) That Still Authenticates | **8.a** Create, delete, and modify local user accounts |
| 14 | not completed | USER-F03 | User With Explicit (Hand-Built) Home Directory | **8.a** Create, delete, and modify local user accounts |
| 15 | not completed | USER-F06 | Welcome.txt Auto-Created for Every New User via `/etc/skel` | **8.a** Create, delete, and modify local user accounts |
| 16 | not completed | 164 | Modify Default Password Aging | **8.b** Change passwords and adjust password aging |
| 17 | not completed | 168 | Force Password Changes | **8.b** Change passwords and adjust password aging |
| 18 | not completed | USER-F04 | Force Password Change at Next Login | **8.b** Change passwords and adjust password aging |
| 19 | not completed | USER-F05 | Set Hard Account Expiry Date | **8.b** Change passwords and adjust password aging |
| 20 | not completed | USER-F07 | Configure System-Wide Password Aging Policy | **8.b** Change passwords and adjust password aging |
| 21 | not completed | 167 | Advanced Group Management | **8.c** Create, delete, and modify local groups and group memberships |
| 22 | not completed | 182 | Control Group Ownership SGID | **8.c** Create, delete, and modify local groups and group memberships |
| 23 | not completed | 183 | Set Up Group-Managed Directory | **8.c** Create, delete, and modify local groups and group memberships |
| 24 | not completed | 172 | Proper Use of su vs su - | **8.d** Configure superuser access |
| 25 | not completed | 173 | Limit Access to su PAM | **8.d** Configure superuser access |
| 26 | not completed | 174 | Configure Custom Administrators | **8.d** Configure superuser access |
| 27 | not completed | 175 | Granular sudo Privileges | **8.d** Configure superuser access |
| 28 | not completed | 176 | Limit root Logins | **8.d** Configure superuser access |
| 29 | not completed | 177 | Restrict Root to Single Console | **8.d** Configure superuser access |
| 30 | not completed | SUDO-F01 | Full Sudo for a User + NOPASSWD for an Entire Group | **8.d** Configure superuser access |
| 31 | not completed | SUDO-F02 | Granular Sudo: Allow `passwd` Except Root Password Changes | **8.d** Configure superuser access |
| 32 | not completed | SUDO-F03 | Privileged User with Account Expiry | **8.d** Configure superuser access |

#### Objective 9: Manage security

| # | Status | ID / # | Full Lab Name | Objective |
|---|---|---|---|---|
| 1 | not completed | 55 | Inspecting iptables | **9.a** Configure firewall settings |
| 2 | not completed | 56 | Exploring firewalld Zones | **9.a** Configure firewall settings |
| 3 | not completed | 57 | Changing Default Firewall Zone | **9.a** Configure firewall settings |
| 4 | not completed | 58 | Adding Services to Zones | **9.a** Configure firewall settings |
| 5 | not completed | 59 | Opening Custom Ports | **9.a** Configure firewall settings |
| 6 | not completed | 60 | Inspect Active Firewall Zones | **9.a** Configure firewall settings |
| 7 | not completed | 61 | Reassign Interfaces to Zones | **9.a** Configure firewall settings |
| 8 | not completed | 62 | Allow Services Through Firewall | **9.a** Configure firewall settings |
| 9 | not completed | 63 | Configure IP Masquerading NAT | **9.a** Configure firewall settings |
| 10 | not completed | 64 | Configure IP Forwarding | **9.a** Configure firewall settings |
| 11 | not completed | 65 | Configure Rich Rules | **9.a** Configure firewall settings |
| 12 | not completed | 66 | Setup Port Forwarding DNAT | **9.a** Configure firewall settings |
| 13 | not completed | 67 | Configure ICMP Filters | **9.a** Configure firewall settings |
| 14 | not completed | FW-F01 | Open Multiple Services at Once for Web Hosting | **9.a** Configure firewall settings |
| 15 | not completed | FW-F02 | Open a Non-Standard SSH Port + Move SSH There | **9.a** Configure firewall settings |
| 16 | not completed | 219 | Comprehensive firewalld Setup | **9.a** Configure firewall settings |
| 17 | not completed | 47 | Check ACL Support | **9.b.RHEL8** Create and use file access control lists |
| 18 | not completed | 48 | Viewing ACLs | **9.b.RHEL8** Create and use file access control lists |
| 19 | not completed | 49 | Modifying ACLs | **9.b.RHEL8** Create and use file access control lists |
| 20 | not completed | 50 | Denying Access via ACLs | **9.b.RHEL8** Create and use file access control lists |
| 21 | not completed | 51 | Default Directory ACLs | **9.b.RHEL8** Create and use file access control lists |
| 22 | not completed | 52 | ACL Masks | **9.b.RHEL8** Create and use file access control lists |
| 23 | not completed | 53 | Removing ACLs | **9.b.RHEL8** Create and use file access control lists |
| 24 | not completed | PERM-F04 | Per-User Default umask via `~/.bashrc` | **9.b.RHEL9** Manage default file permissions |
| 25 | not completed | 180 | Alter Global Default umask | **9.b.RHEL9** Manage default file permissions |
| 26 | not completed | 39 | Configure SSH and Key-Based Auth | **9.c** Configure key-based authentication for SSH |
| 27 | not completed | SSH-F01 | Configure SSH to Listen on a Custom Port | **9.c** Configure key-based authentication for SSH |
| 28 | not completed | SSH-F02 | Permit Root SSH Login with Authentication-Failure Lockout | **9.c** Configure key-based authentication for SSH |
| 29 | not completed | SSH-F03 | Passwordless SSH from Root to Remote Root | **9.c** Configure key-based authentication for SSH |
| 30 | not completed | SSH-F04 | Key-Based SSH from a User to a Remote Root on a Custom Port | **9.c** Configure key-based authentication for SSH |
| 31 | not completed | 208 | Generate a GPG Key Pair | **9.c** Configure key-based authentication for SSH |
| 32 | not completed | 209 | Encrypt a File with GPG | **9.c** Configure key-based authentication for SSH |
| 33 | not completed | 210 | Decrypt a GPG File | **9.c** Configure key-based authentication for SSH |
| 34 | not completed | 211 | Share and Verify Public Keys | **9.c** Configure key-based authentication for SSH |
| 35 | not completed | 78 | Managing SELinux Modes | **9.d** Set enforcing and permissive modes for SELinux |
| 36 | not completed | SEL-F03 | Set SELinux to Permissive Mode Persistently | **9.d** Set enforcing and permissive modes for SELinux |
| 37 | not completed | 79 | Viewing SELinux Contexts | **9.e** List and identify SELinux file and process context |
| 38 | not completed | 186 | View SELinux Process Contexts | **9.e** List and identify SELinux file and process context |
| 39 | not completed | 83 | SELinux User Mapping | **9.e** List and identify SELinux file and process context |
| 40 | not completed | 80 | Temporary Context Changes | **9.e** List and identify SELinux file and process context |
| 41 | not completed | 81 | Persistent Context Restoration | **9.f** Restore default file contexts |
| 42 | not completed | in-repo | Apply Recursive SELinux Contexts to a New Directory | **9.f** Restore default file contexts |
| 43 | not completed | SEL-F04 | Apply Recursive SELinux Context from a Reference Directory | **9.f** Restore default file contexts |
| 44 | not completed | SEL-F02 | Add a Custom HTTP Port to the SELinux Policy Database | **9.ex.RHEL9** Manage SELinux Ports |
| 45 | not completed | 82 | Toggling SELinux Booleans | **9.g** Use boolean settings to modify system SELinux settings |
| 46 | not completed | SEL-F06 | Toggle the `httpd_can_network_connect` Boolean Persistently | **9.g** Use boolean settings to modify system SELinux settings |
| 47 | not completed | 84 | Troubleshooting SELinux | **9.h** Diagnose and address routine SELinux policy violations |
| 48 | not completed | 220 | PAM and SELinux with FTP | **9.h** Diagnose and address routine SELinux policy violations |
| 49 | not completed | 72 | Explore PAM Config Files | **9.h** Diagnose and address routine SELinux policy violations |
| 50 | not completed | 73 | Read PAM Module Documentation | **9.h** Diagnose and address routine SELinux policy violations |
| 51 | not completed | 74 | Implement Password Complexity | **9.h** Diagnose and address routine SELinux policy violations |
| 52 | not completed | 75 | Configure PAM to Limit root Access | **9.h** Diagnose and address routine SELinux policy violations |
| 53 | not completed | 76 | Use PAM to Limit User Access | **9.h** Diagnose and address routine SELinux policy violations |
| 54 | not completed | 77 | Restrict Service Access by User List | **9.h** Diagnose and address routine SELinux policy violations |
| 55 | not completed | 217 | Monitor Security Updates | **9.h** Diagnose and address routine SELinux policy violations |
| 56 | not completed | 68 | Verify TCP Wrappers Support | **9.a** Configure firewall settings |
| 57 | not completed | 69 | Restrict Access via hosts.deny | **9.a** Configure firewall settings |
| 58 | not completed | 70 | Allow Specific Access via hosts.allow | **9.a** Configure firewall settings |
| 59 | not completed | 71 | Configure TCP Wrappers for FTP | **9.a** Configure firewall settings |
| 60 | not completed | 216 | Service Isolation Bastion Host | **9.a** Configure firewall settings |
| 61 | not completed | 218 | Build a Bastion Server | **9.a** Configure firewall settings |

#### Objective 10: Manage containers

| # | Status | ID / # | Full Lab Name | Objective |
|---|---|---|---|---|
| 1 | not completed | CON-F05 | Authenticated Pull from `registry.redhat.io` | **10.a** Find and retrieve container images from a remote registry |
| 2 | not completed | CON-F06 | Build a UBI Image from a Single-Line Containerfile | **10.b** Inspect container images · **10.cx.RHEL9** Build from Containerfile |
| 3 | not completed | CON-F02 | Build a Custom Container Image with a Containerfile | **10.b** Inspect container images · **10.cx.RHEL9** Build from Containerfile |
| 4 | not completed | LAB | Launch Named Root Container with Port Mapping | **10.c** podman/skopeo · **10.d** Run, start, stop, list |
| 5 | not completed | in-repo | Rootless Container with Bind Mount and systemd Auto-Start | **10.d** Run, start, stop, list · **10.f** systemd auto-start · **10.g** persistent storage |
| 6 | not completed | CON-F03 | Rootless Container with Port Mapping + systemd Auto-Start | **10.d** Run, start, stop, list · **10.f** systemd auto-start |
| 7 | not completed | CON-F04 | Rootless Container with Bind Mount + Env Vars + Port Mapping | **10.d** Run, start, stop, list · **10.f** systemd auto-start · **10.g** persistent storage |
| 8 | not completed | CON-F07 | Rootless HTTP Container with Bind-Mounted DocumentRoot | **10.e** Run a service inside a container · **10.g** persistent storage |
| 9 | not completed | CON-F08 | Rootless Database Container with Env Vars + Persistent Data | **10.e** Run a service inside a container · **10.g** persistent storage |
| 10 | not completed | CON-F09 | Rootless Nginx with Custom Config + DocumentRoot Mounts | **10.e** Run a service inside a container · **10.g** persistent storage |
| 11 | not completed | CON-F10 | Multi-Mount Rootless Container with Two Bind Mounts + Port | **10.g** Attach persistent storage to a container |
| 12 | not completed | 161 | Managing Flatpak | **10.c** Perform container management using podman and skopeo |
| 13 | not completed | CON-F11 | Add Both Flathub and RHEL Flatpak Remotes | **10.c** Perform container management using podman and skopeo |
| 14 | not completed | CON-F12 | Install Flatpak Applications (Firefox + VLC + GIMP) | **10.c** Perform container management using podman and skopeo |
| 15 | not completed | CON-F13 | User-Scoped vs System-Wide Flatpak Installation | **10.c** Perform container management using podman and skopeo |
| 16 | not completed | CON-F14 | Remove Flatpak Apps, Prune Runtimes, Remove Remote | **10.c** Perform container management using podman and skopeo |

> **Labs outside the RHCSA exam blueprint.** The following labs in this repo are **not** on the official RHCSA v10 objectives and are optional enrichment only: **213** Network Troubleshooting · **214** Command-Line Web and FTP Testing · **215** Command-Line Email Testing · **221–224** Apache web services · **WEB-F01–WEB-F05** Apache future labs · **54** NFSv4 ACLs · **5.f.RHEL8** layered storage (no dedicated lab yet).

---

### 🖥 Shells, Terminals & Redirection (README Labs 01–04)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 01 | Standard Output Redirection | [01a RHCSA](lab-01a-stdout-redirection-rhcsa/) · [01b Ansible](lab-01b-stdout-redirection-ansible/) · [01c Verify](lab-01c-stdout-redirection-verify/) |
| not completed | 02 | Standard Error Redirection | [02a RHCSA](lab-02a-stderr-redirection-rhcsa/) · [02b Ansible](lab-02b-stderr-redirection-ansible/) · [02c Verify](lab-02c-stderr-redirection-verify/) |
| not completed | 03 | Pipe Text Streams | [03a RHCSA](lab-03a-pipe-text-streams-rhcsa/) · [03b Ansible](lab-03b-pipe-text-streams-ansible/) · [03c Verify](lab-03c-pipe-text-streams-verify/) |
| not completed | 04 | Capture Both Output and Error | [04a RHCSA](lab-04a-capture-both-output-error-rhcsa/) · [04b Ansible](lab-04b-capture-both-output-error-ansible/) · [04c Verify](lab-04c-capture-both-output-error-verify/) |

---

### 🔧 Essential Tools & File Operations (README Labs 05–18)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 00 | Ansible Control Node Setup | [00a RHCSA](lab-00a-ansible-control-node-setup-rhcsa/) · [00b Ansible](lab-00b-ansible-control-node-setup-ansible/) · [00c Verify](lab-00c-ansible-control-node-setup-verify/) |
| not completed | 05 | Directory Navigation | [05a RHCSA](lab-05a-directory-navigation-rhcsa/) · [05b Ansible](lab-05b-directory-navigation-ansible/) · [05c Verify](lab-05c-directory-navigation-verify/) |
| not completed | 06 | Listing Files and SELinux Contexts | [06a RHCSA](lab-06a-listing-files-selinux-rhcsa/) · [06b Ansible](lab-06b-listing-files-selinux-ansible/) · [06c Verify](lab-06c-listing-files-selinux-verify/) |
| not completed | 07 | Creating Empty Files and Timestamps | [07a RHCSA](lab-07a-touch-timestamps-rhcsa/) · [07b Ansible](lab-07b-touch-timestamps-ansible/) · [07c Verify](lab-07c-touch-timestamps-verify/) |
| not completed | 08 | Copying Files and Directories | [08a RHCSA](lab-08a-copying-files-directories-rhcsa/) · [08b Ansible](lab-08b-copying-files-directories-ansible/) · [08c Verify](lab-08c-copying-files-directories-verify/) |
| not completed | 09 | Hard and Soft Links | [09a RHCSA](lab-09a-hard-and-soft-links-rhcsa/) · [09b Ansible](lab-09b-hard-and-soft-links-ansible/) · [09c Verify](lab-09c-hard-and-soft-links-verify/) |
| not completed | 10 | Moving and Renaming Files | [10a RHCSA](lab-10a-moving-renaming-files-rhcsa/) · [10b Ansible](lab-10b-moving-renaming-files-ansible/) · [10c Verify](lab-10c-moving-renaming-files-verify/) |
| not completed | 11 | Safe Deletion of Files and Directories | [11a RHCSA](lab-11a-removing-files-rhcsa/) · [11b Ansible](lab-11b-removing-files-ansible/) · [11c Verify](lab-11c-removing-files-verify/) |
| not completed | 12 | Creating Nested Directories | [12a RHCSA](lab-12a-creating-nested-directories-rhcsa/) · [12b Ansible](lab-12b-creating-nested-directories-ansible/) · [12c Verify](lab-12c-creating-nested-directories-verify/) |
| not completed | 13 | Creating Command Aliases | [13a RHCSA](lab-13a-creating-command-aliases-rhcsa/) · [13b Ansible](lab-13b-creating-command-aliases-ansible/) · [13c Verify](lab-13c-creating-command-aliases-verify/) |
| not completed | 14 | File Searching with find | [14a RHCSA](lab-14a-searching-with-find-rhcsa/) · [14b Ansible](lab-14b-searching-with-find-ansible/) · [14c Verify](lab-14c-searching-with-find-verify/) |
| not completed | 15 | Instant File Searching with locate | [15a RHCSA](lab-15a-searching-with-locate-rhcsa/) · [15b Ansible](lab-15b-searching-with-locate-ansible/) · [15c Verify](lab-15c-searching-with-locate-verify/) |
| not completed | 16 | Search for a String and Save Output | <https://github.com/kelvintechnical/search-string-save-output> |
| not completed | 17 | Find and Save Config Files | <https://github.com/kelvintechnical/find-save-config-files> |
| not completed | 18 | Locate Command Documentation | <https://github.com/kelvintechnical/locate-command-docs> |
| not completed | — | Find Files by Modification Time and Act on Them (in-repo) | [`labs/find-files-by-mtime/`](labs/find-files-by-mtime/) |

**Future Labs (planned — from [`future_labs.txt`](future_labs.txt)):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | FILES-F01 | Find Files by Size Range and Copy Preserving All Attributes | `find /etc -type f -size +5M -size -10M -exec cp --preserve=ownership,mode,timestamps,context {} /find/largefiles/ \;` — prove with `stat -c '%A %U:%G %y'` |
| not completed | FILES-F02 | Find Files Owned by a User Within a Size Range | `find / -xdev -user linda -type f -size +3M -size -50M 2>/dev/null -exec cp -a {} /root/linda-files/ \;` — suppresses permission-denied noise |
| not completed | FILES-F03 | Find Configuration Files by Name and Owner | `find /etc -type f -name '*.conf' -user root > /root/config_files` — verify with `wc -l` and spot-check |
| not completed | FILES-F04 | Find Files Modified More Than 30 Days Ago and Copy with Hierarchy | `find /etc -type f -mtime +30 -exec cp --parents --preserve=all {} /tmp/etc_backup/ \;` — `--parents` preserves the directory layout |
| not completed | FILES-F05 | Find Directories with the SUID Bit Set + Copy with Attributes | `find / -xdev -type d -perm -4000 2>/dev/null -exec cp -a {} /security_backup/ \;` — security audits and forensic copies |
| not completed | FILES-F06 | Find Directories by Size Range and Save Long Listing | `find / -xdev -type d -size +50k -size -100k 2>/dev/null \| xargs ls -ld > /root/moderate_dir_list.txt` — note `find` reports *directory entry size*, not recursive contents size |
| not completed | FILES-F07 | Hard and Symbolic Link Lifecycle Demonstration | `touch report.txt`, `ln report.txt report_hard.txt`, `ln -s report.txt report_symlink.txt`, `rm report.txt` — hard link still has data but symlink is now dangling |

---

### 📄 Text File Management (README Labs 19–27)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 19 | Concatenating Files with cat | <https://github.com/kelvintechnical/concactenating-files-with-cat> |
| not completed | 20 | Scrolling Through Large Files | <https://github.com/kelvintechnical/less-more-scrolling> |
| not completed | 21 | Monitoring Live Log Files | <https://github.com/kelvintechnical/tail-f-live-logs> |
| not completed | 22 | Filtering Text with grep and Regex | <https://github.com/kelvintechnical/grep-regex> |
| not completed | 23 | Comparing File Differences with diff | <https://github.com/kelvintechnical/diff-comparing-files> |
| not completed | 24 | Stream Editing with sed | <https://github.com/kelvintechnical/sed-stream-editor> |
| not completed | 25 | Extracting Columns with awk | <https://github.com/kelvintechnical/awk-columns> |
| not completed | 26 | Command Mode and Insert Mode in vi | <https://github.com/kelvintechnical/vi-editor> |
| not completed | 27 | Safely Editing System Databases | <https://github.com/kelvintechnical/vipw-vigr-safe-editing> |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | TEXT-F01 | Extract Lines Containing a String Preserving Order | `grep 'bin' /etc/passwd > /root/bin_lines` — prove line order matches source with `grep -n` |
| not completed | TEXT-F02 | Find Exact Word Matches with `grep -w` | `grep -wE 'bin' /etc/passwd > /root/bin_users.txt` — `-w` prevents matches inside `sbin`, `binary`, `roundbin` |
| not completed | TEXT-F03 | Search Apache Configuration for Listen Directives | `grep '^Listen' /etc/httpd/conf/httpd.conf > /root/httpd_listen.txt` — `^` excludes commented-out lines |

---

### 📖 Documentation Tools (README Labs 28–30)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 28 | Exploring Manual Pages | <https://github.com/kelvintechnical/man-pages-exploration> |
| not completed | 29 | Searching Manuals by Keyword | <https://github.com/kelvintechnical/whatis-apropos-keyword-search> |
| not completed | 30 | Navigating info Pages | <https://github.com/kelvintechnical/info-pages-navigation> |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | DOC-F01 | Locate Command Documentation Under `/usr/share/doc` | `find /usr/share/doc -iname '*passwd*'`, display path of one matching file, `less`/`cat` to confirm, prove package owns it with `rpm -qf` |

---

### 🌐 Networking (README Labs 31–39)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 31 | Configure a Static IP Address | [31a RHCSA](lab-31a-static-ip-nmcli-rhcsa/) · [31b Ansible](lab-31b-static-ip-nmcli-ansible/) · [31c Verify](lab-31c-static-ip-nmcli-verify/) |
| not completed | 32 | Check Network Connectivity | [32a RHCSA](lab-32a-ping-traceroute-rhcsa/) · [32b Ansible](lab-32b-ping-traceroute-ansible/) · [32c Verify](lab-32c-ping-traceroute-verify/) |
| not completed | 33 | Display IP and Routing Info | [33a RHCSA](lab-33a-ip-addr-route-show-rhcsa/) · [33b Ansible](lab-33b-ip-addr-route-show-ansible/) · [33c Verify](lab-33c-ip-addr-route-show-verify/) |
| not completed | 34 | Inspecting Listening Sockets | [34a RHCSA](lab-34a-ss-listening-sockets-rhcsa/) · [34b Ansible](lab-34b-ss-listening-sockets-ansible/) · [34c Verify](lab-34c-ss-listening-sockets-verify/) |
| not completed | 35 | Text-Based Network Config nmtui | [35a RHCSA](lab-35a-nmtui-tui-config-rhcsa/) · [35b Ansible](lab-35b-nmtui-tui-config-ansible/) · [35c Verify](lab-35c-nmtui-tui-config-verify/) |
| not completed | 36 | Command-Line Network Config nmcli | [36a RHCSA](lab-36a-nmcli-cli-config-rhcsa/) · [36b Ansible](lab-36b-nmcli-cli-config-ansible/) · [36c Verify](lab-36c-nmcli-cli-config-verify/) |
| not completed | 37 | Configuring Local Host Resolution | [37a RHCSA](lab-37a-etc-hosts-resolution-rhcsa/) · [37b Ansible](lab-37b-etc-hosts-resolution-ansible/) · [37c Verify](lab-37c-etc-hosts-resolution-verify/) |
| not completed | 38 | Configuring DNS Servers | [38a RHCSA](lab-38a-resolv-conf-dns-rhcsa/) · [38b Ansible](lab-38b-resolv-conf-dns-ansible/) · [38c Verify](lab-38c-resolv-conf-dns-verify/) |
| not completed | 39 | Configure SSH and Key-Based Auth | [39a RHCSA](lab-39a-ssh-key-auth-rhcsa/) · [39b Ansible](lab-39b-ssh-key-auth-ansible/) · [39c Verify](lab-39c-ssh-key-auth-verify/) |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | NET-F01 | Manual Hostname Configuration by Editing `/etc/hostname` | Set the hostname *without* `hostnamectl`: write the FQDN directly into `/etc/hostname`, refresh the shell prompt, verify after reboot |
| not completed | NET-F02 | Manual Network Configuration by Editing Connection Files | Hand-edit the keyfile under `/etc/NetworkManager/system-connections/` or `/etc/sysconfig/network-scripts/ifcfg-*`, `nmcli connection reload`, prove persistence |
| not completed | NET-F03 | Configure Static IPv4 with Specific Host Address | `nmcli con mod ens-XX ipv4.addresses 192.168.50.10/24`, `ipv4.gateway 192.168.50.1`, `ipv4.dns "8.8.8.8 8.8.4.4"`, `ipv4.method manual`, `connection.autoconnect yes` |
| not completed | NET-F04 | Configure Static IPv6 Address with DNS Search Domain | `ipv6.addresses fd02::42/64`, `ipv6.gateway fd02::1`, `ipv6.dns fd02::222`, `ipv6.dns-search example.local`, hostname `node1.example.local` |
| not completed | NET-F05 | Dual-Stack IPv4 + IPv6 with Local Host Resolution | Both `192.168.56.25/24` and `fd12:3456:789a:1::25/64` on one interface, hostname `node1.lab3.example.net`, `/etc/hosts` entry so short + FQDN both resolve |

---

### 🔒 Permissions, Special Bits & ACLs (README Labs 40–54)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 40 | Standard File Permissions | [40a RHCSA](lab-40a-chmod-standard-perms-rhcsa/) · [40b Ansible](lab-40b-chmod-standard-perms-ansible/) · [40c Verify](lab-40c-chmod-standard-perms-verify/) |
| not completed | 41 | Changing Ownership | [41a RHCSA](lab-41a-chown-chgrp-ownership-rhcsa/) · [41b Ansible](lab-41b-chown-chgrp-ownership-ansible/) · [41c Verify](lab-41c-chown-chgrp-ownership-verify/) |
| not completed | 42 | SUID Executables | [42a RHCSA](lab-42a-suid-executable-rhcsa/) · [42b Ansible](lab-42b-suid-executable-ansible/) · [42c Verify](lab-42c-suid-executable-verify/) |
| not completed | 43 | Configure SGID and Sticky Bit | [43a RHCSA](lab-43a-sgid-sticky-bit-rhcsa/) · [43b Ansible](lab-43b-sgid-sticky-bit-ansible/) · [43c Verify](lab-43c-sgid-sticky-bit-verify/) |
| not completed | 44 | Immutable File Attribute | [44a RHCSA](lab-44a-chattr-immutable-rhcsa/) · [44b Ansible](lab-44b-chattr-immutable-ansible/) · [44c Verify](lab-44c-chattr-immutable-verify/) |
| not completed | 45 | Append-Only File Attribute | [45a RHCSA](lab-45a-chattr-append-only-rhcsa/) · [45b Ansible](lab-45b-chattr-append-only-ansible/) · [45c Verify](lab-45c-chattr-append-only-verify/) |
| not completed | 46 | Identifying File Attributes | [46a RHCSA](lab-46a-lsattr-extended-attrs-rhcsa/) · [46b Ansible](lab-46b-lsattr-extended-attrs-ansible/) · [46c Verify](lab-46c-lsattr-extended-attrs-verify/) |
| not completed | 47 | Check ACL Support | [47a RHCSA](lab-47a-acl-mount-option-rhcsa/) · [47b Ansible](lab-47b-acl-mount-option-ansible/) · [47c Verify](lab-47c-acl-mount-option-verify/) |
| not completed | 48 | Viewing ACLs | [48a RHCSA](lab-48a-getfacl-view-acl-rhcsa/) · [48b Ansible](lab-48b-getfacl-view-acl-ansible/) · [48c Verify](lab-48c-getfacl-view-acl-verify/) |
| not completed | 49 | Modifying ACLs | [49a RHCSA](lab-49a-setfacl-modify-rhcsa/) · [49b Ansible](lab-49b-setfacl-modify-ansible/) · [49c Verify](lab-49c-setfacl-modify-verify/) |
| not completed | 50 | Denying Access via ACLs | [50a RHCSA](lab-50a-setfacl-deny-rhcsa/) · [50b Ansible](lab-50b-setfacl-deny-ansible/) · [50c Verify](lab-50c-setfacl-deny-verify/) |
| not completed | 51 | Default Directory ACLs | [51a RHCSA](lab-51a-default-acl-inherit-rhcsa/) · [51b Ansible](lab-51b-default-acl-inherit-ansible/) · [51c Verify](lab-51c-default-acl-inherit-verify/) |
| not completed | 52 | ACL Masks | [52a RHCSA](lab-52a-acl-masks-rhcsa/) · [52b Ansible](lab-52b-acl-masks-ansible/) · [52c Verify](lab-52c-acl-masks-verify/) |
| not completed | 53 | Removing ACLs | [53a RHCSA](lab-53a-setfacl-remove-rhcsa/) · [53b Ansible](lab-53b-setfacl-remove-ansible/) · [53c Verify](lab-53c-setfacl-remove-verify/) |
| not completed | 54 | NFSv4 ACLs | [54a RHCSA](lab-54a-nfs4-acl-rhcsa/) · [54b Ansible](lab-54b-nfs4-acl-ansible/) · [54c Verify](lab-54c-nfs4-acl-verify/) |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | PERM-F01 | Collaborative SGID Directory with Multi-User Write Test | `mkdir /sdata`, `chown root:group30`, `chmod 2770`, add `user60` + `user80` to `group30`, prove a file created by `user60` can be edited *and* not deleted by `user80` |
| not completed | PERM-F02 | File Copy with Combined Ownership + Permissions + ACL + Future-User Safety | `cp /etc/fstab /var/tmp`, `chown root:admins`, `chmod 644`, `setfacl -m u:harry:rw,u:bruce:r,u:natasha:---`, prove "other" still has read so future users automatically get access |
| not completed | PERM-F03 | ACL with Mixed Read/Write/Read-Only Per User | `cp /etc/hosts /srv/project/hosts_copy`, `setfacl u:emma:rw,u:liam:rw,u:sophie:r,m::rw`, default ACL on parent dir for inheritance, verify with `getfacl` and `sudo -u sophie tee` test |
| not completed | PERM-F04 | Per-User Default umask via `~/.bashrc` | `echo 'umask 0577' >> /home/bruce/.bashrc` — files become `-r--------`, directories `dr-x------` for owner only, prove with `touch ~/test && stat -c '%a' ~/test` showing 400 |
| not completed | PERM-F05 | Collaborative Group Directory with SGID + Sticky Bit | `mkdir /data/engineers`, `chown root:engineers`, `chmod 3770` — SGID for group inheritance, sticky for owner-only delete |
| not completed | PERM-F06 | Restricted Directory Where Owner Has chmod But No rwx | `mkdir /data/engineers`, `chown tom:engineers`, `chmod g+rwx,o-rwx,u-rwx` — prove tom can still `chmod` because owner even though he cannot read or write |

---

### 🔥 Firewall (firewalld) (README Labs 55–67)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 55 | Inspecting iptables | [55a RHCSA](lab-55a-iptables-inspect-rhcsa/) · [55b Ansible](lab-55b-iptables-inspect-ansible/) · [55c Verify](lab-55c-iptables-inspect-verify/) |
| not completed | 56 | Exploring firewalld Zones | [56a RHCSA](lab-56a-firewalld-zones-rhcsa/) · [56b Ansible](lab-56b-firewalld-zones-ansible/) · [56c Verify](lab-56c-firewalld-zones-verify/) |
| not completed | 57 | Changing Default Firewall Zone | [57a RHCSA](lab-57a-firewalld-default-zone-rhcsa/) · [57b Ansible](lab-57b-firewalld-default-zone-ansible/) · [57c Verify](lab-57c-firewalld-default-zone-verify/) |
| not completed | 58 | Adding Services to Zones | [58a RHCSA](lab-58a-firewalld-add-service-rhcsa/) · [58b Ansible](lab-58b-firewalld-add-service-ansible/) · [58c Verify](lab-58c-firewalld-add-service-verify/) |
| not completed | 59 | Opening Custom Ports | [59a RHCSA](lab-59a-firewalld-add-port-rhcsa/) · [59b Ansible](lab-59b-firewalld-add-port-ansible/) · [59c Verify](lab-59c-firewalld-add-port-verify/) |
| not completed | 60 | Inspect Active Firewall Zones | [60a RHCSA](lab-60a-firewalld-active-zones-rhcsa/) · [60b Ansible](lab-60b-firewalld-active-zones-ansible/) · [60c Verify](lab-60c-firewalld-active-zones-verify/) |
| not completed | 61 | Reassign Interfaces to Zones | <https://github.com/kelvintechnical/reassign-interfaces-zones> |
| not completed | 62 | Allow Services Through Firewall | <https://github.com/kelvintechnical/firewall-allow-services> |
| not completed | 63 | Configure IP Masquerading NAT | <https://github.com/kelvintechnical/ip-masquerading-nat> |
| not completed | 64 | Configure IP Forwarding | <https://github.com/kelvintechnical/ip-forwarding> |
| not completed | 65 | Configure Rich Rules | <https://github.com/kelvintechnical/firewalld-rich-rules> |
| not completed | 66 | Setup Port Forwarding DNAT | <https://github.com/kelvintechnical/port-forwarding-dnat> |
| not completed | 67 | Configure ICMP Filters | <https://github.com/kelvintechnical/icmp-filters> |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | FW-F01 | Open Multiple Services at Once for Web Hosting | `firewall-cmd --permanent --add-service={ssh,http,https}`, reload, verify with `--list-services`, prove external connectivity from a second host |
| not completed | FW-F02 | Open a Non-Standard SSH Port + Move SSH There | `firewalld --add-port=88/tcp --permanent`, then `sshd_config Port 88`, `semanage port -a -t ssh_port_t -p tcp 88`, restart sshd, prove `ssh -p 88` works while port 22 is closed |

---

### 🔐 TCP Wrappers & PAM (README Labs 68–77)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 68 | Verify TCP Wrappers Support | <https://github.com/kelvintechnical/tcp-wrappers-support> |
| not completed | 69 | Restrict Access via hosts.deny | <https://github.com/kelvintechnical/hosts-deny-restrictions> |
| not completed | 70 | Allow Specific Access via hosts.allow | <https://github.com/kelvintechnical/hosts-allow-access> |
| not completed | 71 | Configure TCP Wrappers for FTP | <https://github.com/kelvintechnical/tcp-wrappers-ftp> |
| not completed | 72 | Explore PAM Config Files | <https://github.com/kelvintechnical/pam-config-files> |
| not completed | 73 | Read PAM Module Documentation | <https://github.com/kelvintechnical/pam-module-docs> |
| not completed | 74 | Implement Password Complexity | <https://github.com/kelvintechnical/password-complexity-pam> |
| not completed | 75 | Configure PAM to Limit root Access | <https://github.com/kelvintechnical/pam-limit-root-access> |
| not completed | 76 | Use PAM to Limit User Access | <https://github.com/kelvintechnical/pam-limit-user-access> |
| not completed | 77 | Restrict Service Access by User List | <https://github.com/kelvintechnical/pam-restrict-by-user-list> |

---

### 🛡 SELinux (README Labs 78–84)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 78 | Managing SELinux Modes | <https://github.com/kelvintechnical/selinux-modes-management> |
| not completed | 79 | Viewing SELinux Contexts | <https://github.com/kelvintechnical/selinux-viewing-contexts> |
| not completed | 80 | Temporary Context Changes | <https://github.com/kelvintechnical/selinux-temporary-contexts> |
| not completed | 81 | Persistent Context Restoration | <https://github.com/kelvintechnical/selinux-persistent-contexts> |
| not completed | 82 | Toggling SELinux Booleans | <https://github.com/kelvintechnical/selinux-booleans> |
| not completed | 83 | SELinux User Mapping | <https://github.com/kelvintechnical/selinux-user-mapping> |
| not completed | 84 | Troubleshooting SELinux | <https://github.com/kelvintechnical/selinux-troubleshooting> |
| not completed | — | Apply Recursive SELinux Contexts to a New Directory (in-repo) | [`labs/selinux-recursive-contexts-direct01/`](labs/selinux-recursive-contexts-direct01/) |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | SEL-F02 | Add a Custom HTTP Port to the SELinux Policy Database | `semanage port -a -t http_port_t -p tcp 8300`, verify with `semanage port -l \| grep http_port_t`, prove the change survives a relabel |
| not completed | SEL-F03 | Set SELinux to Permissive Mode Persistently | Edit `/etc/selinux/config: SELINUX=permissive`, `setenforce 0`, prove with `getenforce` and reboot to verify persistence |
| not completed | SEL-F04 | Apply Recursive SELinux Context from a Reference Directory | `mkdir /dir && mkdir /dir/subdir{1,2}`, `semanage fcontext -a -e /etc /dir`, `restorecon -RFv /dir`, prove with `ls -Zd /dir/subdir1` matching `/etc/skel` exactly |
| not completed | SEL-F05 | Configure Apache to Serve from a Non-Default Directory | `mkdir /web`, drop `practice.html`, `semanage fcontext -a -t httpd_sys_content_t '/web(/.*)?'`, `restorecon -Rv /web`, prove `ls -Z` and `curl http://localhost/web/practice.html` |
| not completed | SEL-F06 | Toggle the `httpd_can_network_connect` Boolean Persistently | `setsebool -P httpd_can_network_connect on`, prove `getsebool` shows on, reboot and re-verify |

---

### 🥾 Boot Process & GRUB (README Labs 85–89)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 85 | Modify GRUB Timeout | <https://github.com/kelvintechnical/grub-timeout> |
| not completed | 86 | Enable Verbose Kernel Messages | <https://github.com/kelvintechnical/verbose-kernel-messages> |
| not completed | 87 | Generate New GRUB Config | <https://github.com/kelvintechnical/grub-mkconfig> |
| not completed | 88 | Reset Root Password via Boot | <https://github.com/kelvintechnical/reset-root-password-boot> |
| not completed | 89 | Chroot into Rescue Filesystem | <https://github.com/kelvintechnical/chroot-rescue-filesystem> |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | BOOT-F01 | Enable Verbose Boot by Removing `quiet` and `rhgb` | Edit `/etc/default/grub`, remove `quiet rhgb` from `GRUB_CMDLINE_LINUX`, `grub2-mkconfig -o /boot/grub2/grub.cfg`, reboot and watch the verbose systemd boot log |

---

### ⚙️ Systemd & Services (README Labs 90–99)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 90 | Check Default Boot Target | <https://github.com/kelvintechnical/default-boot-target> |
| not completed | 91 | Change Default Boot Target | <https://github.com/kelvintechnical/change-default-boot-target> |
| not completed | 92 | System Reboots and Shutdowns | <https://github.com/kelvintechnical/reboot-shutdown-systemd> |
| not completed | 93 | List All System Units | <https://github.com/kelvintechnical/list-system-units> |
| not completed | 94 | Check Service Status | <https://github.com/kelvintechnical/service-status-check> |
| not completed | 95 | Start and Stop Services | <https://github.com/kelvintechnical/start-stop-services> |
| not completed | 96 | Enable Services at Boot | <https://github.com/kelvintechnical/enable-services-at-boot> |
| not completed | 97 | Disable Services at Boot | <https://github.com/kelvintechnical/disable-services-at-boot> |
| not completed | 98 | Mask System Services | <https://github.com/kelvintechnical/mask-system-services> |
| not completed | 99 | Create and Manage systemd Unit Files | <https://github.com/kelvintechnical/systemd-unit-files> |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | SYSD-F01 | Set the Default Boot Target to `multi-user.target` | `systemctl set-default multi-user.target`, `systemctl isolate multi-user.target` for immediate effect, prove with `systemctl get-default` + reboot |

---

### 📋 Log Management (README Labs 100–106)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 100 | Analyze Boot Performance | <https://github.com/kelvintechnical/analyze-boot-performance> |
| not completed | 101 | Query Logs with journalctl | <https://github.com/kelvintechnical/query-logs-with-journalctl> |
| not completed | 102 | Configure Persistent Journal Logs | <https://github.com/kelvintechnical/configure-persistent-journal-logs> |
| not completed | 103 | Understand Log Routing | <https://github.com/kelvintechnical/understand-log-routing> |
| not completed | 104 | Monitor Authentication Logs | <https://github.com/kelvintechnical/monitor-authentication-logs> |
| not completed | 105 | Filter systemd Journals by Priority | <https://github.com/kelvintechnical/filter-systemd-journals-by-priority> |
| not completed | 106 | Service-Specific Journal Logs | <https://github.com/kelvintechnical/service-specific-journal-logs> |

---

### ⏰ System Time & Locale (README Labs 107–109)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 107 | Configure Timezone and Time Synchronization | <https://github.com/kelvintechnical/Configure-Timezone-and-Time-Synchronization> |
| not completed | 108 | Check NTP Sync Status | <https://github.com/kelvintechnical/check-ntp-sync-status> |
| not completed | 109 | Configure NTP Time Source | <https://github.com/kelvintechnical/configure-ntp> |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | TIME-F01 | Set System Timezone via `timedatectl` | `timedatectl set-timezone Europe/London` — also practice America/New_York and Asia/Tokyo; verify with `timedatectl` and `date` |
| not completed | TIME-F02 | Configure Chrony with a Specific NTP Server | Edit `/etc/chrony.conf`: comment out default pool, add `server utility.ntp.org iburst`, restart chronyd, `chronyc sources -v` showing `^*` reachability |

---

### 💾 Storage Management (README Labs 110–120)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 110 | Inspect Filesystems | <https://github.com/kelvintechnical/inspect-filesystems> |
| not completed | 111 | Display Partition Tables | <https://github.com/kelvintechnical/display-partition-tables> |
| not completed | 112 | Create MBR Partition with fdisk | <https://github.com/kelvintechnical/create-mbr-partition-fdisk> |
| not completed | 113 | Change Partition Types in fdisk | <https://github.com/kelvintechnical/change-partition-types-fdisk> |
| not completed | 114 | Create GPT Partition with gdisk | <https://github.com/kelvintechnical/create-gpt-partition-gdisk> |
| not completed | 115 | Command-Line Partitioning with parted | <https://github.com/kelvintechnical/command-line-partitioning-parted> |
| not completed | 116 | Format Partition with XFS | <https://github.com/kelvintechnical/format-partition-xfs> |
| not completed | 117 | Format Partition with Ext4 | <https://github.com/kelvintechnical/format-partition-ext4> |
| not completed | 118 | Check Filesystem Consistency | <https://github.com/kelvintechnical/check-filesystem-consistency-fsck> |
| not completed | 119 | Inspect Filesystem Features | <https://github.com/kelvintechnical/inspect-filesystem-features-dumpe2fs> |
| not completed | 120 | Create and Activate Swap Space | <https://github.com/kelvintechnical/create-and-activate-swap> |
| not completed | — | Create a Swap Partition by UUID (in-repo) | [`labs/storage-swap-partition-uuid/`](labs/storage-swap-partition-uuid/) |
| not completed | — | Create an Ext4 Partition Mounted by LABEL (in-repo) | [`labs/storage-ext4-partition-label/`](labs/storage-ext4-partition-label/) |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | STOR-F03 | Create an MBR Partition with ext4 Mounted by LABEL | `parted /dev/vdb mklabel msdos`, `mkpart primary ext4 1MiB 2GiB`, `mkfs.ext4 -L MYDEV`, fstab `LABEL=MYDEV /mnt/dev ext4 defaults 0 2`, prove persistence after reboot |
| not completed | STOR-F04 | Create a Companion LVM-Type Partition on the Same Disk | `parted /dev/vdb mkpart primary 2GiB 7GiB`, `set 2 lvm on`, prove with `fdisk -l` showing partition type `Linux LVM` — preps the disk for an LVM lab |

---

### 🗂 LVM (Logical Volume Management) (README Labs 121–130)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 121 | Initialize Physical Volumes | [`labs/lvm-pvcreate-initialize-pv/`](labs/lvm-pvcreate-initialize-pv/) |
| not completed | 122 | Display Physical Volumes | [`labs/lvm-display-physical-volumes/`](labs/lvm-display-physical-volumes/) |
| not completed | 123 | Create Volume Group | [`labs/lvm-create-volume-group/`](labs/lvm-create-volume-group/) |
| not completed | 124 | Display Volume Groups | [`labs/lvm-display-volume-groups/`](labs/lvm-display-volume-groups/) |
| not completed | 125 | Create Logical Volume | [`labs/lvm-create-logical-volume/`](labs/lvm-create-logical-volume/) |
| not completed | 126 | Display Logical Volumes | [`labs/lvm-display-logical-volumes/`](labs/lvm-display-logical-volumes/) |
| not completed | 127 | Extend Volume Group | [`labs/lvm-extend-volume-group/`](labs/lvm-extend-volume-group/) |
| not completed | 128 | Extend Logical Volume | [`labs/lvm-extend-logical-volume/`](labs/lvm-extend-logical-volume/) |
| not completed | 129 | Resize Filesystem After Extend | [`labs/lvm-resize-filesystem-after-extend/`](labs/lvm-resize-filesystem-after-extend/) |
| not completed | 130 | Remove LVM Components | [`labs/lvm-remove-components/`](labs/lvm-remove-components/) |
| not completed | LAB | Create LV `lvol1` (ext4, 280 MB) | <https://github.com/kelvintechnical/lvm-create-lvol1-ext4> ([also `labs/lvm-create-lvol1-ext4/`](labs/lvm-create-lvol1-ext4/)) |
| not completed | — | Create LV with XFS Filesystem (in-repo) | [`labs/lvm-create-lv1-xfs/`](labs/lvm-create-lv1-xfs/) |
| not completed | — | Online Extend an LV and Its Filesystem Without Unmounting (in-repo) | [`labs/lvm-online-extend-xfs/`](labs/lvm-online-extend-xfs/) |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | LVM-F02 | Create an LVM VDO Volume with Thin Provisioning | `vdo create --name=vdo1 --device=/dev/sdb --vdoLogicalSize=20G`; mount with ext4 and XFS variants; persistent fstab with `_netdev,x-systemd.requires=vdo.service` |
| not completed | LVM-F03 | LV by Extent Count in a VG with Custom PE Size (ext4 variant) | `vgcreate -s 8M vgstore /dev/vdb1`, `lvcreate -l 50 -n lvdata vgstore` (= 400 MiB LV), mkfs.ext4, persistent mount on `/mnt/data` |
| not completed | LVM-F04 | LV Sized as a Percentage of the VG with XFS + UUID Mount | `lvcreate -l 50%VG -n mylv myvg`, mkfs.xfs, capture UUID with `blkid`, fstab UUID entry on `/mnt/mylv` |
| not completed | LVM-F05 | LV Sized as a Percentage of Free Space with XFS | `lvcreate -l 75%FREE -n lvstore vgdata`, mkfs.xfs, fstab UUID entry on `/mnt/lvm` |
| not completed | LVM-F06 | LV with Extent Count + Reserved Free Extents Constraint | `vgcreate -s 16M team_vg /dev/sdb1`, `lvcreate -l 40 -n team_lv team_vg` while leaving at least 10 free extents |
| not completed | LVM-F07 | Online Resize LV to a New Total Extent Count + Grow ext4 | `lvresize -l 85 /dev/vgstore/lvdata && resize2fs ...`; `-l 85` means "exactly 85 extents total," not "add 85" |
| not completed | LVM-F08 | Add Extents to an Existing LV + Grow XFS Online | `lvextend -l +8 /dev/team_vg/team_lv && xfs_growfs /mnt/team_lv` |
| not completed | LVM-F09 | Create Swap from Remaining VG Free Space | `lvcreate -L 500M -n swap_lv team_vg`, `mkswap`, `swapon`, fstab UUID entry `swap swap defaults 0 0` |

---

### 📁 Filesystem Mounts (README Labs 131–136)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 131 | Mount Filesystem Manually | *(coming soon — see Lab #131 in [README](README.md#-filesystem-mounts))* |
| not completed | 132 | Retrieve Filesystem UUIDs | *(coming soon — see Lab #132 in [README](README.md#-filesystem-mounts))* |
| not completed | 133 | Configure Persistent Mounts fstab | *(coming soon — see Lab #133 in [README](README.md#-filesystem-mounts))* |
| not completed | 134 | Mount Network CIFS Shares | *(coming soon — see Lab #134 in [README](README.md#-filesystem-mounts))* |
| not completed | 135 | Remount with New Options | *(coming soon — see Lab #135 in [README](README.md#-filesystem-mounts))* |
| not completed | 136 | Manage Autofs Service | *(coming soon — see Lab #136 in [README](README.md#-filesystem-mounts))* |

**NFS & AutoFS Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | NFS-F01 | NFS Server + AutoFS Direct Map | Export `/rh_share` on server; client `/etc/auto.master.d/direct.autofs` + `/etc/auto.direct` map mounts share on demand at `/mnt/rh_share` |
| not completed | NFS-F02 | NFS Home-Directory Export with AutoFS Indirect Map on Login | Server exports `/home/user60`; client indirect map under `/nfsdir` mounts home dir automatically first login; prove unmount-on-idle |
| not completed | NFS-F03 | NFS Static Export with Persistent `/etc/fstab` Mount | `exportfs -rav` on server, `server:/share5 /share6 nfs _netdev,defaults 0 0` in fstab on client, `mount -a`, prove survives reboot |
| not completed | NFS-F04 | Configure a Node as an NFS Server (companion lab) | `dnf install nfs-utils`, `mkdir /exports/home`, `/etc/exports` `/exports/home *(rw,sync,no_root_squash)`, `exportfs -rav`, `systemctl enable --now nfs-server`, `firewall-cmd --add-service={nfs,mountd,rpc-bind}` |
| not completed | NFS-F05 | AutoFS Indirect Map for Remote Home Dirs with 60s Timeout | `auto.master.d/homes.autofs` entry `/homes/remote /etc/auto.homes --timeout=60`, `/etc/auto.homes` with `* server.example.com:/exports/home/&` |
| not completed | NFS-F06 | AutoFS Direct Map for `/mnt/shared` with 5-Minute Timeout | `auto.master.d/direct.autofs` `/- /etc/auto.direct --timeout=300`, `/etc/auto.direct` `/mnt/shared -rw server.example.com:/srv/shared` |

---

### 📦 Package Management & Repositories (README Labs 137–161)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 137 | Install Local RPM Package | *(coming soon — see Lab #137 in [README](README.md#-package-management--repositories))* |
| not completed | 138 | Upgrade RPM Package | *(coming soon — see Lab #138 in [README](README.md#-package-management--repositories))* |
| not completed | 139 | Install New Kernel Safely | *(coming soon — see Lab #139 in [README](README.md#-package-management--repositories))* |
| not completed | 140 | Uninstall Package rpm -e | *(coming soon — see Lab #140 in [README](README.md#-package-management--repositories))* |
| not completed | 141 | Query All Installed Packages | *(coming soon — see Lab #141 in [README](README.md#-package-management--repositories))* |
| not completed | 142 | Query Specific Package Info | *(coming soon — see Lab #142 in [README](README.md#-package-management--repositories))* |
| not completed | 143 | List Files Within Package | *(coming soon — see Lab #143 in [README](README.md#-package-management--repositories))* |
| not completed | 144 | Identify File Owner | *(coming soon — see Lab #144 in [README](README.md#-package-management--repositories))* |
| not completed | 145 | Query Uninstalled RPMs | *(coming soon — see Lab #145 in [README](README.md#-package-management--repositories))* |
| not completed | 146 | Verify Package Integrity | *(coming soon — see Lab #146 in [README](README.md#-package-management--repositories))* |
| not completed | 147 | System-Wide Verification | *(coming soon — see Lab #147 in [README](README.md#-package-management--repositories))* |
| not completed | 148 | Import GPG Key | *(coming soon — see Lab #148 in [README](README.md#-package-management--repositories))* |
| not completed | 149 | Check Package Signatures | *(coming soon — see Lab #149 in [README](README.md#-package-management--repositories))* |
| not completed | 150 | Configure Repository Access | <https://github.com/kelvintechnical/Configure-Repository-Access-> |
| not completed | 151 | Install Packages with dnf | *(coming soon — see Lab #151 in [README](README.md#-package-management--repositories))* |
| not completed | 152 | Remove Packages with dnf | *(coming soon — see Lab #152 in [README](README.md#-package-management--repositories))* |
| not completed | 153 | Update System dnf update | *(coming soon — see Lab #153 in [README](README.md#-package-management--repositories))* |
| not completed | 154 | Search for Software | *(coming soon — see Lab #154 in [README](README.md#-package-management--repositories))* |
| not completed | 155 | Find File Providers | *(coming soon — see Lab #155 in [README](README.md#-package-management--repositories))* |
| not completed | 156 | List dnf Packages | *(coming soon — see Lab #156 in [README](README.md#-package-management--repositories))* |
| not completed | 157 | Display Enabled Repositories | *(coming soon — see Lab #157 in [README](README.md#-package-management--repositories))* |
| not completed | 158 | View Package Group Info | *(coming soon — see Lab #158 in [README](README.md#-package-management--repositories))* |
| not completed | 159 | Install Package Groups | <https://github.com/kelvintechnical/install-package-group> |
| not completed | 160 | Create Custom YUM Repository | *(coming soon — see Lab #160 in [README](README.md#-package-management--repositories))* |
| not completed | 161 | Managing Flatpak | <https://github.com/kelvintechnical/Managing-Flatpak> |
| not completed | — | Install Development Tools Package Group with Output Capture (in-repo) | [`labs/dnf-install-dev-tools-capture/`](labs/dnf-install-dev-tools-capture/) |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | PKG-F02 | Configure Local Repository from Installation ISO Media | Mount RHEL 9 ISO at `/repo` with a persistent loop entry in `/etc/fstab`, create `/etc/yum.repos.d/local-baseos.repo` + `local-appstream.repo` pointing at `file:///repo/BaseOS` and `/repo/AppStream` with `gpgcheck=0` |
| not completed | PKG-F03 | Configure Two HTTP-Hosted Repositories from a Network Source | BaseOS and AppStream `.repo` files pointing at `http://repo.example.com/rhel9/{BaseOS,AppStream}` with `enabled=1`, prove with `dnf repolist enabled` + `dnf install -y httpd` |

---

### 👥 User & Group Management (README Labs 162–183)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 162 | Inspect Password Database | *(coming soon — see Lab #162 in [README](README.md#-user--group-management))* |
| not completed | 163 | Analyze Shadow File | *(coming soon — see Lab #163 in [README](README.md#-user--group-management))* |
| not completed | 164 | Modify Default Password Aging | *(coming soon — see Lab #164 in [README](README.md#-user--group-management))* |
| not completed | 165 | User & Group Management / Permissions | <https://github.com/kelvintechnical/User-Group-Management-Permissions> |
| not completed | 166 | Modify Existing Account | *(coming soon — see Lab #166 in [README](README.md#-user--group-management))* |
| not completed | 167 | Advanced Group Management | *(coming soon — see Lab #167 in [README](README.md#-user--group-management))* |
| not completed | 168 | Force Password Changes | *(coming soon — see Lab #168 in [README](README.md#-user--group-management))* |
| not completed | 169 | Safely Delete Users | *(coming soon — see Lab #169 in [README](README.md#-user--group-management))* |
| not completed | 170 | Disable User Login Without Removing the Account | <https://github.com/kelvintechnical/disable-user-login> |
| not completed | 171 | Validate User and Group Creation | *(coming soon — see Lab #171 in [README](README.md#-user--group-management))* |
| not completed | 172 | Proper Use of su vs su - | *(coming soon — see Lab #172 in [README](README.md#-user--group-management))* |
| not completed | 173 | Limit Access to su PAM | *(coming soon — see Lab #173 in [README](README.md#-user--group-management))* |
| not completed | 174 | Configure Custom Administrators | *(coming soon — see Lab #174 in [README](README.md#-user--group-management))* |
| not completed | 175 | Granular sudo Privileges | *(coming soon — see Lab #175 in [README](README.md#-user--group-management))* |
| not completed | 176 | Limit root Logins | *(coming soon — see Lab #176 in [README](README.md#-user--group-management))* |
| not completed | 177 | Restrict Root to Single Console | *(coming soon — see Lab #177 in [README](README.md#-user--group-management))* |
| not completed | 178 | Populate Directory Templates | *(coming soon — see Lab #178 in [README](README.md#-user--group-management))* |
| not completed | 179 | Manage Shell Environments | *(coming soon — see Lab #179 in [README](README.md#-user--group-management))* |
| not completed | 180 | Alter Global Default umask | *(coming soon — see Lab #180 in [README](README.md#-user--group-management))* |
| not completed | 181 | Distribute Documentation via Skel | *(coming soon — see Lab #181 in [README](README.md#-user--group-management))* |
| not completed | 182 | Control Group Ownership SGID | *(coming soon — see Lab #182 in [README](README.md#-user--group-management))* |
| not completed | 183 | Set Up Group-Managed Directory | *(coming soon — see Lab #183 in [README](README.md#-user--group-management))* |
| not completed | — | Lock User Account and Capture Regex Evidence (in-repo) | [`labs/user-lock-capture-regex/`](labs/user-lock-capture-regex/) |

**User & Group Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | USER-F01 | Group with Fixed GID + User with Primary/Secondary Groups | `groupadd -g 3500 admins`, `groupadd users`, `useradd -u 3455 -g admins -G users harry`, prove with `id harry` |
| not completed | USER-F02 | User Without Interactive Shell (`nologin`) That Still Authenticates | `useradd -s /sbin/nologin sarah`, set password, prove SSH login rejected but PAM-level password auth succeeds for password-only services |
| not completed | USER-F03 | User With Explicit (Hand-Built) Home Directory | `useradd -M bruce`, `mkdir /home/bruce`, `cp -av /etc/skel/. /home/bruce`, `chown -R bruce:bruce`, `chmod 700` |
| not completed | USER-F04 | Force Password Change at Next Login | `passwd --expire liam` (or `chage -d 0 liam`), prove with `chage -l liam`, then ssh in and observe the forced-change prompt |
| not completed | USER-F05 | Set Hard Account Expiry Date | `chage -E 2029-01-01 lina`, or `chage -E $(date -d '+7 days' +%Y-%m-%d) marvin` for relative expiry, prove with `chage -l USER` |
| not completed | USER-F06 | Welcome.txt Auto-Created for Every New User via `/etc/skel` | `echo "Welcome Onboard!" > /etc/skel/Welcome.txt`, useradd a new user, verify Welcome.txt appears with right ownership and mode |
| not completed | USER-F07 | Configure System-Wide Password Aging Policy | Edit `/etc/login.defs`: `PASS_MAX_DAYS 30`, `PASS_MIN_LEN 9`; prove the policy applies only to users created *after* the edit |
| not completed | USER-F08 | Reset Root Password from GRUB Boot Menu (`rd.break` Path) | Edit GRUB at boot, append `rd.break`, ctrl-x, `mount -o remount,rw /sysroot`, `chroot /sysroot`, `passwd root`, `touch /.autorelabel`, two `exit`s, reboot |

**Sudo & Privilege Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | SUDO-F01 | Full Sudo for a User + NOPASSWD for an Entire Group | `visudo`: `john ALL=(ALL) ALL` + `%admins ALL=(ALL) NOPASSWD: ALL`, prove via `sudo -l` per user |
| not completed | SUDO-F02 | Granular Sudo: Allow `passwd` Except Root Password Changes | `visudo`: `brian ALL=(ALL) /usr/bin/passwd [A-Za-z]*, !/usr/bin/passwd root, !/usr/bin/passwd ""` |
| not completed | SUDO-F03 | Privileged User with Account Expiry | `useradd -u 4545 marvin`, `passwd marvin`, add to wheel, `chage -E $(date -d '+7 days' +%F) marvin` |

---

### 🔄 Process Management (README Labs 184–192)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 184 | Audit All Running Processes | *(coming soon — see Lab #184 in [README](README.md#-process-management))* |
| not completed | 185 | Identify Process Details | *(coming soon — see Lab #185 in [README](README.md#-process-management))* |
| not completed | 186 | View SELinux Process Contexts | *(coming soon — see Lab #186 in [README](README.md#-process-management))* |
| not completed | 187 | Real-Time Process Monitoring | *(coming soon — see Lab #187 in [README](README.md#-process-management))* |
| not completed | 188 | Adjust Process Priority | *(coming soon — see Lab #188 in [README](README.md#-process-management))* |
| not completed | 189 | Start Processes with Custom Priority | *(coming soon — see Lab #189 in [README](README.md#-process-management))* |
| not completed | 190 | Terminate Processes Gracefully | *(coming soon — see Lab #190 in [README](README.md#-process-management))* |
| not completed | 191 | Force Kill Unresponsive Processes | *(coming soon — see Lab #191 in [README](README.md#-process-management))* |
| not completed | 192 | Kill Processes by Name | *(coming soon — see Lab #192 in [README](README.md#-process-management))* |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | PROC-F01 | Start a Background Process with a Specific nice Value | `nice -n 10 sleep 3600 &`, capture `$!` into a variable, verify nice value with `ps -o pid,ni,cmd $!` |
| not completed | PROC-F02 | Renice a Running Process to a Higher Priority | `renice -n -5 -p $PID` — requires root for negative niceness, prove with `ps -o pid,ni` before and after |
| not completed | PROC-F03 | Lowest-Priority Background Task on User Login | As `lina`: in `~/.bash_profile` add `nice -n 19 sleep infinity &`, verify with `ps -o pid,ni -u lina` showing `19` |
| not completed | PROC-F04 | Clean Termination of a Background Process | `kill $PID` for SIGTERM first, verify exit, fall back to `kill -9` only on hung processes |

---

### 🗜 Archives & Compression (README Labs 193–198)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 193 | Standard File Compression with gzip | <https://github.com/kelvintechnical/standard-file-compression> |
| not completed | 194 | High-Ratio Compression with bzip2 | <https://github.com/kelvintechnical/high-ratio-compression> |
| not completed | 195 | Create Standard Archives with tar | <https://github.com/kelvintechnical/create-standard-archives> |
| not completed | 196 | Create Compressed Archives | *(coming soon — see Lab #196 in [README](README.md#-archives--compression))* |
| not completed | 197 | Extract Archives | *(coming soon — see Lab #197 in [README](README.md#-archives--compression))* |
| not completed | 198 | Preserve Security Contexts in Archives | *(coming soon — see Lab #198 in [README](README.md#-archives--compression))* |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | ARCH-F01 | Create an xz-Compressed Tar Archive | `tar -cJvf /archives/config_backup.tar.xz /etc`, restore with `tar -xJvf` into `/restore` — highest-compression-ratio option |
| not completed | ARCH-F02 | Create an Uncompressed Standard Tar Archive | `tar -cvf /root/etc_opt.bak.tar /etc /opt` — the no-compression variant for streaming to other compressors |
| not completed | ARCH-F03 | Restore a Tar Archive into a Specific Destination Directory | `mkdir -p /root/restored_tmp && tar -xzvf /root/tmp.tgz -C /root/restored_tmp`, prove with `find /root/restored_tmp -maxdepth 2` |

---

### 🕐 Scheduled Tasks (README Labs 199–207)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 199 | Review System-Wide cron Jobs | *(coming soon — see Lab #199 in [README](README.md#-scheduled-tasks))* |
| not completed | 200 | Schedule Tasks with cron | *(coming soon — see Lab #200 in [README](README.md#-scheduled-tasks))* |
| not completed | 201 | Remove User cron Jobs | *(coming soon — see Lab #201 in [README](README.md#-scheduled-tasks))* |
| not completed | 202 | Schedule One-Time Task with at | *(coming soon — see Lab #202 in [README](README.md#-scheduled-tasks))* |
| not completed | 203 | Limit Access to cron | *(coming soon — see Lab #203 in [README](README.md#-scheduled-tasks))* |
| not completed | 204 | Limit Access to at | *(coming soon — see Lab #204 in [README](README.md#-scheduled-tasks))* |
| not completed | 205 | Review the Anacron System | *(coming soon — see Lab #205 in [README](README.md#-scheduled-tasks))* |
| not completed | 206 | Create a Specific cron Job | *(coming soon — see Lab #206 in [README](README.md#-scheduled-tasks))* |
| not completed | 207 | Schedule Software Audit with at | *(coming soon — see Lab #207 in [README](README.md#-scheduled-tasks))* |
| not completed | LAB | Scheduling Jobs (systemd timer, Mon–Fri 2 AM) | <https://github.com/kelvintechnical/scheduling-jobs-systemd-timer> ([also `labs/scheduling-jobs-systemd-timer/`](labs/scheduling-jobs-systemd-timer/)) |
| not completed | — | User-Level Cron Job with `find -exec` (in-repo) | [`labs/cron-user-find-exec-coredir/`](labs/cron-user-find-exec-coredir/) |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | CRON-F02 | User Cron Job at 12:45 AM Daily | As `bruce`: `crontab -e` `45 0 * * * /usr/bin/echo "EX200 Practice Test!" >> $HOME/cron.log` |
| not completed | CRON-F03 | Recurring User Cron Job Every 2 Minutes | As `linda`: `*/2 * * * * logger "RHCSA EX200 Practice Test 2 In Progress!"` |
| not completed | CRON-F04 | Weekday-Only Cron Job at 5:45 AM | As `emma`: `45 5 * * 1-5 logger "Good morning! Work day about to start."` |
| not completed | CRON-F05 | Midnight-Weekend Root Cron Job to Clean Empty Files in `/tmp` | Root crontab: `0 0 * * 6,0 find /tmp -maxdepth 1 -type f -empty -delete` |
| not completed | CRON-F06 | One-Time `at` Job for a Specific Wall-Clock Time | As `russ`: `echo 'echo "EX200 Mock Practice 1 Complete!" >> $HOME/practice.log' \| at 21:30` |
| not completed | CRON-F07 | One-Time `at` Job One Hour from Now Writing to journald | As `alina`: `echo 'logger "Making Progress with EX200!"' \| at now + 1 hour` |

---

### 🔐 GPG Encryption (README Labs 208–211)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 208 | Generate a GPG Key Pair | *(coming soon — see Lab #208 in [README](README.md#-gpg-encryption))* |
| not completed | 209 | Encrypt a File with GPG | *(coming soon — see Lab #209 in [README](README.md#-gpg-encryption))* |
| not completed | 210 | Decrypt a GPG File | *(coming soon — see Lab #210 in [README](README.md#-gpg-encryption))* |
| not completed | 211 | Share and Verify Public Keys | *(coming soon — see Lab #211 in [README](README.md#-gpg-encryption))* |

---

### 🔗 Remote Administration & Network Tools (README Labs 212–215)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 212 | SSH and SCP File Transfer | *(coming soon — see Lab #212 in [README](README.md#-remote-administration--network-tools))* |
| not completed | 213 | Network Troubleshooting | *(coming soon — see Lab #213 in [README](README.md#-remote-administration--network-tools))* |
| not completed | 214 | Command-Line Web and FTP Testing | <https://github.com/kelvintechnical/elinks-iftp> |
| not completed | 215 | Command-Line Email Testing | <https://github.com/kelvintechnical/mutt-mail-smtp> |

**SSH Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | SSH-F01 | Configure SSH to Listen on a Custom Port | `sshd_config Port 88`, SELinux `semanage port -a -t ssh_port_t -p tcp 88`, `firewall-cmd --add-port=88/tcp --permanent`, restart sshd |
| not completed | SSH-F02 | Permit Root SSH Login with Authentication-Failure Lockout | `sshd_config PermitRootLogin yes` + `MaxAuthTries 3`, demonstrate the 4th failed attempt is rejected and earlier produce auth-failure lines |
| not completed | SSH-F03 | Passwordless SSH from Root to Remote Root | `ssh-keygen -t ed25519 -N ""` on Node1, `ssh-copy-id root@Node2`, verify with `ssh root@Node2 hostname` |
| not completed | SSH-F04 | Key-Based SSH from a User to a Remote Root on a Custom Port | As `marvin` on Node2: `ssh-keygen`, `ssh-copy-id -p 88 root@Node1`, prove `ssh -p 88 root@Node1` succeeds without a password |
| not completed | SSH-F05 | Configure Local `/etc/hosts` Name Resolution | Add `192.168.56.25 node1.lab3.example.net node1` so `ping node1` resolves locally, persists across reboots, and `ssh node1` works without DNS |
| not completed | SSH-F06 | Secure File Transfer with `scp` Preserving Attributes | `scp -p /etc/fstab user@host:~/` — `-p` preserves timestamps and mode but NOT ownership across users; for ownership use `rsync -avz --chown` |

---

### 🛡 Security Administration (README Labs 216–220)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 216 | Service Isolation Bastion Host | *(coming soon — see Lab #216 in [README](README.md#-security-administration))* |
| not completed | 217 | Monitor Security Updates | *(coming soon — see Lab #217 in [README](README.md#-security-administration))* |
| not completed | 218 | Build a Bastion Server | *(coming soon — see Lab #218 in [README](README.md#-security-administration))* |
| not completed | 219 | Comprehensive firewalld Setup | *(coming soon — see Lab #219 in [README](README.md#-security-administration))* |
| not completed | 220 | PAM and SELinux with FTP | *(coming soon — see Lab #220 in [README](README.md#-security-administration))* |

---

### 🌍 Web Services (Apache) (README Labs 221–224)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 221 | Configure Apache to Serve Default and Custom Web Content | <https://github.com/kelvintechnical/apache-custom-content> |
| not completed | 222 | Password-Protect a Directory | *(coming soon — see Lab #222 in [README](README.md#-web-services-apache))* |
| not completed | 223 | Deploy Name-Based Virtual Hosts | *(coming soon — see Lab #223 in [README](README.md#-web-services-apache))* |
| not completed | 224 | Configure Secure Virtual Hosts HTTPS | *(coming soon — see Lab #224 in [README](README.md#-web-services-apache))* |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | WEB-F01 | Apache Listening on a Non-Standard TCP Port | `Listen 85` in `/etc/httpd/conf.d/port.conf` drop-in, `semanage port -a -t http_port_t -p tcp 85`, `firewall-cmd --add-port=85/tcp --permanent`, `curl http://localhost:85` |
| not completed | WEB-F02 | Apache Default Page + Custom Content Directory | Modify `/var/www/html/index.html`, create `/web/practice.html`, `Require all granted`, `semanage fcontext httpd_sys_content_t` for `/web(/.*)?`, `restorecon -Rv /web` |
| not completed | WEB-F03 | Apache Subdirectory Routing with SELinux Inheritance | `mkdir /var/www/html/route_station`, drop index.html, confirm inherited `httpd_sys_content_t` from parent, curl `http://Node1/route_station/index.html` |
| not completed | WEB-F04 | Password-Protected Apache Directory with htpasswd | `htpasswd -c /etc/httpd/.htpasswd alice`, `AuthType Basic` + `AuthUserFile` + `Require valid-user`, prove anonymous returns HTTP 401 |
| not completed | WEB-F05 | Apache SSL Virtual Host with Self-Signed Certificate | `openssl req -x509 -newkey rsa:2048 -nodes -keyout ... -out ... -days 365`, ssl.conf `SSLCertificateFile`/`SSLCertificateKeyFile`, `firewall-cmd --add-service=https` |

---

### ⚡ System Performance & Tuning (README Lab 225)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 225 | Enable Recommended Tuning Profile | <https://github.com/kelvintechnical/tuning-profile> |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | PERF-F01 | Apply the `virtual-guest` Tuning Profile | `tuned-adm profile virtual-guest` — virtualization-efficiency profile for VMs, verify with `tuned-adm active` |
| not completed | PERF-F02 | Apply a Power-Saving / Virtualization-Balanced Profile | `tuned-adm profile balanced-battery` or `virtual-guest-powersave`, compare with `tuned-adm recommend`, prove active profile changed |

---

### 📜 Shell Scripting & Automation (README Labs 226–227)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 226 | Argument-Based Conditional Script | <https://github.com/kelvintechnical/argument-script> |
| not completed | 227 | Use for Loops for Iteration | *(coming soon — see Lab #227 in [README](README.md#-shell-scripting--automation))* |
| not completed | — | Bidirectional Bash Script with Argument Logic (in-repo) | [`labs/bash-bidirectional-arg-script/`](labs/bash-bidirectional-arg-script/) |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | SCRIPT-F02 | Bash Script: Find Files Matching a Pattern and Print stat | Loop over `/usr/bin/ac*`, `[ -f $f ]` guard to exclude directories, run `stat $f` for each match, redirect to `/var/tmp/acstats.out` |
| not completed | SCRIPT-F03 | Bash Script: Create a User Whose Name Comes from a Variable | Declare `ENV1=book1`, `useradd "$ENV1"`, set default password from stdin, verify `id "$ENV1"` |
| not completed | SCRIPT-F04 | Countdown Timer Script with Argument or Interactive Prompt | If `$# -eq 1`, `COUNT=$1`; else `read -p`; `while [ $COUNT -gt 0 ]; do echo "$COUNT seconds remaining..."; sleep 1; ((COUNT--)); done` |
| not completed | SCRIPT-F05 | Sum of an Unknown Number of Integer Arguments | `$# -eq 0` → exit 1; else `for n in "$@"; do ((total+=n)); done; echo "Sum is $total"` |
| not completed | SCRIPT-F06 | Find Users by Login Shell and Save the List | `getent passwd \| awk -F: '$7=="/bin/bash" {print $1}' > /root/bash_users.txt`, chmod +x, re-runnable so file is always current |
| not completed | SCRIPT-F07 | Extract Login Shells of the Last 5 Users in `/etc/passwd` | `tail -5 /etc/passwd \| awk -F: '{printf "User %s has login shell %s\n", $1, $7}'` |
| not completed | SCRIPT-F08 | Per-User Login Script via `.bash_profile` | As `john`: append `grep bash /etc/passwd > ~/bash-users.txt` to `~/.bash_profile` — every interactive login refreshes the file |
| not completed | SCRIPT-F09 | Three-Way Argument-Based Script with Multi-Arg Rejection | `team.sh`: `$# > 1` → exit 5; `$1 == "ops"` → message; `$1 == "dev"` → different message; else usage |

---

### 🐳 Containers & Runtime Management (README LAB row)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | LAB | Launch Named Root Container with Port Mapping | <https://github.com/kelvintechnical/Launch-Named-Root-Container-with-Port-Mapping> |
| not completed | — | Rootless Container with Bind Mount and systemd Auto-Start (in-repo) | [`labs/podman-rootless-bind-mount-systemd/`](labs/podman-rootless-bind-mount-systemd/) |

**Future Labs (planned):**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | CON-F02 | Build a Custom Container Image with a Containerfile | Write a Containerfile FROM ubi8/ubi9, RUN/COPY a small script printing `ls` + `pwd`, `podman build -t custom:latest`, push to local registry, run as named rootless container under `user60` |
| not completed | CON-F03 | Rootless Container with Port Mapping + systemd Auto-Start | As `user60`: `podman run -d --name web -p 10000:80 ubi8`, `podman generate systemd --new --files`, copy to `~/.config/systemd/user/`, `loginctl enable-linger` |
| not completed | CON-F04 | Rootless Container with Bind Mount + Env Vars + Port Mapping | `podman run` as `user60` with `-v /host_data01:/container_data01`, `-e ENVIRON=Exam`, `-e KERN=$(uname -r)`, `-p 1050:1050`, ubi9; user-level systemd unit with linger |
| not completed | CON-F05 | Authenticated Pull from `registry.redhat.io` | `podman login registry.redhat.io` with developer credentials, pull `ubi9/ubi`, prove with `podman images` |
| not completed | CON-F06 | Build a UBI Image from a Single-Line Containerfile | Containerfile with just `FROM registry.redhat.io/ubi8/ubi-init`, `podman build -t ubigreeter`, podman run --rm |
| not completed | CON-F07 | Rootless HTTP Container with Bind-Mounted DocumentRoot | `podman run -d --name webcon -p 8080:80 -v /var/www/html:/usr/local/apache2/htdocs:Z docker.io/library/httpd`, echo content > index.html, `curl localhost:8080` |
| not completed | CON-F08 | Rootless Database Container with Env Vars + Persistent Data | As `ray`: `podman run -d --name inventorydb -p 3308:3306 -e MYSQL_ROOT_PASSWORD=InvPass123 -v /home/ray/inventory_data:/var/lib/mysql:Z registry.redhat.io/rhel9/mariadb-1011` |
| not completed | CON-F09 | Rootless Nginx with Custom Config + DocumentRoot Mounts | As `david`: `podman run -d --name mynginx -p 8080:80 -v /srv/nginx/html:/usr/share/nginx/html:Z -v /srv/nginx/conf:/etc/nginx/conf.d:Z docker.io/library/nginx` |
| not completed | CON-F10 | Multi-Mount Rootless Container with Two Bind Mounts + Port | `podman run -d --name ubicon -p 8089:8089 -v /opt/out:/opt/in:Z -v /opt/send:/opt/receive:Z registry.redhat.io/ubi9/ubi sleep infinity` |
| not completed | CON-F11 | Add Both Flathub and RHEL Flatpak Remotes | `flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo`, `flatpak remote-add --if-not-exists rhel https://flatpaks.redhat.io/rhel.flatpakrepo` |
| not completed | CON-F12 | Install Flatpak Applications (Firefox + VLC + GIMP) | `flatpak search firefox`, `flatpak install -y flathub org.mozilla.firefox`, repeat for VLC and GIMP |
| not completed | CON-F13 | User-Scoped vs System-Wide Flatpak Installation | Compare `flatpak install --user flathub org.mozilla.firefox` vs root `flatpak install --system` |
| not completed | CON-F14 | Remove Flatpak Apps, Prune Runtimes, Remove Remote | `flatpak uninstall -y org.videolan.VLC org.gimp.GIMP`, `flatpak uninstall --unused -y`, `flatpak remote-delete flathub` |

---

### 🌱 Environment & Shell Configuration (Future Labs only)

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | ENV-F01 | System-Wide Environment Variable via `/etc/profile.d` | `cat > /etc/profile.d/sys_tag.sh <<'EOF' \nexport SYS_TAG="RHCSA v9 EX200 PRACTICE EXAMS COMPLETED!"\nEOF`, chmod +x, prove every new shell has the variable with `printenv SYS_TAG` |

---

## 🎯 RHCE Track (EX294)

> Sample-exam scenario labs (Sander van Vugt-style end-to-end Ansible playbooks). All entries below are Planned — they're the "build an entire control project" tier, distinct from the chapter-grained Ansible labs in the [Ansible Track](#-ansible-track-mastering-ansible-4th-ed--rhce-companion-repos) section. The Foundation labs share inventory + repo-server setup across all three sample-exam paths.

### 📋 Complete Labs in This Order

Foundation builds the control project that every later lab reuses. After that, each exam-practice block is a self-contained mock exam — work them in order so you compound difficulty.

#### Step 1: Foundation — Build the Control Project

| # | Status | ID | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 1 | not completed | RHCE-F01 | Build an RHCE Ansible Control Project | `ansible.cfg`, static inventory, test/dev/prod groups, FQDN resolution |
| 2 | not completed | RHCE-F02 | Bootstrap Managed Hosts with Ad-Hoc Commands | Install Python, create `ansible` user, sudoers drop-in, ping module |
| 3 | not completed | RHCE-F03 | Configure a Repository Server with an Ansible Playbook | `setupreposerver.yml`, loop-mount RHEL ISO, vsftpd anonymous access |
| 4 | not completed | RHCE-F04 | Configure Managed Repo Clients with Ad-Hoc Commands | `dnf config-manager`, BaseOS + AppStream from `control.example.com` |

#### Step 2: Exam Practice 1 — Apache + Roles + Storage

| # | Status | ID | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 5 | not completed | RHCE-F05 | HTTP Server and Client Playbooks with `site.yml` | `webserver.yml` + `webclient.yml`, `httpd.j2` template, handler, `site.yml` |
| 6 | not completed | RHCE-F06 | Convert HTTP Playbooks Into an Ansible Role | `defaults/`, `tasks/`, `templates/`, `handlers/` role refactor |
| 7 | not completed | RHCE-F07 | Ansible Storage Role for `/web` with SELinux Contexts | `parted gpt`, mount `/web`, `semanage fcontext httpd_sys_content_t` |

#### Step 3: Exam Practice 2 — Roles Path + LVM + Vault + Galaxy + Users

| # | Status | ID | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 8 | not completed | RHCE-F08 | Default Roles Path in `ansible.cfg` | `roles_path = /home/ansible/roles` with system fallbacks |
| 9 | not completed | RHCE-F09 | `setupstorage.yml` — Conditional LVM Playbook | 5GiB partition, `vgdata` 8MiB PEs, `lvdata` 1GiB ext3, `/data` mount |
| 10 | not completed | RHCE-F10 | `packagefacts.yml` — Package Version Report | Gather package facts, format kernel/bash/glibc into `/root/packages.txt` |
| 11 | not completed | RHCE-F11 | Ansible Vault Credentials Workflow | `cloudpass.yml` encrypted, `vaultpass.txt`, `usevault.yml` writes `/root/cloudcreds.txt` |
| 12 | not completed | RHCE-F12 | Install Galaxy Roles from `requirements.yml` | `geerlingguy.nginx` + `geerlingguy.docker`, `start-galaxy-roles.yml` |
| 13 | not completed | RHCE-F13 | Apache Role with Custom Template Showing HOSTNAME/IPADDRESS | `ansible_facts.hostname`, `ansible_default_ipv4.address` in template |
| 14 | not completed | RHCE-F14 | Create Users from YAML Input with SHA256 Passwords | Read `users_pass.yml`, filter `department=profs`, `password_hash('sha512')` |

#### Step 4: Exam Practice 3 — Conditionals + Vault Rotate + Time + Group Vars

| # | Status | ID | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 15 | not completed | RHCE-F15 | Conditional Package Installation by Host Group | perl/php on dev/test/prod, "Virtualization Host" on prod, `dnf upgrade` prod |
| 16 | not completed | RHCE-F16 | Conditional LVM Playbook with Failure Messages | `vgdata` 2GiB prod only, "vgprod does not exist" + insufficient-space messages |
| 17 | not completed | RHCE-F17 | `sysreport.yml` — Hardware Report from a Template | `hwtemplate.txt`, NAME/IPADDRESS/TOTAL_MEMORY/NIC_NAME → `/root/report.txt` |
| 18 | not completed | RHCE-F18 | Ansible Vault Password Rotation | `anspass.txt` with `devpass` + `prodpass`, rekey from `vaultpass` to `myvaultpass` |
| 19 | not completed | RHCE-F19 | RHEL Time Sync System Role (`rhel-system-roles.timesync`) | `settime.yml`, `control.example.com` source, `makestep`, `chronyc tracking` |
| 20 | not completed | RHCE-F20 | `runwebserver.yml` — Web Content with Symlink and Group Vars | `/webcontent/index.html`, `USERNAME=anna` in `group_vars/prod`, symlink to `/var/www/html` |

> **Prerequisite:** finish the **Ansible Track** chapter labs (at minimum Ch 1, Ch 2, Ch 7, Ch 8) before starting RHCE-F01 — Foundation assumes you can read a playbook, write a role, and trace variable precedence.

---

### Foundation (Common Tasks across all sample exams)

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | RHCE-F01 | Build an RHCE Ansible Control Project | `/home/ansible`, `ansible.cfg`, static inventory, groups `test/dev/prod/servers`, FQDN + short-name resolution |
| not completed | RHCE-F02 | Bootstrap Managed Hosts with Ad-Hoc Commands | `setuphosts.sh`: install Python, create `ansible` user, write sudoers drop-in, ping module to verify |
| not completed | RHCE-F03 | Configure a Repository Server with an Ansible Playbook | `setupreposerver.yml`: loop-mount RHEL ISO to `/var/ftp/repo`, disable firewalld, enable vsftpd with anonymous access |
| not completed | RHCE-F04 | Configure Managed Repo Clients with Ad-Hoc Commands | Disable existing repos, add BaseOS + AppStream from `control.example.com` via `dnf config-manager` |

### Exam Practice 1 specifics

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | RHCE-F05 | HTTP Server and Client Playbooks with `site.yml` | `webserver.yml` installs httpd, `webclient.yml` installs curl, shared `vars/web.yml`, `templates/httpd.j2`, handler restarts httpd, `site.yml` ties them together |
| not completed | RHCE-F06 | Convert HTTP Playbooks Into an Ansible Role | Refactor webserver tasks into a role with `defaults/main.yml`, `tasks/main.yml`, `templates/`, `handlers/`, then call from a new top-level play |
| not completed | RHCE-F07 | Ansible Storage Role for `/web` with SELinux Contexts | `parted gpt mkpart 1MiB 100%`, mount `/web`, `semanage fcontext httpd_sys_content_t`, deploy `/web/index.html` with welcome message |

### Exam Practice 2 specifics

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | RHCE-F08 | Default Roles Path in `ansible.cfg` | Set `roles_path = /home/ansible/roles` while preserving system role locations as fallbacks |
| not completed | RHCE-F09 | `setupstorage.yml` — Conditional LVM Playbook | Only on hosts with a second disk: 5GiB partition, `vgdata` with 8MiB PEs, `lvdata` 1GiB, ext3 format, `/data` persistent mount |
| not completed | RHCE-F10 | `packagefacts.yml` — Package Version Report | Gather package facts, format kernel/bash/glibc as `packagename=version` into `/root/packages.txt` |
| not completed | RHCE-F11 | Ansible Vault Credentials Workflow | `cloudpass.yml` with `CLOUDID` and `CLOUDPASS` encrypted, vault password file `vaultpass.txt`, `usevault.yml` reads vars and writes `/root/cloudcreds.txt` |
| not completed | RHCE-F12 | Install Galaxy Roles from `requirements.yml` | `geerlingguy.nginx` + `geerlingguy.docker` into `/home/ansible/roles`, then `start-galaxy-roles.yml` plays both |
| not completed | RHCE-F13 | Apache Role with Custom Template Showing HOSTNAME/IPADDRESS | Role enables httpd, opens firewall, deploys templated index.html using `ansible_facts.hostname` and `ansible_default_ipv4.address`; `runweb.yml` runs it on `test` group |
| not completed | RHCE-F14 | Create Users from YAML Input with SHA256 Passwords | Read `users_pass.yml`; on `prod` create only users whose `department=profs`, set department as secondary group, hash passwords with `password_hash('sha512')` |

### Exam Practice 3 specifics

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | RHCE-F15 | Conditional Package Installation by Host Group | perl/php on dev/test/prod, "Virtualization Host" group on prod only, `dnf upgrade` on prod |
| not completed | RHCE-F16 | Conditional LVM Playbook with Failure Messages | `vgdata` 2GiB only on prod; if missing print "vgprod does not exist"; if <1GiB free print "insufficient disk space available" |
| not completed | RHCE-F17 | `sysreport.yml` — Hardware Report from a Template | Generate `hwtemplate.txt`, copy to `/root/report.txt` on each managed host, populate `NAME`, `IPADDRESS`, `TOTAL_MEMORY`, `NIC_NAME`, `SECOND_NIC_NAME=NONE` if absent |
| not completed | RHCE-F18 | Ansible Vault Password Rotation | Create `anspass.txt` with `devpass` + `prodpass` under password `vaultpass`, then rekey to `myvaultpass` and confirm the file is still readable |
| not completed | RHCE-F19 | RHEL Time Sync System Role (`rhel-system-roles.timesync`) | `settime.yml` uses `control.example.com` as time source with `makestep` enabled; verify `chronyc tracking`; print failure message if not synchronized |
| not completed | RHCE-F20 | `runwebserver.yml` — Web Content with Symlink and Group Vars | Create `/webcontent/index.html` with welcome message, `USERNAME=anna` sourced from a `group_vars/prod` file, symlink `/var/www/html/index.html` to it, prove remote access |

---

## 🎯 CKA Track (Kubernetes Administrator)

### 📋 Complete Labs in This Order

Follows the official CKA exam domain weights (Cluster Architecture 25% → Workloads 15% → Networking 20% → Storage 10% → Troubleshooting 30%). Build the cluster first, deploy on top of it, then break it on purpose.

#### Step 1: Cluster Architecture, Installation, Configuration

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 1 | not completed | CKA #01 | Explore Cluster Components | `kubectl get nodes`, `kubectl cluster-info` |
| 2 | not completed | CKA #02 | Install a Cluster with kubeadm | `kubeadm init`, `kubeadm join` |
| 3 | not completed | CKA-F01 | Highly Available Control Plane with kubeadm | Stacked-etcd HA, `--control-plane-endpoint`, three control planes + VIP/LB |
| 4 | not completed | CKA-F02 | Install Cluster Components with Helm | `helm repo add`, `helm install`, `helm upgrade --atomic`, `helm rollback` |
| 5 | not completed | CKA-F03 | Manage Configs with Kustomize | `base/` + `overlays/dev/`+`overlays/prod/`, `kubectl apply -k`, SecretGenerator |
| 6 | not completed | CKA-F04 | Container Runtime and Extension Interfaces | CRI: `crictl ps` with containerd; CNI: Calico/Cilium; CSI: deploy driver |
| 7 | not completed | CKA-F05 | Install and Configure an Operator with a CRD | OLM or vendor operator, define CRD, watch reconcile |

#### Step 2: Workloads and Scheduling

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 8 | not completed | CKA #03 | Deploy and Manage Pods | `kubectl run`, `kubectl get pods`, `kubectl describe` |
| 9 | not completed | CKA #04 | Create and Scale Deployments | `kubectl create deployment`, `kubectl scale` |
| 10 | not completed | CKA #05 | Configure DaemonSets and Jobs | `kubectl apply -f`, DaemonSet/Job YAML |
| 11 | not completed | CKA-F06 | Perform a Rolling Update and Rollback | `kubectl set image`, `rollout status`, `rollout undo`, `maxSurge`/`maxUnavailable` |
| 12 | not completed | CKA-F07 | Configure Pods with ConfigMaps | `--from-file`, `--from-literal`, project as env vars vs volume mounts |
| 13 | not completed | CKA-F09 | ReplicaSet Self-Healing Demonstration | Delete pod, observe recreation; cordon/drain node, observe reschedule |
| 14 | not completed | CKA-F10 | Resource Limits and LimitRanges | Set requests/limits, apply LimitRange, watch admission rejections |
| 15 | not completed | CKA-F11 | Resource Quotas at Namespace Scope | ResourceQuota for cpu/memory/pods/pvcs, prove rejection |
| 16 | not completed | CKA-F12 | Node Affinity and Anti-Affinity Scheduling | `requiredDuringScheduling…`, podAntiAffinity with `topologyKey=hostname` |
| 17 | not completed | CKA-F13 | Taints and Tolerations | `kubectl taint node ... NoSchedule`, NoExecute + `tolerationSeconds` |
| 18 | not completed | CKA-F14 | Pod Topology Spread Constraints | `maxSkew`, `topologyKey`, `whenUnsatisfiable=DoNotSchedule` |
| 19 | not completed | CKA-F08 | Horizontal Pod Autoscaling | Deploy metrics-server, HPA on CPU, hey/wrk load, watch scale up/down |

#### Step 3: Services and Networking

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 20 | not completed | CKA #06 | Expose Applications with Services | `kubectl expose`, ClusterIP/NodePort/LoadBalancer |
| 21 | not completed | CKA #07 | Configure Ingress | Ingress YAML, `kubectl get ingress` |
| 22 | not completed | CKA #08 | Apply NetworkPolicy | NetworkPolicy YAML, ingress/egress rules |
| 23 | not completed | CKA-F16 | Use Gateway API for Ingress Traffic | Gateway API CRDs, GatewayClass, Gateway, HTTPRoute |
| 24 | not completed | CKA-F17 | Use CoreDNS for Service Discovery | kube-system coredns ConfigMap, custom stub-domain, debug pod nslookup |

#### Step 4: Storage

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 25 | not completed | CKA #09 | Create PersistentVolumes and PVCs | PV/PVC YAML, `kubectl get pv` |
| 26 | not completed | CKA #10 | Configure StorageClasses | StorageClass YAML, dynamic provisioning |
| 27 | not completed | CKA-F15 | Volume Access Modes and Reclaim Policies | RWO/RWX/ROX, `persistentVolumeReclaimPolicy` Retain/Delete/Recycle |

#### Step 5: Security

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 28 | not completed | CKA #11 | Configure RBAC | `Role`, `ClusterRole`, `RoleBinding`, `kubectl auth can-i` |
| 29 | not completed | CKA #12 | Manage Secrets and ServiceAccounts | `kubectl create secret`, ServiceAccount YAML |

#### Step 6: Cluster Maintenance

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 30 | not completed | CKA #13 | Upgrade a Kubernetes Cluster | `kubeadm upgrade`, `apt-get`, `kubectl drain` |
| 31 | not completed | CKA #14 | Back Up and Restore etcd | `etcdctl snapshot save`, `snapshot restore` |

#### Step 7: Troubleshooting (Heaviest Exam Weight)

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 32 | not completed | CKA #15 | Troubleshoot Pods and Deployments | `kubectl logs`, `kubectl describe`, `kubectl exec` |
| 33 | not completed | CKA #16 | Troubleshoot Node and Cluster Failures | `kubectl get nodes`, `systemctl status kubelet` |
| 34 | not completed | CKA-F18 | Monitor Cluster with `kubectl top` and Metrics Server | Deploy metrics-server, `top nodes`, `top pods --containers`, identify hot pods |
| 35 | not completed | CKA-F19 | Manage Container Output Streams | `logs --previous/--tail/--since/-f`, sidecar logging patterns |
| 36 | not completed | CKA-F20 | Troubleshoot Services and Networking | `kubectl get endpoints`, netshoot/busybox, `iptables -t nat -L KUBE-SERVICES` |

> **Prerequisite:** finish RHCSA at least through **Step 4 (SELinux)** and **Step 6 (Storage/LVM)** before starting — CKA assumes you can fix a Linux node, not just `kubectl describe pod`.

---

### README Labs 01–16 (placeholder rows in main README)

| Status | # | Lab | Full Path |
|---|---|---|---|
| not completed | 01 | Explore Cluster Components | *(coming soon — see CKA Lab #01 in [README](README.md#-cluster-architecture))* |
| not completed | 02 | Install a Cluster with kubeadm | *(coming soon — see CKA Lab #02 in [README](README.md#-cluster-architecture))* |
| not completed | 03 | Deploy and Manage Pods | *(coming soon — see CKA Lab #03 in [README](README.md#-workloads))* |
| not completed | 04 | Create and Scale Deployments | *(coming soon — see CKA Lab #04 in [README](README.md#-workloads))* |
| not completed | 05 | Configure DaemonSets and Jobs | *(coming soon — see CKA Lab #05 in [README](README.md#-workloads))* |
| not completed | 06 | Expose Applications with Services | *(coming soon — see CKA Lab #06 in [README](README.md#-kubernetes-networking))* |
| not completed | 07 | Configure Ingress | *(coming soon — see CKA Lab #07 in [README](README.md#-kubernetes-networking))* |
| not completed | 08 | Apply NetworkPolicy | *(coming soon — see CKA Lab #08 in [README](README.md#-kubernetes-networking))* |
| not completed | 09 | Create PersistentVolumes and PVCs | *(coming soon — see CKA Lab #09 in [README](README.md#-kubernetes-storage))* |
| not completed | 10 | Configure StorageClasses | *(coming soon — see CKA Lab #10 in [README](README.md#-kubernetes-storage))* |
| not completed | 11 | Configure RBAC | *(coming soon — see CKA Lab #11 in [README](README.md#-kubernetes-security))* |
| not completed | 12 | Manage Secrets and ServiceAccounts | *(coming soon — see CKA Lab #12 in [README](README.md#-kubernetes-security))* |
| not completed | 13 | Upgrade a Kubernetes Cluster | *(coming soon — see CKA Lab #13 in [README](README.md#-cluster-maintenance))* |
| not completed | 14 | Back Up and Restore etcd | *(coming soon — see CKA Lab #14 in [README](README.md#-cluster-maintenance))* |
| not completed | 15 | Troubleshoot Pods and Deployments | *(coming soon — see CKA Lab #15 in [README](README.md#-kubernetes-troubleshooting))* |
| not completed | 16 | Troubleshoot Node and Cluster Failures | *(coming soon — see CKA Lab #16 in [README](README.md#-kubernetes-troubleshooting))* |

### Future Labs Planned (from [`future_labs.txt`](future_labs.txt))

**Cluster Architecture, Installation, Configuration**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | CKA-F01 | Highly Available Control Plane with kubeadm | Stacked-etcd HA topology with `kubeadm init --control-plane-endpoint`, three control planes behind a VIP/LB, `kubeadm join --control-plane` |
| not completed | CKA-F02 | Install Cluster Components with Helm | `helm repo add`, `helm install`, `helm upgrade --atomic`, `helm rollback`, inspect `helm history` |
| not completed | CKA-F03 | Manage Configs with Kustomize | `base/` + `overlays/dev/` + `overlays/prod/`, `kubectl apply -k`, `kustomize edit set image`, `SecretGenerator` and `ConfigMapGenerator` |
| not completed | CKA-F04 | Container Runtime and Extension Interfaces | CRI: `crictl ps` with containerd; CNI: install Calico or Cilium and inspect `/etc/cni/net.d`; CSI: deploy a CSI driver and validate StorageClass |
| not completed | CKA-F05 | Install and Configure an Operator with a CRD | Install Operator Lifecycle Manager or a vendor operator, define a CRD, create a custom resource, watch the controller reconcile |

**Workloads and Scheduling**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | CKA-F06 | Perform a Rolling Update and Rollback | `kubectl set image deployment/web app=v2`, `kubectl rollout status`, `kubectl rollout undo`, control `maxSurge`/`maxUnavailable` |
| not completed | CKA-F07 | Configure Pods with ConfigMaps | `kubectl create configmap --from-file` and `--from-literal`, project as env vars vs volume mounts, demonstrate hot reload limits |
| not completed | CKA-F08 | Horizontal Pod Autoscaling | Deploy metrics-server, create HPA targeting CPU, hey/wrk load generator, watch `kubectl get hpa` scale up and back down |
| not completed | CKA-F09 | ReplicaSet Self-Healing Demonstration | Delete a pod backed by a ReplicaSet, observe recreation; cordon/drain a node and observe reschedule |
| not completed | CKA-F10 | Resource Limits and LimitRanges | Set requests/limits on a Pod, apply a LimitRange to the namespace, watch admission rejections when exceeded |
| not completed | CKA-F11 | Resource Quotas at Namespace Scope | ResourceQuota for cpu, memory, pods, pvcs; prove rejection of pods that exceed quota |
| not completed | CKA-F12 | Node Affinity and Anti-Affinity Scheduling | `requiredDuringSchedulingIgnoredDuringExecution` vs preferred; labels on nodes; podAntiAffinity with `topologyKey=kubernetes.io/hostname` |
| not completed | CKA-F13 | Taints and Tolerations | `kubectl taint node ... NoSchedule`, matching tolerations on workloads, NoExecute eviction and `tolerationSeconds` |
| not completed | CKA-F14 | Pod Topology Spread Constraints | Spread pods across zones with `maxSkew`, `topologyKey`, `whenUnsatisfiable=DoNotSchedule` |

**Storage**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | CKA-F15 | Volume Access Modes and Reclaim Policies | RWO vs RWX vs ROX, `persistentVolumeReclaimPolicy` Retain vs Delete vs Recycle, demonstrate each state transition |

**Servicing and Networking**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | CKA-F16 | Use Gateway API for Ingress Traffic | Install Gateway API CRDs, define a GatewayClass, Gateway, and HTTPRoute, replace a classic Ingress resource |
| not completed | CKA-F17 | Use CoreDNS for Service Discovery | Inspect kube-system coredns ConfigMap, add a custom stub-domain, validate DNS resolution from a debug pod with `nslookup` |

**Troubleshooting**

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | CKA-F18 | Monitor Cluster with `kubectl top` and Metrics Server | Deploy metrics-server, `kubectl top nodes`, `kubectl top pods --containers`, identify hot pods |
| not completed | CKA-F19 | Manage Container Output Streams | `kubectl logs --previous`, `--tail`, `--since`, `-f` to follow, sidecar logging patterns |
| not completed | CKA-F20 | Troubleshoot Services and Networking | `kubectl get endpoints`, validate Service selectors, debug from within the cluster using netshoot or busybox, trace via `iptables -t nat -L KUBE-SERVICES` |

---

## 🎯 CKAD Track (Kubernetes Application Developer)

> All entries below are Planned — sourced from the CKAD Study Guide Appendix B (all five curriculum domains).

### 📋 Complete Labs in This Order

Domains follow the official CKAD curriculum weights (Design 20% → Deployment 20% → Observability 15% → Environment/Config/Security 25% → Networking 20%). Build images and Pods first, then layer in rollout strategies, probes, configuration, and finally Services + Ingress.

#### Step 1: Application Design and Build

| # | Status | ID | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 1 | not completed | CKAD-DES-F01 | Build a Container Image from a Dockerfile/Containerfile | Dockerfile FROM `python:3.12-slim`, `podman build`, push, `kubectl run` |
| 2 | not completed | CKAD-DES-F02 | Run a Kubernetes Job (One-Shot Batch Task) | `kind: Job`, `completions: 5`, `parallelism: 2`, `backoffLimit: 4` |
| 3 | not completed | CKAD-DES-F03 | Schedule a Kubernetes CronJob | `kind: CronJob`, `schedule: "*/5 * * * *"`, `kubectl get jobs --watch` |
| 4 | not completed | CKAD-DES-F04 | Multi-Container Pod: Sidecar Logging Pattern | shared emptyDir `/var/log`, busybox sidecar `tail -F app.log` |
| 5 | not completed | CKAD-DES-F05 | Multi-Container Pod: Init Container for Pre-Start Setup | `initContainers` wget config into emptyDir, main waits for init |
| 6 | not completed | CKAD-DES-F06 | Persistent Volume + PVC Workflow End-to-End | PVC `ReadWriteOnce` + `1Gi`, file survives Pod recreation |
| 7 | not completed | CKAD-DES-F07 | Ephemeral Volume Shared Between Containers (emptyDir) | emptyDir `/shared` in both containers, gone on Pod deletion |

#### Step 2: Application Deployment

| # | Status | ID | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 8 | not completed | CKAD-DEP-F01 | Canary Deployment with One Service + Two Deployments | v1 `replicas: 9` + v2 `replicas: 1`, Service selects only `app: web` |
| 9 | not completed | CKAD-DEP-F02 | Blue-Green Deployment via Service Selector Switch | `color: blue` → `color: green`, smoke-test, `kubectl patch svc` |
| 10 | not completed | CKAD-DEP-F03 | Deploy an Application via Helm Chart with Custom Values | `helm install --set service.type=NodePort,replicaCount=3`, upgrade --atomic, rollback |

#### Step 3: Application Observability and Maintenance

| # | Status | ID | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 11 | not completed | CKAD-OBS-F01 | Configure Liveness + Readiness + Startup Probes Together | httpGet/tcpSocket/`failureThreshold: 30` probes at `/healthz` |
| 12 | not completed | CKAD-OBS-F02 | Identify Deprecated API Versions and Migrate Manifests | `kubectl api-resources`, rewrite `extensions/v1beta1` → `apps/v1`, `--dry-run=server` |
| 13 | not completed | CKAD-OBS-F03 | Debug a Failing Pod End-to-End | CrashLoopBackOff: `describe`, `logs --previous`, `exec`, `kubectl debug`, `port-forward` |

#### Step 4: Application Environment, Configuration & Security

| # | Status | ID | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 14 | not completed | CKAD-ENV-F03 | Pod Resource Requests and Limits (CPU + Memory) | `requests.cpu: 100m`/`memory: 128Mi`, limits `500m`/`256Mi`, watch OOMKilled |
| 15 | not completed | CKAD-ENV-F04 | ConfigMap Injection: env vs envFrom vs Volume Mount | `valueFrom.configMapKeyRef`, `envFrom.configMapRef`, volume mount — all three in one Pod |
| 16 | not completed | CKAD-ENV-F05 | Secret Patterns: Env Injection vs Mounted File | `envFrom.secretRef`, mount at `/etc/db`, rotate by re-creating Secret |
| 17 | not completed | CKAD-ENV-F06 | Custom ServiceAccount with Pod Binding | `create sa myapp-sa`, `serviceAccountName`, projected token at `/var/run/secrets/...` |
| 18 | not completed | CKAD-ENV-F02 | RBAC: Role + RoleBinding for a ServiceAccount | Role `[get, list, watch]` on pods, prove via `kubectl auth can-i` |
| 19 | not completed | CKAD-ENV-F07 | SecurityContext: runAsUser, fsGroup, Capabilities, ROFS | `runAsUser: 1000`, `fsGroup: 2000`, drop ALL, add `NET_BIND_SERVICE` |
| 20 | not completed | CKAD-ENV-F01 | Define a Custom Resource Definition and a Custom Resource | `kind: CustomResourceDefinition`, openAPIV3Schema validation |

#### Step 5: Services and Networking

| # | Status | ID | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 21 | not completed | CKAD-NET-F02 | Service Types: ClusterIP vs NodePort vs LoadBalancer vs ExternalName | Expose same backend four ways, verify reachability for each |
| 22 | not completed | CKAD-NET-F01 | NetworkPolicy: Default-Deny + Allow Specific Ingress | `podSelector: {}` blocks all, second policy allows `role: frontend` (needs Calico/Cilium) |
| 23 | not completed | CKAD-NET-F03 | Ingress with Path-Based Routing and TLS Termination | NGINX Ingress, `/api` + `/web` backends, self-signed cert + `kubernetes.io/tls` Secret |

> **Prerequisite:** finish CKA **Steps 1–4** (cluster up + workloads + services + storage) before CKAD — you can't deploy applications cleanly on a cluster you can't troubleshoot.

---

### Application Design and Build

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | CKAD-DES-F01 | Build a Container Image from a Dockerfile/Containerfile | Write a Dockerfile FROM `python:3.12-slim`, COPY app.py, CMD `python app.py`; `podman build -t myapp:1.0`, push to local registry, `kubectl run myapp --image=...`, verify with `kubectl describe pod` |
| not completed | CKAD-DES-F02 | Run a Kubernetes Job (One-Shot Batch Task) | `kind: Job` spec with `completions: 5`, `parallelism: 2`, `backoffLimit: 4`, container command runs to completion; verify with `kubectl get jobs` and `kubectl logs job/myjob` |
| not completed | CKAD-DES-F03 | Schedule a Kubernetes CronJob | `kind: CronJob` with `schedule: "*/5 * * * *"`, jobTemplate runs `date` and echoes to stdout, prove with `kubectl get cronjob` and `kubectl get jobs --watch` |
| not completed | CKAD-DES-F04 | Multi-Container Pod: Sidecar Logging Pattern | Main container writes to `/var/log/app.log`; sidecar `busybox` runs `tail -F /var/log/app.log`; shared emptyDir at `/var/log`; verify with `kubectl logs POD -c sidecar` |
| not completed | CKAD-DES-F05 | Multi-Container Pod: Init Container for Pre-Start Setup | `initContainers` run `wget` to fetch a config file into a shared emptyDir; main container starts only after init succeeds; verify with `kubectl describe pod` |
| not completed | CKAD-DES-F06 | Persistent Volume + PVC Workflow End-to-End | StorageClass-backed PV or static hostPath PV, PVC with `ReadWriteOnce` + `1Gi`; Pod consumes the claim; write a file; delete Pod; new Pod with same PVC sees the file |
| not completed | CKAD-DES-F07 | Ephemeral Volume Shared Between Containers (emptyDir) | Pod with two containers + emptyDir volume mounted at `/shared` in both; one writes, the other reads; verify emptyDir does NOT survive Pod deletion |

### Application Deployment

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | CKAD-DEP-F01 | Canary Deployment with One Service + Two Deployments | Deployment v1 `replicas: 9` + label `version: v1`, Deployment v2 `replicas: 1` + label `version: v2`, Service selector matches only `app: web` so traffic splits ~90/10 |
| not completed | CKAD-DEP-F02 | Blue-Green Deployment via Service Selector Switch | Two Deployments labelled `color: blue` and `color: green`, Service starts on `color: blue`, deploy green, smoke-test via debug Pod, `kubectl patch svc` to flip selector |
| not completed | CKAD-DEP-F03 | Deploy an Application via Helm Chart with Custom Values | `helm repo add bitnami`, `helm install myapp bitnami/nginx --set service.type=NodePort,replicaCount=3`, prove with `helm list` + `kubectl get all -l app.kubernetes.io/instance=myapp` |

### Application Observability and Maintenance

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | CKAD-OBS-F01 | Configure Liveness + Readiness + Startup Probes Together | Deployment with three probe types at `/healthz`: livenessProbe httpGet, readinessProbe tcpSocket, startupProbe with `failureThreshold: 30`; break `/healthz` and watch kubelet restart |
| not completed | CKAD-OBS-F02 | Identify Deprecated API Versions and Migrate Manifests | Run `kubectl api-resources` and `kubectl api-versions`, identify apps using removed APIs like `extensions/v1beta1`, rewrite to current `apps/v1` |
| not completed | CKAD-OBS-F03 | Debug a Failing Pod End-to-End | `kubectl get pods` shows CrashLoopBackOff; `kubectl describe pod` for events; `kubectl logs --previous`; `kubectl exec -it POD -- sh`; ephemeral debug via `kubectl debug` for distroless |

### Application Environment, Configuration, and Security

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | CKAD-ENV-F01 | Define a Custom Resource Definition and a Custom Resource | `kind: CustomResourceDefinition` with group, names, versions, openAPIV3Schema validation; create a custom resource of that kind; verify with `kubectl get crd` |
| not completed | CKAD-ENV-F02 | RBAC: Role + RoleBinding for a ServiceAccount | ServiceAccount `read-only`, Role with verbs `[get, list, watch]` on pods, RoleBinding wiring SA to Role; Pod with `serviceAccountName: read-only` can list pods but not create them via `kubectl auth can-i` |
| not completed | CKAD-ENV-F03 | Pod Resource Requests and Limits (CPU + Memory) | `resources.requests.cpu: 100m`, `requests.memory: 128Mi`, `limits.cpu: 500m`, `limits.memory: 256Mi`; deploy a stress-test Pod that exceeds memory and watch OOMKilled event |
| not completed | CKAD-ENV-F04 | ConfigMap Injection: env vs envFrom vs Volume Mount | One ConfigMap with three keys; demonstrate `env.valueFrom.configMapKeyRef`, `envFrom.configMapRef`, and `volumes.configMap` + `volumeMounts`; show all three patterns in one Pod manifest |
| not completed | CKAD-ENV-F05 | Secret Patterns: Env Injection vs Mounted File | `kubectl create secret generic db --from-literal=password=s3cret`, inject via `envFrom.secretRef`, also mount at `/etc/db`; observe base64 is decoded at injection |
| not completed | CKAD-ENV-F06 | Custom ServiceAccount with Pod Binding | `kubectl create sa myapp-sa`, `kubectl create token myapp-sa`, Pod spec with `serviceAccountName: myapp-sa`, verify projected token works against the API |
| not completed | CKAD-ENV-F07 | SecurityContext: runAsUser, fsGroup, Capabilities, ROFS | Pod-level securityContext with `runAsUser: 1000`, `runAsGroup: 1000`, `fsGroup: 2000`, `readOnlyRootFilesystem: true`, `capabilities.drop: ["ALL"]`, `capabilities.add: ["NET_BIND_SERVICE"]` |

### Services and Networking

| Status | ID | Lab | Details |
|---|---|---|---|
| not completed | CKAD-NET-F01 | NetworkPolicy: Default-Deny + Allow Specific Ingress | NetworkPolicy with `podSelector: {}` + `policyTypes: [Ingress]` blocks ALL ingress; second NetworkPolicy allows ingress from pods with `role: frontend`; verify with `kubectl exec` and `curl` |
| not completed | CKAD-NET-F02 | Service Types: ClusterIP vs NodePort vs LoadBalancer vs ExternalName | Deploy same backend, expose via four Service types in turn, verify reachability for each |
| not completed | CKAD-NET-F03 | Ingress with Path-Based Routing and TLS Termination | Deploy NGINX Ingress Controller or Traefik, Ingress with two backends `/api → backend1`, `/web → backend2`, provision self-signed cert + Secret `kubernetes.io/tls`, attach via `spec.tls` |

---

## 🎯 Ansible Track (Mastering Ansible 4th Ed. + RHCE Companion Repos)

> Two layers stacked here:
> 1. **Currently Built — RHCE Ansible Companion Repos** (15 standalone repos that already exist; numbering matches the main [README](README.md#-rhce-ex294-labs))
> 2. **Future Labs Planned — Mastering Ansible 4th Edition** (73 labs across chapters 1, 2, 7, 8, 13, sourced from [`future_labs.txt`](future_labs.txt))
>
> For the scenario-based RHCE labs (build the whole control project, run sample-exam playbooks end-to-end), see the [RHCE Track (EX294)](#-rhce-track-ex294) section above.

### 📋 Complete Labs in This Order

Read each *Mastering Ansible, 4th Ed.* chapter first, then work the matching companion-repo lab, then drill the chapter's future labs. This gets you fluent in the chapter's mental model before you grind individual edge cases.

#### Step 1: Ch 1 — System Architecture & Design

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 1 | not completed | RHCE #01 | Ansible Architecture & Inventory | `ansible.cfg`, inventory, `group_vars`, `host_vars`, `ansible-inventory --graph` |
| 2 | not completed | ANS-CH1-F01 | Static INI Inventory with Groups, Children, and Group-Vars | `mastery-hosts` with `[frontend:children]`, `[backend:children]`, group_vars file |
| 3 | not completed | ANS-CH1-F02 | Behavioral Inventory Variables Cheat-Sheet Playbook | `ansible_host`, `ansible_port`, `ansible_user`, `ansible_connection`, `_become_*` |
| 4 | not completed | ANS-CH1-F03 | Inventory Ordering: inventory / reverse_inventory / sorted / reverse_sorted / shuffle | Play-level `order:` keyword, mastery1/11/2 lexicographic gotcha |
| 5 | not completed | ANS-CH1-F04 | AWS EC2 Dynamic Inventory Plugin Bring-Up | `amazon.aws` collection, `aws_ec2` plugin YAML, `boto_profile`, key/cert |
| 6 | not completed | ANS-CH1-F05 | Runtime Inventory Additions with `ansible.builtin.add_host` | Provision then `add_host` mid-play, manage the new host in next play |
| 7 | not completed | ANS-CH1-F06 | Inventory Limiting with `--limit` + Cross-Host hostvars Access | `--limit frontend`, prove `hostvars['backend...']` still readable |
| 8 | not completed | ANS-CH1-F07 | YAML vs INI Inventory Equivalence Audit | Convert INI inventory → YAML, diff `--list` output, prove identical |
| 9 | not completed | ANS-CH1-F08 | Static + Dynamic Inventory Combined (Directory-Based Inventory) | `-i inventory/` directory mixing static + plugin sources |
| 10 | not completed | ANS-CH1-F09 | Strict Play Order: pre_tasks → roles → tasks → post_tasks → handlers | Scrambled YAML, execution-order proof |
| 11 | not completed | ANS-CH1-F10 | Handler Flushing with `meta: flush_handlers` | Force handler to fire mid-play instead of waiting for end |
| 12 | not completed | ANS-CH1-F11 | Relative Path Resolution for vars_files and include | tasks/a.yaml, tasks/b.yaml, file-relative paths in nested includes |
| 13 | not completed | ANS-CH1-F12 | Linear vs Free vs Debug Execution Strategies | `strategy:` keyword, `serial: 2`, `pause` race demonstration |
| 14 | not completed | ANS-CH1-F13 | Host Pattern Selection: groups, wildcards, regex, &, ! | Intersection, exclusion, regex matching on inventory |
| 15 | not completed | ANS-CH1-F14 | Play and Task Names with Variables — When Templating Works | Play vars vs set_fact vs runtime templating differences |
| 16 | not completed | ANS-CH1-F15 | Variable Precedence Pyramid: prove all 21 levels | extra-vars > set_fact > task-vars > … > role defaults |
| 17 | not completed | ANS-CH1-F16 | Magic Variables Tour: inventory_hostname / group_names / hostvars / play_hosts / ansible_play_batch | Parse-time vs execution-time magic vars |
| 18 | not completed | ANS-CH1-F17 | `ansible_group_priority` for Conflict Resolution | Alphabetical sort tiebreaker, override with `ansible_group_priority` |
| 19 | not completed | ANS-CH1-F18 | Hash Merge vs Replace via `hash_behavior` | `hash_behavior=merge` vs default replace, dict overlay |
| 20 | not completed | ANS-CH1-F19 | Lookup Plugins: file / env / pipe / password / dnstxt | `lookup('file'/'env'/'pipe'/'password'/'dig', ...)` |
| 21 | not completed | ANS-CH1-F20 | vars_prompt for Interactive Variable Capture | `vars_prompt`, `private: yes`, `encrypt: sha512` for passwords |
| 22 | not completed | ANS-CH1-F21 | SSH ControlPersist + Pipelining Performance Benchmark | `pipelining=true`, `ControlPersist`, time savings comparison |
| 23 | not completed | ANS-CH1-F22 | Ansible Forks Tuning | `forks=5` vs `forks=20`, `time` comparison on parallel hosts |
| 24 | not completed | ANS-CH1-F23 | Module Discovery Path Order (role library → playbook library → ANSIBLE_LIBRARY → /usr/share/ansible) | Shadow `debug` module at each level |
| 25 | not completed | ANS-CH1-F24 | Module Blacklisting with plugin_filters.yml | `module_blacklist: [debug]`, prove play fails with helpful error |
| 26 | not completed | ANS-CH1-F25 | Module Argument Formats: free-form vs key=value vs YAML hash | Three forms of same `user` module call |

#### Step 2: Ch 2 — Collections / FQCNs / Migration

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 27 | not completed | RHCE #02 | Ansible Collections & Migration | `ansible-galaxy collection install`, FQCN, `requirements.yml` |
| 28 | not completed | ANS-CH2-F01 | Clean Reinstall: Remove Ansible 2.9 / 3.x, Install Ansible 4.3 | Uninstall via dnf/apt/pip, install 4.3 fresh, verify `ansible --version` |
| 29 | not completed | ANS-CH2-F02 | Pip + virtualenv: Two Side-by-Side Ansible Versions | `ansible-2.9` and `ansible-4.3` virtualenvs, activation gates version |
| 30 | not completed | ANS-CH2-F03 | Build Your First Custom Collection (`masterybook.demo`) | `collection init`, populate `plugins/`, `collection build`, `.tar.gz` artifact |
| 31 | not completed | ANS-CH2-F04 | Install Your Custom Collection Locally via `collections_paths` | Set `collections_paths`, install tarball, call modules via FQCN |
| 32 | not completed | ANS-CH2-F05 | FQCN vs Short Module Names — Shadowing Demo | Custom `pause` module shadowing core, FQCN forces correct module |
| 33 | not completed | ANS-CH2-F06 | Collection Installation from Git URL | `git+https://github.com/.../...,branch=main`, verify with `ansible-doc -l` |
| 34 | not completed | ANS-CH2-F07 | Bulk Collection Install via requirements.yml | `geerlingguy.k8s` + `geerlingguy.php_roles` pinned by version |
| 35 | not completed | ANS-CH2-F08 | Semantic Versioning Walk-Through for Ansible Packages | 4.0.0 → 4.3.0 → 5.0.0 compatibility for ansible-base modules |
| 36 | not completed | ANS-CH2-F09 | Discover All Modules in a Collection via `ansible-doc -l` | `ansible-doc -l cisco.ios`, `community.aws`, `amazon.aws` |
| 37 | not completed | ANS-CH2-F10 | Force-Install a Pre-Release / Dev Collection Version | `--force`, `amazon.aws:==1.4.2-dev9` |
| 38 | not completed | ANS-CH2-F11 | Publish a Collection to Ansible Galaxy | Galaxy account, API key, `ansible-galaxy collection publish` |

#### Step 3: Ch 3 — Ansible Vault

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 39 | not completed | RHCE #08 | Ansible Vault — Secrets at Rest | `ansible-vault create`, `encrypt_string`, `--vault-id`, `no_log` |

#### Step 4: Ch 6 — Jinja2 Templates

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 40 | not completed | RHCE #07 | Jinja2 Templates in Ansible | `ansible.builtin.template`, `{{ }}`, `{% if %}`, filters, whitespace control |

#### Step 5: Ch 7 — Task Conditions, Error Recovery, Loops

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 41 | not completed | RHCE #03 | Task Conditions, Blocks & Loops | `when`, `failed_when`, `block`/`rescue`/`always`, `loop` |
| 42 | not completed | ANS-CH7-F01 | `ignore_errors: true` on a Deliberately-Failing URI Task | `ansible.builtin.uri` against bad host, play keeps running |
| 43 | not completed | ANS-CH7-F02 | `failed_when` for iscsiadm Exit Code Tolerance | `failed_when: sessions.rc not in (0, 21)` |
| 44 | not completed | ANS-CH7-F03 | Multi-Condition `failed_when` as YAML List (Git Branch Delete) | YAML-list condition implicit AND of branch-missing + non-error stderr |
| 45 | not completed | ANS-CH7-F04 | `changed_when` to Suppress False-Positive Changes | `changed_when: gitout.rc == 0`, idempotent reports `ok=` not `changed=` |
| 46 | not completed | ANS-CH7-F05 | `creates` / `removes` for Command-Family Idempotency | `args: creates:`, idempotent script that skips if file exists |
| 47 | not completed | ANS-CH7-F06 | Pure Data-Gathering Tasks with `changed_when: false` | Gather-only task can only be `ok` or `failed`, never `changed` |
| 48 | not completed | ANS-CH7-F07 | `block` + `rescue` for Graceful Cleanup | Block fails → rescue logs → post-block task still runs |
| 49 | not completed | ANS-CH7-F08 | `block` + `rescue` + `always` (Three-Section Block) | `always` runs whether block fails or not |
| 50 | not completed | ANS-CH7-F09 | `ignore_unreachable: true` Against an Inventory of Dead Hosts | Continue when DNS-resolved IPs are unreachable |
| 51 | not completed | ANS-CH7-F10 | Modern `loop:` vs Legacy `with_items:` Equivalence | Identical output, `with_items` deprecation warning |
| 52 | not completed | ANS-CH7-F11 | `until` / `retries` / `delay` Loop Waiting for /tmp/flag | Poll every 10s, give up after 5 attempts |
| 53 | not completed | ANS-CH7-F12 | Nested Loops with `product` Filter and `loop_control.loop_var` | `paths × files`, `loop_control: loop_var: pathname` to avoid collision |

#### Step 6: Ch 8 — Roles, Includes & ansible-galaxy

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 54 | not completed | RHCE #05 | Ansible Roles | `ansible-galaxy init`, `tasks/`, `handlers/`, `defaults/`, `notify` |
| 55 | not completed | ANS-CH8-F01 | Basic Task Inclusion with `ansible.builtin.include` | `includer.yaml` runs inline → included → after, order preserved |
| 56 | not completed | ANS-CH8-F02 | Passing Variables Inline to Included Tasks | `files.yaml` with `path` + `file` vars, reusable across plays |
| 57 | not completed | ANS-CH8-F03 | Passing Complex Hash Data to Included Tasks via dict2items | `files: {herp:..., derp:...}`, `dict2items` loop with attribute access |
| 58 | not completed | ANS-CH8-F04 | Conditional Include with `when: item \| bool` | Iterate `[true, false]`, skip false items entirely |
| 59 | not completed | ANS-CH8-F05 | Tagged Task Includes for Selective Execution | `--tags second`, per-include vars survive tag filter |
| 60 | not completed | ANS-CH8-F06 | Looping Over a Task Include with `loop_control: loop_var` | Outer `include_item`, inner `item`, no collision |
| 61 | not completed | ANS-CH8-F07 | Handler Inclusion with `when` on the Include Statement | Trigger handler with `-e foo=false` skip |
| 62 | not completed | ANS-CH8-F08 | `vars_files` Static Inclusion vs `include_vars` Dynamic Inclusion | Parse-time vs task-time variable load |
| 63 | not completed | ANS-CH8-F09 | `include_vars` with `with_first_found` for OS-Specific Vars | `{{ ansible_distribution }}.yaml` fallback chain |
| 64 | not completed | ANS-CH8-F10 | Loading Extra Vars from a File via `-e @file.yaml` | `-e @variables.yaml` extra-vars from file |
| 65 | not completed | ANS-CH8-F11 | `import_playbook` for Composing Multi-Playbook Workflows | Master playbook imports children in order |
| 66 | not completed | ANS-CH8-F12 | Build a Role From Scratch with `ansible-galaxy role init` | `init --init-path roles/ simple`, populate `defaults/`, `tasks/`, `handlers/` |
| 67 | not completed | ANS-CH8-F13 | Role Dependencies with Variables + Tags + Conditionals | `meta/main.yaml` dependencies pass vars + tags |
| 68 | not completed | ANS-CH8-F14 | pre_tasks / roles / tasks / post_tasks Handler-Flush Ordering | Handler fires 3 times, one per section, prove by counter file |
| 69 | not completed | ANS-CH8-F15 | Install Roles from Ansible Galaxy + Git + tarball + requirements.yml | `angstwad.docker_ubuntu`, git+repo, bulk install |

#### Step 7: Ch 9 — Troubleshooting

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 70 | not completed | RHCE #09 | Troubleshooting Ansible | `--syntax-check`, `--check`, `--diff`, `-vvv`, `ansible-doc` |

#### Step 8: Ch 4 — Windows Automation

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 71 | not completed | RHCE #10 | Windows Automation | WinRM, `ansible.windows`, IIS, registry/services automation |

#### Step 9: Ch 5 — AWX / Tower

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 72 | not completed | RHCE #11 | AWX / Tower | AWX Operator, Projects, Job Templates, REST launch |

#### Step 10: Ch 10 — Extending Ansible

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 73 | not completed | RHCE #12 | Extending Ansible with Modules and Plugins | `AnsibleModule`, `library/`, `filter_plugins/`, custom module |

#### Step 11: Ch 11 — Rolling Deployments

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 74 | not completed | RHCE #13 | Rolling Deployments | `serial`, `max_fail_percentage`, `wait_for`, LB drain pattern |

#### Step 12: Ch 12 — Infrastructure Provisioning

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 75 | not completed | RHCE #14 | Infrastructure Provisioning | `amazon.aws.ec2_instance`, dynamic inventory, post-provision config |

#### Step 13: Ch 13 — Network Automation

| # | Status | ID / # | Full Lab Name | Key Commands / Focus |
|---|---|---|---|---|
| 76 | not completed | RHCE #15 | Network Automation | `network_cli`, network collections, config backup |
| 77 | not completed | ANS-CH13-F01 | Choosing the Right Connection Protocol: local vs network_cli vs netconf vs httpapi | Decision matrix for IOS/EOS/F5/Cumulus |
| 78 | not completed | ANS-CH13-F02 | Inventory for Cisco IOS via `ansible.netcommon.network_cli` | `[ios_devices]` group, `cisco.ios.ios_facts` smoke test |
| 79 | not completed | ANS-CH13-F03 | Save Running Config on Cisco IOS with `cisco.ios.ios_config` | `save_when: always`, prove second run is idempotent |
| 80 | not completed | ANS-CH13-F04 | Bring Up an Arista vEOS Switch from Zero | `zerotouch cancel`, admin password, mgmt IP via console |
| 81 | not completed | ANS-CH13-F05 | Configure Arista EOS Interfaces with `arista.eos.eos_interfaces` | `eos_interfaces`, `save_when: modified` |
| 82 | not completed | ANS-CH13-F06 | Configure Cumulus Linux Layer-2 Bridge with `community.network.nclu` | Jinja2 for-loop swp1..swp3, `commit: true` |
| 83 | not completed | ANS-CH13-F07 | Multi-Vendor Inventory with `[switches:children]` Grouping | `[eos]` + `[cumulus]` under `[switches:children]`, single play |
| 84 | not completed | ANS-CH13-F08 | Conditional Fact-Gathering for Different Network OSes | `eos_facts` vs `setup` based on `ansible_network_os` |
| 85 | not completed | ANS-CH13-F09 | Jump Host / Bastion via `ansible_ssh_common_args` ProxyCommand | `ProxyCommand="ssh -W %h:%p bastion01"` |
| 86 | not completed | ANS-CH13-F10 | Raw-Command Fallback for Unsupported Devices via `ansible.builtin.raw` | TP-Link or unmanaged switch with SSH only, no Python |

#### Step 14: Capstone — RHCE Sample Exams

Move to the [RHCE Track (EX294)](#-rhce-track-ex294) section and work all 20 RHCE-F## labs in order: **RHCE-F01…F04** (Foundation) → **RHCE-F05…F07** (Exam 1) → **RHCE-F08…F14** (Exam 2) → **RHCE-F15…F20** (Exam 3).

> **Prerequisite:** finish RHCSA at least through **Step 7 (Packages, Users, Sudo)** — Ansible automates everything RHCSA teaches by hand, and you can't write a correct playbook for a system you can't configure manually.

---

### Currently Built — RHCE Ansible Companion Repos

| Status | # / Ch | Lab | Full Path |
|---|---|---|---|
| not completed | 01 / Ch 1 | Ansible Architecture & Inventory | <https://github.com/kelvintechnical/ansible-architecture-and-inventory> |
| not completed | 02 / Ch 2 | Ansible Collections & Migration | <https://github.com/kelvintechnical/ansible-collections-and-migration> |
| not completed | 03 / Ch 7 | Task Conditions, Blocks & Loops | <https://github.com/kelvintechnical/ansible-task-conditions-loops> |
| not completed | 04 | Write Your First Playbook | *(coming soon — see RHCE Lab #04 in [README](README.md#-ansible-playbooks))* |
| not completed | 05 / Ch 8 | Ansible Roles | <https://github.com/kelvintechnical/ansible-roles> |
| not completed | 06 | Use Roles from Ansible Galaxy | *(coming soon — see RHCE Lab #06 in [README](README.md#-ansible-roles))* |
| not completed | 07 / Ch 6 | Jinja2 Templates in Ansible | <https://github.com/kelvintechnical/ansible-jinja2-templates> |
| not completed | 08 / Ch 3 | Ansible Vault — Secrets at Rest | <https://github.com/kelvintechnical/ansible-vault-secrets> |
| not completed | 09 / Ch 9 | Troubleshooting Ansible | <https://github.com/kelvintechnical/ansible-troubleshooting> |
| not completed | 10 / Ch 4 | Windows Automation | <https://github.com/kelvintechnical/ansible-windows-automation> |
| not completed | 11 / Ch 5 | AWX / Tower | <https://github.com/kelvintechnical/ansible-awx-tower> |
| not completed | 12 / Ch 10 | Extending Ansible with Modules and Plugins | <https://github.com/kelvintechnical/ansible-extending-modules-plugins> |
| not completed | 13 / Ch 11 | Rolling Deployments | <https://github.com/kelvintechnical/ansible-rolling-deployments> |
| not completed | 14 / Ch 12 | Infrastructure Provisioning | <https://github.com/kelvintechnical/ansible-infrastructure-provisioning> |
| not completed | 15 / Ch 13 | Network Automation | <https://github.com/kelvintechnical/ansible-network-automation> |

### Future Labs Planned — Mastering Ansible, 4th Edition

#### 🗂 Ch 1 — System Architecture & Design (25 labs)

**Inventory Architecture**

| Status | ID | Lab |
|---|---|---|
| not completed | ANS-CH1-F01 | Static INI Inventory with Groups, Children, and Group-Vars |
| not completed | ANS-CH1-F02 | Behavioral Inventory Variables Cheat-Sheet Playbook |
| not completed | ANS-CH1-F03 | Inventory Ordering: inventory / reverse_inventory / sorted / reverse_sorted / shuffle |
| not completed | ANS-CH1-F04 | AWS EC2 Dynamic Inventory Plugin Bring-Up |
| not completed | ANS-CH1-F05 | Runtime Inventory Additions with `ansible.builtin.add_host` |
| not completed | ANS-CH1-F06 | Inventory Limiting with `--limit` + Cross-Host hostvars Access |
| not completed | ANS-CH1-F07 | YAML vs INI Inventory Equivalence Audit |
| not completed | ANS-CH1-F08 | Static + Dynamic Inventory Combined (Directory-Based Inventory) |

**Playbook Parsing & Execution Order**

| Status | ID | Lab |
|---|---|---|
| not completed | ANS-CH1-F09 | Strict Play Order: pre_tasks → roles → tasks → post_tasks → handlers |
| not completed | ANS-CH1-F10 | Handler Flushing with `meta: flush_handlers` |
| not completed | ANS-CH1-F11 | Relative Path Resolution for vars_files and include |
| not completed | ANS-CH1-F12 | Linear vs Free vs Debug Execution Strategies |
| not completed | ANS-CH1-F13 | Host Pattern Selection: groups, wildcards, regex, &, ! |
| not completed | ANS-CH1-F14 | Play and Task Names with Variables — When Templating Works |

**Variable Precedence & Magic Variables**

| Status | ID | Lab |
|---|---|---|
| not completed | ANS-CH1-F15 | Variable Precedence Pyramid: prove all 21 levels |
| not completed | ANS-CH1-F16 | Magic Variables Tour: inventory_hostname / group_names / hostvars / play_hosts / ansible_play_batch |
| not completed | ANS-CH1-F17 | `ansible_group_priority` for Conflict Resolution |
| not completed | ANS-CH1-F18 | Hash Merge vs Replace via `hash_behavior` |
| not completed | ANS-CH1-F19 | Lookup Plugins: file / env / pipe / password / dnstxt |
| not completed | ANS-CH1-F20 | vars_prompt for Interactive Variable Capture |

**Module Transport, Performance & Safety**

| Status | ID | Lab |
|---|---|---|
| not completed | ANS-CH1-F21 | SSH ControlPersist + Pipelining Performance Benchmark |
| not completed | ANS-CH1-F22 | Ansible Forks Tuning |
| not completed | ANS-CH1-F23 | Module Discovery Path Order (role library → playbook library → ANSIBLE_LIBRARY → /usr/share/ansible) |
| not completed | ANS-CH1-F24 | Module Blacklisting with plugin_filters.yml |
| not completed | ANS-CH1-F25 | Module Argument Formats: free-form vs key=value vs YAML hash |

#### 📦 Ch 2 — Migration / Collections / FQCNs (11 labs)

| Status | ID | Lab |
|---|---|---|
| not completed | ANS-CH2-F01 | Clean Reinstall: Remove Ansible 2.9 / 3.x, Install Ansible 4.3 |
| not completed | ANS-CH2-F02 | Pip + virtualenv: Two Side-by-Side Ansible Versions |
| not completed | ANS-CH2-F03 | Build Your First Custom Collection (`masterybook.demo`) |
| not completed | ANS-CH2-F04 | Install Your Custom Collection Locally via `collections_paths` |
| not completed | ANS-CH2-F05 | FQCN vs Short Module Names — Shadowing Demo |
| not completed | ANS-CH2-F06 | Collection Installation from Git URL |
| not completed | ANS-CH2-F07 | Bulk Collection Install via requirements.yml |
| not completed | ANS-CH2-F08 | Semantic Versioning Walk-Through for Ansible Packages |
| not completed | ANS-CH2-F09 | Discover All Modules in a Collection via `ansible-doc -l` |
| not completed | ANS-CH2-F10 | Force-Install a Pre-Release / Dev Collection Version |
| not completed | ANS-CH2-F11 | Publish a Collection to Ansible Galaxy |

#### 🎛 Ch 7 — Task Conditions, Error Recovery, Loops (12 labs)

| Status | ID | Lab |
|---|---|---|
| not completed | ANS-CH7-F01 | `ignore_errors: true` on a Deliberately-Failing URI Task |
| not completed | ANS-CH7-F02 | `failed_when` for iscsiadm Exit Code Tolerance |
| not completed | ANS-CH7-F03 | Multi-Condition `failed_when` as YAML List (Git Branch Delete) |
| not completed | ANS-CH7-F04 | `changed_when` to Suppress False-Positive Changes |
| not completed | ANS-CH7-F05 | `creates` / `removes` for Command-Family Idempotency |
| not completed | ANS-CH7-F06 | Pure Data-Gathering Tasks with `changed_when: false` |
| not completed | ANS-CH7-F07 | `block` + `rescue` for Graceful Cleanup |
| not completed | ANS-CH7-F08 | `block` + `rescue` + `always` (Three-Section Block) |
| not completed | ANS-CH7-F09 | `ignore_unreachable: true` Against an Inventory of Dead Hosts |
| not completed | ANS-CH7-F10 | Modern `loop:` vs Legacy `with_items:` Equivalence |
| not completed | ANS-CH7-F11 | `until` / `retries` / `delay` Loop Waiting for /tmp/flag |
| not completed | ANS-CH7-F12 | Nested Loops with `product` Filter and `loop_control.loop_var` |

#### 🧱 Ch 8 — Roles, Includes & ansible-galaxy (15 labs)

| Status | ID | Lab |
|---|---|---|
| not completed | ANS-CH8-F01 | Basic Task Inclusion with `ansible.builtin.include` |
| not completed | ANS-CH8-F02 | Passing Variables Inline to Included Tasks |
| not completed | ANS-CH8-F03 | Passing Complex Hash Data to Included Tasks via dict2items |
| not completed | ANS-CH8-F04 | Conditional Include with `when: item \| bool` |
| not completed | ANS-CH8-F05 | Tagged Task Includes for Selective Execution |
| not completed | ANS-CH8-F06 | Looping Over a Task Include with `loop_control: loop_var` |
| not completed | ANS-CH8-F07 | Handler Inclusion with `when` on the Include Statement |
| not completed | ANS-CH8-F08 | `vars_files` Static Inclusion vs `include_vars` Dynamic Inclusion |
| not completed | ANS-CH8-F09 | `include_vars` with `with_first_found` for OS-Specific Vars |
| not completed | ANS-CH8-F10 | Loading Extra Vars from a File via `-e @file.yaml` |
| not completed | ANS-CH8-F11 | `import_playbook` for Composing Multi-Playbook Workflows |
| not completed | ANS-CH8-F12 | Build a Role From Scratch with `ansible-galaxy role init` |
| not completed | ANS-CH8-F13 | Role Dependencies with Variables + Tags + Conditionals |
| not completed | ANS-CH8-F14 | pre_tasks / roles / tasks / post_tasks Handler-Flush Ordering |
| not completed | ANS-CH8-F15 | Install Roles from Ansible Galaxy + Git + tarball + requirements.yml |

#### 🌐 Ch 13 — Network Automation (10 labs)

| Status | ID | Lab |
|---|---|---|
| not completed | ANS-CH13-F01 | Choosing the Right Connection Protocol: local vs network_cli vs netconf vs httpapi |
| not completed | ANS-CH13-F02 | Inventory for Cisco IOS via `ansible.netcommon.network_cli` |
| not completed | ANS-CH13-F03 | Save Running Config on Cisco IOS with `cisco.ios.ios_config` |
| not completed | ANS-CH13-F04 | Bring Up an Arista vEOS Switch from Zero |
| not completed | ANS-CH13-F05 | Configure Arista EOS Interfaces with `arista.eos.eos_interfaces` |
| not completed | ANS-CH13-F06 | Configure Cumulus Linux Layer-2 Bridge with `community.network.nclu` |
| not completed | ANS-CH13-F07 | Multi-Vendor Inventory with `[switches:children]` Grouping |
| not completed | ANS-CH13-F08 | Conditional Fact-Gathering for Different Network OSes |
| not completed | ANS-CH13-F09 | Jump Host / Bastion via `ansible_ssh_common_args` ProxyCommand |
| not completed | ANS-CH13-F10 | Raw-Command Fallback for Unsupported Devices via `ansible.builtin.raw` |

---

## 📈 Summary by Category

### RHCSA EX200 (356 labs)

> README columns count only the labs visible in the main [README](README.md) (companion-repo URLs + `*(coming soon)*` placeholders). **In-Repo** counts labs that live in [`labs/<slug>/`](labs/). **Future** counts labs from [`future_labs.txt`](future_labs.txt) that have a `*-F##` ID but no page yet.

| Category | README | README (placeholder) | In-Repo | Future | Total |
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

> \* Note: in-repo labs that are *also* listed as a "LAB" row in the README (3 labs: `lvm-create-lvol1-ext4`, `scheduling-jobs-systemd-timer`, plus the Container LAB row pointing to an external repo) are counted in the In-Repo column to avoid double-counting against the README columns; the README "LAB" row count is separately when its companion repo exists.

### RHCE EX294 (20 labs)

| Section | Planned |
|---|---:|
| Foundation (common tasks) | 4 |
| Exam Practice 1 | 3 |
| Exam Practice 2 | 7 |
| Exam Practice 3 | 6 |

### CKA (36 labs)

| Section | README (placeholder) | Future | Total |
|---|---:|---:|---:|
| Cluster Architecture | 2 | 5 | 7 |
| Workloads & Scheduling | 3 | 9 | 12 |
| Networking | 3 | 2 | 5 |
| Storage | 2 | 1 | 3 |
| Security | 2 | 0 | 2 |
| Cluster Maintenance | 2 | 0 | 2 |
| Troubleshooting | 2 | 3 | 5 |

### CKAD (22 labs)

| Section | Planned |
|---|---:|
| Application Design & Build | 7 |
| Application Deployment | 3 |
| Observability & Maintenance | 3 |
| Environment, Config & Security | 7 |
| Services & Networking | 3 |

### Ansible (88 labs)

| Section | Companion Repo | README (placeholder) | Future | Total |
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

1. **Status visibility** — every lab currently reads `not completed` while the curriculum is rebuilt under the ADHD-method format; once a lab is re-authored, its row will update.
2. **Full paths to every lab** — companion-repo URLs are written out in plain text, in-repo `labs/<slug>/` paths are linked, and "coming soon" placeholders point back to the specific README section by lab number so you can always find the source.
3. **Future-lab prefixes** — `LVM-F##`, `NET-F##`, `ANS-CH1-F##`, etc. are stable identifiers that survive renumbering when labs get built and slotted into the main README's global sequence.
4. **The non-RHCSA tracks** — the README is RHCSA-first; this roadmap surfaces the parallel RHCE / CKA / CKAD / Ansible curricula so the whole multi-cert arc is visible in one place.
5. **Exam-objective study order** — the [Complete Labs by RHCSA v10 Objective (EX200)](#-complete-labs-by-rhcsa-v10-objective-ex200) section lists every RHCSA lab under official objectives **1 → 10**, sub-ordered **a → h** within each objective, for straight EX200 exam prep.

When a lab is re-authored under the ADHD-method format in [`labs/<slug>/`](labs/), its row in this roadmap will be updated from `not completed` to the new completion status, and a new row will be added to the main [README](README.md) with the next free global number (e.g. `228`, `229`...).

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
