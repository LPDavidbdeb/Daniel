# Micro/Macro Architecture - Developer Guide

## Overview

The `derive_student_state` function now implements a **two-level hierarchical analysis**:

1. **Micro-Level**: Individual course evaluation
2. **Macro-Level**: Student-level aggregation with precedence rules

This design ensures:
- No short-circuiting (ALL courses evaluated)
- Clear decision hierarchy
- Complete traceability
- Easier to understand and modify

---

## Micro-Level: `evaluate_course_result`

### Purpose
Evaluates a single `AcademicResult` to determine its course-level state.

### Signature
```python
def evaluate_course_result(
    result: AcademicResult,
) -> Tuple[CourseEvalState, str]:
```

### Returns
- `CourseEvalState`: One of `PASS`, `TEACHER_REVIEW_PENDING`, `SUMMER_ELIGIBLE`, `FAILED`
- `str`: Reason code, e.g., "FRA228 (57%)"

### Logic Flow

```
Input: AcademicResult with final_grade
  │
  ├─ If grade is None → FAILED, reason_code
  │
  ├─ If 57 ≤ grade ≤ 59 → TEACHER_REVIEW_PENDING, reason_code
  │   (Regardless of core/non-core status)
  │
  ├─ If 50 ≤ grade ≤ 56:
  │   ├─ If course.is_core_or_sanctioned:
  │   │   → SUMMER_ELIGIBLE, reason_code
  │   └─ Else:
  │       → FAILED, reason_code
  │
  ├─ If grade < 50 → FAILED, reason_code
  │
  └─ If grade ≥ 60 → PASS, reason_code
```

### Example Usage
```python
result = AcademicResult.objects.get(...)
state, reason = evaluate_course_result(result)
# state might be SUMMER_ELIGIBLE
# reason would be "MAT101 (52%)"
```

---

## Macro-Level: `aggregate_micro_results`

### Purpose
Aggregates micro-level course states into a student-level workflow state using strict hierarchical precedence.

### Signature
```python
def aggregate_micro_results(
    micro_states: Dict[str, CourseEvalState],
    reason_codes_by_state: Dict[CourseEvalState, List[str]],
) -> Tuple[WorkflowState, FinalAprilState | None, VettingStatus, Dict]:
```

### Returns
- `WorkflowState`: The student's workflow state (e.g., `REGULAR_REVIEW_PENDING`)
- `FinalAprilState | None`: The final state if one is auto-assigned
- `VettingStatus`: Review status (e.g., `REQUIRES_REVIEW`)
- `Dict`: Diagnostic payload with decision reasoning

### Hierarchical Rules

#### Rule 1: TEACHER_REVIEW_PRIORITY (Absolute)
```python
if any_course_is(TEACHER_REVIEW_PENDING):
    return REGULAR_REVIEW_PENDING, None, REQUIRES_REVIEW, payload
```

**Rationale**: Teacher review requires human judgment. All other rules are suspended.

**Payload Example**:
```python
{
    "message": "Teacher Review PENDING - Absolute Priority",
    "rule": "TEACHER_REVIEW_PRIORITY",
    "teacher_review_courses": ["FRA228 (57%)", "CCQ222 (59%)"],
}
```

#### Rule 2: SUMMER_ROUTING (Secondary)
```python
if (not has_teacher_review) and any_course_is(SUMMER_ELIGIBLE):
    return READY_FOR_FINALIZATION, APRIL_FINAL_PROMOTE_WITH_SUMMER, AUTO_VETTED, payload
```

**Rationale**: Only if no teacher review is needed, route to summer school.

**Payload Example**:
```python
{
    "message": "Summer Eligible - Auto-routed to summer school",
    "rule": "SUMMER_ROUTING",
    "summer_eligible_courses": ["MAT101 (52%)"],
}
```

#### Rule 3: AUTO_PROMOTE
```python
if all_courses_are(PASS):
    return READY_FOR_FINALIZATION, APRIL_FINAL_PROMOTE_REGULAR, AUTO_VETTED, payload
```

**Rationale**: All courses passed; automatic promotion.

#### Rule 4: HARD_FAILURE
```python
if any_course_is(FAILED):
    return IFP_CANDIDATE_REVIEW, None, REQUIRES_REVIEW, payload
```

**Rationale**: At least one course failed; requires IFP review.

---

## Orchestration: `derive_student_state`

### Full Process

```
Input: student: Student, academic_year: str
  │
  ├─ [STEP 0] Check for legacy overrides
  │   ├─ If override exists → return mapped state (MANUALLY_VETTED)
  │   └─ Else → continue
  │
  ├─ [STEP 1] Fetch core course results
  │   ├─ If no results → return REQUIRES_REVIEW
  │   ├─ If all grades None → return REQUIRES_REVIEW
  │   └─ Else → continue
  │
  ├─ [STEP 2] MICRO ANALYSIS
  │   for each core_result:
  │       state, reason = evaluate_course_result(core_result)
  │       record_state(state, reason)
  │
  ├─ [STEP 3] MACRO ANALYSIS
  │   workflow_state, final_state, vetting_status, payload = 
  │       aggregate_micro_results(all_states, reasons)
  │
  └─ [STEP 4] Return comprehensive diagnostic
      return {
          "workflow_state": workflow_state,
          "final_april_state": final_state,
          "vetting_status": vetting_status,
          "reason_codes": enriched_payload,
      }
```

### Reason Codes Structure

The `reason_codes` field now contains comprehensive diagnostic information:

```python
reason_codes = {
    "message": "Human-readable summary",
    "rule": "RULE_NAME",  # One of: TEACHER_REVIEW_PRIORITY, SUMMER_ROUTING, AUTO_PROMOTE, HARD_FAILURE
    
    # Rule-specific fields (optional)
    "teacher_review_courses": ["FRA228 (57%)", "CCQ222 (59%)"],  # If teacher review
    "summer_eligible_courses": ["MAT101 (52%)"],                  # If summer routing
    "failed_courses": ["PHY101 (42%)"],                           # If hard failure
    
    # Micro-analysis details
    "micro_analysis": {
        "courses_evaluated": ["FRA228", "CCQ222", "MAT101"],
        "state_distribution": {
            "PASS": 1,
            "TEACHER_REVIEW_PENDING": 2,
        },
    },
}
```

---

## Testing Guidelines

### Adding a New Test

1. **Determine Test Level**:
   - Micro-level → Use `evaluate_course_result` directly
   - Macro-level → Use `aggregate_micro_results` directly
   - Integration → Use `derive_student_state`

2. **Micro-Level Template**:
```python
def test_micro_your_scenario(self):
    """Micro: Your scenario description."""
    result = self._create_course_and_result("COURSE", grade, is_core=True)
    state, reason = evaluate_course_result(result)
    
    self.assertEqual(state, CourseEvalState.EXPECTED_STATE)
    self.assertIn("expected_substring", reason)
```

3. **Macro-Level Template**:
```python
def test_macro_your_rule(self):
    """Macro: Your rule description."""
    micro_states = {
        "COURSE1": CourseEvalState.STATE1,
        "COURSE2": CourseEvalState.STATE2,
    }
    reason_codes_by_state = {
        CourseEvalState.STATE1: ["COURSE1 (X%)"],
        # ... fill in all states
    }
    
    workflow_state, final_state, vetting_status, payload = aggregate_micro_results(
        micro_states, reason_codes_by_state
    )
    
    self.assertEqual(workflow_state, WorkflowState.EXPECTED)
    self.assertEqual(payload["rule"], "RULE_NAME")
```

4. **Integration Template**:
```python
def test_integration_scenario(self):
    """Integration: End-to-end scenario."""
    # Create student and results
    student = Student.objects.create(...)
    # ... create courses and results
    
    # Derive state
    result = derive_student_state(student, academic_year)
    
    # Verify
    self.assertEqual(result["workflow_state"], WorkflowState.EXPECTED)
    # ... verify reason_codes, micro_analysis, etc.
```

---

## Common Patterns

### Checking if Teacher Review is Needed
```python
reason_codes = derive_student_state(student, year)["reason_codes"]
is_teacher_review = reason_codes.get("rule") == "TEACHER_REVIEW_PRIORITY"
```

### Getting All Failed Courses
```python
reason_codes = derive_student_state(student, year)["reason_codes"]
failed_courses = reason_codes.get("failed_courses", [])
```

### Understanding Decision Path
```python
micro_analysis = reason_codes.get("micro_analysis", {})
state_distribution = micro_analysis.get("state_distribution", {})
# Now you can see how many courses in each state
```

---

## Future Enhancements

### Adding a New Micro-Level State
1. Add to `CourseEvalState` enum
2. Update `evaluate_course_result` logic
3. Add corresponding test case
4. Update macro aggregation if needed

### Adding a New Macro-Level Rule
1. Define rule priority (where does it fit in hierarchy?)
2. Add to `aggregate_micro_results` in correct priority order
3. Add test cases for:
   - Rule fires correctly
   - Rule respects higher-priority rules
4. Update documentation

### Performance Optimization
- **Current**: O(n) where n = number of core courses
- **Safe Optimizations**:
  - Cache `course.is_core_or_sanctioned` lookups
  - Batch query course properties
  - Pre-compute micro states if called multiple times

---

## Debugging Tips

1. **Enable Detailed Logging**:
```python
import logging
logger = logging.getLogger("students.services.auto_derivation")
logger.setLevel(logging.DEBUG)
```

2. **Inspect Micro States**:
```python
reason_codes = result["reason_codes"]
micro = reason_codes.get("micro_analysis", {})
print(f"Courses: {micro.get('courses_evaluated')}")
print(f"Distribution: {micro.get('state_distribution')}")
```

3. **Trace Decision Path**:
```python
print(f"Rule Applied: {reason_codes.get('rule')}")
print(f"Message: {reason_codes.get('message')}")
# Look at rule-specific fields
```

---

## References

- **Source Code**: `students/services/auto_derivation.py`
- **Tests**: `students/test_micro_macro_architecture.py`
- **Constants**: `students/constants.py`
- **Enums**: `students/enums.py`
- **Report**: `MICRO_MACRO_REFACTORING_REPORT.md`

