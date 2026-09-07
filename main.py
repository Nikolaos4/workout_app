from datetime import date

Person = "Николай Аниканов"
terning_date = date(2026, 9, 7)
count_task = int("3")
task_done = 0


def count_task(task_done):
    task1 = "Жим, 3 подхода по 8 раз, 80 кг"
    task_done += 1
    task2 = "Присед, 2 подхода по 10 раз, 100 кг"
    task_done += 1
    task3 = "Молотки, 4 подхода по 12 раз, 20 кг"
    task_done += 1
    return task_done

def trening_result(result):
    if result == True:
        print(f"Тренировка выполнена! Количество сделанных упражнений = {count_task(task_done)}")
    else:
        print("Ты лентяй!!!")

result = True
trening_result(result)



