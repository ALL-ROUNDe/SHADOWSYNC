Here’s a comprehensive Documentation & Project Report for your ShadowSync setup. It covers purpose, features, architecture, setup, usage, and next steps:

🧾 1. Project Overview
Project Name: ShadowSync
Purpose: A private, multi-user file upload/download portal hosted on your home server.
Key Features:

User authentication (admin & regular users)

File operations (upload, download, delete via GUI)

Multiple folders (movies, allfiles)

Admin dashboard for user management

Persistent account storage

Drag‑and‑drop support for uploads

Responsive, dark-themed UI

🛠️ 2. Stack & Architecture
Backend: Python + Flask, reverse‑proxied via Gunicorn (4 workers)

Frontend: HTML/CSS + JavaScript, responsive dark theme

Storage: Local folders on server

User Data: Stored in shadowsync/users.json

Systemd: shadowsync.service to run Gunicorn at startup

Reverse Proxy: Caddy/Nginx optional for HTTPS


✅ 3. Setup Instructions
Place uploads under /home/shadowroot/share/uploads

Install dependencies, e.g.:

bash
Copy
Edit
pip install flask werkzeug gunicorn
Initialize users.json (auto-handled on first run)

Run it:

bash
Copy
Edit
gunicorn -w 4 -b 0.0.0.0:5050 app:app
Configure systemd for auto-start:

shadowsync.service points to Gunicorn

(Optional) Enable HTTPS via Caddy or Tailscale for external access

👥 4. User & Admin Workflows
Admin Login using default or created credentials

User Creation via admin console (/admin)

Folder Navigation:

View file list with icons, size, timestamps

Upload / Drag‑and‑drop files

Download files via buttons

Admins also have “Delete” options

Logout link

🎨 5. UI Highlights
Dark theme with glowing white logo

Responsive for mobile and desktop

Drag‑and‑drop enhanced upload area

Search bar for quick filtering

File list includes icons by extension and formatted sizes

🔧 6. Technical Highlights
Persistent Users: users.json only created if missing — no overwrites

Admin access control: Role-based restrictions

File Handling: Uses secure_filename and safe uploads

Formatting: Sizes in KB/MB/GB

Gunicorn Integration: Multithreaded with systemd service

📦 7. Sample shadowsync.service
ini
Copy
Edit
[Unit]
Description=ShadowSync Gunicorn Service
After=network.target

[Service]
User=shadowroot
WorkingDirectory=/home/shadowroot/shadowsync
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5050 app:app
Restart=on-failure

[Install]
WantedBy=multi-user.target
🔒 8. Next Steps & Enhancements
Feature	Description
folder-based access control	Assign users to specific folders
HTTPS via Tailscale/Caddy/Nginx	For secure remote access
Activity Logs	Track user uploads/downloads
File versioning/archive	Undo or restore old versions
Analytics dashboard	Show usage metrics
Backup strategy	Regular snapshots of user & file data

📝 9. Your Action Report
User: [Your Name/Handle]

Date Completed: June 2025

Environment: Home server , Linux Debian/Ubuntu

Execution Summary:

Configured Flask app with persistent storage

Made responsive UI and drag-and-drop

Wrapped in Gunicorn, auto-started via systemd

Tested local access, left room for HTTPS

Goal Achieved: ✅ A multi-user, persistent, file-sharing portal with admin controls
