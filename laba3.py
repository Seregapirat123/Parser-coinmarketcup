import requests
from bs4 import BeautifulSoup
import re
import sqlite3

# 1. Функции
#Очистка от тегов
def clean_html(raw_html):
    """Удаляет HTML-теги из строки."""
    return BeautifulSoup(raw_html, "html.parser").get_text()

#Форматируем убираем лишнгее
def format_description(description):
    """Форматирует описание занятия."""
    cleaned = clean_html(description)
    cleaned = re.sub(r'(\b[А-Яа-я])\s+(?=[А-Яа-я])', r'\1', cleaned)
    cleaned = re.sub(r'(\d{2}:\d{2})-(\d{2}:\d{2})', r'\1-\2 ', cleaned)
    cleaned = re.sub(r'(?<=[а-я]),(?=[А-Я])', r', ', cleaned)
    cleaned = re.sub(r'(Лабораторные работы|Лекции|Практические занятия)', r' \1 ', cleaned)
    cleaned = re.sub(r'(\d-ИАИТ-\d{2})(ИАИТ-\d{3})', r'\1 \2', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()
#Извлекает имена преподавателей Фио и Фамилия.И.О
def extract_teachers(description):
    """Извлекает имена преподавателей"""
    teacher_matches = re.findall(r'([А-Я][а-я]+)\s([А-Я])\.([А-Я])\.', description)
    teachers = []
    
    for last_name, first_initial, patronymic_initial in teacher_matches:
        # Сохраняем оба варианта
        teachers.append(f"{last_name} {first_initial}.{patronymic_initial}.")  
        teachers.append(f"{last_name} {first_initial} {patronymic_initial}")   
    
    return list(set(teachers))  # Убираем дубли

#Функции работы с базой данных
def init_db():
    """Инициализирует базу данных."""
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        start_datetime TEXT NOT NULL,
        end_datetime TEXT NOT NULL,
        description TEXT NOT NULL,
        date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        type_lesson TEXT NOT NULL
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lesson_id INTEGER NOT NULL,
        teacher_name TEXT NOT NULL,
        FOREIGN KEY (lesson_id) REFERENCES lessons (id)
    )''')
    conn.commit()
    conn.close()
#Сохраняем нашу бд
def save_to_db(lessons_data):
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM teachers')
    cursor.execute('DELETE FROM lessons')
    
    for lesson in lessons_data:
        description = format_description(lesson['description'])
        type_lesson = "Не указано"
        if "Лекции" in description:
            type_lesson = "Лекции"
        elif "Лабораторные работы" in description:
            type_lesson = "Лабораторные работы"
        elif "Практические занятия" in description:
            type_lesson = "Практические занятия"
        
        date = lesson['start'].split("T")[0]
        start_time = lesson['start'].split('T')[1][:5]
        end_time = lesson['end'].split('T')[1][:5]
        
        cursor.execute('''
        INSERT INTO lessons (title, start_datetime, end_datetime, description, date, start_time, end_time, type_lesson)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (lesson['title'], lesson['start'], lesson['end'], description, date, start_time, end_time, type_lesson))
        
        lesson_id = cursor.lastrowid
        for teacher in extract_teachers(description):
            cursor.execute('''
            INSERT INTO teachers (lesson_id, teacher_name)
            VALUES (?, ?)
            ''', (lesson_id, teacher))
    
    conn.commit()
    conn.close()

#Функции получения данных из БД
def get_schedule_by_date(date):
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT title, start_time, end_time, type_lesson 
    FROM lessons 
    WHERE date = ?
    ORDER BY start_time
    ''', (date,))
    lessons = cursor.fetchall()
    conn.close()
    
    if lessons:
        for lesson in lessons:
            print(f"{date} - {lesson[0]:<50} {lesson[1]:<5} - {lesson[2]:<5}   Тип: {lesson[3]}")
    else:
        print("Расписание на этот день не найдено.")

def get_subject_details(subject):
    """Получает подробности о предмете."""
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT date, title, start_time, end_time, description 
    FROM lessons 
    WHERE title LIKE ? 
    ORDER BY date, start_time
    ''', (f'%{subject}%',))
    lessons = cursor.fetchall()
    conn.close()
    
    if lessons:
        for lesson in lessons:
            print(f"{lesson[0]} - {lesson[1]:<50} {lesson[2]:<5} - {lesson[3]:<5}")
            print(f"Описание:\n{lesson[4]}\n")
    else:
        print("Предмет не найден.")

def get_teacher_subjects(teacher):
    """Получает предметы преподавателя, ища прямо в описании (как в оригинале)"""
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    # Занятия, где в описании есть указанный преподаватель
    cursor.execute('''
    SELECT date, title, start_time, end_time, description, type_lesson 
    FROM lessons 
    WHERE description LIKE ?
    ORDER BY date, start_time
    ''', (f'%{teacher}%',))
    
    lessons = cursor.fetchall()
    conn.close()
    
    if lessons:
        print(f"\nНайдено {len(lessons)} занятий для преподавателя {teacher}:")
        for lesson in lessons:
            # Определяем тип занятия
            desc = lesson[4]
            type_lesson = "Не указано"
            if "Лекции" in desc: type_lesson = "Лекции"
            elif "Лабораторные работы" in desc: type_lesson = "Лабораторные работы"
            elif "Практические занятия" in desc: type_lesson = "Практические занятия"
            
            print(f"{lesson[0]} - {lesson[1]:<50} {lesson[2]:<5}-{lesson[3]:<5}  Тип: {type_lesson}")
    else:
        print("Преподаватель не найден.")
        
#Основной код
headers = {
    "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

session = requests.Session()
session.headers.update(headers)

# Ссылочка
url_point = "https://lk.samgtu.ru/distancelearning"
r = session.get(url_point)

# парсим чтобы получить токен
soup = BeautifulSoup(r.content, "html.parser")
csrf = soup.find("input", {"name": "_csrf"})["value"]

# URL для авторизации
url_auth = "https://lk.samgtu.ru/site/login"


payload = {
    "_csrf": csrf,
    "LoginForm[username]": "golovachev.v.a",
    "LoginForm[password]": "220598arT",
    "LoginForm[rememberMe]": "1"
}

# Отправляем POST-запрос для авторизации
r = session.post(url_auth, data=payload)

# Получаем куки после авторизации
cookies = session.cookies.get_dict()

# Формируем словарь куков
cookies = {
    '_identity': cookies['_identity'],
    'PHPSESSID': cookies['PHPSESSID'],
    '_csrf': cookies['_csrf'],
}

# Хедеры для запроса к API
headers = {
    'Accept': '*/*',
    'Accept-Language': 'ru,en;q=0.9',
    'Connection': 'keep-alive',
    'Referer': 'https://lk.samgtu.ru/distancelearning/distancelearning/index',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 YaBrowser/25.2.0.0 Safari/537.36',
    'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "YaBrowser";v="25.2", "Yowser";v="2.5"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}


params = {
    'start': '2025-01-27T00:00:00+04:00',
    'end': '2025-06-10T00:00:00+04:00',
}

# Отправляем GET к API
response = requests.get('https://lk.samgtu.ru/api/common/distancelearning', 
                       params=params, 
                       cookies=cookies, 
                       headers=headers)

# Сохранение данных
init_db()
save_to_db(response.json())

# Менюшка
print("Выберите действие:\n1 - Вводим день - получаем расписание\n2 - Вводим предмет - получаем подробности\n3 - Вводим преподавателя - получаем предметы\n0 - Выход\n")
while True:
    try:
        choice = int(input("Введите номер действия: "))
        if choice == 1:
            date = input("Введите интересующий день в формате год-месяц-число (Пример: 2025-02-26)\n")
            get_schedule_by_date(date)
        elif choice == 2:
            subject = input("Введите название дисциплины (Пример: Технологии и методы программирования)\n")
            get_subject_details(subject)
        elif choice == 3:
            teacher = input("Введите имя преподавателя (Пример: Панфилова Ирина Евгеньевна)\n")
            get_teacher_subjects(teacher)
        elif choice == 0:
            print("Выход из программы.")
            break
        else:
            print("Неверный выбор. Пожалуйста, выберите 1, 2, 3 или 0 для выхода.")
    except ValueError:
        print("Пожалуйста, введите число.")