import os
import io
import json
import requests

from PIL import Image
from dotenv import load_dotenv
from datetime import datetime


# ===================== ENV =====================
load_dotenv()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")


# ===================== ENTRY =====================
class Entry:
    def __init__(self, text, mood):
        self.text = text
        self.mood = mood
        self.date = datetime.now().strftime("%d.%m.%Y %H:%M")

    def show(self):
        print("\n" + "=" * 50)
        print(self.date)
        print("Настроение:", self.mood)
        print("-" * 50)
        print(self.text)
        print("=" * 50)


# ===================== PEXELS =====================
class PexelsArt:
    chars = " .:-=+*#%@"

    def __init__(self):
        self.headers = {
            "Authorization": PEXELS_API_KEY
        }

    def search_image(self, query):
        url = "https://api.pexels.com/v1/search"

        params = {
            "query": query,
            "per_page": 1
        }

        response = requests.get(
            url,
            headers=self.headers,
            params=params
        )

        data = response.json()

        photos = data.get("photos")

        if not photos:
            raise Exception("Картинки не найдены")

        return photos[0]["src"]["medium"]

    def image_to_ascii(self, image_url):
        response = requests.get(image_url)

        image = Image.open(io.BytesIO(response.content))

        image = image.convert("L")

        image = image.resize((60, 30))

        pixels = image.getdata()

        ascii_text = ""

        for i, pixel in enumerate(pixels):
            ascii_text += self.chars[pixel // 25]

            if i % 60 == 0:
                ascii_text += "\n"

        return ascii_text

    def show(self, query):
        try:
            image_url = self.search_image(query)

            ascii_art = self.image_to_ascii(image_url)

            print("\n")
            print("▓" * 60)
            print("PEXELS AESTHETIC:", query)
            print("▓" * 60)
            print(ascii_art)
            print("▓" * 60)

        except Exception as e:
            print("\nОшибка Pexels API:")
            print(e)


# ===================== DIARY =====================
class Diary:
    def __init__(self):
        self.entries = []

        self.art = PexelsArt()

        self.load()

    def add_entry(self):
        text = input("Текст:\n> ")

        mood = input("Настроение:\n> ")

        entry = Entry(text, mood)

        self.entries.append(entry)

        self.save()

        print("Запись сохранена")

    def show_entries(self):
        if not self.entries:
            print("Записей нет")
            return

        for entry in self.entries:
            entry.show()

    def aesthetic(self):
        query = input("Введите aesthetic:\n> ")

        self.art.show(query)

    def save(self):
        data = []

        for entry in self.entries:
            data.append({
                "text": entry.text,
                "mood": entry.mood,
                "date": entry.date
            })

        with open("diary.json", "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def load(self):
        if not os.path.exists("diary.json"):
            return

        with open("diary.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        for item in data:
            entry = Entry(
                item["text"],
                item["mood"]
            )

            entry.date = item["date"]

            self.entries.append(entry)

    def menu(self):
        while True:
            print("\n")
            print("█" * 50)
            print("PIXEL DIARY")
            print("█" * 50)

            print("1. Добавить запись")
            print("2. Показать записи")
            print("3. Pexels aesthetic")
            print("4. Выход")

            choice = input("\nВыбор: ")

            if choice == "1":
                self.add_entry()

            elif choice == "2":
                self.show_entries()

            elif choice == "3":
                self.aesthetic()

            elif choice == "4":
                break

            else:
                print("Ошибка")


# ===================== START =====================
diary = Diary()
diary.menu()
