"""
Step 2: Get the full description of every job in jobs.csv, then count
which skills employers ask for most often.

Install first:  pip install requests pandas matplotlib
Run:            python extract_skills.py

Creates:
  jobs_with_descriptions.csv  - your jobs plus their full description text
  skills.csv                  - each skill and how many jobs mention it
  top_skills.png              - a bar chart of the top 20 skills
"""

import base64
import os
import re
import time

import matplotlib.pyplot as plt
import pandas as pd
import requests

# Search uses v6, but the job details endpoint is still v4.
# It wants the reference number base64-encoded.
DETAILS_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobdetails/"
HEADERS = {"X-API-Key": "jobboerse-jobsuche", "Accept": "application/json"}

# Skill name -> regex pattern. \b means "word boundary", so "R" won't match inside "Rust".
SKILLS = {
    "Python": r"\bpython\b",
    "SQL": r"\bsql\b",
    "R": r"\bR\b",  # case-sensitive, handled below
    "Java": r"\bjava\b(?!script)",
    "Scala": r"\bscala\b",
    "JavaScript": r"\bjavascript\b",
    "C++": r"c\+\+",
    "Excel": r"\bexcel\b",
    "Power BI": r"\bpower\s?bi\b",
    "Tableau": r"\btableau\b",
    "Spark": r"\b(?:py)?spark\b",
    "Hadoop": r"\bhadoop\b",
    "Kafka": r"\bkafka\b",
    "Airflow": r"\bairflow\b",
    "dbt": r"\bdbt\b",
    "Databricks": r"\bdatabricks\b",
    "Snowflake": r"\bsnowflake\b",
    "AWS": r"\baws\b|amazon web services",
    "Azure": r"\bazure\b",
    "GCP": r"\bgcp\b|google cloud",
    "Docker": r"\bdocker\b",
    "Kubernetes": r"\bkubernetes\b|\bk8s\b",
    "Git": r"\bgit\b",
    "Linux": r"\blinux\b",
    "Pandas": r"\bpandas\b",
    "NumPy": r"\bnumpy\b",
    "scikit-learn": r"scikit[\s-]?learn|\bsklearn\b",
    "TensorFlow": r"\btensorflow\b",
    "PyTorch": r"\bpytorch\b",
    "Machine Learning": r"machine learning|maschinelles lernen",
    "Deep Learning": r"deep learning",
    "NLP": r"\bnlp\b|natural language processing",
    "LLM / GenAI": r"\bllms?\b|large language model|generative ai|\bgenai\b",
    "Statistics": r"statisti",  # matches statistics, Statistik, statistical...
    "SAP": r"\bsap\b",
    "ETL": r"\betl\b|\belt\b",
    "MLOps": r"\bmlops\b",
    "English": r"\benglisch|\benglish\b",
    "German": r"\bdeutsch|\bgerman\b",
}


def fetch_description(refnr):
    """Get the full job description text for one reference number."""
    encoded = base64.b64encode(refnr.encode()).decode()
    response = requests.get(DETAILS_URL + encoded, headers=HEADERS, timeout=30)
    if response.status_code != 200:
        return None
    return response.json().get("stellenangebotsBeschreibung")


def find_skills(text):
    """Return the set of skills mentioned in a description."""
    if not isinstance(text, str):
        return set()
    found = set()
    for skill, pattern in SKILLS.items():
        flags = 0 if skill == "R" else re.IGNORECASE
        if re.search(pattern, text, flags):
            found.add(skill)
    return found


# --- 1. Download descriptions (only for jobs we don't have yet) ---
df = pd.read_csv("jobs.csv")

known = {}
if os.path.exists("jobs_with_descriptions.csv"):
    old = pd.read_csv("jobs_with_descriptions.csv")
    known = dict(zip(old["refnr"], old["description"]))

missing = [r for r in df["refnr"] if not isinstance(known.get(r), str)]
print(f"{len(df) - len(missing)} descriptions already downloaded, {len(missing)} to download.")
for i, refnr in enumerate(missing, start=1):
    known[refnr] = fetch_description(refnr)
    if i % 25 == 0:
        print(f"Downloaded {i}/{len(missing)} descriptions...")
    time.sleep(0.5)  # be polite to the server

df["description"] = df["refnr"].map(known)
df.to_csv("jobs_with_descriptions.csv", index=False, encoding="utf-8-sig")
print(f"Saved descriptions for {df['description'].notna().sum()} of {len(df)} jobs.")

# --- 2. Count skills ---
df = df[df["description"].notna()].copy()
df["skills"] = df["description"].apply(find_skills)

counts = pd.Series([s for skills in df["skills"] for s in skills]).value_counts()
skills_df = counts.rename_axis("skill").reset_index(name="jobs")
skills_df["percent_of_jobs"] = (skills_df["jobs"] / len(df) * 100).round(1)
skills_df.to_csv("skills.csv", index=False)

print(f"\nTop 20 skills across {len(df)} jobs:")
print(skills_df.head(20).to_string(index=False))

# --- 3. Chart ---
top = skills_df.head(20).iloc[::-1]  # reverse so the biggest bar is on top
plt.figure(figsize=(9, 7))
plt.barh(top["skill"], top["percent_of_jobs"], color="#4C72B0")
plt.xlabel("% of job postings that mention the skill")
plt.title(f"Most requested skills in {len(df)} data job postings")
plt.tight_layout()
plt.savefig("top_skills.png", dpi=150)
print("\nChart saved to top_skills.png")
