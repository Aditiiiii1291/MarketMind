"""FastAPI application entry point for MarketMind."""

from fastapi import FastAPI

from api.routers import concepts, dashboard, products


app = FastAPI(
    title="MarketMind API",
    version="1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(products.router)
app.include_router(concepts.router)
app.include_router(dashboard.router)
