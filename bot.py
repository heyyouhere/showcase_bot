from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardButton, KeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext, Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, ConversationHandler, MessageHandler

import io

import openai_generation
import texts
import pics

import os
TOKEN = os.getenv("TG_TOKEN")
TG_CHANNEL_ID = os.getenv("TG_CHANNEL_ID")
MACHINE_ROLE = os.getenv("MACHINE_ROLE")




WAITING_FOR_PHOTO, BUTTON_INPUT = range(2)

async def start(update, context):
    await update.message.reply_text(texts.intro)
    keyboard = [
            [InlineKeyboardButton(texts.choose_buttons[0], callback_data="description_generation")],
            [InlineKeyboardButton(texts.choose_buttons[1], callback_data="image_generation")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_chat.send_message(texts.choose, reply_markup=reply_markup)
    return BUTTON_INPUT



async def send_description(update: Update, context: CallbackContext):
    message = update.message if update.message != None else update.callback_query.message
    file_id = message.photo[-1].file_id
    file = await context.bot.getFile(file_id)
    photo_bytes = await file.download_as_bytearray()


    if MACHINE_ROLE == 'PROD':
        desc = openai_generation.description_of_image(photo_bytes, texts.prompt) # TODO: make me async
    else:
        desc = "Я учу секреты продуктивности, пока все смотрят Nornikel digital week."

    output_bytes_io = pics.create_card(photo_bytes, desc)

    keyboard = [
            [InlineKeyboardButton("Сгенерировать ещё", callback_data="gen_again")],
            [InlineKeyboardButton("Отправить в канал", callback_data="send_to_channel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_user.send_photo(photo=output_bytes_io.getvalue(), reply_markup=reply_markup)
    return BUTTON_INPUT


async def buttons_handler(update: Update, context: CallbackContext):
    # await update.callback_query.edit_message_reply_markup(None)
    await update.callback_query.answer()
    match update.callback_query.data:
        case "description_generation":
            await update.effective_chat.send_message(texts.description_gen_welcome)
            return WAITING_FOR_PHOTO
        case "image_generation":
            await update.effective_chat.send_message(texts.image_gen_welcome)
        case 'gen_again':
            await send_description(update, context)
        case 'send_to_channel':
            await context.bot.copy_message(message_id=update.callback_query.message.message_id, chat_id=TG_CHANNEL_ID, from_chat_id=update.effective_chat.id)


async def fallback_executor(update: Update, context: CallbackContext):
    await update.effective_chat.send_message("no handler is found")


async def generate_from_desc(update: Update, context: CallbackContext):
    if MACHINE_ROLE == 'PROD':
        image = openai_generation.image_from_prompt(update.message.text)
    else:
        with open('mask.png', 'rb') as f:
            image = f.readall()

    keyboard = [
            [InlineKeyboardButton("Отправить в канал", callback_data="send_to_channel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_chat.send_photo(image, caption=update.message.text, reply_markup=reply_markup)
    return BUTTON_INPUT



def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start), CommandHandler('generate', generate_from_desc)],
            states={
                WAITING_FOR_PHOTO : [MessageHandler(filters.PHOTO, send_description), CallbackQueryHandler(buttons_handler)],
                BUTTON_INPUT : [CallbackQueryHandler(buttons_handler), MessageHandler(filters.PHOTO, send_description)],
            },
            fallbacks=[
                MessageHandler(filters.ALL, fallback_executor)
                ],
            )
    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
