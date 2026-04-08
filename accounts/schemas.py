from ninja import Schema


class AdminUserCreateInput(Schema):
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""
    is_staff: bool = False
    is_active: bool = True
    is_superuser: bool = False


class AdminUserCreateOutput(Schema):
    id: int
    email: str
    first_name: str
    last_name: str
    is_staff: bool
    is_active: bool
    is_superuser: bool
