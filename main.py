import asyncio

from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import gspread
from oauth2client.service_account import ServiceAccountCredentials



BOT_TOKEN = "7054986465:AAFqsAOfgiOWC-BOtTOken-4CTGdM9Uc"

GOOGLE_SHEETS_CREDS = "credentials.json"  # Файл из Google Cloud
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1vEZ50apy1Mt9iYejuUyC7khO7QrmT6ILYRUpCJ_A7ok/edit?usp=sharing"


scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDS, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(SPREADSHEET_URL).sheet1


class Order(StatesGroup):
    weight = State()
    address = State()
    phone = State()

class SupportState(StatesGroup):
    waiting_for_message = State()

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Сделать заказ")],
            [KeyboardButton(text="🔄 Статус заказа")],
            [KeyboardButton(text="📞 Поддержка")]
        ],
        resize_keyboard=True
    )
    await message.answer("Добро пожаловать в бота доставки!", reply_markup=keyboard)


@dp.message(F.text == "📦 Сделать заказ")
async def make_order(message: types.Message, state: FSMContext):
    await message.answer("Введите вес посылки (кг):", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Order.weight)


@dp.message(Order.weight)
async def process_weight(message: types.Message, state: FSMContext):
    await state.update_data(weight=message.text)
    await message.answer("Введите адрес доставки:")
    await state.set_state(Order.address)


@dp.message(Order.address)
async def process_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer("Введите ваш телефон:")
    await state.set_state(Order.phone)


@dp.message(Order.phone)
async def process_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    sheet.append_row([message.from_user.id, data['weight'], data['address'], message.text])
    await message.answer(
        f"✅ Заказ оформлен! Номер: #{sheet.row_count}",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📦 Сделать заказ")],
                      [KeyboardButton(text="🔄 Статус заказа")],
                      [KeyboardButton(text="📞 Поддержка")]],

            resize_keyboard=True
        )
    )
    await state.clear()


@dp.message(F.text == "📞 Поддержка")
async def support(message: types.Message, state: FSMContext):
    await message.answer("Опишите проблему — оператор ответит в течение 5 минут.")
    await state.set_state(SupportState.waiting_for_message)


@dp.message(SupportState.waiting_for_message)
async def process_support_message(message: types.Message, state: FSMContext):


    typing_phrases = [
        "Дай-ка подумать...",
        "Сейчас посмотрим...",
        "Один момент..."
    ]


    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)


    for phrase in typing_phrases:
        temp_msg = await message.answer(phrase)
        await asyncio.sleep(1.5)
        await temp_msg.delete()
        await asyncio.sleep(0.5)


    final_text = "❤️ Не расстраивайся! Мы уже решаем твой вопрос!"
    temp_msg = await message.answer("...")

    for i in range(1, len(final_text) + 1):
        await temp_msg.edit_text(final_text[:i] + " ✍️")
        await asyncio.sleep(0.07)


    await temp_msg.edit_text(final_text)
    await asyncio.sleep(1)
    await message.answer("Всеее, поздравляем все ваши проблемы решены. Вам на карту отправили 10 000 000!")


if __name__ == '__main__':
    dp.run_polling(bot)