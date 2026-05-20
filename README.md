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
- [Labs](#-labs)
- [RHCSA Exam Coverage](#-rhcsa-exam-coverage)
- [How to Use This Repo](#-how-to-use-this-repo)
- [Author & Connect](#-author--connect)

---

## 📖 About

A complete, hands-on Linux operations study guide built for engineers preparing for **RHCSA (EX200)** and **RHCE (EX294)** — and anyone building production-grade Linux skills for cloud, DevOps, or AI/MLOps infrastructure roles.

All commands tested on **RHEL 9** / **Rocky Linux**.

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
|---|---|
| 🌐 [accessing-your-linux-system](https://github.com/kelvintechnical/accessing-your-linux-system) | Console access, SSH, PuTTY, AWS EC2 |
| 🗂 [managing-linux-files-cli](https://github.com/kelvintechnical/managing-linux-files-cli) | File system, file management, links, I/O redirection, pipes |

> 💡 **Start here if you're new to Linux** — these repos build the foundation before diving into RHCSA-level material.

---

## 🗺️ Certification Path

| Phase | Certification | Exam | Status |
|---|---|---|---|
| Foundation | CompTIA Linux+ | XK0-005 | ✅ Complete |
| Intermediate | RHCSA | EX200 | 🔄 In Progress |
| Advanced | RHCE (Ansible) | EX294 | 🔜 Planned |

---

## 📂 Modules

| # | Module | Focus |
|---|---|---|
| 01 | [System Management](./01-system-management/README.md) | Users, storage, boot, SELinux, networking |
| 02 | [Networking](./02-networking/README.md) | firewalld, SSH, advanced routing |
| 03 | [Containers](./03-containers/README.md) | Podman, systemd services, rootless containers |
| 04 | [Automation](./04-automation) | Ansible playbooks, roles, inventories (RHCE core) |
| 05 | [Labs Archive](./05-labs) | Exam-style scenario labs |

---

## 🧪 Labs

| # | Lab | Topic | Exam |
|---|---|---|---|
| 01 | [Configure a Static IP Address](./01-system-management/README.md#lab-01--configure-a-static-ip-address) | nmcli, DNS, hostname, persistence | RHCSA EX200 |
| 02 | [Configure Repository Access](https://github.com/kelvintechnical/Configure-Repository-Access-) | dnf, BaseOS, AppStream, .repo files | RHCSA EX200 |

*New labs added as I work through the cert objectives.*

---

## 📋 RHCSA Exam Coverage

| Domain | Module |
|---|---|
| Essential tools & file management | [01](./01-system-management/README.md) |
| Local storage & filesystems | [01](./01-system-management/README.md) |
| Deploy, configure, maintain systems | [01](./01-system-management/README.md) |
| Manage networking | [01](./01-system-management/README.md) / [02](./02-networking/README.md) |
| Manage security (SELinux, firewalld) | [02](./02-networking/README.md) |
| Manage containers | [03](./03-containers/README.md) |

---

## 🧭 How to Use This Repo

1. **New to Linux?** Start with the [companion repos](#-companion-repos) above
2. **Ready for RHCSA?** Pick a lab from the [Labs](#-labs) table
3. **Practice in a VM** — RHEL 9 or Rocky Linux (setup in [Module 01](./01-system-management/README.md#-environment-setup))
4. **Follow the modules** in order, or jump to the exam domain you need

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
