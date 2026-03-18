# 🚀 Sky Internal Collaboration & Service Management Platform

A modern internal web platform designed to manage teams, departments, services, repositories, and communication within an organisation.

This system enables structured collaboration, clear ownership, and efficient communication across technical teams.

---

## 📌 Overview

This platform simulates a real-world enterprise internal system (similar to Sky’s internal tools), where employees can:

* Explore organisational structure (Teams, Departments, People)
* Manage services and repositories
* Communicate via messaging and contact channels
* Track system activity via audit logs
* Collaborate efficiently across teams

---

## 🎯 Objectives

* Provide a **centralised platform** for organisational management
* Ensure **clear ownership and accountability**
* Enable **efficient communication between users**
* Maintain **data integrity and traceability**
* Follow **industry-level software architecture practices**

---

## 🧩 Features

### 👥 People Module

* Manage employees (Person entity)
* Store:

  * Name
  * Email
  * Job title
  * Active status

---

### 🏢 Departments Module

* Organise teams under departments
* Assign a department head
* Maintain structured hierarchy

---

### 👨‍👩‍👧 Teams Module

* Create and manage teams
* Assign members to teams
* Define relationships between teams

---

### 🔗 Team Dependencies

* Model relationships between teams
* Understand collaboration and ownership flow

---

### ⚙️ Services Module

* Represent internal systems/products
* Link services to teams
* Track ownership

---

### 📂 Repository Module

* Store repositories linked to teams
* Includes:

  * Name
  * URL
  * Description

---

### 📞 Contact Channels

* Define communication channels:

  * Slack
  * Email
  * Internal tools

---

### 💬 Messaging System

* User-to-user conversations
* Message history support
* Scalable design (conversation-based)

---

### 📝 Audit Log

* Track user actions
* Record system changes
* Ensure accountability and debugging

---

### 👤 User & Authentication

* Roles:

  * Admin (full control)
  * Regular User (limited access)
* Secure authentication system

---

## 🏗️ System Architecture

The system follows a layered architecture:

Database → Models → Controllers → Views (UI)

* Backend: Python (Django)
* Frontend: HTML, CSS, JavaScript
* Database: SQLite 
* Pattern: MVC

---

## 🗄️ Database Design

* Normalised relational schema
* Strong constraints (PK, FK, CHECK, NOT NULL, UNIQUE)
* Separation of concerns:

  * Person ≠ User
  * UserProfile for linking

---

## 🔐 Security

* Role-Based Access Control (RBAC)
* Input validation
* Secure authentication
* Audit logging

---

## ⚙️ Technologies

| Layer      | Technology            |
| ---------- | --------------------- |
| Backend    | Python (Django)       |
| Frontend   | HTML, CSS, JavaScript |
| Database   | SQLite / MySQL        |
| Versioning | Git & GitHub          |
| Design     | Figma                 |

---

## 🚀 Getting Started

### 1. Clone

git clone https://github.com/your-username/your-repo.git
cd your-repo

---

### 2. Virtual Environment

python3 -m venv venv
source venv/bin/activate

---

### 3. Install Dependencies

pip install -r requirements.txt

---

### 4. Environment Variables

Create `.env`:

SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=your_database_url

---

### 5. Run Migrations

python manage.py migrate

---

### 6. Run Server

python manage.py runserver

---

### 7. Access

http://127.0.0.1:8000/

---

## 📊 Future Improvements

* Real-time messaging (WebSockets)
* Notification system
* Analytics dashboard
* Fine-grained permissions
* REST API versioning

---

## 🧠 Design Decisions

* Conversation-based messaging → scalable
* Audit log → traceability
* Team dependencies → real-world modelling
* User vs Person separation → flexibility

---

## 📄 License

Educational / demonstration purposes

---

## 👨‍💻 Author

**Yanis Kaced**
Computer Science Student – University of Westminster
Aspiring Full-Stack & Backend Engineer

---

## ⭐ Final Note

This project demonstrates:

* Strong database design
* Clean architecture
* Real-world system thinking
* Industry-level development practices

