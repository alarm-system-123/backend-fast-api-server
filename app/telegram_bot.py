"""Telegram bot module"""
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient

from data.config import Config
# pylint: disable=import-error

BOT_TOKEN = f"{Config.BOT_TOKEN}"
MONGO_URL = f"{Config.MONGO_URL}"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client.iot_security
gateways_collection = db.gateways


class SubscriptionFlow(StatesGroup): # pylint: disable=too-few-public-methods
    """Get information from telegram"""
    waiting_for_mac = State()
    waiting_for_password = State()

@dp.message(Command("start", "add_hub"))
async def start_cmd(message: Message, state: FSMContext):
    """Start telegram bot"""
    await message.answer(
        "👋 Вітаю в системі безпеки!\n"
        "Щоб додати хаб та отримувати сповіщення, надішліть його **MAC-адресу**.",
        parse_mode="Markdown"
    )
    await state.set_state(SubscriptionFlow.waiting_for_mac)


@dp.message(SubscriptionFlow.waiting_for_mac)
async def process_mac(message: Message, state: FSMContext):
    """write a pin code"""
    await state.update_data(mac_address=message.text.strip())
    await message.answer("🔒 Тепер введіть **PIN-код / Пароль** вашого хаба:")
    await state.set_state(SubscriptionFlow.waiting_for_password)


@dp.message(SubscriptionFlow.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    """write a pin code"""
    password = message.text.strip()
    data = await state.get_data()
    mac_address = data['mac_address']

    hub = await gateways_collection.find_one({"_id": mac_address})

    if not hub or hub.get("password") != password:
        await message.answer("❌ Неправильна MAC-адреса або пароль. Спробуйте ще раз: /add_hub")
        await state.clear()
        return

    chat_id = message.chat.id

    await gateways_collection.update_one(
        {"_id": mac_address},
        {"$addToSet": {"telegram_chat_ids": chat_id}}
    )

    await message.answer(f"✅ Успішно! Ви підписалися на сповіщення від хаба: "
                         f"`{mac_address}`", parse_mode="Markdown")
    await state.clear()

@dp.message(Command("my_hubs"))
async def list_hubs_cmd(message: Message):
    """list all hubs"""
    chat_id = message.chat.id

    cursor = gateways_collection.find({"telegram_chat_ids": chat_id})
    hubs = await cursor.to_list(length=100)

    if not hubs:
        await message.answer("📭 У вас немає підключених хабів. Натисніть /add_hub, щоб додати.")
        return

    text = "🏠 **Ваші підключені хаби:**\n\n"
    for h in hubs:
        text += f"🔹 `{h['_id']}`\n"

    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("remove_hub"))
async def remove_hub_cmd(message: Message):
    """remove a hub"""
    chat_id = message.chat.id
    cursor = gateways_collection.find({"telegram_chat_ids": chat_id})
    hubs = await cursor.to_list(length=100)

    if not hubs:
        await message.answer("📭 У вас немає підключених хабів для видалення.")
        return

    buttons = []
    for h in hubs:
        buttons.append([InlineKeyboardButton(text=f"❌ Видалити {h['_id']}",
                                             callback_data=f"del_{h['_id']}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer("Оберіть хаб, від якого хочете відписатися:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("del_"))
async def process_remove_hub(callback: CallbackQuery):
    """remove a hub"""
    mac_address = callback.data.split("_", 1)[1]
    chat_id = callback.message.chat.id

    await gateways_collection.update_one(
        {"_id": mac_address},
        {"$pull": {"telegram_chat_ids": chat_id}}
    )

    await callback.message.edit_text(f"🗑 Ви успішно відписалися від хаба: "
                                     f"`{mac_address}`", parse_mode="Markdown")
    await callback.answer()

async def main():
    """start telegram bot"""
    print("🤖 Telegram-бот запущено...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
