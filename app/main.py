from fastapi import FastAPI
from app.api.routes.application import router as applications_router

app = FastAPI(
    title="Loan Origination System",
    version="0.1.0"
)

app.include_router(applications_router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Loan-Underwriting-API"
    }