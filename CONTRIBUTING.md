<div align="center">

# 🤝 Contributing to Linux Ops Mastery

### A Beginner-Friendly Guide for First-Time Contributors

![Contributors Welcome](https://img.shields.io/badge/Contributors-Welcome-success?style=flat)
![First-Timer Friendly](https://img.shields.io/badge/First--Timer-Friendly-blue?style=flat)
![Tech Affiliates](https://img.shields.io/badge/Tech%20Affiliates-Community-purple?style=flat)
![License](https://img.shields.io/badge/License-Free%20Public%20Resource-success?style=flat)

</div>

---

## 📚 Table of Contents

- [About This Project](#-about-this-project)
- [Who Can Contribute](#-who-can-contribute)
- [Ways to Contribute](#-ways-to-contribute)
- [How to Submit a Change](#-how-to-submit-a-change)
- [Contribution Standards](#-contribution-standards)
- [Reporting Issues](#-reporting-issues)
- [Contact](#-contact)

---

## 📖 About This Project

This repo is maintained by **Kelvin R. Tobias** through **Kelvinintech Consulting LLC** and **Tech Affiliates**, a STEM outreach community serving Eastern North Carolina and beyond.

Everything in this project is a free public resource. There is no paywall, no subscription, no catch. The goal is simple: help as many people as possible get into Linux and IT careers without going broke and without going back to school for four years.

If this repo helped you, contributing back is one of the best ways to pay it forward.

---

## 👥 Who Can Contribute

Anyone. Seriously, anyone. Specifically:

- 🧑‍🤝‍🧑 **Tech Affiliates community members** who have worked through any part of the course.
- 🎒 **Students and learners in Eastern NC** taking the workforce track.
- 🔎 **Anyone who used a guide here and found something unclear**, broken, or missing.
- 🌱 **First-time open source contributors** who have never submitted a pull request before.

You do not need a Computer Science degree. You do not need years of experience. You do not need to be a "developer". If you spotted a typo on page 3, you can fix it. That counts.

> 💡 If you have never contributed to an open source project before, this is a great first repo. We will help you through it.

---

## 🛠 Ways to Contribute

Pick whatever fits your skill level:

| Type | What it looks like | Skill level |
| --- | --- | --- |
| 🔤 **Fix a typo** | You see "thier" instead of "their". Fix it. | Beginner |
| 🔗 **Fix a broken link** | A link 404s or points to the wrong page. Update it. | Beginner |
| ✍️ **Improve step wording** | A step in the install guide confused you. Rewrite it clearer. | Beginner |
| 🐛 **Add a troubleshooting entry** | You hit an error not listed in the troubleshooting table. Add it with the fix. | Beginner / Intermediate |
| 🌎 **Translate to Spanish** | ⭐ **HIGH PRIORITY.** Spanish translations of any guide are extremely valuable for our Eastern NC audience. | Intermediate |
| 📸 **Submit screenshots** | Some learners are visual. Annotated screenshots of installer dialogs or commands help a lot. | Beginner |
| 🧪 **Propose a new lab** | Have an idea for a hands-on exercise that fits the curriculum? Open an Issue first to discuss. | Advanced |

> ✨ **Spanish translation contributors:** open an Issue first so we can coordinate which file you are translating. We do not want two people translating the same page at the same time.

---

## 🚀 How to Submit a Change

Never made a pull request before? Read this carefully. We walk through every click.

### Step 1: Fork the Repo

A "fork" is your own copy of the project. You can change anything in your copy without affecting the real repo.

1. Go to **https://github.com/kelvintechnical/linux-ops-mastery**
2. Click the **Fork** button (top-right of the page).
3. Click **Create fork**. GitHub copies the repo to your account.

You now have a copy at `https://github.com/YOUR-USERNAME/linux-ops-mastery`.

### Step 2: Edit the File

You have two options. Pick whichever feels easier.

**Option A: Edit directly on GitHub (easiest for small changes)**

1. In your fork, click the file you want to change.
2. Click the pencil icon (top-right of the file).
3. Make your edit.
4. Scroll down to **Commit changes**.
5. Write a short message describing what you changed (example: "Fix typo in WSL section").
6. Click **Commit changes**.

**Option B: Clone, edit locally, and push (best for bigger changes)**

1. Open a terminal on your computer.
2. Run:

   ```bash
   git clone https://github.com/YOUR-USERNAME/linux-ops-mastery.git
   cd linux-ops-mastery
   ```

3. Edit the file in any text editor (VS Code, nano, vim, Notepad++, whatever you like).
4. Save your change. Then run:

   ```bash
   git add .
   git commit -m "Fix typo in WSL section"
   git push
   ```

### Step 3: Open a Pull Request

A "pull request" (often shortened to PR) is you asking the maintainer to pull your change into the real repo.

1. Go to your fork on GitHub.
2. You will see a banner saying "This branch is X commits ahead of kelvintechnical/main". Click **Contribute**, then **Open pull request**.
3. Give the PR a clear title (example: "Fix typo on line 47 of install guide").
4. In the description box, briefly explain:
   - What you changed
   - Why you changed it
   - What device or OS you tested on, if relevant
5. Click **Create pull request**.

### Step 4: What Happens Next

1. Kelvin (the maintainer) gets a notification.
2. He reviews the change, usually within a few days.
3. If anything needs adjusting, he leaves a comment. Reply to the comment, push the fix to the same branch, and the PR updates automatically.
4. Once approved, your change gets merged into the main repo.
5. Your GitHub profile now shows you as a contributor to a public open source project. That is real proof of work you can put on a resume.

---

## ✅ Contribution Standards

A few ground rules to keep the repo readable and consistent:

1. **Match the existing tone.** Plain language. Friendly. Assume the reader has never opened a terminal before. Write like you are explaining the step to a curious 12 year old.
2. **Test commands before submitting.** If your change includes a command, actually run it on the operating system it targets. Do not paste in untested commands.
3. **One change per pull request.** Do not bundle a typo fix, a new troubleshooting entry, and a screenshot into one PR. Submit them separately so each one can be reviewed cleanly.
4. **Use clear commit messages.** "Fix WSL step 2 typo" is good. "update" is not.
5. **Be careful with AI tools.** Using ChatGPT, Claude, or any AI assistant to draft text is fine, but read every line carefully and rewrite anything that sounds generic, hallucinated, or off-tone before you submit.
6. **Be kind in reviews.** This community is built for learners. Phrase feedback the way you would want to hear it.

---

## 🐛 Reporting Issues

If something is broken but you are not ready to fix it yourself, open an Issue. Issues are how we track bugs and ideas.

1. Go to **https://github.com/kelvintechnical/linux-ops-mastery/issues**
2. Click **New issue**.
3. Fill in all five of these fields:
   - **Title:** a one-line summary (example: "WSL install command fails on Windows 10 build 1909").
   - **Operating System:** Windows 10, Windows 11, macOS Intel, macOS Apple Silicon, or which Linux distro and version.
   - **Install method used:** WSL, VirtualBox, UTM, Multipass, or dual boot.
   - **Exact error message:** copy and paste the full text. Screenshots help too.
   - **What you already tried:** what fixes did you attempt before reporting?

Filling all five fields gets your Issue resolved much faster.

---

## 📬 Contact

For anything that does not fit into a GitHub Issue or pull request:

- 🏢 **Kelvinintech Consulting LLC**
- 📧 Email: **kelvinrtobias@gmail.com**
- 🌐 Website: **[kelvinintech.com](https://kelvinintech.com/)**

For Tech Affiliates community questions (course access, mentorship, partnerships, employer engagement), reach out through the same email.

---

<div align="center">

**⭐ Thanks for helping make Linux education accessible.**

*Part of the Tech Affiliates community. Built in Eastern NC. Open to everyone.*

</div>
