from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.routes.application import router as applications_router
from app.adapters.document_intelligence import document_intelligence


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await document_intelligence.close()


app = FastAPI(
    title="Loan Origination System",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(applications_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Loan-Underwriting-API"
    }