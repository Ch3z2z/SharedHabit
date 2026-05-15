# SharedHabits

SharedHabits — это веб-приложение для совместного отслеживания привычек. Пользователи могут создавать привычки, делиться ими с друзьями, приглашать участников и отслеживать прогресс выполнения.\
<p align=center ><img width="297" height="600" alt="image" src="https://github.com/user-attachments/assets/356e5200-4db7-417c-b87d-6de6ef9e82ce" />&nbsp;&nbsp;&nbsp;<img width="362" height="600" alt="image" src="https://github.com/user-attachments/assets/5f23b9e9-0c27-4e83-aa12-b20f969fe9df" />
</p>



## Что внутри

- Flask + SQLAlchemy на Python
- PostgreSQL в Docker
- JWT-аутентификация через Flask-JWT-Extended
- Веб-интерфейс с Jinja2 шаблонами

## Быстрый старт с Docker

### Требования

- Docker
- Docker Compose

### Запуск

1. Перейдите в папку проекта:
   ```bash
   cd SharedHabbits
   ```

2. Запустите сервисы:
   ```bash
   docker-compose up -d
   ```

3. Откройте приложение:
   ```text
   http://localhost:5000
   ```

### Остановка

```bash
docker-compose down
```

## Локальный запуск (опционально)

Если вы хотите запустить приложение без Docker:

1. Создайте виртуальное окружение:
   ```bash
   python -m venv venv
   ```

2. Активируйте его:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/macOS:
     ```bash
     source venv/bin/activate
     ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Настройте подключение к базе данных в `app/config.py` или через переменную окружения `DATABASE_URL`.

5. Запустите приложение:
   ```bash
   python run.py
   ```

Приложение будет доступно по адресу `http://localhost:5000`.

## Конфигурация

Основные параметры задаются через переменные окружения:

- `DATABASE_URL` — URL подключения к PostgreSQL
- `JWT_SECRET_KEY` — секретный ключ для JWT
- `FLASK_APP` — `run.py`
- `FLASK_ENV` — `development`

По умолчанию приложение использует:

- `postgresql://postgres:postgres@localhost/SharedHabit`
- `JWT_SECRET_KEY=super-secret`

## Docker-конфигурация

- `Dockerfile` — сборка образа Python-приложения
- `docker-compose.yml` — сервисы `web` и `postgres`
- `.dockerignore` — файлы, исключаемые из сборки

В `docker-compose.yml` PostgreSQL создается с:

- пользователь: `postgres`
- пароль: `postgres`
- база: `SharedHabit`

## Структура проекта

```
SharedHabbits/
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── README.md
├── requirements.txt
├── run.py
├── app/
│   ├── __init__.py
│   ├── auth.py
│   ├── config.py
│   ├── habits.py
│   ├── models.py
│   ├── utils.py
│   ├── web.py
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── habits.html
│       ├── habit.html
│       ├── habit_edit.html
│       ├── profile.html
│       ├── profile_settings.html
│       ├── user_profile.html
│       └── invites.html
```

## Основные маршруты

- `GET /` — главная страница
- `POST /api/login` — вход
- `POST /api/register` — регистрация
- `POST /api/logout` — выход
- `POST /api/refresh` — refresh token
- `GET /api/habits` — список привычек
- `POST /api/habits` — создание привычки
- `GET /api/habits/<id>` — детали привычки
- `PUT /api/habits/<id>` — обновление привычки
- `DELETE /api/habits/<id>` — удаление привычки
- `GET /api/habits/<id>/logs` — логи привычки
- `POST /api/habits/<id>/logs` — добавление лога
- `POST /api/habits/<id>/invite` — отправка приглашения
- `GET /api/invites` — список приглашений
- `POST /api/invites/<id>/accept` — принятие приглашения

