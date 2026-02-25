"""
Rule-based intervention recommendation mapper.
Maps feature values and prediction outputs to actionable intervention strings.
Ordered by severity — highest priority interventions appear first.
"""

from models.schemas import StudentInput


RULES = [
    # (condition_fn, intervention_string)
    (lambda s, p: p >= 0.70,           "Dropout Prevention Committee Review"),
    (lambda s, p: s.get("backlogs", 0) >= 3,      "Mandatory Counseling Session"),
    (lambda s, p: s.get("attendance_pct", 100) < 50,  "Attendance Warning Letter"),
    (lambda s, p: s.get("semester_gpa", 10) < 4.5,   "Academic Support Program"),
    (lambda s, p: s.get("study_hours_per_week", 10) < 5, "Peer Tutoring Assignment"),
    (lambda s, p: s.get("participation_score", 10) < 3,  "Class Engagement Initiative"),
    (lambda s, p: s.get("assignment_score_avg", 100) < 40, "Assignment Remedial Plan"),
    (lambda s, p: s.get("financial_aid", False) and p >= 0.5, "Financial Aid Counseling"),
]


def get_interventions(student_features: dict, dropout_probability: float) -> list[str]:
    """
    Given a student feature dict and predicted dropout probability,
    return a list of recommended intervention strings.
    """
    interventions = []
    for condition, recommendation in RULES:
        try:
            if condition(student_features, dropout_probability):
                interventions.append(recommendation)
        except Exception:
            pass
    return interventions if interventions else ["Regular Performance Monitoring"]
