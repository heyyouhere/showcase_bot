from telegram.ext import Application, MessageHandler, filters, CommandHandler
import os
import requests
import description_gen

TOKEN = os.getenv("TG_TOKEN")

prompt = 'Я отправлю тебе фотографию, твоя задача сгенерировать ироничную фразу используя контекст фотографии по типу "Я еду на работу, пока все смотрят Nornikel digital week". Фраза должна заканчиваться на "Пока все смотрят Nornikel digital week" и должна быть достаточно короткой, ответь только этой фразой ничего больше не пиши. Фраза ни в коем случае не должна осквернять или быть негативный в сторону Норникеля. Фраза должна быть позитивной.'

async def start(update, context):
    await update.message.reply_text("Привет! Отправь фотку и получи смешное описание")


async def send_description(update, context):
    user_id = update.message.from_user.id
    photo = update.message.photo[-1]
    file_id = photo.file_id
    file_name = f"{user_id}_{file_id}.jpg"
    new_file = await context.bot.getFile(file_id)
    r = requests.get(new_file.file_path)
    image_path = os.path.join("./inputs", file_name)
    with open(image_path, "wb") as out_file:
        out_file.write(r.content)
    desc = description_gen.gererate_ai_description(image_path, prompt)
    # desc = "test_test_test"
    # os.remove(path)
    await update.effective_user.send_message(desc)


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, send_description))
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
