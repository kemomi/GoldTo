from fastapi import FastAPI

app = FastAPI(title="Overseas Jewelry Strategy Simulator API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
