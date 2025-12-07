from datetime import datetime

import pytz
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.database import UserRepository, async_session
from bot.keyboards import get_notification_choices_keyboard
from bot.services.iqair import iqair_service
from bot.states import SetupStates

ALMATY_TZ = pytz.timezone("Asia/Almaty")


def get_greeting(hour: int) -> str:
    if 5 <= hour < 12:
        return "🌅 Доброе утро!"
    elif 12 <= hour < 18:
        return "🌤 Добрый день!"
    elif 18 <= hour < 23:
        return "🌆 Добрый вечер!"
    else:
        return "🌙 Доброй ночи!"

router = Router()

WELCOME_MESSAGE = """Здравствуйте! Вас приветствует бот, который получает данные о состоянии воздуха в городе Алматы и отправляет их Вам.

Укажите какие уведомления вы хотели бы получать от бота:"""


@router.message(Command("air"))
async def cmd_air(message: Message) -> None:
    """Show current air quality"""
    air_data = await iqair_service.get_air_quality()
    if air_data:
        await message.answer(air_data.format_message(), parse_mode="HTML")
    else:
        await message.answer("Не удалось получить данные о качестве воздуха. Попробуйте позже.")


@router.message(Command("test"))
async def cmd_test(message: Message) -> None:
    """Test notification - shows how daily and alert notifications will look"""
    air_data = await iqair_service.get_air_quality()
    if not air_data:
        await message.answer("Не удалось получить данные. Попробуйте позже.")
        return

    # Get current hour in Almaty
    now = datetime.now(ALMATY_TZ)
    greeting = get_greeting(now.hour)

    # Show daily notification example
    daily_msg = f"<b>{greeting}</b>\n\n{air_data.format_message()}"
    await message.answer(daily_msg, parse_mode="HTML")

    # Show alert notification example
    if air_data.aqi >= 101:
        alert_msg = f"⚠️ <b>Внимание! Качество воздуха ухудшилось</b>\n\n{air_data.format_message()}"
    else:
        alert_msg = f"✅ <b>Качество воздуха улучшилось!</b>\n\n{air_data.format_message()}"
    await message.answer(alert_msg, parse_mode="HTML")


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    # Get or create user
    async with async_session() as session:
        repo = UserRepository(session)
        user = await repo.get_or_create(message.from_user.id)

        # Initialize FSM state data with user's current settings
        await state.update_data(
            daily_enabled=user.daily_enabled,
            alert_enabled=user.alert_enabled,
            daily_hour=user.daily_hour,
            daily_minute=user.daily_minute,
            alert_threshold=user.alert_threshold,
        )

    # Set state and send welcome message
    await state.set_state(SetupStates.choose_notifications)
    await message.answer(
        WELCOME_MESSAGE,
        reply_markup=get_notification_choices_keyboard(
            daily_enabled=True, alert_enabled=True
        ),
    )
