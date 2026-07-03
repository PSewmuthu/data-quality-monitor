'''
Generate sample data for testing and development purposes.
Intentionally injects quality issues to simulate real-world data challenges.
'''
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import random
import os

random.seed(42)
np.random.seed(42)


def random_date(start_days_ago=365, end_days_ago=0):
    delta = random.randint(end_days_ago, start_days_ago)

    return (datetime.now() - timedelta(days=delta)).strftime('%Y-%m-%d')


FIRST_NAMES = ["Kasun", "Nimali", "Ruwan", "Sandya", "Thilina", "Malsha", "Dinesh", "Priya", "Saman", "Amali",
               "Chathura", "Dilini", "Nuwan", "Shamali", "Tharaka", "Buddhika", "Chamara", "Nadeeka", "Suresh", "Lakmali"]
LAST_NAMES = ["Perera", "Silva", "Fernando", "Jayawardena", "Wickramasinghe", "De Silva", "Gunawardena",
              "Dissanayake", "Rajapaksa", "Herath", "Senanayake", "Amarasinghe", "Bandara", "Ranasinghe"]
SKILLS_POOL = ["Python", "Java", "SQL", "Excel", "Power BI", "Machine Learning", "Data Analysis",
               "Tableau", "JavaScript", "Project Management", "Communication", "R", "AWS", "Docker", "Agile"]
JOB_TITLES = ["Data Analyst", "Software Engineer", "HR Manager", "Marketing Specialist", "Business Analyst",
              "Data Scientist", "IT Support", "Finance Manager", "Sales Executive", "Operations Manager"]
SECTORS = ["IT", "Finance", "Healthcare", "Marketing",
           "Manufacturing", "Retail", "Logistics", "Education"]
STATUSES = ["Applied", "Screened", "Interview", "Offered", "Hired", "Rejected"]
DISTRICTS = ["Colombo", "Gampaha", "Kandy", "Galle",
             "Matara", "Kurunegala", "Ratnapura", "Anuradhapura"]


def generate_candidates(n=300):
    records = []

    for i in range(1, n + 1):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        experience = round(random.gauss(5, 3), 1)
        sallary = random.randint(40, 300) * 1000

        # Inject quality issues
        inject = random.random()

        if inject < 0.04:   # 4% duplicates
            cid = f"C{random.randint(1, i-1):04d}" if i > 1 else f"C{i:04d}"
        else:
            cid = f"C{i:04d}"

        email = f"{first_name.lower()}.{last_name.lower()}@email.com" if inject > 0.06 else (
            "invalid email" if inject < 0.02 else None)  # 2% invalid, 2% missing

        phone = f"07{random.randint(10000000, 99999999)}" if inject > 0.08 else (
            "12345" if inject < 0.04 else None)  # 4% short/invalid, 4% missing

        # 3% missing, 2% negative
        experience = None if inject < 0.03 else (
            -2 if inject < 0.05 else experience)

        sallary = None if inject < 0.04 else (
            9999999 if inject < 0.06 else sallary)  # 4% missing, 2% outlier

        applied_date = random_date(400, 0) if inject > 0.07 else (
            "2045-01-01" if inject < 0.03 else None)  # 3% future date, 4% missing

        skills_n = random.randint(2, 6)
        skills = ", ".join(random.sample(SKILLS_POOL, skills_n)
                           ) if inject > 0.05 else None  # 5% missing

        records.append({
            "candidate_id": cid,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "district": random.choice(DISTRICTS),
            "years_experience": experience,
            "salary_expectation": sallary,
            "skills": skills,
            "applied_date": applied_date,
            "status": random.choice(STATUSES),
            "job_title_applied": random.choice(JOB_TITLES),
            "sector": random.choice(SECTORS)
        })

        return pd.DataFrame(records)
