

import json
import random
from datetime import datetime, UTC
from aiogram import Router, F
import time
from collections import defaultdict
from aiogram import Bot
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import Dispatcher, types
from aiogram.enums import ParseMode
from config import TOKEN, ADMINS, MODERATORS
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import aiohttp
from aiogram import types

import random
from collections import defaultdict
from aiogram import Bot, Dispatcher
from aiogram import Bot, Dispatcher
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from aiogram.fsm.context import FSMContext
API_TOKEN = "7750083612:AAG2BGjYAHPtY4bkSZetxlJ4fmDa-6jEqKA"
bot = Bot(token="7750083612:AAG2BGjYAHPtY4bkSZetxlJ4fmDa-6jEqKA")
dp = Dispatcher()

OPENWEATHER_API_KEY = "37c1fe288c1a5bb876a736948dc4ce29"  # Вставь свой ключ от openweathermap.org


DB_FILE = "db.json"


PLANTS = [
    {"name": "Пшеница",   "grow_time": 2*60,   "reward": 50,   "cost": 10},
    {"name": "Картошка",  "grow_time": 5*60,   "reward": 120,  "cost": 25},
    {"name": "Клубника",  "grow_time": 10*60,  "reward": 300,  "cost": 50},
    {"name": "Кукуруза",  "grow_time": 20*60,  "reward": 650,  "cost": 120},
    {"name": "Тыква",     "grow_time": 30*60,  "reward": 1100, "cost": 220},
    {"name": "Арбуз",     "grow_time": 60*60,  "reward": 2500, "cost": 450},
    {"name": "Виноград",  "grow_time": 45*60,  "reward": 1800, "cost": 330},
    {"name": "Яблоко",    "grow_time": 90*60,  "reward": 4000, "cost": 750},
    {"name": "Вишня",     "grow_time": 120*60, "reward": 7000, "cost": 1200},
    {"name": "Морковь",   "grow_time": 8*60,   "reward": 190,  "cost": 30},
    {"name": "Лук",       "grow_time": 12*60,  "reward": 330,  "cost": 55},
    {"name": "Огурец",    "grow_time": 15*60,  "reward": 370,  "cost": 70},
    {"name": "Помидор",   "grow_time": 18*60,  "reward": 420,  "cost": 95},
    {"name": "Рис",       "grow_time": 35*60,  "reward": 1200, "cost": 200},
    {"name": "Соя",       "grow_time": 25*60,  "reward": 900,  "cost": 170},
]

UPGRADES = {
    "plots": [1, 2, 3, 4, 5, 8, 12],
    "fertilizer": [1.0, 0.8, 0.6, 0.5, 0.35]
}

# Апгрейды: ускорение роста, удобрение, новые грядки
UPGRADES = {
    "plots": [1, 2, 3, 4, 5],  # количество доступных грядок
    "fertilizer": [1.0, 0.9, 0.8, 0.7, 0.5],  # множитель времени роста
}

# FSM состояния
from aiogram.fsm.state import StatesGroup, State

class ShopStates(StatesGroup):
    buying = State()
class FarmStates(StatesGroup):
    main = State()
    selecting_plot = State()
    choosing_plant = State()
    fertilizing = State()


def load_db():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

# ==== СТАТИСТИКА ПО ЧАТАМ ====


def get_user(user_id):
    db = load_db()
    user_id = str(user_id)
    week_now = datetime.now(UTC).isocalendar()[1]
    month_now = datetime.now(UTC).month
    if user_id not in db:
        db[user_id] = {
            "coins": 1000,
            "mana": 100,
            "level": 1,
            "messages": 0,
            "car": "Нет",
            "business": "Нет",
            "phone": "Нет",
            "notebook": "Нет",
            "last_bonus": 0,
            "job": "Безработный",
            "last_salary": 0,
            "banned": False,
            "ban_reason": "",
            "ban_until": 0,
            "muted": False,
            "mute_until": 0,
            "mute_reason": "",
            "is_moderator": False,
            "week_messages": 0,
            "week_reset": week_now,
            "month_messages": 0,
            "month_reset": month_now,
            "nick": "",
            "username": "",
            "first_name": "",
            "partner": None,
            "is_adult": False,   # <--- вот эта строка
        }
        save_db(db)

    user = db[user_id]
    # сброс недельной/месячной статистики
    if user.get("week_reset", week_now) != week_now:
        user["week_messages"] = 0
        user["week_reset"] = week_now
    if user.get("month_reset", month_now) != month_now:
        user["month_messages"] = 0
        user["month_reset"] = month_now
    save_db(db)
    return user

def update_user(user_id, data):
    db = load_db()
    user_id = str(user_id)
    db[user_id].update(data)
    save_db(db)

def get_partner_name(user):
    db = load_db()
    partner_id = user.get("partner")
    if not partner_id:
        return "Нет"
    partner = db.get(str(partner_id))
    if not partner:
        return "Нет"
    return partner.get("nick") or ("@" + partner.get("username", str(partner_id)))

def get_top_users(period="all", top_n=10):
    db = load_db()
    users = []
    for k, v in db.items():
        if not k.isdigit():
            continue
        if period == "all":
            users.append((k, v.get("messages", 0)))
        elif period == "week":
            users.append((k, v.get("week_messages", 0)))
        elif period == "month":
            users.append((k, v.get("month_messages", 0)))
    users.sort(key=lambda x: x[1], reverse=True)
    return users[:top_n]

def format_top(users, name="Топ"):
    if not users:
        return f"{name} пуст!"
    db = load_db()
    text = f"🏆 <b>{name}</b> 🏆\n\n"
    for i, (user_id, count) in enumerate(users, 1):
        user_obj = db.get(str(user_id), {})
        nick = user_obj.get("nick")
        username = user_obj.get("username")
        first_name = user_obj.get("first_name", "Без имени")
        if nick:
            mention = nick
        elif username:
            mention = f"@{username}"
        else:
            mention = first_name
        text += f"{i}. {mention} — <b>{count}</b> сообщений\n"
    return text

def calc_level(messages):
    return messages // 20 + 1

def is_admin(user_id):
    return str(user_id) in ADMINS

def is_moderator(user_id):
    db = load_db()
    return str(user_id) in db.get("moderators", [])

def can_moderate(user_id):
    return is_admin(user_id) or is_moderator(user_id)

def add_moderator(user_id):
    db = load_db()
    moderators = set(map(str, db.get("moderators", [])))
    moderators.add(str(user_id))
    db["moderators"] = list(moderators)
    save_db(db)

def remove_moderator(user_id):
    db = load_db()
    moderators = set(map(str, db.get("moderators", [])))
    moderators.discard(str(user_id))
    db["moderators"] = list(moderators)
    save_db(db)


import time

BANK_PERCENT = 0.10      # 10%
BANK_PERIOD = 3 * 24 * 60 * 60  # 3 дня в секундах

def get_bank(user_id):
    user = get_user(user_id)
    # Если первый раз — инициализируем банк
    if "bank_balance" not in user:
        user["bank_balance"] = 0
        user["bank_updated"] = int(time.time())
        update_user(user_id, user)
    # Автоматически начисляем проценты
    now = int(time.time())
    last = user.get("bank_updated", 0)
    balance = user.get("bank_balance", 0)
    while now >= last + BANK_PERIOD and balance > 0:
        balance = int(balance * (1 + BANK_PERCENT))
        last += BANK_PERIOD
    if balance != user.get("bank_balance", 0) or last != user.get("bank_updated", 0):
        user["bank_balance"] = balance
        user["bank_updated"] = last
        update_user(user_id, user)
    return balance, last

def deposit(user_id, amount):
    user = get_user(user_id)
    if user["coins"] < amount:
        return False, "Недостаточно коинов для депозита."
    user["coins"] -= amount
    balance, _ = get_bank(user_id)  # начислим проценты прежде чем пополнить
    user["bank_balance"] = balance + amount
    user["bank_updated"] = int(time.time())
    update_user(user_id, user)
    return True, f"На банковский счёт положено {amount} коинов. Текущий баланс банка: {user['bank_balance']}."

def withdraw(user_id, amount):
    balance, _ = get_bank(user_id)
    if amount > balance:
        return False, "Недостаточно средств в банке."
    user = get_user(user_id)
    user["bank_balance"] = balance - amount
    user["coins"] += amount
    user["bank_updated"] = int(time.time())
    update_user(user_id, user)
    return True, f"С банковского счёта снято {amount} коинов. Остаток в банке: {user['bank_balance']}."

def create_promo(code, reward_type, value):
    db = load_db()
    if "promo_codes" not in db:
        db["promo_codes"] = {}
    db["promo_codes"][code] = {
        "reward_type": reward_type,
        "reward_value": value,
        "activated_by": []
    }
    save_db(db)

JOBS = [
    {"name": "Доставщик", "min_level": 1, "salary": (25, 50)},
    {"name": "Бухгалтер", "min_level": 100, "salary": (150, 200)},
    {"name": "Пчеловод", "min_level": 500, "salary": (400, 600)},
    {"name": "Трейдер", "min_level": 2000, "salary": (1200, 2000)},
    {"name": "Инженер", "min_level": 8000, "salary": (4000, 6000)},
    {"name": "Юрист", "min_level": 25000, "salary": (10000, 15000)},
    {"name": "Архитектор", "min_level": 60000, "salary": (30000, 45000)},
    {"name": "Бизнесмен", "min_level": 100000, "salary": (80000, 120000)},
]

bot = Bot(token=TOKEN)
dp = Dispatcher()

class WorkStates(StatesGroup):
    choosing_job = State()

class ShopStates(StatesGroup):
    buy_phone = State()
    buy_car = State()
    buy_laptop = State()

from aiogram.fsm.state import State, StatesGroup

class PromoStates(StatesGroup):
    promo_code_step1 = State()
    promo_code_step2 = State()
    promo_code_step3 = State()
    # если используется старое состояние для активации, его тоже можно оставить:
    waiting_for_code = State()

class AdminStates(StatesGroup):
    entering_coins = State()
    entering_mana = State()
    entering_car = State()
    entering_phone = State()
    entering_notebook = State()
    promo_code_step1 = State()
    promo_code_step2 = State()
    promo_code_step3 = State()

# Добавь команду "работа"
@dp.message(lambda m: m.text and m.text.lower() == "работа")
async def job_list(msg: types.Message):
    user = get_user(msg.from_user.id)
    lvl = user.get("level", 1)
    available = [j for j in JOBS if lvl >= j["min_level"]]
    text = "<b>Работа</b>\n\n"
    text += f"Текущая работа: <b>{user.get('job', 'Безработный')}</b>\n\n"
    text += "Доступные профессии:\n"
    for job in available:
        text += f"- {job['name']} (с {job['min_level']} лвл)\n"
    text += "\nУстроиться: устроиться [название_профессии]\nПример: устроиться курьер"
    await msg.answer(text, parse_mode="HTML")

@dp.message(lambda m: m.text and m.text.lower().startswith("устроиться "))
async def choose_job(msg: types.Message):
    job_name = msg.text[11:].strip().lower()
    user = get_user(msg.from_user.id)
    lvl = user.get("level", 1)
    found = next((job for job in JOBS if job["name"].lower() == job_name), None)
    if not found:
        await msg.answer("Такой профессии нет. Проверь список через команду 'работа'.")
        return
    if lvl < found["min_level"]:
        await msg.answer(f"Эта работа доступна с {found['min_level']} уровня.")
        return
    user["job"] = found["name"]
    update_user(msg.from_user.id, user)
    await msg.answer(f"Поздравляю! Ты теперь работаешь: {found['name']}.")

@dp.message(lambda m: m.text and m.text.lower() == "зарплата")
async def get_salary(msg: types.Message):
    user = get_user(msg.from_user.id)
    job = next((j for j in JOBS if j["name"] == user.get("job")), None)
    if not job:
        await msg.answer("Ты сейчас безработный. Устройся на работу командой: работа")
        return
    now = int(time.time())
    cooldown = 15 * 60  # 15 минут
    last_salary = user.get("last_salary", 0)
    if now < last_salary + cooldown:
        left = last_salary + cooldown - now
        m = left // 60
        s = left % 60
        await msg.answer(f"Получить зарплату можно через {m:02}:{s:02}")
        return
    salary = random.randint(*job["salary"])
    user["coins"] += salary
    user["last_salary"] = now
    update_user(msg.from_user.id, user)
    await msg.answer(f"Ты получил зарплату: <b>{salary} коинов</b> за работу {job['name']}.", parse_mode="HTML")

@dp.message(lambda m: m.text and m.text.lower() == "профиль")
async def profile(msg: Message):
    user_id = msg.from_user.id
    user = get_user(msg.from_user.id)
    user["level"] = calc_level(user.get("messages", 0))
    nik = user.get("nick") or msg.from_user.first_name  
    next_level_msgs = user["level"] * 20 - user["messages"]
    next_level_msgs = max(0, next_level_msgs)
    ban_status = "Да" if user.get("banned") else "Нет"
    ban_reason = user.get("ban_reason", "")
    ban_until = user.get("ban_until", 0)
    if ban_until and ban_until > time.time():
        ban_time_left = int(ban_until - time.time())
        ban_str = f"Да (ещё {ban_time_left//60} мин, причина: {ban_reason})"
    elif user.get("banned"):
        ban_str = f"Да (навсегда, причина: {ban_reason})"
    else:
        ban_str = "Нет"
    mute_status = "Да" if user.get("muted") and user.get("mute_until",0)>time.time() else "Нет"
    if user.get("muted") and user.get("mute_until",0)>time.time():
        mute_left = int(user["mute_until"] - time.time())
        mute_str = f"Да (ещё {mute_left//60} мин, причина: {user.get('mute_reason','')})"
    else:
        mute_str = "Нет"
    mod_status = "Да" if is_moderator(msg.from_user.id) else "Нет"
    text = (
        f"👤 <b>Профиль</b>\n"
        f"Ник: <b>{nik}</b>\n"
        f"ID: <code>{user_id}</code>\n"
        f"Парадизкоины: <b>{user['coins']}</b>\n"
        f"Парадиз мана: <b>{user['mana']}</b>\n"
        f"Уровень: <b>{user['level']}</b>\n"
        f"Сообщений: <b>{user.get('messages',0)}</b>\n"
        f"До следующего лвла: <b>{next_level_msgs}</b>\n"
        f"🚗 Машина: <b>{user['car']}</b>\n"
        f"🏢 Бизнес: <b>{user['business']}</b>\n"
        f"📱 Телефон: <b>{user['phone']}</b>\n"
        f"💻 Ноутбук: <b>{user['notebook']}</b>\n"
        f"💼 Работа: <b>{user.get('job','Безработный')}</b>\n"
        f"💍 Партнёр: <b>{get_partner_name(user)}</b>\n"
        f"🤐 Мут: <b>{mute_str}</b>\n"
        f"🛡️ Модератор: <b>{mod_status}</b>"
    )
    await msg.answer(text, parse_mode=ParseMode.HTML)
@dp.message(lambda m: m.text and m.text.lower() == "ферма")
async def farm_menu(msg: types.Message):
    print("farm_menu called")
    await msg.answer("🌾 Добро пожаловать на ферму!")
    user = get_user(msg.from_user.id)
    plots = user.get("farm_plots", 1)
    fert = user.get("fertilizer_lvl", 0)
    text = (
        "<b>🌾 Твоя ферма</b>\n"
        f"Грядок: <b>{plots}</b>\n"
        f"Уровень удобрений: <b>{fert}</b>\n"
        f"Баланс: <b>{user.get('coins', 0)}</b> коинов\n\n"
        "Команды:\n"
        "грядки — показать состояние\n"
        "посадить [номер] [культура]\n"
        "собрать — собрать урожай\n"
        "удобрить [номер] — ускорить текущий рост\n"
        "срезать [номер] — удалить растение\n"
        "апгрейды — улучшения\n"
        "купить грядку\n"
        "купить удобрение\n"
        "баланс или б — баланс\n"
    )
    await msg.answer(text, parse_mode="HTML")

@dp.message(lambda m: m.text and m.text.lower() in ["баланс", "б"])
async def show_balance(msg: types.Message):
    user = get_user(msg.from_user.id)
    await msg.answer(
        f"💰 Баланс:\nПарадизкоины: <b>{user['coins']}</b>\nПарадиз мана: <b>{user['mana']}</b>",
        parse_mode="HTML"
    )

import random


@dp.message(lambda m: m.text and m.text.lower().startswith("+ник "))
async def set_nick(msg: types.Message):
    nick = msg.text[5:].strip()
    if not (1 <= len(nick) <= 32):
        await msg.answer("Ник должен быть от 1 до 32 символов.")
        return
    # Можно добавить проверку на уникальность и мат, если нужно
    user = get_user(msg.from_user.id)
    user["nick"] = nick
    update_user(msg.from_user.id, user)
    await msg.answer(f"Твой ник теперь: <b>{nick}</b>", parse_mode="HTML")


@dp.message(lambda m: m.text and m.text.lower().startswith("казино"))
async def casino(msg: types.Message):
    parts = msg.text.strip().split()
    if len(parts) < 2 or not parts[1].isdigit():
        await msg.answer("Используй: казино [ставка], например: казино 100")
        return
    bet = int(parts[1])
    if bet <= 0:
        await msg.answer("Ставка должна быть положительным числом.")
        return
    user = get_user(msg.from_user.id)
    if user["coins"] < bet:
        await msg.answer("У тебя недостаточно коинов для ставки.")
        return

    outcome = random.choice(["lose", "win"])
    if outcome == "lose":
        user["coins"] -= bet
        update_user(msg.from_user.id, user)
        await msg.answer(f"🎰 Увы, ты проиграл {bet} коинов.\nБаланс: {user['coins']}")
    else:
        multiplier = random.choice([2, 1.5])
        win = int(bet * multiplier)
        user["coins"] += win
        update_user(msg.from_user.id, user)
        await msg.answer(f"🎰 Ты выиграл {win} коинов! ({multiplier}x)\nБаланс: {user['coins']}")

@dp.message(lambda m: m.text and m.text.lower() == "грядки")
async def farm_state(msg: types.Message):
    user = get_user(msg.from_user.id)
    plots = user.get("farm_plots", 1)
    farm = user.get("farm", [None] * plots)
    text = "<b>Состояние грядок:</b>\n"
    for i in range(plots):
        plot = farm[i] if i < len(farm) else None
        if not plot:
            text += f"{i+1}: пусто\n"
        else:
            ready = plot["start"] + plot["grow_time"]
            left = max(0, ready - int(time.time()))
            m, s = left // 60, left % 60
            text += f"{i+1}: {plot['plant']} — {m:02}:{s:02} до урожая\n"
    await msg.answer(text, parse_mode="HTML")

@dp.message(lambda m: m.text and m.text.lower().startswith("посадить "))
async def farm_plant(msg: types.Message):
    parts = msg.text.strip().split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await msg.answer("Формат: посадить [номер_грядки] [культура]")
        return
    plot_idx = int(parts[1]) - 1
    plant_name = parts[2].capitalize()
    plant = next((p for p in PLANTS if p["name"].lower() == plant_name.lower()), None)
    if not plant:
        await msg.answer("Нет такой культуры. Проверь список!")
        return
    user = get_user(msg.from_user.id)
    if user.get("coins", 0) < plant["cost"]:
        await msg.answer("Недостаточно коинов.")
        return
    plots = user.get("farm_plots", 1)
    if not (0 <= plot_idx < plots):
        await msg.answer("Нет такой грядки.")
        return
    farm = user.get("farm", [None] * plots)
    if farm[plot_idx]:
        await msg.answer("Грядка занята!")
        return
    fert = user.get("fertilizer_lvl", 0)
    time_mul = UPGRADES["fertilizer"][fert] if fert < len(UPGRADES["fertilizer"]) else 1.0
    grow_time = int(plant["grow_time"] * time_mul)
    farm[plot_idx] = {
        "plant": plant["name"],
        "start": int(time.time()),
        "grow_time": grow_time,
        "reward": plant["reward"],
        "fertilized": False
    }
    user["coins"] -= plant["cost"]
    user["farm"] = farm
    update_user(msg.from_user.id, user)
    await msg.answer(f"{plant['name']} посажена на грядке {plot_idx+1}. Урожай через {grow_time//60} мин.")

@dp.message(lambda m: m.text and m.text.lower() == "собрать")
async def farm_harvest(msg: types.Message):
    user = get_user(msg.from_user.id)
    plots = user.get("farm_plots", 1)
    farm = user.get("farm", [None] * plots)
    any_harvest = False
    for i in range(plots):
        plot = farm[i] if i < len(farm) else None
        if plot and int(time.time()) >= plot["start"] + plot["grow_time"]:
            user["coins"] += plot["reward"]
            farm[i] = None
            any_harvest = True
            await msg.answer(f"С грядки {i+1} собран урожай {plot['plant']}! +{plot['reward']} коинов.")
    user["farm"] = farm
    update_user(msg.from_user.id, user)
    if not any_harvest:
        await msg.answer("Нет готового урожая. Проверь 'грядки'.")

@dp.message(lambda m: m.text and m.text.lower().startswith("удобрить "))
async def fertilize_plot(msg: types.Message):
    parts = msg.text.strip().split()
    if len(parts) < 2 or not parts[1].isdigit():
        await msg.answer("Формат: удобрить [номер_грядки]")
        return
    plot_idx = int(parts[1]) - 1
    user = get_user(msg.from_user.id)
    plots = user.get("farm_plots", 1)
    farm = user.get("farm", [None] * plots)
    if not (0 <= plot_idx < plots):
        await msg.answer("Нет такой грядки.")
        return
    plot = farm[plot_idx]
    if not plot:
        await msg.answer("Грядка пустая!")
        return
    if plot.get("fertilized"):
        await msg.answer("Эта грядка уже удобрена!")
        return
    if user["coins"] < 100:
        await msg.answer("Недостаточно коинов для удобрения (нужно 100).")
        return
    plot["grow_time"] = max(1, plot["grow_time"] // 2)
    plot["fertilized"] = True
    user["coins"] -= 100
    farm[plot_idx] = plot
    user["farm"] = farm
    update_user(msg.from_user.id, user)
    await msg.answer(f"Грядка {plot_idx+1} удобрена! Урожай теперь через {plot['grow_time']//60} мин.")

@dp.message(lambda m: m.text and m.text.lower().startswith("срезать "))
async def remove_plant(msg: types.Message):
    parts = msg.text.strip().split()
    if len(parts) < 2 or not parts[1].isdigit():
        await msg.answer("Формат: срезать [номер_грядки]")
        return
    plot_idx = int(parts[1]) - 1
    user = get_user(msg.from_user.id)
    plots = user.get("farm_plots", 1)
    farm = user.get("farm", [None] * plots)
    if not (0 <= plot_idx < plots):
        await msg.answer("Нет такой грядки.")
        return
    if not farm[plot_idx]:
        await msg.answer("Грядка и так пуста!")
        return
    farm[plot_idx] = None
    user["farm"] = farm
    update_user(msg.from_user.id, user)
    await msg.answer(f"Грядка {plot_idx+1} теперь пуста.")

@dp.message(lambda m: m.text and m.text.lower() == "апгрейды")
async def farm_upgrades(msg: types.Message):
    user = get_user(msg.from_user.id)
    plots = user.get("farm_plots", 1)
    fert = user.get("fertilizer_lvl", 0)
    upgrades = []
    if plots < max(UPGRADES["plots"]):
        price = 200 * (plots+1)
        upgrades.append(f"Увеличить грядок до {plots+1}: {price} коинов. Команда: купить грядку")
    if fert < len(UPGRADES["fertilizer"]) - 1:
        price = 150 * (fert+1)
        upgrades.append(f"Прокачать удобрение до {fert+1}: {price} коинов. Команда: купить удобрение")
    if not upgrades:
        upgrades.append("Все апгрейды куплены!")
    await msg.answer("\n".join(upgrades))

@dp.message(lambda m: m.text and m.text.lower() == "купить грядку")
async def buy_plot(msg: types.Message):
    user = get_user(msg.from_user.id)
    plots = user.get("farm_plots", 1)
    if plots >= max(UPGRADES["plots"]):
        await msg.answer("Максимум грядок!")
        return
    price = 200 * (plots+1)
    if user["coins"] < price:
        await msg.answer("Недостаточно коинов!")
        return
    user["coins"] -= price
    user["farm_plots"] = plots+1
    farm = user.get("farm", [None]*plots)
    farm.extend([None]*(user["farm_plots"]-len(farm)))
    user["farm"] = farm
    update_user(msg.from_user.id, user)
    await msg.answer(f"Теперь у тебя {plots+1} грядок!")

@dp.message(lambda m: m.text and m.text.lower() == "купить удобрение")
async def buy_fertilizer(msg: types.Message):
    user = get_user(msg.from_user.id)
    fert = user.get("fertilizer_lvl", 0)
    if fert >= len(UPGRADES["fertilizer"])-1:
        await msg.answer("Максимум удобрения!")
        return
    price = 150 * (fert+1)
    if user["coins"] < price:
        await msg.answer("Недостаточно коинов!")
        return
    user["coins"] -= price
    user["fertilizer_lvl"] = fert+1
    update_user(msg.from_user.id, user)
    await msg.answer(f"Уровень удобрений теперь {fert+1}! Растения растут быстрее.")


import random
from aiogram import types

# --- НАСТРОЙКИ ---
ROULETTE = {}
ROULETTE_TIMEOUT = 120  # секунд на сбор игроков
ROULETTE_LIMIT_HOUR = 3  # лимит на участие в рулетке для одного пользователя в час
LAST_ROULETTE_PLAY = {}  # user_id: [timestamps]

def can_play_roulette(user_id):
    now = int(time.time())
    times = LAST_ROULETTE_PLAY.get(user_id, [])
    times = [t for t in times if now - t < 3600]
    LAST_ROULETTE_PLAY[user_id] = times
    return len(times) < ROULETTE_LIMIT_HOUR

def mark_play_roulette(user_id):
    now = int(time.time())
    LAST_ROULETTE_PLAY.setdefault(user_id, []).append(now)

@dp.message(lambda m: m.text and m.text.lower().startswith("рулетка "))
async def start_roulette(msg: types.Message):
    global ROULETTE
    if ROULETTE.get("started"):
        await msg.answer("Сейчас уже идёт игра! Ждите окончания или отмените её.")
        return
    parts = msg.text.strip().split()
    if len(parts) < 2 or not parts[1].isdigit():
        await msg.answer("Используй: рулетка [ставка], например: рулетка 300")
        return
    bet = int(parts[1])
    if bet < 1:
        await msg.answer("Минимальная ставка — 1.")
        return
    user = get_user(msg.from_user.id)
    if not can_play_roulette(msg.from_user.id):
        await msg.answer(f"Лимит: не больше {ROULETTE_LIMIT_HOUR} игр в час.")
        return
    if user["coins"] < bet:
        await msg.answer("У тебя недостаточно коинов для такой ставки.")
        return
    ROULETTE = {
        "started": True,
        "bet": bet,
        "creator_id": msg.from_user.id,
        "players": {msg.from_user.id: msg.from_user.full_name},
        "nicknames": {msg.from_user.id: user.get("nick") or msg.from_user.full_name},
        "time_start": int(time.time())
    }
    await msg.answer(
        f"🎲 Русская рулетка!\n"
        f"Ставка: <b>{bet}</b> коинов\n"
        f"Минимум 3, максимум 10 игроков.\n"
        f"Чтобы записаться — напиши <b>+</b>.\n"
        f"Создатель может начать раньше командой <b>старт</b> (если 3+ участников).\n"
        f"Для отмены — <b>отмена</b> (может только создатель).\n"
        f"Время на набор: {ROULETTE_TIMEOUT//60} минут.",
        parse_mode="HTML"
    )

@dp.message(lambda m: m.text and m.text.strip() == "+")
async def join_roulette(msg: types.Message):
    global ROULETTE
    if not ROULETTE.get("started"):
        return
    if int(time.time()) - ROULETTE["time_start"] > ROULETTE_TIMEOUT:
        await msg.answer("Время набора вышло, рулетка отменена.")
        ROULETTE.clear()
        return
    if len(ROULETTE["players"]) >= 10:
        await msg.answer("В игре уже максимум 10 участников!")
        return
    if msg.from_user.id in ROULETTE["players"]:
        await msg.answer("Ты уже участвуешь в этой рулетке!")
        return
    if not can_play_roulette(msg.from_user.id):
        await msg.answer(f"Лимит: не больше {ROULETTE_LIMIT_HOUR} игр в час.")
        return
    user = get_user(msg.from_user.id)
    if user["coins"] < ROULETTE["bet"]:
        await msg.answer("Недостаточно коинов для участия.")
        return
    ROULETTE["players"][msg.from_user.id] = msg.from_user.full_name
    ROULETTE["nicknames"][msg.from_user.id] = user.get("nick") or msg.from_user.full_name
    await msg.answer(f"{ROULETTE['nicknames'][msg.from_user.id]} присоединился к рулетке! ({len(ROULETTE['players'])}/10)")

@dp.message(lambda m: m.text and m.text.lower() == "старт")
async def run_roulette(msg: types.Message):
    global ROULETTE
    if not ROULETTE.get("started"):
        return
    if msg.from_user.id != ROULETTE["creator_id"]:
        await msg.answer("Только создатель рулетки может начать игру командой 'старт'.")
        return
    if int(time.time()) - ROULETTE["time_start"] > ROULETTE_TIMEOUT:
        await msg.answer("Время набора вышло, рулетка отменена.")
        ROULETTE.clear()
        return
    if len(ROULETTE["players"]) < 3:
        await msg.answer("Для старта нужно минимум 3 участника.")
        return
    players = list(ROULETTE["players"].keys())
    nicks = ROULETTE["nicknames"]
    bet = ROULETTE["bet"]

    # Проверяем баланс перед стартом
    for uid in players[:]:
        user = get_user(uid)
        if user["coins"] < bet:
            await msg.answer(f"{nicks[uid]} выбыл: не хватает коинов для ставки!")
            players.remove(uid)
    if len(players) < 3:
        await msg.answer("Недостаточно игроков с деньгами для старта (3+).")
        ROULETTE.clear()
        return
    # Снимаем ставку и отмечаем лимит
    for uid in players:
        user = get_user(uid)
        user["coins"] -= bet
        update_user(uid, user)
        mark_play_roulette(uid)

    round_num = 1
    while len(players) > 1:
        await msg.answer(
            f"Раунд {round_num}: осталось игроков — {len(players)}."
        )
        # Обратный отсчёт
        for sec in range(5, 0, -1):
            await msg.answer(str(sec))
            await asyncio.sleep(1)
        await msg.answer("БАМ!")
        loser = random.choice(players)
        loser_name = nicks[loser]
        players.remove(loser)
        await msg.answer(f"🔫 {loser_name} выбывает из игры!")
        round_num += 1

    winner = players[0]
    pot = bet * len(nicks)
    user = get_user(winner)
    user["coins"] += pot
    update_user(winner, user)
    await msg.answer(
        f"🏆 Победитель — {nicks[winner]}! Забирает банк: <b>{pot}</b> коинов.",
        parse_mode="HTML"
    )
    ROULETTE.clear()

@dp.message(lambda m: m.text and m.text.lower() == "отмена")
async def cancel_roulette(msg: types.Message):
    global ROULETTE
    if not ROULETTE.get("started"):
        return
    if msg.from_user.id != ROULETTE["creator_id"]:
        await msg.answer("Только создатель рулетки может отменить игру.")
        return
    await msg.answer("Рулетка отменена создателем.")
    ROULETTE.clear()

@dp.message(lambda m: m.text and m.text.lower() == "бонус")
async def daily_bonus(msg: Message):
    user = get_user(msg.from_user.id)
    now = int(time.time())
    next_bonus_time = user.get("last_bonus", 0) + 5*60*60
    if now < next_bonus_time:
        left = next_bonus_time - now
        h = left // 3600
        m = (left % 3600) // 60
        s = left % 60
        await msg.answer(f"Бонус будет доступен через {h:02}:{m:02}:{s:02}")
        return
    bonus = random.randint(200, 500)
    user["coins"] += bonus
    user["last_bonus"] = now
    update_user(msg.from_user.id, user)
    await msg.answer(f"🎁 Ты получил <b>{bonus} Парадизкоинов</b>!", parse_mode=ParseMode.HTML)


router = Router()

class PromoStates(StatesGroup):
    waiting_for_code = State()

PROMOCODES = {"test2024": 100}

@router.message(lambda m: m.text and m.text.lower() == "промокод")
async def promo_enter(msg: Message, state: FSMContext):
    await state.set_state(PromoStates.waiting_for_code)
    await msg.answer("Введи промокод:")

@router.message(PromoStates.waiting_for_code)
async def promo_code_process(msg: Message, state: FSMContext):
    promo_code = msg.text.strip().lower()
    if promo_code in PROMOCODES:
        await msg.answer(f"Промокод активирован! +{PROMOCODES[promo_code]} коинов")
        await state.clear()
    else:
        await msg.answer("Промокод недействителен. Попробуй ещё раз.")


    # Начисляем бонус
    bonus = PROMOCODES[promo_code]
    user["coins"] += bonus
    user.setdefault("activated_promos", []).append(promo_code)
    update_user(user_id, user)

    await msg.answer(f"Промокод активирован! Тебе начислено {bonus} коинов.")
    await state.clear()
    
@dp.message(lambda m: m.text and m.text.lower() == "админ")
async def admin_panel_entry(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("Нет доступа.")
        return
    await msg.answer(
        "Админ-панель:\n"
        "выдать коины — выдать коины\n"
        "выдать ману — выдать ману\n"
        "выдать машину — выдать машину\n"
        "выдать телефон — выдать телефон\n"
        "выдать ноутбук — выдать ноутбук\n"
        "создать промокод — создать промокод\n"
        "кик — кикнуть пользователя"
    )

@dp.message(lambda m: m.text and m.text.lower() == "парадиз")
async def paradiz_menu(msg: Message):
    await msg.answer(
        "Добро пожаловать в Парадиз! Доступные команды:\n"
        "магазин — открыть магазин\n"
        "профиль — посмотреть профиль\n"
        "промокод — активировать промокод\n"
        "бонус — получить ежедневный бонус\n"
        "админ — админ-панель (для админов)"
    )
    get_user(msg.from_user.id)

@dp.message(lambda m: m.text and m.text.lower() == "удалить кнопки")
async def remove_inline_markup(msg: types.Message):
    try:
        await msg.bot.edit_message_reply_markup(
            chat_id=msg.chat.id,
            message_id=msg.message_id - 1,
            reply_markup=None
        )
        await msg.answer("Инлайн-кнопки удалены у последнего сообщения.")
    except Exception as e:
        await msg.answer("Не удалось удалить кнопки. Возможно, сообщение слишком старое или кнопок нет.")

phones = [
        {"name": "Nokia 105", "price": 500, "colors": ["Черный", "Синий", "Красный", "Зеленый", "Белый"]},
        {"name": "Samsung Galaxy A10", "price": 3000, "colors": ["Черный", "Синий", "Красный", "Зеленый", "Белый"]},
        {"name": "Xiaomi Redmi 9A", "price": 5500, "colors": ["Черный", "Синий", "Красный", "Зеленый", "Белый"]},
        {"name": "Realme C21", "price": 8000, "colors": ["Черный", "Синий", "Красный", "Зеленый", "Белый"]},
        {"name": "Huawei P30", "price": 12000, "colors": ["Черный", "Синий", "Красный", "Зеленый", "Белый"]},
        {"name": "iPhone SE", "price": 25000, "colors": ["Черный", "Синий", "Красный", "Зеленый", "Белый"]},
        {"name": "Poco X5 Pro", "price": 38000, "colors": ["Черный", "Синий", "Красный", "Зеленый", "Белый"]},
        {"name": "Samsung Galaxy S21", "price": 45000, "colors": ["Черный", "Синий", "Красный", "Зеленый", "Белый"]},
        {"name": "iPhone 13", "price": 70000, "colors": ["Черный", "Синий", "Красный", "Зеленый", "Белый"]},
        {"name": "iPhone 15 Pro Max", "price": 180000, "colors": ["Черный", "Синий", "Красный", "Зеленый", "Белый"]}
]
cars = [
        {"name": "Lada Granta", "price": 20000, "colors": ["Черный", "Белый", "Красный", "Синий", "Зеленый"]},
        {"name": "Volkswagen Polo", "price": 400000, "colors": ["Черный", "Белый", "Красный", "Синий", "Зеленый"]},
        {"name": "Kia Rio", "price": 600000, "colors": ["Черный", "Белый", "Красный", "Синий", "Зеленый"]},
        {"name": "Hyundai Solaris", "price": 750000, "colors": ["Черный", "Белый", "Красный", "Синий", "Зеленый"]},
        {"name": "Toyota Camry", "price": 1200000, "colors": ["Черный", "Белый", "Красный", "Синий", "Зеленый"]},
        {"name": "Mazda 6", "price": 1500000, "colors": ["Черный", "Белый", "Красный", "Синий", "Зеленый"]},
        {"name": "BMW 3 Series", "price": 2300000, "colors": ["Черный", "Белый", "Красный", "Синий", "Зеленый"]},
        {"name": "Mercedes-Benz C-Class", "price": 2700000, "colors": ["Черный", "Белый", "Красный", "Синий", "Зеленый"]},
        {"name": "Tesla Model S", "price": 3200000, "colors": ["Черный", "Белый", "Красный", "Синий", "Зеленый"]},
        {"name": "Lamborghini Aventador", "price": 15000000, "colors": ["Черный", "Белый", "Красный", "Синий", "Зеленый"]}
]
laptops = [
        {"name": "Irbis NB", "price": 8000, "colors": ["Черный", "Серый", "Синий", "Красный", "Белый"]},
        {"name": "Acer Extensa", "price": 25000, "colors": ["Черный", "Серый", "Синий", "Красный", "Белый"]},
        {"name": "Lenovo IdeaPad", "price": 35000, "colors": ["Черный", "Серый", "Синий", "Красный", "Белый"]},
        {"name": "HP 15s", "price": 46000, "colors": ["Черный", "Серый", "Синий", "Красный", "Белый"]},
        {"name": "ASUS VivoBook", "price": 52000, "colors": ["Черный", "Серый", "Синий", "Красный", "Белый"]},
        {"name": "Dell Inspiron", "price": 67000, "colors": ["Черный", "Серый", "Синий", "Красный", "Белый"]},
        {"name": "Huawei MateBook D", "price": 83000, "colors": ["Черный", "Серый", "Синий", "Красный", "Белый"]},
        {"name": "MacBook Air M1", "price": 120000, "colors": ["Черный", "Серый", "Синий", "Красный", "Белый"]},
        {"name": "ASUS ROG Strix", "price": 170000, "colors": ["Черный", "Серый", "Синий", "Красный", "Белый"]},
        {"name": "Apple MacBook Pro 16", "price": 350000, "colors": ["Черный", "Серый", "Синий", "Красный", "Белый"]}
]
adult_items = [
    {"name": "Виски Jack Daniels", "price": 5000, "colors": ["Коричневый"], "adult": True},
    {"name": "Сигары Cohiba", "price": 3000, "colors": ["Коричневый"], "adult": True},
    {"name": "Шампанское Moet", "price": 7000, "colors": ["Золотой"], "adult": True},
    {"name": "Стринги", "price": 2000, "colors": ["Красный, Черный, Белый"], "adult": True},
    {"name": "Поношенные стринги", "price": 5000, "colors": ["Красный, Черный, Белый"], "adult": True},
    {"name": "Дилдо", "price": 150000, "colors": ["10 см, 15 см, 20 см, 25 см"], "adult": True}

]

category_map = [
    ("📱 Телефоны", phones),
    ("🚗 Машины", cars),
    ("💻 Ноутбуки", laptops),
    ("🔞 18+", adult_items),
]

def get_all_items():
    all_items = []
    for _, items in category_map:
        all_items.extend(items)
    return all_items



from aiogram.fsm.state import State, StatesGroup
class ShopStates(StatesGroup):
    buying = State()

@dp.message(lambda m: m.text and m.text.lower() == "магазин")
async def shop_menu(msg: types.Message, state: FSMContext):
    text = "<b>🛒 Магазин</b>\n\n"
    for idx, (cat_name, _) in enumerate(category_map, 1):
        text += f"{cat_name} — напиши \"{cat_name.split(' ',1)[1].lower()}\"\n"
    text += '\nДля покупки напиши: <i>номер цвет</i> (например: 1 черный)\nДля выхода: "выход"\n'
    await msg.answer(text, parse_mode="HTML")
    await state.set_state(ShopStates.buying)

@dp.message(ShopStates.buying)
async def shop_handler(msg: types.Message, state: FSMContext):
    text = msg.text.strip().lower()
    if text == "выход":
        await msg.answer("Вы вышли из магазина.")
        await state.clear()
        return

    # Категории
    if text in ["телефоны", "машины", "ноутбуки", "18+"]:
        idx = ["телефоны", "машины", "ноутбуки", "18+"].index(text)
        cat_name, items = category_map[idx]
        out = f"<b>{cat_name}:</b>\n"
        for i, item in enumerate(items, 1):
            out += f"{i}. {item['name']} — {item['price']} коинов (цвета: {', '.join(item['colors'])})\n"
        out += "\nДля покупки: <i>номер цвет</i> (например: 1 черный)\nДля выхода: \"выход\""
        await msg.answer(out, parse_mode="HTML")
        return

    # Покупка по номеру и цвету
    parts = msg.text.strip().split()
    if len(parts) < 2 or not parts[0].isdigit():
        await msg.answer("Формат: номер цвет. Пример: 1 черный\nИли напиши 'выход' для выхода из магазина.")
        return

    number = int(parts[0])
    color = " ".join(parts[1:]).capitalize()
    all_items = get_all_items()
    if not (1 <= number <= len(all_items)):
        await msg.answer("Нет товара с таким номером.")
        return

    item = all_items[number - 1]
    if color not in item["colors"]:
        await msg.answer(f"Нет такого цвета. Доступные: {', '.join(item['colors'])}")
        return

    user = get_user(msg.from_user.id)
    if user["coins"] < item["price"]:
        await msg.answer("Недостаточно коинов для покупки.")
        return

    user["coins"] -= item["price"]
    # Сохраняем покупку в профиль пользователя по типу товара
    if item in phones:
        user["phone"] = f"{item['name']} ({color})"
    elif item in cars:
        user["car"] = f"{item['name']} ({color})"
    elif item in laptops:
        user["notebook"] = f"{item['name']} ({color})"
    elif item in adult_items:
        user.setdefault("adult_items", []).append(f"{item['name']} ({color})")
    update_user(msg.from_user.id, user)
    await msg.answer(f"Покупка успешна!\nТы купил {item['name']} цвета {color} за {item['price']} коинов.\nОсталось: {user['coins']} коинов.")
    await state.clear()



import logging
import sys

from telegram.ext import Updater, CommandHandler
from host import Host
from game import GameStatus
from player import Player, roles


class Player(object):
    """player"""
    def __init__(self, user, game_master=False):
        self.identity = user.id
        self.name = (user.first_name +' '+ user.last_name).encode('utf-8')
        if len(self.name) == 0:
            self.name = (user.username).encode('utf-8')
        self.role = None
        if game_master:
            self.role = '☝🏽️ Ведущий'

    def __eq__(self, other):
        return self.identity == other.id

roles = {
    'mafia' : '🔫 Мафия',
    'godfather' : '💂 Крестный отец',
    'civilian' : '👦 Обыватель',
    'detective' : '👮 Детектив',
    'doctor' : '🚑 Доктор',
    'prostitute' : '💃 Красотка',
    'killer' : '🔪 Маньяк'
}

if len(sys.argv) > 1:
    token = sys.argv[1]
else:
    token = "7750083612:AAG2BGjYAHPtY4bkSZetxlJ4fmDa-6jEqKA"

logging.basicConfig(filename='bot.log',level=logging.INFO)

logger = logging.getLogger('mafiapartygamebot')

logger.setLevel(logging.INFO)

logger.info('bot started')

host = Host()

def new(bot, update):
    """start new game"""
    game = host.get_game(update.message.chat_id)
    if game and game.state == GameStatus.waiting:
        bot.sendMessage(
            update.message.chat_id,
            'Мы уже ожидаем игроков! \r\n{} {}'
            .format(game.game_master.name, game.game_master.role))
    elif game and game.state == GameStatus.started:
        bot.sendMessage(
            update.message.chat_id,
            'А мы уже играем 😁 Чтобы завершить текущую игру, воспользуйтесь командой /cancel')
    else:
        game = host.create_game(update.message.chat_id, update.message.from_user)
        game_master = game.game_master
        bot.sendMessage(
            update.message.chat_id,
            'Начинаем новую игру, присоединяйся быстрее! \r\n{} {}'
            .format(game_master.name, game_master.role))

def join(bot, update):
    """join game"""
    game = host.get_game(update.message.chat_id)

    if game is None:
        bot.sendMessage(
            update.message.chat_id,
            'Для начала создайте новую игру при помощи команды /new')
    else:
        if game.game_master.identity == update.message.from_user.id:
            bot.sendMessage(
                update.message.chat_id,
                'Ведущий играет роль ведущего...')
        else:
            player = game.add_player(update.message.from_user)
            if player:
                bot.sendMessage(
                    update.message.chat_id,
                    'К игре присоединился {}'.format(player.name))

def play(bot, update):
    """play new game"""
    game = host.get_game(update.message.chat_id)

    if not game:
        bot.sendMessage(
            update.message.chat_id,
            'Сначала нужно создать игру при помощи команды /new')

    elif game and game.state == GameStatus.waiting:
        if game.game_master.identity != update.message.from_user.id:
            bot.sendMessage(
                update.message.chat_id,
                'Только ведущий может начать игру. \r\n{} {}'
                .format(game.game_master.name, game.game_master.role))
        else:
            game.start()
            game_master = game.game_master

            if len(game.players) == 0:
                bot.sendMessage(update.message.chat_id, 'Для игры в мафии нужны игроки 😊')
                return

            players = ['Роли игроков: \r\n']
            for player in game.players:
                players.append('{} {}'.format(player.role, player.name))
                bot.sendMessage(player.identity, '❗️ Твоя роль {}'.format(player.role))

            bot.sendMessage(game_master.identity, '\r\n'.join(players))

            bot.sendMessage(
                update.message.chat_id,
                'Город засыпает 💤 \r\n{} {}'.format(game_master.name, game_master.role))

    elif game and game.state == GameStatus.started:
        bot.sendMessage(
            update.message.chat_id,
            'А мы уже играем 😁 Чтобы завершить текущую игру, воспользуйтесь командой /cancel')

def cancel(bot, update):
    """cancel game"""
    game = host.get_game(update.message.chat_id)

    if game:
        game_master = game.game_master
        if game_master.identity != update.message.from_user.id:
            bot.sendMessage(
                update.message.chat_id,
                'Только ведущий может остановить игру. \r\n{} {}'
                .format(game_master.name, game_master.role))
        else:
            host.delete_game(update.message.chat_id)
            bot.sendMessage(update.message.chat_id, 'Игра остановлена 😐')
    else:
        bot.sendMessage(update.message.chat_id, 'Игра не найдена 😳')

def help(bot, update):
    """print help"""
    bot.sendMessage(update.message.chat_id,
                    '/new - создание новой игры \r\n'+
                    '/join - присоединиться к игре \r\n'+
                    '/play - город зассыпает... \r\n'+
                    '/cancel - закончить игру')

from queue import Queue
updater = Updater(token, Queue())

from telegram.ext import Application, CommandHandler

application = Application.builder().token(token).build()

application.add_handler(CommandHandler('new', new))
application.add_handler(CommandHandler('join', join))
application.add_handler(CommandHandler('play', play))
application.add_handler(CommandHandler('cancel', cancel))
application.add_handler(CommandHandler('help', help))


@dp.message(lambda m: m.text and m.text.lower() == "выдать коины")
async def admin_give_coins(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer("Нет доступа.")
        return
    await state.set_state(AdminStates.entering_coins)
    await msg.answer("Введи сколько коинов выдать:")

@dp.message(AdminStates.entering_coins)
async def process_coins_amount(m: Message, state: FSMContext):
    try:
        coins = int(m.text)
        user = get_user(m.from_user.id)
        user["coins"] += coins
        update_user(m.from_user.id, user)
        await m.answer(f"Выдано {coins} коинов. Текущий баланс: {user['coins']}")
    except:
        await m.answer("Ошибка. Введи число.")
    await state.clear()

@dp.message(lambda m: m.text and m.text.lower() == "выдать ману")
async def admin_give_mana(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer("Нет доступа.")
        return
    await state.set_state(AdminStates.entering_mana)
    await msg.answer("Введи сколько маны выдать:")

@dp.message(AdminStates.entering_mana)
async def process_mana_amount(m: Message, state: FSMContext):
    try:
        mana = int(m.text)
        user = get_user(m.from_user.id)
        user["mana"] += mana
        update_user(m.from_user.id, user)
        await m.answer(f"Выдано {mana} маны. Текущий баланс: {user['mana']}")
    except:
        await m.answer("Ошибка. Введи число.")
    await state.clear()

@dp.message(lambda m: m.text and m.text.lower() == "выдать машину")
async def admin_give_car(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer("Нет доступа.")
        return
    await state.set_state(AdminStates.entering_car)
    await msg.answer("Введи модель машины для выдачи:")

@dp.message(AdminStates.entering_car)
async def process_car_amount(m: Message, state: FSMContext):
    car_model = m.text.strip()
    user = get_user(m.from_user.id)
    user["car"] = car_model
    update_user(m.from_user.id, user)
    await m.answer(f"Выдана машина: {car_model}")
    await state.clear()

@dp.message(lambda m: m.text and m.text.lower() == "выдать телефон")
async def admin_give_phone(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer("Нет доступа.")
        return
    await state.set_state(AdminStates.entering_phone)
    await msg.answer("Введи модель телефона для выдачи:")

@dp.message(AdminStates.entering_phone)
async def process_phone_amount(m: Message, state: FSMContext):
    phone_model = m.text.strip()
    user = get_user(m.from_user.id)
    user["phone"] = phone_model
    update_user(m.from_user.id, user)
    await m.answer(f"Выдан телефон: {phone_model}")
    await state.clear()

@dp.message(lambda m: m.text and m.text.lower() == "выдать ноутбук")
async def admin_give_notebook(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer("Нет доступа.")
        return
    await state.set_state(AdminStates.entering_notebook)
    await msg.answer("Введи модель ноутбука для выдачи:")

@dp.message(lambda m: m.text and m.text.lower() in ['отмена', '/отмена', 'cancel'])
async def cancel_any_fsm(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Действие отменено. Вы в главном меню.", reply_markup=ReplyKeyboardRemove())


@dp.message(AdminStates.entering_notebook)
async def process_notebook_amount(m: Message, state: FSMContext):
    notebook_model = m.text.strip()
    user = get_user(m.from_user.id)
    user["notebook"] = notebook_model
    update_user(m.from_user.id, user)
    await m.answer(f"Выдан ноутбук: {notebook_model}")
    await state.clear()


# ...все твои импорты и код выше...

@dp.message(lambda m: m.text and m.text.lower() == "профиль")
async def profile(msg: Message):
    user = get_user(msg.from_user.id)
    user["level"] = calc_level(user.get("messages", 0))
    update_user(msg.from_user.id, {"level": user["level"]})
    text = (
        f"👤 <b>Профиль</b>\n"
        f"Парадизкоины: <b>{user['coins']}</b>\n"
        f"Парадиз мана: <b>{user['mana']}</b>\n"
        f"Уровень: <b>{user['level']}</b>\n"
        f"Сообщений: <b>{user.get('messages',0)}</b>\n"
        f"🚗 Машина: <b>{user['car']}</b>\n"
        f"🏢 Бизнес: <b>{user['business']}</b>\n"
        f"📱 Телефон: <b>{user['phone']}</b>\n"
        f"💻 Ноутбук: <b>{user['notebook']}</b>\n"
        f"💼 Работа: <b>{user.get('job','Безработный')}</b>"
    )
    await msg.answer(text, parse_mode=ParseMode.HTML)

# ...остальные команды...

# В help/помощь добавь описание
@dp.message(lambda m: m.text and m.text.lower() == "помощь")
async def help_command(msg: Message):
    await msg.answer(
        "🆘 <b>Помощь</b>\n\n"
        "<b>Доступные команды:</b>\n"
        "парадиз — главное меню\n"
        "магазин — открыть магазин\n"
        "телефоны — список телефонов\n"
        "машины — список машин\n"
        "ноутбуки — список ноутбуков\n"
        "профиль — посмотреть профиль\n"
        "работа — посмотреть и выбрать профессию\n"
        "зарплата — получить зарплату на текущей работе\n"
        "ферма — зайти на ферму\n"
        "бонус — получить ежедневный бонус\n"
        "промокод — активировать промокод\n"
        "админ — админ-панель (для админов)\n"
        "\n"
        "<b>Фермерские:</b>\n"
        "состояние грядок — что растет и сколько ждать\n"
        "посадить [культуру] — быстро посадить растение\n"
        "собрать урожай — собрать готовый урожай\n"
        "купить грядку — расширить ферму\n"
        "купить удобрение — ускорить рост\n"
        "\n"
        "<b>Экономика и инвентарь:</b>\n"
        "курс валют — узнать курс игровых валют и доллара\n"
        "инвентарь — посмотреть свои запасы и предметы\n"
        "\n"
        "<b>Погода и развлечения:</b>\n"
        "погода [город] — узнать погоду в городе\n"
        "\n"
        "<b>Аукцион:</b>\n"
        "аукцион [предмет] [начальная цена] — открыть аукцион\n"
        "ставка [цена] — сделать ставку на аукцион\n"
        "мои сделки — посмотреть свои аукционные сделки\n"
        "\n"
        "<b>Социальное:</b>\n"
        "перевести @user сумма — перевести коины\n"
        "предложение @user — сделать предложение пользователю\n"
        "согласен — принять предложение (брак)\n"
        "развод — расторгнуть брак\n"
        "\n"
        "Для покупки в магазине: <i>номер цвет</i> (например: 1 черный)\n"
        "Если нужна подробная инструкция по команде — просто напиши её название!\n",
        parse_mode=ParseMode.HTML
    )

# ...остальной твой код...
import time
from aiogram import Bot
from aiogram.types import Message

# Функции is_admin, is_moderator, get_user, update_user должны быть определены выше!

# Исправленный блок предложения брака
pending_marriages = {}  # user_id: partner_id

@dp.message(lambda m: m.text and m.text.lower().startswith("предложение "))
async def propose_marriage(msg: Message):
    parts = msg.text.split()
    if len(parts) < 2:
        await msg.answer("Использование: предложение @user")
        return
    to_name = parts[1]
    db = load_db()
    to_id = None
    to_search = to_name.replace("@", "").lower()
    for uid, data in db.items():
        if not isinstance(data, dict):
            continue
        if (data.get("nick", "").lower() == to_search or data.get("username", "").lower() == to_search):
            to_id = int(uid)
            break
    if not to_id:
        await msg.answer("Пользователь не найден.")
        return
    if to_id == msg.from_user.id:
        await msg.answer("Нельзя жениться на себе :)")
        return
    user = get_user(msg.from_user.id)
    if user.get("partner"):
        await msg.answer("Ты уже в браке!")
        return
    partner = get_user(to_id)
    if partner.get("partner"):
        await msg.answer("Пользователь уже в браке!")
        return
    pending_marriages[to_id] = msg.from_user.id
    await msg.answer(f"Ты сделал(-а) предложение {to_name}! Ждём ответа.")
    try:
        await msg.bot.send_message(
            to_id,
            f"Вам сделали предложение руки и сердца! Напишите 'согласен' чтобы принять."
        )
    except Exception:
        pass

# Система браков
pending_marriages = {}  # user_id: partner_id

@dp.message(lambda m: m.text and m.text.lower().startswith("предложение "))
async def propose_marriage(msg: Message):
    parts = msg.text.split()
    if len(parts) < 2:
        await msg.answer("Использование: предложение @user")
        return
    to_name = parts[1]
    db = load_db()
    to_id = None
    to_search = to_name.replace("@", "").lower()
    for uid, data in db.items():
        if not isinstance(data, dict):
            continue
        if (data.get("nick", "").lower() == to_search or data.get("username", "").lower() == to_search):
            to_id = int(uid)
            break
    if not to_id:
        await msg.answer("Пользователь не найден.")
        return
    if to_id == msg.from_user.id:
        await msg.answer("Нельзя жениться на себе :)")
        return
    user = get_user(msg.from_user.id)
    if user.get("partner"):
        await msg.answer("Ты уже в браке!")
        return
    partner = get_user(to_id)
    if partner.get("partner"):
        await msg.answer("Пользователь уже в браке!")
        return
    pending_marriages[to_id] = msg.from_user.id
    await msg.answer(f"Ты сделал(-а) предложение {to_name}! Ждём ответа.")
    try:
        await msg.bot.send_message(to_id, f"Вам сделали предложение руки и сердца! Напишите 'согласен' чтобы принять.")
    except Exception:
        pass

@dp.message(lambda m: m.text and m.text.lower() == "согласен")
async def accept_marriage(msg: Message):
    user_id = msg.from_user.id
    if user_id not in pending_marriages:
        await msg.answer("Вам никто не делал предложения.")
        return
    partner_id = pending_marriages.pop(user_id)
    user = get_user(user_id)
    partner = get_user(partner_id)
    user["partner"] = partner_id
    partner["partner"] = user_id
    update_user(user_id, user)
    update_user(partner_id, partner)
    await msg.answer("Поздравляем! Теперь вы в браке ❤️")
    try:
        await msg.bot.send_message(partner_id, f"Пользователь {user.get('nick') or '@'+user.get('username', str(user_id))} согласился(-ась) выйти за вас замуж/жениться!")
    except Exception:
        pass

@dp.message(lambda m: m.text and m.text.lower() == "развод")
async def divorce(msg: Message):
    user = get_user(msg.from_user.id)
    if not user.get("partner"):
        await msg.answer("Вы не в браке!")
        return
    partner_id = user["partner"]
    partner = get_user(partner_id)
    user["partner"] = None
    if partner:
        partner["partner"] = None
        update_user(partner_id, partner)
        try:
            await msg.bot.send_message(partner_id, "Вам подали на развод 💔")
        except Exception:
            pass
    update_user(msg.from_user.id, user)
    await msg.answer("Вы развелись.")


from aiogram.fsm.state import State, StatesGroup

class PromoStates(StatesGroup):
    promo_code_step1 = State()
    promo_code_step2 = State()
    promo_code_step3 = State()


@dp.message(lambda m: m.text and m.text.lower() == "создать промокод")
async def create_promo_start(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer("Нет доступа.")
        return
    await msg.answer("Введи код промокода (например: SUMMER2025):")
    await state.set_state(PromoStates.promo_code_step1)

@dp.message(PromoStates.promo_code_step1)
async def promo_code_step1(msg: Message, state: FSMContext):
    code = msg.text.strip()
    await state.update_data(code=code)
    await msg.answer("Тип награды: coins или mana?")
    await state.set_state(PromoStates.promo_code_step2)

@dp.message(PromoStates.promo_code_step2)
async def promo_code_step2(msg: Message, state: FSMContext):
    reward_type = msg.text.strip().lower()
    if reward_type not in ["coins", "mana"]:
        await msg.answer("Введи только coins или mana!")
        return
    await state.update_data(reward_type=reward_type)
    await msg.answer("Введи значение награды (сколько):")
    await state.set_state(PromoStates.promo_code_step3)

@dp.message(PromoStates.promo_code_step3)
async def promo_code_step3(msg: Message, state: FSMContext):
    try:
        value = int(msg.text.strip())
    except Exception:
        await msg.answer("Введи число!")
        return
    data = await state.get_data()
    code = data["code"]
    reward_type = data["reward_type"]
    create_promo(code, reward_type, value)
    await msg.answer(f"Промокод {code} создан! Тип: {reward_type}, значение: {value}")
    await state.clear()

# МУТ
@dp.message(lambda m: m.text and m.text.startswith("мут"))
async def mute_user(msg: Message):
    if not (is_admin(msg.from_user.id) or is_moderator(msg.from_user.id)):
        return
    try:
        args = msg.text.split()
        user_id = int(args[1])
        mins = int(args[2])
        reason = " ".join(args[3:]) or "Без причины"
        mute_until = int(time.time()) + mins*60
        user = get_user(user_id)
        user["muted"] = True
        user["mute_until"] = mute_until
        user["mute_reason"] = reason
        update_user(user_id, user)
        await msg.answer(f"Пользователь {user_id} в муте на {mins} мин. Причина: {reason}")
    except Exception:
        await msg.answer("Использование: мут user_id минуты причина")

@dp.message(lambda m: m.text and m.text.startswith("размут"))
async def unmute_user(msg: Message):
    if not (is_admin(msg.from_user.id) or is_moderator(msg.from_user.id)):
        return
    try:
        args = msg.text.split()
        user_id = int(args[1])
        user = get_user(user_id)
        user["muted"] = False
        user["mute_until"] = 0
        user["mute_reason"] = ""
        update_user(user_id, user)
        await msg.answer(f"Пользователь {user_id} размучен.")
    except:
        await msg.answer("Использование: размут user_id")

    print('user:', msg.from_user.id, user)


@dp.message(lambda m: m.text and m.text.startswith("модер"))
async def grant_moder(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("Нет доступа.")
        return
    try:
        args = msg.text.split()
        user_id = int(args[1])
        add_moderator(user_id)
        await msg.answer(f"Пользователь {user_id} теперь модератор!")
    except Exception:
        await msg.answer("Использование: модер user_id")

# Хендлер снятия модерки (только для админов)
@dp.message(lambda m: m.text and m.text.startswith("размодер"))
async def revoke_moder(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("Нет доступа.")
        return
    try:
        args = msg.text.split()
        user_id = int(args[1])
        remove_moderator(user_id)
        await msg.answer(f"Пользователь {user_id} больше не модератор.")
    except Exception:
        await msg.answer("Использование: размодер user_id")

@dp.message(lambda m: m.text and m.text.startswith("модеры"))
async def list_moders(msg: Message):
    db = load_db()
    mods = db.get("moderators", [])
    if mods:
        await msg.answer("Модераторы:\n" + "\n".join(mods))
    else:
        await msg.answer("Модераторов пока нет.")

@dp.message(lambda m: m.text and m.text.startswith("роль"))
async def who_am_i(msg: Message):
    if is_admin(msg.from_user.id):
        role = "Админ"
    elif is_moderator(msg.from_user.id):
        role = "Модератор"
    else:
        role = "Пользователь"
    await msg.answer(f"Ваша роль: {role}")

@dp.message(lambda m: m.text and m.text.startswith("модпомощь"))
async def moder_help(msg: Message):
    if not can_moderate(msg.from_user.id):
        return
    await msg.answer(
        "мут user_id мин причина — выдать мут\n"
        "размут user_id — снять мут\n"

        "кик user_id — кикнуть\n"
        "модеры — список модеров\n"
        "роль — узнать свою роль"
    )


@dp.message(lambda m: m.text and m.text.lower().startswith("ник "))
async def set_nick(msg: Message):
    nick = msg.text[4:].strip()
    if not (1 <= len(nick) <= 32):
        await msg.answer("Ник должен быть от 1 до 32 символов.")
        return
    # Можно добавить проверку на нецензурные слова и уникальность ника!
    user = get_user(msg.from_user.id)
    user["nick"] = nick
    update_user(msg.from_user.id, user)
    await msg.answer(f"Твой ник теперь: <b>{nick}</b>", parse_mode="HTML")

# КИК (из группы)
@dp.message(lambda m: m.text and m.text.startswith("кик"))
async def kick_user(msg: Message):
    if not (is_admin(msg.from_user.id) or is_moderator(msg.from_user.id)):
        return
    try:
        args = msg.text.split()
        user_id = int(args[1])
        try:
            await msg.bot.ban_chat_member(msg.chat.id, user_id)
            await msg.bot.unban_chat_member(msg.chat.id, user_id)
            await msg.answer(f"Пользователь {user_id} кикнут из группы.")
        except Exception as err:
            await msg.answer(f"Ошибка кика: {err}")
    except:
        await msg.answer("Использование: кик user_id")

# Погода
@dp.message(lambda m: m.text and m.text.lower().startswith("погода"))
async def weather(msg: types.Message):
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("Напиши город, например: погода Москва")
        return
    city = parts[1]
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid={OPENWEATHER_API_KEY}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            if data.get("cod") != 200:
                await msg.answer("Город не найден.")
                return
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            await msg.answer(f"Погода в {city}: {desc}, {temp}°C")

# Инвентарь
@dp.message(lambda m: m.text and m.text.lower() == "инвентарь")
async def show_inventory(msg: Message):
    user = get_user(msg.from_user.id)
    text = "<b>🎒 Твой инвентарь:</b>\n"

    # Обычные предметы
    if user.get("phone"):
        text += f"• Телефон: {user['phone']}\n"
    if user.get("car"):
        text += f"• Машина: {user['car']}\n"
    if user.get("notebook"):
        text += f"• Ноутбук: {user['notebook']}\n"
    if user.get("adult_items"):
        text += "• 18+: " + ", ".join(user["adult_items"]) + "\n"

    # NFT подарки — отдельным блоком, даже если пусто
    nft = user.get("nft_items", [])
    text += "\n<b>🎁 NFT-подарки:</b>\n"
    if nft:
        for n in nft:
            text += f"• {n}\n"
    else:
        text += "Нет\n"

    await msg.answer(text, parse_mode="HTML")

# Курс валют (игровой и реальный курс доллара)
@dp.message(lambda m: m.text and m.text.lower() == "курс валют")
async def currency_rate(msg: types.Message):
    coin_to_mana = 10
    text = f"Игровой курс: 1 мана = {coin_to_mana} коинов\n"
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json(content_type=None)  # <-- вот здесь исправление
            usd = data["Valute"]["USD"]["Value"]
            text += f"Курс доллара: {usd:.2f} RUB"
    await msg.answer(text)


active_auctions = {}  # item -> auction dict

@dp.message(lambda m: m.text and m.text.lower().startswith("аукцион"))
async def auction_start(msg: types.Message):
    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3 or not parts[2].isdigit():
        await msg.answer("Формат: аукцион [предмет] [начальная цена]\nПример: аукцион арбуз 100")
        return
    item = parts[1]
    price = int(parts[2])
    if item in active_auctions:
        await msg.answer("Аукцион на этот предмет уже идёт!")
        return
    active_auctions[item] = {"owner": msg.from_user.id, "price": price, "winner": None}
    await msg.answer(f"Аукцион на {item} открыт! Стартовая цена: {price}. Делайте ставки командой 'ставка N'.")

@dp.message(lambda m: m.text and m.text.lower().startswith("ставка"))
async def auction_bid(msg: types.Message):
    parts = msg.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await msg.answer("Формат: ставка [цена]\nПример: ставка 150")
        return
    bid = int(parts[1])
    # ищем активный аукцион с самой высокой ценой
    for item, auction in active_auctions.items():
        if bid > auction["price"]:
            auction["price"] = bid
            auction["winner"] = msg.from_user.id
            await msg.answer(f"Ставка {bid} на {item} принята! Вы — лидер.")
            return
    await msg.answer("Нет активных аукционов или ваша ставка слишком мала.")

@dp.message(lambda m: m.text and m.text.lower() == "мои сделки")
async def my_auctions(msg: types.Message):
    text = "<b>Твои аукционные сделки:</b>\n"
    found = False
    for item, auction in active_auctions.items():
        if auction.get("winner") == msg.from_user.id or auction.get("owner") == msg.from_user.id:
            text += f"{item}: цена {auction['price']}, лидер: {auction.get('winner')}\n"
            found = True
    if not found:
        text += "Нет активных сделок."
    await msg.answer(text, parse_mode="HTML")



import os
import pickle
from datetime import datetime, timedelta
from market_items import market_extra_items

MARKET_STATE_FILE = "market_state.pkl"

def get_market_items():
    if os.path.exists(MARKET_STATE_FILE):
        with open(MARKET_STATE_FILE, "rb") as f:
            state = pickle.load(f)
        if datetime.now() < state["expires"]:
            return state["items"]
    # Сформировать новый рынок
    all_items = []
    phones_sample = random.sample(phones, 2)
    cars_sample = random.sample(cars, 1)
    laptops_sample = random.sample(laptops, 1)
    # Скидка 25%
    for it in phones_sample+cars_sample+laptops_sample:
        item = it.copy()
        item["price"] = int(item["price"] * 0.75)
        all_items.append(item)
    extra = random.sample(market_extra_items, min(2, len(market_extra_items)))
    all_items.extend(extra)
    state = {"items": all_items, "expires": datetime.now() + timedelta(hours=6)}
    with open(MARKET_STATE_FILE, "wb") as f:
        pickle.dump(state, f)
    return all_items


@dp.message(lambda m: m.text and m.text.lower() == "рынок")
async def market_menu(msg: Message):
    items = get_market_items()
    text = "<b>🛒 Рынок (обновляется каждые 6 часов):</b>\n"
    for i, item in enumerate(items, 1):
        text += f"{i}. {item['name']} — {item['price']} коинов"
        if "desc" in item:
            text += f" ({item['desc']})"
        text += "\n"
    text += "\nДля покупки: рынок купить номер"
    await msg.answer(text, parse_mode="HTML")

@dp.message(lambda m: m.text and m.text.lower().startswith("рынок купить"))
async def market_buy(msg: Message):
    parts = msg.text.strip().split()
    if len(parts) < 3 or not parts[2].isdigit():
        await msg.answer("Формат: рынок купить номер")
        return
    idx = int(parts[2]) - 1
    items = get_market_items()
    if not (0 <= idx < len(items)):
        await msg.answer("Нет такого товара.")
        return
    item = items[idx]
    user = get_user(msg.from_user.id)
    if user["coins"] < item["price"]:
        await msg.answer("Недостаточно коинов.")
        return
    user["coins"] -= item["price"]
    # Можно добавить выдачу уникальных предметов в инвентарь
    if "desc" in item:
        user.setdefault("inventory", {})
        user["inventory"][item["name"]] = user["inventory"].get(item["name"], 0) + 1
    else:
        # Как в магазине: phone, car, notebook
        if item in phones:
            user["phone"] = item["name"]
        elif item in cars:
            user["car"] = item["name"]
        elif item in laptops:
            user["notebook"] = item["name"]
    update_user(msg.from_user.id, user)
    await msg.answer(f"Покупка успешна! Ты купил {item['name']}. Осталось: {user['coins']} коинов.")

NFT_ITEMS = [
    {"name": "Алмаз Дурова", "desc": "Легендарный NFT!"},
    {"name": "Трусы Дурова", "desc": "Эксклюзив!"},
    {"name": "Золотая чаша", "desc": "Роскошь!"},
]

NFT_PRICE = 100000  # фиксированная цена

def get_nft_items():
    return NFT_ITEMS

from aiogram.fsm.state import State, StatesGroup
class ShopStates(StatesGroup):
    buying = State()
    nft_buying = State()

@dp.message(lambda m: m.text and m.text.lower() == "нфт магазин")
async def nft_shop_menu(msg: Message, state: FSMContext):
    text = "<b>🎁 NFT-магазин</b>\n\n"
    for idx, item in enumerate(get_nft_items(), 1):
        text += f"{idx}. {item['name']} — {item['desc']}. Цена: {NFT_PRICE} коинов\n"
    text += "\nДля покупки: нфт купить номер\nДля выхода: нфт выход"
    await msg.answer(text, parse_mode="HTML")
    await state.set_state(ShopStates.nft_buying)

@dp.message(ShopStates.nft_buying)
async def nft_shop_buy(msg: Message, state: FSMContext):
    txt = msg.text.strip().lower()
    if txt == "нфт выход":
        await msg.answer("Вы вышли из NFT-магазина.")
        await state.clear()
        return

    if txt.startswith("нфт купить"):
        parts = txt.split()
        if len(parts) < 3 or not parts[2].isdigit():
            await msg.answer("Формат: нфт купить номер")
            return
        idx = int(parts[2]) - 1
        nft_items = get_nft_items()
        if not (0 <= idx < len(nft_items)):
            await msg.answer("Нет такого NFT.")
            return
        user = get_user(msg.from_user.id)
        nft_name = nft_items[idx]["name"]
        if nft_name in user.get("nft_items", []):
            await msg.answer("Этот NFT уже у тебя есть!")
            return
        if user["coins"] < NFT_PRICE:
            await msg.answer("Недостаточно коинов для покупки.")
            return
        user["coins"] -= NFT_PRICE
        user.setdefault("nft_items", []).append(nft_name)
        update_user(msg.from_user.id, user)
        await msg.answer(f"Поздравляем! Ты купил NFT: {nft_name} за {NFT_PRICE} коинов.")
        await state.clear()
        return

    await msg.answer("Для покупки: нфт купить номер\nДля выхода: нфт выход")


router = Router()

# Пример простой "базы" балансов (замени на свою систему!)
balances = {}

def get_coins(user_id):
    return balances.get(user_id, 0)

def add_coins(user_id, amount):
    balances[user_id] = get_coins(user_id) + amount

def remove_coins(user_id, amount):
    balances[user_id] = max(0, get_coins(user_id) - amount)

# FSM для передачи монет
class TransferStates(StatesGroup):
    waiting_for_recipient = State()
    waiting_for_amount = State()

# Старт передачи
@router.message(lambda m: m.text and m.text.lower().startswith("перевести"))
async def transfer_start(msg: Message, state: FSMContext):
    await msg.answer("Укажи ID пользователя, которому хочешь перевести монеты:")
    await state.set_state(TransferStates.waiting_for_recipient)

# Получаем ID получателя
@router.message(TransferStates.waiting_for_recipient)
async def transfer_get_recipient(msg: Message, state: FSMContext):
    try:
        recipient_id = int(msg.text.strip())
        if recipient_id == msg.from_user.id:
            await msg.answer("Нельзя переводить монеты самому себе.")
            return
        await state.update_data(recipient_id=recipient_id)
        await msg.answer("Сколько монет перевести?")
        await state.set_state(TransferStates.waiting_for_amount)
    except Exception:
        await msg.answer("Некорректный ID пользователя. Введи числовой ID!")

# Получаем сумму и выполняем перевод
@router.message(TransferStates.waiting_for_amount)
async def transfer_get_amount(msg: Message, state: FSMContext):
    try:
        amount = int(msg.text.strip())
        data = await state.get_data()
        recipient_id = data["recipient_id"]
        sender_id = msg.from_user.id

        if amount <= 0:
            await msg.answer("Сумма должна быть положительной!")
            return
        if get_coins(sender_id) < amount:
            await msg.answer("У тебя недостаточно монет.")
            return

        remove_coins(sender_id, amount)
        add_coins(recipient_id, amount)
        await msg.answer(f"Успешно переведено {amount} монет пользователю {recipient_id}!")
        await state.clear()
    except Exception:
        await msg.answer("Ошибка! Введи корректное число монет.")

from aiogram import Bot, Dispatcher
import asyncio
from anime_vote_handlers import router


from datetime import datetime, timedelta, UTC

PROMO_PARADISE_REWARD = 100_000

@dp.message(lambda m: m.text and m.text.lower() == "промокод paradise")
async def promo_paradise(msg: types.Message):
    user = get_user(msg.from_user.id)
    now = datetime.now(UTC)
    last = user.get("promo_paradise_last", 0)
    if last:
        last_dt = datetime.fromtimestamp(last, UTC)
        if (now - last_dt) < timedelta(days=7):
            left = timedelta(days=7) - (now - last_dt)
            d, h, m = left.days, left.seconds//3600, (left.seconds//60)%60
            txt = []
            if d: txt.append(f"{d}д")
            if h: txt.append(f"{h}ч")
            if m: txt.append(f"{m}м")
            await msg.answer(f"Этот промокод можно активировать раз в неделю.\nОсталось ждать: {' '.join(txt) or 'несколько минут'}")
            return
    user["coins"] += PROMO_PARADISE_REWARD
    user["promo_paradise_last"] = int(now.timestamp())
    update_user(msg.from_user.id, user)
    await msg.answer(f"🎉 Ты активировал промокод PARADISE и получил {PROMO_PARADISE_REWARD:,} коинов!\nДо следующей активации — неделя.")


@dp.message(lambda m: m.text and m.text.lower() == "банк")
async def bank_status(msg: types.Message):
    balance, last = get_bank(msg.from_user.id)
    last_dt = datetime.datetime.fromtimestamp(last).strftime("%d.%m.%Y %H:%M")
    await msg.answer(f"🏦 Баланс в банке: {balance} коинов\nПоследнее начисление: {last_dt}\n"
                     f"Чтобы положить коины: банк пополнить 123\nЧтобы снять: банк снять 123")

@dp.message(lambda m: m.text and m.text.lower().startswith("банк пополнить"))
async def bank_deposit(msg: types.Message):
    parts = msg.text.strip().split()
    if len(parts) < 3 or not parts[2].isdigit():
        await msg.answer("Формат: банк пополнить 123 (где 123 — сумма перевода)")
        return
    amount = int(parts[2])
    if amount <= 0:
        await msg.answer("Сумма должна быть положительной.")
        return
    ok, txt = deposit(msg.from_user.id, amount)
    await msg.answer(txt)

@dp.message(lambda m: m.text and m.text.lower().startswith("банк снять"))
async def bank_withdraw(msg: types.Message):
    parts = msg.text.strip().split()
    if len(parts) < 3 or not parts[2].isdigit():
        await msg.answer("Формат: банк снять 123 (где 123 — сумма снятия)")
        return
    amount = int(parts[2])
    if amount <= 0:
        await msg.answer("Сумма должна быть положительной.")
        return
    ok, txt = withdraw(msg.from_user.id, amount)
    await msg.answer(txt)


# АНТИФЛУД — ОСТАВЛЯЕМ ТОЛЬКО ЭТОТ ГЛОБАЛЬНЫЙ ХЕНДЛЕР!
@dp.message()
async def filter_ban_mute(msg: Message):
    user = get_user(msg.from_user.id)
    user["messages"] = user.get("messages", 0) + 1
    user["first_name"] = msg.from_user.first_name
    user["username"] = msg.from_user.username
    week_now = datetime.now(UTC).isocalendar()[1]
    month_now = datetime.now(UTC).month
    if user.get("week_reset", week_now) != week_now:
        user["week_messages"] = 0
        user["week_reset"] = week_now
    if user.get("month_reset", month_now) != month_now:
        user["month_messages"] = 0
        user["month_reset"] = month_now
    user["week_messages"] = user.get("week_messages", 0) + 1
    user["month_messages"] = user.get("month_messages", 0) + 1
    user["level"] = calc_level(user["messages"])
    update_user(msg.from_user.id, user)

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
