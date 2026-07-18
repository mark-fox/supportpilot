from fastapi import FastAPI

app = FastAPI(
    title="SupportPilot API",
    description="Backend services for the SupportPilot support operations platform.",
    version="0.1.0",
)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Return the current health status of the API."""
    return {"status": "healthy"}