"""
Модуль database.py — работа с базой данных SQLite для учёта медицинских карт.
Используется только встроенная библиотека Python sqlite3 (установка пакетов не нужна).
"""

import sqlite3
from datetime import datetime

# Имя файла базы данных (создастся автоматически рядом с main.py)
DB_NAME = "medical_cards.db"


def lower_ru(text):
    """Вспомогательная функция для корректного поиска кириллицы без учёта регистра."""
    return text.lower() if isinstance(text, str) else text


def get_connection():
    """Открывает соединение с базой данных SQLite и настраивает доступ по именам столбцов."""
    conn = sqlite3.connect(DB_NAME)
    # Позволяет обращаться к полям записи как к словарю: row["full_name"]
    conn.row_factory = sqlite3.Row
    # Переопределяем LOWER(), чтобы поиск работал для русских букв (Иванов == иванов)
    conn.create_function("LOWER", 1, lower_ru)
    return conn


def init_db():
    """Создаёт таблицу patients, если её ещё нет, и добавляет тестовые записи при первом запуске."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_number TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                birth_date TEXT NOT NULL,
                policy_number TEXT UNIQUE NOT NULL,
                diagnosis TEXT NOT NULL,
                phone TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )

        # Проверяем, пустая ли таблица; если да — добавим 5 учебных примеров для демонстрации
        cursor.execute("SELECT COUNT(*) FROM patients")
        count = cursor.fetchone()[0]
        if count == 0:
            demo_patients = [
                ("МК-2026-001", "Иванов Алексей Сергеевич", "14.03.1988", "7745120983451201", "ОРВИ, острый ринофарингит", "+7 (916) 245-18-90"),
                ("МК-2026-002", "Смирнова Елена Викторовна", "27.09.1995", "7745120983451202", "Вегетососудистая дистония, плановый осмотр", "+7 (925) 412-67-33"),
                ("МК-2026-003", "Кузнецов Дмитрий Андреевич", "05.11.1976", "7745120983451203", "Гипертоническая болезнь I стадии", "+7 (903) 881-04-15"),
                ("МК-2026-004", "Соколова Мария Олеговна", "19.06.2002", "7745120983451204", "Сезонный аллергический ринит", "+7 (985) 309-52-41"),
                ("МК-2026-005", "Морозов Павел Игоревич", "30.01.1991", "7745120983451205", "Остеохондроз грудного отдела позвоночника", "+7 (910) 674-29-08"),
            ]
            now = datetime.now().strftime("%d.%m.%Y %H:%M")
            cursor.executemany(
                """
                INSERT INTO patients
                    (card_number, full_name, birth_date, policy_number, diagnosis, phone, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [(c, fn, bd, p, d, ph, now) for c, fn, bd, p, d, ph in demo_patients],
            )
        conn.commit()


def get_all_patients():
    """Возвращает список всех медицинских карт, отсортированных по ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients ORDER BY id ASC")
        return cursor.fetchall()


def add_patient(card_number, full_name, birth_date, policy_number, diagnosis, phone):
    """
    Добавляет новую медицинскую карту в базу данных.
    Возвращает кортеж (успех: bool, сообщение: str).
    """
    created_at = datetime.now().strftime("%d.%m.%Y %H:%M")
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Используем параметры (?) вместо f-строк для защиты от SQL-инъекций
            cursor.execute(
                """
                INSERT INTO patients
                    (card_number, full_name, birth_date, policy_number, diagnosis, phone, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (card_number, full_name, birth_date, policy_number, diagnosis, phone, created_at),
            )
            conn.commit()
            return True, f"Медицинская карта {card_number} успешно добавлена (ID: {cursor.lastrowid})."
    except sqlite3.IntegrityError:
        return False, "Ошибка: пациент с таким номером карты или полисом ОМС уже существует."


def search_patients(query):
    """Ищет пациентов по ФИО, номеру карты, полису ОМС или диагнозу."""
    pattern = f"%{query.strip()}%"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM patients
            WHERE LOWER(full_name) LIKE LOWER(?)
               OR LOWER(card_number) LIKE LOWER(?)
               OR policy_number LIKE ?
               OR LOWER(diagnosis) LIKE LOWER(?)
            ORDER BY id ASC
            """,
            (pattern, pattern, pattern, pattern),
        )
        return cursor.fetchall()


def get_patient_by_id(patient_id):
    """Возвращает одну запись пациента по его ID или None, если запись не найдена."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
        return cursor.fetchone()


def update_patient_field(patient_id, field_name, new_value):
    """Обновляет диагноз или телефон выбранного пациента."""
    # Разрешаем обновлять только конкретные безопасные столбцы
    allowed_fields = {"diagnosis", "phone"}
    if field_name not in allowed_fields:
        return False, "Недопустимое поле для редактирования."

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE patients SET {field_name} = ? WHERE id = ?",
            (new_value, patient_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return False, f"Запись с ID {patient_id} не найдена."
        return True, f"Запись с ID {patient_id} успешно обновлена."


def delete_patient(patient_id):
    """Удаляет медицинскую карту пациента по ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return False, f"Запись с ID {patient_id} не найдена."
        return True, f"Медицинская карта с ID {patient_id} удалена из базы."
