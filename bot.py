import json
import datetime
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, filters, ContextTypes

import os

# Configura tu token y tu ID de admin
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6828410834  # <- Reemplaza con tu verdadero ID (el bot te lo dice al usar /start)

# Configuración del log
logging.basicConfig(level=logging.INFO)

# Archivos
CLAVES_FILE = "claves.json"
USUARIOS_ULTIMO_USO = {}

# Conversación para crear key
CORREO, CLAVE, DIAS = range(3)

# Cargar claves desde archivo
def cargar_claves():
    try:
        with open(CLAVES_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

# Guardar claves
def guardar_claves(claves):
    with open(CLAVES_FILE, "w") as f:
        json.dump(claves, f, indent=2)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"👋 Hola, tu ID es: {user_id}\nUsa /codigo correo clave para obtener tu código.")

# /crear_key
async def crear_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ No tienes permiso para usar este comando.")
        return ConversationHandler.END
    await update.message.reply_text("📧 Ingresa el correo del cliente:")
    return CORREO

async def ingresar_correo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["correo"] = update.message.text.strip()
    await update.message.reply_text("🔐 Ingresa la clave que usará el cliente:")
    return CLAVE

async def ingresar_clave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["clave"] = update.message.text.strip()
    await update.message.reply_text("📅 ¿Cuántos días será válida?")
    return DIAS

async def ingresar_dias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dias = int(update.message.text.strip())
    correo = context.user_data["correo"]
    clave = context.user_data["clave"]
    expira = (datetime.datetime.now() + datetime.timedelta(days=dias)).isoformat()

    claves = cargar_claves()
    claves[correo] = {"key": clave, "expira": expira}
    guardar_claves(claves)

    await update.message.reply_text(f"✅ Clave creada para {correo} válida por {dias} días.")
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Operación cancelada.")
    return ConversationHandler.END

# /codigo
async def obtener_codigo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    user_id = update.effective_user.id

    if len(args) != 2:
        await update.message.reply_text("❌ Usa el comando así:\n/codigo correo clave")
        return

    correo, clave = args
    claves = cargar_claves()

    if correo not in claves:
        await update.message.reply_text("❌ No tienes una clave activa.")
        return

    data = claves[correo]
    if clave != data["key"]:
        await update.message.reply_text("❌ Clave incorrecta.")
        return

    expira = datetime.datetime.fromisoformat(data["expira"])
    if datetime.datetime.now() > expira:
        await update.message.reply_text("⛔ Tu clave ha expirado.")
        return

    # Control de espera mínima (1 minuto)
    ultimo_uso = USUARIOS_ULTIMO_USO.get(user_id)
    ahora = datetime.datetime.now()
    if ultimo_uso and (ahora - ultimo_uso).total_seconds() < 60:
        await update.message.reply_text("⏱️ Espera 1 minuto antes de volver a pedir un código.")
        return

    USUARIOS_ULTIMO_USO[user_id] = ahora

    # Lógica para buscar el código en Gmail (solo muestra mensaje por ahora)
    await update.message.reply_text("🔍 Buscando código en Gmail...")
    # Aquí agregarás la conexión a Gmail con IMAP y extracción del código

    # Simulando un código encontrado:
    await update.message.reply_text("✅ Tu código Disney+ es: 259535\n🔓 Acceso satisfactorio.")

# MAIN
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("codigo", obtener_codigo))

    conv = ConversationHandler(
        entry_points=[CommandHandler("crear_key", crear_key)],
        states={
            CORREO: [MessageHandler(filters.TEXT & ~filters.COMMAND, ingresar_correo)],
            CLAVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ingresar_clave)],
            DIAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ingresar_dias)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )
    app.add_handler(conv)

    print("🤖 Bot en ejecución...")
    app.run_polling()
