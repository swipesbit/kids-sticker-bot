import os
import requests
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from PIL import Image, ImageDraw, ImageFilter
from rembg import remove, new_session
import asyncio

TOKEN = os.getenv("TOKEN")
UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

if not TOKEN:
    raise ValueError("Не задан токен бота в переменных окружения (TOKEN)!")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Создаем сессию с легкой моделью u2netp для экономии памяти на сервере
rembg_session = new_session("u2netp")

def make_real_sticker(input_path: str, output_path: str):
    with open(input_path, 'rb') as i:
        input_image = i.read()
    
    # Удаляем фон с помощью легкой модели
    output_image_bytes = remove(input_image, session=rembg_session)
    
    import io
    img = Image.open(io.BytesIO(output_image_bytes)).convert("RGBA")
    
    # Вписываем в размер 512x512 с сохранением пропорций
    img.thumbnail((512, 512), Image.Resampling.LANCZOS)
    final_img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    
    paste_x = (512 - img.width) // 2
    paste_y = (512 - img.height) // 2
    final_img.paste(img, (paste_x, paste_y), img)

    # Добавляем белую обводку
    alpha = final_img.getchannel("A")
    mask = alpha.point(lambda p: 255 if p > 0 else 0)
    
    border_width = 6
    dilated_mask = mask.filter(ImageFilter.MaxFilter(border_width * 2 + 1))
    
    border_layer = Image.new("RGBA", (512, 512), (255, 255, 255, 255))
    border_layer.putalpha(dilated_mask)
    
    sticker_with_border = Image.alpha_composite(border_layer, final_img)
    sticker_with_border.save(output_path, "PNG")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот-мастер детских стикеров.\n\n"
        "Используй команду `/find [тема]`, чтобы создать готовый стикер!\n"
        "Пример: `/find cute cartoon dog`"
    )

@dp.message(Command("find"))
async def cmd_find(message: types.Message):
    text_parts = message.text.split(maxsplit=1)
    if len(text_parts) < 2:
        await message.answer("Укажи тему поиска, например:\n`/find funny bear`")
        return
    
    query = text_parts[1]
    
    if not UNSPLASH_KEY:
        await message.answer("Ошибка: не настроен ключ UNSPLASH_ACCESS_KEY.")
        return

    url = f"https://api.unsplash.com/photos/random?query={query}&client_id={UNSPLASH_KEY}"
    
    try:
        await message.answer("Ищу картинку и делаю стикер...")
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            image_url = data["urls"]["regular"]
            
            img_data = requests.get(image_url).content
            raw_path = "raw_image.jpg"
            sticker_path = "sticker.png"
            
            with open(raw_path, "wb") as handler:
                handler.write(img_data)
            
            # Обрабатываем и создаем стикер
            make_real_sticker(raw_path, sticker_path)
            
            sticker_file = types.FSInputFile(sticker_path)
            await message.answer_sticker(sticker=sticker_file)
            await message.answer(f"✨ Готовый стикер по запросу: *{query}*")
        else:
            await message.answer("Ничего не нашлось, попробуй другое слово.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    await message.answer("Фото получено! Скоро добавлю автогенерацию для загруженных фото.")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())