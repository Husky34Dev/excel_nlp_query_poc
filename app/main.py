
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.endpoints import router

app = FastAPI()

# CORS si frontend está en otra URL/puerto
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # cámbialo a ["http://localhost:3000"] si usas Vite/React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas de la API
app.include_router(router)

# (Opcional) Servir archivos estáticos si frontend está en la misma carpeta
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
