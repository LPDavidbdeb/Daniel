from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from ninja import Router
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth

from .models import User
from .schemas import AdminUserCreateInput, AdminUserCreateOutput

router = Router(tags=["Admin Users"], auth=JWTAuth())


@router.post("/users", response={201: AdminUserCreateOutput})
def create_user(request, payload: AdminUserCreateInput):
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required.")

    if not request.user.is_superuser:
        raise HttpError(403, "Only superusers can create users.")

    try:
        validate_email(payload.email)
    except DjangoValidationError as exc:
        raise HttpError(400, "; ".join(exc.messages))

    if User.objects.filter(email__iexact=payload.email).exists():
        raise HttpError(409, "A user with this email already exists.")

    try:
        validate_password(payload.password)
    except DjangoValidationError as exc:
        raise HttpError(400, "; ".join(exc.messages))

    user = User.objects.create_user(
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name,
        last_name=payload.last_name,
        is_staff=payload.is_staff,
        is_active=payload.is_active,
        is_superuser=payload.is_superuser,
    )

    return 201, AdminUserCreateOutput(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_staff=user.is_staff,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
    )
