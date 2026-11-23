"""
Step 1: Collect job postings from the Bundesagentur für Arbeit job search API (v6).
Collects full-time jobs, working student jobs (Werkstudent) and internships.
Saves the results to jobs.csv.

Install first:  pip install requests pandas
Run:            python collect_jobs.py
"""

import time
import requests
import pandas as pd

# The old /pc/v4/jobs endpoint was shut down (it returns 403). v6 is the current one.
URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs"
HEADERS = {"X-API-Key": "jobboerse-jobsuche", "Accept": "application/json"}

# Job titles to search for - change these to whatever you like
KEYWORDS = ["Data Scientist", "Data Analyst", "Data Engineer", "Machine Learning"]

# angebotsart: 1 = regular job, 34 = internship (Praktikum/Trainee)
SEARCHES = []
for kw in KEYWORDS:
    SEARCHES.append({"role": kw, "was": kw, "angebotsart": 1})                  # full-time jobs
    SEARCHES.append({"role": kw, "was": f"Werkstudent {kw}", "angebotsart": 1}) # working student
    SEARCHES.append({"role": kw, "was": kw, "angebotsart": 34})                 # internships


def job_type(title, angebotsart):
    """Classify a posting as Working student, Internship, Thesis or Full-time."""
    t = (title or "").lower()
    if any(w in t for w in ["werkstudent", "werksstudent", "werkstudium", "working student",
                            "studentische", "studentenjob"]):
        return "Working student"
    if any(w in t for w in ["abschlussarbeit", "masterarbeit", "bachelorarbeit", "thesis",
                            "bachelorand", "masterand"]):
        return "Thesis"
    if angebotsart == 34 or any(w in t for w in ["praktik", "intern ", "internship"]):
        return "Internship"
    return "Full-time"


def first_location(job):
    """Return the address of the first workplace listed for a job (or an empty dict)."""
    locations = job.get("stellenlokationen") or []
    if locations:
        return locations[0].get("adresse") or {}
    return {}


def fetch_jobs(search, pages=2, size=50):
    """Fetch a few pages of jobs for one search."""
    jobs = []
    for page in range(1, pages + 1):
        params = {"was": search["was"], "angebotsart": search["angebotsart"],
                  "page": page, "size": size}
        response = requests.get(URL, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        results = response.json().get("ergebnisliste") or []
        if not results:
            break
        for job in results:
            address = first_location(job)
            title = job.get("stellenangebotsTitel")
            jobs.append({
                "search_keyword": search["role"],
                "job_type": job_type(title, search["angebotsart"]),
                "title": title,
                "employer": job.get("firma"),
                "city": address.get("ort"),
                "region": address.get("region"),
                "published": (job.get("veroeffentlichungszeitraum") or {}).get("von"),
                "home_office": job.get("homeofficemoeglich"),
                "salary_from": job.get("gehaltsspanneVon"),
                "salary_to": job.get("gehaltsspanneBis"),
                "refnr": job.get("referenznummer"),  # unique ID, used later for full descriptions
            })
        time.sleep(1)  # be polite to the server
    return jobs


all_jobs = []
for s in SEARCHES:
    print(f"Searching: {s['was']} ({'internship' if s['angebotsart'] == 34 else 'job'})")
    all_jobs.extend(fetch_jobs(s))

df = pd.DataFrame(all_jobs).drop_duplicates(subset="refnr")
df.to_csv("jobs.csv", index=False, encoding="utf-8-sig")  # utf-8-sig so Excel shows ä/ö/ü correctly

print(f"\nSaved {len(df)} jobs to jobs.csv")
print("\nJobs by type:")
print(df["job_type"].value_counts())
print("\nStudent jobs and internships by role:")
student = df[df["job_type"] != "Full-time"]
print(pd.crosstab(student["search_keyword"], student["job_type"]))
