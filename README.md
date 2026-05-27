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
- [Tech Affiliates — How to Install Linux](#-tech-affiliates--how-to-install-linux)
- [Companion Repos](#-companion-repos) 
- [Certification Path](#-certification-path) 
- [Suggested Learning Path](#-suggested-learning-path) 
- [Roadmap (212+ labs)](#-roadmap) 
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

## 🧰 Tech Affiliates — How to Install Linux

> **Brand new to Linux and not sure how to even get it on your laptop?** Start here.

A beginner-friendly, step-by-step install guide written for students **from middle school all the way to working adults**. It covers what Linux is, what a virtual machine is, what WSL is, and walks you through installing Linux on **Windows**, **Intel Mac**, and **Apple Silicon (M1/M2/M3/M4) Mac** — with troubleshooting and a full FAQ.

📘 **[Open the guide → Tech-Affiliates-How-To-Install-Linux.md](./Tech-Affiliates-How-To-Install-Linux.md)**

| You have... | The guide recommends... |
|---|---|
| 🪟 Windows 10 / 11 | WSL (10-minute install) |
| 💻 Intel Mac | VirtualBox VM |
| 🍏 Apple Silicon Mac (M1/M2/M3/M4) | UTM or Multipass |
| 🧪 An old laptop | Full install / dual boot (advanced) |

**Pairs with these Tech Affiliates resources:**

- 🐧 [linux-ops-mastery (main repo)](https://github.com/kelvintechnical/linux-ops-mastery) — the 212+ hands-on labs you'll work through after you install Linux.
- 🎓 [Tech-Affiliates-Comptia-Linux-Preparation](https://github.com/kelvintechnical/Tech-Affiliates-Comptia-Linux-Preparation) — the 8-week CompTIA Linux+ course (Tech Affiliates X Lenoir Community College, Kinston, NC).
- 📅 [Course outline](https://github.com/kelvintechnical/Tech-Affiliates-Comptia-Linux-Preparation) — week-by-week schedule.

---

## 🔗 Companion Repos

Foundational Linux skills broken into focused, standalone learning resources:

| Repo | Topic |
|------|-------|
| 🌐 [accessing-your-linux-system](https://github.com/kelvintechnical/accessing-your-linux-system) | Console access, SSH, PuTTY, AWS EC2 |
| 🗂 [managing-linux-files-cli](https://github.com/kelvintechnical/managing-linux-files-cli) | File system, file management, links, I/O redirection, pipes |

**Ansible (RHCE prep):** Hands-on labs aligned with *Mastering Ansible, 4th Edition* — inventory through network automation — are listed under **[RHCE EX294 Labs](#-rhce-ex294-labs)** (subsection *Mastering Ansible — full chapter labs*).

> 💡 **Start here if you're new to Linux** — these repos build the foundation before diving into RHCSA-level material.

---

### 🗂️ Linux Filesystem Hierarchy Standard (FHS)
> Before touching a single command, know where everything lives. This reference repo documents every directory in the Linux root filesystem (`/`) with hands-on labs showing real-world purpose.

| Repo | Topic |
|------|-------|
| 🗂️ [Linux-Filesystem-Hierarchy-Standard](https://github.com/kelvintechnical/Linux-Filesystem-Hierarchy-Standard) | What every `/` directory is, why it exists, and how to use it |

---

## 🗺️ Certification Path

| Phase | Certification | Exam | Status |
|-------|--------------|------|--------|
| Foundation | CompTIA Linux+ | XK0-005 | ✅ Complete |
| Intermediate | RHCSA | EX200 | 🔄 In Progress |
| Advanced | RHCE (Ansible) | EX294 | 🔜 Planned |
| Cloud Native | CKA (Kubernetes) | CKA | 🔜 Planned | 
 
--- 
 
## 🗺️ Suggested Learning Path 
 
> Labs in this repo are globally numbered. **Work through the modules in order** — each module unlocks the next. 
> For the full curriculum (every planned RHCSA/RHCE/CKA/CKAD lab including 183+ future labs), see the **[Roadmap](./roadmap.md)**. 
 
| Module | Labs | Focus | Time | 
|---|---|---|---| 
| **1. Shells & Text Fluency** | 01–27 | stdout/stderr/pipes, file operations, find/grep/sed/awk, vi | ~2 weeks | 
| **2. Documentation & Networking** | 28–39 | man/whatis/apropos, nmcli, /etc/hosts, DNS, SSH key auth | ~1 week | 
| **3. Permissions, ACLs, Firewall** | 40–67 | chmod/chown, SUID/SGID, getfacl/setfacl, firewalld zones + NAT | ~2 weeks | 
| **4. TCP Wrappers, PAM, SELinux** | 68–84 | hosts.allow/deny, pam_pwquality/securetty, sestatus, semanage, restorecon, sealert | ~2 weeks | 
| **5. Boot, Systemd, Logging** | 85–106 | GRUB, rd.break root reset, systemctl, journalctl, rsyslog | ~1 week | 
| **6. Storage, LVM, Mounts** | 107–136 | partitioning, mkfs.ext4/xfs, fstab UUID/LABEL, pvcreate→vgcreate→lvcreate, autofs | ~2 weeks | 
| **7. Packages, Users, Sudo** | 137–183 | rpm/dnf, custom repos, useradd/groupadd, chage, visudo, /etc/skel | ~1 week | 
| **8. Processes, Archives, Cron** | 184–207 | ps/top/nice/renice/kill, tar/gzip/bzip2/xz, crontab, at, anacron | ~1 week | 
| **9. GPG, Remote Admin, Security** | 208–220 | gpg keygen/encrypt, ssh/scp, telnet/nmap, bastion hardening | ~3 days | 
| **10. Web, Tuning, Scripting, Containers** | 221–227 | httpd + SELinux contexts, tuned-adm, argument-validating bash, podman | ~3 days | 
| **11+. RHCE → CKA → CKAD** | — | Ansible playbooks/roles/vault, Kubernetes admin, Kubernetes app dev | see [Roadmap](./roadmap.md) | 
 
> **About this order:** within each module, labs are sequenced foundation → advanced. Across modules, prerequisites flow forward — you can't fully grok LVM (Module 6) until you have `find`/`grep` from Module 1, and you can't do SELinux (Module 4) until you've configured standard permissions in Module 3. **Skip at your own risk.** 
> 
> **About the by-category tables below:** they're the *reference index*, not the *study order*. Use them when you need a specific command — not as a curriculum. 
 
--- 
 
## 🗺️ Roadmap 
 
The labs in this README are the *currently scoped* curriculum. The full multi-cert plan — **212+ labs** across RHCSA, RHCE (Ansible), CKA, and CKAD — lives in **[roadmap.md](./roadmap.md)**, organized by exam objective with status flags (✅ Done · 🚧 In Progress · 📅 Planned) and per-category future-lab IDs (`LVM-F01`, `NET-F03`, `CKAD-DES-F02`...). 
 
| Track | Labs in Roadmap | 
|---|---| 
| 🐧 RHCSA EX200 | 150 (5 done · 8 in progress · 137 planned) | 
| 🤖 RHCE EX294 (Ansible) | 20 planned | 
| ☸️ CKA (Kubernetes Administrator) | 20 planned | 
| 🚢 CKAD (Kubernetes App Developer) | 22 planned | 
 
> See [roadmap.md](./roadmap.md) for the full per-lab breakdown, including the 13 labs already in [`labs/`](./labs/) with file links. 
 
--- 
 
## 🧪 RHCSA EX200 Labs 

Labs organized by official RHCSA EX200 exam objectives.

---

### 🖥️ Shells, Terminals & Redirection

> Understand stdout, stderr, pipes, and how to control where command output goes.

| # | Lab | Key Commands |
|---|-----|-------------|
| 01 | [Standard Output Redirection](https://github.com/kelvintechnical/stdout-redirection) | `>`, `>>`, `cat` — Use `>` to direct output into a new file and `>>` to append output to an existing file |
| 02 | [Standard Error Redirection](https://github.com/kelvintechnical/stderr-redirection) | `2>`, `2>/dev/null` — Force a command to generate an error and redirect that error stream to a file or discard it |
| 03 | [Pipe Text Streams](https://github.com/kelvintechnical/pipe-text-streams) | `\|`, `less`, `grep`, `tee`, `wc -l` — Combine multiple commands using `\|` to send stdout of one command into stdin of another |
| 04 | [Capture Both Output and Error](https://github.com/kelvintechnical/capture-both-output-error/blob/main/README.md) | `&>`, `2>&1` — Send both stdout and stderr to the same file using the `&>` operator |

---

### 🔧 Essential Tools & File Operations

> Search, filter, redirect, compress, and manage files from the command line.

| # | Lab | Key Commands |
|---|-----|-------------|
| 05 | [Directory Navigation](labs/directory-nav/) | `cd`, `pwd`, `ls` — Five-task ADHD-format drill for absolute paths, relative paths, `..`, `cd -`, and `ls` evidence capture |
| 06 | [Listing Files and SELinux Contexts](labs/listing-files-selinux/) | `ls -l`, `ls -Z`, `ps -eZ`, `matchpathcon` — Five-task ADHD-format drill for DAC columns, SELinux contexts, traps, persistence checks, and journal writes |
| 07 | [Creating Empty Files and Timestamps](https://github.com/kelvintechnical/touch-timestamps/blob/main/README.md) | `touch` — Create an empty file and update the last modification timestamp |
| 08 | [Copying Files and Directories](https://github.com/kelvintechnical/copying-files-directories) | `cp`, `cp -R`, `cp -a` — Copy single files and entire directory structures recursively |
| 09 | [Hard and Soft Links](https://github.com/kelvintechnical/hard-and-soft-links/blob/main/README.md) | `ln`, `ln -s` — Create a hard link pointing to the same inode, then create a soft link and observe the differences |
| 10 | [Moving and Renaming Files](https://github.com/kelvintechnical/moving-renaming-files/blob/main/README.md) | `mv` — Use `mv` to rename files locally and move files from one directory to another |
| 11 | [Safe Deletion of Files and Directories](https://github.com/kelvintechnical/safe-deletion/blob/main/README.md) | `rm`, `rmdir`, `rm -rf` — Delete files with `rm`, empty directories with `rmdir`, and entire trees with `rm -rf` |
| 12 | [Creating Nested Directories](https://github.com/kelvintechnical/creating-nested-directories) | `mkdir -p` — Create a long nested directory structure in a single command |
| 13 | [Creating Command Aliases](https://github.com/kelvintechnical/creating-command-aliases) | `alias` — Map a custom shortcut to a standard command and understand how aliases can override defaults |
| 14 | [File Searching with find](https://github.com/kelvintechnical/searching-with-find) | `find` — Search the filesystem for specific files by name starting from root or a specific subdirectory |
| 15 | [Instant File Searching with locate](https://github.com/kelvintechnical/searching-with-locate) | `locate`, `updatedb` — Run the manual database update script and use `locate` to instantly find files |
| 16 | [Search for a String and Save Output](https://github.com/kelvintechnical/search-string-save-output) | `grep`, `tee`, `>` — Search for strings inside config files and experiment with regular expressions |
| 17 | [Find and Save Config Files](https://github.com/kelvintechnical/find-save-config-files) | `find -type f -name -user`, `2>/dev/null` — Search the filesystem for specific files by name |
| 18 | [Locate Command Documentation](https://github.com/kelvintechnical/locate-command-docs) | `find /usr/share/doc`, `rpm -qf`, `rpm -qd` — Find documentation when you only know a keyword or purpose |

---

### 📄 Text File Management

> Read, filter, edit, and compare text files from the command line.

| # | Lab | Key Commands |
|---|-----|-------------|
| 19 | [Concatenating Files with cat](https://github.com/kelvintechnical/concactenating-files-with-cat) | `cat` — Use `cat` to read the contents of short text files directly in the terminal |
| 20 | [Scrolling Through Large Files](https://github.com/kelvintechnical/less-more-scrolling) | `less`, `more` — Scroll through large system logs and search using `/` and `?` |
| 21 | [Monitoring Live Log Files](https://github.com/kelvintechnical/tail-f-live-logs) | `tail -f` — Actively monitor a log file and watch new lines appended in real-time |
| 22 | [Filtering Text with grep and Regex](https://github.com/kelvintechnical/grep-regex) | `grep` — Search for strings inside config files and experiment with regular expressions |
| 23 | [Comparing File Differences with diff](https://github.com/kelvintechnical/diff-comparing-files) | `diff` — Modify a config file and use `diff` to compare it against a backup to identify exact line changes |
| 24 | [Stream Editing with sed](https://github.com/kelvintechnical/sed-stream-editor) | `sed` — Use `sed` to automatically find and replace text strings within a file without opening an editor |
| 25 | [Extracting Columns with awk](https://github.com/kelvintechnical/awk-columns) | `awk` — Use `awk` to specify a delimiter and print only a specific field to the screen |
| 26 | [Command Mode and Insert Mode in vi](https://github.com/kelvintechnical/vi-editor) | `vi`, `:wq` — Open a config file in vi, switch to insert mode, make a change, and save with `:wq` |
| 27 | [Safely Editing System Databases](https://github.com/kelvintechnical/vipw-vigr-safe-editing) | `vipw`, `vigr` — Practice editing password and group files safely using `vipw` and `vigr` |

---

### 📖 Documentation Tools

> Look up man pages, keyword searches, and info pages.

| # | Lab | Key Commands |
|---|-----|-------------|
| 28 | [Exploring Manual Pages](https://github.com/kelvintechnical/man-pages-exploration) | `man` — Look up manual pages with `man` and practice scrolling through descriptions and syntax examples |
| 29 | [Searching Manuals by Keyword](https://github.com/kelvintechnical/whatis-apropos-keyword-search) | `whatis`, `apropos` — Find documentation when you only know a keyword or purpose |
| 30 | [Navigating info Pages](https://github.com/kelvintechnical/info-pages-navigation) | `info` — Use `info` to read detailed manual pages, navigating with `n`, `p`, and `u` keys |

---

### 🌐 Networking

> Configure and manage network interfaces, static IPs, hostnames, SSH, and DNS.

| # | Lab | Key Commands |
|---|-----|-------------|
| 31 | [Configure a Static IP Address](https://github.com/kelvintechnical/static-ip-address) | `nmcli con mod`, `ip addr`, `ip route` — Configure a network interface with a static IPv4 address, gateway, and DNS using `nmcli` |
| 32 | [Check Network Connectivity](https://github.com/kelvintechnical/network-connectivity-check) | `ping`, `traceroute` — Use `ping` to test connections and `traceroute` to map the path packets take across the network |
| 33 | [Display IP and Routing Info](https://github.com/kelvintechnical/ip-and-routing-info) | `ip addr show`, `ip route show` — Use `ip addr show` to check IP assignments and `ip route show` to review the routing table |
| 34 | [Inspecting Listening Sockets](https://github.com/kelvintechnical/listening-sockets) | `ss -tuna4` — View active TCP and UDP sockets and identify open ports |
| 35 | [Text-Based Network Config nmtui](https://github.com/kelvintechnical/nmtui-network-config) | `nmtui` — Launch `nmtui` to set a static IPv4 address, subnet mask, gateway, and DNS |
| 36 | [Command-Line Network Config nmcli](https://github.com/kelvintechnical/nmcli-network-config) | `nmcli` — Use `nmcli` to modify connection settings and reload a network interface |
| 37 | [Configuring Local Host Resolution](https://github.com/kelvintechnical/local-host-resolution) | `/etc/hosts` — Open `/etc/hosts` and manually map IP addresses to hostnames for local name resolution |
| 38 | [Configuring DNS Servers](https://github.com/kelvintechnical/dns-servers-config) | `/etc/resolv.conf` — Examine and modify `/etc/resolv.conf` to specify external name servers and search domains |
| 39 | [Configure SSH and Key-Based Auth](https://github.com/kelvintechnical/ssh-key-based-auth) | `ssh-keygen`, `ssh-copy-id` — Generate an RSA key pair and deploy it for passwordless login |

---

### 🔒 Permissions, Special Bits & ACLs

> Configure standard permissions, special bits, and access control lists.

| # | Lab | Key Commands |
|---|-----|-------------|
| 40 | [Standard File Permissions](https://github.com/kelvintechnical/standard-file-permissions) | `chmod` — Use `chmod` to list, set, and change standard ugo/rwx permissions |
| 41 | [Changing Ownership](https://github.com/kelvintechnical/changing-file-ownership) | `chown`, `chgrp` — Reassign file and directory ownership using `chown` and `chgrp` |
| 42 | [SUID Executables](https://github.com/kelvintechnical/suid-executables) | `chmod u+s`, `ls -l` — Configure the SUID bit on a file and observe how it executes with the privileges of the file owner |
| 43 | [Configure SGID and Sticky Bit](https://github.com/kelvintechnical/sgid-sticky-bit) | `chmod g+s`, `chmod +t`, `ls -ld` — Create a directory with SGID set so new files inherit the group ownership of the parent |
| 44 | [Immutable File Attribute](https://github.com/kelvintechnical/immutable-file-attribute) | `chattr +i`, `lsattr` — Use `chattr +i` to make a critical file immutable, preventing deletion even by root |
| 45 | [Append-Only File Attribute](https://github.com/kelvintechnical/append-only-file-attribute) | `chattr +a`, `lsattr` — Use `chattr +a` on a log file to ensure data can only be appended and never overwritten |
| 46 | [Identifying File Attributes](https://github.com/kelvintechnical/identifying-file-attributes) | `lsattr` — Use `lsattr` to list extended attributes of files on ext4 or XFS filesystems |
| 47 | [Check ACL Support](https://github.com/kelvintechnical/acl-support-check) | `mount`, `acl` option — Verify a filesystem is mounted with the `acl` option using the `mount` command |
| 48 | [Viewing ACLs](https://github.com/kelvintechnical/viewing-acls) | `getfacl` — Inspect a file's current access control list using `getfacl` |
| 49 | [Modifying ACLs](https://github.com/kelvintechnical/modifying-acls) | `setfacl -m` — Use `setfacl` to grant a specific user read and write access to a file |
| 50 | [Denying Access via ACLs](https://github.com/kelvintechnical/acl-deny-access) | `setfacl` — Implement an ACL to explicitly deny access to a specific user |
| 51 | [Default Directory ACLs](https://github.com/kelvintechnical/default-directory-acls) | `setfacl -d` — Configure a default ACL on a directory so newly created files automatically inherit permissions |
| 52 | [ACL Masks](https://github.com/kelvintechnical/acl-masks) | `setfacl -m m::` — Use `setfacl` to set a mask that caps maximum allowable permissions for users and groups |
| 53 | [Removing ACLs](https://github.com/kelvintechnical/removing-acls) | `setfacl -x`, `setfacl -b` — Strip specific ACL entries with `setfacl -x` or remove all ACLs with `setfacl -b` |
| 54 | [NFSv4 ACLs](https://github.com/kelvintechnical/nfsv4-acls) | `nfs4_getfacl`, `nfs4_setfacl` — Use `nfs4_getfacl` and `nfs4_setfacl` to display and edit permissions on an NFS v4 share |

---

### 🔥 Firewall (firewalld)

> Manage firewall rules, zones, ports, services, NAT, and rich rules.

| # | Lab | Key Commands |
|---|-----|-------------|
| 55 | [Inspecting iptables](https://github.com/kelvintechnical/inspecting-iptables) | `iptables -L` — Review the default filtering chains and packet rules using `iptables -L` |
| 56 | [Exploring firewalld Zones](https://github.com/kelvintechnical/firewalld-zones) | `firewall-cmd --get-default-zone`, `--list-all` — List available and active zones |
| 57 | [Changing Default Firewall Zone](https://github.com/kelvintechnical/default-firewall-zone) | `firewall-cmd --set-default-zone` — Reassign an active interface from the public zone to the dmz or internal zone |
| 58 | [Adding Services to Zones](https://github.com/kelvintechnical/firewalld-add-services) | `firewall-cmd --add-service`, `--permanent` — Permanently open ports for a service using `firewall-cmd --add-service` and reload |
| 59 | [Opening Custom Ports](https://github.com/kelvintechnical/firewalld-custom-ports) | `firewall-cmd --add-port` — Open a non-standard port by adding it directly to a zone |
| 60 | [Inspect Active Firewall Zones](https://github.com/kelvintechnical/active-firewall-zones) | `firewall-cmd --get-default-zone`, `--list-all` — Review zones and allowed services |
| 61 | [Reassign Interfaces to Zones](https://github.com/kelvintechnical/reassign-interfaces-zones) | `firewall-cmd --change-interface` — Temporarily and permanently move a network interface between zones |
| 62 | [Allow Services Through Firewall](https://github.com/kelvintechnical/firewall-allow-services) | `firewall-cmd --permanent --add-service` — Use `firewall-cmd` to open ports for web and FTP servers |
| 63 | [Configure IP Masquerading NAT](https://github.com/kelvintechnical/ip-masquerading-nat) | `firewall-cmd --add-masquerade` — Enable IP masquerading on the external zone |
| 64 | [Configure IP Forwarding](https://github.com/kelvintechnical/ip-forwarding) | `/etc/sysctl.conf`, `sysctl -p` — Edit `/etc/sysctl.conf` to enable `net.ipv4.ip_forward = 1` and apply with `sysctl -p` |
| 65 | [Configure Rich Rules](https://github.com/kelvintechnical/firewalld-rich-rules) | `firewall-cmd --add-rich-rule` — Use `firewall-cmd` to create a rich rule that denies traffic from a specific host |
| 66 | [Setup Port Forwarding DNAT](https://github.com/kelvintechnical/port-forwarding-dnat) | `firewall-cmd` rich rules — Use `firewalld` rich rules to redirect inbound traffic from port 80 to port 8008 |
| 67 | [Configure ICMP Filters](https://github.com/kelvintechnical/icmp-filters) | `firewall-cmd --add-icmp-block` — Block specific ICMP message types like `echo-request` to drop ping floods |

---

### 🔐 TCP Wrappers & PAM

> Restrict network access and enforce authentication policies.

| # | Lab | Key Commands |
|---|-----|-------------|
| 68 | [Verify TCP Wrappers Support](https://github.com/kelvintechnical/tcp-wrappers-support) | `ldd /usr/sbin/sshd \| grep libwrap` — Confirm SSH is linked to TCP Wrappers |
| 69 | [Restrict Access via hosts.deny](https://github.com/kelvintechnical/hosts-deny-restrictions) | `/etc/hosts.deny` — Edit with `ALL : ALL` to block all wrapper-aware network traffic by default |
| 70 | [Allow Specific Access via hosts.allow](https://github.com/kelvintechnical/hosts-allow-access) | `/etc/hosts.allow` — Explicitly allow SSH from localhost and a specific subnet |
| 71 | [Configure TCP Wrappers for FTP](https://github.com/kelvintechnical/tcp-wrappers-ftp) | `vsftpd`, `/etc/hosts.deny` — Install `vsftpd`, enable the service, and configure TCP Wrappers to deny a specific IP |
| 72 | [Explore PAM Config Files](https://github.com/kelvintechnical/pam-config-files) | `/etc/pam.d/` — Inspect `/etc/pam.d/` files to understand PAM types and control flags |
| 73 | [Read PAM Module Documentation](https://github.com/kelvintechnical/pam-module-docs) | `/usr/share/doc/pam-*/txts/` — Review `pam_securetty.so` documentation |
| 74 | [Implement Password Complexity](https://github.com/kelvintechnical/password-complexity-pam) | `pam_pwquality.so`, `system-auth` — Review `pam_pwquality.so` in `system-auth` to see how RHEL enforces password rules |
| 75 | [Configure PAM to Limit root Access](https://github.com/kelvintechnical/pam-limit-root-access) | `pam_securetty.so` — Use `pam_securetty.so` to limit root logins to only virtual terminal 6 |
| 76 | [Use PAM to Limit User Access](https://github.com/kelvintechnical/pam-limit-user-access) | `/etc/nologin` — Create `/etc/nologin` with a custom message to block regular users from logging in |
| 77 | [Restrict Service Access by User List](https://github.com/kelvintechnical/pam-restrict-by-user-list) | `pam_listfile.so` — Configure `pam_listfile.so` to deny access to users defined in a text file |

---

### 🛡️ SELinux

> Manage SELinux modes, contexts, booleans, and troubleshoot denials.

| # | Lab | Key Commands |
|---|-----|-------------|
| 78 | [Managing SELinux Modes](https://github.com/kelvintechnical/selinux-modes-management) | `sestatus`, `setenforce` — Check SELinux status with `sestatus` and toggle between enforcing and permissive using `setenforce` |
| 79 | [Viewing SELinux Contexts](https://github.com/kelvintechnical/selinux-viewing-contexts) | `ls -Z`, `ps -eZ` — Use `ls -Z` to view file contexts and `ps -eZ` to view contexts of running processes |
| 80 | [Temporary Context Changes](https://github.com/kelvintechnical/selinux-temporary-contexts) | `chcon` — Use `chcon` to temporarily modify the SELinux type context of a custom directory |
| 81 | [Persistent Context Restoration](https://github.com/kelvintechnical/selinux-persistent-contexts) | `semanage fcontext`, `restorecon` — Use `semanage fcontext` to define persistent rules and apply them with `restorecon` |
| 82 | [Toggling SELinux Booleans](https://github.com/kelvintechnical/selinux-booleans) | `getsebool`, `setsebool -P` — Search available booleans, check their status, and make persistent changes with `setsebool -P` |
| 83 | [SELinux User Mapping](https://github.com/kelvintechnical/selinux-user-mapping) | `semanage login` — Map a Linux user account to a restricted SELinux user type such as `guest_u` or `staff_u` |
| 84 | [Troubleshooting SELinux](https://github.com/kelvintechnical/selinux-troubleshooting) | `audit.log`, `sealert` — Trigger a policy violation, locate it in `audit.log`, and analyze using `sealert` |

---

### 🥾 Boot Process & GRUB

> Understand the boot process, reset root passwords, and configure GRUB.

| # | Lab | Key Commands |
|---|-----|-------------|
| 85 | [Modify GRUB Timeout](https://github.com/kelvintechnical/grub-timeout) | `/etc/default/grub`, `GRUB_TIMEOUT` — Edit `GRUB_TIMEOUT` in `/etc/default/grub` to adjust bootloader countdown |
| 86 | [Enable Verbose Kernel Messages](https://github.com/kelvintechnical/verbose-kernel-messages) | `GRUB_CMDLINE_LINUX` — Remove the `quiet` keyword from `GRUB_CMDLINE_LINUX` to show verbose startup output |
| 87 | [Generate New GRUB Config](https://github.com/kelvintechnical/grub-mkconfig) | `grub2-mkconfig -o /boot/grub2/grub.cfg` — Run `grub2-mkconfig` to apply changes persistently |
| 88 | [Reset Root Password via Boot](https://github.com/kelvintechnical/reset-root-password-boot) | GRUB interrupt, `rd.break`, `chroot`, `passwd` — Append `rd.break` to interrupt boot before filesystem mount and reset root password |
| 89 | [Chroot into Rescue Filesystem](https://github.com/kelvintechnical/chroot-rescue-filesystem) | `chroot /mnt/sysimage` — Use `chroot /mnt/sysimage` to change root and make repairs to the installed system |

---

### ⚙️ Systemd & Services

> Manage system services, unit files, and boot targets.

| # | Lab | Key Commands |
|---|-----|-------------|
| 90 | [Check Default Boot Target](https://github.com/kelvintechnical/default-boot-target) | `systemctl get-default` — Use `systemctl get-default` to verify if system boots into graphical or multi-user target |
| 91 | [Change Default Boot Target](https://github.com/kelvintechnical/change-default-boot-target) | `systemctl set-default` — Configure system to permanently boot into text-based environment |
| 92 | [System Reboots and Shutdowns](https://github.com/kelvintechnical/reboot-shutdown-systemd) | `systemctl reboot`, `systemctl poweroff` — Use `systemctl reboot` and `systemctl poweroff` to safely transition system state |
| 93 | [List All System Units](https://github.com/kelvintechnical/list-system-units) | `systemctl list-units --all` — Run `systemctl list-units --all` to display state of all systemd units |
| 94 | [Check Service Status](https://github.com/kelvintechnical/service-status-check) | `systemctl status` — Verify running status, PID, and recent logs of a daemon using `systemctl status` |
| 95 | [Start and Stop Services](https://github.com/kelvintechnical/start-stop-services) | `systemctl start`, `systemctl stop` — Control active services on the fly |
| 96 | [Enable Services at Boot](https://github.com/kelvintechnical/enable-services-at-boot) | `systemctl enable` — Ensure services survive restart using `systemctl enable` to link to the default target |
| 97 | [Disable Services at Boot](https://github.com/kelvintechnical/disable-services-at-boot) | `systemctl disable` — Prevent a service from launching automatically using `systemctl disable` |
| 98 | [Mask System Services](https://github.com/kelvintechnical/mask-system-services) | `systemctl mask` — Use `systemctl mask` to prevent a conflicting daemon from being started accidentally |
| 99 | [Create and Manage systemd Unit Files](https://github.com/kelvintechnical/systemd-unit-files) | Unit file syntax, `systemctl daemon-reload` |

---

### 📋 Log Management

> Query and manage system logs using journalctl and rsyslog.

| # | Lab | Key Commands |
|---|-----|-------------|
| 100 | [Analyze Boot Performance](https://github.com/kelvintechnical/analyze-boot-performance) | `systemd-analyze blame` — Run `systemd-analyze blame` to identify services slowing down the boot process |
| 101 | [Query Logs with journalctl](https://github.com/kelvintechnical/journalctl-query-logs) | `journalctl -u`, `-p`, `--since`, `--until` — Use `journalctl` to read and filter system logs by priority using `-p warning` |
| 102 | [Configure Persistent Journal Logs](https://github.com/kelvintechnical/persistent-journal-logs) | `/var/log/journal` — Create `/var/log/journal` directory to force systemd to write logs persistently to disk |
| 103 | [Understand Log Routing](https://github.com/kelvintechnical/rsyslog-log-routing) | `/etc/rsyslog.conf` — Review `/etc/rsyslog.conf` to identify where different system and kernel messages are logged |
| 104 | [Monitor Authentication Logs](https://github.com/kelvintechnical/monitor-auth-logs-secure) | `/var/log/secure` — Check `/var/log/secure` to track user logins, SSH access, and failed authentication attempts |
| 105 | [Filter systemd Journals by Priority](https://github.com/kelvintechnical/journalctl-filter-priority) | `journalctl -p alert` — Use `journalctl -p alert` to query the journal filtering for high-priority errors |
| 106 | [Service-Specific Journal Logs](https://github.com/kelvintechnical/journalctl-service-logs) | `journalctl -u httpd` — Display journal entries for a specific daemon using `journalctl -u` |

---

### ⏰ System Time & Locale

> Set timezone, configure NTP, and ensure time synchronization persists.

| # | Lab | Key Commands |
|---|-----|-------------|
| 107 | [Configure Timezone and Time Synchronization](https://github.com/kelvintechnical/Configure-Timezone-and-Time-Synchronization) | `timedatectl`, `systemctl enable --now chronyd` — List timezones with `timedatectl list-timezones` and set timezone |
| 108 | [Check NTP Sync Status](https://github.com/kelvintechnical/check-ntp-sync-status) | `ntpq -p`, `chronyc tracking` — Verify NTP is actively synchronizing using `ntpq -p` or `chronyc tracking` |
| 109 | [Configure NTP Time Source](https://github.com/kelvintechnical/configure-ntp) | `/etc/chrony.conf`, `chronyc sources`, `iburst` — Open `/etc/chrony.conf` and configure server or peer directives for NTP synchronization |

---

### 💾 Storage Management

> Create and manage partitions, filesystems, and disk devices.

| # | Lab | Key Commands |
|---|-----|-------------|
| 110 | [Inspect Filesystems](https://github.com/kelvintechnical/inspect-filesystems-df-findmnt) | `df -h`, `findmnt` — Use `df -h` to view space on mounted filesystems and `findmnt` for tree-like view |
| 111 | [Display Partition Tables](https://github.com/kelvintechnical/display-partition-tables-fdisk) | `fdisk -l` — Run `fdisk -l` to list configured partitions from all attached hard drives |
| 112 | [Create MBR Partition with fdisk](https://github.com/kelvintechnical/create-mbr-partition-fdisk) *(needs spare disk / loop lab)* | `fdisk /dev/vdb` — Launch `fdisk`, create partition with `n`, print with `p`, write with `w` |
| 113 | [Change Partition Types in fdisk](https://github.com/kelvintechnical/change-partition-types-fdisk) *(needs spare disk / loop lab)* | `fdisk t` command — Use `t` command in `fdisk` with identifier `83` for Linux filesystem or `8e` for LVM |
| 114 | [Create GPT Partition with gdisk](https://github.com/kelvintechnical/create-gpt-partition-gdisk) *(needs spare disk / loop lab)* | `gdisk` — Launch `gdisk` to practice creating a GPT-based partition table |
| 115 | [Command-Line Partitioning with parted](https://github.com/kelvintechnical/partitioning-with-parted) *(needs spare disk / loop lab)* | `parted`, `mklabel`, `mkpart` — Use `parted` to create partitions directly from the command line |
| 116 | [Format Partition with XFS](https://github.com/kelvintechnical/format-partition-xfs) *(needs spare disk / loop lab)* | `mkfs.xfs` — Use `mkfs.xfs` to format a newly created partition with the default RHEL XFS filesystem |
| 117 | [Format Partition with Ext4](https://github.com/kelvintechnical/format-partition-ext4) *(needs spare disk / loop lab)* | `mkfs.ext4` — Use `mkfs.ext4` to format a partition with the ext4 journaling filesystem |
| 118 | [Check Filesystem Consistency](https://github.com/kelvintechnical/check-filesystem-fsck) *(needs spare disk / loop lab)* | `fsck.ext4`, `e2fsck -b BACKUP_SB`, `xfs_repair -n` — Detect corruption, recover via backup superblock, decode fsck exit codes |
| 119 | [Inspect Filesystem Features](https://github.com/kelvintechnical/inspect-filesystem-dumpe2fs) *(needs spare disk / loop lab)* | `dumpe2fs -h`, `tune2fs -O FEAT`, `xfs_info` — Read ext4 superblock features, classify COMPAT/INCOMPAT/RO_COMPAT, toggle feature bits |
| 120 | [Create and Activate Swap Space](https://github.com/kelvintechnical/create-activate-swap-space) | `mkswap`, `swapon`, `swapoff`, `/etc/fstab`, `vm.swappiness` — Format a swap partition + swap file, persist via fstab with priorities, tune `vm.swappiness` |

---

### 🗂 LVM (Logical Volume Management)

> Create, extend, and manage logical volumes.

| # | Lab | Key Commands |
|---|-----|-------------|
| 121 | [Initialize Physical Volumes](https://github.com/kelvintechnical/lvm-pvcreate-initialize-pv) *(needs spare disk / loop lab)* | `pvcreate`, `pvscan`, `wipefs -a`, `--dataalignment` — Write the LVM label, read it back with `hexdump`, and bake idempotency into ensure-pv scripts |
| 122 | [Display Physical Volumes](https://github.com/kelvintechnical/lvm-display-physical-volumes) *(needs spare disk / loop lab)* | `pvs -o`, `pvdisplay --maps`, `--reportformat json`, `--select`, `--sort` — Treat `pvs` as a SQL cursor and emit Prometheus-style PV metrics |
| 123 | [Create Volume Group](https://github.com/kelvintechnical/lvm-create-volume-group) *(needs spare disk / loop lab)* | `vgcreate -s`, `vgrename`, `vgcfgbackup`, `vgcfgrestore`, `--addtag` — Pool PVs, pick the extent size, back up metadata, and restore from `/etc/lvm/archive/` |
| 124 | [Display Volume Groups](https://github.com/kelvintechnical/lvm-display-volume-groups) *(needs spare disk / loop lab)* | `vgs -o`, `vgdisplay`, `--select 'vg_tags=prod'`, `--reportformat json` — Read the 6-char `vg_attr`, compute percent-free in awk, and export to node_exporter |
| 125 | [Create Logical Volume](https://github.com/kelvintechnical/lvm-create-logical-volume) *(needs spare disk / loop lab)* | `lvcreate -L`, `-l +100%FREE`, `--type striped`, `--type thin-pool`, `-s` — Build linear, striped, snapshot, and thin LVs; trace the device-mapper plumbing with `dmsetup` |
| 126 | [Display Logical Volumes](https://github.com/kelvintechnical/display-logical-volumes-lvs-lvdisplay) *(needs spare disk / loop lab)* | `lvs -o`, `lvs -a`, `lvdisplay --maps`, `--select 'data_percent>80'` — Decode the 10-char `lv_attr`, surface hidden `_tdata`/`_tmeta`, monitor thin-pool fill |
| 127 | [Extend Volume Group](https://github.com/kelvintechnical/extend-volume-group-vgextend) *(needs spare disk / loop lab)* | `vgextend`, `pvmove`, `vgreduce`, `vgreduce --removemissing` — Live hot-add of a new PV; drain a PV with `pvmove`; recover from a failed disk |
| 128 | [Extend Logical Volume](https://github.com/kelvintechnical/extend-logical-volume-lvextend) *(needs spare disk / loop lab)* | `lvextend -L +SIZE`, `-l +100%FREE`, `--resizefs / -r`, ext4 safe-shrink — Grow LV every way the exam asks; learn why XFS cannot shrink |
| 129 | [Resize Filesystem After Extend](https://github.com/kelvintechnical/resize-filesystem-xfs-growfs-resize2fs) *(needs spare disk / loop lab)* | `resize2fs DEV [SIZE]`, `xfs_growfs MOUNTPOINT`, `resize2fs -M`, `growpart + resize2fs` — Complete the grow workflow at the FS layer for ext4 and XFS |
| 130 | [Remove LVM Components](https://github.com/kelvintechnical/remove-lvm-components-lvremove-vgremove-pvremove) *(needs spare disk / loop lab)* | `lvremove`, `vgremove`, `pvremove`, `wipefs -a`, `vgcfgrestore` — Destroy in reverse; thin-pool teardown order; recover from accidental `vgremove` |
| LAB | [Create LV `lvol1` (ext4, 280 MB)](https://github.com/kelvintechnical/lvm-create-lvol1-ext4) | `pvcreate`, `vgcreate`, `lvcreate -L 280M -n lvol1 vgtest`, `mkfs.ext4`, `blkid`, `/etc/fstab` — Build a 280 MiB ext4 logical volume end-to-end and mount it persistently by UUID on `/mnt/mnt1` |

---

### 📁 Filesystem Mounts

> Mount, configure, and automate filesystem mounts.

| # | Lab | Key Commands |
|---|-----|-------------|
| 131 | Mount Filesystem Manually *(coming soon — needs EBS)* | `mount` — Use `mount` to manually attach a partition or logical volume to an empty directory |
| 132 | Retrieve Filesystem UUIDs *(coming soon)* | `blkid` — Run `blkid` to identify the UUID of formatted block devices for persistent mounting |
| 133 | Configure Persistent Mounts fstab *(coming soon)* | `/etc/fstab` — Edit `/etc/fstab` to add a new mount entry using UUID, mount point, and filesystem type |
| 134 | Mount Network CIFS Shares *(coming soon — needs Samba)* | `mount.cifs` — Use `mount.cifs` to mount a remote Windows or Samba share to a local directory |
| 135 | Remount with New Options *(coming soon)* | `mount -o remount` — Modify mount options of an actively mounted filesystem using `mount -o remount` |
| 136 | Manage Autofs Service *(coming soon)* | `systemctl` — Ensure the automounter is running and set to start at boot with `systemctl` |

---

### 📦 Package Management & Repositories

> Configure DNF repositories, install packages, manage RPMs, and manage software sources.

| # | Lab | Key Commands |
|---|-----|-------------|
| 137 | Install Local RPM Package *(coming soon)* | `rpm -ivh` — Use `rpm -ivh` to install an RPM package directly from a local directory |
| 138 | Upgrade RPM Package *(coming soon)* | `rpm -U`, `rpm -F` — Practice upgrading an existing package using `rpm -U` or `rpm -F` |
| 139 | Install New Kernel Safely *(coming soon)* | `rpm -ivh` — Use `rpm -ivh` to install a new kernel alongside the old one without overwriting |
| 140 | Uninstall Package rpm -e *(coming soon)* | `rpm -e` — Use `rpm -e` to remove a specific package from the system |
| 141 | Query All Installed Packages *(coming soon)* | `rpm -qa` — Run `rpm -qa` to retrieve a complete list of all installed RPM packages |
| 142 | Query Specific Package Info *(coming soon)* | `rpm -qi` — Use `rpm -qi` to display detailed metadata about a specific package |
| 143 | List Files Within Package *(coming soon)* | `rpm -ql` — Discover where an installed package placed its files using `rpm -ql` |
| 144 | Identify File Owner *(coming soon)* | `rpm -qf` — Find which RPM package provided a specific file using `rpm -qf` |
| 145 | Query Uninstalled RPMs *(coming soon)* | `rpm -p` — Inspect contents of an RPM file before installing using the `-p` switch |
| 146 | Verify Package Integrity *(coming soon)* | `rpm -V` — Check an installed package against the RPM database using `rpm -V` |
| 147 | System-Wide Verification *(coming soon)* | `rpm -Va` — Verify integrity of all installed packages using `rpm -Va` |
| 148 | Import GPG Key *(coming soon)* | `rpm --import` — Import a public GPG key into the RPM database |
| 149 | Check Package Signatures *(coming soon)* | `rpm -K` — Verify the cryptographic signature of an RPM using `rpm -K` before installation |
| 150 | [Configure Repository Access](https://github.com/kelvintechnical/Configure-Repository-Access-) | `dnf`, `tee`, `/etc/yum.repos.d/` — Create a `.repo` configuration file in `/etc/yum.repos.d/` pointing to a repository |
| 151 | Install Packages with dnf *(coming soon)* | `dnf install` — Use `dnf install` to install a package and automatically resolve dependencies |
| 152 | Remove Packages with dnf *(coming soon)* | `dnf remove` — Use `dnf remove` to uninstall a package and remove orphaned dependencies |
| 153 | Update System dnf update *(coming soon)* | `dnf update` — Update a specific package or the entire system using `dnf update` |
| 154 | Search for Software *(coming soon)* | `dnf search` — Search YUM repositories for a specific tool using `dnf search` |
| 155 | Find File Providers *(coming soon)* | `dnf whatprovides` — Use `dnf whatprovides` to locate the package providing a specific command or file |
| 156 | List dnf Packages *(coming soon)* | `dnf list` — Use `dnf list` to display both installed and available packages |
| 157 | Display Enabled Repositories *(coming soon)* | `dnf repolist all` — View all active repositories using `dnf repolist all` |
| 158 | View Package Group Info *(coming soon)* | `dnf group list`, `dnf group info` — Inspect available package groups |
| 159 | [Install Package Groups](https://github.com/kelvintechnical/install-package-group) | `dnf group list`, `dnf groupinstall`, `dnf groupremove` — Install a complete set of related software using `dnf group install` |
| 160 | Create Custom YUM Repository *(coming soon)* | `createrepo` — Copy RPMs into a local directory and use `createrepo` to generate XML metadata |
| 161 | [Managing Flatpak](https://github.com/kelvintechnical/Managing-Flatpak/blob/main/README.md) | `flatpak remote-add`, `flatpak install --user`, `flatpak list` |

---

### 👥 User & Group Management

> Create and manage users and groups, control login access, and enforce account policies.

| # | Lab | Key Commands |
|---|-----|-------------|
| 162 | Inspect Password Database *(coming soon)* | `/etc/passwd` — Review `/etc/passwd` to understand usernames, UIDs, GIDs, and home directory structure |
| 163 | Analyze Shadow File *(coming soon)* | `/etc/shadow` — Open `/etc/shadow` to view hashed passwords and identify password aging fields |
| 164 | Modify Default Password Aging *(coming soon)* | `/etc/login.defs` — Edit `/etc/login.defs` to set new default security policies like `PASS_MAX_DAYS` |
| 165 | [User & Group Management / Permissions](https://github.com/kelvintechnical/User-Group-Management-Permissions) | `useradd`, `groupadd`, `chown`, `chmod`, `id`, `getent` — Add a new user with `useradd` and assign a password securely with `passwd` |
| 166 | Modify Existing Account *(coming soon)* | `usermod -L`, `usermod -U`, `usermod -aG` — Use `usermod` to lock an account, unlock it, and append to a group |
| 167 | Advanced Group Management *(coming soon)* | `groupadd`, `gpasswd`, `groupmod` — Create a group with `groupadd`, assign admin with `gpasswd`, modify GID with `groupmod` |
| 168 | Force Password Changes *(coming soon)* | `chage` — Use `chage` to view password aging info and force a password change on next login |
| 169 | Safely Delete Users *(coming soon)* | `userdel -r` — Use `userdel -r` to remove a user and completely delete their home directory and mail spool |
| 170 | [Disable User Login Without Removing the Account](https://github.com/kelvintechnical/disable-user-login) | `usermod -s /sbin/nologin`, `getent passwd` — Modify a user to assign `/sbin/nologin` as their shell, preventing interactive access |
| 171 | Validate User and Group Creation *(coming soon)* | `/etc/group`, `/etc/shadow` — Create users, verify primary groups in `/etc/group`, check passwords in `/etc/shadow` |
| 172 | Proper Use of su vs su - *(coming soon)* | `su`, `su -` — Practice switching users with `su` and note environment variable differences with `su -` |
| 173 | Limit Access to su PAM *(coming soon)* | PAM, `wheel` group — Configure PAM to restrict `su` so only members of the wheel group can switch to root |
| 174 | Configure Custom Administrators *(coming soon)* | `visudo`, `/etc/sudoers` — Use `visudo` to edit `/etc/sudoers` and grant a user full administrative privileges |
| 175 | Granular sudo Privileges *(coming soon)* | `visudo`, `Cmnd_Alias` — Use `visudo` with `Cmnd_Alias` to grant permission to run only specific commands |
| 176 | Limit root Logins *(coming soon)* | `/etc/securetty` — Edit `/etc/securetty` to restrict which virtual consoles root can log into directly |
| 177 | Restrict Root to Single Console *(coming soon)* | `/etc/securetty` — Modify `/etc/securetty` so root can only log in locally via `tty6` and test the restriction |
| 178 | Populate Directory Templates *(coming soon)* | `/etc/skel` — Add custom files to `/etc/skel` and verify new users automatically receive them on creation |
| 179 | Manage Shell Environments *(coming soon)* | `.bash_profile`, `.bashrc` — Edit `.bash_profile` and `.bashrc` to configure persistent environment variables and aliases |
| 180 | Alter Global Default umask *(coming soon)* | `/etc/bashrc`, `/etc/profile` — Modify `/etc/bashrc` and `/etc/profile` to restrict default file permissions system-wide |
| 181 | Distribute Documentation via Skel *(coming soon)* | `/etc/skel` — Copy docs into `/etc/skel` so all new users automatically receive them on creation |
| 182 | Control Group Ownership SGID *(coming soon)* | `chmod g+s` — Create a shared directory with SGID set and verify new files inherit group ownership |
| 183 | Set Up Group-Managed Directory *(coming soon)* | `chmod 2770`, SGID — Create `/home/galley` for four users with SGID and permissions `2770` for group sharing |

---

### 🔄 Process Management

> Monitor, control, and prioritize running processes.

| # | Lab | Key Commands |
|---|-----|-------------|
| 184 | Audit All Running Processes *(coming soon)* | `ps aux` — Use `ps aux` to list all running processes and identify CPU and memory usage |
| 185 | Identify Process Details *(coming soon)* | `ps axl` — Use `ps axl` to display process details including parent PIDs and nice values |
| 186 | View SELinux Process Contexts *(coming soon)* | `ps -Z` — Identify SELinux security contexts of running daemons using `ps -Z` |
| 187 | Real-Time Process Monitoring *(coming soon)* | `top` — Launch `top` to monitor real-time system load, tasks, memory, and swap |
| 188 | Adjust Process Priority *(coming soon)* | `renice` — Use `renice` to change the priority of an already running CPU-intensive process |
| 189 | Start Processes with Custom Priority *(coming soon)* | `nice` — Use `nice` to launch a new process with a predefined priority level |
| 190 | Terminate Processes Gracefully *(coming soon)* | `kill` (SIGTERM) — Identify a PID and terminate it safely using `kill` which sends SIGTERM |
| 191 | Force Kill Unresponsive Processes *(coming soon)* | `kill -9` (SIGKILL) — Use `kill -9 SIGKILL` to forcibly terminate a hung process |
| 192 | Kill Processes by Name *(coming soon)* | `killall` — Terminate multiple instances of a process at once using `killall` |

---

### 🗜 Archives & Compression

> Compress files and create, extract, and preserve archives.

| # | Lab | Key Commands |
|---|-----|-------------|
| 193 | [Standard File Compression with gzip](https://github.com/kelvintechnical/standard-file-compression) | `gzip`, `gunzip`, `zcat` — Compress a large text file using `gzip` and view the resulting `.gz` file |
| 194 | [High-Ratio Compression with bzip2](https://github.com/kelvintechnical/high-ratio-compression) | `bzip2`, `bunzip2`, `bzcat` — Compress files using `bzip2` for higher compression ratio and extract with `bunzip2` |
| 195 | [Create Standard Archives with tar](https://github.com/kelvintechnical/create-standard-archives) | `tar -cvf`, `tar -tvf`, `tar -xvf` — Combine files and directories into a single uncompressed archive using `tar -cvf` |
| 196 | Create Compressed Archives *(coming soon)* | `tar -czf`, `tar -cjf`, `tar -cJf`, `xz` — Create a gzip-compressed tarball using `tar -czvf` |
| 197 | Extract Archives *(coming soon)* | `tar -xvf` — Extract contents of a `.tar.bz2` archive into a specific directory using `tar -xvf` |
| 198 | Preserve Security Contexts in Archives *(coming soon)* | `tar --selinux` — Create a tarball preserving SELinux contexts and ACLs using `tar --selinux` |

---

### 🕐 Scheduled Tasks

> Automate recurring and one-time tasks using cron and at.

| # | Lab | Key Commands |
|---|-----|-------------|
| 199 | Review System-Wide cron Jobs *(coming soon)* | `/etc/crontab` — Inspect `/etc/crontab` to understand minute, hour, day, month, day-of-week formatting |
| 200 | Schedule Tasks with cron *(coming soon)* | `crontab -e`, `/etc/cron.d/` — Use `crontab -e` to schedule a recurring script to run at a specific interval |
| 201 | Remove User cron Jobs *(coming soon)* | `crontab -l`, `crontab -r` — View active jobs with `crontab -l` and remove all user cron jobs with `crontab -r` |
| 202 | Schedule One-Time Task with at *(coming soon)* | `at` — Use `at` to schedule a command to execute exactly once at a specified time |
| 203 | Limit Access to cron *(coming soon)* | `/etc/cron.deny` — Restrict users from scheduling tasks by adding usernames to `/etc/cron.deny` |
| 204 | Limit Access to at *(coming soon)* | `/etc/at.allow`, `/etc/at.deny` — Control which users can schedule one-time tasks |
| 205 | Review the Anacron System *(coming soon)* | `/etc/anacrontab` — Examine `/etc/anacrontab` to see how RHEL ensures periodic jobs run after downtime |
| 206 | Create a Specific cron Job *(coming soon)* | `crontab -e` — Use `crontab -e` to schedule a script to run at 1:05 PM every Monday in January |
| 207 | Schedule Software Audit with at *(coming soon)* | `at` — Use `at` to run `rpm -qa > /root/rpms.txt` in exactly 5 minutes |
| LAB | [Scheduling Jobs (systemd timer, Mon–Fri 2 AM)](https://github.com/kelvintechnical/scheduling-jobs-systemd-timer) | `systemd.timer`, `OnCalendar=Mon..Fri *-*-* 02:00:00`, `systemctl daemon-reload`, `systemctl enable --now`, `journalctl -u`, `logger` — Build a `.timer` + `.service` unit pair that writes "hello folks" to syslog every weekday at 2 AM as a non-root user |

---

### 🔐 GPG Encryption

> Generate keys, encrypt, decrypt, and share GPG-protected files.

| # | Lab | Key Commands |
|---|-----|-------------|
| 208 | Generate a GPG Key Pair *(coming soon)* | `gpg --gen-key` — Run `gpg --gen-key` to create an RSA public/private key pair with a passphrase |
| 209 | Encrypt a File with GPG *(coming soon)* | `gpg --recipient --encrypt` — Create a text file and use `gpg --recipient --encrypt` to secure it |
| 210 | Decrypt a GPG File *(coming soon)* | `gpg --decrypt` — Use `gpg --decrypt` entering the passphrase to read the original plaintext contents |
| 211 | Share and Verify Public Keys *(coming soon)* | `gpg --export -a`, `scp`, `gpg --import` — Export a GPG key, transfer with `scp`, and import on another system |

---

### 🔗 Remote Administration & Network Tools

> Remotely administer systems, transfer files, test ports, and verify network services.

| # | Lab | Key Commands |
|---|-----|-------------|
| 212 | SSH and SCP File Transfer *(coming soon)* | `ssh`, `scp` — Access VMs remotely using `ssh` and transfer files using `scp` |
| 213 | Network Troubleshooting *(coming soon)* | `telnet`, `nmap` — Use `telnet` to check listening services and `nmap` to scan ports |
| 214 | [Command-Line Web and FTP Testing](https://github.com/kelvintechnical/elinks-iftp) | `elinks -dump`, `lftp`, `get`, `mget`, `put` — Use `elinks` to test web connectivity and `lftp` to download and upload files |
| 215 | [Command-Line Email Testing](https://github.com/kelvintechnical/mutt-mail-smtp) | `mail -s`, `mutt -f`, `postfix`, `/var/mail/` — Use `mail` and `mutt` to test local SMTP and verify `/var/mail` spool delivery |

---

### 🛡️ Security Administration

> Harden services, monitor updates, and build secure baseline configurations.

| # | Lab | Key Commands |
|---|-----|-------------|
| 216 | Service Isolation Bastion Host *(coming soon)* | `systemctl disable` — Configure a minimal VM to run only SSH and disable all other network services |
| 217 | Monitor Security Updates *(coming soon)* | `dnf update` — Review Red Hat Errata and apply latest security fixes using `dnf update` |
| 218 | Build a Bastion Server *(coming soon)* | minimal install, `systemctl` — Perform minimal RHEL install, confirm SSH is active, and disable unneeded services |
| 219 | Comprehensive firewalld Setup *(coming soon)* | `firewall-cmd` — Add HTTP and SSH permanently, block ICMP, configure masquerading and rich rules |
| 220 | PAM and SELinux with FTP *(coming soon)* | `vsftpd`, `ftp_home_dir`, PAM — Activate `ftp_home_dir` SELinux boolean, start `vsftpd`, verify PAM blocks root FTP login |

---

### 🌍 Web Services (Apache)

> Install, configure, and verify the Apache web server.

| # | Lab | Key Commands |
|---|-----|-------------|
| 221 | [Configure Apache to Serve Default and Custom Web Content](https://github.com/kelvintechnical/apache-custom-content) | `httpd`, `semanage fcontext`, `restorecon`, `curl` — Install Apache, start/enable the service, and deploy web content |
| 222 | Password-Protect a Directory *(coming soon)* | `htpasswd`, `AuthType Basic`, `Require user` — Configure a `<Directory>` container to restrict access to a specific folder |
| 223 | Deploy Name-Based Virtual Hosts *(coming soon)* | `<VirtualHost *:80>`, `/etc/httpd/conf.d/` — Configure multiple virtual hosts resolving to the same IP address |
| 224 | Configure Secure Virtual Hosts HTTPS *(coming soon)* | `ssl.conf`, `SSLCertificateFile`, `genkey` — Configure an HTTPS virtual host with self-signed certificates |

---

### ⚡ System Performance & Tuning

> Identify and apply system tuning profiles using tuned.

| # | Lab | Key Commands |
|---|-----|-------------|
| 225 | [Enable Recommended Tuning Profile](https://github.com/kelvintechnical/tuning-profile) | `tuned-adm recommend`, `tuned-adm profile`, `tuned-adm active` |

---

### 📜 Shell Scripting & Automation

> Write conditional bash scripts that handle arguments, validate input, and return exit codes.

| # | Lab | Key Commands |
|---|-----|-------------|
| 226 | [Argument-Based Conditional Script](https://github.com/kelvintechnical/argument-script) | `$1`, `$#`, `if/elif/else`, `exit 5`, `chmod +x` — Write a script that reads user input using special variables and checks conditions |
| 227 | Use for Loops for Iteration *(coming soon)* | `for`, `getent passwd` — Write a script that uses a `for` loop to cycle through a list of items |

---

### 🐳 Containers & Runtime Management

> Build and run containerized Linux environments using Docker/Podman.

| # | Lab | Key Commands |
|---|-----|-------------|
| LAB | [Launch Named Root Container with Port Mapping](https://github.com/kelvintechnical/Launch-Named-Root-Container-with-Port-Mapping) | `podman run`, `docker run`, `-p`, `--name`, `-it` — Run containerized Linux environments with port mapping and interactive shells (8-part lab) |

---

## 🤖 RHCE EX294 Labs

Labs organized by official RHCE EX294 exam objectives. Requires RHCSA as a prerequisite.

---

### 📡 Ansible Fundamentals

> Install Ansible, configure inventory, run ad-hoc commands, and work with collections (ansible-core + Galaxy).

| # | Lab | Key Commands |
|---|-----|-------------|
| 01 | [Ansible Architecture & Inventory](https://github.com/kelvintechnical/ansible-architecture-and-inventory) | `ansible`, `ansible.cfg`, `inventory`, `ansible-inventory`, `group_vars`, `host_vars` |
| 02 | [Ansible Collections & Migration](https://github.com/kelvintechnical/ansible-collections-and-migration) | `ansible-galaxy collection`, FQCN, `requirements.yml`, porting legacy playbooks |

---

### 📝 Ansible Playbooks

> Write YAML plays, control task flow, and use Jinja2 in templates and conditionals.

| # | Lab | Key Commands |
|---|-----|-------------|
| 03 | [Task Conditions, Blocks & Loops](https://github.com/kelvintechnical/ansible-task-conditions-loops) | `when`, `failed_when`, `changed_when`, `block`/`rescue`/`always`, `loop` |
| 04 | Write Your First Playbook *(coming soon)* | YAML syntax, `hosts`, `tasks`, `become` |

---

### 🎭 Ansible Roles

> Structure reusable Ansible content using roles, handlers, and Galaxy.

| # | Lab | Key Commands |
|---|-----|-------------|
| 05 | [Ansible Roles](https://github.com/kelvintechnical/ansible-roles) | `ansible-galaxy init`, `tasks/`, `handlers/`, `defaults/` vs `vars/`, `notify` |
| 06 | Use Roles from Ansible Galaxy *(coming soon)* | `ansible-galaxy role install`, `requirements.yml` |

---

### 🧩 Jinja2 Templates

> Generate dynamic config files using Ansible templates.

| # | Lab | Key Commands |
|---|-----|-------------|
| 07 | [Jinja2 Templates in Ansible](https://github.com/kelvintechnical/ansible-jinja2-templates) | `ansible.builtin.template`, `{{ }}`, `{% if %}`, `{% for %}`, filters, `validate:` |

---

### 🔒 Ansible Vault

> Encrypt and manage sensitive data in playbooks.

| # | Lab | Key Commands |
|---|-----|-------------|
| 08 | [Ansible Vault — Secrets at Rest](https://github.com/kelvintechnical/ansible-vault-secrets) | `ansible-vault create`, `encrypt_string`, `--vault-id`, `no_log`, mixing encrypted YAML |

---

### 🧯 Ansible Troubleshooting

> Debug playbooks, inspect configuration, and recover from failed automation runs.

| # | Lab | Key Commands |
|---|-----|-------------|
| 09 | [Troubleshooting Ansible](https://github.com/kelvintechnical/ansible-troubleshooting) | `--syntax-check`, `--check`, `--diff`, `-vvv`, `ansible-doc`, `ansible-config dump` |

---

### 🏢 Automation Platform & Windows

> Run Ansible in controller-style workflows and automate Windows targets.

| # | Lab | Key Commands |
|---|-----|-------------|
| 10 | [Windows Automation](https://github.com/kelvintechnical/ansible-windows-automation) | WinRM, `ansible.windows`, IIS automation, Windows facts |
| 11 | [AWX / Tower](https://github.com/kelvintechnical/ansible-awx-tower) | AWX Operator, projects, credentials, job templates, REST launch |

---

### 🚀 Advanced Ansible Patterns

> Extend Ansible, roll changes safely, provision infrastructure, and automate networks.

| # | Lab | Key Commands |
|---|-----|-------------|
| 12 | [Extending Ansible with Modules and Plugins](https://github.com/kelvintechnical/ansible-extending-modules-plugins) | `AnsibleModule`, `library/`, `filter_plugins/`, collections |
| 13 | [Rolling Deployments](https://github.com/kelvintechnical/ansible-rolling-deployments) | `serial`, `max_fail_percentage`, `wait_for`, load-balancer drain/add |
| 14 | [Infrastructure Provisioning](https://github.com/kelvintechnical/ansible-infrastructure-provisioning) | `amazon.aws.ec2_instance`, dynamic inventory, `add_host`, `wait_for_connection` |
| 15 | [Network Automation](https://github.com/kelvintechnical/ansible-network-automation) | `network_cli`, network collections, facts, config backup, drift remediation |

---

### 🎓 Mastering Ansible (4th Ed.) — full chapter labs

> Thirteen standalone repos mapped to the book’s chapters — architecture through network automation. Clone each repo’s `README.md` as the lab guide.

| Ch | Lab | Key topics |
|----|-----|------------|
| 1 | [Ansible Architecture & Inventory](https://github.com/kelvintechnical/ansible-architecture-and-inventory) | Config resolution, static inventory, `group_vars` / `host_vars`, `ansible all -m ping` |
| 2 | [Collections & Migration](https://github.com/kelvintechnical/ansible-collections-and-migration) | Collections, `ansible-galaxy collection install`, FQCN, `requirements.yml` |
| 3 | [Ansible Vault](https://github.com/kelvintechnical/ansible-vault-secrets) | Encrypt files & inline strings, multi `--vault-id`, `no_log` |
| 4 | [Windows Automation](https://github.com/kelvintechnical/ansible-windows-automation) | WinRM, `ansible.windows`, WSL control node, IIS capstone |
| 5 | [AWX / Tower](https://github.com/kelvintechnical/ansible-awx-tower) | Kubernetes + AWX Operator, Projects, Job Templates, REST API launch |
| 6 | [Jinja2 Templates](https://github.com/kelvintechnical/ansible-jinja2-templates) | Conditionals, loops, filters, real `httpd`/`template` + `validate:` |
| 7 | [Task Conditions & Loops](https://github.com/kelvintechnical/ansible-task-conditions-loops) | `when`, `failed_when`, `block`/`rescue`, `loop`, idempotent `command:` |
| 8 | [Ansible Roles](https://github.com/kelvintechnical/ansible-roles) | `ansible-galaxy init`, handlers, multi-group role application |
| 9 | [Troubleshooting Ansible](https://github.com/kelvintechnical/ansible-troubleshooting) | `-v`…`-vvvv`, `log_path`, `--check`/`--diff`, `--start-at-task` |
| 10 | [Extending Ansible](https://github.com/kelvintechnical/ansible-extending-modules-plugins) | Custom module, filter plugin, dynamic inventory script, `collection build` |
| 11 | [Rolling Deployments](https://github.com/kelvintechnical/ansible-rolling-deployments) | `serial`, `delegate_to`, `throttle`, `max_fail_percentage` |
| 12 | [Infrastructure Provisioning](https://github.com/kelvintechnical/ansible-infrastructure-provisioning) | `amazon.aws`, Azure, OpenStack, `community.docker`, multi-cloud skeleton |
| 13 | [Network Automation](https://github.com/kelvintechnical/ansible-network-automation) | `network_cli`, `ansible_network_os`, IOS/EOS commands & guarded `ios_config` |

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
