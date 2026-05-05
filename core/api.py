from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController
from accounts.api import router as accounts_router
from ingestion.api import router as ingestion_router
from students.api import router as students_router
from students.system_api import router as system_router
from school.api import router as school_router

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

# Ajout du routeur des élèves
api.add_router("/students/", students_router)

# Ajout du routeur de l'école (enseignants, cours)
api.add_router("/school/", school_router)

# Ajout du routeur système (introspection — aucune auth requise)
api.add_router("/system/", system_router)
