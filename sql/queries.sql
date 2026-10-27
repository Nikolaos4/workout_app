-- ==========================================
-- Сервис учета тренировок: SQL-запросы проекта
-- ==========================================
-- Проверка в SQLite CLI (из корня проекта):
--     sqlite3 data/workout_app.sqlite < sql/queries.sql
-- Значения, которые в веб-приложении приходят параметрами (?, :name),
-- здесь заданы числами и строками для проверки.
-- Запросы 1–4 и 6–13 используются Django-представлениями (указано в
-- комментариях), запросы 5 и 14–16 предназначены для проверки в SQLite CLI.


-- ==========================================
-- ВЫБОРКА СПИСКОВ (SELECT, ORDER BY)
-- ==========================================

-- 1. Список упражнений. exercises/views.py: exercises()
SELECT
    id,
    name,
    muscle_group
FROM exercises
ORDER BY name;

-- 2. Список групп мышц без повторов (для выпадающего списка поиска).
--    exercises/views.py: exercise_search()
SELECT DISTINCT
    muscle_group
FROM exercises
ORDER BY muscle_group;


-- ==========================================
-- ФИЛЬТРАЦИЯ (WHERE)
-- ==========================================

-- 3. Одно упражнение по идентификатору.
--    exercises/views.py: exercise_detail()
SELECT
    id,
    name,
    muscle_group
FROM exercises
WHERE id = 1;

-- 4. Поиск упражнений по группе мышц и части названия.
--    exercises/views.py: exercise_search()
--    '%' || ? || '%' с пустой строкой даёт '%%' — подходит любое название.
SELECT
    id,
    name,
    muscle_group
FROM exercises
WHERE muscle_group = 'Грудь'
  AND name LIKE '%' || 'Жим' || '%'
ORDER BY name;

-- 5. Активные тренировки за период (несколько условий: признак и даты).
--    Условия по признаку и датам в этом виде входят в запрос 6.
SELECT
    id,
    user_id,
    workout_date,
    workout_type
FROM workouts
WHERE is_cancelled = 0
  AND workout_date BETWEEN '2026-09-01' AND '2026-09-30'
ORDER BY workout_date;


-- ==========================================
-- СОЕДИНЕНИЕ ТАБЛИЦ (JOIN)
-- ==========================================

-- 6. Список тренировок с именем пользователя, числом упражнений и тоннажем.
--    Параметры в приложении: :active (1 — только активные), :start, :end.
--    workouts/views.py: workouts()
SELECT
    workouts.id,
    workouts.workout_date,
    workouts.workout_type,
    workouts.duration_min,
    workouts.is_cancelled,
    users.name AS user_name,
    COUNT(workout_exercises.id) AS exercises_count,
    COALESCE(
        SUM(workout_exercises.sets
            * workout_exercises.reps
            * workout_exercises.weight),
        0
    ) AS tonnage
FROM workouts
JOIN users
    ON workouts.user_id = users.id
LEFT JOIN workout_exercises
    ON workout_exercises.workout_id = workouts.id
WHERE (0 = 0 OR workouts.is_cancelled = 0)
  AND workouts.workout_date BETWEEN '0000-01-01' AND '9999-12-31'
GROUP BY workouts.id, users.name
ORDER BY workouts.workout_date DESC, workouts.id DESC;

-- 7. Тренировка по идентификатору вместе с пользователем.
--    workouts/views.py: workout_detail()
SELECT
    workouts.id,
    workouts.workout_date,
    workouts.workout_type,
    workouts.duration_min,
    workouts.is_cancelled,
    users.name AS user_name
FROM workouts
JOIN users
    ON workouts.user_id = users.id
WHERE workouts.id = 1;

-- 8. Упражнения тренировки с подсчётом тоннажа каждой строки.
--    workouts/views.py: workout_detail()
SELECT
    exercises.name AS exercise_name,
    exercises.muscle_group,
    workout_exercises.sets,
    workout_exercises.reps,
    workout_exercises.weight,
    workout_exercises.sets
        * workout_exercises.reps
        * workout_exercises.weight AS tonnage
FROM workout_exercises
JOIN exercises
    ON workout_exercises.exercise_id = exercises.id
WHERE workout_exercises.workout_id = 1
ORDER BY workout_exercises.id;


-- ==========================================
-- АГРЕГАТНЫЕ ФУНКЦИИ (COUNT, AVG, MIN, MAX, SUM)
-- ==========================================

-- 9. Сводка по активным тренировкам: количество, средняя длительность,
--    первая и последняя дата. workouts/views.py: statistics()
SELECT
    COUNT(*) AS workouts_count,
    AVG(duration_min) AS avg_duration,
    MIN(workout_date) AS first_date,
    MAX(workout_date) AS last_date
FROM workouts
WHERE is_cancelled = 0;

-- 10. В скольких активных тренировках выполнялось упражнение.
--     exercises/views.py: exercise_detail()
SELECT
    COUNT(DISTINCT workouts.id) AS used_count
FROM workout_exercises
JOIN workouts
    ON workouts.id = workout_exercises.workout_id
WHERE workout_exercises.exercise_id = 1
  AND workouts.is_cancelled = 0;


-- ==========================================
-- ГРУППИРОВКА (GROUP BY) И ФИЛЬТРАЦИЯ ГРУПП (HAVING)
-- ==========================================

-- 11. Популярность упражнений: в скольких активных тренировках выполнялось
--     каждое. LEFT JOIN сохраняет упражнения, которых не было ни разу.
--     workouts/views.py: statistics()
SELECT
    exercises.name AS exercise_name,
    exercises.muscle_group,
    COUNT(DISTINCT workouts.id) AS workouts_count
FROM exercises
LEFT JOIN workout_exercises
    ON workout_exercises.exercise_id = exercises.id
LEFT JOIN workouts
    ON workouts.id = workout_exercises.workout_id
   AND workouts.is_cancelled = 0
GROUP BY exercises.id, exercises.name, exercises.muscle_group
ORDER BY workouts_count DESC, exercises.name;

-- 12. Суммарный тоннаж по группам мышц (только активные тренировки).
--     workouts/views.py: statistics()
SELECT
    exercises.muscle_group,
    SUM(workout_exercises.sets
        * workout_exercises.reps
        * workout_exercises.weight) AS tonnage
FROM workout_exercises
JOIN exercises
    ON exercises.id = workout_exercises.exercise_id
JOIN workouts
    ON workouts.id = workout_exercises.workout_id
WHERE workouts.is_cancelled = 0
GROUP BY exercises.muscle_group
ORDER BY tonnage DESC;

-- 13. Пользователи, у которых не меньше N активных тренировок (HAVING).
--     WHERE отбирает строки до группировки, HAVING — группы после неё.
--     Параметр в приложении: :min_workouts. workouts/views.py: statistics()
SELECT
    users.name AS user_name,
    COUNT(workouts.id) AS workouts_count,
    SUM(workouts.duration_min) AS total_minutes
FROM users
JOIN workouts
    ON workouts.user_id = users.id
WHERE workouts.is_cancelled = 0
GROUP BY users.id, users.name
HAVING COUNT(workouts.id) >= 1
ORDER BY workouts_count DESC, users.name;


-- ==========================================
-- СЛУЖЕБНЫЕ ЗАПРОСЫ (проверка импорта, постраничный вывод, подзапрос)
-- ==========================================

-- 14. Количество записей в таблицах — сравнивается с JSON-файлами.
SELECT 'users' AS table_name, COUNT(*) AS records FROM users
UNION ALL
SELECT 'exercises', COUNT(*) FROM exercises
UNION ALL
SELECT 'workouts', COUNT(*) FROM workouts
UNION ALL
SELECT 'workout_exercises', COUNT(*) FROM workout_exercises
UNION ALL
SELECT 'results', COUNT(*) FROM results
UNION ALL
SELECT 'result_workouts', COUNT(*) FROM result_workouts;

-- 15. Постраничный вывод тренировок: LIMIT и OFFSET вместе с ORDER BY.
SELECT
    id,
    workout_date,
    workout_type
FROM workouts
ORDER BY workout_date DESC, id DESC
LIMIT 5 OFFSET 0;

-- 16. Упражнения, которые ни разу не выполнялись (подзапрос NOT IN).
SELECT
    id,
    name
FROM exercises
WHERE id NOT IN (
    SELECT exercise_id
    FROM workout_exercises
)
ORDER BY name;
