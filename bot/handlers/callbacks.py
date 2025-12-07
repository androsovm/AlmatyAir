from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.database import UserRepository, async_session
from bot.keyboards import (
    get_notification_choices_keyboard,
    get_threshold_keyboard,
    get_time_keyboard,
)
from bot.states import SetupStates

router = Router()


# ============ Screen 1: Notification choices ============


@router.callback_query(SetupStates.choose_notifications, F.data == "toggle_daily")
async def toggle_daily(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    daily_enabled = not data.get("daily_enabled", True)
    await state.update_data(daily_enabled=daily_enabled)

    await callback.message.edit_reply_markup(
        reply_markup=get_notification_choices_keyboard(
            daily_enabled=daily_enabled,
            alert_enabled=data.get("alert_enabled", True),
        )
    )
    await callback.answer()


@router.callback_query(SetupStates.choose_notifications, F.data == "toggle_alert")
async def toggle_alert(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    alert_enabled = not data.get("alert_enabled", True)
    await state.update_data(alert_enabled=alert_enabled)

    await callback.message.edit_reply_markup(
        reply_markup=get_notification_choices_keyboard(
            daily_enabled=data.get("daily_enabled", True),
            alert_enabled=alert_enabled,
        )
    )
    await callback.answer()


@router.callback_query(SetupStates.choose_notifications, F.data == "notifications_done")
async def notifications_done(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    daily_enabled = data.get("daily_enabled", True)
    alert_enabled = data.get("alert_enabled", True)

    if daily_enabled:
        # Go to time selection screen
        await state.set_state(SetupStates.set_time)
        await callback.message.edit_text(
            "Укажите в какое время вы бы хотели получать уведомления о качестве воздуха на предстоящий день:",
            reply_markup=get_time_keyboard(
                hour=data.get("daily_hour", 8),
                minute=data.get("daily_minute", 0),
            ),
        )
    elif alert_enabled:
        # Skip time, go to threshold
        await state.set_state(SetupStates.set_threshold)
        await callback.message.edit_text(
            "Укажите при каком качестве воздуха вы бы хотели получать уведомления.\n\n"
            "В случае если состояние воздуха улучшится, вы также получите уведомление об этом:",
            reply_markup=get_threshold_keyboard(data.get("alert_threshold", 101)),
        )
    else:
        # No notifications selected, save and finish
        await save_settings_and_finish(callback, state)

    await callback.answer()


# ============ Screen 2: Time selection ============


@router.callback_query(SetupStates.set_time, F.data == "hour_inc")
async def hour_increment(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    hour = (data.get("daily_hour", 8) + 1) % 24
    await state.update_data(daily_hour=hour)

    await callback.message.edit_reply_markup(
        reply_markup=get_time_keyboard(hour=hour, minute=data.get("daily_minute", 0))
    )
    await callback.answer()


@router.callback_query(SetupStates.set_time, F.data == "hour_dec")
async def hour_decrement(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    hour = (data.get("daily_hour", 8) - 1) % 24
    await state.update_data(daily_hour=hour)

    await callback.message.edit_reply_markup(
        reply_markup=get_time_keyboard(hour=hour, minute=data.get("daily_minute", 0))
    )
    await callback.answer()


@router.callback_query(SetupStates.set_time, F.data == "min_inc")
async def minute_increment(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    minute = (data.get("daily_minute", 0) + 5) % 60  # Increment by 5 minutes
    await state.update_data(daily_minute=minute)

    await callback.message.edit_reply_markup(
        reply_markup=get_time_keyboard(hour=data.get("daily_hour", 8), minute=minute)
    )
    await callback.answer()


@router.callback_query(SetupStates.set_time, F.data == "min_dec")
async def minute_decrement(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    minute = (data.get("daily_minute", 0) - 5) % 60  # Decrement by 5 minutes
    await state.update_data(daily_minute=minute)

    await callback.message.edit_reply_markup(
        reply_markup=get_time_keyboard(hour=data.get("daily_hour", 8), minute=minute)
    )
    await callback.answer()


@router.callback_query(SetupStates.set_time, F.data.in_({"hour_noop", "min_noop"}))
async def time_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(SetupStates.set_time, F.data == "time_done")
async def time_done(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    alert_enabled = data.get("alert_enabled", True)

    if alert_enabled:
        # Go to threshold selection
        await state.set_state(SetupStates.set_threshold)
        await callback.message.edit_text(
            "Укажите при каком качестве воздуха вы бы хотели получать уведомления.\n\n"
            "В случае если состояние воздуха улучшится, вы также получите уведомление об этом:",
            reply_markup=get_threshold_keyboard(data.get("alert_threshold", 101)),
        )
    else:
        # No alert notifications, save and finish
        await save_settings_and_finish(callback, state)

    await callback.answer()


# ============ Screen 3: Threshold selection ============


@router.callback_query(SetupStates.set_threshold, F.data.startswith("threshold_"))
async def select_threshold(callback: CallbackQuery, state: FSMContext) -> None:
    data_value = callback.data

    if data_value == "threshold_done":
        await save_settings_and_finish(callback, state)
        await callback.answer()
        return

    # Extract threshold value
    threshold = int(data_value.replace("threshold_", ""))
    await state.update_data(alert_threshold=threshold)

    await callback.message.edit_reply_markup(
        reply_markup=get_threshold_keyboard(selected_threshold=threshold)
    )
    await callback.answer()


# ============ Helper functions ============


async def save_settings_and_finish(callback: CallbackQuery, state: FSMContext) -> None:
    """Save user settings to database and show confirmation"""
    data = await state.get_data()

    async with async_session() as session:
        repo = UserRepository(session)
        user = await repo.get_or_create(callback.from_user.id)
        await repo.update(
            user,
            daily_enabled=data.get("daily_enabled", True),
            daily_hour=data.get("daily_hour", 8),
            daily_minute=data.get("daily_minute", 0),
            alert_enabled=data.get("alert_enabled", True),
            alert_threshold=data.get("alert_threshold", 101),
        )

    # Build confirmation message
    lines = ["✅ <b>Уведомления настроены!</b>\n"]

    if data.get("daily_enabled"):
        hour = data.get("daily_hour", 8)
        minute = data.get("daily_minute", 0)
        lines.append(f"📅 Ежедневные уведомления: {hour:02d}:{minute:02d}")

    if data.get("alert_enabled"):
        threshold = data.get("alert_threshold", 101)
        lines.append(f"⚠️ Оповещения при AQI ≥ {threshold}")

    if not data.get("daily_enabled") and not data.get("alert_enabled"):
        lines.append("❌ Все уведомления отключены")

    lines.append("\nНажмите /start для изменения настроек.")

    await callback.message.edit_text("\n".join(lines), parse_mode="HTML")
    await state.clear()
