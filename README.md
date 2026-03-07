# RendezVousDZ

A modern **digital queue management platform** designed for local service businesses.

RendezVousDZ allows businesses such as **barbershops, salons, clinics, and mechanics** to manage daily customer queues and accept online bookings using a simple **number-based system**.

Instead of chaotic waiting lines or phone calls, customers simply **join the queue online and receive a number**.

---

# 🌍 Product Vision

Create a simple web platform that helps local service businesses manage their daily customer flow digitally.

The system starts with **barbershops**, then expands to:

* Beauty salons
* Dentists
* Mechanics
* Tutors
* Clinics
* Gyms

---

# 🎯 Mission

Help small businesses in Algeria:

* reduce chaos
* reduce phone calls
* avoid missed appointments
* serve more customers efficiently

using a **simple digital queue system**.

---

# 🔥 The Problem

Many small businesses still manage customers using:

* paper notebooks
* phone calls
* physical waiting lines

This leads to:

* long queues
* lost customers
* confusion
* wasted time

---

# ✅ The Solution

RendezVousDZ provides a **daily queue system** where:

1. The business sets a **maximum number of clients per day**
2. Customers reserve the **next available queue number**
3. When the limit is reached → bookings automatically close
4. The business manages the queue digitally

No complicated schedules.

Just **queue numbers**.

---

# 🧩 Core Concept

Each day the system generates a queue:

```
1
2
3
4
...
20
```

Customers reserve the **next available number**.

---

# 🔁 User Flow

## Business Owner

1. Register an account
2. Create a business profile
3. Set max clients per day
4. Share booking link
5. Manage queue from dashboard

---

## Customer

1. Open booking link
2. Choose date
3. Join queue
4. Enter name and phone
5. Receive queue number

---

# ✨ Key Features

### Business Dashboard

* View today's queue
* Add walk-in clients
* Mark clients as **Done**
* Skip clients
* Modify settings

### Customer Booking Page

* Simple booking interface
* Queue number confirmation
* Automatic limit enforcement

### Real-Time Queue Updates

Using **WebSockets**, the queue updates live without refreshing.

### Smart Wait Time Estimation

The system calculates estimated wait time using **average service duration**.

### Digital Display Mode

A full-screen display for shops showing:

* current client
* next clients
* animated queue display

Perfect for tablets or TVs in waiting rooms.

### Analytics Dashboard

Business owners can see:

* daily client counts
* peak hours
* average service time
* weekly activity

---

# 🛠 Tech Stack

### Backend

* Python
* Flask
* Flask-SocketIO

### Frontend

* HTML
* TailwindCSS
* JavaScript

### Database

* SQLite (development)
* PostgreSQL (production)

---

# 📂 Project Structure

```
backend/
    app.py
    models.py
    db.py
    routes/

templates/
static/

.env.example
README.md
```

---

# ⚙️ Installation

Clone the repository:

```
git clone https://github.com/yourusername/rendezvousdz.git
cd rendezvousdz
```

Create virtual environment:

```
python -m venv venv
```

Activate environment:

Windows

```
venv\Scripts\activate
```

Install dependencies:

```
pip install -r requirements.txt
```

Create `.env` file:

```
cp .env.example .env
```

Run the server:

```
python app.py
```

Open in browser:

```
http://localhost:5000
```

---

# 🔐 Environment Variables

Example `.env` file:

```
SECRET_KEY=your_secret_key_here

MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password
MAIL_DEFAULT_SENDER=your_email@example.com
```

---

# 📸 Screenshots

## Business Dashboard

![Dashboard](screenshots/dashboard.png)

## Booking Page

![Booking](screenshots/booking.png)

## Digital Queue Display

![Display](screenshots/display.png)

---



# 📈 Growth Plan

Phase 1 — Barbershops
Phase 2 — Salons
Phase 3 — Dentists
Phase 4 — Mechanics
Phase 5 — Multi-service platform

---

# 🧠 Long Term Vision

Transform from a simple:

Queue system

into a full

**Business Management Platform**

including:

* bookings
* analytics
* notifications
* business intelligence

---

# 🏆 Success Metrics

* Number of businesses using the platform
* Daily bookings
* Paid subscribers
* Retention rate

---

# 🧑‍💻 Author

Abderraouf Atsamnia

---

# ⭐ Support the Project

If you like the project, consider giving it a **star ⭐ on GitHub**.
