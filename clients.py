import os
import aiohttp

from dotenv import load_dotenv

load_dotenv()

WEATHER_API_TOKEN = os.getenv('WEATHER_API_TOKEN')

async def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_TOKEN}&units=metric"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception(f"Failed to get weather: {response.status}")
            return await response.json()
        

async def get_food_info(product_name):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={product_name}&json=true"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                products = data.get('products', [])
                if products:
                    first_product = products[0]
                    return {
                        'info': f"{first_product.get('product_name', 'Неизвестно')} - {first_product.get('nutriments', {}).get('energy-kcal_100g', 0)} ккал на 100 г",
                        'calories': first_product.get('nutriments', {}).get('energy-kcal_100g', 0)
                    }
                return {
                    'info': "Продукт не найден, будет использовано среднее значение 50 ккал на 100 г",
                    'calories': 50
                }
            print(f"Ошибка при получении информации о продукте {product_name}: {response.status}")
            return {
                'info': "Продукт не найден, будет использовано среднее значение 50 ккал на 100 г",
                'calories': 50
            }

