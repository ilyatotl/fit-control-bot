from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    weight = State()
    height = State()
    age = State()
    city = State()
    activity = State()


class FoodForm(StatesGroup):
    calories = State()
    amount = State()
