# Security Policy

## 🛡️ Our Commitment
This project is a local macOS dashboard that categorizes your network
activity using DNS query data. We take security seriously because the
app runs with elevated privileges and observes sensitive traffic
metadata. We review reports promptly, provide clear guidance to
reporters, and prioritize fixes that reduce user risk while keeping the
tool stable and accessible.

## 🚩 Reporting a Vulnerability

**If you discover a vulnerability**, please use the "Report a 
vulnerability" button under [Security][security] on this repo's GitHub page.

## 💡 Best Practices for Contributors
- **No Secrets**: Never commit personal information, API keys, or passwords to 
  the repository.
- **Dependency Awareness**: Be cautious when adding new third-party libraries. 
  Stick to well-known packages and keep them updated.
- **Sanitize Input**: If you add a method that takes user input, ensure it 
  doesn't execute unintended code.

## 🛠️ Security Tools
We use GitHub Dependabot to automatically monitor and update our dependencies 
for known vulnerabilities.

[security]: https://github.com/Leto-cmd/PNTCD-macOS/security
