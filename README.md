# E2E Voting Prototype System

A work-inprogress, the current implementation is a simplified end-to-end verifiable (E2E-V) voting system. It demonstrates the core concepts of secure electronic voting, including client-side encryption, token-based authentication, and public ballot verification. Uses python and javascript via a flask app.

As of right now, changes must be made to every security property mentioned under the project 2 design instructions. The following are necessary security properties:
- secure authentication before voting       Done
- secrecy (votes are private)               Done
- individual verifiability                  Done
- universal verifiability                   Done
- anti-coercion                             Not Done
- integrity                                 Weak (needs to be changed)

---

## Running the App

To run the application, first create a virtual environment from the project root using "python -m venv venv", which will generate a local environment folder named venv. Then activate the environment using "source venv/bin/activate" on Linux, macOS, or WSL, or "venv\Scripts\activate" on Windows Command Prompt, or "venv\Scripts\Activate.ps1" on PowerShell. After activation, install all required dependencies with "pip install -r requirements.txt". Once the setup is complete, start the Flask application by running "python -m web.app", and then open your browser to http://127.0.0.1:5000 to interact with the system through localhost.

## ⚙️ Overview

The system allows users to:

- Obtain a one-time voting token
- Encrypt their vote in the browser
- Submit an encrypted ballot to the server
- Have the server verify and record the ballot
- Prevent multiple voting using single-use tokens

The system is EXTREMELY basic and does not even have functionality to show the current votes or anything.

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

- **Authentication**: One-time voting tokens
- **Ballot Encryption**: Client-side encryption
- **Integrity Checking**: Proof validation for ballot structure (needs to be updated to better implementation)
- **Single Voting Enforcement**: Tokens are consumed after use (could discuss about changing original votes in the future)
- **Transparency**: All ballots are stored on a public bulletin board (currently not shown in the application)

⚠️ Note: Cryptographic components are simplified and must be changed.

---

## 🔁 Voting Flow

1. User opens the voting webpage
2. Browser requests:
   - Public key (`/api/public_key`)
   - Voting token (`/api/token`)
3. User selects a vote (YES/NO)
4. Browser:
   - Encrypts vote locally
   - Generates proof (simplified)
5. Encrypted ballot is sent to server (`/api/vote`)
6. Server:
   - Validates token (single-use)
   - Verifies proof
   - Stores ballot on bulletin board
7. Ballot becomes publicly visible

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
