from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import os
import re

app = FastAPI()

# ------------------------
# CONFIG
# ------------------------
ARCHIVO = "gastos.json"
TZ = ZoneInfo("America/Sao_Paulo")


# ------------------------
# MODELO
# ------------------------
class Gasto(BaseModel):
    mensaje: str


# ------------------------
# UTILIDADES
# ------------------------
def cargar_gastos():
    if not os.path.exists(ARCHIVO):
        return []
    with open(ARCHIVO, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_gastos(gastos):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(gastos, f, ensure_ascii=False, indent=2)


def interpretar_fecha(texto: str):
    ahora = datetime.now(TZ)
    texto = texto.lower()

    if "ayer" in texto or "ontem" in texto:
        return ahora - timedelta(days=1)

    return ahora


def interpretar_mensaje(texto: str):
    texto = texto.lower()

    # 1️⃣ Monto
    monto_match = re.search(r"\d+(\.\d+)?", texto)
    if not monto_match:
        return None, None, None

    monto = float(monto_match.group())
    pos_monto = monto_match.start()

    # 2️⃣ Palabras
    palabras = list(re.finditer(r"[a-záéíóúñç]+", texto))

    ignoradas = {
        "gaste", "gasté", "gastei",
        "pague", "pagué", "paguei",
        "en", "com", "ayer", "ontem", "hoy"
    }

    palabras_validas = [
        p for p in palabras if p.group() not in ignoradas
    ]

    if not palabras_validas:
        return None, None, None

    # 3️⃣ Categoría más cercana al monto
    categoria = min(
        palabras_validas,
        key=lambda p: abs(p.start() - pos_monto)
    ).group()

    # 4️⃣ Fecha
    fecha = interpretar_fecha(texto)

    return categoria, monto, fecha


def formatear_respuesta(categoria, monto, fecha, total):
    return (
        "✅ *Gasto registrado*\n"
        f"📂 Categoría: {categoria}\n"
        f"💰 Monto: ${monto}\n"
        f"📊 Total hoy: ${total}\n"
        f"🕒 {fecha.strftime('%d/%m/%Y %H:%M')}"
    )


# ------------------------
# ENDPOINT
# ------------------------
@app.post("/gasto")
def registrar_gasto(gasto: Gasto):

    categoria, monto, fecha = interpretar_mensaje(gasto.mensaje)

    if not categoria or monto is None:
        return {
            "mensaje": (
                "❌ No entendí el mensaje\n"
                "Ejemplos:\n"
                "- comida 25\n"
                "- gasté 25 en comida\n"
                "- pagué uber 18.5\n"
                "- comida 30 ayer"
            )
        }

    gastos = cargar_gastos()

    nuevo = {
        "categoria": categoria,
        "monto": monto,
        "fecha": fecha.strftime("%Y-%m-%d"),
        "hora": fecha.strftime("%H:%M")
    }

    gastos.append(nuevo)
    guardar_gastos(gastos)

    # Total del día
    total = sum(
        g["monto"]
        for g in gastos
        if g["fecha"] == nuevo["fecha"]
    )

    mensaje = formatear_respuesta(categoria, monto, fecha, total)

    return {"mensaje": mensaje}


# ------------------------
# VER GASTOS
# ------------------------
@app.get("/gastos")
def ver_gastos():
    return cargar_gastos()
