import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq
 
# Configuración de logs
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
 
# Clientes
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
BOT_TOKEN = os.environ["BOT_TOKEN"]
 
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
 
    # Inicializar historial si no existe
    if user_id not in conversation_history:
        conversation_history[user_id] = []
 
    # Añadir mensaje del usuario al historial
    conversation_history[user_id].append({
        "role": "user",
        "content": user_message
    })
 
    # Limitar historial a los últimos 20 mensajes para no exceder tokens
    if len(conversation_history[user_id]) > 20:
        conversation_history[user_id] = conversation_history[user_id][-20:]
 
    # Indicar que está escribiendo
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
 
    try:
        # Llamar a Groq API
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
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
 
        # Añadir respuesta al historial
        conversation_history[user_id].append({
            "role": "assistant",
            "content": assistant_message
        })
 
        await update.message.reply_text(assistant_message)
 
    except Exception as e:
        logging.error(f"Error al llamar a Groq: {e}")
        await update.message.reply_text(
            "⚠️ Hubo un error al procesar tu mensaje. Inténtalo de nuevo."
        )
 
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
 
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
 
    logging.info("🤖 Bot iniciado...")
    app.run_polling()
 
if __name__ == "__main__":
    main()
