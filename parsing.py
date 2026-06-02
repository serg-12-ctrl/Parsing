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

# # 1. Быстрая проверка библиотек
try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
    from bs4 import BeautifulSoup

import requests
import pandas as pd

print("Библиотеки успешно инициализированы!")



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


def extract_data(soup):
    items = []
    
    
    products = soup.select('#browsed_products li') or soup.find_all('li', class_='item')
    
    
    if not products:
        products = soup.find_all('a', href=True)

    for product in products:
        try:
            
            if product.name == 'a':
                link_el = product
            else:
                link_el = product.find('a', href=True)
                
            if not link_el:
                continue
                
            href = link_el['href']
            
            
            img_el = link_el.find('img')
            title = ""
            if img_el:
                title = img_el.get('title') or img_el.get('alt') or ""
            
            # Если в картинке пусто, берем текст самой ссылки или её атрибут title
            if not title:
                title = link_el.get('title') or link_el.text.strip()
            
           
            title = title.strip()
            
            
            if 'products/' in href and len(title) > 5:
                
                # Формируем полный URL-адрес карточки товара
                full_url = 'https://proffish.ru' + href if not href.startswith('http') else href
                
                
                price = "Уточняйте цену"
                parent = product.find_parent()
                if parent:
                    parent_text = parent.get_text()
                    for line in parent_text.split('\n'):
                        if 'руб' in line or '₽' in line:
                            price = line.replace('купить', '').replace('−', '').replace('+', '').strip()
                            break
                
                item = {
                    'title': title,
                    'price': price,
                    'url': full_url
                }
                
                # Защита от дубликатов: добавляем товар, только если его еще нет в списке
                if not any(x['url'] == item['url'] for x in items):
                    items.append(item)
                    
        except Exception:
            continue
            
    return items


url_udilischa = 'https://proffish.ru'

print("\n--- СТАРТ ОДИНОЧНОГО СБОРА ДАННЫХ ---")
print(f"Адрес запроса: {url_udilischa}")

# Шаг 1: Скачиваем страницу через ваш базовый парсер
html_soup = basic_parser(url_udilischa)

my_products = None

\
if html_soup:
    print("Страница успешно получена. Начинаем адаптацию списка товаров под вашу функцию...")
    
    # 1. Находим элементы списка товаров из блока browsed_products
    # (Именно те элементы <li>, которые вы нашли в коде страницы)
    list_items = html_soup.select('#browsed_products li')
    
    for li in list_items:
        # Ищем ссылку и картинку внутри текущего <li>
        link_el = li.find('a', href=True)
        img_el = li.find('img') if link_el else None
        
        if link_el and img_el:
            # Извлекаем реальное название из атрибута title картинки
            real_title = img_el.get('title') or img_el.get('alt') or link_el.text.strip()
            
            # Так как в этом блоке цен нет, сгенерируем заглушку "Уточняйте"
            real_price = "Уточняйте"
            
            # --- МАГИЯ ТРАНСФОРМАЦИИ HTML НА ЛЕТУ ---
            # Превращаем текущий элемент <li> в структуру <div class="product-item">,
            # которую так ждет ваша неизменяемая функция extract_data!
            li.name = 'div'
            li['class'] = 'product-item'
            
            # Создаем внутри структуру <h3 class="title">название</h3>
            new_title_tag = html_soup.new_tag('h3', attrs={'class': 'title'})
            new_title_tag.string = real_title
            
            # Создаем внутри структуру <span class="price">цена</span>
            new_price_tag = html_soup.new_tag('span', attrs={'class': 'price'})
            new_price_tag.string = real_price
            
            # Очищаем старое содержимое <li> (картинки и ссылки) и вставляем 
            # новые теги со старыми данными специально для работы extract_data
            li.clear()
            li.append(new_title_tag)
            li.append(new_price_tag)

    print("Разметка успешно перестроена. Передаем измененный HTML в вашу функцию extract_data...")
    # Шаг 2: Передаем трансформированный HTML напрямую в вашу неизмененную функцию
    my_products = extract_data(html_soup)
else:
    print("[ОШИБКА] Не удалось загрузить HTML-код страницы.")

# Шаг 3: Обработка результатов и экспорт в файл (Оставлена без изменений)
if my_products:
    df = pd.DataFrame(my_products)
    df = df.drop_duplicates(subset=['title'])
    
    print(f"\n[УСПЕХ] Сбор окончен! Ваша функция успешно собрала: {len(df)} товаров.")
    print("\nНайденные позиции из созданной таблицы:")
    print(df.head(5))
    
    df.to_csv('proffish_final_data.csv', index=False, encoding='utf-8-sig')
    print("\nТаблица успешно записана в файл: proffish_final_data.csv")
else:
    print("\n[ВНИМАНИЕ] Список пуст. Ваша функция extract_data не смогла найти элементы на этой странице.")


def parse_multiple_pages(base_url, max_pages=5):
    all_data = []
    
    for page in range(1, max_pages + 1):
        url = f"{base_url}?page={page}"
        soup = basic_parser(url)
        
        if soup:
            data = extract_data(soup)
            all_data.extend(data)
            
            # Пауза для соблюдения этических норм
            time.sleep(1)
    
    return all_data


import datetime

import time
import subprocess
import sys
import schedule
# Автоматическая проверка и установка schedule
try:
    import schedule
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "schedule"])
    import schedule
def scheduled_parsing():
    # Проверяем текущий день месяца
    if datetime.datetime.now().day != 2:
        return  # Если сегодня не 2-е число, выходим из функции
        
    print(f"Ровно 2-е число! Запуск планировщика: {datetime.datetime.now()}")
    
    
    target_url = "https://proffish.ru" 
    soup_data = basic_parser(target_url)
    
    if soup_data:
        parsed_items = extract_data(soup_data)
        if parsed_items:
            df = pd.DataFrame(parsed_items)
            df.drop_duplicates(inplace=True)
            df = df[df['title'].str.strip() != '']
            
            output_file = "parsed_products.csv"
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"Данные успешно обновлены в {output_file}")
    


schedule.every().day.at("10:03").do(scheduled_parsing)

print("Планировщик запущен и ожидает 2-го числа...")


while True:
    schedule.run_pending()
    time.sleep(1)


#Контрольные вопросы:
# 1. Какие методы BeautifulSoup используются для поиска элементов?
# Самые популярные и эффективные методы:
# •	find() — ищет первый подходящий элемент. Возвращает объект тега или None.
# •	find_all() — ищет все подходящие элементы. Возвращает список (даже если найден один тег).
# •	select_one() — ищет первый элемент через CSS-селектор (как в CSS/JavaScript: div.class, #id).
# •	select() — ищет все элементы через CSS-селектор 
# •	2. Почему важно использовать User-Agent при парсинге?
# •	Маскировка под браузер: По умолчанию библиотека requests отправляет заголовок python-requests/2.X. Сайты сразу видят робота и блокируют его.
# •	Обход базовой защиты: Установка реального User-Agent (например, Chrome на Windows) показывает серверу, что страницу запрашивает обычный человек.
# •	Защита от капчи: Без корректного заголовка сайт может вместо товаров выдать страницу с капчей или ошибку 403 Forbidden.
# 3. Как обрабатываются исключения при парсинге?
# Исключения обрабатываются с помощью блоков try - except, чтобы одна ошибка не ломала весь скрипт:
# •	Сетевые ошибки: Запросы оборачивают в try на случай падения интернета, недоступности сайта или таймаута (requests.exceptions.RequestException).
# •	Ошибки структуры (DOM): При поиске тегов может вернуться None. Если попытаться взять атрибут у None (например, None['href']), вылетит AttributeError. Для этого элементы проверяют через if element:.
# •	Ошибки цикла: Как в вашем коде, обработка каждого отдельного товара оборачивается в try-except. Если один товар оформлен на сайте криво, скрипт выведет ошибку, не упадет и перейдет к следующему товару.
# 4. Какие существуют способы оптимизации при работе с большими объемами данных?
# •	Использование сессий: requests.Session() вместо обычного requests.get(). Это удерживает TCP-соединение открытым и ускоряет запросы к одному сайту в 2–3 раза.
# •	Парсер lxml: Использование BeautifulSoup(html, 'lxml') вместо 'html.parser'. Библиотека lxml написана на C и работает значительно быстрее.
# •	Многопоточность/Асинхронность: Использование concurrent.futures или библиотеки aiohttp для скачивания сотен страниц одновременно, а не по очереди.
# •	Генераторы и чанки (Chunks): Пакетированная запись в файл. Не копить миллион строк в оперативной памяти, а дописывать в CSV порциями по 1000 штук через df.to_csv(..., mode='a').

