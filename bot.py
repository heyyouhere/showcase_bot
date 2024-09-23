from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardButton, KeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatMemberLeft
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, ConversationHandler, MessageHandler

import io

import openai_generation
import texts
import pics
import random

import os
TOKEN = os.getenv("TG_TOKEN")
TG_CHANNEL_ID = os.getenv("TG_CHANNEL_ID")
MACHINE_ROLE = os.getenv("MACHINE_ROLE")




WAITING_FOR_PHOTO, WAITING_FOR_IMAGE_PROMPT,  BUTTON_INPUT = range(3)


async def start(update: Update, context: CallbackContext):
    await update.effective_chat.send_message(texts.intro)
    return await check_if_member(update, context)


async def check_if_member(update: Update, context: CallbackContext):
    check = type(await context.bot.getChatMember(TG_CHANNEL_ID, update.effective_user.id)) != ChatMemberLeft
    if check:
        keyboard = [
                [InlineKeyboardButton(texts.choose_buttons[0], callback_data="description_generation")],
                [InlineKeyboardButton(texts.choose_buttons[1], callback_data="image_generation")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_chat.send_message(texts.choose, reply_markup=reply_markup)
    else:
        keyboard = [
                [InlineKeyboardButton(texts.not_a_member_button, callback_data="check_for_membership")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_chat.send_message(texts.not_a_member, reply_markup=reply_markup)
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
            [InlineKeyboardButton("Решить задачу будущего", callback_data="image_generation")],
            [InlineKeyboardButton("Отправить в канал", callback_data="send_to_channel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_user.send_photo(photo=output_bytes_io.getvalue(), reply_markup=reply_markup)
    return BUTTON_INPUT


async def buttons_handler(update: Update, context: CallbackContext):
    # await update.callback_query.edit_message_reply_markup(None)
    await update.callback_query.answer()
    match update.callback_query.data:
        case "check_for_membership":
            await update.callback_query.edit_message_reply_markup(None)
            await check_if_member(update, context)

        case "description_generation":
            await update.effective_chat.send_message(texts.description_gen_welcome)
            return WAITING_FOR_PHOTO

        case "image_generation":
            await update.effective_chat.send_message(texts.image_gen_welcome)
            problem = texts.problems_descriptions[random.randint(0, len(texts.problems_descriptions)-1)]
            context.user_data['problem'] = problem
            await update.effective_chat.send_message(problem)
            return WAITING_FOR_IMAGE_PROMPT

        case 'gen_again':
            await send_description(update, context)

        case 'send_to_channel':
            await update.callback_query.edit_message_reply_markup(None)
            await context.bot.copy_message(message_id=update.callback_query.message.message_id, chat_id=TG_CHANNEL_ID, from_chat_id=update.effective_chat.id)


async def fallback_executor(update: Update, context: CallbackContext):
    await update.effective_chat.send_message("no handler is found")


async def generate_from_desc(update: Update, context: CallbackContext):
    if MACHINE_ROLE == 'PROD':
        image = openai_generation.image_from_prompt(update.message.text)
    else:
        with open('generated.png', 'rb') as f:
            image = f.read()
    image = pics.add_watermark(image)

    keyboard = [
            [InlineKeyboardButton("Отправить в канал", callback_data="send_to_channel")],
            [InlineKeyboardButton("Новая задача", callback_data="image_generation")],
            [InlineKeyboardButton("Сгенерировать описание", callback_data="description_generation")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    problem = context.user_data['problem']
    text = update.message.text

    msg = f'<b>Проблема:</b>\n{problem}\n\n\n<b>Решение:</b>\n{text}'

    await update.effective_chat.send_photo(image.getvalue(), caption=msg, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    return BUTTON_INPUT



def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                WAITING_FOR_PHOTO : [MessageHandler(filters.PHOTO, send_description), CallbackQueryHandler(buttons_handler)],
                BUTTON_INPUT : [CallbackQueryHandler(buttons_handler), MessageHandler(filters.PHOTO, send_description)],
                WAITING_FOR_IMAGE_PROMPT : [MessageHandler(filters.TEXT, generate_from_desc)]
            },
            fallbacks=[
                MessageHandler(filters.ALL, fallback_executor)
                ],
            )
    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
