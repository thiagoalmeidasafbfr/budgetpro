from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import (
    auth_router, companies_router, departments_router,
    cost_centers_router, accounts_router, budget_versions_router,
    budgets_router, actuals_router, forecast_router,
    dashboard_router, audit_router, users_router,
)
from app.routers import import_router
from app.routers import importacao_router

app = FastAPI(
    title="BudgetPro API",
    description="Plataforma de Controle Orçamentário Corporativo",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth_router.router)
app.include_router(companies_router.router)
app.include_router(departments_router.router)
app.include_router(cost_centers_router.router)
app.include_router(accounts_router.router)
app.include_router(budget_versions_router.router)
app.include_router(budgets_router.router)
app.include_router(actuals_router.router)
app.include_router(forecast_router.router)
app.include_router(dashboard_router.router)
app.include_router(audit_router.router)
app.include_router(users_router.router)
app.include_router(import_router.router)
app.include_router(importacao_router.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}
