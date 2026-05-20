<div align="center">

# 🐧 Linux Ops Mastery

### A Hands-On Linux Operations Study Guide
**RHCSA → RHCE → CKA → Production AI/MLOps Infrastructure**

![RHCSA](https://img.shields.io/badge/RHCSA-EX200-EE0000?style=flat&logo=redhat&logoColor=white)
![RHCE](https://img.shields.io/badge/RHCE-EX294-EE0000?style=flat&logo=redhat&logoColor=white)
![CKA](https://img.shields.io/badge/CKA-Kubernetes-326CE5?style=flat&logo=kubernetes&logoColor=white)
![CompTIA Linux+](https://img.shields.io/badge/Linux%2B-FF0000?style=flat&logo=comptia&logoColor=white)
![CompTIA Security+](https://img.shields.io/badge/Security%2B-FF0000?style=flat&logo=comptia&logoColor=white)
![AWS CCP](https://img.shields.io/badge/AWS_Cloud_Practitioner-232F3E?style=flat&logo=amazonaws&logoColor=white)

[![Stars](https://img.shields.io/github/stars/kelvintechnical/linux-ops-mastery?style=social)](https://github.com/kelvintechnical/linux-ops-mastery)

</div>

---

## 📚 Table of Contents

- [About](#-about)
- [Who This Is For](#-who-this-is-for)
- [Companion Repos](#-companion-repos)
- [Certification Path](#-certification-path)
- [RHCSA Labs](#-rhcsa-ex200-labs)
- [RHCE Labs](#-rhce-ex294-labs)
- [CKA Labs](#-cka-labs)
- [How to Use This Repo](#-how-to-use-this-repo)
- [Author & Connect](#-author--connect)

---

## 📖 About

A complete, hands-on Linux operations study guide built for engineers preparing for **RHCSA (EX200)**, **RHCE (EX294)**, and **CKA** — and anyone building production-grade Linux and Kubernetes skills for cloud, DevOps, or AI/MLOps infrastructure roles.

All commands tested on **RHEL 9** / **Rocky Linux** / **AWS RHEL AMI**.

---

## 🎯 Who This Is For

- Engineers preparing for **RHCSA**, **RHCE**, or **CKA**
- DevOps / SRE / Platform engineers building Linux and Kubernetes skills
- AI/MLOps practitioners deploying on Linux infrastructure
- Self-learners working through Red Hat and CNCF certification objectives

> No prior Red Hat experience required. CompTIA Linux+ or equivalent familiarity recommended.

---

## 🔗 Companion Repos

Foundational Linux skills broken into focused, standalone learning resources:

| Repo | Topic |
|------|-------|
| 🌐 [accessing-your-linux-system](https://github.com/kelvintechnical/accessing-your-linux-system) | Console access, SSH, PuTTY, AWS EC2 |
| 🗂 [managing-linux-files-cli](https://github.com/kelvintechnical/managing-linux-files-cli) | File system, file management, links, I/O redirection, pipes |

> 💡 **Start here if you're new to Linux** — these repos build the foundation before diving into RHCSA-level material.

---

### 🗂️ Linux Filesystem Hierarchy Standard (FHS)
> Before touching a single command, know where everything lives. This reference repo documents every directory in the Linux root filesystem (`/`) with hands-on labs showing real-world purpose.

| Repo | Topic |
|------|-------|
| 🗂️ [Linux-Filesystem-Hierarchy-Standard](https://github.com/kelvintechnical/Linux-Filesystem-Hierarchy-Standard-) | What every `/` directory is, why it exists, and how to use it |

---

## 🗺️ Certification Path

| Phase | Certification | Exam | Status |
|-------|--------------|------|--------|
| Foundation | CompTIA Linux+ | XK0-005 | ✅ Complete |
| Intermediate | RHCSA | EX200 | 🔄 In Progress |
| Advanced | RHCE (Ansible) | EX294 | 🔜 Planned |
| Cloud Native | CKA (Kubernetes) | CKA | 🔜 Planned |

---

## 🧪 RHCSA EX200 Labs

Labs organized by official RHCSA EX200 exam objectives.

---

### 🖥️ Shells, Terminals & Redirection

> Understand stdout, stderr, pipes, and how to control where command output goes.

| # | Lab | Key Commands |
|---|-----|-------------|
| 01 | [Standard Output Redirection](https://github.com/kelvintechnical/stdout-redirection) | `>`, `>>`, `cat` — Use `>` to direct output into a new file and `>>` to append output to an existing file |
| 02 | [Standard Error Redirection](https://github.com/kelvintechnical/stderr-redirection) | `2>`, `2>/dev/null`, `&>` — Force a command to generate an error and redirect that error stream to a file or discard it |
| 03 | [Pipe Text Streams](https://github.com/kelvintechnical/pipe-text-streams) | `\|`, `less`, `grep`, `tee`, `wc -l` — Combine multiple commands using `\|` to send stdout of one command into stdin of another |
| 04 | Capture Both Output and Error *(coming soon)* | `&>`, `2>&1` — Send both stdout and stderr to the same file using the `&>` operator |

---

### 🌐 Networking

> Configure and manage network interfaces, static IPs, hostnames, SSH, and DNS.

| # | Lab | Key Commands |
|---|-----|-------------|
| 05 | [Configure a Static IP Address](./01-system-management/README.md#lab-01--configure-a-static-ip-address) | `nmcli con mod`, `ip addr`, `ip route` — Configure a network interface with a static IPv4 address, gateway, and DNS |
| 06 | Check Network Connectivity *(coming soon)* | `ping`, `traceroute` — Test connections and map the path packets take across the network |
| 07 | Display IP and Routing Info *(coming soon)* | `ip addr show`, `ip route show` — Check IP assignments and review the routing table |
| 08 | Inspecting Listening Sockets *(coming soon)* | `ss -tuna4` — View active TCP and UDP sockets and identify open ports |
| 09 | Text-Based Network Config *(coming soon)* | `nmtui` — Set a static IPv4 address, subnet mask, gateway, and DNS |
| 10 | Command-Line Network Config *(coming soon)* | `nmcli` — Modify connection settings and reload a network interface |
| 11 | Configuring Local Host Resolution *(coming soon)* | `/etc/hosts` — Manually map IP addresses to hostnames for local name resolution |
| 12 | Configuring DNS Servers *(coming soon)* | `/etc/resolv.conf` — Specify external name servers and search domains |
| 13 | Configure SSH & Key-Based Authentication *(coming soon)* | `ssh-keygen`, `ssh-copy-id`, `authorized_keys`, `sshd_config` — Generate an RSA key pair and deploy it for passwordless login |

---

### 📦 Package Management & Repositories

> Configure DNF repositories, install packages, and manage software sources.

| # | Lab | Key Commands |
|---|-----|-------------|
| 14 | [Configure Repository Access](https://github.com/kelvintechnical/Configure-Repository-Access-) | `dnf`, `tee`, `/etc/yum.repos.d/` — Create a `.repo` configuration file pointing to a repository |
| 15 | [Install Package Groups](https://github.com/kelvintechnical/install-package-group) | `dnf group list`, `dnf groupinstall`, `dnf groupremove` — Install a complete set of related software |
| 16 | [Managing Flatpak](https://github.com/kelvintechnical/Managing-Flatpak/blob/main/README.md) | `flatpak remote-add`, `flatpak install --user`, `flatpak list` |
| 17 | Install Packages with dnf *(coming soon)* | `dnf install`, `dnf remove`, `dnf update` — Install, remove, and update packages with automatic dependency resolution |
| 18 | Search for Software *(coming soon)* | `dnf search`, `dnf whatprovides`, `dnf list` — Search repositories and find file providers |
| 19 | Query and Verify RPM Packages *(coming soon)* | `rpm -qa`, `rpm -qi`, `rpm -ql`, `rpm -V` — Query installed packages and verify integrity |

---

### ⏰ System Time & Locale

> Set timezone, configure NTP, and ensure time synchronization persists.

| # | Lab | Key Commands |
|---|-----|-------------|
| 20 | [Configure Timezone and Time Synchronization](https://github.com/kelvintechnical/Configure-Timezone-and-Time-Synchronization) | `timedatectl`, `systemctl enable --now chronyd` — List timezones and set timezone |
| 21 | [Configure NTP Time Source](https://github.com/kelvintechnical/configure-ntp) | `/etc/chrony.conf`, `chronyc sources`, `iburst` — Configure server/peer directives for NTP synchronization |
| 22 | Check NTP Sync Status *(coming soon)* | `ntpq -p`, `chronyc tracking` — Verify NTP is actively synchronizing |

---

### 🔧 Essential Tools & File Operations

> Search, filter, redirect, compress, and manage files from the command line.

| # | Lab | Key Commands |
|---|-----|-------------|
| 23 | [Search for a String and Save Output](https://github.com/kelvintechnical/search-string-save-output) | `grep`, `tee`, `>` — Search for strings inside config files and experiment with regular expressions |
| 24 | [Find and Save Config Files](https://github.com/kelvintechnical/find-save-config-files) | `find -type f -name -user`, `2>/dev/null` — Search the filesystem for specific files by name |
| 25 | [Locate Command Documentation](https://github.com/kelvintechnical/locate-command-docs) | `find /usr/share/doc`, `rpm -qf`, `rpm -qd` — Look up manual pages and locate documentation |
| 26 | Directory Navigation *(coming soon)* | `cd`, `pwd`, `ls` — Move through the filesystem using absolute paths, relative paths, `..`, and `~` |
| 27 | Listing Files and SELinux Contexts *(coming soon)* | `ls -l`, `ls -Z` — Use long listings and display SELinux contexts of files and directories |
| 28 | Creating Empty Files and Timestamps *(coming soon)* | `touch` — Create an empty file and update the last modification timestamp |
| 29 | Copying Files and Directories *(coming soon)* | `cp`, `cp -R`, `cp -a` — Copy single files and entire directory structures recursively |
| 30 | Hard and Soft Links *(coming soon)* | `ln`, `ln -s` — Create hard links pointing to the same inode and soft links |
| 31 | Moving and Renaming Files *(coming soon)* | `mv` — Rename files locally and move files from one directory to another |
| 32 | Safe Deletion of Files and Directories *(coming soon)* | `rm`, `rmdir`, `rm -rf` — Delete files, empty directories, and entire directory trees |
| 33 | Creating Nested Directories *(coming soon)* | `mkdir -p` — Create a long nested directory structure in a single command |
| 34 | Creating Command Aliases *(coming soon)* | `alias` — Map a custom shortcut to a standard command |
| 35 | File Searching with find *(coming soon)* | `find` — Search the filesystem for specific files by name starting from root or a subdirectory |
| 36 | Instant File Searching with locate *(coming soon)* | `locate`, `updatedb` — Run the manual database update script and use locate to instantly find files |
| 37 | [Standard File Compression with gzip](https://github.com/kelvintechnical/standard-file-compression) | `gzip`, `gunzip`, `zcat`, `gzip -k`, `gzip -v` — Compress a large text file and view the resulting `.gz` file |
| 38 | [High-Ratio Compression with bzip2](https://github.com/kelvintechnical/high-ratio-compression) | `bzip2`, `bunzip2`, `bzcat`, `bzip2 -k`, `bzip2 -v` — Compress files using bzip2 for higher compression ratio |
| 39 | [Create Standard Archives with tar](https://github.com/kelvintechnical/create-standard-archives) | `tar -cvf`, `tar -tvf`, `tar -xvf` — Combine files and directories into a single uncompressed archive |
| 40 | Create Compressed Archives *(coming soon)* | `tar -czf`, `tar -cjf`, `tar -cJf`, `xz` — Create a gzip-compressed tarball |
| 41 | Extract Archives *(coming soon)* | `tar -xvf` — Extract contents of a `.tar.bz2` archive into a specific directory |
| 42 | Preserve Security Contexts in Archives *(coming soon)* | `tar --selinux` — Create a tarball preserving SELinux contexts and ACLs |

---

### 📄 Text File Management

> Read, filter, edit, and compare text files from the command line.

| # | Lab | Key Commands |
|---|-----|-------------|
| 43 | Concatenating Files with cat *(coming soon)* | `cat` — Read the contents of short text files directly in the terminal |
| 44 | Scrolling Through Large Files *(coming soon)* | `less`, `more` — Scroll through large system logs and search using `/` and `?` |
| 45 | Monitoring Live Log Files *(coming soon)* | `tail -f` — Actively monitor a log file and watch new lines appended in real-time |
| 46 | Filtering Text with grep and Regex *(coming soon)* | `grep` — Search for strings inside config files and experiment with regular expressions |
| 47 | Comparing File Differences with diff *(coming soon)* | `diff` — Modify a config file and compare it against a backup to identify exact line changes |
| 48 | Stream Editing with sed *(coming soon)* | `sed` — Automatically find and replace text strings within a file without opening an editor |
| 49 | Extracting Columns with awk *(coming soon)* | `awk` — Specify a delimiter and print only a specific field to the screen |
| 50 | Command Mode and Insert Mode in vi *(coming soon)* | `vi`, `:wq` — Open a config file in vi, switch to insert mode, make a change, and save |
| 51 | Safely Editing System Databases *(coming soon)* | `vipw`, `vigr` — Practice editing password and group files safely |

---

### 📖 Documentation Tools

> Look up man pages, keyword searches, and info pages.

| # | Lab | Key Commands |
|---|-----|-------------|
| 52 | Exploring Manual Pages *(coming soon)* | `man` — Look up manual pages and practice scrolling through descriptions and syntax examples |
| 53 | Searching Manuals by Keyword *(coming soon)* | `whatis`, `apropos` — Find documentation when you only know a keyword or purpose |
| 54 | Navigating info Pages *(coming soon)* | `info` — Read detailed manual pages, navigating with `n`, `p`, and `u` keys |

---

### 👥 User & Group Management

> Create and manage users and groups, control login access, and enforce account policies.

| # | Lab | Key Commands |
|---|-----|-------------|
| 55 | [User & Group Management / Permissions](https://github.com/kelvintechnical/User-Group-Management-Permissions) | `useradd`, `groupadd`, `chown`, `chmod`, `id`, `getent` — Add a new user and assign a password securely |
| 56 | [Disable User Login Without Removing the Account](https://github.com/kelvintechnical/disable-user-login) | `usermod -s /sbin/nologin`, `getent passwd` — Modify a user to assign `/sbin/nologin` as their shell |
| 57 | Inspect Password Database *(coming soon)* | `/etc/passwd` — Review usernames, UIDs, GIDs, and home directory structure |
| 58 | Analyze Shadow File *(coming soon)* | `/etc/shadow` — View hashed passwords and identify password aging fields |
| 59 | Modify Default Password Aging *(coming soon)* | `/etc/login.defs` — Set new default security policies like `PASS_MAX_DAYS` |
| 60 | Modify Existing Account *(coming soon)* | `usermod -L`, `usermod -U`, `usermod -aG` — Lock an account, unlock it, and append to a group |
| 61 | Advanced Group Management *(coming soon)* | `groupadd`, `gpasswd`, `groupmod` — Create a group, assign admin, and modify GID |
| 62 | Force Password Changes *(coming soon)* | `chage` — View password aging info and force a password change on next login |
| 63 | Safely Delete Users *(coming soon)* | `userdel -r` — Remove a user and completely delete their home directory and mail spool |
| 64 | Configure Custom Administrators *(coming soon)* | `visudo`, `/etc/sudoers` — Grant a user full administrative privileges |
| 65 | Granular sudo Privileges *(coming soon)* | `visudo`, `Cmnd_Alias` — Grant permission to run only specific commands |
| 66 | Limit root Logins *(coming soon)* | `/etc/securetty` — Restrict which virtual consoles root can log into directly |
| 67 | Populate Directory Templates *(coming soon)* | `/etc/skel` — Add custom files so new users automatically receive them |
| 68 | Manage Shell Environments *(coming soon)* | `.bash_profile`, `.bashrc` — Configure persistent environment variables and aliases |
| 69 | Alter Global Default umask *(coming soon)* | `/etc/bashrc`, `/etc/profile` — Restrict default file permissions system-wide |

---

### 🔒 Permissions, Special Bits & ACLs

> Configure standard permissions, special bits, and access control lists.

| # | Lab | Key Commands |
|---|-----|-------------|
| 70 | [Configure SGID and Sticky Bit](https://github.com/kelvintechnical/sgid-sticky-bit) | `chmod g+s`, `chmod +t`, `ls -ld` — Create a directory with SGID set so new files inherit the group ownership of the parent |
| 71 | Standard File Permissions *(coming soon)* | `chmod`, `ls -l`, `ugo/rwx` — List, set, and change standard ugo/rwx permissions |
| 72 | Changing Ownership *(coming soon)* | `chown`, `chgrp` — Reassign file and directory ownership |
| 73 | SUID Executables *(coming soon)* | `chmod u+s`, `ls -l` — Configure the SUID bit on a file and observe how it executes with the privileges of the file owner |
| 74 | SGID Collaboration Directory *(coming soon)* | `chmod g+s` — Create a directory with SGID set so new files inherit the group ownership of the parent |
| 75 | Immutable File Attribute *(coming soon)* | `chattr +i`, `lsattr` — Make a critical file immutable, preventing deletion even by root |
| 76 | Append-Only File Attribute *(coming soon)* | `chattr +a`, `lsattr` — Use `chattr +a` on a log file to ensure data can only be appended and never overwritten |
| 77 | Identifying File Attributes *(coming soon)* | `lsattr` — List extended attributes of files on ext4 or XFS filesystems |
| 78 | Check ACL Support *(coming soon)* | `mount`, `acl` option — Verify a filesystem is mounted with the acl option |
| 79 | Viewing ACLs *(coming soon)* | `getfacl` — Inspect a file's current access control list |
| 80 | Modifying ACLs *(coming soon)* | `setfacl -m` — Grant a specific user read and write access to a file |
| 81 | Denying Access via ACLs *(coming soon)* | `setfacl` — Implement an ACL to explicitly deny access to a specific user |
| 82 | Default Directory ACLs *(coming soon)* | `setfacl -d` — Configure a default ACL on a directory so newly created files automatically inherit permissions |
| 83 | ACL Masks *(coming soon)* | `setfacl -m m::` — Set a mask that caps maximum allowable permissions for users and groups |
| 84 | Removing ACLs *(coming soon)* | `setfacl -x`, `setfacl -b` — Strip specific ACL entries or remove all ACLs |
| 85 | NFSv4 ACLs *(coming soon — needs NFS)* | `nfs4_getfacl`, `nfs4_setfacl` — Display and edit permissions on an NFS v4 share |

---

### 🔥 Firewall (firewalld)

> Manage firewall rules, zones, ports, services, NAT, and rich rules.

| # | Lab | Key Commands |
|---|-----|-------------|
| 86 | Inspecting iptables *(coming soon)* | `iptables -L` — Review the default filtering chains and packet rules |
| 87 | Exploring firewalld Zones *(coming soon)* | `firewall-cmd --get-default-zone`, `--list-all` — List available and active zones |
| 88 | Changing Default Firewall Zone *(coming soon)* | `firewall-cmd --set-default-zone` — Reassign an active interface from the public zone to the dmz or internal zone |
| 89 | Adding Services to Zones *(coming soon)* | `firewall-cmd --add-service`, `--permanent` — Permanently open ports for a service |
| 90 | Opening Custom Ports *(coming soon)* | `firewall-cmd --add-port` — Open a non-standard port by adding it directly to a zone |
| 91 | Inspect Active Firewall Zones *(coming soon)* | `firewall-cmd --get-default-zone`, `--list-all` — Review zones and allowed services |
| 92 | Reassign Interfaces to Zones *(coming soon)* | `firewall-cmd --change-interface` — Temporarily and permanently move a network interface between zones |
| 93 | Allow Services Through Firewall *(coming soon)* | `firewall-cmd --permanent --add-service` — Open ports for web and FTP servers |
| 94 | Configure IP Masquerading NAT *(coming soon)* | `firewall-cmd --add-masquerade` — Enable IP masquerading on the external zone |
| 95 | Configure IP Forwarding *(coming soon)* | `/etc/sysctl.conf`, `sysctl -p` — Enable `net.ipv4.ip_forward = 1` and apply |
| 96 | Configure Rich Rules *(coming soon)* | `firewall-cmd --add-rich-rule` — Create a rich rule that denies traffic from a specific host |
| 97 | Setup Port Forwarding DNAT *(coming soon)* | `firewall-cmd` rich rules — Redirect inbound traffic from port 80 to port 8008 |
| 98 | Configure ICMP Filters *(coming soon)* | `firewall-cmd --add-icmp-block` — Block specific ICMP message types to drop ping floods |

---

### 🔐 TCP Wrappers & PAM

> Restrict network access and enforce authentication policies.

| # | Lab | Key Commands |
|---|-----|-------------|
| 99 | Verify TCP Wrappers Support *(coming soon)* | `ldd /usr/sbin/sshd \| grep libwrap` — Confirm SSH is linked to TCP Wrappers |
| 100 | Restrict Access via hosts.deny *(coming soon)* | `/etc/hosts.deny` — Edit with `ALL : ALL` to block all wrapper-aware network traffic by default |
| 101 | Allow Specific Access via hosts.allow *(coming soon)* | `/etc/hosts.allow` — Explicitly allow SSH from localhost and a specific subnet |
| 102 | Implement Password Complexity *(coming soon)* | `pam_pwquality.so`, `system-auth` — Review how RHEL enforces password rules |
| 103 | Configure PAM to Limit root Access *(coming soon)* | `pam_securetty.so` — Limit root logins to only virtual terminal 6 |
| 104 | Use PAM to Limit User Access *(coming soon)* | `/etc/nologin` — Create `/etc/nologin` with a custom message to block regular users from logging in |
| 105 | Restrict Service Access by User List *(coming soon)* | `pam_listfile.so` — Deny access to users defined in a text file |

---

### 🛡️ SELinux

> Manage SELinux modes, contexts, booleans, and troubleshoot denials.

| # | Lab | Key Commands |
|---|-----|-------------|
| 106 | Managing SELinux Modes *(coming soon)* | `sestatus`, `setenforce` — Check SELinux status and toggle between enforcing and permissive |
| 107 | Viewing SELinux Contexts *(coming soon)* | `ls -Z`, `ps -eZ` — View file contexts and contexts of running processes |
| 108 | Temporary Context Changes *(coming soon)* | `chcon` — Temporarily modify the SELinux type context of a custom directory |
| 109 | Persistent Context Restoration *(coming soon)* | `semanage fcontext`, `restorecon` — Define persistent rules and apply them |
| 110 | Toggling SELinux Booleans *(coming soon)* | `getsebool`, `setsebool -P` — Search available booleans and make persistent changes |
| 111 | SELinux User Mapping *(coming soon)* | `semanage login` — Map a Linux user account to a restricted SELinux user type |
| 112 | Troubleshooting SELinux *(coming soon)* | `audit.log`, `sealert` — Trigger a policy violation, locate it in audit.log, and analyze |

---

### 🥾 Boot Process & GRUB

> Understand the boot process, reset root passwords, and configure GRUB.

| # | Lab | Key Commands |
|---|-----|-------------|
| 113 | Modify GRUB Timeout *(coming soon)* | `/etc/default/grub`, `GRUB_TIMEOUT` — Adjust bootloader countdown |
| 114 | Enable Verbose Kernel Messages *(coming soon)* | `GRUB_CMDLINE_LINUX` — Remove the `quiet` keyword to show verbose startup output |
| 115 | Generate New GRUB Config *(coming soon)* | `grub2-mkconfig -o /boot/grub2/grub.cfg` — Apply changes persistently |
| 116 | Reset Root Password via Boot *(coming soon)* | GRUB interrupt, `rd.break`, `chroot`, `passwd` — Interrupt boot before filesystem mount and reset root password |

---

### ⚙️ Systemd & Services

> Manage system services, unit files, and boot targets.

| # | Lab | Key Commands |
|---|-----|-------------|
| 117 | Check Default Boot Target *(coming soon)* | `systemctl get-default` — Verify if system boots into graphical or multi-user target |
| 118 | Change Default Boot Target *(coming soon)* | `systemctl set-default` — Configure system to permanently boot into text-based environment |
| 119 | System Reboots and Shutdowns *(coming soon)* | `systemctl reboot`, `systemctl poweroff` — Safely transition system state |
| 120 | List All System Units *(coming soon)* | `systemctl list-units --all` — Display state of all systemd units |
| 121 | Check Service Status *(coming soon)* | `systemctl status` — Verify running status, PID, and recent logs of a daemon |
| 122 | Start and Stop Services *(coming soon)* | `systemctl start`, `systemctl stop` — Control active services on the fly |
| 123 | Enable Services at Boot *(coming soon)* | `systemctl enable` — Ensure services survive restart by linking to the default target |
| 124 | Disable Services at Boot *(coming soon)* | `systemctl disable` — Prevent a service from launching automatically |
| 125 | Mask System Services *(coming soon)* | `systemctl mask` — Prevent a conflicting daemon from being started accidentally |
| 126 | Create and Manage systemd Unit Files *(coming soon)* | Unit file syntax, `systemctl daemon-reload` |

---

### 📋 Log Management

> Query and manage system logs using journalctl and rsyslog.

| # | Lab | Key Commands |
|---|-----|-------------|
| 127 | Analyze Boot Performance *(coming soon)* | `systemd-analyze blame` — Identify services slowing down the boot process |
| 128 | Query Logs with journalctl *(coming soon)* | `journalctl -u`, `-p`, `--since`, `--until` — Read and filter system logs by priority |
| 129 | Configure Persistent Journal Logs *(coming soon)* | `/var/log/journal` — Create directory to force systemd to write logs persistently to disk |
| 130 | Understand Log Routing *(coming soon)* | `/etc/rsyslog.conf` — Review where different system and kernel messages are logged |
| 131 | Monitor Authentication Logs *(coming soon)* | `/var/log/secure` — Track user logins, SSH access, and failed authentication attempts |
| 132 | Filter systemd Journals by Priority *(coming soon)* | `journalctl -p alert` — Query the journal filtering for high-priority errors |
| 133 | Service-Specific Journal Logs *(coming soon)* | `journalctl -u httpd` — Display journal entries for a specific daemon |

---

### 💾 Storage Management

> Create and manage partitions, filesystems, and disk devices.

| # | Lab | Key Commands |
|---|-----|-------------|
| 134 | Inspect Filesystems *(coming soon)* | `df -h`, `findmnt` — View space on mounted filesystems |
| 135 | Display Partition Tables *(coming soon)* | `fdisk -l` — List configured partitions from all attached hard drives |
| 136 | Create MBR Partition with fdisk *(coming soon — needs EBS)* | `fdisk /dev/vdb` — Create partition with `n`, print with `p`, write with `w` |
| 137 | Create GPT Partition with gdisk *(coming soon — needs EBS)* | `gdisk` — Practice creating a GPT-based partition table |
| 138 | Format Partition with XFS *(coming soon — needs EBS)* | `mkfs.xfs` — Format a newly created partition with the default RHEL XFS filesystem |
| 139 | Format Partition with Ext4 *(coming soon — needs EBS)* | `mkfs.ext4` — Format a partition with the ext4 journaling filesystem |
| 140 | Check Filesystem Consistency *(coming soon — needs EBS)* | `fsck.ext4` — Check integrity of an unmounted ext partition |
| 141 | Create and Activate Swap Space *(coming soon)* | `mkswap`, `swapon`, `swapoff`, `/etc/fstab` |

---

### 🗂 LVM (Logical Volume Management)

> Create, extend, and manage logical volumes.

| # | Lab | Key Commands |
|---|-----|-------------|
| 142 | Initialize Physical Volumes *(coming soon — needs EBS)* | `pvcreate` — Initialize a disk or partition for use by LVM |
| 143 | Create Volume Group *(coming soon — needs EBS)* | `vgcreate` — Pool one or more physical volumes into a volume group |
| 144 | Create Logical Volume *(coming soon — needs EBS)* | `lvcreate` — Allocate space from a volume group into a logical volume |
| 145 | Extend Logical Volume *(coming soon — needs EBS)* | `lvextend`, `xfs_growfs`, `resize2fs` — Increase space and expand filesystem to fill new space |
| 146 | Remove LVM Components *(coming soon — needs EBS)* | `lvremove`, `vgremove`, `pvremove` — Unmount, then remove LV, VG, and PV |

---

### 📁 Filesystem Mounts

> Mount, configure, and automate filesystem mounts.

| # | Lab | Key Commands |
|---|-----|-------------|
| 147 | Retrieve Filesystem UUIDs *(coming soon)* | `blkid` — Identify the UUID of formatted block devices for persistent mounting |
| 148 | Configure Persistent Mounts fstab *(coming soon)* | `/etc/fstab` — Add a new mount entry using UUID, mount point, and filesystem type |
| 149 | Remount with New Options *(coming soon)* | `mount -o remount` — Modify mount options of an actively mounted filesystem |
| 150 | Manage Autofs Service *(coming soon)* | `systemctl` — Ensure the automounter is running and set to start at boot |

---

### 🔄 Process Management

> Monitor, control, and prioritize running processes.

| # | Lab | Key Commands |
|---|-----|-------------|
| 151 | Audit All Running Processes *(coming soon)* | `ps aux` — List all running processes and identify CPU and memory usage |
| 152 | Real-Time Process Monitoring *(coming soon)* | `top` — Monitor real-time system load, tasks, memory, and swap |
| 153 | Adjust Process Priority *(coming soon)* | `renice` — Change the priority of an already running CPU-intensive process |
| 154 | Start Processes with Custom Priority *(coming soon)* | `nice` — Launch a new process with a predefined priority level |
| 155 | Terminate Processes Gracefully *(coming soon)* | `kill` (SIGTERM) — Identify a PID and terminate it safely |
| 156 | Force Kill Unresponsive Processes *(coming soon)* | `kill -9` (SIGKILL) — Forcibly terminate a hung process |
| 157 | Kill Processes by Name *(coming soon)* | `killall` — Terminate multiple instances of a process at once |

---

### 🕐 Scheduled Tasks

> Automate recurring and one-time tasks using cron and at.

| # | Lab | Key Commands |
|---|-----|-------------|
| 158 | Schedule Tasks with cron *(coming soon)* | `crontab -e`, `/etc/cron.d/`, cron syntax — Schedule a recurring script to run at a specific interval |
| 159 | Remove User cron Jobs *(coming soon)* | `crontab -l`, `crontab -r` — View active jobs and remove all user cron jobs |
| 160 | Schedule One-Time Tasks with at *(coming soon)* | `at`, `atq`, `atrm` — Schedule a command to execute exactly once at a specified time |
| 161 | Limit Access to cron *(coming soon)* | `/etc/cron.deny` — Restrict users from scheduling tasks |
| 162 | Review the Anacron System *(coming soon)* | `/etc/anacrontab` — See how RHEL ensures periodic jobs run after downtime |

---

### 🔐 GPG Encryption

> Generate keys, encrypt, decrypt, and share GPG-protected files.

| # | Lab | Key Commands |
|---|-----|-------------|
| 163 | Generate a GPG Key Pair *(coming soon)* | `gpg --gen-key` — Create an RSA public/private key pair with a passphrase |
| 164 | Encrypt a File with GPG *(coming soon)* | `gpg --recipient --encrypt` — Create a text file and secure it |
| 165 | Decrypt a GPG File *(coming soon)* | `gpg --decrypt` — Enter the passphrase to read the original plaintext contents |
| 166 | Share and Verify Public Keys *(coming soon)* | `gpg --export -a`, `scp`, `gpg --import` — Export, transfer, and import a GPG key |

---

### 🌍 Web Services (Apache)

> Install, configure, and verify the Apache web server.

| # | Lab | Key Commands |
|---|-----|-------------|
| 167 | [Configure Apache to Serve Default and Custom Web Content](https://github.com/kelvintechnical/apache-custom-content) | `httpd`, `semanage fcontext`, `restorecon`, `curl` — Install Apache, start/enable the service, and deploy web content |
| 168 | Password-Protect a Directory *(coming soon)* | `htpasswd`, `AuthType Basic`, `Require user` — Restrict access to a specific folder |
| 169 | Deploy Name-Based Virtual Hosts *(coming soon)* | `<VirtualHost *:80>`, `/etc/httpd/conf.d/` — Configure multiple virtual hosts resolving to the same IP |
| 170 | Configure Secure Virtual Hosts HTTPS *(coming soon)* | `ssl.conf`, `SSLCertificateFile`, `genkey` — Configure an HTTPS virtual host with self-signed certificates |

---

### 🔗 Remote Administration & Network Tools

> Remotely administer systems, transfer files, test ports, and verify network services.

| # | Lab | Key Commands |
|---|-----|-------------|
| 171 | SSH and SCP File Transfer *(coming soon)* | `ssh`, `scp` — Access VMs remotely and transfer files |
| 172 | Network Troubleshooting *(coming soon)* | `telnet`, `nmap` — Check listening services and scan ports |
| 173 | [Command-Line Web and FTP Testing](https://github.com/kelvintechnical/elinks-iftp) | `elinks -dump`, `lftp`, `get`, `mget`, `put` — Use elinks to test web connectivity and lftp to download and upload files |
| 174 | [Command-Line Email Testing](https://github.com/kelvintechnical/mutt-mail-smtp) | `mail -s`, `mutt -f`, `postfix`, `/var/mail/` — Use mail and mutt to test local SMTP and verify mail spool delivery |

---

### ⚡ System Performance & Tuning

> Identify and apply system tuning profiles using tuned.

| # | Lab | Key Commands |
|---|-----|-------------|
| 175 | [Enable Recommended Tuning Profile](https://github.com/kelvintechnical/tuning-profile) | `tuned-adm recommend`, `tuned-adm profile`, `tuned-adm active` |

---

### 📜 Shell Scripting & Automation

> Write conditional bash scripts that handle arguments, validate input, and return exit codes.

| # | Lab | Key Commands |
|---|-----|-------------|
| 176 | [Argument-Based Conditional Script](https://github.com/kelvintechnical/argument-script) | `$1`, `$#`, `if/elif/else`, `exit 5`, `chmod +x` — Write a script that reads user input using special variables |
| 177 | Use for Loops for Iteration *(coming soon)* | `for`, `getent passwd` — Write a script that cycles through a list of items |
| 178 | Evaluate Command Exit Codes *(coming soon)* | `$?` — Check the exit code to determine if a command succeeded or failed |
| 179 | Create a Directory Backup Script *(coming soon)* | `tar`, `date` — Build a script that takes source/destination arguments and creates a `.tar` backup named dynamically |

---

### 🐳 Containers & Runtime Management

> Build and run containerized Linux environments using Docker/Podman.

| # | Lab | Key Commands |
|---|-----|-------------|
| 180 | [Launch Named Root Container with Port Mapping](https://github.com/kelvintechnical/Launch-Named-Root-Container-with-Port-Mapping) | `podman run`, `docker run`, `-p`, `--name`, `-it` — Run containerized Linux environments with port mapping and interactive shells |

---

## 🤖 RHCE EX294 Labs

Labs organized by official RHCE EX294 exam objectives. Requires RHCSA as a prerequisite.

---

### 📡 Ansible Fundamentals

> Install Ansible, configure inventory, and run ad-hoc commands.

| # | Lab | Key Commands |
|---|-----|-------------|
| 01 | Ansible Installation and Inventory *(coming soon)* | `ansible`, `ansible.cfg`, `inventory` |
| 02 | Ansible Ad-Hoc Commands *(coming soon)* | `ansible -m`, `ping`, `command`, `shell` |

---

### 📝 Ansible Playbooks

> Write and execute YAML playbooks with tasks, handlers, and variables.

| # | Lab | Key Commands |
|---|-----|-------------|
| 03 | Write Your First Playbook *(coming soon)* | YAML syntax, `hosts`, `tasks`, `become` |
| 04 | Playbook Variables and Handlers *(coming soon)* | `vars`, `notify`, `handlers`, `register` |

---

### 🎭 Ansible Roles

> Structure reusable Ansible content using roles.

| # | Lab | Key Commands |
|---|-----|-------------|
| 05 | Create and Use Ansible Roles *(coming soon)* | `ansible-galaxy init`, role directory structure |
| 06 | Use Roles from Ansible Galaxy *(coming soon)* | `ansible-galaxy install`, `requirements.yml` |

---

### 🧩 Jinja2 Templates

> Generate dynamic config files using Ansible templates.

| # | Lab | Key Commands |
|---|-----|-------------|
| 07 | Create and Deploy Jinja2 Templates *(coming soon)* | `template` module, `{{ variable }}`, `{% for %}` |

---

### 🔒 Ansible Vault

> Encrypt and manage sensitive data in playbooks.

| # | Lab | Key Commands |
|---|-----|-------------|
| 08 | Encrypt Secrets with Ansible Vault *(coming soon)* | `ansible-vault create`, `encrypt`, `decrypt`, `--ask-vault-pass` |

---

## ☸️ CKA Labs

Labs organized by official CKA exam objectives.

---

### 🏗️ Cluster Architecture

> Understand Kubernetes components and cluster setup.

| # | Lab | Key Commands |
|---|-----|-------------|
| 01 | Explore Cluster Components *(coming soon)* | `kubectl get nodes`, `kubectl cluster-info` |
| 02 | Install a Cluster with kubeadm *(coming soon)* | `kubeadm init`, `kubeadm join` |

---

### 📦 Workloads

> Deploy and manage Pods, Deployments, and ReplicaSets.

| # | Lab | Key Commands |
|---|-----|-------------|
| 03 | Deploy and Manage Pods *(coming soon)* | `kubectl run`, `kubectl get pods`, `kubectl describe` |
| 04 | Create and Scale Deployments *(coming soon)* | `kubectl create deployment`, `kubectl scale` |
| 05 | Configure DaemonSets and Jobs *(coming soon)* | `kubectl apply -f`, DaemonSet/Job YAML |

---

### 🌐 Kubernetes Networking

> Configure Services, Ingress, and NetworkPolicy.

| # | Lab | Key Commands |
|---|-----|-------------|
| 06 | Expose Applications with Services *(coming soon)* | `kubectl expose`, ClusterIP, NodePort, LoadBalancer |
| 07 | Configure Ingress *(coming soon)* | Ingress YAML, `kubectl get ingress` |
| 08 | Apply NetworkPolicy *(coming soon)* | NetworkPolicy YAML, ingress/egress rules |

---

### 💾 Kubernetes Storage

> Manage persistent storage with PVs, PVCs, and StorageClasses.

| # | Lab | Key Commands |
|---|-----|-------------|
| 09 | Create PersistentVolumes and PVCs *(coming soon)* | PV/PVC YAML, `kubectl get pv` |
| 10 | Configure StorageClasses *(coming soon)* | StorageClass YAML, dynamic provisioning |

---

### 🔐 Kubernetes Security

> Manage RBAC, ServiceAccounts, and Secrets.

| # | Lab | Key Commands |
|---|-----|-------------|
| 11 | Configure RBAC *(coming soon)* | `Role`, `ClusterRole`, `RoleBinding`, `kubectl auth can-i` |
| 12 | Manage Secrets and ServiceAccounts *(coming soon)* | `kubectl create secret`, ServiceAccount YAML |

---

### 🔧 Cluster Maintenance

> Upgrade clusters, manage nodes, and back up etcd.

| # | Lab | Key Commands |
|---|-----|-------------|
| 13 | Upgrade a Kubernetes Cluster *(coming soon)* | `kubeadm upgrade`, `apt-get`, `kubectl drain` |
| 14 | Back Up and Restore etcd *(coming soon)* | `etcdctl snapshot save`, `snapshot restore` |

---

### 🔍 Kubernetes Troubleshooting

> Diagnose and fix failing pods, nodes, and cluster components.

| # | Lab | Key Commands |
|---|-----|-------------|
| 15 | Troubleshoot Pods and Deployments *(coming soon)* | `kubectl logs`, `kubectl describe`, `kubectl exec` |
| 16 | Troubleshoot Node and Cluster Failures *(coming soon)* | `kubectl get nodes`, `systemctl status kubelet` |

---

## 🧭 How to Use This Repo

1. **New to Linux?** Start with the [companion repos](#-companion-repos) above
2. **RHCSA prep?** Work through the [RHCSA labs](#-rhcsa-ex200-labs) in domain order
3. **RHCE prep?** Complete RHCSA first, then move to [RHCE labs](#-rhce-ex294-labs)
4. **CKA prep?** Tackle [CKA labs](#-cka-labs) after solid Linux fundamentals
5. **Practice on a RHEL AMI** — all RHCSA/RHCE labs tested on AWS RHEL 9 AMI

---

## 👤 Author & Connect

**Kelvin R. Tobias** — Software Engineer | AI Engineering Candidate | Consultant
📍 Kinston, NC

- B.S. Software Engineering, WGU (2026) — 3× Excellence Award
- M.S. AI Engineering, WGU (in progress)
- TEDxRaleigh 2026 Speaker
- Certs: CompTIA Security+, Linux+, AWS Cloud Practitioner, ITIL 4 Foundation
- ✍️ Blog: [PyTorch Zero to One](https://hashnode.com/@kelvintechnical) — 32+ articles

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Kelvin%20Tobias-0A66C2?logo=linkedin)](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
[![GitHub](https://img.shields.io/badge/GitHub-kelvintechnical-181717?logo=github)](https://github.com/kelvintechnical)
[![Website](https://img.shields.io/badge/Web-kelvinintech.com-808000?logo=google-chrome)](https://kelvinintech.com)
[![Hashnode](https://img.shields.io/badge/Blog-PyTorch%20Zero%20to%20One-2962FF?logo=hashnode)](https://hashnode.com/@kelvintechnical)

---

<div align="center">

**⭐ Star this repo if it helped you on your Linux journey.**

*Part of a larger engineering stack — from Linux ops to AI infrastructure to computational biology research.*

</div>
