"""
Step 3: Interactive web dashboard for the job market analysis.

Install first:  pip install streamlit plotly pandas
Run:            streamlit run app.py
(Keep this file in the same folder as jobs_with_descriptions.csv.)
"""

import re

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Data Job Market Analyzer", page_icon="📊", layout="wide")

BLUE = "#2a78d6"
BLUE_SCALE = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#104281"]  # light -> dark

# Same skill list as extract_skills.py
SKILLS = {
    "Python": r"\bpython\b", "SQL": r"\bsql\b", "R": r"\bR\b", "Java": r"\bjava\b(?!script)",
    "Scala": r"\bscala\b", "JavaScript": r"\bjavascript\b", "C++": r"c\+\+", "Excel": r"\bexcel\b",
    "Power BI": r"\bpower\s?bi\b", "Tableau": r"\btableau\b", "Spark": r"\b(?:py)?spark\b",
    "Hadoop": r"\bhadoop\b", "Kafka": r"\bkafka\b", "Airflow": r"\bairflow\b", "dbt": r"\bdbt\b",
    "Databricks": r"\bdatabricks\b", "Snowflake": r"\bsnowflake\b",
    "AWS": r"\baws\b|amazon web services", "Azure": r"\bazure\b", "GCP": r"\bgcp\b|google cloud",
    "Docker": r"\bdocker\b", "Kubernetes": r"\bkubernetes\b|\bk8s\b", "Git": r"\bgit\b",
    "Linux": r"\blinux\b", "Pandas": r"\bpandas\b", "NumPy": r"\bnumpy\b",
    "scikit-learn": r"scikit[\s-]?learn|\bsklearn\b", "TensorFlow": r"\btensorflow\b",
    "PyTorch": r"\bpytorch\b", "Machine Learning": r"machine learning|maschinelles lernen",
    "Deep Learning": r"deep learning", "NLP": r"\bnlp\b|natural language processing",
    "LLM / GenAI": r"\bllms?\b|large language model|generative ai|\bgenai\b",
    "Statistics": r"statisti", "SAP": r"\bsap\b", "ETL": r"\betl\b|\belt\b", "MLOps": r"\bmlops\b",
    "English": r"\benglisch|\benglish\b", "German": r"\bdeutsch|\bgerman\b",
}

AUSTRIA = {"WIEN", "NIEDEROESTERREICH", "OBEROESTERREICH", "STEIERMARK", "KAERNTEN",
           "TIROL", "VORARLBERG", "SALZBURG", "BURGENLAND"}
SWITZERLAND = {"ZUERICH", "ZENTRALSCHWEIZ", "NORDWESTSCHWEIZ_MIT_BASEL", "OSTSCHWEIZ",
               "ESPACE_MITTELLAND_WESTSCHWEIZ_MIT_BERN", "GENFERSEE_REGION", "TESSIN"}


def get_country(row):
    city, region = str(row["city"]), row["region"]
    if region in AUSTRIA or str(row["refnr"]).startswith("11949-") or "Österreich" in city \
            or city.startswith(("Bundesland:", "Bezirk:")):
        return "Austria"
    if region in SWITZERLAND:
        return "Switzerland"
    if region == "SONSTIGES":
        return "Other"
    return "Germany"


# Titles that look like data / AI work (used by the "Only data & AI titles" switch)
RELEVANT_TITLE = r"data|daten|analy|\bki\b|ki-|\bai\b|machine|learning|intelligen|scien|\bbi\b|statist|llm|genai|python|agent|\brag\b"


def job_type(title, current):
    """Same rules as collect_jobs.py, applied again so older CSV files get the fixes too."""
    t = str(title).lower()
    if any(w in t for w in ["werkstudent", "werksstudent", "werkstudium", "working student",
                            "studentische", "studentenjob"]):
        return "Working student"
    if any(w in t for w in ["abschlussarbeit", "masterarbeit", "bachelorarbeit", "thesis",
                            "bachelorand", "masterand"]):
        return "Thesis"
    return current


def find_skills(text):
    if not isinstance(text, str):
        return []
    return [s for s, p in SKILLS.items()
            if re.search(p, text, 0 if s == "R" else re.IGNORECASE)]


@st.cache_data
def load_data():
    df = pd.read_csv("jobs_with_descriptions.csv")
    df["country"] = df.apply(get_country, axis=1)
    df["role"] = df["search_keyword"]
    if "job_type" not in df.columns:  # data collected with the old version of collect_jobs.py
        df["job_type"] = "Full-time"
    df["job_type"] = [job_type(t, c) for t, c in zip(df["title"], df["job_type"])]
    df["relevant"] = df["title"].str.contains(RELEVANT_TITLE, case=False, regex=True, na=False)
    df["skills"] = df["description"].apply(find_skills)
    df["city_clean"] = df["city"].str.split(",").str[0].str.strip()
    # Only yearly salaries are comparable (some ads give hourly or monthly pay)
    mid = (df["salary_from"] + df["salary_to"]) / 2
    df["yearly_salary_mid"] = mid.where(df["salary_from"] >= 20000)
    df["hourly_pay_mid"] = mid.where(df["salary_from"].between(10, 100))
    df["link"] = "https://www.arbeitsagentur.de/jobsuche/jobdetail/" + df["refnr"]
    return df


df = load_data()

# ---------------- Header & filters ----------------
st.title("📊 Data Job Market Analyzer")
st.caption("Which skills do employers in the DACH region ask for - in full-time jobs, "
           "working student jobs and internships? "
           "Based on live postings from the Bundesagentur für Arbeit job search API.")

f1, f2, f3 = st.columns(3)
TYPE_ORDER = ["Working student", "Internship", "Thesis", "Full-time"]
types_available = [t for t in TYPE_ORDER if t in set(df["job_type"])]
student_types = [t for t in types_available if t != "Full-time"]
job_types = f1.multiselect("Job type", types_available, default=student_types or types_available)
countries = f2.multiselect("Country", sorted(df["country"].unique()), default=["Germany"])
roles = f3.multiselect("Role", sorted(df["role"].unique()), default=sorted(df["role"].unique()))

only_relevant = st.toggle("Only data & AI job titles", value=True,
                          help="Hides postings the search returned that aren't really data jobs, "
                               "e.g. 'Praktikum energiewirtschaftliche Prüfung'")

base = df[df["country"].isin(countries) & df["role"].isin(roles)]
if only_relevant:
    base = base[base["relevant"]]
data = base[base["job_type"].isin(job_types)]
if data.empty:
    st.warning("No jobs match these filters.")
    st.stop()

# ---------------- KPI row ----------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Job postings", len(data))
k2.metric("Employers", data["employer"].nunique())
ho_known = data["home_office"].dropna()
k3.metric("Home office possible", f"{(ho_known == True).mean():.0%}" if len(ho_known) else "n/a",
          help="Share of postings that state whether home office is possible")
if "Full-time" in job_types:
    salaries = data["yearly_salary_mid"].dropna()
    k4.metric("Median salary (yearly)", f"€{salaries.median():,.0f}" if len(salaries) else "n/a",
              help=f"Only {len(salaries)} postings include a yearly salary range")
else:
    hourly = data["hourly_pay_mid"].dropna()
    k4.metric("Median pay (per hour)", f"€{hourly.median():,.2f}" if len(hourly) else "n/a",
              help=f"Only {len(hourly)} postings include an hourly pay range")

# ---------------- Skills chart ----------------
skill_counts = pd.Series([s for skills in data["skills"] for s in skills]).value_counts()
top = (skill_counts / len(data) * 100).round(1).head(20).rename_axis("Skill").reset_index(name="% of jobs")

st.subheader("Most requested skills")
fig = px.bar(top.iloc[::-1], x="% of jobs", y="Skill", orientation="h",
             color_discrete_sequence=[BLUE], text="% of jobs")
fig.update_traces(texttemplate="%{text}%", textposition="outside", cliponaxis=False,
                  hovertemplate="%{y}: %{x}% of jobs<extra></extra>")
fig.update_layout(height=560, margin=dict(l=0, r=40, t=10, b=0), bargap=0.25,
                  xaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.15)", title="% of job postings"),
                  yaxis_title=None)
st.plotly_chart(fig, width="stretch")

# ---------------- Skills by role (heatmap) ----------------
st.subheader("Skills by role")
top_skills = skill_counts.head(15).index.tolist()
rows = []
for role, group in data.groupby("role"):
    for skill in top_skills:
        rows.append({"Role": role, "Skill": skill,
                     "% of jobs": round(group["skills"].apply(lambda s: skill in s).mean() * 100)})
matrix = pd.DataFrame(rows).pivot(index="Role", columns="Skill", values="% of jobs")[top_skills]
heat = px.imshow(matrix, color_continuous_scale=BLUE_SCALE, text_auto=True, aspect="auto",
                 labels=dict(color="% of jobs"))
heat.update_traces(hovertemplate="%{y} · %{x}: %{z}% of jobs<extra></extra>")
heat.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), xaxis_title=None, yaxis_title=None)
st.plotly_chart(heat, width="stretch")

# ---------------- Student vs full-time ----------------
students = base[base["job_type"] != "Full-time"]
fulltime = base[base["job_type"] == "Full-time"]
if len(students) and len(fulltime):
    st.subheader("Student jobs vs full-time jobs")
    st.caption(f"Share of postings that mention each skill: {len(students)} student jobs "
               f"(working student, internship, thesis) vs {len(fulltime)} full-time jobs")

    def skill_share(frame):
        return frame["skills"].apply(lambda s: pd.Series({k: k in s for k in SKILLS})).mean() * 100

    comp = pd.DataFrame({"Student jobs": skill_share(students), "Full-time jobs": skill_share(fulltime)})
    comp = comp.loc[comp.max(axis=1).sort_values(ascending=False).index[:12]].round(0)
    long = comp.rename_axis("Skill").reset_index().melt(id_vars="Skill", var_name="Type", value_name="% of jobs")
    comp_fig = px.bar(long, x="Skill", y="% of jobs", color="Type", barmode="group",
                      color_discrete_map={"Student jobs": BLUE, "Full-time jobs": "#eb6834"})
    comp_fig.update_traces(hovertemplate="%{x}: %{y:.0f}%<extra>%{fullData.name}</extra>")
    comp_fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0), bargap=0.25, bargroupgap=0.08,
                           legend=dict(orientation="h", y=1.08, x=0, title=None), xaxis_title=None,
                           yaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.15)"))
    st.plotly_chart(comp_fig, width="stretch")

# ---------------- Cities ----------------
st.subheader("Top cities")
cities = data["city_clean"].value_counts().head(10).rename_axis("City").reset_index(name="Jobs")
city_fig = px.bar(cities.iloc[::-1], x="Jobs", y="City", orientation="h",
                  color_discrete_sequence=[BLUE], text="Jobs")
city_fig.update_traces(textposition="outside", cliponaxis=False,
                       hovertemplate="%{y}: %{x} jobs<extra></extra>")
city_fig.update_layout(height=380, margin=dict(l=0, r=30, t=10, b=0), bargap=0.25,
                       xaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.15)"), yaxis_title=None)
st.plotly_chart(city_fig, width="stretch")

# ---------------- Job table ----------------
st.subheader("Browse the jobs")
skill_filter = st.multiselect("Show only jobs that mention these skills", sorted(SKILLS))
table = data[data["skills"].apply(lambda s: all(x in s for x in skill_filter))]
st.dataframe(
    table[["title", "employer", "city_clean", "job_type", "role", "published", "link"]]
    .rename(columns={"city_clean": "city", "job_type": "type"}),
    column_config={"link": st.column_config.LinkColumn("Posting", display_text="Open")},
    hide_index=True, width="stretch",
)
st.caption(f"{len(table)} jobs shown")
