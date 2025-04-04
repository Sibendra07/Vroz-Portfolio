from fastapi import FastAPI
from artist import artist
app = FastAPI()

app.include_router(artist.router, prefix="/artist", tags=["artist"])

