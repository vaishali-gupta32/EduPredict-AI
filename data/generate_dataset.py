"""
Synthetic Dataset Generator
Generates a realistic 2000-student dataset for training the ML models.
Features are correlated so that low attendance + high backlogs → "At Risk".

Run: python data/generate_dataset.py
Output: data/students.csv
"""

import numpy as np
import pandas as pd
import os
import random

random.seed(42)
np.random.seed(42)

N = 2000
DEPARTMENTS = ["CS", "ECE", "ME", "CE", "IT", "EE", "MBA"]
GENDERS = ["Male", "Female", "Other"]

def generate_dataset():
    records = []

    for i in range(N):
        sid = f"STU-{2022 + (i // 500)}-{i+1:04d}"
        age = np.random.randint(18, 28)
        gender = np.random.choice(GENDERS, p=[0.55, 0.42, 0.03])
        department = np.random.choice(DEPARTMENTS)
        semester = np.random.randint(1, 9)
        financial_aid = np.random.choice([True, False], p=[0.3, 0.7])

        # ── Risk profile assignment (hidden label driver) ──────────────
        risk_profile = np.random.choice(["high", "medium", "low"], p=[0.25, 0.40, 0.35])

        if risk_profile == "low":
            attendance_pct       = np.clip(np.random.normal(85, 8),  60, 100)
            assignment_score_avg = np.clip(np.random.normal(78, 8),  50, 100)
            internal_marks_avg   = np.clip(np.random.normal(76, 8),  50, 100)
            semester_gpa         = np.clip(np.random.normal(8.2, 0.7), 6.0, 10.0)
            study_hours          = np.clip(np.random.normal(22, 5),  10, 50)
            participation_score  = np.clip(np.random.normal(7.5, 1.2), 4, 10)
            prev_semester_gpa    = np.clip(semester_gpa + np.random.normal(0, 0.3), 5.0, 10.0)
            backlogs             = np.random.choice([0, 1], p=[0.92, 0.08])

        elif risk_profile == "medium":
            attendance_pct       = np.clip(np.random.normal(72, 10), 50, 90)
            assignment_score_avg = np.clip(np.random.normal(62, 10), 40, 85)
            internal_marks_avg   = np.clip(np.random.normal(60, 10), 40, 82)
            semester_gpa         = np.clip(np.random.normal(6.5, 0.8), 4.5, 8.5)
            study_hours          = np.clip(np.random.normal(14, 5),  5, 30)
            participation_score  = np.clip(np.random.normal(5.5, 1.5), 2, 8)
            prev_semester_gpa    = np.clip(semester_gpa + np.random.normal(-0.2, 0.4), 4.0, 9.0)
            backlogs             = np.random.choice([0, 1, 2, 3], p=[0.50, 0.30, 0.15, 0.05])

        else:  # high risk
            attendance_pct       = np.clip(np.random.normal(50, 12), 20, 75)
            assignment_score_avg = np.clip(np.random.normal(44, 12), 20, 65)
            internal_marks_avg   = np.clip(np.random.normal(42, 12), 20, 62)
            semester_gpa         = np.clip(np.random.normal(4.2, 1.0), 2.0, 6.5)
            study_hours          = np.clip(np.random.normal(7, 4),   1, 20)
            participation_score  = np.clip(np.random.normal(3.2, 1.5), 0, 6)
            prev_semester_gpa    = np.clip(semester_gpa + np.random.normal(-0.5, 0.5), 2.0, 7.5)
            backlogs             = np.random.choice([0, 1, 2, 3, 4, 5], p=[0.10, 0.15, 0.20, 0.25, 0.20, 0.10])

        # ── Derive performance category label ─────────────────────────
        score = (
            0.30 * (attendance_pct / 100) +
            0.20 * (semester_gpa / 10) +
            0.15 * (assignment_score_avg / 100) +
            0.15 * (internal_marks_avg / 100) +
            0.10 * (study_hours / 50) +
            0.10 * max(0, (1 - backlogs / 5))
        )

        if score >= 0.68:
            performance_category = "High"
        elif score >= 0.48:
            performance_category = "Medium"
        else:
            performance_category = "At Risk"

        records.append({
            "student_id":           sid,
            "age":                  age,
            "gender":               gender,
            "department":           department,
            "semester":             semester,
            "attendance_pct":       round(attendance_pct, 2),
            "assignment_score_avg": round(assignment_score_avg, 2),
            "internal_marks_avg":   round(internal_marks_avg, 2),
            "semester_gpa":         round(semester_gpa, 2),
            "study_hours_per_week": round(study_hours, 1),
            "participation_score":  round(participation_score, 2),
            "prev_semester_gpa":    round(prev_semester_gpa, 2),
            "backlogs":             int(backlogs),
            "financial_aid":        financial_aid,
            "performance_category": performance_category,
        })

    df = pd.DataFrame(records)

    os.makedirs("data", exist_ok=True)
    df.to_csv("data/students.csv", index=False)

    # Print distribution summary
    print(f"✅ Generated {N} student records → data/students.csv")
    print("\nPerformance Category Distribution:")
    print(df["performance_category"].value_counts())
    print("\nSample records:")
    print(df.head(3).to_string())
    return df


if __name__ == "__main__":
    generate_dataset()
