# 🚀 HackIT Commit Rush — Open Source Contribution Drive

[![Event](https://img.shields.io/badge/Event-HackIT%20Commit%20Rush-8A2BE2?style=for-the-badge&logo=github)](https://github.com/Hackit-DROID)
[![Organization](https://img.shields.io/badge/Community-HackIT--DROID-007ACC?style=for-the-badge&logo=discord)](https://github.com/Hackit-DROID)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://python.org)
[![Security](https://img.shields.io/badge/Secrets%20Scan-Passed-success?style=for-the-badge&logo=shield)](./.env.example)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

Welcome to the official repository for **HackIT Commit Rush**, an open-source contribution drive organized by **HackIT — SGGSIE&T**. 

This repository serves as a centralized, curated hub housing **67 standardized, feature-indexed student projects** spanning Artificial Intelligence, Agentic Workflows, Machine Learning, Deep Learning, Campus MIS Portals, and Enterprise Web Applications.

---

## 📋 Table of Contents

- [✨ Key Features](#-key-features)
- [🛠️ Technology Stack](#️-technology-stack)
- [⚡ Quick Start](#-quick-start)
- [🔐 Environment & Security Configuration](#-environment--security-configuration)
- [🗂️ Project Directory Index](#️-project-directory-index)
- [🤝 How to Contribute](#-how-to-contribute)
- [📜 License](#-license)

---

## ✨ Key Features

- **Standardized Architecture**: All 67 projects have been restructured with descriptive, feature-accurate titles derived from codebase analysis (Models, Endpoints, and Views).
- **Hardcoded Secrets Sanitization**: 100% compliant with zero hardcoded API keys in source code. Credentials are managed via centralized environment variables.
- **Diverse Domain Coverage**:
  - 🤖 **Agentic & AI Automation**: Multi-agent LLM systems, LangChain/LangGraph pipelines, OpenAI/OpenRouter integrations.
  - 👁️ **Deep Learning & Computer Vision**: Automated document data extraction (Gemini Vision/Flash).
  - 🎓 **Campus & Academic MIS**: Timetable engines, Course enrollment, Student mark processing, and Hostel management.
  - 🌐 **Full-Stack & Web Frameworks**: Django and Flask MVC applications with SQLite/PostgreSQL support.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Core Languages** | Python 3.10+, HTML5, CSS3, JavaScript (ES6+) |
| **Web Frameworks** | Django, Flask, Streamlit |
| **AI & LLM Frameworks** | LangChain, LangGraph, OpenAI SDK, Google GenAI (Gemini), OpenRouter API |
| **Database & Storage** | SQLite, PostgreSQL, Supabase |
| **DevOps & Environment** | `python-dotenv`, Virtual Environment (`venv`), Git |

---

## ⚡ Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Hackit-DROID/Open-Source-Contribution-Drive.git
cd Open-Source-Contribution-Drive
```

### 2. Set Up Virtual Environment

```bash
python3 -m venv venv
source venv/bin/venv/activate   # On Linux/macOS
# venv\Scripts\activate          # On Windows
```

### 3. Install Dependencies

Install the required core packages for AI, web frameworks, and environment management:

```bash
pip install django flask langchain langchain-openai langgraph google-genai supabase python-dotenv requests pandas
```

---

## 🔐 Environment & Security Configuration

To run projects that interact with LLM APIs or Supabase databases, configure your root `.env` file.

### 1. Create your `.env` file

Copy the provided root `.env.example` template:

```bash
cp .env.example .env
```

### 2. Populate Environment Variables

Fill in your actual secret keys inside `.env`:

```env
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# OpenRouter API Key
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Supabase Credentials
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_KEY=your_supabase_anon_or_service_key

# Email Automation (Gmail App Password)
SENDER_EMAIL=your_email@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password

# Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here
```

> ⚠️ **Security Note**: Never commit your `.env` file to version control. All `.env` files are ignored via `.gitignore`.

---

## 🗂️ Project Directory Index

The 67 project submissions in this repository are categorized into domain suites:

### 🤖 AI, Agentic Workflows & ML
- `LangChain_Form_Automation_Agent`: Multi-node form automation using LangGraph, OpenRouter, Gmail SMTP, and Supabase.
- `AI_Data_Analyst_Agent`: Natural language data analysis agent using OpenAI APIs.
- `DeepLearning_Invoice_PDF_Extractor`: PDF invoice parser and structured JSON generator powered by Gemini Flash.
- `OpenAI_Syntax_Generator`: Automated Python syntax generator powered by OpenAI response endpoints.
- `NeuralChat_Multi_Agent_Bot`: Multi-agent chat interface.

### 🎓 Campus MIS & Student Management
- `Hostel_Room_Allocation_System` (v1–v3): Room allocation, fee tracking, and hostel warden management.
- `University_Course_Enrollment_Portal` (v1–v8): Course registration, prerequisites, and department timetable manager.
- `Student_Attendance_Marks_Dashboard` (v1–v4): Student marks, test scores, and attendance reporting.
- `Student_Grade_Mark_Management_System` (v1–v7): Grade calculation and academic report generator.
- `Student_Academic_Dashboard` (v1–v3): Student performance metrics and personal dashboard.
- `Student_Records_CRUD_Portal` (v1–v7): Student record registration and administrative portal.

### 📚 Library & Campus Services
- `Library_Book_Issuance_Portal` (v1–v4): Book issuing, return tracking, and library catalog.
- `Library_Catalog_Management_System` (v1–v21): Complete library inventory and borrowing system.
- `Blood_Donation_Management_System`: Blood bank inventory, donor registration, and emergency requests.
- `Hotel_Reservation_Fee_System`: Room booking and guest billing portal.

---

## 🤝 How to Contribute

We welcome contributions during **HackIT Commit Rush**!

1. **Fork the Repository** on GitHub.
2. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Commit your Changes**:
   ```bash
   git commit -m "Add: Descriptive message of your changes"
   ```
4. **Push to your Fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Open a Pull Request** against the `main` branch.

Please review [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines on code quality and submission protocols.

---

## 📜 License

This repository is distributed under the **MIT License**. See [LICENSE](./LICENSE) for details.

---

<p align="center">
  Organized with ❤️ by <b>HackIT — SGGSIE&T</b>
</p>
