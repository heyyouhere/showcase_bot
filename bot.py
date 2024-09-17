from telegram.ext import Application, MessageHandler, filters, CommandHandler
import os
import requests
from PIL import Image, ImageDraw, ImageFont
import description_gen
import textwrap

TOKEN = os.getenv("TG_TOKEN")

prompt = 'Я отправлю тебе фотографию, твоя задача сгенерировать ироничную фразу используя контекст фотографии по типу "Я еду на работу, пока все смотрят Nornikel digital week". Фраза должна заканчиваться на "Пока все смотрят Nornikel digital week" и должна быть достаточно короткой, ответь только этой фразой ничего больше не пиши. Фраза ни в коем случае не должна осквернять или быть негативный в сторону Норникеля. Фраза должна быть позитивной.'

target_size=(1024, 1024)

async def start(update, context):
    await update.message.reply_text("Привет! Отправь фотку и получи смешное описание")

def drawText(draw, font, text : str, position : (int, int)):
    text_color = (255, 255, 255)
    text_size = draw.textbbox((0,0), text, font=font)
    print(text.split(','))
    for line in text.split(','):
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
    font = ImageFont.truetype(font_path, size=40)
    drawText(draw, font, desc.upper(), (60, 900))
    output_path= "output.png"
    background_image.save("output.png")
    return output_path



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
    # desc = "Я учу секреты продуктивности, пока все смотрят Nornikel digital week."
    output_path = create_card(image_path, desc)
    await update.effective_user.send_photo(photo=open(output_path, 'rb'), caption=desc)


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, send_description))
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
