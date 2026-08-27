# Quest Tracker

Quest Tracker is a full-stack, gamified task management web application inspired by **Genshin Impact's daily commission system**. Users complete real-world daily tasks, submit image proof of their progress, and earn in-app currency to track personal growth.

 **Live Application:** [https://quest-tracker-6wt3.onrender.com/login/](https://quest-tracker-6wt3.onrender.com/login/)

---

## Features

- **Daily Commission System:** Inspired by Genshin Impact, users are assigned daily tasks to keep real-world productivity engaging.
- **Task Progression & Proof Uploads:** Submit image proof for completed quests to update progression status.
- **In-App Currency & Rewards:** Earn virtual currency upon quest completion and track overall user progression.
- **Production Architecture:** Deployed on Render using dynamic static asset handling and secure environment separation.

---

## Tech Stack

- **Backend:** Python, Django
- **Frontend:** HTML5, CSS3, JavaScript
- **Database:** MySQL (Managed via Aiven Cloud DB), SQLite (Development)
- **Deployment & Hosting:** Render, Gunicorn, WhiteNoise

---

## Getting Started Locally

### Prerequisites

Ensure you have the following installed locally:
- Python 3.10+
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/BISHESH-T/Quest-Tracker.git
   cd Quest-Tracker
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Environment Variables:**
   Create a `.env` file in the root directory and add your credentials:
   ```env
   SECRET_KEY=your_django_secret_key
   DEBUG=True
   ```

5. **Run Database Migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Start the Development Server:**
   ```bash
   python manage.py runserver
   ```
   Open `http://127.0.0.1:8000/` in your browser.

---

## Deployment & Build Configuration

The project uses a custom `build.sh` script for automated zero-downtime deployment on Render:

```bash
#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

---

