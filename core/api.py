from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController
from accounts.api import router as accounts_router
from ingestion.api import router as ingestion_router

api = NinjaExtraAPI(title="GPI-Optimizer API")

# Enregistre les routes JWT par défaut :
# /api/token/pair (POST)
# /api/token/refresh (POST)
# /api/token/verify (POST)
api.register_controllers(NinjaJWTDefaultController)

# Workflow admin pour gerer les utilisateurs
api.add_router("/admin/", accounts_router)

# Ajout du routeur d'ingestion
api.add_router("/ingestion/", ingestion_router)
