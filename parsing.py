import sys
import subprocess
import time

# 1. Проверяем/устанавливаем библиотеку автоматизации
try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
    from bs4 import BeautifulSoup

import requests
import pandas as pd

print("Библиотеки успешно импортированы!")


# 2. Функция для скачивания страницы
def basic_parser(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return BeautifulSoup(response.content, 'html.parser')
        else:
            print(f"Ошибка при скачивании страницы: {response.status_code}")
            return None
    except Exception as e:
        print(f"Ошибка сети: {e}")
        return None


# 3. Функция точного сбора данных с Proffish.ru
def extract_products(soup_obj):
    items = []
    
    # Находим блоки товаров по CSS-селектору класса '.product_holder'
    products = soup_obj.select('div.product_holder')
    
    for product in products:
        try:
            # Находим название товара (ссылка внутри блока с классом .name)
            title_element = product.select_one('div.name a')
            title = title_element.text.strip() if title_element else "Без названия"
            
            # Находим ссылку на товар
            href = title_element['href'] if title_element else ""
            full_url = 'https://proffish.ru' + href if href and not href.startswith('http') else href
            
            # Находим цену товара (блок с классом .price)
            price_element = product.select_one('div.price')
            price = price_element.text.strip() if price_element else "Цена не указана"
            
            # Формируем словарь, если нашли название
            if title != "Без названия":
                item = {
                    'title': title,
                    'price': price,
                    'url': full_url
                }
                items.append(item)
        except Exception:
            continue
            
    return items



# =====================================================================
# ВТОРОЙ ЭТАП ДИАГНОСТИКИ: АНАЛИЗ ССЫЛОК И КЛАССОВ
# =====================================================================

target_url = 'https://proffish.ru'

print(f"Анализируем внутреннюю структуру страницы: {target_url}...\n")
html_soup = basic_parser(target_url)

if html_soup:
    # 1. Посмотрим на первые 20 ссылок каталога, чтобы понять их структуру
    print("--- ПРИМЕРЫ ССЫЛОК НА СТРАНИЦЕ ---")
    all_links = html_soup.find_all('a', href=True)
    count = 0
    for link in all_links:
        href = link['href']
        text = link.text.strip()
        # Пропускаем ссылки на корзину, контакты, соцсети и пустые ссылки
        if any(x in href for x in ['javascript', 'cart', 'contact', 'about', 'delivery', 'telefoni']):
            continue
        if text and len(text) > 10:  # Ищем длинные текстовые ссылки (похожие на названия товаров)
            print(f"Текст: {text[:40]}... -> Ссылка: {href}")
            count += 1
            if count >= 10:
                break
                
    # 2. Посмотрим, какие крупные блоки (div) с классами вообще есть на странице
    print("\n--- СПИСОК КЛАССОВ ДЛЯ КАРТОЧЕК ---")
    div_classes = set()
    for div in html_soup.find_all('div', class_=True):
        for cls in div['class']:
            if any(keyword in cls.lower() for keyword in ['prod', 'item', 'catalog', 'card', 'holder', 'good']):
                div_classes.add(cls)
    print("Найденные классы блоков:", list(div_classes))

else:
    print("Не удалось загрузить данные.")
