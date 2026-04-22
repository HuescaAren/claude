import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Validar variables de entorno
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY no está definida en las variables de entorno.")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN no está definida en las variables de entorno.")

# Clientes
groq_client = Groq(api_key=GROQ_API_KEY)

# Historial de conversación por usuario
conversation_history = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola! Soy tu asistente de IA. Escríbeme lo que necesites y te ayudaré."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Comandos disponibles:*\n"
        "/start - Iniciar el bot\n"
        "/help - Ver esta ayuda\n"
        "/reset - Borrar el historial de conversación\n\n"
        "También puedes escribirme directamente cualquier pregunta.",
        parse_mode="Markdown"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text("🔄 Historial borrado. ¡Empezamos de nuevo!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({
        "role": "user",
        "content": user_message
    })

    if len(conversation_history[user_id]) > 20:
        conversation_history[user_id] = conversation_history[user_id][-20:]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un asistente útil, claro y amigable. Responde siempre en el idioma del usuario."
                }
            ] + conversation_history[user_id],
            max_tokens=1024,
            temperature=0.7
        )

        assistant_message = response.choices[0].message.content

        conversation_history[user_id].append({
            "role": "assistant",
            "content": assistant_message
        })

        await update.message.reply_text(assistant_message)

    except Exception as e:
        logging.exception("Error al llamar a Groq")
        await update.message.reply_text(
            "⚠️ Hubo un error al procesar tu mensaje. Inténtalo de nuevo."
        )

def main():
    logging.info("Iniciando bot de Telegram...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("🤖 Bot iniciado. Esperando mensajes...")
    app.run_polling()

if __name__ == "__main__":
    main()
