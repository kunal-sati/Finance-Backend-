from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from database import Base, engine
from routers import auth, dashboard, records, users

app = FastAPI(title="Finance Backend API")

# Create tables
Base.metadata.create_all(bind=engine)

# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(records.router)
app.include_router(dashboard.router)

# Root
@app.get("/")
def root():
    return {"message": "Finance Backend Running 🚀"}

# Global Error Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Something went wrong"}
    )