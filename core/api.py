from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController

api = NinjaExtraAPI(title="GPI-Optimizer API")

# Use the built-in JWT controller; it derives the login field from USERNAME_FIELD.
api.register_controllers(NinjaJWTDefaultController)
