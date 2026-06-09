from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.setup import init_db
from routes.research_routes import router as research_router
from routes.analytics_routes import router as analytics_router
from routes.search_routes import router as search_router
from routes.model_routes import router as model_router

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

app.include_router(research_router)
app.include_router(analytics_router)
app.include_router(search_router)
app.include_router(model_router)


@app.on_event("startup")
def startup():
    init_db()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
else:
    app.router.redirect_slashes = False
