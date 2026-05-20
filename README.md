<div align="center">

# 🐧 Linux Ops Mastery

### A Hands-On Linux Operations Study Guide
**RHCSA → RHCE → Production AI/MLOps Infrastructure**

![RHCSA](https://img.shields.io/badge/RHCSA-EX200-EE0000?style=flat&logo=redhat&logoColor=white)
![RHCE](https://img.shields.io/badge/RHCE-EX294-EE0000?style=flat&logo=redhat&logoColor=white)
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
- [Modules](#-modules)
- [Labs by RHCSA Exam Domain](#-labs-by-rhcsa-exam-domain)
- [How to Use This Repo](#-how-to-use-this-repo)
- [Author & Connect](#-author--connect)

---

## 📖 About

A complete, hands-on Linux operations study guide built for engineers preparing for **RHCSA (EX200)** and **RHCE (EX294)** — and anyone building production-grade Linux skills for cloud, DevOps, or AI/MLOps infrastructure roles.

All commands tested on **RHEL 9** / **Rocky Linux** / **AWS RHEL AMI**.

---

## 🎯 Who This Is For

- Engineers preparing for **RHCSA** or **RHCE**
- DevOps / SRE / Platform engineers building Linux skills
- AI/MLOps practitioners deploying on Linux infrastructure
- Self-learners working through Red Hat certification objectives

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

## 🗺️ Certification Path

| Phase | Certification | Exam | Status |
|-------|--------------|------|--------|
| Foundation | CompTIA Linux+ | XK0-005 | ✅ Complete |
| Intermediate | RHCSA | EX200 | 🔄 In Progress |
| Advanced | RHCE (Ansible) | EX294 | 🔜 Planned |

---

## 📂 Modules

| # | Module | Focus |
|---|--------|-------|
| 01 | [System Management](./01-system-management/README.md) | Users, storage, boot, SELinux, networking |
| 02 | [Networking](./02-networking/README.md) | firewalld, SSH, advanced routing |
| 03 | [Containers](./03-containers/README.md) | Podman, systemd services, rootless containers |
| 04 | [Automation](./04-automation) | Ansible playbooks, roles, inventories (RHCE core) |
| 05 | [Labs Archive](./05-labs) | Exam-style scenario labs |

---

## 🧪 Labs by RHCSA Exam Domain

Labs are organized by the official RHCSA EX200 exam objectives. Each domain maps directly to what Red Hat tests on exam day.

---

### 🌐 Networking

> Configure and manage network interfaces, static IPs, hostnames, and DNS.

| # | Lab | Key Commands |
|---|-----|-------------|
| 01 | [Configure a Static IP Address](./01-system-management/README.md#lab-01--configure-a-static-ip-address) | `nmcli con mod`, `ip addr`, `ip route` |

---

### 📦 Package Management & Repositories

> Configure DNF repositories, install packages, and manage software sources.

| # | Lab | Key Commands |
|---|-----|-------------|
| 02 | [Configure Repository Access](https://github.com/kelvintechnical/Configure-Repository-Access-) | `dnf`, `tee`, `/etc/yum.repos.d/` |

---

### ⏰ System Time & Locale

> Set timezone, configure NTP, and ensure time synchronization persists.

| # | Lab | Key Commands |
|---|-----|-------------|
| 03 | [Configure Timezone and Time Synchronization](https://github.com/kelvintechnical/Configure-Timezone-and-Time-Synchronization) | `timedatectl`, `systemctl enable --now chronyd` |
| 04 | [Configure NTP Time Source](https://github.com/kelvintechnical/configure-ntp) | `/etc/chrony.conf`, `chronyc sources`, `iburst` |

---

### 🔧 Essential Tools & File Operations

> Search, filter, redirect, and manage files from the command line.

| # | Lab | Key Commands |
|---|-----|-------------|
| 05 | [Search for a String and Save Output](https://github.com/kelvintechnical/search-string-save-output) | `grep`, `tee`, `>` redirect |
| 06 | [Find and Save Config Files](https://github.com/kelvintechnical/find-save-config-files) | `find -type f -name -user`, `2>/dev/null` |
| 07 | [Locate Command Documentation](https://github.com/kelvintechnical/locate-command-docs) | `find /usr/share/doc`, `rpm -qf`, `rpm -qd` |

---

### 👥 User & Group Management

> Create and manage users and groups, control login access, and enforce account policies.

| # | Lab | Key Commands |
|---|-----|-------------|
| 08 | [User & Group Management / Permissions](https://github.com/kelvintechnical/User-Group-Management-Permissions) | `useradd`, `groupadd`, `chown`, `chmod`, `id`, `getent` |
| 09 | [Disable User Login Without Removing the Account](https://github.com/kelvintechnical/disable-user-login) | `usermod -s /sbin/nologin`, `getent passwd` |

---

### 🔒 Permissions & Special Bits

> Configure standard and special permissions (SGID, sticky bit) on files and directories.

| # | Lab | Key Commands |
|---|-----|-------------|
| 10 | [Configure SGID and Sticky Bit](https://github.com/kelvintechnical/sgid-sticky-bit) | `chmod g+s`, `chmod +t`, `ls -ld` |

---

### 🌍 Web Services (Apache)

> Install, configure, and verify the Apache web server and serve content from custom directories.

| # | Lab | Key Commands |
|---|-----|-------------|
| 11 | [Configure Apache to Serve Default and Custom Web Content](https://github.com/kelvintechnical/apache-custom-content) | `httpd`, `semanage fcontext`, `restorecon`, `curl` |

---

### ⚙️ System Performance & Tuning

> Identify and apply system tuning profiles using tuned.

| # | Lab | Key Commands |
|---|-----|-------------|
| 12 | [Enable Recommended Tuning Profile](https://github.com/kelvintechnical/tuning-profile) | `tuned-adm recommend`, `tuned-adm profile`, `tuned-adm active` |

---  

### 📜 Shell Scripting & Automation

> Write conditional bash scripts that handle arguments, validate input, and return exit codes.

| # | Lab | Key Commands |
|---|-----|-------------|
| 13 | [Argument-Based Conditional Script](https://github.com/kelvintechnical/argument-script) | `$1`, `$#`, `if/elif/else`, `exit 5`, `chmod +x` |

---

## 🧭 How to Use This Repo

1. **New to Linux?** Start with the [companion repos](#-companion-repos) above
2. **Ready for RHCSA?** Pick a domain from [Labs by RHCSA Exam Domain](#-labs-by-rhcsa-exam-domain)
3. **Practice on a RHEL AMI** — all labs tested on AWS RHEL 9 AMI
4. **Follow labs in order within each domain** — each builds on the last

---

## 👤 Author & Connect

**Kelvin R. Tobias** — Software Engineer | AI Engineering Candidate | Consultant
📍 Kinston, NC

- B.S. Software Engineering, WGU (2026) — 3× Excellence Award
- M.S. AI Engineering, WGU (in progress)
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
