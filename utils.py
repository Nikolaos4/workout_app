"""Вспомогательные функции безопасного ввода."""

from datetime import date, datetime


def input_int(prompt: str) -> int:
    """Запросить у пользователя целое число, повторяя запрос при ошибке."""
    while True:
        raw = input(prompt)
        try:
            return int(raw)
        except ValueError:
            print("Нужно ввести целое число, попробуйте ещё раз")


def input_date(prompt: str) -> date:
    """Запросить у пользователя дату в формате ДД.ММ.ГГГГ."""
    while True:
        raw = input(prompt)
        try:
            return datetime.strptime(raw, "%d.%m.%Y").date()
        except ValueError:
            print("Некорректный формат даты, используйте ДД.ММ.ГГГГ")
