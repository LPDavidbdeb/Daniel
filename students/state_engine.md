# State Engine Foundation - US1.1

## Purpose
This feature defines the core state enumerations and policy constants for the April progression engine. These definitions provide a single source of truth for student states, course outcomes, and workflow status across the backend (models, services, and API schemas).

## Design Patterns Used
- **Django TextChoices**: Used for all enumerations (`CourseState`, `WorkflowState`, `FinalAprilState`, `VettingStatus`). This pattern was chosen because:
    - It provides type safety and prevents magic strings.
    - It integrates seamlessly with Django models (as choices).
    - It allows defining both a machine-readable value (in English) and a human-readable label (in French).
    - It is easily serializable for API responses.
- **Centralized Constants**: Policy thresholds are defined in `students/constants.py` to ensure they are easily discoverable and maintainable.

## Data/Algorithm Decisions

### Enums
- **CourseState**: Represents the outcome of a single course. Distinguishes between hard fails and those eligible for summer school or teacher review.
- **WorkflowState**: Manages the high-level progression of the April review process.
- **FinalAprilState**: The final decision for a student at the end of the April review phase.
- **VettingStatus**: Tracks whether an automated decision has been reviewed or manually overridden.

### Policy Constants
The following constants reflect the school's pedagogical policies:
- `PASS_THRESHOLD = 60`: Minimum grade to pass a course.
- `FAIL_HARD_BLOCK_THRESHOLD = 50`: Grades below this are considered "hard fails" (no summer school).
- `TEACHER_REVIEW_MIN = 57`: Grades between 57 and 59 trigger a teacher review for summer school eligibility.
- `MAX_SUMMER_CLASSES = 1`: The maximum number of summer school classes a student can take to be promoted.

## Integration
These enums and constants are designed to be imported into:
- `students.models`: For database fields.
- `students.schemas`: For Pydantic/Django Ninja API schemas.
- `students.services`: For business logic calculations (e.g., the April progression engine).
