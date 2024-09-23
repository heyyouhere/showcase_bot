from PIL import Image, ImageDraw, ImageFont
import textwrap
import io

target_size=(1024, 1024)

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
font_path = 'ttfirsneue-bold.ttf'


def create_card(photo_bytes: bytes, desc: str) -> io.BytesIO:
    background_image = Image.open(io.BytesIO(photo_bytes))
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
    font = ImageFont.truetype(font_path, size=31)
    drawText(draw, font, desc.upper(), (25, 925))
    output_bytes = io.BytesIO()
    background_image.save(output_bytes, format='PNG')
    return output_bytes


watermark_path = 'watermark.png'
watermark_image = Image.open(watermark_path)

def add_watermark(image_bytes: bytes) -> io.BytesIO:
    background_image = Image.open(io.BytesIO(image_bytes))
    background_image.paste(watermark_image, (0, 0), watermark_image)
    output_bytes = io.BytesIO()
    background_image.save(output_bytes, format='PNG')
    return output_bytes
