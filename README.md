# CapRoute AI

## Prerequisites

- Python 3.11+ (recommended)
- Node.js 20+
- Git

---

## Clone the repository

```bash
git clone https://github.com/<your-username>/<your-repository>.git
cd <your-repository>
```

---

## Backend Setup

### Create a virtual environment

Windows

```bash
python -m venv .venv
```

Activate

```bash
.venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Start the backend

```bash
python -m uvicorn main:app --reload
```

Backend runs at:

http://127.0.0.1:8000

---

## Frontend Setup

Open another terminal.

```bash
npm install
```

Start Vite

```bash
npm run dev
```

Frontend runs at:

http://localhost:5173

---

## Environment Variables

Create a `.env` file.

Example:

```env
GROQ_API_KEY=your_key_here
SARVAM_API_KEY=your_key_here
```

---

## Folder Structure

```
src/
main.py
logic.py
map.py
ml_model.py
requirements.txt
package.json
```
