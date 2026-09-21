from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import Settings


def create_app(settings: Settings = None) -> FastAPI:
    if settings is None:
        settings = Settings()

    app = FastAPI(
        title="I Hate PDFs API",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.settings = settings

    from routers import merge, split, convert, compress, jpeg_to_pdf, image_convert, api

    app.include_router(merge.router, tags=["merge"])
    app.include_router(split.router, tags=["split"])
    app.include_router(convert.router, tags=["convert"])
    app.include_router(compress.router, tags=["compress"])
    app.include_router(jpeg_to_pdf.router, tags=["jpeg-to-pdf"])
    app.include_router(image_convert.router, tags=["image-convert"])
    app.include_router(api.router, tags=["api"])

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "i-hate-pdfs"}

    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:create_app", host="0.0.0.0", port=8000, reload=True)
