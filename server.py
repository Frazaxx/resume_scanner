"""
Resume Scanner - Local Web Application
----------------------------------------
A tiny web app that analyzes resume text and returns a heuristic score,
statistics, section detection, keyword matches, and improvement suggestions.

Built ONLY with the Python standard library (http.server) plus plain
HTML/CSS/JS on the frontend. No Flask, Django, or third-party packages.

Run it with:
    python server.py

Then open:
    http://localhost:8000
"""

import json
import re
from http.server import HTTPServer, BaseHTTPRequestHandler

# ---------------------------------------------------------------------------
# Configuration / reference data used by the analysis engine
# ---------------------------------------------------------------------------

PORT = 8000

# Resume sections we look for. The "aliases" are alternate headings that
# should count as the same section (e.g. "Work Experience" -> "Experience").
SECTION_ALIASES = {
    "Summary": ["summary", "professional summary", "profile"],
    "Objective": ["objective", "career objective"],
    "Contact": ["contact", "contact information", "contact details"],
    "Education": ["education", "academic background"],
    "Experience": ["experience", "work experience", "employment history",
                   "professional experience", "work history"],
    "Projects": ["projects", "personal projects", "academic projects"],
    "Skills": ["skills", "technical skills", "core competencies"],
    "Certifications": ["certifications", "certificates", "licenses"],
    "Achievements": ["achievements", "awards", "honors", "accomplishments"],
}

# A small built-in library of technical/professional keywords to scan for.
KEYWORD_LIBRARY = [
    "Python", "Java", "JavaScript", "TypeScript", "HTML", "CSS", "SQL",
    "Git", "GitHub", "C++", "C", "React", "Node.js", "Excel",
    "Communication", "Leadership", "Teamwork", "Problem Solving",
    "Management", "Docker", "Linux", "AWS", "Agile", "REST API",
]

# Common resume action verbs. Presence of many of these signals an
# achievement-oriented (rather than duty-oriented) resume.
ACTION_VERBS = [
    "achieved", "administered", "analyzed", "built", "collaborated",
    "created", "delivered", "designed", "developed", "directed",
    "engineered", "established", "executed", "generated", "implemented",
    "improved", "increased", "initiated", "launched", "led", "managed",
    "optimized", "organized", "planned", "produced", "reduced",
    "resolved", "spearheaded", "streamlined", "supervised", "trained",
]

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Matches common phone formats: (123) 456-7890, 123-456-7890, +1 123 456 7890 ...
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[\s.-]?)?(?:\(\d{2,4}\)[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}[\s.-]?\d{0,4}"
)

BULLET_PATTERN = re.compile(r"^\s*([•\-\*▪●‣]|(\d+[.)]))\s+", re.MULTILINE)


# ---------------------------------------------------------------------------
# Analysis engine
# ---------------------------------------------------------------------------

def find_sections(text_lower):
    """Return (found_sections, missing_sections) using heading aliases."""
    found = []
    for section_name, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            # Look for the alias as its own line/heading, or as a short
            # standalone phrase, so we don't false-positive on body text.
            pattern = r"(?m)^\s*" + re.escape(alias) + r"\s*:?\s*$"
            if re.search(pattern, text_lower):
                found.append(section_name)
                break
    missing = [s for s in SECTION_ALIASES if s not in found]
    return found, missing


def find_keywords(text_lower):
    """Return the keywords from KEYWORD_LIBRARY that appear in the resume."""
    found = []
    for kw in KEYWORD_LIBRARY:
        # Word-boundary match, case-insensitive. Keywords with symbols like
        # "C++" need a slightly relaxed boundary on the right-hand side.
        escaped = re.escape(kw.lower())
        pattern = r"(?<![a-zA-Z0-9])" + escaped + r"(?![a-zA-Z0-9])"
        if re.search(pattern, text_lower):
            found.append(kw)
    return found


def count_action_verbs(text_lower):
    """Count total occurrences of any known action verb (whole-word)."""
    total = 0
    for verb in ACTION_VERBS:
        matches = re.findall(r"\b" + re.escape(verb) + r"\b", text_lower)
        total += len(matches)
    return total


def calculate_score(stats, found_sections, keywords_found):
    """
    Heuristic 0-100 score built from weighted sub-scores.
    This is a simple rule-based estimate, NOT an AI hiring prediction.
    """
    score = 0

    # 1) Length: reward a substantial but not excessive resume (up to 20 pts)
    words = stats["words"]
    if words >= 250:
        score += 20
    elif words >= 120:
        score += 12
    elif words > 0:
        score += 5

    # 2) Important sections present (up to 25 pts, ~3.1 pts per key section)
    key_sections = ["Experience", "Education", "Skills", "Projects",
                     "Summary", "Certifications", "Achievements", "Contact"]
    present_key = [s for s in key_sections if s in found_sections]
    score += round(25 * (len(present_key) / len(key_sections)))

    # 3) Contact info found (up to 10 pts)
    if stats["emails"] > 0:
        score += 6
    if stats["phones"] > 0:
        score += 4

    # 4) Skills / keywords detected (up to 20 pts)
    score += min(20, len(keywords_found) * 2)

    # 5) Projects / experience shown via bullet points (up to 10 pts)
    if stats["bullets"] >= 6:
        score += 10
    elif stats["bullets"] >= 2:
        score += 6
    elif stats["bullets"] > 0:
        score += 3

    # 6) Action verbs (up to 15 pts)
    verbs = stats["action_verbs"]
    if verbs >= 10:
        score += 15
    elif verbs >= 5:
        score += 9
    elif verbs > 0:
        score += 4

    return max(0, min(100, score))


def build_suggestions(stats, found_sections, missing_sections, keywords_found):
    """Generate plain-language suggestions based on what's missing/weak."""
    suggestions = []

    if "Summary" not in found_sections and "Objective" not in found_sections:
        suggestions.append("Add a professional summary or objective near the top.")

    if "Skills" not in found_sections:
        suggestions.append("Add a Skills section listing your technical and soft skills.")

    if "Projects" not in found_sections and "Experience" not in found_sections:
        suggestions.append("Include projects or work experience to demonstrate practical ability.")

    if "Certifications" in missing_sections:
        suggestions.append("Add certifications if relevant to your field.")

    if "Achievements" in missing_sections:
        suggestions.append("Add measurable achievements (e.g. numbers, percentages, results).")

    if stats["emails"] == 0:
        suggestions.append("Include a professional email address so employers can reach you.")

    if stats["phones"] == 0:
        suggestions.append("Include a phone number in your contact details.")

    if stats["action_verbs"] < 5:
        suggestions.append("Your resume contains very few action verbs — start bullet points with words like 'led', 'built', or 'improved'.")

    if stats["bullets"] < 3:
        suggestions.append("Use more bullet points to make achievements easy to scan.")

    if len(keywords_found) < 4:
        suggestions.append("Add more relevant technical or professional keywords for your target role.")

    if stats["words"] < 150:
        suggestions.append("Your resume looks short — consider adding more detail about your experience.")
    elif stats["words"] > 900:
        suggestions.append("Your resume looks long — consider trimming it to keep it concise.")

    if not suggestions:
        suggestions.append("Great job! Your resume covers the essentials well.")

    return suggestions


def analyze_resume(text):
    """Run the full analysis pipeline and return a JSON-serializable dict."""
    text_lower = text.lower()

    stats = {
        "words": len(text.split()),
        "characters": len(text),
        "bullets": len(BULLET_PATTERN.findall(text)),
        "emails": len(EMAIL_PATTERN.findall(text)),
        "phones": len(PHONE_PATTERN.findall(text)),
    }

    found_sections, missing_sections = find_sections(text_lower)
    keywords_found = find_keywords(text_lower)
    stats["action_verbs"] = count_action_verbs(text_lower)
    stats["sections_found"] = len(found_sections)
    stats["skills_detected"] = len(keywords_found)

    score = calculate_score(stats, found_sections, keywords_found)
    suggestions = build_suggestions(stats, found_sections, missing_sections, keywords_found)

    return {
        "score": score,
        "stats": stats,
        "sections_found": found_sections,
        "sections_missing": missing_sections,
        "keywords_found": keywords_found,
        "suggestions": suggestions,
    }


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

class ResumeScannerHandler(BaseHTTPRequestHandler):
    """Serves the static frontend and handles the /scan analysis endpoint."""

    # Map of URL paths to (filename, content-type) for static assets.
    STATIC_FILES = {
        "/": ("index.html", "text/html"),
        "/index.html": ("index.html", "text/html"),
        "/style.css": ("style.css", "text/css"),
    }

    def do_GET(self):
        if self.path in self.STATIC_FILES:
            filename, content_type = self.STATIC_FILES[self.path]
            try:
                with open(filename, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except FileNotFoundError:
                self.send_error(404, f"{filename} not found")
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        if self.path == "/scan":
            try:
                length = int(self.headers.get("Content-Length", 0))
                raw_body = self.rfile.read(length)
                payload = json.loads(raw_body.decode("utf-8"))
                resume_text = payload.get("text", "")

                if not resume_text.strip():
                    self._send_json({"error": "No resume text provided."}, status=400)
                    return

                result = analyze_resume(resume_text)
                self._send_json(result, status=200)
            except Exception as exc:  # keep the server alive on bad input
                self._send_json({"error": f"Failed to analyze resume: {exc}"}, status=500)
        else:
            self.send_error(404, "Not found")

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Slightly quieter console output than the default.
        print(f"[{self.log_date_time_string()}] {format % args}")


def run():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, ResumeScannerHandler)
    print(f"Resume Scanner running at http://localhost:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        httpd.server_close()


if __name__ == "__main__":
    run()
