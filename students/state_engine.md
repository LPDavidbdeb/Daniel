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

## Orchestration Gateway (US2.1)
The `apply_event` method in `students/services/state_engine.py` serves as the singular entry point for all student state transitions.

### Design Patterns
- **Gateway/Orchestrator Pattern**: Centralizes complex logic (validation, guards, persistence, logging) into a single method to ensure consistency.
- **Concurrency Control**: 
    - Uses `transaction.atomic()` to ensure that the ledger update and audit log write happen as a single unit of work.
    - Employs `select_for_update()` to obtain a row-level database lock on the `StudentState` record, preventing race conditions during concurrent modifications.
- **Audit Logging**: Synchronously creates a `StateTransitionLog` for every successful call, ensuring 100% traceability.

### Transition Guards
- **IllegalTransitionError**: A custom exception raised when a requested transition violates business rules.
- **Invariants**: 
- Validates all enum inputs against their allowed values.
- Prevents "de-finalization" (e.g., returning to a pending workflow state once a final April state has been assigned).
- **Snapshot Closure Gate (US2.4)**: Enforced via `close_april_snapshot(academic_year)` in `students/services/state_engine.py`.
- **Purpose**: Prevents closing the April progression phase if any active student remains in `REQUIRES_REVIEW`.
- **Optimization**: Uses `exists()` and `values()` to efficiently identify incomplete records without loading entire model instances into memory.
- **Error Handling**: Raises `SnapshotClosureError` containing a list of incomplete students (names and IDs) to provide immediate actionable feedback to administrators.
- **Pedagogical Guards (US2.2)**: Enforced via `validate_transition` in `students/services/transition_guards.py`.

    - **Summer Limit**: Maximum of 1 summer class per year.
    - **Teacher Review Boundary**: Overrides to pass/promote are only permitted for course grades between 57 and 59.
    - **Summer Eligibility**: Routing to summer school is restricted to course grades between 50 and 59.
    - **Hard Blocker**: Core or sanctioned courses with grades < 50 prevent any summer school promotion.
    - **IFP Prerequisites**: Finalizing to an IFP state requires a prior `IFP_CANDIDATE_REVIEW` workflow state.

## Legacy System Synchronization (Epic 3)
The `apply_event` gateway ensures bidirectional integrity with legacy tables during the transition phase.

### Summer School Synchronization (US3.2)
When a student's state is modified via `apply_event`, the system automatically synchronizes the legacy `SummerSchoolEnrollment` table:
- **Automatic Enrollment**: Transitioning to `APRIL_FINAL_PROMOTE_WITH_SUMMER` triggers an automatic upsert in the legacy enrollment table. The `course_id` must be provided in the event payload.
- **Automatic Withdrawal**: Transitioning to any state *other* than summer promotion (e.g., `PROMOTE_REGULAR`, `HOLDBACK`) automatically removes the corresponding record from the legacy table.
- **Transactional Integrity**: Both the `StudentState` ledger update and the legacy table synchronization are wrapped in the same `transaction.atomic()` block.

## Auto-Derivation Service (US2.3)
The `derive_student_state` service in `students/services/auto_derivation.py` calculates suggested states based on academic results.

### Precedence Hierarchy (US3.1)
1. **Manual Legacy Overrides (Highest)**: If a `StudentPromotionOverride` exists for the student and year, it is used immediately. The status is set to `MANUALLY_VETTED`.
2. **Grade-based Logic (Standard)**: If no override exists, the logic matrix below is applied.

### Logic Matrix
1. **Rule 4 (IFP / Holdback Candidate)**: 
    - Trigger: >1 failure OR any hard blocker (< 50) in core courses.
    - Derived State: `WorkflowState.IFP_CANDIDATE_REVIEW`.
2. **Rule 2 (Teacher Review Queue)**: 
    - Trigger: Any core course grade between 57-59 AND no hard blockers.
    - Derived State: `WorkflowState.REGULAR_REVIEW_PENDING` (REQUIRES_REVIEW).
3. **Rule 3 (Summer School Queue)**: 
    - Trigger: Exactly one core course failure between 50-59 (and no hard blockers).
    - Derived State: `WorkflowState.READY_FOR_FINALIZATION` with `FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER`.
4. **Rule 1 (Auto-Promote)**: 
    - Trigger: All core courses >= 60.
    - Derived State: `WorkflowState.READY_FOR_FINALIZATION` with `FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR` (AUTO_VETTED).

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
