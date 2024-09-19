from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardButton, KeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext, Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, ConversationHandler, MessageHandler
import os
import requests
from PIL import Image, ImageDraw, ImageFont
import openai_generation
import textwrap

TOKEN = os.getenv("TG_TOKEN")
TG_CHANNEL_ID = os.getenv("TG_CHANNEL_ID")
MACHINE_ROLE = os.getenv("MACHINE_ROLE")


prompt = 'Я отправлю тебе фотографию, твоя задача сгенерировать ироничную фразу используя контекст фотографии по типу "Я еду на работу, пока все смотрят Nornikel digital week". Фраза должна заканчиваться на "Пока все смотрят Nornikel digital week" и должна быть достаточно короткой, ответь только этой фразой ничего больше не пиши. Фраза ни в коем случае не должна осквернять или быть негативный в сторону Норникеля. Фраза должна быть позитивной.'

target_size=(1024, 1024)


WAITING_FOR_PHOTO, BUTTON_INPUT = range(2)

async def start(update, context):
    await update.message.reply_text("Привет! Отправь фотку и получи смешное описание")
    return WAITING_FOR_PHOTO

def drawText(draw, font, text : str, position : (int, int)):
    text_color = (255, 255, 255)
    text_size = draw.textbbox((0,0), text, font=font)
    #TODO: ADD ',' at the end of first line normaly
    need_sym = True
    for line in text.split(','):
        if need_sym:
            draw.text(position, line.strip()+',', fill=text_color, font=font)
            need_sym = False
        else:
            draw.text(position, line.strip(), fill=text_color, font=font)
        position = (position[0], position[1]+font.size)


mask_path = 'mask.png'
mask_image = Image.open(mask_path)
font_path = 'afuturaortobold.ttf'


def create_card(image_path, desc):
    background_image = Image.open(image_path)

    size = background_image.size
    x = min(size[0], size[1])
    factor = target_size[0]/x
    new_size = (int(size[0]*factor), int(size[1]*factor))
    background_image = background_image.resize(new_size)
    if new_size[0] == target_size[0]:
        crop_box = (0, (new_size[1] - target_size[1])/2, new_size[0],  new_size[1]/2 + target_size[1]/2)
    else:
        crop_box = ((new_size[0] - target_size[0])/2, 0,  new_size[0]/2 + target_size[0]/2, new_size[1])
    background_image = background_image.crop(crop_box)

    background_image.paste(mask_image, (0, 0), mask_image)
    draw = ImageDraw.Draw(background_image)
    font = ImageFont.truetype(font_path, size=37)
    drawText(draw, font, desc.upper(), (60, 900))
    output_path= "output.png"
    background_image.save("output.png")
    return output_path

async def send_description(update, context):
    message = update.message if update.message != None else update.callback_query.message
    user_id = message.from_user.id
    photo = message.photo[-1]
    file_id = photo.file_id
    file_name = f"{user_id}_{file_id}.jpg"
    new_file = await context.bot.getFile(file_id)
    r = requests.get(new_file.file_path)
    image_path = os.path.join("./inputs", file_name)
    with open(image_path, "wb") as out_file:
        out_file.write(r.content)
    if MACHINE_ROLE != 'TEST':
        desc = openai_generation.describtion_of_image(image_path, prompt)
    else:
        desc = "Я учу секреты продуктивности, пока все смотрят Nornikel digital week."

    output_path = create_card(image_path, desc)
    keyboard = [
            [InlineKeyboardButton("Сгенерировать ещё", callback_data="gen_again")],
            [InlineKeyboardButton("Отправить в канал", callback_data="send_to_channel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_user.send_photo(photo=open(output_path, 'rb'), reply_markup=reply_markup)
    return BUTTON_INPUT




async def buttons_handler(update: Update, context: CallbackContext):
    # await update.callback_query.edit_message_reply_markup(None)
    await update.callback_query.answer()
    match update.callback_query.data:
        case 'gen_again':
            await send_description(update, context)
        case 'send_to_channel':
            await context.bot.copy_message(message_id=update.callback_query.message.message_id, chat_id=TG_CHANNEL_ID, from_chat_id=update.effective_chat.id)

async def fallback_executor(update: Update, context: CallbackContext):
    await update.effective_chat.send_message("no handler is found")

async def generate_from_desc(update: Update, context: CallbackContext):
    if MACHINE_ROLE != 'TEST':
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
