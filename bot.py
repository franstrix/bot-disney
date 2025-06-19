import json
import random
import string
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

# Tu token real está en las variables de entorno
import os
BOT_TOKEN = os.environ.get("BOT_TOKEN")

ADMIN_ID = 6828410834  # Reemplazar con tu ID real de Telegram
CLAVES_FILE = "claves.json"

# --- Utilidades ---
def cargar_claves():
    try:
        with open(CLAVES_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def guardar_claves(data):
    with open(CLAVES_FILE, "w") as f:
        json.dump(data, f)

def generar_clave(longitud=5):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=longitud))

# --- Estados para la creación de clave ---
CORREO, DIAS = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"👋 Hola, tu ID es: {update.effective_user.id}\nUsa /codigo correo clave para obtener tu código.")

async def crear_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ No tienes permiso para usar este comando.")
        return ConversationHandler.END
    await update.message.reply_text("📧 Ingresa el correo del cliente:")
    return CORREO

async def recibir_correo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["correo"] = update.message.text.strip()
    await update.message.reply_text("📅 ¿Cuántos días será válida la clave?")
    return DIAS

async def recibir_dias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dias = int(update.message.text.strip())
    except:
        await update.message.reply_text("❌ Ingresa un número válido de días.")
        return DIAS

    correo = context.user_data["correo"]
    clave = generar_clave()
    fecha_exp = (datetime.datetime.now() + datetime.timedelta(days=dias)).strftime("%Y-%m-%d")

    claves = cargar_claves()
    claves[clave] = {"correo": correo, "expira": fecha_exp}
    guardar_claves(claves)

    mensaje = f"🔑 ENVÍA ESTO A TU CLIENTE:\n/codigo {correo} {clave}\n\n✅ Puede recibir códigos durante {dias} días."
    await update.message.reply_text(mensaje)
    return ConversationHandler.END

async def codigo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        correo, clave = context.args[0], context.args[1]
    except:
        await update.message.reply_text("❌ Formato incorrecto. Usa: /codigo correo clave")
        return

    claves = cargar_claves()
    if clave not in claves:
        await update.message.reply_text("❌ Clave inválida.")
        return

    datos = claves[clave]
    if datos["correo"] != correo:
        await update.message.reply_text("❌ Esta clave no corresponde con ese correo.")
        return

    fecha_exp = datetime.datetime.strptime(datos["expira"], "%Y-%m-%d")
    if datetime.datetime.now() > fecha_exp:
        await update.message.reply_text("⛔ La clave ha expirado.")
        return

    dias_restantes = (fecha_exp - datetime.datetime.now()).days
    await update.message.reply_text(
        f"✅ Registro exitoso.\nPodrás recibir códigos del correo {correo} durante {dias_restantes} días."
    )

# --- Main ---
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("codigo", codigo))

crear_handler = ConversationHandler(
    entry_points=[CommandHandler("crear_key", crear_key)],
    states={
        CORREO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_correo)],
        DIAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_dias)],
    },
    fallbacks=[],
)
app.add_handler(crear_handler)

print("🤖 Bot en ejecución...")
app.run_polling()
