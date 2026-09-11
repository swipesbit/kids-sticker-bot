import os
import cv2
import numpy as np
from PIL import Image
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile

# Ваш токен Telegram-бота
TOKEN = "8664542968:AAFjq8WlqQthIyxLv69BVPXGHCfremZ8zKw"

bot = Bot(token=TOKEN)
dp = Dispatcher()

def make_cartoon(input_path, output_path):
    img = cv2.imread(input_path)
    
    # Сглаживание цветов для мультяшного эффекта
    color = cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)
    
    # Выделение контуров
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 7)
    edges = cv2.adaptiveThreshold(
        blur, 255, 
        cv2.ADAPTIVE_THRESH_MEAN_C, 
        cv2.THRESH_BINARY, 
        blockSize=9, 
        C=2
    )
    
    edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    cartoon = cv2.bitwise_and(color, edges)
    
    cv2.imwrite(output_path, cartoon)
    
    # Подгонка под стандарт стикеров Telegram (512x512)
    pil_img = Image.open(output_path)
    pil_img = pil_img.resize((512, 512), Image.Resampling.LANCZOS)
    
    sticker_path = output_path.replace(".jpg", ".png")
    pil_img.save(sticker_path, "PNG")
    return sticker_path

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🎨 Привет! Я бот-мастер детских стикеров.\n"
        "Пришли мне любую фотографию или мем, а я превращу ее в мультяшный стикер!"
    )

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    await message.answer("🪄 Колдую над мультяшным стикером...")
    
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    
    input_file = f"downloads_{photo.file_unique_id}.jpg"
    output_file = f"cartoon_{photo.file_unique_id}.jpg"
    
    await bot.download(file_info, destination=input_file)
    
    try:
        final_sticker_path = make_cartoon(input_file, output_file)
        await message.answer_document(
            document=FSInputFile(final_sticker_path),
            caption="Вот твой мультяшный стикер! Готов для добавления в пак."
        )
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")
    finally:
        if os.path.exists(input_file): os.remove(input_file)
        if os.path.exists(output_file): os.remove(output_file)

async def main():
    print("Бот запущен и ждет сообщения!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())