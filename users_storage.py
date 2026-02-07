from threading import Lock

class UserData:
    def __init__(
        self,
        weight: int,
        height: int,
        age: int,
        activity: int,
        city: str,
        water_norm: int,
        calories_norm: int
    ):
        self.weight = weight
        self.height = height
        self.age = age
        self.activity = activity
        self.city = city
        self.water_norm = water_norm
        self.calories_norm = calories_norm
        self.current_water = 0
        self.current_calories = 0
        self.calories_burned = 0


class UsersStorage:
    def __init__(self):
        self._dict = {}
        self._lock = Lock()
    
    def get(self, key):
        with self._lock:
            return self._dict.get(key)
    
    def set(self, key: int, value: UserData):
        with self._lock:
            self._dict[key] = value
    
    def delete(self, key):
        with self._lock:
            del self._dict[key]
    
    def contains(self, key):
        with self._lock:
            return key in self._dict

