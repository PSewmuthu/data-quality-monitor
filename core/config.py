'''
config.py - Data Quality Standards & Thresholds
Defines acceptable thresholds per dimension, per dataset.
'''

# ======================================================================================================
#  Global Quality Thresholds (0-100 score)
# ======================================================================================================
THRESHOLDS = {
    "completeness":  {"critical": 70, "warning": 85, "good": 95},
    "uniqueness":    {"critical": 90, "warning": 95, "good": 99},
    "validity":      {"critical": 75, "warning": 88, "good": 96},
    "consistency":   {"critical": 70, "warning": 85, "good": 95},
    "timeliness":    {"critical": 60, "warning": 80, "good": 92},
    "accuracy":      {"critical": 80, "warning": 90, "good": 97}
}

OVERALL_THRESHOLD = {"critical": 75, "warning": 85, "good": 93}


# ======================================================================================================
#  Dataset Schemas (column -> rules)
# ======================================================================================================
SCHEMAS = {
    "candidates": {
        "primary_key": "candidate_id",
        "date_columns": ["applied_date"],
        "columns": {
            "candidate_id":      {"required": True,  "type": "string", "pattern": r"^C\d{4}$"},
            "first_name":        {"required": True,  "type": "string"},
            "last_name":         {"required": True,  "type": "string"},
            "email":             {"required": True,  "type": "email"},
            "phone":             {"required": False, "type": "phone_lk"},
            "district":          {"required": False, "type": "categorical",
                                  "allowed": ["Colombo", "Gampaha", "Kandy", "Galle", "Matara",
                                              "Kurunegala", "Ratnapura", "Anuradhapura", "Badulla",
                                              "Batticaloa", "Hambantota", "Jaffna", "Kalutara",
                                              "Kegalle", "Kilinochchi", "Mannar", "Matale", "Monaragala",
                                              "Mullaitivu", "Nuwara Eliya", "Polonnaruwa", "Puttalam",
                                              "Trincomalee", "Vavuniya"]},
            "years_experience":  {"required": True,  "type": "numeric", "min": 0, "max": 50},
            "salary_expectation": {"required": False, "type": "numeric", "min": 20000, "max": 1000000},
            "skills":            {"required": False, "type": "string"},
            "applied_date":      {"required": True,  "type": "date"},
            "status":            {"required": True,  "type": "categorical",
                                  "allowed": ["Applied", "Screened", "Interview", "Offered", "Hired", "Rejected"]},
            "job_title_applied": {"required": True,  "type": "string"},
            "sector":            {"required": False, "type": "string"},
        },
        "cross_field_rules": [
            # (description, lambda that returns True if OK)
        ]
    },
    "job_postings": {
        "primary_key": "job_id",
        "date_columns": ["posted_date", "closing_date"],
        "columns": {
            "job_id":             {"required": True,  "type": "string", "pattern": r"^J\d{3}$"},
            "title":              {"required": True,  "type": "string"},
            "sector":             {"required": True,  "type": "string"},
            "min_experience":     {"required": True,  "type": "numeric", "min": 0, "max": 40},
            "max_experience":     {"required": False, "type": "numeric", "min": 0, "max": 50},
            "min_salary":         {"required": True,  "type": "numeric", "min": 10000, "max": 5000000},
            "max_salary":         {"required": False, "type": "numeric", "min": 10000, "max": 5000000},
            "posted_date":        {"required": True,  "type": "date"},
            "closing_date":       {"required": True,  "type": "date"},
            "district":           {"required": False, "type": "string"},
            "is_active":          {"required": True,  "type": "boolean"},
            "applications_count": {"required": False, "type": "numeric", "min": 0, "max": 10000},
        }
    },
    "applications": {
        "primary_key": "application_id",
        "date_columns": ["application_date"],
        "foreign_keys": {
            "candidate_id": "candidates.candidate_id",
            "job_id":       "job_postings.job_id",
        },
        "columns": {
            "application_id":  {"required": True, "type": "string"},
            "candidate_id":    {"required": True, "type": "string"},
            "job_id":          {"required": True, "type": "string"},
            "application_date": {"required": True, "type": "date"},
            "stage":           {"required": True, "type": "categorical",
                                "allowed": ["Applied", "Screened", "Interview", "Offered", "Hired", "Rejected"]},
        }
    }
}


# ======================================================================================================
#  Alert Rules
# ======================================================================================================
ALERT_RULES = [
    {"name": "Critical Overall Score",
        "condition": "overall_score < 75",     "severity": "CRITICAL"},
    {"name": "High Duplicate Rate",
        "condition": "uniqueness_score < 90",   "severity": "HIGH"},
    {"name": "Missing Key Fields",
        "condition": "completeness_score < 85", "severity": "HIGH"},
    {"name": "Invalid Formats",
        "condition": "validity_score < 88",     "severity": "MEDIUM"},
    {"name": "Stale Data",
        "condition": "timeliness_score < 80",   "severity": "MEDIUM"},
    {"name": "Consistency Drift",
        "condition": "consistency_score < 85",  "severity": "MEDIUM"},
]
