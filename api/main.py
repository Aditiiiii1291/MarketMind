"""FastAPI application entry point for MarketMind."""

from fastapi import FastAPI

from api.auth import auth_router
from api.routers import analysis, concepts, dashboard, products, uploads


app = FastAPI(
    title="MarketMind API",
    version="1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(auth_router.router)
app.include_router(products.router)
app.include_router(concepts.router)
app.include_router(dashboard.router)
app.include_router(uploads.router)
app.include_router(analysis.router)
