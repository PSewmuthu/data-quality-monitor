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
