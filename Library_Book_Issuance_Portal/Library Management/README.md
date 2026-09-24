# SGGS Library Management System

A simple Django-based library management system for **Shri Guru Gobind Singhji Institute of Engineering and Technology (SGGS)**, with AI features powered by Google Gemini.

## Features

- **Two roles:** Students (self-register) and Admin / Librarian.
- **Books:** title, author, ISBN, category, description, total/available copies.
- **Browsing:** filter by category or author; keyword search.
- **Issue / Return:** 14-day loan; ₹5 per day late fine.
- **AI (Gemini):**
  - Auto-generates a short summary and tags when a book is added.
  - Natural-language search ("easy books for learning Python").
  - Personalized recommendations based on previously issued books.
  - A chat assistant for book suggestions and library help.
- Admin CRUD via both custom pages and the built-in Django admin.

## Project Structure

```
library_project/    # Django project (settings, urls)
users/              # Custom user model, auth, profile
books/              # Book + Category models, listing, search, CRUD
transactions/       # Issue / return records and fine calculation
ai/                 # Gemini client, services, chat views, prompts
templates/          # Django templates
static/             # CSS
```

All AI-related code lives inside `ai/` for easy maintenance.

## Setup

1. **Clone / open the project folder** (this directory).

2. **Create a virtual environment and install dependencies:**

   ```bash
   python -m venv venv
   source venv/bin/activate        # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables** — copy `.env.example` to `.env` and fill in values:

   ```
   SECRET_KEY=some-random-string
   DEBUG=True
   GEMINI_API_KEY=your-gemini-api-key
   ```

   You can get a Gemini API key at https://aistudio.google.com/app/apikey.

   > If `GEMINI_API_KEY` is not set, the app still runs — AI features gracefully
   > degrade (summaries/tags/recommendations skip; search falls back to keywords;
   > chat returns a polite unavailable message).

4. **Run migrations:**

   ```bash
   python manage.py makemigrations users books transactions
   python manage.py migrate
   ```

5. **Create an admin user** (librarian):

   ```bash
   python manage.py createsuperuser
   ```

   Then open `/admin/` → Users → edit the user → set **Role** to *Admin / Librarian*.

6. **Run the development server:**

   ```bash
   python manage.py runserver
   ```

   Open http://127.0.0.1:8000/.

## Usage

- **Students** can register at `/users/register/`, browse books, use AI search, chat with the assistant, and issue/return books.
- **Librarians** can add/edit/delete books at `/books/add/`, view all issues at `/transactions/all/`, and manage users via Django admin.

## Notes

- Database: SQLite (simple, file-based). Swap `DATABASES` in `library_project/settings.py` for Postgres/MySQL if needed.
- Loan length and fine rate are in `settings.py` (`LIBRARY_LOAN_DAYS`, `LIBRARY_FINE_PER_DAY`).
- Gemini model used: `gemini-2.0-flash` (fast, inexpensive).
