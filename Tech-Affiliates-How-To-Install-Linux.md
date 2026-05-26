# Tech Affiliates — How to Install Linux

### A Beginner-Friendly Install Guide for Windows and Mac

**A Tech Affiliates community resource · Eastern NC**

![Audience](https://img.shields.io/badge/Audience-Middle%20School%20%E2%86%92%20Adult-blue?style=flat)
![Level](https://img.shields.io/badge/Level-Absolute%20Beginner-success?style=flat)
![Time](https://img.shields.io/badge/Time-15%E2%80%9360%20minutes-orange?style=flat)
![Cost](https://img.shields.io/badge/Cost-%240-success?style=flat)

---

## 📖 About This Guide

This guide takes you from **"I have a laptop and I want to learn Linux"** to **"I have Linux running and I'm ready to start Week 1"** — even if you have never opened a terminal in your life.

It is written so a curious **12-year-old** can follow it and so a **45-year-old** changing careers can follow it. We do not assume you know what an "ISO" is, what a "kernel" is, or what "boot" means. Every term gets defined the first time we use it.

If you get stuck on any step, **stop and ask in the Tech Affiliates group chat**. Nobody learns Linux alone.

---

## 🔗 Related Repos

This install guide is part of a larger Tech Affiliates learning stack. Once Linux is running on your laptop, jump into:

| Repo | What it's for |
| --- | --- |
| 🐧 **[linux-ops-mastery](https://github.com/kelvintechnical/linux-ops-mastery)** | The main repo — 212+ hands-on labs covering CompTIA Linux+, RHCSA, RHCE, and CKA. This is your home base. |
| 🎓 **[Tech-Affiliates-Comptia-Linux-Preparation](https://github.com/kelvintechnical/Tech-Affiliates-Comptia-Linux-Preparation)** | The companion 8-week CompTIA Linux+ course built by the Tech Affiliates community in Eastern NC. |
| 📘 **[Tech-Affiliates-Comptia-Linux-Plus-Preparation (course outline)](https://github.com/kelvintechnical/Tech-Affiliates-Comptia-Linux-Preparation)** | The week-by-week schedule that lives inside this repo. Open this after you finish installing Linux. |

> 🧭 **TL;DR:** finish this install guide → open the **[Linux+ course outline](https://github.com/kelvintechnical/Tech-Affiliates-Comptia-Linux-Preparation)** → start working through the labs in **[linux-ops-mastery](https://github.com/kelvintechnical/linux-ops-mastery)**.

---

## 📚 Table of Contents

- [Related Repos](#-related-repos)
- [What Is Linux (in plain English)](#-what-is-linux-in-plain-english)
- [Key Terms You Need to Know First](#-key-terms-you-need-to-know-first)
  - [What is a Virtual Machine (VM)?](#what-is-a-virtual-machine-vm)
  - [What is WSL?](#what-is-wsl)
  - [What is a Linux Distribution (Distro)?](#what-is-a-linux-distribution-distro)
  - [What is Dual Boot?](#what-is-dual-boot)
  - [What is an ISO File?](#what-is-an-iso-file)
- [Which Method Should I Pick?](#-which-method-should-i-pick)
- [What You Need Before You Start](#-what-you-need-before-you-start)
- [Method 1 — Install WSL on Windows (Easiest)](#-method-1--install-wsl-on-windows-easiest)
- [Method 2 — Install Linux in a Virtual Machine on Windows](#-method-2--install-linux-in-a-virtual-machine-on-windows)
- [Method 3 — Install Linux on a Mac (Intel)](#-method-3--install-linux-on-a-mac-intel)
- [Method 4 — Install Linux on a Mac (Apple Silicon M1 / M2 / M3 / M4)](#-method-4--install-linux-on-a-mac-apple-silicon-m1--m2--m3--m4)
- [Method 5 — Dual Boot (Advanced — Optional)](#-method-5--dual-boot-advanced--optional)
- [Verify Your Install (Do This Every Time)](#-verify-your-install-do-this-every-time)
- [Troubleshooting](#-troubleshooting)
- [Frequently Asked Questions](#-frequently-asked-questions)
- [What's Next](#-whats-next)

---

## 🐧 What Is Linux (in plain English)

**Linux is an operating system.** An operating system is the software that runs your computer — it's the same kind of thing as Windows or macOS. The big difference is:

- **Windows** was made by Microsoft and you pay for it.
- **macOS** was made by Apple and only runs on Apple computers.
- **Linux** is free, open, and runs on almost any computer in the world — from a $35 Raspberry Pi to the world's biggest supercomputers.

**Why care?**

- Over **96%** of the world's top web servers run Linux.
- **Every** Android phone runs a Linux core.
- **All** of the world's top 500 supercomputers run Linux.
- Companies like Google, Netflix, Amazon, Meta, Tesla, and NASA all run Linux to power their products.

If you learn Linux, you learn the language the modern internet speaks. That's why this course exists.

---

## 🔑 Key Terms You Need to Know First

Read these once. You can come back to them anytime.

### What is a Virtual Machine (VM)?

A **virtual machine** is a computer **inside** your computer.

Picture this: you have a laptop running Windows. You install a free program (like VirtualBox or UTM). That program creates a fake computer inside a window — like a video game character of a computer. You can install Linux inside that fake computer. When you're done for the day, you close the window and your real computer is exactly how you left it.

**Pros of a VM**
- Safe — if you break it, you delete it and start over. Your real computer is fine.
- You can have many VMs (one Ubuntu, one Rocky Linux, one Kali, etc.).
- Easy to follow tutorials because the VM is a clean environment.

**Cons of a VM**
- Uses more memory (RAM) than WSL because you are running two operating systems at once.
- Slightly slower than a real install.
- Needs at least **8 GB of RAM** to feel smooth.

> **Plain language:** a VM is like running Linux on a TV inside your Windows or Mac.

---

### What is WSL?

**WSL** stands for **Windows Subsystem for Linux**. It is a feature **built into Windows 10 and Windows 11** by Microsoft that lets you run Linux **directly** inside Windows — no virtual machine needed, no dual boot needed.

When you install WSL, you get a real Linux terminal that lives inside your Windows computer. You can use Linux commands and Windows at the same time, side by side.

**Pros of WSL**
- The **easiest** way to get Linux on a Windows computer.
- Installs in about 10 minutes.
- Uses very little memory.
- Microsoft maintains it, so it gets updates automatically.
- Perfect for Tech Affiliates students starting out.

**Cons of WSL**
- Only works on Windows (not Mac).
- A few advanced topics in this course (deep networking and some kernel tools) work better in a real VM, but **everything we cover in Weeks 1–6 works perfectly in WSL**.

> **Plain language:** WSL is the official Microsoft shortcut for running Linux inside Windows. It is our recommended starting point for every Windows user in this course.

---

### What is a Linux Distribution (Distro)?

Linux comes in many flavors called **distributions**, or "distros" for short. They are all Linux at the core, but they look slightly different and use different tools.

The two distros we use in this course are:

| Distro | Why we use it | Used by |
| --- | --- | --- |
| **Ubuntu** | Friendly for beginners, huge community, easy installer | Most cloud servers, AWS, NASA, Tesla |
| **Rocky Linux** | A free version of Red Hat Linux | Banks, hospitals, government, defense |

> If this is your very first time, **start with Ubuntu**. You can add Rocky Linux later in Week 4.

---

### What is Dual Boot?

**Dual boot** means installing **two operating systems on the same computer** — for example, Windows AND Ubuntu — and choosing which one to start when you turn the computer on.

It gives you the fastest, most "real" Linux experience because Linux runs directly on your hardware. But it is also the **riskiest** option for beginners because if you make a mistake, you can lose your Windows files.

> For this course, we **do not recommend** dual boot for your first install. Use WSL or a VM first. Try dual boot later, after you understand partitions.

---

### What is an ISO File?

An **ISO file** is a single file that contains an entire DVD or installer inside it. When you download Linux, you download an `.iso` file. You then either:

- Attach it to a virtual machine (the VM treats it like a DVD in a DVD drive), or
- "Burn" it to a USB stick to install Linux on a real computer.

For the VM methods below, you do **not** need a USB stick — you just point the VM at the ISO file.

---

## 🧭 Which Method Should I Pick?

Use this chart to pick your path. Most students should pick the green box.

| I have a... | I should use... | Difficulty |
| --- | --- | --- |
| Windows 10 or 11 laptop | ✅ **Method 1 — WSL** | Easy (recommended) |
| Windows laptop, want a full Linux desktop | Method 2 — VirtualBox VM | Medium |
| Intel Mac (made 2019 or earlier) | Method 3 — VirtualBox VM | Medium |
| Apple Silicon Mac (M1 / M2 / M3 / M4) | Method 4 — UTM or Multipass | Medium |
| Old laptop you don't care about | Method 5 — Dual boot | Hard |

> Not sure if your Mac is Intel or Apple Silicon? Click the Apple logo (top-left) → **About This Mac**. If it says **"Chip: Apple M1"** (or M2, M3, M4) you have Apple Silicon. If it says **"Processor: Intel"** you have Intel.

---

## ✅ What You Need Before You Start

- A laptop or desktop with at least **8 GB of RAM** (16 GB is better, but 8 GB works).
- **20 GB of free disk space** (50 GB if you want both Ubuntu and Rocky later).
- A stable Wi-Fi or Ethernet connection — the downloads are 1 GB to 5 GB.
- **A charger plugged in.** Do not start an install on battery. Ever.
- **About 1 hour** of uninterrupted time for your first install.
- (Optional) A second device (phone is fine) to keep this guide open while you install.

> ⚠️ **Back up anything important first.** None of these methods *should* erase your files, but computers are computers. If a photo, paper, or project would ruin your week to lose, copy it to Google Drive, iCloud, or a USB stick before you start.

---

## 🪟 Method 1 — Install WSL on Windows (Easiest)

**What you get:** A real Ubuntu Linux terminal inside Windows.
**Time:** ~10 minutes (plus ~10 minutes for the first Windows reboot)
**Skill level:** Beginner

### Step 1 — Open PowerShell as Administrator

1. Click the **Start** button (Windows logo, bottom-left).
2. Type `powershell`.
3. **Right-click** the "Windows PowerShell" result.
4. Click **"Run as administrator"**.
5. A blue window opens. If Windows asks "Do you want to allow this app to make changes?" click **Yes**.

> "Administrator" mode is just Windows asking, "Are you sure you want to change the system?" Yes, we're sure.

### Step 2 — Run the One-Line Install

In the blue PowerShell window, type exactly this and press **Enter**:

```powershell
wsl --install
```

That single command:
1. Turns on the Windows feature that allows Linux.
2. Downloads Ubuntu (the default distro).
3. Sets everything up for you.

You'll see a bunch of text scroll by. This is normal. Wait until it finishes (about 5–10 minutes).

### Step 3 — Reboot Your Computer

When PowerShell tells you to restart, **save anything you have open** and restart your PC normally.

### Step 4 — Finish Ubuntu Setup

After your computer restarts, a black window labeled **"Ubuntu"** opens automatically.

It asks you two things:

1. **"Enter new UNIX username:"** — Type a simple lowercase name like `kelvin` or `student`. No spaces, no capitals. Press Enter.
2. **"New password:"** — Type a password. **You will not see the characters as you type — this is normal in Linux, it's a security feature.** Press Enter. Type it again to confirm.

> Write your password down. Linux will not show it on screen ever again. If you forget it, you'll have to reset Ubuntu.

### Step 5 — Update Ubuntu

You are now in Linux. Type this command and press Enter:

```bash
sudo apt update && sudo apt upgrade -y
```

Ubuntu will ask for your password (the one you just made). Type it, press Enter, and wait. This downloads the latest security patches.

### Step 6 — Confirm It Worked

Type these three commands one at a time:

```bash
whoami
pwd
lsb_release -a
```

If you see your username, a path like `/home/kelvin`, and a line that says `Description: Ubuntu 24.04 LTS` (or similar) — **you did it. You have Linux on your Windows machine.**

### Step 7 — How to Open It Next Time

From now on, just click **Start** and type `Ubuntu`. The terminal opens instantly.

> 🎉 You're done with Method 1. Skip to ["Verify Your Install"](#-verify-your-install-do-this-every-time).

---

## 💻 Method 2 — Install Linux in a Virtual Machine on Windows

**What you get:** A full Ubuntu desktop in a window on top of Windows.
**Time:** ~45–60 minutes
**Skill level:** Beginner — Intermediate

### Step 1 — Download VirtualBox

VirtualBox is a free program made by Oracle that runs virtual machines.

1. Go to **https://www.virtualbox.org/wiki/Downloads**
2. Click **"Windows hosts"** to download the installer.
3. Open the file you downloaded and click **Next → Next → Install → Finish** (default settings are fine).

### Step 2 — Download the Ubuntu ISO

1. Go to **https://ubuntu.com/download/desktop**
2. Click the green **Download** button for the latest **LTS** version.
   - **LTS** means "Long Term Support" — it gets security updates for 5 years. Always pick LTS.
3. The download is about 5 GB. It may take 10–30 minutes depending on your internet.
4. Save the `.iso` file somewhere you can find it, like your `Downloads` folder.

### Step 3 — Create a New Virtual Machine

1. Open **VirtualBox** (the program you just installed).
2. Click the blue **"New"** button.
3. Fill in:
   - **Name:** `Ubuntu-Lab`
   - **ISO Image:** click the dropdown → **Other...** → pick the Ubuntu ISO file you downloaded
   - Check the box **"Skip Unattended Installation"** (we want to do it manually so you learn)
4. Click **Next**.

### Step 4 — Give the VM Resources

VirtualBox will ask how much of your computer to give the VM:

- **Base Memory (RAM):** drag to **4096 MB** (4 GB). If your computer has 16 GB or more, you can give it 8192 MB (8 GB).
- **Processors:** **2**.
- Click **Next**.

> Rule of thumb: never give a VM more than **half** of your computer's RAM, or your real computer will freeze.

### Step 5 — Create the Virtual Hard Disk

- **Virtual hard disk size:** drag to **25 GB**.
- Leave the rest at default.
- Click **Next**, then **Finish**.

### Step 6 — Start the VM and Install Ubuntu

1. Click your new VM in the left sidebar.
2. Click the green **"Start"** arrow at the top.
3. A new window opens — this is the fake computer "turning on".
4. You'll see a purple Ubuntu screen. Click **"Try or Install Ubuntu"**.
5. Click **"Install Ubuntu"**.
6. Follow the prompts:
   - **Keyboard layout:** English (US) — Continue
   - **Updates:** "Normal installation" — Continue
   - **Installation type:** "Erase disk and install Ubuntu" — **this only erases the fake VM disk, not your real Windows files** — Continue
   - **Where are you?** pick your city — Continue
   - **Who are you?**
     - Your name: your real name
     - Computer name: `ubuntu-lab`
     - Username: a simple lowercase name
     - Password: pick a password and write it down
   - Click **Continue**.

7. Wait 10–20 minutes for the install to finish.
8. Click **Restart Now**. If it says "Please remove the installation medium", just press **Enter**.

### Step 7 — First Login

The VM reboots into your shiny new Ubuntu desktop. Log in with the password you just made.

### Step 8 — Update Ubuntu

Open the terminal inside Ubuntu (search for "Terminal" in the dock, or press `Ctrl + Alt + T`) and run:

```bash
sudo apt update && sudo apt upgrade -y
```

> 🎉 You're done with Method 2. Skip to ["Verify Your Install"](#-verify-your-install-do-this-every-time).

---

## 🍎 Method 3 — Install Linux on a Mac (Intel)

**What you get:** A full Ubuntu desktop in a window on top of macOS.
**Time:** ~45–60 minutes
**Skill level:** Beginner — Intermediate

> Apple Silicon (M1/M2/M3/M4) Macs **cannot** use VirtualBox reliably. If you have one of those, **skip to Method 4**.

### Step 1 — Download VirtualBox for macOS

1. Go to **https://www.virtualbox.org/wiki/Downloads**
2. Click **"macOS / Intel hosts"**.
3. Open the `.dmg` file and follow the on-screen installer.
4. If macOS blocks the install with a security warning:
   - Open **System Settings → Privacy & Security**
   - Scroll down and click **"Allow"** next to the Oracle message
   - Re-run the installer

### Step 2 — Download the Ubuntu ISO

Same as Method 2, Step 2: **https://ubuntu.com/download/desktop**

### Step 3 → Step 8

The steps inside VirtualBox are **identical to Method 2, Steps 3–8** above. Follow them exactly.

> 🎉 You're done with Method 3. Skip to ["Verify Your Install"](#-verify-your-install-do-this-every-time).

---

## 🍏 Method 4 — Install Linux on a Mac (Apple Silicon M1 / M2 / M3 / M4)

**What you get:** A full Ubuntu desktop in a window on top of macOS.
**Time:** ~45–60 minutes
**Skill level:** Beginner — Intermediate

Apple Silicon Macs use a different chip (ARM, not Intel), so VirtualBox does not work well. We use **UTM** instead — it's free, made for Apple Silicon, and easy.

### Step 1 — Download UTM

1. Go to **https://mac.getutm.app/**
2. Click **"Download"** (the free version is fine — the App Store version costs $10 and is the same product, just used to support the developer).
3. Drag UTM into your **Applications** folder.

### Step 2 — Download the Ubuntu ARM ISO

Apple Silicon Macs need the **ARM** version of Ubuntu, not the regular one.

1. Go to **https://cdimage.ubuntu.com/releases/**
2. Click the newest LTS folder (for example `24.04`).
3. Click **release/**
4. Download the file ending in **`-live-server-arm64.iso`** (about 2.5 GB).

> If you want a desktop instead of just a server, go to **https://ubuntu.com/download/desktop** and look for the **"For Apple Silicon"** link near the bottom.

### Step 3 — Create a New VM in UTM

1. Open **UTM**.
2. Click **"Create a New Virtual Machine"**.
3. Click **"Virtualize"** (NOT "Emulate" — virtualize is much faster).
4. Click **"Linux"**.
5. Check **"Use Apple Virtualization"** for best speed.
6. Under **Boot ISO Image**, click **Browse** and pick the Ubuntu ARM ISO you downloaded.
7. Click **Continue**.

### Step 4 — Give the VM Resources

- **Memory:** 4096 MB
- **CPU Cores:** 2
- **Storage:** 25 GB
- Click **Continue → Continue → Save**.

### Step 5 — Start and Install

1. Click the **▶ Play** button.
2. The Ubuntu installer starts. Follow the same prompts as Method 2, Step 6.
3. When install finishes, **shut the VM down**, then in UTM click the VM → **Edit (the slider icon) → Drives → remove the CD/DVD drive** so it doesn't try to reinstall every boot.
4. Start the VM again and log in.

### (Easy Alternative for Apple Silicon) Multipass — Terminal-Only Ubuntu

If you don't need a graphical desktop and just want a terminal, install **Multipass** instead — it's the simplest way to get Ubuntu on a Mac.

1. Go to **https://multipass.run/**
2. Click **Download for macOS** and run the installer.
3. Open **Terminal** (search Spotlight for it).
4. Run:

   ```bash
   multipass launch --name lab
   multipass shell lab
   ```

You are now inside Ubuntu. Type `exit` to go back to macOS. To reopen later, run `multipass shell lab`.

> 🎉 You're done with Method 4. Skip to ["Verify Your Install"](#-verify-your-install-do-this-every-time).

---

## ⚠️ Method 5 — Dual Boot (Advanced — Optional)

**What you get:** Linux runs directly on your hardware (fastest possible Linux).
**Time:** ~1.5–2 hours
**Skill level:** Advanced — **do not pick this as your first install**

Dual boot means installing Linux **next to** Windows on the same hard drive and choosing which OS to load when you power on the computer.

> 🚨 **Warning:** dual boot involves resizing your hard drive partitions. If you make a mistake, you can lose Windows. Only attempt this after you've completed at least 2 weeks of the course **and** you have a full backup of every file you care about.

We will publish a dedicated dual-boot walkthrough in a separate lab when the course reaches Module 6 (Storage and LVM). For now, **use WSL or a VM**.

---

## 🔍 Verify Your Install (Do This Every Time)

No matter which method you used, open the Linux terminal and run these five commands one at a time. If they all work, you are ready for Week 1.

```bash
whoami
```
Should print your Linux username.

```bash
pwd
```
Should print something like `/home/yourname` — this is your home directory.

```bash
uname -a
```
Tells you the kernel (the heart of Linux) version. You should see the word `Linux` and a version number.

```bash
cat /etc/os-release
```
Should print details like `Ubuntu 24.04 LTS` or `Rocky Linux 9`. This confirms which distro you have.

```bash
sudo apt update
```
(Use `sudo dnf check-update` instead if you installed Rocky Linux.) This pulls the latest software list. If it runs without an error, your internet works inside Linux.

✅ All five worked? **Congratulations — you officially have Linux.** Take a screenshot. Post it in the Tech Affiliates group. You earned it.

---

## 🛠️ Troubleshooting

| Problem | Try this |
| --- | --- |
| `wsl --install` says "command not found" | You're on an old version of Windows. Run **Windows Update** until you're on Windows 10 build 2004 or newer, then try again. |
| WSL Ubuntu won't open after install | Open PowerShell (Admin) and run `wsl --shutdown`, then try opening Ubuntu again. |
| VirtualBox won't start a VM ("VT-x not enabled") | Restart your computer, press the BIOS key (F2, F10, or Del) on startup, find a setting called **Intel VT-x**, **AMD-V**, or **Virtualization**, and turn it **on**. Save and reboot. |
| Mac says "VirtualBox can't be opened because Apple cannot check it" | Go to **System Settings → Privacy & Security**, scroll down, click **Allow Anyway**, then reopen the installer. |
| VM is super slow | You probably gave it too little RAM. Shut it down, edit settings, raise RAM to 4096 MB or higher, and start it again. |
| I forgot my Linux password | In WSL: open PowerShell and run `wsl -u root passwd yourname`. In a VM: easier to delete and reinstall — that's why we use VMs. |
| Black screen after installing in VirtualBox | The CD/DVD is still attached. Shut down the VM, go to **Settings → Storage**, remove the ISO, then start again. |
| "Could not connect to the internet" inside the VM | Inside VirtualBox: VM **Settings → Network → Attached to: NAT**. Inside UTM: **Network → Shared Network**. |
| Apple Silicon Mac shows VirtualBox crashing | VirtualBox is unreliable on M1/M2/M3/M4. Use **Method 4 (UTM or Multipass)** instead. |

Still stuck? Drop a screenshot in the Tech Affiliates group chat. We help each other.

---

## ❓ Frequently Asked Questions

**Q: Will this delete Windows / macOS from my computer?**
No. Methods 1–4 leave your main operating system completely untouched. Only Method 5 (Dual Boot) changes your real hard drive — and we recommend you skip that for now.

**Q: How much will this cost me?**
$0. Ubuntu, Rocky Linux, WSL, VirtualBox, UTM, and Multipass are all 100% free.

**Q: I'm in middle school. Is this safe?**
Yes — installing Linux in a VM or in WSL is one of the safest ways to learn computing. Your parents' computer stays exactly the same. If you break the VM, you delete it and start over. Nothing on the real computer changes.

**Q: My laptop only has 4 GB of RAM. Can I still do this?**
Yes — use **WSL (Method 1)** if you're on Windows. WSL is much lighter than a VM. If you're on a Mac with 4 GB, use **Multipass** (in Method 4).

**Q: Do I need to know how to code already?**
No. We start from `whoami` and build up. Most students have never opened a terminal before Week 1.

**Q: Will this slow my computer down forever?**
No. A VM only uses RAM while it's running. Close the VM window and your computer is back to normal. WSL is even lighter — it sits idle until you open it.

**Q: Can I use a Chromebook?**
Yes. Most modern Chromebooks support **Linux (Beta)** in their settings — go to **Settings → Advanced → Developers → Turn on Linux development environment**. You'll get an Ubuntu-like terminal natively. Skip the WSL/VM steps entirely.

**Q: Why does the password not show when I type it?**
That's a Linux security feature. Anyone looking at your screen can't even count the characters. Just type it and press Enter.

**Q: Ubuntu or Rocky — which should I install first?**
**Ubuntu.** It's the friendliest. We use it for Weeks 1–3. We introduce Rocky in Week 4 once you're comfortable.

**Q: Can I uninstall it later if I don't like it?**
Yes, easily:
- **WSL:** Open Settings → Apps → search "Ubuntu" → Uninstall.
- **VM:** Open VirtualBox or UTM → right-click the VM → Remove → Delete All Files.

**Q: Do I need a fast internet connection?**
You need internet for the **download** (1–5 GB). After that, Linux runs offline just fine.

---

## 🚀 What's Next

Once your `whoami` and `pwd` commands work, you are ready to start the course.

1. ⭐ Star the main repo: **[linux-ops-mastery](https://github.com/kelvintechnical/linux-ops-mastery)** — this is where all 212+ labs live.
2. ⭐ Star the course repo: **[Tech-Affiliates-Comptia-Linux-Preparation](https://github.com/kelvintechnical/Tech-Affiliates-Comptia-Linux-Preparation)** — the 8-week CompTIA Linux+ workforce-ready course.
3. 📅 Open the course outline: **[Tech-Affiliates-Comptia-Linux-Preparation](https://github.com/kelvintechnical/Tech-Affiliates-Comptia-Linux-Preparation)**.
4. ✏️ Begin **Week 1 — Welcome, Linux, and Your First Terminal**.

You did the hardest part: you got Linux running. Everything from here on out is just typing commands and learning what they do.

Welcome to Linux. Welcome to the rest of your career.

---

## 👤 Guide Author

**Kelvin R. Tobias**
AI Engineer · Founder, Kelvinintech Consulting LLC & Tech Affiliates · Eastern NC

- B.S. Software Engineering, Western Governors University (3× Excellence Award)
- M.S. AI Engineering, Western Governors University (Starting Dec 2026)
- **Active Certifications:** CompTIA Linux+, CompTIA Security+, AWS Cloud Practitioner, ITIL 4 Foundation
- **In Progress:** RHCSA → RHCE (Red Hat Certified Engineer path)

[Website](https://kelvinintech.com/) · [Hashnode](https://hashnode.com/@kelvintechnical) · [Substack](https://kelvinintech.substack.com/) · [LinkedIn](https://www.linkedin.com/in/kelvinrtobias) · [GitHub](https://github.com/kelvintechnical)

---

📧 kelvinrtobias@gmail.com
📞 (980) 800-6776

**⭐ Star [linux-ops-mastery](https://github.com/kelvintechnical/linux-ops-mastery) if this guide helped you get started.**

*A Tech Affiliates community resource · Eastern NC*
