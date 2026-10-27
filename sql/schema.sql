-- ==========================================
-- Сервис учета тренировок: структура базы данных
-- ==========================================
-- Скрипт можно выполнять повторно: таблицы создаются только если их ещё нет.

-- Пользователи (data/users.json)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    registered_at TEXT NOT NULL            -- дата в формате YYYY-MM-DD
);

-- Справочник упражнений (data/exercises.json)
CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    muscle_group TEXT NOT NULL
);

-- Тренировки (data/workouts.json)
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    workout_date TEXT NOT NULL,            -- дата в формате YYYY-MM-DD
    workout_type TEXT NOT NULL CHECK (workout_type IN ('кардио', 'силовая')),
    duration_min INTEGER NOT NULL DEFAULT 0,
    is_cancelled INTEGER NOT NULL DEFAULT 0 CHECK (is_cancelled IN (0, 1)),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Выполненные упражнения тренировки: список "exercises" внутри записи
-- тренировки в JSON. Таблица связывает workouts и exercises (многие ко многим).
CREATE TABLE IF NOT EXISTS workout_exercises (
    id INTEGER PRIMARY KEY,
    workout_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    sets INTEGER NOT NULL CHECK (sets >= 0),
    reps INTEGER NOT NULL CHECK (reps >= 0),
    weight REAL NOT NULL DEFAULT 0,
    FOREIGN KEY (workout_id) REFERENCES workouts(id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
);

-- Результаты за период (data/results.json)
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    CHECK (period_end >= period_start),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Тренировки, вошедшие в результат: список "workout_ids" в JSON.
CREATE TABLE IF NOT EXISTS result_workouts (
    result_id INTEGER NOT NULL,
    workout_id INTEGER NOT NULL,
    PRIMARY KEY (result_id, workout_id),
    FOREIGN KEY (result_id) REFERENCES results(id),
    FOREIGN KEY (workout_id) REFERENCES workouts(id)
);
