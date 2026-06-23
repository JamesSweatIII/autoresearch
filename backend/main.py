from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.setup import init_db
from routes.article_routes import router as article_router
from routes.legacy_routes import router as legacy_router
from routes.pooler_routes import router as pooler_router
from routes.autoresearch_routes import router as autoresearch_router
from routes.group_routes import router as group_router
from routes.research_routes import router as research_router
from fastapi.responses import JSONResponse

app = FastAPI(
    title="AutoResearch API",
    description="AI-Powered Research Intelligence Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(article_router)
app.include_router(legacy_router)
app.include_router(pooler_router)
app.include_router(autoresearch_router)
app.include_router(group_router)
app.include_router(research_router)


@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})

@app.on_event("startup")
def startup():
    init_db()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
else:
    app.router.redirect_slashes = False
