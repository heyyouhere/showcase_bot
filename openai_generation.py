from openai import OpenAI
import base64
import requests
import os
api_key= os.getenv("OPENAI_TOKEN")


openai_headers = {
  "Content-Type": "application/json",
  "Authorization": f"Bearer {api_key}"
}


def describtion_of_image(image_path : str, prompt: str) -> str:
    # Getting the base64 string
    with open(image_path, "rb") as image_file:
        base64_image =  base64.b64encode(image_file.read()).decode('utf-8')
    payload = {
      "model": "gpt-4o",
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
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=openai_headers, json=payload)
    print(response.json())
    result = response.json()['choices'][0]['message']['content']
    return result

def image_from_prompt(prompt: str) -> str:
    payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024"
    }
    response = requests.post("https://api.openai.com/v1/images/generations", headers=openai_headers, json=payload)
    print(response.json())
    response.raise_for_status()
    image_url = response.json()["data"][0]['url']
    image_res = requests.get(image_url)
    return image_res.content


if __name__ == '__main__':
    # image_path = "./photo.jpeg"
    # prompt = 'Я отправлю тебе фотографию, твоя задача сгенерировать ироничную фразу используя контекст фотографии по типу "Я еду на работу, пока все смотрят Nornikel digital week". Фраза должна заканчиваться на "Пока все смотрят Nornikel digital week" и должна быть достаточно короткой, ответь только этой фразой ничего больше не пиши. Фраза ни в коем случае не должна осквернять или быть негативный в сторону Норникеля. Фраза должна быть позитивной.'
    # res = gererate_ai_description(image_path, prompt)
    # description = generate_ai_description("image_path.jpg", "A photo of a cute puppy playing with a ball.")
    # print(description)


    generated_image = generate_image_from_description("Чистильщик окон, который используюет реактивный ранец")
    with open("generated_image.jpg", "wb") as f:
        f.write(generated_image)
