from openai import OpenAI
import base64
import requests
import httpx
import os
import random

api_key= os.getenv("OPENAI_TOKEN")
client = httpx.AsyncClient(timeout=None)

openai_headers = {
  "Content-Type": "application/json",
  "Cache-Control": "no-cache",
  "Authorization": f"Bearer {api_key}"
}


async def description_of_image(image_bytes : bytes, prompt: str) -> str:
    # Getting the base64 string
    base64_image =  base64.b64encode(image_bytes).decode('utf-8')
    payload = {
      "model": "gpt-4o",
      "temperature": 1.1,
      "messages": [
        {
          "role": "user",
          "content": [
            {
              "type": 'text',
              "text": prompt
            },
            {
              "type": "image_url",
              "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
              }
            }
          ]
        }
      ],
      "max_tokens": 300
    }

    response = await client.post("https://api.openai.com/v1/chat/completions", headers=openai_headers, json=payload)
    result = response.json()['choices'][0]['message']['content']
    return result

async def image_from_prompt(prompt: str) -> bytes:
    payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024"
    }
    response = await client.post("https://api.openai.com/v1/images/generations", headers=openai_headers, json=payload)
    image_url = response.json()["data"][0]['url']
    image_res = await client.get(image_url)
    return image_res.content


if __name__ == '__main__':
    image_path = "./photo.jpeg"
    prompt = 'Я отправлю тебе фотографию, твоя задача сгенерировать ироничную фразу используя контекст фотографии по типу "Я еду на работу, пока все смотрят Nornikel digital week". Фраза должна заканчиваться на "Пока все смотрят Nornikel digital week" и должна быть достаточно короткой, ответь только этой фразой ничего больше не пиши. Фраза ни в коем случае не должна осквернять или быть негативный в сторону Норникеля. Фраза должна быть позитивной.'
    with open(image_path, 'rb') as f:
        description = description_of_image(f.readall(), prompt)

    generated_image = generate_image_from_description("Чистильщик окон, который используюет реактивный ранец")
    with open("generated_image.jpg", "wb") as f:
        f.write(generated_image)
