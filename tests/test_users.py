"""Тесты класса User и функций работы с пользователями."""

from datetime import date

import pytest

from models import User
from models.users import add_user, find_user, find_user_by_id


def test_user_creation():
    user = User(1, "Иван Петров", date(2026, 9, 7))
    assert user.id == 1
    assert user.name == "Иван Петров"
    assert user.registered_at == date(2026, 9, 7)


def test_user_str():
    user = User(1, "Иван Петров", date(2026, 9, 7))
    assert str(user) == "Иван Петров (регистрация: 07.09.2026)"


def test_user_from_data():
    user = User.from_data(
        {"id": 2, "name": "Анна Смирнова", "registered_at": "2026-09-10"}
    )
    assert isinstance(user, User)
    assert user.id == 2
    assert user.registered_at == date(2026, 9, 10)


def test_user_from_data_missing_key_raises():
    with pytest.raises(KeyError):
        User.from_data({"id": 1, "name": "Без даты"})


def test_add_user_adds_object_to_collection():
    users = []
    add_user(users, "Иван Петров", date(2026, 9, 7))
    assert len(users) == 1
    assert isinstance(users[0], User)
    assert users[0].id == 1


def test_add_user_default_registration_date_is_today():
    users = []
    add_user(users, "Иван Петров")
    assert users[0].registered_at == date.today()


def test_add_user_empty_name_raises():
    with pytest.raises(ValueError):
        add_user([], "   ")


def test_find_user_and_find_user_by_id():
    users = []
    add_user(users, "Иван Петров")
    add_user(users, "Анна Смирнова")
    assert [u.name for u in find_user(users, "анна")] == ["Анна Смирнова"]
    assert find_user_by_id(users, 1) is users[0]
    assert find_user_by_id(users, 99) is None
