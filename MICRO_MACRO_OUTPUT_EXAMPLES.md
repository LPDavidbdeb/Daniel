# Micro/Macro Architecture - Output Examples

## Test Case 1: Ahmed Chabane (Critical - Teacher Review Priority)

### Input
```python
Student: Ahmed Chabane (fiche=8002)
Academic Year: 2025-2026

Courses:
  - FRA228 (Français, Core): final_grade=57
  - CCQ222 (Chimie, Core): final_grade=59
```

### Micro-Level Analysis
```
FRA228 (57%):
  ├─ Grade 57 is in range [57, 59]
  ├─ Classification: TEACHER_REVIEW_PENDING
  └─ Reason: "FRA228 (57%)"

CCQ222 (59%):
  ├─ Grade 59 is in range [57, 59]
  ├─ Classification: TEACHER_REVIEW_PENDING
  └─ Reason: "CCQ222 (59%)"
```

### Macro-Level Aggregation
```
Micro States: {
  "FRA228": TEACHER_REVIEW_PENDING,
  "CCQ222": TEACHER_REVIEW_PENDING,
}

Decision Logic:
  ├─ Rule 1 (Absolute Priority): 
  │    has_teacher_review = TRUE ✅
  │    → Apply TEACHER_REVIEW_PRIORITY rule
  └─ Result: REGULAR_REVIEW_PENDING

Final Output:
{
  "workflow_state": "REGULAR_REVIEW_PENDING",
  "final_april_state": null,
  "vetting_status": "REQUIRES_REVIEW",
  "reason_codes": {
    "message": "Teacher Review PENDING - Absolute Priority",
    "rule": "TEACHER_REVIEW_PRIORITY",
    "teacher_review_courses": [
      "FRA228 (57%)",
      "CCQ222 (59%)"
    ],
    "micro_analysis": {
      "courses_evaluated": ["FRA228", "CCQ222"],
      "state_distribution": {
        "TEACHER_REVIEW_PENDING": 2
      }
    }
  }
}
```

---

## Test Case 2: Precedence (Math vs. French)

### Input
```python
Student: Precedence Test (fiche=8003)
Academic Year: 2025-2026

Courses:
  - MAT101 (Mathématiques, Core): final_grade=52
  - FRA101 (Français, Core): final_grade=58
```

### Micro-Level Analysis
```
MAT101 (52%):
  ├─ Grade 52 is in range [50, 56]
  ├─ Course is core_or_sanctioned = True
  ├─ Classification: SUMMER_ELIGIBLE
  └─ Reason: "MAT101 (52%)"

FRA101 (58%):
  ├─ Grade 58 is in range [57, 59]
  ├─ Classification: TEACHER_REVIEW_PENDING
  └─ Reason: "FRA101 (58%)"
```

### Macro-Level Aggregation
```
Micro States: {
  "MAT101": SUMMER_ELIGIBLE,
  "FRA101": TEACHER_REVIEW_PENDING,
}

Decision Logic:
  ├─ Rule 1 (Absolute Priority):
  │    has_teacher_review = TRUE ✅
  │    → Apply TEACHER_REVIEW_PRIORITY rule
  │    (Summer routing is suspended!)
  └─ Result: REGULAR_REVIEW_PENDING

Final Output:
{
  "workflow_state": "REGULAR_REVIEW_PENDING",
  "final_april_state": null,
  "vetting_status": "REQUIRES_REVIEW",
  "reason_codes": {
    "message": "Teacher Review PENDING - Absolute Priority",
    "rule": "TEACHER_REVIEW_PRIORITY",
    "teacher_review_courses": [
      "FRA101 (58%)"
    ],
    "micro_analysis": {
      "courses_evaluated": ["MAT101", "FRA101"],
      "state_distribution": {
        "SUMMER_ELIGIBLE": 1,
        "TEACHER_REVIEW_PENDING": 1
      }
    }
  }
}
```

**Note**: Summer school decision for MAT101 is suspended pending French teacher review.

---

## Test Case 3: Summer School Routing

### Input
```python
Student: Summer Routing Test (fiche=8004)
Academic Year: 2025-2026

Courses:
  - MAT101 (Mathématiques, Core): final_grade=52
  - FRA101 (Français, Core): final_grade=75
  - ANG101 (Anglais, Core): final_grade=68
```

### Micro-Level Analysis
```
MAT101 (52%):
  ├─ Grade 52 is in range [50, 56]
  ├─ Course is core_or_sanctioned = True
  ├─ Classification: SUMMER_ELIGIBLE
  └─ Reason: "MAT101 (52%)"

FRA101 (75%):
  ├─ Grade 75 >= 60
  ├─ Classification: PASS
  └─ Reason: "FRA101 (75%)"

ANG101 (68%):
  ├─ Grade 68 >= 60
  ├─ Classification: PASS
  └─ Reason: "ANG101 (68%)"
```

### Macro-Level Aggregation
```
Micro States: {
  "MAT101": SUMMER_ELIGIBLE,
  "FRA101": PASS,
  "ANG101": PASS,
}

Decision Logic:
  ├─ Rule 1 (Absolute Priority):
  │    has_teacher_review = FALSE
  ├─ Rule 2 (Secondary Priority):
  │    has_summer_eligible = TRUE ✅
  │    has_failed = FALSE ✅
  │    → Apply SUMMER_ROUTING rule
  └─ Result: READY_FOR_FINALIZATION + PROMOTE_WITH_SUMMER

Final Output:
{
  "workflow_state": "READY_FOR_FINALIZATION",
  "final_april_state": "APRIL_FINAL_PROMOTE_WITH_SUMMER",
  "vetting_status": "AUTO_VETTED",
  "reason_codes": {
    "message": "Summer Eligible - Auto-routed to summer school",
    "rule": "SUMMER_ROUTING",
    "summer_eligible_courses": [
      "MAT101 (52%)"
    ],
    "micro_analysis": {
      "courses_evaluated": ["MAT101", "FRA101", "ANG101"],
      "state_distribution": {
        "SUMMER_ELIGIBLE": 1,
        "PASS": 2
      }
    }
  }
}
```

---

## Test Case 4: Auto-Promotion

### Input
```python
Student: Auto-Promote Test (fiche=8005)
Academic Year: 2025-2026

Courses:
  - MAT101 (Mathématiques, Core): final_grade=75
  - FRA101 (Français, Core): final_grade=82
  - ANG101 (Anglais, Core): final_grade=68
```

### Micro-Level Analysis
```
All three courses:
  ├─ Grades >= 60
  ├─ Classification: PASS
  └─ Reasons: "MAT101 (75%)", "FRA101 (82%)", "ANG101 (68%)"
```

### Macro-Level Aggregation
```
Micro States: {
  "MAT101": PASS,
  "FRA101": PASS,
  "ANG101": PASS,
}

Decision Logic:
  ├─ Rule 1: has_teacher_review = FALSE
  ├─ Rule 2: has_summer_eligible = FALSE
  ├─ Rule 3: all_pass = TRUE ✅
  │    → Apply AUTO_PROMOTE rule
  └─ Result: READY_FOR_FINALIZATION + PROMOTE_REGULAR

Final Output:
{
  "workflow_state": "READY_FOR_FINALIZATION",
  "final_april_state": "APRIL_FINAL_PROMOTE_REGULAR",
  "vetting_status": "AUTO_VETTED",
  "reason_codes": {
    "message": "All courses passed - Auto-promotion",
    "rule": "AUTO_PROMOTE",
    "micro_analysis": {
      "courses_evaluated": ["MAT101", "FRA101", "ANG101"],
      "state_distribution": {
        "PASS": 3
      }
    }
  }
}
```

---

## Test Case 5: Hard Failure (IFP Candidate)

### Input
```python
Student: Hard Failure Test (fiche=8006)
Academic Year: 2025-2026

Courses:
  - MAT101 (Mathématiques, Core): final_grade=42
  - FRA101 (Français, Core): final_grade=65
  - ANG101 (Anglais, Core): final_grade=72
```

### Micro-Level Analysis
```
MAT101 (42%):
  ├─ Grade 42 < 50
  ├─ Classification: FAILED (Hard Blocker)
  └─ Reason: "MAT101 (42%)"

FRA101 (65%):
  ├─ Grade 65 >= 60
  ├─ Classification: PASS
  └─ Reason: "FRA101 (65%)"

ANG101 (72%):
  ├─ Grade 72 >= 60
  ├─ Classification: PASS
  └─ Reason: "ANG101 (72%)"
```

### Macro-Level Aggregation
```
Micro States: {
  "MAT101": FAILED,
  "FRA101": PASS,
  "ANG101": PASS,
}

Decision Logic:
  ├─ Rule 1: has_teacher_review = FALSE
  ├─ Rule 2: has_summer_eligible = FALSE
  ├─ Rule 3: all_pass = FALSE
  ├─ Rule 4: has_failed = TRUE ✅
  │    → Apply HARD_FAILURE rule
  └─ Result: IFP_CANDIDATE_REVIEW + REQUIRES_REVIEW

Final Output:
{
  "workflow_state": "IFP_CANDIDATE_REVIEW",
  "final_april_state": null,
  "vetting_status": "REQUIRES_REVIEW",
  "reason_codes": {
    "message": "Hard failure detected - IFP Candidate Review",
    "rule": "HARD_FAILURE",
    "failed_courses": [
      "MAT101 (42%)"
    ],
    "micro_analysis": {
      "courses_evaluated": ["MAT101", "FRA101", "ANG101"],
      "state_distribution": {
        "FAILED": 1,
        "PASS": 2
      }
    }
  }
}
```

---

## Test Case 6: Non-Core Course in Summer Range (Should Fail)

### Input
```python
Student: Non-Core Summer Range (fiche=8007)
Academic Year: 2025-2026

Courses:
  - MAT101 (Mathématiques, Core): final_grade=65
  - OPT101 (Option, Non-Core): final_grade=52
```

### Micro-Level Analysis
```
MAT101 (65%):
  ├─ Grade 65 >= 60
  ├─ Classification: PASS
  └─ Reason: "MAT101 (65%)"

OPT101 (52%):
  ├─ Grade 52 is in range [50, 56]
  ├─ Course is core_or_sanctioned = FALSE
  ├─ Classification: FAILED (not summer-eligible for non-core)
  └─ Reason: "OPT101 (52%)"
```

### Macro-Level Aggregation
```
Micro States: {
  "MAT101": PASS,
  "OPT101": FAILED,
}

Decision Logic:
  ├─ Rule 4: has_failed = TRUE ✅
  │    → Apply HARD_FAILURE rule
  └─ Result: IFP_CANDIDATE_REVIEW + REQUIRES_REVIEW

Final Output:
{
  "workflow_state": "IFP_CANDIDATE_REVIEW",
  "final_april_state": null,
  "vetting_status": "REQUIRES_REVIEW",
  "reason_codes": {
    "message": "Hard failure detected - IFP Candidate Review",
    "rule": "HARD_FAILURE",
    "failed_courses": [
      "OPT101 (52%)"
    ],
    "micro_analysis": {
      "courses_evaluated": ["MAT101", "OPT101"],
      "state_distribution": {
        "PASS": 1,
        "FAILED": 1
      }
    }
  }
}
```

**Note**: Non-core courses (grades 50-56) are treated as failures, not summer-eligible.

---

## Key Insights

### 1. No Short-Circuiting
All 6 test cases show that **every course is evaluated** before the final decision is made. The `micro_analysis.courses_evaluated` list confirms this.

### 2. Strict Hierarchy
The `rule` field in reason_codes shows which decision rule was applied:
- `TEACHER_REVIEW_PRIORITY`: Absolute (highest)
- `SUMMER_ROUTING`: Secondary
- `AUTO_PROMOTE`: Standard
- `HARD_FAILURE`: Fallback

### 3. Complete Traceability
Each output includes:
- Workflow state (high-level)
- Final April state (if applicable)
- Vetting status (review requirement)
- Rule applied (decision path)
- Affected courses (audit trail)
- Micro analysis (detailed breakdown)

### 4. Deterministic Behavior
Given the same input, the output is always identical. The architecture eliminates hidden dependencies.

