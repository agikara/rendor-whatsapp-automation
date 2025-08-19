# Full-Stack WhatsApp FAQ Bot

This project is a complete, full-stack WhatsApp FAQ and support automation system built with Python and FastAPI. It integrates with the official Meta WhatsApp Business Cloud API to provide automated responses to users, while also offering an admin dashboard for manual chat management.

## Features

- **Interactive WhatsApp Bot:**
  - Greets users and presents a main menu of FAQ categories.
  - Uses interactive List Menus for easy navigation.
  - Responds with predefined answers from a configurable `faq.json` file.
  - Handles user input from text messages and interactive replies.
  - Includes a fallback message for unrecognized input.

- **Admin Dashboard:**
  - A secure, web-based dashboard for chat administration.
  - Simple authentication using username and password.
  - View a list of all users who have contacted the bot.
  - Select a user to view the full chat history.
  - Send manual text messages to users directly from the dashboard.

- **Technical:**
  - Built with **FastAPI**, a modern, high-performance Python web framework.
  - Uses **SQLAlchemy** ORM for database interactions with a **SQLite** database.
  - Frontend built with vanilla **HTML, CSS, and JavaScript**.
  - Securely manages credentials and settings using a `.env` file.
  - All conversations are logged in the database.

## Tech Stack

- **Backend:** FastAPI, Uvicorn
- **Database:** SQLite, SQLAlchemy
- **Frontend:** HTML, CSS, Vanilla JavaScript
- **API Integration:** Python `requests` library for the WhatsApp Cloud API

## Prerequisites

- Python 3.8+ and Pip
- A Meta for Developers account
- A WhatsApp Business Account and a registered phone number
- A Meta App with the "WhatsApp Business" product configured

## Setup and Installation

**1. Clone the Repository**

First, get the source code onto your local machine.
```bash
git clone <repository-url>
cd <repository-name>
```

**2. Create a Virtual Environment**

It's highly recommended to use a virtual environment to manage project dependencies.
```bash
# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
venv\Scripts\activate
```

**3. Install Dependencies**

Install all the required Python packages.
```bash
pip install -r requirements.txt
```

**4. Configure Environment Variables**

The project uses a `.env` file to store sensitive credentials.

- Make a copy of the example file:
  ```bash
  cp .env.example .env
  ```
- Open the new `.env` file and fill in the required values:
  - `WHATSAPP_TOKEN`: Your temporary or permanent access token from the Meta App's "API Setup" page.
  - `WHATSAPP_PHONE_NUMBER_ID`: The Phone Number ID associated with your WhatsApp number, also found on the "API Setup" page.
  - `VERIFY_TOKEN`: Create a strong, random string. You will use this exact string when setting up the webhook in the Meta App Dashboard.
  - `ADMIN_USERNAME` and `ADMIN_PASSWORD`: Set the credentials you want to use to log in to the admin dashboard.

## Running the Application

Once the setup is complete, you can run the application using Uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
The server will be running on `http://localhost:8000`.

## How to Use

**1. Configure the Webhook**

Your application needs a publicly accessible URL for Meta to send webhook events. When deploying to a server, this will be your domain. For local development, you can use a tool like **ngrok** to expose your local server to the internet.

- Start ngrok to forward traffic to your local port 8000:
  ```bash
  ngrok http 8000
  ```
- Ngrok will give you a public HTTPS URL (e.g., `https://random-string.ngrok.io`).

- In your Meta App Dashboard, go to WhatsApp > Configuration.
- Click "Edit" on the Webhook section.
- **Callback URL:** Enter your public URL followed by `/webhook` (e.g., `https://random-string.ngrok.io/webhook`).
- **Verify token:** Enter the exact same `VERIFY_TOKEN` you set in your `.env` file.
- Click "Verify and save".

- After verifying, click "Manage" and subscribe to the `messages` webhook field.

**2. Access the Admin Dashboard**

- Navigate to `http://localhost:8000/dashboard` in your web browser.
- You will be prompted for a username and password. Use the `ADMIN_USERNAME` and `ADMIN_PASSWORD` from your `.env` file.

## Project Structure

```
.
├── app/
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── dashboard.py  # API endpoints for the admin dashboard
│   │   └── webhook.py    # Endpoints for WhatsApp webhook
│   ├── static/
│   │   ├── app.js        # Frontend logic for the dashboard
│   │   └── styles.css    # Styles for the dashboard
│   ├── templates/
│   │   └── dashboard.html # HTML for the admin dashboard
│   ├── __init__.py
│   ├── config.py         # Pydantic settings management
│   ├── crud.py           # Database create, read, update, delete functions
│   ├── database.py       # SQLAlchemy database setup
│   ├── faq_service.py    # Core logic for FAQ conversation flow
│   ├── main.py           # Main FastAPI application
│   ├── models.py         # SQLAlchemy ORM models
│   ├── schemas.py        # Pydantic data validation schemas
│   ├── security.py       # Authentication logic
│   └── whatsapp_client.py# Client for sending messages to WhatsApp API
├── .env                  # Your local environment variables (DO NOT COMMIT)
├── .env.example          # Example environment file
├── .gitignore            # Files to be ignored by Git
├── debug.py              # A helper script for debugging
├── faq.json              # The structure and content of the FAQ bot
├── README.md             # This file
└── requirements.txt      # Python dependencies
```
