from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Gasto(BaseModel):
    mensaje: str


@app.get("/")
def inicio():
    return {
        "mensaje": "Bot de gastos funcionando 🚀"
    }
