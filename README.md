# AlmatyAir Bot

Telegram-бот для уведомлений о качестве воздуха в Алматы.

Данные: [IQAir API](https://www.iqair.com/)

## Возможности

- Текущее качество воздуха и погода (`/air`)
- Ежедневные уведомления в заданное время
- Оповещения при превышении порога AQI (101/151/201/301)
- Уведомления об улучшении качества воздуха

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Настройка уведомлений |
| `/air` | Текущее качество воздуха |
| `/test` | Тест уведомлений |

## Технологии

- Python 3.12
- aiogram 3.22
- PostgreSQL 16
- APScheduler
- Docker

## Установка

### 1. Клонировать репозиторий

```bash
git clone git@github.com:androsovm/AlmatyAir.git
cd AlmatyAir
```

### 2. Создать `.env` файл

```bash
cp .env.example .env
```

Заполнить переменные:

```env
BOT_TOKEN=your_telegram_bot_token
IQAIR_API_KEY=your_iqair_api_key

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=almaty_air
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=almaty_air
```

**Получить ключи:**
- Telegram Bot Token: [@BotFather](https://t.me/BotFather)
- IQAir API Key: [dashboard.iqair.com](https://dashboard.iqair.com/)

### 3. Запустить

```bash
docker-compose up -d
```

### 4. Проверить логи

```bash
docker-compose logs -f bot
```

## Разработка

### Локальный запуск без Docker

```bash
# Установить зависимости
pip install -r requirements.txt

# Запустить PostgreSQL отдельно
docker-compose up -d postgres

# Запустить бота
python -m bot.main
```

### Пересборка после изменений

```bash
docker-compose up --build -d
```

## Структура проекта

```
AlmatyAir/
├── bot/
│   ├── main.py              # Точка входа
│   ├── config.py            # Конфигурация
│   ├── handlers/            # Обработчики команд
│   ├── keyboards/           # Inline клавиатуры
│   ├── services/            # IQAir API, планировщик
│   ├── states/              # FSM состояния
│   └── database/            # Модели и репозиторий
├── alembic/                 # Миграции БД
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Лицензия

MIT
