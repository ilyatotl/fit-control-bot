from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import Form, FoodForm
from users_storage import UsersStorage, UserData
from config import WEIGHT_EXCEPTION_TEXT, HEIGHT_EXCEPTION_TEXT, AGE_EXCEPTION_TEXT, ACTIVITY_EXCEPTION_TEXT, FOOD_AMOUNT_EXCEPTION_TEXT, CALORIES_PER_SPORT

import clients


router = Router()
users_storage = UsersStorage()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Добро пожаловать! Я ваш бот.\nВведите /help для списка команд.")


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply("/set_profile - установить выши данные, для корректного расчета всех параметров\n"
                        + "/log_water <количество выпитой воды в мл> - сохранение информаии о выпитой воде\n"
                        + "/log_food <название еды> - сохранение числа ккал, после приема пищи\n"
                        + "/log_workout <тип тренировки> <продолжительность в минутах> - сохранение сожженных ккал на тренировке и рекомендация по выпитой жидкости\n"
                        + "/check_progress - получить прогресс по ккал и выпитой воде\n"
                        + "/get_profile_data - получить данные вашего профиля (вес, рост, возраст, город и тд)")


@router.message(Command("set_profile"))
async def start_setting_profile(message: Message, state: FSMContext):
    await message.answer("Введите ваш вес (в кг):")
    await state.set_state(Form.weight)


@router.message(Form.weight)
async def process_weight(message: Message, state: FSMContext):
    try:
        weight = int(message.text)
    except ValueError:
        await message.answer(WEIGHT_EXCEPTION_TEXT)
        return
    
    if weight <= 0:
        await message.answer(WEIGHT_EXCEPTION_TEXT)
        return

    await state.update_data(weight=weight)
    await message.answer("Введите ваш рост (в см):")
    await state.set_state(Form.height)


@router.message(Form.height)
async def process_height(message: Message, state: FSMContext):
    try:
        height = int(message.text)
    except ValueError:
        await message.answer(HEIGHT_EXCEPTION_TEXT)
        return
    
    if height <= 0:
        await message.answer(HEIGHT_EXCEPTION_TEXT)
        return

    await state.update_data(height=height)
    await message.answer("Введите ваш возраст:")
    await state.set_state(Form.age)


@router.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
    except ValueError:
        await message.answer(AGE_EXCEPTION_TEXT)
        return
    
    if age <= 0:
        await message.answer(AGE_EXCEPTION_TEXT)
        return

    await state.update_data(age=age)
    await message.answer("Сколько минут активности у вас в день?")
    await state.set_state(Form.activity)


@router.message(Form.activity)
async def process_activity(message: Message, state: FSMContext):
    try:
        activity = int(message.text)
    except ValueError:
        await message.answer(ACTIVITY_EXCEPTION_TEXT)
        return
    
    if activity < 0:
        await message.answer(ACTIVITY_EXCEPTION_TEXT)
        return

    await state.update_data(activity=activity)
    await message.answer("В каком городе вы находитесь:")
    await state.set_state(Form.city)


@router.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    try:
        data = await clients.get_weather(message.text)
        temp = data.get("main").get("temp")
    except Exception as e:
        await message.answer(f"Invalid city name: [{message.text}], error: {e}")
        return

    data = await state.get_data()
    weight = data.get("weight")
    height = data.get("height")
    age = data.get("age")
    activity = data.get("activity")

    water_norm = weight * 30 + 500 * (activity // 30)
    if temp > 25:
        water_norm += 1000

    calories_norm = 10 * weight + 6.25 * height - 5 * age + (activity // 60) * 200

    users_storage.set(message.from_user.id, UserData(
        weight=weight,
        height=height,
        age=age,
        activity=activity,
        city=message.text,
        water_norm=water_norm,
        calories_norm=calories_norm
    ))

    await message.answer(f"Ваши данные сохранены")
    await state.clear()


@router.message(Command("log_water"))
async def log_water(message: Message):
    if not users_storage.contains(message.from_user.id):
        await message.answer("Вы еще не заполнили данные профиля. Для этого сначала выполните команду /set_profile")
        return

    try:
        data = message.text.strip().split(" ")
        if len(data) != 2:
            await message.answer("Невалидное число аргументов в сообщении - необходимо указать одно число - количество выпитой воды в миллилитрах")
            return
        amount = int(data[1])
    except ValueError:
        await message.answer("Невалиданый объем воды - необходимо указать число выпитой воды в миллилитрах")
        return
    
    user_data = users_storage.get(message.from_user.id)
    user_data.current_water += amount
    users_storage.set(message.from_user.id, user_data)

    if user_data.current_water < user_data.water_norm:
        await message.answer(f"Данные сохранены\nДо выполнения нормы осталось: {user_data.water_norm - user_data.current_water} миллилитров")
    elif user_data.current_water == user_data.water_norm:
        await message.answer(f"Данные сохранены\nНорма выполнена!")
    else:
        await message.answer(f"Данные сохранены\nНорма перевыполенн на: {user_data.current_water - user_data.water_norm} миллилитров")


@router.message(Command("log_food"))
async def log_food(message: Message, state: FSMContext):
    if not users_storage.contains(message.from_user.id):
        await message.answer("Вы еще не заполнили данные профиля. Для этого сначала выполните команду /set_profile")
        return

    data = message.text.strip().split(" ", maxsplit=1)
    if len(data) < 2:
        await message.answer("Невалидное число аргументов в сообщении - необходимо указать название продукта")
        return

    info = await clients.get_food_info(data[1])

    await message.answer(f"{info['info']}\nСколько грамм Вы съели?")
    await state.update_data(calories=info['calories'])
    await state.set_state(FoodForm.amount)


@router.message(FoodForm.amount)
async def process_food_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
    except ValueError:
        await message.answer(FOOD_AMOUNT_EXCEPTION_TEXT)
        return
    
    if amount <= 0:
        await message.answer(FOOD_AMOUNT_EXCEPTION_TEXT)
        return

    data = await state.get_data()
    calories = data.get("calories")

    user_data = users_storage.get(message.from_user.id)
    user_data.current_calories += amount * calories / 100
    users_storage.set(message.from_user.id, user_data)

    await message.answer(f"Записано {amount * calories / 100} ккал")
    await state.clear()


@router.message(Command("log_workout"))
async def log_workout(message: Message):
    if not users_storage.contains(message.from_user.id):
        await message.answer("Вы еще не заполнили данные профиля. Для этого сначала выполните команду /set_profile")
        return

    parts = message.text.strip().split()
    if len(parts) != 3 or not parts[2].isdigit():
        await message.answer("Используйте формат: log_workout <тип тренировки> <количество в минутах>")
        return
    
    workout_minutes = int(parts[2])
    workout_calories = 100

    if parts[1].lower() in CALORIES_PER_SPORT:
        workout_calories = CALORIES_PER_SPORT[parts[1].lower()]
    else:
        await message.answer(f"Спорт {parts[1]} мне неизвестен, поэтому использую среднее занчение потраченных ккал за 30 минут - 100")
    
    calories_burned = workout_calories * workout_minutes / 30
    user_data = users_storage.get(message.from_user.id)
    user_data.calories_burned += calories_burned
    users_storage.set(message.from_user.id, user_data)

    await message.answer(f"Вы сожгли {calories_burned} ккал за {workout_minutes} минут тренировки: {parts[1]}, выпейте {calories_burned * 3/4} мл воды.")
    

@router.message(Command("check_progress"))
async def check_progress(message: Message):
    user_data = users_storage.get(message.from_user.id)
    if user_data is None:
        await message.reply("Вы еще не указали ваши данные. Введите /set_profile для заполнения")
        return
    
    if user_data.water_norm > user_data.current_water:
        water_need = f"{user_data.water_norm - user_data.current_water} мл"
    else:
        water_need = "Норма выполнена!\n"
    
    await message.reply(f"📊 Прогресс:\n\tВода:\n\t - Выпито: {user_data.current_water} мл из {user_data.water_norm} мл.\n"
                        +f"\t - Осталось: {water_need}\n\n\tКалории:\n\t - Потреблено: {user_data.current_calories} ккал из "
                        +f"{user_data.calories_norm} ккал\n\t - Сожжено: {user_data.calories_burned} ккал\n\t"
                        +f" - Баланс: {user_data.current_calories - user_data.calories_burned} ккал")
 

@router.message(Command("get_profile_data"))
async def get_profile_data(message: Message):
    user_data = users_storage.get(message.from_user.id)
    if user_data is None:
        await message.reply("Вы еще не указали ваши данные. Введите /set_profile для заполнения")
        return
    await message.reply(f"Ваши текущие данные:\nРост: {user_data.height}см\nВес: {user_data.weight}кг\n"
                        + f"Возраст: {user_data.age}\nКоличество минут активности в день: {user_data.activity}\n"
                        + f"Город: {user_data.city}")


def setup_handlers(dp):
    dp.include_router(router)