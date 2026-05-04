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

### State Seeding (US1.4)
To transition from legacy Excel-based tracking to the State Engine, a seeding service (`seed_student_state`) and management command (`seed_student_states`) have been implemented.

- **Target**: 100% of active students (`is_active=True`) for a given academic year.
- **Idempotency**: The command uses `update_or_create` to safely handle multiple runs.
- **Legacy Mapping Rules**:
    - **Summer School**: If a `SummerSchoolEnrollment` exists for the student and year, the state is set to `APRIL_FINAL_PROMOTE_WITH_SUMMER` and `vetting_status` to `AUTO_VETTED`.
    - **Overrides**: If a `StudentPromotionOverride` exists (and no summer enrollment is present), the following mapping applies:
        - `FORCE_PASS` -> `APRIL_FINAL_PROMOTE_REGULAR`
        - `FORCE_RETAKE` -> `APRIL_FINAL_HOLDBACK`
        - `TRANSFER_IFP` -> `APRIL_FINAL_IFP_N`
        - `TRANSFER_DIM` -> `APRIL_FINAL_HOLDBACK`
        - Vetting status is set to `AUTO_VETTED` for overrides.
    - **Default**: If no legacy records are found, the student is initialized with `WorkflowState.REGULAR_REVIEW_PENDING` and `vetting_status = REQUIRES_REVIEW`.
- **Audit**: Every seeding event is recorded in the `StateTransitionLog` with `event_name='SYSTEM_SEED_INITIALIZATION'`.

### Models
- **StudentState**: Acts as a "macro ledger" tracking the high-level progression state of each student per academic year.
    - **Unique Constraint**: `(student, academic_year)` ensures a single source of truth per year.
    - **Reason Codes**: A `JSONField` is used to store flexible metadata and audit trail information about decision logic.
    - **Version**: Included for future optimistic concurrency and audit tracing.
    - **Workflow States**: Uses the enums defined in US1.1 to drive the April review process.
- **StateTransitionLog**: An immutable audit trail of every macro state change for a student.
    - **Traceability**: Records `from_state`, `to_state`, `event_name`, and the `actor` (User or System).
    - **Performance**: Indexed on `(student, -timestamp)` for fast retrieval of historical transitions.
    - **Metadata**: Uses `JSONField` for storing situational context, such as specific rule triggers or manual override justifications.

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
