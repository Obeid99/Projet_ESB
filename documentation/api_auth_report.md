# ESB Chatbot System: Authentication & API Endpoints Report

## Table of Contents
- [Overview](#overview)
- [Authentication Module (`auth.py`)](#authentication-module-authpy)
  - [Purpose](#purpose)
  - [Key Endpoints](#key-endpoints)
  - [Security](#security)
  - [Usage Example](#usage-example)
- [Main Web API (`web_interface.py`)](#main-web-api-web_interfacepy)
  - [Purpose](#purpose-1)
  - [Authentication Endpoints](#authentication-endpoints)
  - [Chatbot Endpoints](#chatbot-endpoints)
  - [Admin Endpoints](#admin-endpoints)
  - [Dashboard & Utility Endpoints](#dashboard--utility-endpoints)
  - [Security & Best Practices](#security--best-practices)
- [Design Notes](#design-notes)
- [Improvement Suggestions](#improvement-suggestions)

---

## Overview
This report documents the authentication and API modules of the ESB Chatbot backend, focusing on user/admin registration, login, session management, and the main REST API endpoints for chatbot and dashboard operations. The backend is built with Flask, MongoDB, and integrates with OpenAI for chatbot responses.

---


## Authentication Module (`auth.py`)

### Purpose
The `auth.py` module encapsulates all student authentication logic as a Flask Blueprint. It is responsible for:
- Registering new student users with unique usernames and securely hashed passwords.
- Authenticating users and managing their session state.
- Providing a logout endpoint that clears session data for both users and admins.

### Key Endpoints

#### `POST /auth/register`
- **Description:** Registers a new student user.
- **Request Body:**
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Flow:**
  1. Checks if both username and password are provided.
  2. Checks if the username already exists in the MongoDB collection.
  3. Hashes the password using Werkzeug's `generate_password_hash`.
  4. Stores the new user in MongoDB with the hashed password.
  5. Returns a success or error message.
- **Responses:**
  - `201`/`200`: `{ "success": true, "message": "User registered" }`
  - `400`: `{ "error": "Username and password required" }`
  - `409`: `{ "error": "Username already exists" }`

#### `POST /auth/login`
- **Description:** Authenticates a student user.
- **Request Body:**
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Flow:**
  1. Checks if both username and password are provided.
  2. Looks up the user in MongoDB by username.
  3. Verifies the password using Werkzeug's `check_password_hash`.
  4. If valid, sets `session['user_id']` to the user's MongoDB `_id`.
  5. Returns a success or error message.
- **Responses:**
  - `200`: `{ "success": true, "message": "Logged in" }`
  - `400`: `{ "error": "Username and password required" }`
  - `401`: `{ "error": "Invalid credentials" }`

#### `POST /auth/logout`
- **Description:** Logs out the current user/admin.
- **Flow:**
  1. Removes `user_id` and `admin_id` from the session.
  2. Returns a success message.
- **Response:**
  - `200`: `{ "success": true, "message": "Logged out" }`

### Security
- **Password Hashing:** All student passwords are hashed before storage using `generate_password_hash`.
- **Password Verification:** Login checks use `check_password_hash` to prevent timing attacks.
- **Session Management:** Flask session is used to track authentication state. Session keys are cleared on logout.
- **No Plaintext Storage:** Passwords are never stored or transmitted in plaintext.

### Usage Example
```http
# Register
POST /auth/register
Content-Type: application/json
{
  "username": "alice",
  "password": "secret123"
}

# Login
POST /auth/login
Content-Type: application/json
{
  "username": "alice",
  "password": "secret123"
}

# Logout
POST /auth/logout
```

---


## Main Web API (`web_interface.py`)

### Purpose
The `web_interface.py` module is the main Flask application for the ESB Chatbot system. It provides:
- User and admin authentication and registration endpoints.
- REST API endpoints for chatbot interactions (student and admin).
- Dashboard and analytics endpoints for feedback and statistics.
- Integration with MongoDB for all persistent data storage.
- Integration with OpenAI for chatbot response generation.

### Authentication Endpoints

#### `POST /login`
- **Description:** Authenticates a student user (same logic as `/auth/login`).
- **Request Body:**
  ```json
  { "username": "string", "password": "string" }
  ```
- **Flow:**
  1. Checks credentials against MongoDB.
  2. If valid, sets `session['user_id']`.
  3. Returns success or error message.

#### `POST /register`
- **Description:** Registers a new student user (same logic as `/auth/register`).
- **Request Body:**
  ```json
  { "username": "string", "password": "string" }
  ```
- **Flow:**
  1. Checks for required fields and uniqueness.
  2. Hashes password and stores user in MongoDB.
  3. Returns success or error message.

#### `/logout`
- **Description:** Logs out the current user by clearing the session and redirecting to login.

#### `POST /admin/login`
- **Description:** Authenticates an admin user.
- **Request Body:**
  ```json
  { "username": "string", "password": "string" }
  ```
- **Flow:**
  1. Checks credentials against MongoDB (admin collection) or fallback to environment variables.
  2. If valid, sets `session['admin_id']`.
  3. Returns success or error message.
- **Security Note:** Admin passwords are currently stored in plaintext (should be hashed).

#### `POST /admin/register`
- **Description:** Registers a new admin user.
- **Request Body:**
  ```json
  { "username": "string", "password": "string" }
  ```
- **Flow:**
  1. Checks for required fields and uniqueness.
  2. Stores admin credentials in MongoDB (plaintext, should be hashed).
  3. Returns success or error message.

#### `/admin/logout`
- **Description:** Logs out the admin by clearing `admin_id` from the session.

### Chatbot Endpoints

#### `POST /api/chat`
- **Description:** Handles student chatbot interactions.
- **Request Body:**
  ```json
  { "message": "string" }
  ```
- **Flow:**
  1. Requires user authentication (`session['user_id']`).
  2. Receives a user message and session info.
  3. Runs intent and sentiment analysis using dedicated agents.
  4. Stores user message, intent, and sentiment in MongoDB.
  5. Generates a bot response using OpenAI.
  6. Stores bot response in MongoDB.
  7. Returns the bot response and success status.
- **Responses:**
  - `200`: `{ "success": true, "response": "..." }`
  - `401`: `{ "error": "Authentication required" }`

#### `POST /admin/api/chat`
- **Description:** Handles admin chatbot interactions.
- **Request Body:**
  ```json
  { "message": "string" }
  ```
- **Flow:**
  1. Requires admin authentication (`session['admin_id']`).
  2. Stores admin message in MongoDB.
  3. Orchestrates multi-agent response using `handle_admin_query`.
  4. Stores bot response in MongoDB.
  5. Returns the bot response and any metadata.

### Admin Endpoints

#### `/admin/chat`
- **Description:** Renders the admin chat UI (requires admin session).

#### `/admin/api/feedback`
- **Description:** Returns the latest student feedback for dashboard analytics.
- **Response:** List of feedback objects with id, username, title, created_at, and message.

#### `/admin/feedback_chart`
- **Description:** Demo endpoint for feedback chart visualization (HTML, not production-ready).

### Dashboard & Utility Endpoints

#### `GET /api/student-messages/<user_id>`
- **Description:** Returns all messages for a specific student, including username, sentiment, and intent.
- **Response:** List of message objects with metadata.

#### `GET /api/student-messages/all`
- **Description:** Returns all student messages grouped by user, with usernames.
- **Response:** List of all messages with user info.

#### `GET /api/student-stats`
- **Description:** Returns sentiment and intent statistics for dashboard charts.
- **Response:**
  ```json
  {
    "sentiment": { "positive": 10, "neutral": 5, ... },
    "intent": { "question": 8, "feedback": 7, ... }
  }
  ```

#### `GET /api/health`
- **Description:** Health check for MongoDB and OpenAI connectivity.
- **Response:**
  ```json
  { "status": "healthy", "timestamp": 1720708800.0 }
  ```

#### `/static/<filename>`
- **Description:** Serves static files from the `static` directory.

### Security & Best Practices
- **Student Passwords:** Always hashed before storage.
- **Admin Passwords:** Currently stored in plaintext (should be improved).
- **Session Authentication:** All sensitive endpoints require session authentication.
- **CORS:** Enabled for local frontend development.
- **Environment Variables:** All sensitive configuration (MongoDB URI, OpenAI key, etc.) is loaded from environment variables.


---

## Design Notes
- **Blueprints:** The `auth.py` module is designed as a Flask Blueprint for modularity.
- **Session Management:** Uses Flask's session for both user and admin authentication.
- **MongoDB:** All user, admin, chat, and feedback data is stored in MongoDB collections.
- **OpenAI Integration:** Chatbot responses are generated using OpenAI's API, with model selection via environment variable.
- **Agent Architecture:** Intent and sentiment detection are handled by dedicated agents, and all results are logged and stored.
- **Dashboard:** Provides endpoints for feedback and statistics, supporting admin analytics and visualization.

---

## Improvement Suggestions
- **Hash Admin Passwords:** Store admin passwords hashed, not plaintext, for security.
- **Rate Limiting:** Add rate limiting to authentication and chat endpoints to prevent abuse.
- **Error Handling:** Standardize error responses and logging for easier debugging and monitoring.
- **API Documentation:** Consider using Swagger/OpenAPI for automatic API docs.
- **Unit Tests:** Add tests for all endpoints, especially authentication and chat logic.
- **Role Management:** Expand session/user model to support roles and permissions for future features.

---

_Last updated: July 11, 2025_
