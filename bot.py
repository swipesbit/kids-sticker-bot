import os
import requests
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from PIL import Image, ImageDraw
import asyncio

TOKEN = os.getenv("TOKEN")
UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

if not TOKEN:
    raise ValueError("Не задан токен бота в переменных окружения (TOKEN)!")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Функция превращения картинки в стикер (белая обводка + скругленные углы)
def make_sticker(input_path: str, output_path: str):
    img = Image.open(input_path).convert("RGBA")
    w, h = img.size
    
    # Скругляем углы исходной картинки
    radius = int(min(w, h) * 0.1)
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (w, h)], radius=radius, fill=255)
    img.putalpha(mask)
    
    # Создаем белую подложку (эффект наклейки-стикера)
    padding = 25
    bg_w, bg_h = w + padding * 2, h + padding * 2
    sticker_bg = Image.new("RGBA", (bg_w, bg_h), (255, 255, 255, 0))
    
    bg_mask = Image.new("L", (bg_w, bg_h), 0)
    bg_draw = ImageDraw.Draw(bg_mask)
    bg_draw.rounded_rectangle([(0, 0), (bg_w, bg_h)], radius=radius + 10, fill=255)
    sticker_bg.putalpha(bg_mask)
    
    # Рисуем сплошную белую заливку подложки
    solid_bg = Image.new("RGBA", (bg_w, bg_h), (255, 255, 255, 255))
    solid_bg.putalpha(bg_mask)
    
    # Накладываем картинку на белую подложку
    solid_bg.paste(img, (padding, padding), img)
    solid_bg.save(output_path, "PNG")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот-мастер детских стикеров.\n\n"
        "Используй команду `/find [тема]`, чтобы я нашел картинку и сделал из нее готовый стикер!\n"
        "Пример: `/find cute cat`"
    )

@dp.message(Command("find"))
async def cmd_find(message: types.Message):
    text_parts = message.text.split(maxsplit=1)
    if len(text_parts) < 2:
        await message.answer("Пожалуйста, укажи ключевое слово. Пример:\n`/find funny puppy`")
        return
    
    query = text_parts[1]
    
    if not UNSPLASH_KEY:
        await message.answer("Ошибка: не настроен ключ UNSPLASH_ACCESS_KEY.")
        return

    url = f"https://api.unsplash.com/photos/random?query={query}&client_id={UNSPLASH_KEY}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            image_url = data["urls"]["regular"]
            
            # Скачиваем исходное фото во временный файл
            img_data = requests.get(image_url).content
            raw_path = "raw_image.jpg"
            sticker_path = "sticker.png"
            
            with open(raw_path, "wb") as handler:
                handler.write(img_data)
            
            # Превращаем в стикер
            make_sticker(raw_path, sticker_path)
            
            # Отправляем готовый стикер (как документ, чтобы Telegram не сжимал PNG с прозрачностью)
            photo_file = types.FSInputFile(sticker_path)
            await message.answer_document(
                document=photo_file, 
                caption=f"✨ Готовый стикер по запросу: *{query}*"
            )
        else:
            await message.answer("Ничего не нашлось, попробуй другое слово.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    await message.answer("Фото получено! Скоро здесь будет автогенерация стикера.")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())