# 📊 Data Job Market Analyzer

**Which skills do employers in Germany ask for in data jobs, and how is that different for students?**

I built this project while looking for a working student job or internship in data science. It collects
real job postings from the official job board of the German Federal Employment Agency (Bundesagentur für Arbeit),
extracts the skills from each description, and shows the results in an interactive dashboard.

🔗 **Live dashboard:** _add your Streamlit link here_

![Dashboard screenshot](screenshot.png)

## Key findings (539 postings, November 2026)

Based on 118 student jobs (working student, internship, thesis) and 302 full-time jobs in Germany:

| Skill | Student jobs | Full-time jobs |
|---|---|---|
| German | 78% | 80% |
| English | 75% | 60% |
| Python | 64% | 62% |
| Machine Learning | 43% | 30% |
| SQL | 29% | 52% |
| LLM / GenAI | 23% | 18% |
| Azure | 5% | 23% |

- **Languages matter most.** German is required in almost 4 out of 5 postings, more often than any technical skill.
- **Python is the #1 technical skill** for both students and full-time roles.
- **Student roles focus more on ML and GenAI**, while full-time roles ask much more for SQL and cloud
  platforms (Azure, AWS). Companies seem to expect students to learn the production stack on the job.
- **Only 12% of student postings mention home office.**

## How it works

```
Bundesagentur für Arbeit API ──► collect_jobs.py ──► jobs.csv
                                                        │
                    job details API ──► extract_skills.py ──► jobs_with_descriptions.csv, skills.csv
                                                        │
                                                   app.py (Streamlit dashboard)
```

1. **`collect_jobs.py`**: searches the job API (v6) for data roles: full-time jobs, working student jobs and
   internships, and classifies each posting by job type.
2. **`extract_skills.py`**: downloads the full description of every job (only the ones not downloaded yet)
   and detects about 40 skills with regular expressions (handling cases like "Java" vs "JavaScript" and "R" vs "Rust").
3. **`app.py`**: an interactive Streamlit dashboard with filters for job type, country and role, a skills-by-role
   heatmap, a comparison of student and full-time jobs, top cities, and a searchable job table.

## Run it locally

```bash
pip install -r requirements.txt
python collect_jobs.py      # ~1 minute
python extract_skills.py    # ~5 minutes the first time
streamlit run app.py
```

## Tech stack

Python · pandas · requests · REST APIs · regex · Plotly · Streamlit

## Limitations and next steps

- Skill detection uses keyword matching, so it can't tell "required" from "nice to have". A next step would be
  an NLP or LLM-based extraction.
- Only a few postings include pay, so the salary numbers are rough.
- Next: collect data every week to show trends over time.
