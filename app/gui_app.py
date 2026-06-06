#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import psycopg2
import re
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scripts.db_config import DB_CONFIG

class UniversityDBFullApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ВУЗ: Система управления успеваемостью")
        self.root.geometry("1300x850")
        
        # Переменные состояния
        self.status_var = tk.StringVar(value="Готов")
        self.conn = None
        
        # Подключение к БД
        self.connect_db()
        
        # Создание интерфейса
        self.create_menu()
        self.create_main_layout()
        self.create_status_bar()
        
        # Загрузка начальных данных
        self.load_stats()
    
    def connect_db(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.status_var.set("Подключено к БД")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться:\n{e}")
            self.status_var.set("Ошибка подключения")
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Экспорт в CSV", command=self.export_csv)
        file_menu.add_command(label="Бэкап", command=self.backup_db)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)
        
        reports_menu = tk.Menu(menubar, tearoff=0)
        reports_menu.add_command(label="Средний балл по сезонам", command=lambda: self.run_query("task1"))
        reports_menu.add_command(label="Средний балл по факультетам и сезонам", command=lambda: self.run_query("task2"))
        reports_menu.add_command(label="Средний балл по дням недели", command=lambda: self.run_query("task3"))
        reports_menu.add_separator()
        reports_menu.add_command(label="Топ студентов", command=self.show_top_students)
        reports_menu.add_command(label="Худшие студенты", command=self.show_weak_students)
        reports_menu.add_command(label="Топ преподавателей", command=self.show_top_teachers)
        menubar.add_cascade(label="Отчёты", menu=reports_menu)
        
        subqueries_menu = tk.Menu(menubar, tearoff=0)
        subqueries_menu.add_command(label="Отклонение среднего балла", command=lambda: self.run_query("110"))
        subqueries_menu.add_command(label="Рейтинг преподавателей", command=lambda: self.run_query("111"))
        subqueries_menu.add_command(label="Студенты выше среднего", command=lambda: self.run_query("112"))
        subqueries_menu.add_command(label="Статистика по факультетам", command=lambda: self.run_query("113"))
        subqueries_menu.add_command(label="Топ-3 студента на факультете", command=lambda: self.run_query("114"))
        subqueries_menu.add_command(label="Оценки выше среднего по дисциплине", command=self.show_grades_above_avg)
        subqueries_menu.add_command(label="Студенты без троек и двоек", command=lambda: self.run_query("116"))
        subqueries_menu.add_command(label="Лучшие студенты ALL", command=lambda: self.run_query("117"))
        menubar.add_cascade(label="Подзапросы", menu=subqueries_menu)
        
        func_menu = tk.Menu(menubar, tearoff=0)
        func_menu.add_command(label="Создать все функции", command=self.create_all_functions)
        func_menu.add_command(label="Студенты выше порога", command=self.show_students_above_threshold)
        func_menu.add_command(label="Средний балл по факультетам и сезонам (функция)", command=lambda: self.run_query("202"))
        func_menu.add_command(label="Сводная таблица", command=lambda: self.run_query("203"))
        menubar.add_cascade(label="Функции", menu=func_menu)
        
        charts_menu = tk.Menu(menubar, tearoff=0)
        charts_menu.add_command(label="Динамика успеваемости", command=self.show_dynamics_chart)
        charts_menu.add_command(label="Круговая диаграмма по группам", command=self.show_pie_chart)
        menubar.add_cascade(label="Графики", menu=charts_menu)
        
        admin_menu = tk.Menu(menubar, tearoff=0)
        admin_menu.add_command(label="Статистика БД", command=self.show_db_stats)
        admin_menu.add_command(label="Просмотр таблиц", command=self.show_table_viewer)
        admin_menu.add_command(label="Структура таблиц", command=self.show_table_structure)
        admin_menu.add_separator()
        admin_menu.add_command(label="Архивировать старые записи", command=self.archive_records)
        menubar.add_cascade(label="Администрирование", menu=admin_menu)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_main_layout(self):
        # Левая панель
        left_frame = tk.Frame(self.root, width=240)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        tk.Label(left_frame, text="Быстрый доступ", font=("Arial", 12, "bold")).pack(pady=5)
        
        quick_buttons = [
            ("📊 Топ студентов", self.show_top_students),
            ("📉 Худшие студенты", self.show_weak_students),
            ("👨‍🏫 Топ преподавателей", self.show_top_teachers),
            ("📈 Статистика БД", self.show_db_stats),
            ("📋 Просмотр таблиц", self.show_table_viewer),
            ("📐 Структура таблиц", self.show_table_structure),
            ("📅 Динамика успеваемости", self.show_dynamics_chart),
            ("🥧 Круговая диаграмма", self.show_pie_chart),
        ]
        
        for text, cmd in quick_buttons:
            btn = tk.Button(left_frame, text=text, command=cmd, width=26, anchor="w")
            btn.pack(pady=2)
        
        # Центральная панель
        right_frame = tk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Панель параметров
        param_frame = tk.LabelFrame(right_frame, text="Параметры запроса", padx=5, pady=5)
        param_frame.pack(fill=tk.X, pady=5)
        
        # Количество
        tk.Label(param_frame, text="Количество:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.limit_var = tk.StringVar(value="10")
        tk.Spinbox(param_frame, from_=1, to=100, textvariable=self.limit_var, width=5).grid(row=0, column=1, padx=5, pady=2)
        
        # Фильтр (с подсказкой о триграммах)
        tk.Label(param_frame, text="Поиск (триграммы):").grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        self.filter_var = tk.StringVar()
        self.filter_entry = tk.Entry(param_frame, textvariable=self.filter_var, width=25)
        self.filter_entry.grid(row=0, column=3, padx=5, pady=2)
        
        # Порог схожести (для триграмм)
        tk.Label(param_frame, text="Порог схожести:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.similarity_var = tk.StringVar(value="0.3")
        tk.Spinbox(param_frame, from_=0.1, to=0.9, increment=0.1, textvariable=self.similarity_var, width=5).grid(row=1, column=1, padx=5, pady=2)
        
        # Порог для функции
        tk.Label(param_frame, text="Порог (для функции):").grid(row=1, column=2, padx=5, pady=2, sticky=tk.W)
        self.threshold_var = tk.StringVar(value="4.0")
        tk.Entry(param_frame, textvariable=self.threshold_var, width=10).grid(row=1, column=3, padx=5, pady=2)
        
        # День недели
        tk.Label(param_frame, text="День недели (1-7):").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        self.day_var = tk.StringVar(value="1")
        tk.Spinbox(param_frame, from_=1, to=7, textvariable=self.day_var, width=5).grid(row=2, column=1, padx=5, pady=2)
        
        # Кнопка выполнения
        self.run_btn = tk.Button(param_frame, text="▶ Выполнить", command=self.execute_current_query, bg="#4CAF50", fg="white")
        self.run_btn.grid(row=0, column=4, rowspan=3, padx=10, pady=5)
        
        self.current_query = "top"
        
        # Область результатов
        result_frame = tk.LabelFrame(right_frame, text="Результаты", padx=5, pady=5)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, font=("Courier", 10), state=tk.DISABLED)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # Нижняя панель
        stats_frame = tk.Frame(right_frame)
        stats_frame.pack(fill=tk.X, pady=5)
        self.stats_label = tk.Label(stats_frame, text="", anchor=tk.W)
        self.stats_label.pack(fill=tk.X)
    
    def create_status_bar(self):
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def validate_number(self, value, default=10):
        if re.match(r'^\d+$', str(value)):
            return int(value)
        return default
    
    def validate_day(self, value, default=1):
        if re.match(r'^[1-7]$', str(value)):
            return int(value)
        return default
    
    def validate_threshold(self, value, default=4.0):
        if re.match(r'^\d+(\.\d+)?$', str(value)):
            return float(value)
        return default
    
    def validate_similarity(self, value, default=0.3):
        if re.match(r'^0?\.[0-9]+$|^[0-9]$', str(value)):
            return float(value)
        return default
    
    def display_text(self, text):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.config(state=tk.DISABLED)
    
    def execute_query(self, sql, params=None):
        if not self.conn:
            return [], []
        try:
            cur = self.conn.cursor()
            cur.execute(sql, params)
            if cur.description:
                rows = cur.fetchall()
                colnames = [desc[0] for desc in cur.description]
            else:
                rows = []
                colnames = []
            self.conn.commit()
            cur.close()
            return rows, colnames
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return [], []
    
    def format_results(self, rows, colnames):
        if not rows:
            return "\n" + "═" * 60 + "\n" + \
                   "           НЕТ ДАННЫХ, УДОВЛЕТВОРЯЮЩИХ ЗАПРОСУ\n" + \
                   "═" * 60 + "\n" + \
                   "Возможные причины:\n" + \
                   "• Нет записей в базе данных\n" + \
                   "• Заданные критерии фильтрации не дали результатов\n" + \
                   "• Проверьте правильность введённых параметров\n" + \
                   "• Для поиска по триграммам попробуйте уменьшить порог схожести\n"
        
        col_widths = [len(str(c)) for c in colnames]
        for row in rows[:100]:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))
        
        result = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐\n"
        result += "│" + "│".join(f" {colnames[i].ljust(col_widths[i])} " for i in range(len(colnames))) + "│\n"
        result += "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤\n"
        
        for row in rows[:100]:
            result += "│" + "│".join(f" {str(row[i]).ljust(col_widths[i])} " for i in range(len(colnames))) + "│\n"
        
        if len(rows) > 100:
            result += f"│ ... и ещё {len(rows) - 100} строк │\n"
        result += "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘\n"
        result += f"\n📊 Всего строк: {len(rows)}\n"
        
        return result
    
    def build_trigram_condition(self, field_name):
        """Строит условие поиска по триграммам"""
        filter_value = self.filter_var.get().strip()
        if not filter_value:
            return ""
        similarity = self.validate_similarity(self.similarity_var.get())
        return f"AND {field_name} % '{filter_value}' AND similarity({field_name}, '{filter_value}') >= {similarity}"
    
    def build_like_condition(self, field_name):
        """Обычный LIKE поиск (для точного совпадения)"""
        filter_value = self.filter_var.get().strip()
        if not filter_value:
            return ""
        return f"AND {field_name} ILIKE '%{filter_value}%'"
    
    def execute_current_query(self):
        queries = {
            "top": self.show_top_students,
            "weak": self.show_weak_students,
            "teacher": self.show_top_teachers,
            "task1": lambda: self.run_query("task1"),
            "task2": lambda: self.run_query("task2"),
            "task3": lambda: self.run_query("task3"),
            "task4": lambda: self.run_query("task4"),
            "110": lambda: self.run_query("110"),
            "111": lambda: self.run_query("111"),
            "112": lambda: self.run_query("112"),
            "113": lambda: self.run_query("113"),
            "114": lambda: self.run_query("114"),
            "116": lambda: self.run_query("116"),
            "117": lambda: self.run_query("117"),
            "201": self.show_students_above_threshold,
        }
        if self.current_query in queries:
            queries[self.current_query]()
    
    def run_query(self, query_name):
        self.current_query = query_name
        limit = self.validate_number(self.limit_var.get())
        day = self.validate_day(self.day_var.get())
        filter_cond = self.build_trigram_condition
        
        sql_map = {
            "task1": """
                SELECT s.название as сезон, 
                       ROUND(AVG(u.оценка), 2) as средний_балл,
                       COUNT(*) as количество
                FROM УСПЕВАЕМОСТЬ u 
                JOIN ВРЕМЕНА_ГОДА s ON s.код = u.сезон
                GROUP BY s.код, s.название
                ORDER BY s.код
            """,
            "task2": """
                SELECT g.факультет, s.название as сезон,
                       ROUND(AVG(u.оценка), 2) as средний_балл
                FROM УСПЕВАЕМОСТЬ u
                JOIN ГРУППЫ g ON g.код = u.группа
                JOIN ВРЕМЕНА_ГОДА s ON s.код = u.сезон
                GROUP BY g.факультет, s.код, s.название
                ORDER BY g.факультет, s.код
            """,
            "task3": """
                SELECT EXTRACT(DOW FROM дата) as день_недели,
                       t.фамилия as преподаватель,
                       ROUND(AVG(оценка), 2) as средний_балл
                FROM УСПЕВАЕМОСТЬ u
                JOIN ПРЕПОДАВАТЕЛИ t ON t.код = u.преподаватель
                GROUP BY день_недели, t.фамилия
                ORDER BY день_недели, средний_балл DESC
            """,
            "task4": f"""
                SELECT d.название as дисциплина,
                       ROUND(AVG(u.оценка), 2) as средний_балл
                FROM УСПЕВАЕМОСТЬ u
                JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
                WHERE EXTRACT(DOW FROM дата) = {day}
                GROUP BY d.название
                ORDER BY средний_балл DESC
            """,
            "110": f"""
                SELECT s.фамилия, s.имя, g.название as группа,
                       ROUND(AVG(u.оценка), 2) as средний_студента,
                       (SELECT ROUND(AVG(оценка), 2) FROM УСПЕВАЕМОСТЬ 
                        WHERE группа = g.код) as средний_группы
                FROM СТУДЕНТЫ s
                JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
                JOIN ГРУППЫ g ON g.код = u.группа
                WHERE 1=1 {filter_cond('s.фамилия')}
                GROUP BY s.код, s.фамилия, s.имя, g.код, g.название
                ORDER BY средний_студента - средний_группы DESC
            """,
            "111": f"""
                SELECT t.фамилия, t.имя,
                       ROUND(AVG(u.оценка), 2) as средний_балл,
                       COUNT(*) as оценок
                FROM ПРЕПОДАВАТЕЛИ t
                JOIN УСПЕВАЕМОСТЬ u ON u.преподаватель = t.код
                WHERE 1=1 {filter_cond('t.фамилия')}
                GROUP BY t.код, t.фамилия, t.имя
                ORDER BY средний_балл DESC
                LIMIT {limit}
            """,
            "112": f"""
                SELECT s.фамилия, s.имя, g.название as группа,
                       ROUND(AVG(u.оценка), 2) as средний_балл
                FROM СТУДЕНТЫ s
                JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
                JOIN ГРУППЫ g ON g.код = u.группа
                WHERE 1=1 {filter_cond('g.название')}
                GROUP BY s.код, s.фамилия, s.имя, g.название
                HAVING AVG(u.оценка) > (SELECT AVG(оценка) FROM УСПЕВАЕМОСТЬ)
                ORDER BY средний_балл DESC
            """,
            "113": f"""
                SELECT g.факультет,
                       ROUND(AVG(u.оценка), 2) as средний_балл,
                       COUNT(DISTINCT s.код) as студентов,
                       COUNT(u.код_записи) as оценок
                FROM ГРУППЫ g
                JOIN УСПЕВАЕМОСТЬ u ON u.группа = g.код
                JOIN СТУДЕНТЫ s ON s.код = u.студент
                WHERE 1=1 {filter_cond('g.факультет')}
                GROUP BY g.факультет
                ORDER BY средний_балл DESC
            """,
            "114": f"""
                SELECT * FROM (
                    SELECT g.факультет, s.фамилия, s.имя,
                           ROUND(AVG(u.оценка), 2) as средний_балл,
                           ROW_NUMBER() OVER (PARTITION BY g.факультет ORDER BY AVG(u.оценка) DESC) as место
                    FROM СТУДЕНТЫ s
                    JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
                    JOIN ГРУППЫ g ON g.код = u.группа
                    WHERE 1=1 {filter_cond('g.факультет')}
                    GROUP BY g.факультет, s.код, s.фамилия, s.имя
                ) t WHERE место <= 3
                ORDER BY факультет, место
            """,
            "116": f"""
                SELECT DISTINCT s.фамилия, s.имя, g.название as группа,
                       ROUND(AVG(u.оценка), 2) as средний_балл
                FROM СТУДЕНТЫ s
                JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
                JOIN ГРУППЫ g ON g.код = u.группа
                WHERE 1=1 {filter_cond('g.название')}
                AND NOT EXISTS (
                    SELECT 1 FROM УСПЕВАЕМОСТЬ u2 
                    WHERE u2.студент = s.код AND u2.оценка IN (2, 3)
                )
                GROUP BY s.код, s.фамилия, s.имя, g.название
                ORDER BY средний_балл DESC
            """,
            "117": f"""
                SELECT фамилия, имя, группа, средний_балл
                FROM (
                    SELECT s.фамилия, s.имя, g.название as группа,
                           ROUND(AVG(u.оценка), 2) as средний_балл
                    FROM СТУДЕНТЫ s
                    JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
                    JOIN ГРУППЫ g ON g.код = u.группа
                    WHERE 1=1 {filter_cond('g.название')}
                    GROUP BY s.код, s.фамилия, s.имя, g.название
                ) t ORDER BY средний_балл DESC LIMIT {limit}
            """,
            "202": """
                SELECT факультет, сезон, средний_балл, количество_оценок 
                FROM grades_by_faculty_and_season() 
                ORDER BY факультет
            """,
            "203": """
                SELECT * FROM display_pivot_table()
            """,
        }
        
        sql = sql_map.get(query_name)
        if sql:
            rows, colnames = self.execute_query(sql)
            result = self.format_results(rows, colnames)
            self.display_text(result)
            filter_text = self.filter_var.get().strip()
            similarity = self.validate_similarity(self.similarity_var.get())
            self.status_var.set(f"Выполнен запрос: {query_name}" + 
                              (f" | Поиск: '{filter_text}' (порог схожести: {similarity})" if filter_text else ""))
    
    def show_top_students(self):
        self.current_query = "top"
        limit = self.validate_number(self.limit_var.get())
        filter_cond = self.build_trigram_condition('g.название')
        
        sql = f"""
        SELECT фамилия, имя, группа, средний_балл, количество_оценок
        FROM (
            SELECT s.фамилия, s.имя, g.название as группа,
                   ROUND(AVG(u.оценка), 2) as средний_балл,
                   COUNT(u.код_записи) as количество_оценок
            FROM СТУДЕНТЫ s
            JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
            JOIN ГРУППЫ g ON g.код = u.группа
            WHERE 1=1 {filter_cond}
            GROUP BY s.код, s.фамилия, s.имя, g.название
        ) t ORDER BY средний_балл DESC LIMIT {limit}
        """
        rows, colnames = self.execute_query(sql)
        result = self.format_results(rows, colnames)
        self.display_text(result)
        filter_text = self.filter_var.get().strip()
        similarity = self.validate_similarity(self.similarity_var.get())
        self.status_var.set(f"Топ {limit} студентов" + 
                          (f" | Поиск группы: '{filter_text}' (порог: {similarity})" if filter_text else ""))
    
    def show_weak_students(self):
        self.current_query = "weak"
        limit = self.validate_number(self.limit_var.get())
        filter_cond = self.build_trigram_condition('g.название')
        
        sql = f"""
        SELECT фамилия, имя, группа, средний_балл, количество_оценок
        FROM (
            SELECT s.фамилия, s.имя, g.название as группа,
                   ROUND(AVG(u.оценка), 2) as средний_балл,
                   COUNT(u.код_записи) as количество_оценок
            FROM СТУДЕНТЫ s
            JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
            JOIN ГРУППЫ g ON g.код = u.группа
            WHERE 1=1 {filter_cond}
            GROUP BY s.код, s.фамилия, s.имя, g.название
        ) t ORDER BY средний_балл ASC LIMIT {limit}
        """
        rows, colnames = self.execute_query(sql)
        result = self.format_results(rows, colnames)
        self.display_text(result)
        filter_text = self.filter_var.get().strip()
        similarity = self.validate_similarity(self.similarity_var.get())
        self.status_var.set(f"Худшие {limit} студентов" + 
                          (f" | Поиск группы: '{filter_text}' (порог: {similarity})" if filter_text else ""))
    
    def show_top_teachers(self):
        self.current_query = "teacher"
        limit = self.validate_number(self.limit_var.get())
        filter_cond = self.build_trigram_condition('t.фамилия')
        
        sql = f"""
        SELECT t.фамилия, t.имя, t.отчество,
               ROUND(AVG(u.оценка), 2) as средний_балл,
               COUNT(u.код_записи) as оценок
        FROM ПРЕПОДАВАТЕЛИ t
        JOIN УСПЕВАЕМОСТЬ u ON u.преподаватель = t.код
        WHERE 1=1 {filter_cond}
        GROUP BY t.код, t.фамилия, t.имя, t.отчество
        ORDER BY средний_балл DESC LIMIT {limit}
        """
        rows, colnames = self.execute_query(sql)
        result = self.format_results(rows, colnames)
        self.display_text(result)
        filter_text = self.filter_var.get().strip()
        similarity = self.validate_similarity(self.similarity_var.get())
        self.status_var.set(f"Топ {limit} преподавателей" + 
                          (f" | Поиск фамилии: '{filter_text}' (порог: {similarity})" if filter_text else ""))
    
    def show_grades_above_avg(self):
        subject = self.filter_var.get().strip()
        if not subject:
            messagebox.showwarning("Внимание", "Введите название дисциплины в поле 'Поиск'")
            return
        
        similarity = self.validate_similarity(self.similarity_var.get())
        
        sql = f"""
        SELECT s.фамилия, s.имя, u.оценка, u.дата,
               similarity(d.название, '{subject}') as схожесть
        FROM УСПЕВАЕМОСТЬ u
        JOIN СТУДЕНТЫ s ON s.код = u.студент
        JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
        WHERE d.название % '{subject}'
          AND similarity(d.название, '{subject}') >= {similarity}
          AND u.оценка > (SELECT AVG(оценка) FROM УСПЕВАЕМОСТЬ WHERE дисциплина = d.код)
        ORDER BY схожесть DESC, u.оценка DESC
        """
        rows, colnames = self.execute_query(sql)
        result = self.format_results(rows, colnames)
        self.display_text(result)
        self.status_var.set(f"Оценки выше среднего по дисциплине: {subject} (порог схожести: {similarity})")
    
    def show_students_above_threshold(self):
        self.current_query = "201"
        threshold = self.validate_threshold(self.threshold_var.get())
        filter_cond = self.build_trigram_condition('группа')
        
        sql = f"""
        SELECT фамилия, имя, группа, средний_балл
        FROM students_above_threshold({threshold})
        WHERE 1=1 {filter_cond}
        """
        rows, colnames = self.execute_query(sql)
        result = self.format_results(rows, colnames)
        self.display_text(result)
        filter_text = self.filter_var.get().strip()
        similarity = self.validate_similarity(self.similarity_var.get())
        self.status_var.set(f"Студенты со средним баллом выше {threshold}" + 
                          (f" | Поиск группы: '{filter_text}' (порог: {similarity})" if filter_text else ""))
    
    def create_all_functions(self):
        sqls = [
            "SELECT students_above_threshold(4.0)",
            "SELECT * FROM grades_by_faculty_and_season()",
            "SELECT * FROM display_pivot_table()"
        ]
        for sql in sqls:
            self.execute_query(sql)
        messagebox.showinfo("Успех", "Все функции созданы")
        self.status_var.set("Функции созданы")
    
    def show_db_stats(self):
        sql = """
        SELECT 'СТУДЕНТЫ' as таблица, COUNT(*) as записей FROM СТУДЕНТЫ
        UNION ALL SELECT 'ГРУППЫ', COUNT(*) FROM ГРУППЫ
        UNION ALL SELECT 'ПРЕПОДАВАТЕЛИ', COUNT(*) FROM ПРЕПОДАВАТЕЛИ
        UNION ALL SELECT 'ДИСЦИПЛИНЫ', COUNT(*) FROM ДИСЦИПЛИНЫ
        UNION ALL SELECT 'УСПЕВАЕМОСТЬ', COUNT(*) FROM УСПЕВАЕМОСТЬ
        UNION ALL SELECT 'УСПЕВАЕМОСТЬ_АРХИВ', COUNT(*) FROM УСПЕВАЕМОСТЬ_АРХИВ
        """
        rows, colnames = self.execute_query(sql)
        result = self.format_results(rows, colnames)
        self.display_text(result)
        self.status_var.set("Статистика базы данных")
    
    def show_table_viewer(self):
        viewer = tk.Toplevel(self.root)
        viewer.title("Просмотр таблиц")
        viewer.geometry("400x350")
        viewer.transient(self.root)
        viewer.grab_set()
        
        tk.Label(viewer, text="Выберите таблицу:", font=("Arial", 12)).pack(pady=10)
        
        tables = ["СТУДЕНТЫ", "ГРУППЫ", "ПРЕПОДАВАТЕЛИ", "ДИСЦИПЛИНЫ", "УСПЕВАЕМОСТЬ"]
        
        for table in tables:
            btn = tk.Button(viewer, text=table, width=30, command=lambda t=table: self.view_table(t, viewer))
            btn.pack(pady=5)
    
    def view_table(self, table_name, parent):
        sql = f"SELECT * FROM {table_name} ORDER BY код LIMIT 200"
        rows, colnames = self.execute_query(sql)
        result = self.format_results(rows, colnames)
        
        result_win = tk.Toplevel(parent)
        result_win.title(f"Таблица: {table_name}")
        result_win.geometry("900x600")
        
        text = scrolledtext.ScrolledText(result_win, wrap=tk.WORD, font=("Courier", 10), state=tk.DISABLED)
        text.pack(fill=tk.BOTH, expand=True)
        
        text.config(state=tk.NORMAL)
        text.insert(tk.END, result)
        text.config(state=tk.DISABLED)
    
    def show_table_structure(self):
        sql = """
        SELECT table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
        """
        rows, colnames = self.execute_query(sql)
        result = self.format_results(rows, colnames)
        self.display_text(result)
        self.status_var.set("Структура таблиц")
    
    def show_dynamics_chart(self):
        sql = """
        SELECT DATE_TRUNC('month', дата) as месяц,
               ROUND(AVG(оценка), 2) as средний_балл,
               COUNT(*) as количество
        FROM УСПЕВАЕМОСТЬ
        WHERE дата IS NOT NULL
        GROUP BY DATE_TRUNC('month', дата)
        ORDER BY месяц
        """
        rows, _ = self.execute_query(sql)
        
        if not rows:
            messagebox.showinfo("Нет данных", "Недостаточно данных для построения графика")
            return
        
        months = [row[0] for row in rows]
        avg_grades = [float(row[1]) for row in rows]
        counts = [int(row[2]) for row in rows]
        
        chart_win = tk.Toplevel(self.root)
        chart_win.title("Динамика успеваемости")
        chart_win.geometry("800x500")
        
        fig, ax1 = plt.subplots(figsize=(8, 5))
        
        ax1.set_xlabel('Дата')
        ax1.set_ylabel('Средний балл', color='blue')
        ax1.plot(months, avg_grades, color='blue', marker='o', linewidth=2)
        ax1.tick_params(axis='y', labelcolor='blue')
        ax1.set_ylim(2, 5)
        
        ax2 = ax1.twinx()
        ax2.set_ylabel('Количество оценок', color='red')
        ax2.bar(months, counts, color='red', alpha=0.3)
        ax2.tick_params(axis='y', labelcolor='red')
        
        plt.title('Динамика успеваемости по месяцам')
        plt.xticks(rotation=45, ha='right')
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=chart_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def show_pie_chart(self):
        filter_text = self.filter_var.get().strip()
        similarity = self.validate_similarity(self.similarity_var.get())
        
        if filter_text:
            sql = f"""
            SELECT d.название as дисциплина,
                   ROUND(AVG(u.оценка), 2) as средний_балл,
                   similarity(d.название, '{filter_text}') as схожесть
            FROM ДИСЦИПЛИНЫ d
            LEFT JOIN УСПЕВАЕМОСТЬ u ON u.дисциплина = d.код
            LEFT JOIN ГРУППЫ g ON g.код = u.группа
            WHERE d.название % '{filter_text}' AND similarity(d.название, '{filter_text}') >= {similarity}
            GROUP BY d.код, d.название
            HAVING COUNT(u.код_записи) > 0
            ORDER BY схожесть DESC, средний_балл DESC
            """
            title = f'Средний балл по дисциплинам (поиск: {filter_text})'
        else:
            sql = """
            SELECT g.название as группа,
                   ROUND(AVG(u.оценка), 2) as средний_балл
            FROM ГРУППЫ g
            LEFT JOIN УСПЕВАЕМОСТЬ u ON u.группа = g.код
            GROUP BY g.код, g.название
            HAVING COUNT(u.код_записи) > 0
            ORDER BY средний_балл DESC
            """
            title = 'Средний балл по группам'
        
        rows, _ = self.execute_query(sql)
        
        if not rows:
            messagebox.showinfo("Нет данных", "Недостаточно данных для построения диаграммы")
            return
        
        labels = [row[0] for row in rows]
        sizes = [float(row[1]) for row in rows]
        
        chart_win = tk.Toplevel(self.root)
        chart_win.title(title)
        chart_win.geometry("600x550")
        
        fig, ax = plt.subplots(figsize=(6, 6))
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%')
        ax.set_title(title)
        
        canvas = FigureCanvasTkAgg(fig, master=chart_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def export_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if filename and self.conn:
            try:
                cur = self.conn.cursor()
                cur.execute("SELECT * FROM СТУДЕНТЫ")
                rows = cur.fetchall()
                colnames = [desc[0] for desc in cur.description]
                cur.close()
                
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(colnames)
                    writer.writerows(rows)
                
                messagebox.showinfo("Успех", f"Экспортировано {len(rows)} записей")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
    
    def backup_db(self):
        filename = filedialog.asksaveasfilename(defaultextension=".dump", filetypes=[("Dump files", "*.dump")])
        if filename:
            import os
            cmd = f"pg_dump -Fc -f '{filename}' {DB_CONFIG['dbname']}"
            os.system(cmd)
            messagebox.showinfo("Успех", f"Бэкап создан: {filename}")
    
    def archive_records(self):
        if messagebox.askyesno("Подтверждение", "Архивировать записи старше 2 лет?"):
            sql = "SELECT archive_old_records(2)"
            rows, _ = self.execute_query(sql)
            if rows:
                messagebox.showinfo("Успех", f"Архивировано {rows[0][0]} записей")
            self.show_db_stats()
    
    def load_stats(self):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM СТУДЕНТЫ")
            students = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM УСПЕВАЕМОСТЬ")
            grades = cur.fetchone()[0]
            cur.close()
            self.stats_label.config(text=f"📊 Студентов: {students} | Оценок: {grades}")
        except:
            pass
    
    def show_about(self):
        messagebox.showinfo("О программе",
            "ВУЗ: Система управления успеваемостью\n"
            "Версия 2.0 (Полная)\n\n"
            "Реализовано:\n"
            "✓ Все отчёты из лабораторных работ\n"
            "✓ Подзапросы 110-117\n"
            "✓ Функции 200-204\n"
            "✓ Графики и диаграммы\n"
            "✓ Администрирование\n"
            "✓ Поиск по триграммам (нечёткое совпадение)\n\n"
            "ТулГУ, ИПМКН, Курсовая работа 2025")

if __name__ == "__main__":
    root = tk.Tk()
    app = UniversityDBFullApp(root)
    root.mainloop()
