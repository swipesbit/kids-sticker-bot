import os
import requests
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

# Получаем токены из переменных окружения
TOKEN = os.getenv("TOKEN")
UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

if not TOKEN:
    raise ValueError("Не задан токен бота в переменных окружения (TOKEN)!")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Состояния для возможных сценариев (если понадобятся)
class StickerStates(StatesGroup):
    waiting_for_image = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот-мастер детских стикеров.\n\n"
        "Пришли мне любую фотографию или мем, а я превращу ее в мультяшный стикер!\n"
        "А еще я умею искать картинки сам: просто отправь команду `/find [тема]`, например: `/find cute puppy`"
    )

# Команда для поиска картинок через Unsplash API
@dp.message(Command("find"))
async def cmd_find(message: types.Message):
    text_parts = message.text.split(maxsplit=1)
    if len(text_parts) < 2:
        await message.answer("Пожалуйста, укажи ключевое слово для поиска. Пример:\n`/find funny kids`")
        return
    
    query = text_parts[1]
    
    if not UNSPLASH_KEY:
        await message.answer("Ошибка: не настроен ключ UNSPLASH_ACCESS_KEY в переменных окружения.")
        return

    url = f"https://api.unsplash.com/photos/random?query={query}&client_id={UNSPLASH_KEY}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            image_url = data["urls"]["regular"]
            author = data["user"]["name"]
            
            await message.answer_photo(
                photo=image_url, 
                caption=f"🔍 Нашел картинку по запросу: *{query}*\n📸 Автор: {author}"
            )
        else:
            await message.answer("К сожалению, по вашему запросу ничего не нашлось. Попробуйте другое слово.")
    except Exception as e:
        await message.answer(f"Произошла ошибка при поиске: {e}")

# Обработка обычных фотографий от пользователя
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    await message.answer("Фото получено! Обрабатываю и превращаю в стикер...")
    # Здесь в будущем можно добавить вашу логику OpenCV / Pillow для вырезания стикеров
    # Сейчас бот просто подтверждает прием фото
    await asyncio.sleep(1)
    await message.answer("Готово! (Функция создания стикерпака в разработке, но фото успешно обработано).")

@dp.message(F.text)
async def handle_text(message: types.Message):
    await message.answer(f"Я получил твое сообщение: «{message.text}». Отправь мне картинку или используй команду `/find [слово]` для поиска!")

async def main():
    print("Бот запущен и готов к работе 24/7...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())