import routes.api
import routes.view
from database.models import init_models
from fastapi import FastAPI

app = FastAPI()
app.include_router(router=routes.api.router, prefix="/api/v1")
app.include_router(router=routes.view.router, prefix="/view")


@app.on_event("startup")
async def startup():
    await init_models()


@app.get("/")
async def health():
    return {"status": "ok"}
