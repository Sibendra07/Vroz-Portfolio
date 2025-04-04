from fastapi import FastAPI
from artist import artist
from core.logger import logger
from core.config import config


app = FastAPI(debug=config.DEBUG)

app.include_router(artist.router, prefix="/artist", tags=["artist"])

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on {config.HOST}:{config.PORT}")
    uvicorn.run(app, host=config.HOST, port=config.PORT)
