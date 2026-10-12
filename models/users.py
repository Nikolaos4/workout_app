"""Класс User и функции работы с пользователями."""

from datetime import date
from typing import Optional


class User:
    """Пользователь сервиса учета тренировок."""

    def __init__(self, user_id: int, name: str, registered_at: date) -> None:
        """Создать объект пользователя."""
        self.id = user_id
        self.name = name
        self.registered_at = registered_at

    @classmethod
    def from_data(cls, data: dict) -> "User":
        """Создать пользователя из данных JSON (id, name, registered_at)."""
        return cls(
            user_id=data["id"],
            name=data["name"],
            registered_at=date.fromisoformat(data["registered_at"]),
        )

    def __str__(self) -> str:
        """Вернуть строковое представление пользователя."""
        return f"{self.name} (регистрация: {self.registered_at:%d.%m.%Y})"


def add_user(
    users: list[User], name: str, registered_at: Optional[date] = None
) -> None:
    """Создать пользователя и добавить его в коллекцию.

    Если дата регистрации не указана, берётся сегодняшняя.
    """
    name = name.strip()
    if not name:
        raise ValueError("Имя пользователя не может быть пустым")
    new_id = max((user.id for user in users), default=0) + 1
    users.append(User(new_id, name, registered_at or date.today()))


def find_user(users: list[User], query: str) -> list[User]:
    """Найти пользователей, в имени которых встречается подстрока query."""
    query_lower = query.strip().lower()
    return [user for user in users if query_lower in user.name.lower()]


def find_user_by_id(users: list[User], user_id: int) -> Optional[User]:
    """Найти пользователя по id или вернуть None."""
    for user in users:
        if user.id == user_id:
            return user
    return None


def show_users(users: list[User]) -> None:
    """Вывести список пользователей."""
    if not users:
        print("Пользователи не найдены")
        return
    for user in users:
        print(f"{user.id}. {user}")
