# E2E Voting Prototype System

A work-inprogress, the current implementation is a simplified end-to-end verifiable (E2E-V) voting system. It demonstrates the core concepts of secure electronic voting, including client-side encryption, Google Autherntication for login, token-based authentication for voting, and public ballot verification. Uses python and javascript via a flask app.

It is worth noting that if this were in the real world, eligible voters would be asked to submit their google accounts to the administrator, who would then add them to a list of people in order to prevent multiple different google accounts from one person voting. This would also prevent random people who shouldn't be voting from gaining access.

As of right now, changes must be made to every security property mentioned under the project 2 design instructions. The following are necessary security properties:
- secure authentication before voting       Done
- secrecy (votes are private)               Done
- individual verifiability                  Done
- universal verifiability                   Done
- anti-coercion                             Done
- integrity                                 Weak (each person gets 1 vote and can't change it)

---

## Running the App

To run the application, first create a virtual environment from the project root using "python -m venv venv", which will generate a local environment folder named venv. Then activate the environment using "source venv/bin/activate" on Linux, macOS, or WSL, or "venv\Scripts\activate" on Windows Command Prompt, or "venv\Scripts\Activate.ps1" on PowerShell. After activation, install all required dependencies with "pip install -r requirements.txt". Once the setup is complete, start the Flask application by running "python -m web.app", and then open your browser to http://127.0.0.1:5000 to interact with the system through localhost.

## Common issue

If the app is having errors it most commonly is an issue with the database being outdated, in order to fix this press Ctrl C to stop the app, then run rm web/instance/app.db, then rerun the app again with python -m web.app

## ⚙️ Overview

The system allows users to:

- Obtain a one-time voting token
- Encrypt their vote in the browser
- Submit an encrypted ballot to the server that can either be real or a dummy ballot
- Have the server verify and record the ballot
- Prevent multiple voting using single-use tokens


---

## 🧱 Architecture

The system is split into three main components:

### 🖥️ Frontend (Browser)
- Located in `web/templates` and `web/static`
- Handles user interaction
- Encrypts votes using JavaScript
- Sends ballots to the backend via HTTP requests

### 🌐 Backend (Flask Server)
- Located in `web/app.py`
- Exposes REST API endpoints:
  - `/api/public_key`
  - `/api/token`
  - `/api/vote`
  - `/api/board`
- Coordinates authentication and ballot processing

### 🔐 Core Logic Modules
- `crypto.py` → cryptographic primitives (toy implementation)
- `auth.py` → token generation and validation
- `verify_server.py` → ballot verification logic
- `bulletin_board.py` → public storage of ballots
- `tally.py` → election result computation

---

## 🔐 Security Model (Simplified)

This system implements simplified versions of:

- **Authentication**: One-time voting tokens + Google OAuth
- **Ballot Encryption**: Client-side encryption
- **Integrity Checking**: Proof validation for ballot structure 
- **Single Voting Enforcement**: Tokens are consumed after use (could discuss about changing original votes in the future)
- **Transparency**: All ballots are stored on a public bulletin board

⚠️ Note: Cryptographic components are simplified and must be changed if deployed for real.

---

## 🔁 Voting Flow

1. User opens the voting webpage
2. User logs into their google account and then clicks on "Start Voting"
3. Browser requests:
   - Public key (`/api/public_key`)
   - Voting token (`/api/token`)
4. User selects a vote (YES/NO)
5. Browser:
   - Encrypts vote locally
   - Generates proof (simplified)
6. Encrypted ballot is sent to server (`/api/vote`)
7. Server:
   - Validates token (single-use)
   - Verifies proof
   - Stores ballot on bulletin board
8. Ballot becomes publicly visible

---

## 📡 API Endpoints

### `GET /api/public_key`
Returns the public key used for encryption.

### `POST /api/token`
Issues a one-time voting token.

### `POST /api/vote`
Submits an encrypted ballot:
```json
{
  "ciphertext": [...],
  "proof": {...},
  "token": "uuid"
}
