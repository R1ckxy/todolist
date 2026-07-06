import json
from datetime import datetime, timedelta
from typing import List


class Task:
    WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    def __init__(self, title: str):
        self.title = title
        self.completed = False
        self.scheduled = None
        self.day_of_week = None
        self.created_at = datetime.now().strftime("%d-%m-%Y %H:%M")
        self.completed_at = None

    def set_schedule(self, day: int = None, time: str = None, date: str = None):
        if date:
            self.scheduled = f"{date} {time or '00:00'}"
            self.day_of_week = datetime.strptime(date, "%d-%m-%Y").isoweekday()
        elif day:
            self.day_of_week = day
            days_ahead = day - datetime.now().isoweekday()
            if days_ahead < 0: days_ahead += 7
            self.scheduled = (datetime.now() + timedelta(days=days_ahead)).strftime(f"%d-%m-%Y {time or '00:00'}")

    def to_dict(self) -> dict:
        return {'title': self.title, 'completed': self.completed,
                'scheduled': self.scheduled, 'day_of_week': self.day_of_week,
                'created_at': self.created_at, 'completed_at': self.completed_at}

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        task = cls(data['title'])
        for key in ['completed', 'scheduled', 'day_of_week', 'created_at', 'completed_at']:
            if key in data: setattr(task, key, data[key])
        return task

    def __str__(self) -> str:
        s = "✓" if self.completed else "☐"
        result = f"[{s}] {self.title}"
        if self.created_at: result += f"\n    Создана: {self.created_at}"
        if self.scheduled:
            parts = self.scheduled.split()
            result += f"\n    Запланировано: {parts[0]}"
            if self.day_of_week: result += f" ({self.WEEKDAYS[self.day_of_week - 1]})"
            if len(parts) > 1 and parts[1] != '00:00': result += f" в {parts[1]}"
        if self.completed and self.completed_at: result += f"\n    Выполнена: {self.completed_at}"
        return result


class TodoApp:
    def __init__(self, filename: str = "tasks.json"):
        self.filename = filename
        self.tasks: List[Task] = []
        self._load()

    def _save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump([t.to_dict() for t in self.tasks], f, ensure_ascii=False, indent=2)

    def _load(self):
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                self.tasks = [Task.from_dict(d) for d in json.load(f)]
        except:
            self.tasks = []

    def add(self, title: str, day=None, time=None, date=None):
        task = Task(title)
        if day or time or date: task.set_schedule(day, time, date)
        self.tasks.append(task)
        self._save()

    def get_tasks(self, filter_type=None, day=None, date=None):
        tasks = self.tasks.copy()
        if filter_type == 'today':
            today = datetime.now().strftime("%d-%m-%Y")
            tasks = [t for t in tasks if not t.completed and t.scheduled and t.scheduled.startswith(today)]
        elif filter_type == 'day':
            tasks = [t for t in tasks if t.day_of_week == day and not t.completed]
        elif filter_type == 'date' and date:
            tasks = [t for t in tasks if t.scheduled and t.scheduled.startswith(date)]
        tasks.sort(key=lambda x: (x.completed, x.scheduled or '99-99-9999'))
        return tasks

    def stats(self):
        tasks = self.tasks
        return {
            'total': len(tasks),
            'completed': sum(1 for t in tasks if t.completed),
            'pending': sum(1 for t in tasks if not t.completed),
            'today': len(self.get_tasks('today'))
        }

    def complete(self, i):
        if 0 < i <= len(self.tasks):
            self.tasks[i - 1].completed = True
            self.tasks[i - 1].completed_at = datetime.now().strftime("%d-%m-%Y %H:%M")
            self._save()
            return True

    def delete(self, i):
        if 0 < i <= len(self.tasks):
            del self.tasks[i - 1]
            self._save()
            return True


class Menu:
    def __init__(self, app: TodoApp):
        self.app = app

    def _show(self, tasks, title="ЗАДАЧИ"):
        if not tasks: return print("\nНет задач!")
        print(f"\n{'=' * 60}\n{title.center(60)}\n{'=' * 60}")
        for i, t in enumerate(tasks, 1):
            print(f"{i:2d}. {t}")
            if i < len(tasks): print()
        print("=" * 60)

    def _input_date(self):
        """Ввод даты с валидацией."""
        while True:
            date = input("Дата (ДД-ММ-ГГГГ): ").strip()
            try:
                day, month, year = map(int, date.split('-'))
                if not (1 <= month <= 12 and 1 <= day <= 31 and 2024 <= year <= 2100):
                    raise ValueError
                datetime(year, month, day)
                return date
            except:
                print(" Неверный формат! Используйте ДД-ММ-ГГГГ (день-месяц-год)")

    def _input_time(self):
        """Ввод времени с валидацией."""
        while True:
            time = input("Время (ЧЧ:ММ) или Enter для пропуска: ").strip()
            if not time:
                return None
            try:
                hours, minutes = map(int, time.split(':'))
                if 0 <= hours <= 23 and 0 <= minutes <= 59:
                    return time
                raise ValueError
            except:
                print(" Неверный формат! Используйте ЧЧ:ММ (часы:минуты)")

    def _input_schedule(self):
        print("\n1. По дню недели  2. По дате  3. Пропустить")
        c = input("Выбор: ").strip()

        if c == '3': return None, None, None
        if c not in ['1', '2']:
            print(" Неверный выбор!")
            return False, None, None

        time = self._input_time()

        if c == '1':
            print("\nДни недели:")
            for i, d in enumerate(Task.WEEKDAYS, 1): print(f"{i}. {d}")
            while True:
                try:
                    day = int(input("День (1-7): "))
                    if 1 <= day <= 7:
                        return day, time, None
                except:
                    pass
                print(" Введите число от 1 до 7!")

        elif c == '2':
            date = self._input_date()
            return None, time, date

        return None, None, None

    def run(self):
        while True:
            print(f"\n{'=' * 40}\n{'TODO LIST'.center(40)}\n{'=' * 40}")
            for n, name in enumerate(['Добавить', 'Все задачи', 'Выполнить', 'Удалить',
                                      'На сегодня', 'По дню недели', 'Поиск по дате',
                                      'Статистика', 'Очистить', 'Выход'], 1):
                print(f"{n:2}. {name}")
            print("=" * 40)

            c = input("\nВыбор: ").strip()

            if c == '1':
                title = input("\nЗадача: ").strip()
                if title:
                    result = self._input_schedule()
                    if result[0] is not False:
                        self.app.add(title, *result)
                        print(f" Добавлено!")


            elif c == '2':
                tasks = self.app.get_tasks()
                self._show(tasks)

            elif c == '3':
                tasks = self.app.get_tasks()
                self._show(tasks)
                if tasks:
                    try:
                        i = int(input("\nНомер: "))
                        print("Выполнено!" if self.app.complete(i) else "Ошибка!")
                    except:
                        print("Ошибка!")

            elif c == '4':
                tasks = self.app.get_tasks()
                self._show(tasks)
                if tasks:
                    try:
                        i = int(input("\nНомер: "))
                        if 0 < i <= len(tasks) and input(f"Удалить? (да/нет): ").lower() in ['да', 'y']:
                            print("Удалено!" if self.app.delete(i) else "Ошибка!")
                    except:
                        print("Ошибка!")

            elif c == '5':
                self._show(self.app.get_tasks('today'), "НА СЕГОДНЯ")

            elif c == '6':
                try:
                    d = int(input("\nДень (1-7): "))
                    if 1 <= d <= 7:
                        self._show(self.app.get_tasks('day', day=d), f"НА {Task.WEEKDAYS[d - 1].upper()}")
                except:
                    print("Ошибка!")

            elif c == '7':
                print("\n Поиск задач по дате")
                date = self._input_date()
                if date:
                    tasks = self.app.get_tasks('date', date=date)
                    self._show(tasks, f"ЗАДАЧИ НА {date}")

            elif c == '8':
                s = self.app.stats()
                print(f"\n{'=' * 30}\n{'СТАТИСТИКА'.center(30)}\n{'=' * 30}")
                for k, v in [('Всего', 'total'), ('Выполнено', 'completed'),
                             ('Осталось', 'pending'), ('На сегодня', 'today')]:
                    print(f"{k}: {s[v]}")
                print("=" * 30)

            elif c == '9':
                if self.app.tasks and input("\nУдалить всё? (да/нет): ").lower() in ['да', 'y']:
                    self.app.tasks.clear()
                    self.app._save()
                    print("Очищено!")

            elif c == '10':
                break


if __name__ == "__main__":
        Menu(TodoApp()).run()