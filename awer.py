import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8604442843:AAHce1oVXjIuie1fno4dfGm8qYZEshG8gak"
ADMIN_USERNAME = "@zadkddid"
ADMIN_CARD = "2200 7010 9468 2025"
EXCHANGE_RATE = 0.7  # 1 STAR = 0.7 рубля
ADMIN_IDS = [1417003901,7065329693]

# Цены на Telegram Premium
PREMIUM_PRICES = {
    "1_month": {"name": "1 месяц", "price": 150, "duration": "30 дней"},
    "3_months": {"name": "3 месяца", "price": 400, "duration": "90 дней"},
    "1_year": {"name": "1 год", "price": 800, "duration": "365 дней"}
}

# Инициализация бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Состояния
class Form(StatesGroup):
    waiting_for_buy_amount = State()
    waiting_for_buy_screenshot = State()
    waiting_for_sell_amount = State()
    waiting_for_sell_screenshot = State()
    waiting_for_premium_screenshot = State()

# Проверка админа
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# Клавиатуры
def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Купить STARS")],
            [KeyboardButton(text="💰 Продать STARS")],
            [KeyboardButton(text="⭐ Telegram Premium")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )

def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

def admin_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Заявки STARS")],
            [KeyboardButton(text="⭐ Заявки Premium")],
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="🔙 Выйти из админки")]
        ],
        resize_keyboard=True
    )

def admin_requests_keyboard(request_id: int, req_type: str = "stars"):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{req_type}_{request_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{req_type}_{request_id}")
            ]
        ]
    )

def premium_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"📅 1 месяц - {PREMIUM_PRICES['1_month']['price']} руб.", callback_data="premium_1_month")],
            [InlineKeyboardButton(text=f"📅 3 месяца - {PREMIUM_PRICES['3_months']['price']} руб.", callback_data="premium_3_months")],
            [InlineKeyboardButton(text=f"📅 1 год - {PREMIUM_PRICES['1_year']['price']} руб.", callback_data="premium_1_year")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="premium_cancel")]
        ]
    )

# Хранилище заявок (в памяти вместо БД)
requests_db = []
premium_requests_db = []
request_counter = 1
premium_counter = 1

# ========== ПОЛЬЗОВАТЕЛЬСКАЯ ЧАСТЬ ==========

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    
    if is_admin(message.from_user.id):
        await message.answer(
            "👑 <b>Админ-панель</b>\n\n"
            "Выберите действие:",
            reply_markup=admin_main_keyboard()
        )
        return
    
    await message.answer(
        "🌟 <b>Добро пожаловать в Magazin Stars!</b>\n\n"
        "• <b>🛒 Купить STARS</b> - покупка звезд за рубли\n"
        "• <b>💰 Продать STARS</b> - продажа звезд за рубли\n"
        "• <b>⭐ Telegram Premium</b> - покупка Premium подписки\n"
        "• <b>ℹ️ Помощь</b> - инструкция\n\n"
        f"💰 <b>Курс STARS:</b> 1 STAR = {EXCHANGE_RATE} руб.\n"
        f"⭐ <b>Premium:</b> от 150 руб.\n\n"
        "<b>Выберите действие:</b>",
        reply_markup=main_keyboard()
    )

@dp.message(Command("admin"))
async def admin_command(message: types.Message):
    if is_admin(message.from_user.id):
        await message.answer(
            "👑 <b>Админ-панель</b>\n\n"
            "Выберите действие:",
            reply_markup=admin_main_keyboard()
        )
    else:
        await message.answer("⛔ У вас нет доступа к админ-панели.")

# Помощь
@dp.message(F.text == "ℹ️ Помощь")
async def help_command(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"📋 <b>Инструкция:</b>\n\n"
        f"<b>🛒 Купить STARS:</b>\n"
        f"1. Нажмите 'Купить STARS'\n"
        f"2. Введите количество\n"
        f"3. Переведите {ADMIN_CARD}\n"
        f"4. Отправьте скриншот\n\n"
        f"<b>💰 Продать STARS:</b>\n"
        f"1. Нажмите 'Продать STARS'\n"
        f"2. Введите количество\n"
        f"3. Отправьте STARS подарком на {ADMIN_USERNAME}\n"
        f"4. Отправьте скриншот\n\n"
        f"<b>⭐ Telegram Premium:</b>\n"
        f"1. Нажмите 'Telegram Premium'\n"
        f"2. Выберите срок\n"
        f"3. Переведите {ADMIN_CARD}\n"
        f"4. Отправьте скриншот\n\n"
        f"💰 <b>Курс STARS:</b> 1 STAR = {EXCHANGE_RATE} руб.\n"
        f"⭐ <b>Цены Premium:</b>\n"
        f"• 1 месяц - {PREMIUM_PRICES['1_month']['price']} руб.\n"
        f"• 3 месяца - {PREMIUM_PRICES['3_months']['price']} руб.\n"
        f"• 1 год - {PREMIUM_PRICES['1_year']['price']} руб.",
        reply_markup=main_keyboard()
    )

# ========== ПОКУПКА STARS ==========

@dp.message(F.text == "🛒 Купить STARS")
async def buy_stars_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"🌟 <b>Покупка STARS</b>\n\n"
        f"💰 <b>Курс:</b> 1 STAR = {EXCHANGE_RATE} руб.\n\n"
        f"<b>Введите количество STARS:</b>\n"
        f"<i>Например: 100, 50, 1000</i>",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(Form.waiting_for_buy_amount)

@dp.message(Form.waiting_for_buy_amount)
async def process_buy_amount(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Покупка отменена.", reply_markup=main_keyboard())
        return
    
    try:
        amount = float(message.text.replace(',', '.'))
        
        if amount < 10:
            await message.answer(
                "❌ <b>Минимальная сумма 10 STARS!</b>\n\n"
                "Введите количество STARS:",
                reply_markup=cancel_keyboard()
            )
            return
        
        if amount > 10000:
            await message.answer(
                "❌ <b>Максимальная сумма 10,000 STARS!</b>\n\n"
                "Введите количество STARS:",
                reply_markup=cancel_keyboard()
            )
            return
        
        total_rub = round(amount * EXCHANGE_RATE, 2)
        await state.update_data(amount=amount, total_rub=total_rub)
        
        await message.answer(
            f"✅ <b>Расчет стоимости:</b>\n\n"
            f"• Количество STARS: <b>{amount:.2f}</b>\n"
            f"• Курс: 1 STAR = <b>{EXCHANGE_RATE} руб.</b>\n"
            f"• Итого к оплате: <b>{total_rub:.2f} руб.</b>\n\n"
            f"<b>Переведите на карту:</b>\n"
            f"<code>{ADMIN_CARD}</code>\n\n"
            f"📸 <b>После перевода отправьте скриншот</b>",
            reply_markup=cancel_keyboard()
        )
        await state.set_state(Form.waiting_for_buy_screenshot)
        
    except ValueError:
        await message.answer(
            "❌ <b>Неверный формат!</b>\n\n"
            "Введите число (например: 100, 50.5):",
            reply_markup=cancel_keyboard()
        )

@dp.message(Form.waiting_for_buy_screenshot)
async def process_buy_screenshot(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Покупка отменена.", reply_markup=main_keyboard())
        return
    
    if not message.photo:
        await message.answer(
            "❌ <b>Отправьте скриншот перевода как фото!</b>",
            reply_markup=cancel_keyboard()
        )
        return
    
    global request_counter
    data = await state.get_data()
    amount = data.get('amount', 0)
    total_rub = data.get('total_rub', 0)
    
    # Сохраняем заявку
    request_id = request_counter
    request_counter += 1
    
    request_data = {
        'id': request_id,
        'user_id': message.from_user.id,
        'username': message.from_user.username,
        'first_name': message.from_user.first_name,
        'type': 'buy',
        'amount': amount,
        'total_rub': total_rub,
        'photo_id': message.photo[-1].file_id,
        'status': 'pending',
        'created_at': datetime.now().strftime('%H:%M %d.%m.%Y')
    }
    requests_db.append(request_data)
    
    # Отправляем уведомление админам
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🛒 <b>НОВАЯ ЗАЯВКА НА ПОКУПКУ STARS #{request_id}</b>\n\n"
                f"👤 Пользователь: @{message.from_user.username or 'нет'} ({message.from_user.first_name})\n"
                f"📊 Количество: {amount} STARS\n"
                f"💰 Сумма: {total_rub} руб.\n"
                f"⏰ Время: {request_data['created_at']}\n"
                f"🆔 User ID: {message.from_user.id}",
                reply_markup=admin_requests_keyboard(request_id, "stars")
            )
            await bot.send_photo(admin_id, message.photo[-1].file_id)
        except Exception as e:
            logger.error(f"Ошибка отправки админу {admin_id}: {e}")
    
    await message.answer(
        f"✅ <b>Заявка #{request_id} на покупку STARS создана!</b>\n\n"
        f"📋 <b>Детали:</b>\n"
        f"• Покупка: <b>{amount:.2f} STARS</b>\n"
        f"• Сумма: <b>{total_rub:.2f} руб.</b>\n\n"
        f"⏱️ <b>Администратор проверит в течение 3 минут!</b>",
        reply_markup=main_keyboard()
    )
    
    await state.clear()

# ========== ПРОДАЖА STARS ==========

@dp.message(F.text == "💰 Продать STARS")
async def sell_stars_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"🌟 <b>Продажа STARS</b>\n\n"
        f"💰 <b>Курс:</b> 1 STAR = {EXCHANGE_RATE} руб.\n\n"
        f"<b>Введите количество STARS:</b>\n"
        f"<i>Например: 100, 50, 1000</i>",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(Form.waiting_for_sell_amount)

@dp.message(Form.waiting_for_sell_amount)
async def process_sell_amount(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Продажа отменена.", reply_markup=main_keyboard())
        return
    
    try:
        amount = float(message.text.replace(',', '.'))
        
        if amount < 10:
            await message.answer(
                "❌ <b>Минимальная сумма 10 STARS!</b>\n\n"
                "Введите количество STARS:",
                reply_markup=cancel_keyboard()
            )
            return
        
        if amount > 10000:
            await message.answer(
                "❌ <b>Максимальная сумма 10,000 STARS!</b>\n\n"
                "Введите количество STARS:",
                reply_markup=cancel_keyboard()
            )
            return
        
        total_rub = round(amount * EXCHANGE_RATE, 2)
        await state.update_data(amount=amount, total_rub=total_rub)
        
        await message.answer(
            f"✅ <b>Расчет стоимости:</b>\n\n"
            f"• Количество STARS: <b>{amount:.2f}</b>\n"
            f"• Курс: 1 STAR = <b>{EXCHANGE_RATE} руб.</b>\n"
            f"• Итого к выплате: <b>{total_rub:.2f} руб.</b>\n\n"
            f"<b>Отправьте STARS подарком на:</b>\n"
            f"{ADMIN_USERNAME}\n\n"
            f"📸 <b>После отправки пришлите скриншот</b>",
            reply_markup=cancel_keyboard()
        )
        await state.set_state(Form.waiting_for_sell_screenshot)
        
    except ValueError:
        await message.answer(
            "❌ <b>Неверный формат!</b>\n\n"
            "Введите число (например: 100, 50.5):",
            reply_markup=cancel_keyboard()
        )

@dp.message(Form.waiting_for_sell_screenshot)
async def process_sell_screenshot(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Продажа отменена.", reply_markup=main_keyboard())
        return
    
    if not message.photo:
        await message.answer(
            "❌ <b>Отправьте скриншот отправки STARS как фото!</b>",
            reply_markup=cancel_keyboard()
        )
        return
    
    global request_counter
    data = await state.get_data()
    amount = data.get('amount', 0)
    total_rub = data.get('total_rub', 0)
    
    # Сохраняем заявку
    request_id = request_counter
    request_counter += 1
    
    request_data = {
        'id': request_id,
        'user_id': message.from_user.id,
        'username': message.from_user.username,
        'first_name': message.from_user.first_name,
        'type': 'sell',
        'amount': amount,
        'total_rub': total_rub,
        'photo_id': message.photo[-1].file_id,
        'status': 'pending',
        'created_at': datetime.now().strftime('%H:%M %d.%m.%Y')
    }
    requests_db.append(request_data)
    
    # Отправляем уведомление админам
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"💰 <b>НОВАЯ ЗАЯВКА НА ПРОДАЖУ STARS #{request_id}</b>\n\n"
                f"👤 Пользователь: @{message.from_user.username or 'нет'} ({message.from_user.first_name})\n"
                f"📊 Количество: {amount} STARS\n"
                f"💰 Сумма: {total_rub} руб.\n"
                f"⏰ Время: {request_data['created_at']}\n"
                f"🆔 User ID: {message.from_user.id}",
                reply_markup=admin_requests_keyboard(request_id, "stars")
            )
            await bot.send_photo(admin_id, message.photo[-1].file_id)
        except Exception as e:
            logger.error(f"Ошибка отправки админу {admin_id}: {e}")
    
    await message.answer(
        f"✅ <b>Заявка #{request_id} на продажу STARS создана!</b>\n\n"
        f"📋 <b>Детали:</b>\n"
        f"• Продажа: <b>{amount:.2f} STARS</b>\n"
        f"• Сумма: <b>{total_rub:.2f} руб.</b>\n\n"
        f"⏱️ <b>Администратор проверит в течение 3 минут!</b>",
        reply_markup=main_keyboard()
    )
    
    await state.clear()

# ========== TELEGRAM PREMIUM ==========

@dp.message(F.text == "⭐ Telegram Premium")
async def premium_start(message: types.Message, state: FSMContext):
    await state.clear()
    
    text = (
        "⭐ <b>Telegram Premium</b>\n\n"
        "Выберите срок подписки:\n\n"
        f"📅 <b>1 месяц</b> - {PREMIUM_PRICES['1_month']['price']} руб.\n"
        f"📅 <b>3 месяца</b> - {PREMIUM_PRICES['3_months']['price']} руб.\n"
        f"📅 <b>1 год</b> - {PREMIUM_PRICES['1_year']['price']} руб."
    )
    
    await message.answer(text, reply_markup=premium_keyboard())

@dp.callback_query(F.data.startswith("premium_"))
async def premium_callback(callback: CallbackQuery, state: FSMContext):
    if callback.data == "premium_cancel":
        await callback.message.delete()
        await callback.message.answer("❌ Покупка Premium отменена.", reply_markup=main_keyboard())
        await callback.answer()
        return
    
    premium_type = callback.data.replace("premium_", "")
    
    if premium_type not in PREMIUM_PRICES:
        await callback.answer("❌ Неверный тип подписки!", show_alert=True)
        return
    
    price = PREMIUM_PRICES[premium_type]["price"]
    duration = PREMIUM_PRICES[premium_type]["duration"]
    name = PREMIUM_PRICES[premium_type]["name"]
    
    await state.update_data(premium_type=premium_type, price=price, name=name, duration=duration)
    
    await callback.message.delete()
    await callback.message.answer(
        f"⭐ <b>Telegram Premium - {name}</b>\n\n"
        f"💰 <b>Сумма к оплате:</b> {price} руб.\n"
        f"📅 <b>Срок:</b> {duration}\n\n"
        f"<b>Переведите на карту:</b>\n"
        f"<code>{ADMIN_CARD}</code>\n\n"
        f"📸 <b>После перевода отправьте скриншот</b>",
        reply_markup=cancel_keyboard()
    )
    
    await state.set_state(Form.waiting_for_premium_screenshot)
    await callback.answer()

@dp.message(Form.waiting_for_premium_screenshot)
async def process_premium_screenshot(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Покупка Premium отменена.", reply_markup=main_keyboard())
        return
    
    if not message.photo:
        await message.answer(
            "❌ <b>Отправьте скриншот перевода как фото!</b>",
            reply_markup=cancel_keyboard()
        )
        return
    
    global premium_counter
    data = await state.get_data()
    name = data.get('name', 'Premium')
    price = data.get('price', 0)
    premium_type = data.get('premium_type', '')
    
    # Сохраняем заявку
    request_id = premium_counter
    premium_counter += 1
    
    premium_data = {
        'id': request_id,
        'user_id': message.from_user.id,
        'username': message.from_user.username,
        'first_name': message.from_user.first_name,
        'premium_type': premium_type,
        'name': name,
        'total_rub': price,
        'photo_id': message.photo[-1].file_id,
        'status': 'pending',
        'created_at': datetime.now().strftime('%H:%M %d.%m.%Y')
    }
    premium_requests_db.append(premium_data)
    
    # Отправляем уведомление админам
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"⭐ <b>НОВАЯ ЗАЯВКА НА PREMIUM #{request_id}</b>\n\n"
                f"👤 Пользователь: @{message.from_user.username or 'нет'} ({message.from_user.first_name})\n"
                f"📊 Тариф: {name}\n"
                f"💰 Сумма: {price} руб.\n"
                f"⏰ Время: {premium_data['created_at']}\n"
                f"🆔 User ID: {message.from_user.id}",
                reply_markup=admin_requests_keyboard(request_id, "premium")
            )
            await bot.send_photo(admin_id, message.photo[-1].file_id)
        except Exception as e:
            logger.error(f"Ошибка отправки админу {admin_id}: {e}")
    
    await message.answer(
        f"✅ <b>Заявка #{request_id} на Premium создана!</b>\n\n"
        f"📋 <b>Детали:</b>\n"
        f"• Тариф: <b>{name}</b>\n"
        f"• Сумма: <b>{price} руб.</b>\n"
        f"• Срок: <b>{data.get('duration')}</b>\n\n"
        f"⏱️ <b>Администратор проверит платеж в течение 3 минут!</b>\n\n"
        f"После подтверждения вы получите Premium подписку. 🌟",
        reply_markup=main_keyboard()
    )
    
    await state.clear()

# ========== АДМИН-ПАНЕЛЬ ==========

# 📋 Заявки STARS
@dp.message(F.text == "📋 Заявки STARS")
async def admin_stars_requests(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    pending_requests = [r for r in requests_db if r['status'] == 'pending']
    
    if not pending_requests:
        await message.answer(
            "✅ <b>Нет активных заявок на STARS</b>",
            reply_markup=admin_main_keyboard()
        )
        return
    
    for req in pending_requests:
        type_icon = "🛒" if req['type'] == 'buy' else "💰"
        type_text = "ПОКУПКА" if req['type'] == 'buy' else "ПРОДАЖА"
        
        text = (
            f"{type_icon} <b>Заявка #{req['id']}</b>\n"
            f"👤 {req['first_name']} (@{req['username'] or 'нет'})\n"
            f"🆔 ID: {req['user_id']}\n"
            f"📊 {type_text}: {req['amount']} STARS\n"
            f"💰 Сумма: {req['total_rub']} руб.\n"
            f"⏰ {req['created_at']}\n"
        )
        
        await message.answer(text, reply_markup=admin_requests_keyboard(req['id'], "stars"))

# ⭐ Заявки Premium
@dp.message(F.text == "⭐ Заявки Premium")
async def admin_premium_requests(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    pending_requests = [r for r in premium_requests_db if r['status'] == 'pending']
    
    if not pending_requests:
        await message.answer(
            "✅ <b>Нет активных заявок на Premium</b>",
            reply_markup=admin_main_keyboard()
        )
        return
    
    for req in pending_requests:
        text = (
            f"⭐ <b>Заявка #{req['id']}</b>\n"
            f"👤 {req['first_name']} (@{req['username'] or 'нет'})\n"
            f"🆔 ID: {req['user_id']}\n"
            f"📊 Тариф: {req['name']}\n"
            f"💰 Сумма: {req['total_rub']} руб.\n"
            f"⏰ {req['created_at']}\n"
        )
        
        await message.answer(text, reply_markup=admin_requests_keyboard(req['id'], "premium"))

# 📊 Статистика
@dp.message(F.text == "📊 Статистика")
async def admin_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    total_users = set()
    for req in requests_db:
        total_users.add(req['user_id'])
    for req in premium_requests_db:
        total_users.add(req['user_id'])
    
    pending_stars = len([r for r in requests_db if r['status'] == 'pending'])
    pending_premium = len([r for r in premium_requests_db if r['status'] == 'pending'])
    
    text = (
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: {len(total_users)}\n"
        f"📋 Всего заявок STARS: {len(requests_db)}\n"
        f"⭐ Всего заявок Premium: {len(premium_requests_db)}\n"
        f"⏳ Ожидают обработки:\n"
        f"   • STARS: {pending_stars}\n"
        f"   • Premium: {pending_premium}\n"
    )
    
    await message.answer(text, reply_markup=admin_main_keyboard())

# 🔙 Выйти из админки
@dp.message(F.text == "🔙 Выйти из админки")
async def admin_exit(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "👋 <b>Выход из админ-панели</b>",
        reply_markup=main_keyboard()
    )

# Обработка callback от админа
@dp.callback_query(F.data.startswith(("approve_", "reject_")))
async def handle_admin_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа!", show_alert=True)
        return
    
    data_parts = callback.data.split("_", 2)
    if len(data_parts) != 3:
        await callback.answer("❌ Ошибка данных!", show_alert=True)
        return
    
    action, req_type, request_id_str = data_parts
    request_id = int(request_id_str)
    
    if req_type == "stars":
        # Поиск заявки в requests_db
        request = None
        for r in requests_db:
            if r['id'] == request_id and r['status'] == 'pending':
                request = r
                break
        
        if not request:
            await callback.answer("❌ Заявка не найдена!", show_alert=True)
            return
        
        if action == "approve":
            request['status'] = 'approved'
            result_text = f"✅ Заявка #{request_id} одобрена!"
            
            # Уведомляем пользователя
            try:
                await bot.send_message(
                    request['user_id'],
                    f"✅ <b>Ваша заявка #{request_id} на STARS одобрена!</b>\n\n"
                    f"Спасибо за использование сервиса! 🌟"
                )
            except:
                pass
            
        elif action == "reject":
            request['status'] = 'rejected'
            result_text = f"❌ Заявка #{request_id} отклонена!"
            
            # Уведомляем пользователя
            try:
                await bot.send_message(
                    request['user_id'],
                    f"❌ <b>Ваша заявка #{request_id} на STARS отклонена</b>\n\n"
                    f"По вопросам обращайтесь к администратору."
                )
            except:
                pass
        
        await callback.message.edit_text(
            f"{result_text}\n\n"
            f"Пользователь: {request['first_name']}"
        )
        await callback.answer(result_text)
    
    elif req_type == "premium":
        # Поиск заявки в premium_requests_db
        request = None
        for r in premium_requests_db:
            if r['id'] == request_id and r['status'] == 'pending':
                request = r
                break
        
        if not request:
            await callback.answer("❌ Заявка не найдена!", show_alert=True)
            return
        
        if action == "approve":
            request['status'] = 'approved'
            result_text = f"✅ Заявка #{request_id} на Premium одобрена!"
            
            # Уведомляем пользователя
            try:
                await bot.send_message(
                    request['user_id'],
                    f"✅ <b>Ваша заявка #{request_id} на Premium одобрена!</b>\n\n"
                    f"🎉 <b>Telegram Premium активирован!</b>\n\n"
                    f"Спасибо за покупку! 🌟"
                )
            except:
                pass
            
        elif action == "reject":
            request['status'] = 'rejected'
            result_text = f"❌ Заявка #{request_id} на Premium отклонена!"
            
            # Уведомляем пользователя
            try:
                await bot.send_message(
                    request['user_id'],
                    f"❌ <b>Ваша заявка #{request_id} на Premium отклонена</b>\n\n"
                    f"По вопросам обращайтесь к администратору."
                )
            except:
                pass
        
        await callback.message.edit_text(
            f"{result_text}\n\n"
            f"Пользователь: {request['first_name']}"
        )
        await callback.answer(result_text)

# ========== ОБРАБОТКА ОСТАЛЬНЫХ СООБЩЕНИЙ ==========

@dp.message()
async def handle_other_messages(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state:
        if current_state == Form.waiting_for_buy_amount.state:
            await message.answer(
                "📝 Введите количество STARS:",
                reply_markup=cancel_keyboard()
            )
        elif current_state == Form.waiting_for_buy_screenshot.state:
            await message.answer(
                "📸 Отправьте скриншот перевода:",
                reply_markup=cancel_keyboard()
            )
        elif current_state == Form.waiting_for_sell_amount.state:
            await message.answer(
                "📝 Введите количество STARS:",
                reply_markup=cancel_keyboard()
            )
        elif current_state == Form.waiting_for_sell_screenshot.state:
            await message.answer(
                "📸 Отправьте скриншот отправки STARS:",
                reply_markup=cancel_keyboard()
            )
        elif current_state == Form.waiting_for_premium_screenshot.state:
            await message.answer(
                "📸 Отправьте скриншот перевода:",
                reply_markup=cancel_keyboard()
            )
    else:
        if is_admin(message.from_user.id):
            await message.answer(
                "👑 Используйте кнопки админ-панели:",
                reply_markup=admin_main_keyboard()
            )
        else:
            await message.answer(
                "Используйте кнопки меню:",
                reply_markup=main_keyboard()
            )

# ========== ЗАПУСК БОТА ==========

async def main():
    print("=" * 50)
    print("🚀 Бот запускается...")
    print(f"💰 Курс STARS: 1 STAR = {EXCHANGE_RATE} руб.")
    print(f"⭐ Цены Premium:")
    print(f"   • 1 месяц - {PREMIUM_PRICES['1_month']['price']} руб.")
    print(f"   • 3 месяца - {PREMIUM_PRICES['3_months']['price']} руб.")
    print(f"   • 1 год - {PREMIUM_PRICES['1_year']['price']} руб.")
    print(f"💳 Реквизиты: {ADMIN_CARD}")
    print(f"👤 Администратор: {ADMIN_USERNAME}")
    print(f"👑 Админы: {ADMIN_IDS}")
    print("=" * 50)
    
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Бот готов к работе!")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")