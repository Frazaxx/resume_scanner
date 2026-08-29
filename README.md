# Resume Scanner

A small, local web application that analyzes a resume (pasted text or a
`.txt` upload) and produces a polished, dashboard-style report: a heuristic
0–100 score, key statistics, section detection, keyword matching, and
actionable suggestions.

Built entirely with **Python, HTML, and CSS** — no Flask, Django, React,
Bootstrap, or any third-party packages. The backend uses only Python's
standard library (`http.server`).

---

## Features

- **Resume input** — paste text into a large textarea, or upload a `.txt`
  file (loaded client-side into the textarea).
- **Resume analysis** — word count, character count, number of sections,
  bullet points, emails, phone numbers, detected skills, and action verbs.
- **Section detection** — checks for Summary, Objective, Contact, Education,
  Experience, Projects, Skills, Certifications, and Achievements, and shows
  which are present vs. missing.
- **Keyword analysis** — scans against a built-in list of common technical
  and professional keywords (Python, SQL, Git, Leadership, etc.).
- **Resume score** — a transparent, rule-based 0–100 score combining resume
  length, section coverage, contact info, skills, project/experience
  evidence, and action-verb usage. Clearly labeled as a **basic heuristic**,
  not an AI hiring prediction.
- **Suggestions** — plain-language tips based on what's missing or weak.
- **Dashboard UI** — dark theme, cards, an animated score ring, progress-bar
  style stats, tags for keywords, and a responsive layout.

---

## Project structure

```
resume-scanner/
│
├── server.py       # Python standard-library HTTP server + analysis engine
├── index.html       # Frontend markup (input form + results dashboard)
├── style.css        # Dark, modern styling
└── README.md
```

---

## How it works

1. `server.py` starts a plain `http.server.HTTPServer` on port `8000`.
2. `GET /` and `GET /style.css` serve the static frontend files.
3. When you click **SCAN RESUME**, the browser sends a `POST /scan` request
   with the resume text as JSON.
4. The server analyzes the text with regular expressions and simple word
   lists (no external libraries), computes the score, and returns a JSON
   report.
5. The frontend JavaScript renders that JSON into the dashboard — no page
   reload required.

---

## Setup & running locally

**Requirements:** Python 3.7+ (standard library only — nothing to `pip
install`).

1. Download / clone this folder so `server.py`, `index.html`, and
   `style.css` are all in the same directory.
2. Open a terminal in that directory.
3. Run the server:

   ```bash
   python server.py
   ```

4. You should see:

   ```
   Resume Scanner running at http://localhost:8000
   Press Ctrl+C to stop.
   ```

5. Open your browser and go to **http://localhost:8000**.
6. Paste resume text or upload a `.txt` file, then click **SCAN RESUME**.
7. Press `Ctrl+C` in the terminal to stop the server when you're done.

---

## Technologies used

- **Python 3** (`http.server`, `json`, `re`) — server and analysis engine
- **HTML5** — page structure
- **CSS3** — dark theme, cards, progress ring, responsive grid
- **Vanilla JavaScript** (in `index.html`) — handles the file upload,
  calls `/scan`, and renders the results — no frameworks

---

## Notes & limitations

- The score is a **simple heuristic**, not a machine-learning or AI-based
  hiring assessment. It's meant to give quick, explainable feedback.
- Section detection looks for common heading names on their own line
  (e.g. "Experience", "Work Experience"); resumes with very unconventional
  formatting may not be detected perfectly.
- Only `.txt` file uploads are supported, to keep parsing simple and
  dependency-free (no PDF/DOCX parsing libraries required).