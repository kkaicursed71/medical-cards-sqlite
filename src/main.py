"""
Консольное приложение: Учёт медицинских карт пациентов.
Запуск из корня проекта: python src/main.py
"""

from datetime import datetime
import database


def print_menu():
    """Выводит главное текстовое меню приложения."""
    print("\n" + "=" * 56)
    print("        УЧЁТ МЕДИЦИНСКИХ КАРТ ПАЦИЕНТОВ (SQLite)")
    print("=" * 56)
    print("  1. Показать все медицинские карты")
    print("  2. Добавить новую медицинскую карту")
    print("  3. Найти пациента (ФИО / карта / полис / диагноз)")
    print("  4. Редактировать диагноз или телефон")
    print("  5. Удалить медицинскую карту")
    print("  0. Выход из программы")
    print("-" * 56)


def print_patients(patients):
    """Красиво выводит список пациентов в консоль."""
    if not patients:
        print("\n[База данных пуста или по запросу ничего не найдено]")
        return

    print(f"\nНайдено записей: {len(patients)}")
    print("-" * 78)
    for row in patients:
        print(f"ID: {row['id']} | Карта: {row['card_number']} | Создана: {row['created_at']}")
        print(f"  ФИО:           {row['full_name']}")
        print(f"  Дата рождения: {row['birth_date']} | Полис ОМС: {row['policy_number']}")
        print(f"  Диагноз:       {row['diagnosis']}")
        print(f"  Телефон:       {row['phone'] or 'не указан'}")
        print("-" * 78)


def input_non_empty(prompt):
    """Запрашивает у пользователя непустую строку."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Поле не может быть пустым. Попробуйте ещё раз.")


def input_birth_date():
    """Запрашивает дату рождения и проверяет формат ДД.ММ.ГГГГ."""
    while True:
        value = input("Дата рождения (ДД.ММ.ГГГГ): ").strip()
        try:
            datetime.strptime(value, "%d.%m.%Y")
            return value
        except ValueError:
            print("Неверный формат даты. Пример: 14.03.1998")


def input_policy_number():
    """Запрашивает номер полиса ОМС (16 цифр)."""
    while True:
        value = input("Номер полиса ОМС (16 цифр): ").strip().replace(" ", "")
        if value.isdigit() and len(value) == 16:
            return value
        print("Полис ОМС должен состоять ровно из 16 цифр.")


def handle_add_patient():
    """Диалог добавления новой медицинской карты."""
    print("\n--- Добавление новой медицинской карты ---")
    card_number = input_non_empty("Номер карты (например, МК-2026-006): ")
    full_name = input_non_empty("ФИО пациента: ")
    birth_date = input_birth_date()
    policy_number = input_policy_number()
    diagnosis = input_non_empty("Диагноз / причина обращения: ")
    phone = input("Контактный телефон (можно оставить пустым): ").strip()

    ok, message = database.add_patient(
        card_number, full_name, birth_date, policy_number, diagnosis, phone
    )
    print(f"\n{message}")


def handle_search():
    """Диалог поиска медицинских карт."""
    print("\n--- Поиск пациента ---")
    query = input_non_empty("Введите ФИО, номер карты, полис или диагноз: ")
    results = database.search_patients(query)
    print_patients(results)


def handle_edit():
    """Диалог редактирования диагноза или телефона по ID."""
    print("\n--- Редактирование записи ---")
    raw_id = input("Введите ID пациента для редактирования: ").strip()
    if not raw_id.isdigit():
        print("Ошибка: ID должен быть целым числом.")
        return

    patient = database.get_patient_by_id(int(raw_id))
    if not patient:
        print(f"Пациент с ID {raw_id} не найден.")
        return

    print(f"Выбран пациент: {patient['full_name']} (карта {patient['card_number']})")
    print("Что изменить? 1 — Диагноз, 2 — Телефон")
    field_choice = input("Ваш выбор (1/2): ").strip()

    if field_choice == "1":
        new_val = input_non_empty("Новый диагноз: ")
        ok, msg = database.update_patient_field(patient["id"], "diagnosis", new_val)
        print(f"\n{msg}")
    elif field_choice == "2":
        new_val = input("Новый телефон: ").strip()
        ok, msg = database.update_patient_field(patient["id"], "phone", new_val)
        print(f"\n{msg}")
    else:
        print("Редактирование отменено: неизвестный пункт.")


def handle_delete():
    """Диалог удаления медицинской карты с подтверждением."""
    print("\n--- Удаление медицинской карты ---")
    raw_id = input("Введите ID пациента для удаления: ").strip()
    if not raw_id.isdigit():
        print("Ошибка: ID должен быть целым числом.")
        return

    patient = database.get_patient_by_id(int(raw_id))
    if not patient:
        print(f"Пациент с ID {raw_id} не найден.")
        return

    print(f"Вы действительно хотите удалить карту {patient['card_number']} ({patient['full_name']})?")
    confirm = input("Подтвердите удаление (д/н): ").strip().lower()
    if confirm in ("д", "да", "y", "yes"):
        ok, msg = database.delete_patient(patient["id"])
        print(f"\n{msg}")
    else:
        print("Удаление отменено.")


def main():
    """Точка входа: инициализация базы и главный цикл меню."""
    database.init_db()
    print("База данных medical_cards.db успешно подключена.")

    while True:
        print_menu()
        choice = input("Выберите пункт меню (0-5): ").strip()

        if choice == "1":
            patients = database.get_all_patients()
            print_patients(patients)
        elif choice == "2":
            handle_add_patient()
        elif choice == "3":
            handle_search()
        elif choice == "4":
            handle_edit()
        elif choice == "5":
            handle_delete()
        elif choice == "0":
            print("\nРабота программы завершена. До свидания!")
            break
        else:
            print("\nНеверный пункт меню. Введите цифру от 0 до 5.")


if __name__ == "__main__":
    main()
