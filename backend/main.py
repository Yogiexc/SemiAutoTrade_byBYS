from fastapi import FastAPI

app = FastAPI(title="AI Trading Assistant API", version="1.0.0")

@app.get("/")
def read_root():
    return {"message": "Welcome to AI Trading Assistant API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
