NeuroSense Frontend (React + Vite + TypeScript)

Quick start

1. Install dependencies
   cd frontend
   npm install

2. Run dev server
   npm run dev

3. Default API base
   The frontend expects the backend API at http://localhost:5000/api by default.
   To override, set the Vite env var VITE_API_BASE, for example:

   VITE_API_BASE=http://localhost:5000/api npm run dev

Implemented pages
- /login, /register — authentication (calls /api/auth)
- /dashboard — main landing for logged-in users
- /assessment/start — create a new assessment
- /assessment/lifestyle/:id — lifestyle questionnaire
- /assessment/cognitive/:id — cognitive test submission
- /assessment/speech/:id — upload audio files
- /assessment/finalize/:id — (not implemented UI; backend endpoint exists)
- /reports — list history and trigger generation
- /knowledge — knowledge articles
- /health — simple health page

Notes and next steps
- This is a minimal, functional scaffold. Forms are basic and lack client-side validation.
- You should run the backend (Flask app) and a MongoDB instance to exercise end-to-end flows.
- I can add: nicer layout, persistent user profile, admin UI, file preview, waveform visualization, audio recording, and form validations.
