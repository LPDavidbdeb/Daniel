from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController
from ingestion.api import router as ingestion_router

api = NinjaExtraAPI(title="GPI-Optimizer API")

# Enregistre les routes JWT par défaut :
# /api/token/pair (POST)
# /api/token/refresh (POST)
# /api/token/verify (POST)
api.register_controllers(NinjaJWTDefaultController)

# Ajout du routeur d'ingestion
api.add_router("/ingestion/", ingestion_router)
