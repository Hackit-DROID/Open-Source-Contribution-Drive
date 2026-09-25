# Contributing to HackIT Commit Rush 🚀

Thank you for participating in **HackIT Commit Rush** — the open-source contribution drive organized by **HackIT SGGSIE&T**!

Follow these guidelines to ensure smooth code contributions and pull request reviews.

---

## 📌 Submission Guidelines

1. **Clean Code**: Ensure your Python code follows PEP 8 standards. Keep functions modular and clean.
2. **Secrets Security**:
   - **NEVER** commit API keys, database passwords, or personal credentials into source code.
   - Use `os.getenv("VARIABLE_NAME")` along with `python-dotenv`.
   - Place credentials inside `.env` (which is ignored by Git).
3. **No Redundant Files**:
   - Do not commit virtual environments (`venv`, `env`, `.venv`), `__pycache__`, or `.DS_Store` files.

---

## 🛠️ Step-by-Step Contribution Process

1. **Fork this repository** to your GitHub account.
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Open-Source-Contribution-Drive.git
   cd Open-Source-Contribution-Drive
   ```
3. **Create a new branch**:
   ```bash
   git checkout -b feature/short-description
   ```
4. **Make your changes** and test locally.
5. **Commit your changes**:
   ```bash
   git commit -m "feat: Add brief description of feature"
   ```
6. **Push to your fork**:
   ```bash
   git push origin feature/short-description
   ```
7. **Submit a Pull Request (PR)**:
   - Go to `Hackit-DROID/Open-Source-Contribution-Drive` on GitHub.
   - Click **New Pull Request**.
   - Fill out the PR template describing your changes.

---

## ❓ Need Help?

Reach out to the **HackIT Core Team** or open an issue on the repository! Happy Hacking! 🌟
