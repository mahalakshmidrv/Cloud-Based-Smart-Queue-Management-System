# Cloud-Based Smart Queue Management System

QueueFlow is a beginner-friendly cloud computing project built with **Python Flask, SQLite, HTML, CSS, and JavaScript**. Customers can join a digital queue and receive a ticket number. Staff can manage the line from a dashboard.

## Features

- Responsive customer portal and staff dashboard
- Join queue by entering a name and choosing a service
- Unique daily-style ticket numbers
- Estimated waiting time based on service type and customers ahead
- Live queue overview and JSON queue endpoint (`/api/queue`)
- Call next customer, mark tickets served, or cancel tickets
- Queue statistics: waiting, serving, served today, and tickets created today
- Recent ticket history and explicit reset confirmation
- SQLite database created automatically on first run
- Health check endpoint at `/health`

## Requirements

- Python 3.10 or newer
- pip (Python package installer)

## Run on Windows / VS Code

1. Extract the ZIP and open the `Cloud_Based_Smart_Queue_Management_System` folder in VS Code.
2. Open **Terminal → New Terminal**.
3. Create a virtual environment:

   ```powershell
   python -m venv .venv
   ```

4. Activate it:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, you can run the app using `.venv\Scripts\python.exe` directly without activating the environment.

5. Install packages:

   ```powershell
   python -m pip install -r requirements.txt
   ```

6. Start the app:

   ```powershell
   python app.py
   ```

7. Open **http://127.0.0.1:5000** in your browser.

If activation is blocked, use these alternatives from the project folder:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Pages

- `/` — customer portal
- `/admin` — staff dashboard
- `/ticket/<id>` — ticket confirmation
- `/api/queue` — active queue JSON endpoint
- `/health` — basic health check

## Deploying

The included `Procfile` supports common platforms that run Gunicorn. Set `SECRET_KEY` to a long random value in the hosting environment. SQLite is suitable for a class demo and local testing, but some cloud hosts use ephemeral filesystems; use a managed persistent database for production.

## Important demo limitations

This is an educational prototype, not a secured production service. The staff dashboard has no authentication, so anyone who can access the app can manage tickets or clear the queue. Add staff login/authorization, CSRF protection, rate limiting, and privacy controls before public deployment. Ticket estimates are approximations and do not guarantee service time. This project simulates a cloud-ready web application; it is not deployed live by creating this ZIP.
