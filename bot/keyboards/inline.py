from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_notification_choices_keyboard(
    daily_enabled: bool = True, alert_enabled: bool = True
) -> InlineKeyboardMarkup:
    """Screen 1: Notification type selection"""
    daily_icon = "✅" if daily_enabled else "❌"
    alert_icon = "✅" if alert_enabled else "❌"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{daily_icon} ежедневные уведомления о качестве воздуха",
                    callback_data="toggle_daily",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{alert_icon} уведомления при плохом воздухе",
                    callback_data="toggle_alert",
                )
            ],
            [
                InlineKeyboardButton(text="Готово", callback_data="notifications_done")
            ],
        ]
    )


def get_time_keyboard(hour: int = 8, minute: int = 0) -> InlineKeyboardMarkup:
    """Screen 2: Time selection for daily notifications"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            # Hour row
            [
                InlineKeyboardButton(text="◀️", callback_data="hour_dec"),
                InlineKeyboardButton(text=f"Час: {hour:02d}", callback_data="hour_noop"),
                InlineKeyboardButton(text="▶️", callback_data="hour_inc"),
            ],
            # Minute row
            [
                InlineKeyboardButton(text="◀️", callback_data="min_dec"),
                InlineKeyboardButton(text=f"Мин: {minute:02d}", callback_data="min_noop"),
                InlineKeyboardButton(text="▶️", callback_data="min_inc"),
            ],
            # Done button
            [InlineKeyboardButton(text="Готово", callback_data="time_done")],
        ]
    )


def get_threshold_keyboard(selected_threshold: int = 101) -> InlineKeyboardMarkup:
    """Screen 3: AQI threshold selection"""
    thresholds = [
        (101, "вредно для уязвимых групп"),
        (151, "вредно"),
        (201, "очень вредно"),
        (301, "опасно"),
    ]

    buttons = []
    for threshold, description in thresholds:
        icon = "✅" if threshold == selected_threshold else "◽"
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{icon} {threshold} - {description}",
                    callback_data=f"threshold_{threshold}",
                )
            ]
        )

    buttons.append([InlineKeyboardButton(text="Готово", callback_data="threshold_done")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
