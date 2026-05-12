import json
from datetime import datetime
from abc import ABC, abstractmethod
import requests
import os
from typing import List, Optional, Dict


# ====================== МОДЕЛЬ ЗАПИСИ ======================
class Entry:
    def __init__(self, content: str, mood: str = "нейтрально", city: str = None, weather: str = None):
        self._date = datetime.now()
        self._content = content.strip()
        self._mood = mood
        self._city = city
        self._weather = weather

    @property
    def date(self):
        return self._date

    @property
    def content(self):
        return self._content

    @property
    def mood(self):
        return self._mood

    @property
    def weather(self):
        return self._weather

    def to_dict(self) -> Dict:
        return {
            "date": self._date.isoformat(),
            "content": self._content,
            "mood": self._mood,
            "city": self._city,
            "weather": self._weather
        }

    @classmethod
    def from_dict(cls, data: Dict):
        entry = cls(
            data["content"],
            data.get("mood", "нейтрально"),
            data.get("city"),
            data.get("weather")
        )
        entry._date = datetime.fromisoformat(data["date"])
        return entry

    def display(self) -> str:
        weather_info = f" | {self._city}: {self._weather}" if self._weather else ""
        return (f"Дата: {self._date.strftime('%d.%m.%Y %H:%M')}\n"
                f"Настроение: {self._mood}{weather_info}\n"
                f"{'-' * 55}\n{self._content}\n")


# ====================== ХРАНИЛИЩЕ ======================
class Storage(ABC):
    @abstractmethod
    def save(self, entries: List[Entry]):
        pass

    @abstractmethod
    def load(self) -> List[Entry]:
        pass


class JSONStorage(Storage):
    def __init__(self, filename: str = "pixel_diary.json"):
        self.filename = filename

    def save(self, entries: List[Entry]):
        data = [entry.to_dict() for entry in entries]
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self) -> List[Entry]:
        if not os.path.exists(self.filename):
            return []
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [Entry.from_dict(item) for item in data]
        except Exception:
            return []


# ====================== API ПОГОДЫ ======================
class WeatherAPIClient:
    def __init__(self, api_key: str):
        self._api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    def get_weather(self, city: str) -> Optional[str]:
        if not self._api_key or not city or city.lower() in ["", "нет", "skip", "пропустить"]:
            return None
        try:
            params = {
                "q": city,
                "appid": self._api_key,
                "units": "metric",
                "lang": "ru"
            }
            response = requests.get(self.base_url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                desc = data['weather'][0]['description']
                temp = data['main']['temp']
                return f"{desc.capitalize()}, {temp:.1f}°C"
            return None
        except Exception:
            return None


# ====================== ПИКСЕЛЬНЫЙ РЕНДЕРЕР ======================
class Renderer(ABC):
    @abstractmethod
    def render_header(self, title: str):
        pass

    @abstractmethod
    def render_menu(self, options: List[str]):
        pass

    @abstractmethod
    def render_entries(self, entries: List[Entry]):
        pass


class PixelRenderer(Renderer):
    def __init__(self):
        self.width = 62

    def print_box_top(self):
        print("╔" + "═" * (self.width - 2) + "╗")

    def print_box_bottom(self):
        print("╚" + "═" * (self.width - 2) + "╝")

    def print_box_line(self, text: str = ""):
        line = f"║ {text.ljust(self.width - 4)} ║"
        print(line)

    def render_header(self, title: str):
        print("\n" + "█" * self.width)
        self.print_box_top()
        centered = title.center(self.width - 4)
        self.print_box_line(centered)
        self.print_box_bottom()
        print("█" * self.width + "\n")

    def render_menu(self, options: List[str]):
        self.print_box_top()
        self.print_box_line("ГЛАВНОЕ МЕНЮ")
        self.print_box_bottom()
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        print()

    def render_entries(self, entries: List[Entry]):
        if not entries:
            self.print_box_top()
            self.print_box_line("Дневник пока пуст...")
            self.print_box_bottom()
            return

        self.print_box_top()
        self.print_box_line(f"Записей в дневнике: {len(entries)}")
        self.print_box_bottom()

        for idx, entry in enumerate(entries[-5:], 1):
            print(f"\n{idx}. " + entry.display())


# ====================== ОСНОВНОЙ КЛАСС ДНЕВНИКА ======================
class Diary:
    def __init__(self, storage: Storage, renderer: Renderer, weather_client: Optional[WeatherAPIClient] = None):
        self._entries: List[Entry] = []
        self.storage = storage
        self.renderer = renderer
        self.weather_client = weather_client
        self._load_entries()

    def _load_entries(self):
        self._entries = self.storage.load()

    def add_entry(self):
        self.renderer.render_header("НОВАЯ ЗАПИСЬ")
        content = input("Введите текст записи:\n> ")
        if not content.strip():
            print("Запись не может быть пустой!")
            return

        mood = input("Ваше настроение (или Enter для нейтрально): ") or "нейтрально"
        city = input("Город для погоды (или Enter чтобы пропустить): ").strip()

        weather = None
        if city and self.weather_client:
            print("Получаем данные о погоде...")
            weather = self.weather_client.get_weather(city)

        entry = Entry(content, mood, city if city else None, weather)
        self._entries.append(entry)
        self.storage.save(self._entries)
        print("Запись успешно добавлена!")

    def view_entries(self):
        self.renderer.render_header("МОЙ ПИКСЕЛЬНЫЙ ДНЕВНИК")
        self.renderer.render_entries(self._entries)

    def search_entries(self):
        self.renderer.render_header("ПОИСК ПО ДНЕВНИКУ")
        query = input("Что ищем? ").strip().lower()
        if not query:
            return
        results = [e for e in self._entries if query in e.content.lower()]
        self.renderer.render_header(f"Найдено по запросу: {query}")
        self.renderer.render_entries(results)


# ====================== ЗАПУСК ======================
def main():
    print("Запуск Пиксельного Дневника...\n")

    api_key = input("Введите ваш OpenWeatherMap API-ключ (или Enter, чтобы работать без погоды):\n> ").strip()
    weather_client = WeatherAPIClient(api_key) if api_key else None

    storage = JSONStorage()
    renderer = PixelRenderer()
    diary = Diary(storage, renderer, weather_client)

    menu_options = [
        "Добавить новую запись",
        "Просмотреть записи",
        "Поиск по записям",
        "Выход"
    ]

    while True:
        renderer.render_header("ПИКСЕЛЬНЫЙ ДНЕВНИК")
        renderer.render_menu(menu_options)

        choice = input("Выберите действие (1-4): ").strip()

        if choice == "1":
            diary.add_entry()
        elif choice == "2":
            diary.view_entries()
        elif choice == "3":
            diary.search_entries()
        elif choice == "4":
            print("До свидания! Все записи сохранены.")
            break
        else:
            print("Неверный выбор!")

        input("\nНажмите Enter для продолжения...")


if __name__ == "__main__":
    main()