#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Расширенное GUI-приложение для проекта ВУЗ.

Что добавлено по сравнению с базовой версией:
- основные задачи task1-task4;
- рейтинги;
- просмотр таблиц, структуры, JOIN;
- аналитика;
- запросы с параметрами;
- добавление/редактирование/удаление;
- представления;
- подзапросы;
- SQL-функции;
- экспорт всех таблиц;
- бэкап;
- архивация;
- запуск любого SQL-файла.

Файл рассчитан на запуск из папки app:
    cd ~/Desktop/DATA_BASE/VUZ/app
    python3 gui.py
"""

import csv
import os
import re
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog

import psycopg2
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from scripts.db_config import DB_CONFIG


class UniversityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ВУЗ: система управления успеваемостью")
        self.root.geometry("1450x850")
        self.root.minsize(1150, 720)

        self.app_dir = Path(__file__).resolve().parent
        self.project_root = self.app_dir.parent
        self.conn = None
        self.current_report = "top"
        self.autocomplete_data = {
            "группа": [],
            "фамилия": [],
            "предмет": [],
            "дисциплина": [],
            "факультет": [],
            "преподаватель": [],
        }

        self.status_var = tk.StringVar(value="Готов")

        self.setup_style()
        self.connect_db()
        self.create_menu()
        self.create_widgets()
        self.load_autocomplete_data()
        self.load_stats()
        self.top_students()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ------------------------------------------------------------------
    # Базовые настройки
    # ------------------------------------------------------------------
    def setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TButton", padding=5, font=("Arial", 10))
        style.configure("Small.TButton", padding=3, font=("Arial", 9))
        style.configure("TLabel", font=("Arial", 10))
        style.configure("TLabelframe.Label", font=("Arial", 10, "bold"))

    def connect_db(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = False
            self.status_var.set("Подключено к БД")
        except Exception as e:
            self.conn = None
            self.status_var.set(f"Ошибка подключения: {e}")
            messagebox.showerror("Ошибка подключения к БД", str(e))

    def on_close(self):
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass
        self.root.destroy()

    def set_status(self, text):
        self.status_var.set(text)
        self.root.update_idletasks()

    def create_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Экспорт текущего отчёта в CSV", command=self.export_current_csv)
        file_menu.add_command(label="Экспорт всех таблиц в CSV", command=self.export_all_csv)
        file_menu.add_command(label="Бэкап БД", command=self.backup_db)
        file_menu.add_separator()
        file_menu.add_command(label="Запустить SQL-файл", command=self.run_any_sql_file)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.on_close)
        menubar.add_cascade(label="Файл", menu=file_menu)

        db_menu = tk.Menu(menubar, tearoff=0)
        db_menu.add_command(label="Переподключиться", command=self.reconnect)
        db_menu.add_command(label="Создать расширение pg_trgm", command=self.create_pg_trgm)
        db_menu.add_command(label="Создать представления", command=self.create_views)
        db_menu.add_command(label="Создать функции", command=self.create_functions)
        menubar.add_cascade(label="База данных", menu=db_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.root.config(menu=menubar)

    def reconnect(self):
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass
        self.connect_db()
        self.load_autocomplete_data()
        self.load_stats()

    # ------------------------------------------------------------------
    # Интерфейс
    # ------------------------------------------------------------------
    def create_widgets(self):
        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        top = ttk.LabelFrame(main, text="Параметры")
        top.pack(fill=tk.X, pady=(0, 6))
        self.create_params_panel(top)

        body = ttk.PanedWindow(main, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(body, width=420)
        right = ttk.Frame(body)
        body.add(left, weight=0)
        body.add(right, weight=1)

        self.notebook = ttk.Notebook(left)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.create_tab_main()
        self.create_tab_view()
        self.create_tab_edit()
        self.create_tab_sql()

        result_frame = ttk.LabelFrame(right, text="Результаты")
        result_frame.pack(fill=tk.BOTH, expand=True)

        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            wrap=tk.WORD,
            font=("Menlo", 11),
            bg="#ffffff",
            fg="#111111",
            state=tk.DISABLED,
        )
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        status = ttk.Frame(right)
        status.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(status, textvariable=self.status_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.stats_label = ttk.Label(status, text="")
        self.stats_label.pack(side=tk.RIGHT)

    def create_params_panel(self, parent):
        row1 = ttk.Frame(parent)
        row1.pack(fill=tk.X, padx=5, pady=3)

        ttk.Label(row1, text="Количество:").pack(side=tk.LEFT, padx=(0, 4))
        self.limit_var = tk.StringVar(value="10")
        ttk.Spinbox(row1, from_=1, to=500, textvariable=self.limit_var, width=7).pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(row1, text="Порог:").pack(side=tk.LEFT, padx=(0, 4))
        self.threshold_var = tk.StringVar(value="4.0")
        ttk.Entry(row1, textvariable=self.threshold_var, width=8).pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(row1, text="Дата:").pack(side=tk.LEFT, padx=(0, 4))
        self.date_var = tk.StringVar(value="")
        ttk.Entry(row1, textvariable=self.date_var, width=12).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Label(row1, text="формат YYYY-MM-DD").pack(side=tk.LEFT, padx=(0, 12))

        ttk.Button(row1, text="Очистить фильтры", command=self.clear_filters).pack(side=tk.LEFT)

        row2 = ttk.Frame(parent)
        row2.pack(fill=tk.X, padx=5, pady=3)

        ttk.Label(row2, text="Фильтр по полю:").pack(side=tk.LEFT, padx=(0, 4))
        self.filter_field_var = tk.StringVar(value="группа")
        self.filter_field_combo = ttk.Combobox(
            row2,
            textvariable=self.filter_field_var,
            values=["группа", "фамилия", "предмет", "факультет", "преподаватель"],
            width=16,
            state="readonly",
        )
        self.filter_field_combo.pack(side=tk.LEFT, padx=(0, 8))
        self.filter_field_combo.bind("<<ComboboxSelected>>", self.on_field_change)

        ttk.Label(row2, text="Значение:").pack(side=tk.LEFT, padx=(0, 4))
        self.filter_value_var = tk.StringVar()
        self.filter_value_combo = ttk.Combobox(row2, textvariable=self.filter_value_var, width=28)
        self.filter_value_combo.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(row2, text="Нечёткий поиск:").pack(side=tk.LEFT, padx=(0, 4))
        self.search_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.search_var, width=25).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(row2, text="схожесть:").pack(side=tk.LEFT, padx=(8, 4))
        self.similarity_var = tk.StringVar(value="0.3")
        ttk.Entry(row2, textvariable=self.similarity_var, width=6).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(row2, text="Применить", command=self.apply_filter).pack(side=tk.LEFT)

    def add_buttons(self, parent, items, columns=1):
        for i, (text, command) in enumerate(items):
            btn = ttk.Button(parent, text=text, command=command, style="Small.TButton")
            r = i // columns
            c = i % columns
            btn.grid(row=r, column=c, sticky="ew", padx=3, pady=3)
        for c in range(columns):
            parent.columnconfigure(c, weight=1)

    def create_tab_main(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Основное")

        ratings = ttk.LabelFrame(tab, text="Рейтинги")
        ratings.pack(fill=tk.X, padx=4, pady=4)
        self.add_buttons(ratings, [
            ("Топ студентов", self.top_students),
            ("Худшие студенты", self.weak_students),
            ("Топ преподавателей", self.top_teachers),
        ])

        tasks = ttk.LabelFrame(tab, text="Основные задачи ./h")
        tasks.pack(fill=tk.X, padx=4, pady=4)
        self.add_buttons(tasks, [
            ("task1: средний балл по сезонам", self.task1_avg_by_season),
            ("task2: факультеты × сезоны", self.task2_faculty_season),
            ("task3: дни недели × преподаватели", self.task3_day_teacher),
            ("task4: дисциплины за день", self.task4_subject_for_day),
        ])

        python_tasks = ttk.LabelFrame(tab, text="Задачи ./PYTHON")
        python_tasks.pack(fill=tk.X, padx=4, pady=4)
        self.add_buttons(python_tasks, [
            ("Отчёт группы × дисциплины", self.python_task1_report),
            ("Сводная таблица", self.python_task2_pivot),
            ("График динамики", self.show_dynamics),
            ("Круговая диаграмма", self.show_pie),
            ("Сохранить графики", self.save_all_charts),
        ])

        analytics = ttk.LabelFrame(tab, text="Аналитика")
        analytics.pack(fill=tk.X, padx=4, pady=4)
        self.add_buttons(analytics, [
            ("Распределение оценок", self.grade_distribution),
            ("Успеваемость по курсам", self.performance_by_course),
            ("Статистика группы", self.quick_group_stats),
        ])

    def create_tab_view(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Просмотр")

        tables = ttk.LabelFrame(tab, text="Таблицы")
        tables.pack(fill=tk.X, padx=4, pady=4)
        self.add_buttons(tables, [
            ("Студенты", lambda: self.view_table("СТУДЕНТЫ")),
            ("Группы", lambda: self.view_table("ГРУППЫ")),
            ("Преподаватели", lambda: self.view_table("ПРЕПОДАВАТЕЛИ")),
            ("Предметы / дисциплины", lambda: self.view_table("ДИСЦИПЛИНЫ")),
            ("Успеваемость", lambda: self.view_table("УСПЕВАЕМОСТЬ")),
            ("Количество записей", self.db_stats),
            ("Структура БД", self.show_structure),
        ])

        joins = ttk.LabelFrame(tab, text="Демонстрация JOIN")
        joins.pack(fill=tk.X, padx=4, pady=4)
        self.add_buttons(joins, [
            ("INNER JOIN", self.demo_inner_join),
            ("LEFT JOIN", self.demo_left_join),
            ("CROSS JOIN", self.demo_cross_join),
        ])

        before_after = ttk.LabelFrame(tab, text="Показать ДО/ПОСЛЕ")
        before_after.pack(fill=tk.X, padx=4, pady=4)
        self.add_buttons(before_after, [
            ("ДО UPDATE", self.show_update_before),
            ("ПОСЛЕ UPDATE", self.show_update_after),
            ("ДО DELETE", self.show_delete_before),
            ("ПОСЛЕ DELETE", self.show_delete_after),
        ])

        subs = ttk.LabelFrame(tab, text="Подзапросы")
        subs.pack(fill=tk.X, padx=4, pady=4)
        self.add_buttons(subs, [
            ("110: отклонение среднего", self.sub_110_avg_deviation),
            ("111: рейтинг преподавателей", self.sub_111_teacher_rating),
            ("112: студенты выше среднего", self.sub_112_students_above_avg),
            ("113: статистика факультетов", self.sub_113_faculty_stats),
            ("114: топ-3 на факультете", self.sub_114_top3_faculty),
            ("115: оценки выше среднего по предмету", self.sub_115_above_subject_avg),
            ("116: без троек и двоек", self.sub_116_no_bad_grades),
            ("117: лучшие студенты ALL", self.sub_117_best_all),
            ("199: выполнить все подзапросы", self.sub_199_all),
        ])

    def create_tab_edit(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Редактирование")

        params = ttk.LabelFrame(tab, text="Запросы с параметрами")
        params.pack(fill=tk.X, padx=4, pady=4)
        self.add_buttons(params, [
            ("14: группы по факультету", self.groups_by_faculty),
            ("20: поиск студента", self.search_student),
            ("40: обновить телефон", self.update_student_phone),
            ("41: удалить студента", self.delete_student),
            ("42: обновить оценку", self.update_grade),
            ("43: быстрый поиск студента", self.quick_search_student),
            ("44: статистика группы", self.quick_group_stats),
            ("53: добавить студента", self.insert_student),
        ], columns=1)

        edit = ttk.LabelFrame(tab, text="Редактирование")
        edit.pack(fill=tk.X, padx=4, pady=4)
        self.add_buttons(edit, [
            ("30: изменить телефон код=1", lambda: self.update_student_phone(default_code=1)),
            ("31: изменить дисциплину код=1", lambda: self.update_subject(default_code=1)),
            ("32: повысить оценки студентам 1,2,3", self.raise_grades_for_students),
            ("33: удалить студента код=50", lambda: self.delete_student(default_code=50)),
            ("34: удалить все оценки 2", self.delete_bad_grades),
            ("35: добавить студента", self.insert_student),
            ("36: добавить дисциплину", self.insert_subject),
            ("61: повысить курс групп", self.promote_groups_course),
            ("62: изменить должность преподавателя", self.update_teacher_position),
            ("64: INSERT SELECT в архив", self.copy_to_archive),
        ], columns=1)

        manual = ttk.LabelFrame(tab, text="Ручной ввод")
        manual.pack(fill=tk.X, padx=4, pady=4)
        self.add_buttons(manual, [
            ("70: добавить студента", self.insert_student),
            ("71: добавить оценку", self.insert_grade),
            ("72: добавить дисциплину", self.insert_subject),
            ("73: редактировать студента", self.edit_student),
            ("74: удалить студента", self.delete_student),
            ("75: полный список студентов", lambda: self.view_table("СТУДЕНТЫ", limit=1000)),
            ("76: успеваемость студента", self.view_student_grades),
        ], columns=1)

    def create_tab_sql(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="SQL/админ")

        views = ttk.LabelFrame(tab, text="Представления")
        views.pack(fill=tk.X, padx=4, pady=4)
        self.add_buttons(views, [
            ("100: создать пользовательское", self.create_user_view),
            ("101: создать технологическое", self.create_tech_view),
            ("102: проверить представления", self.check_views),
        ])

        funcs = ttk.LabelFrame(tab, text="Функции")
        funcs.pack(fill=tk.X, padx=4, pady=4)
        self.add_buttons(funcs, [
            ("200: создать все функции", self.create_functions),
            ("201: студенты выше порога", self.func_students_above_threshold),
            ("202: факультеты × сезоны", self.func_faculty_season),
            ("203: сводная таблица", self.python_task2_pivot),
            ("204: выполнить всё", self.functions_run_all),
        ])

        admin = ttk.LabelFrame(tab, text="Администрирование")
        admin.pack(fill=tk.X, padx=4, pady=4)
        self.add_buttons(admin, [
            ("Создать pg_trgm", self.create_pg_trgm),
            ("backup: бэкап", self.backup_db),
            ("export: экспорт всех таблиц", self.export_all_csv),
            ("stats: сводная статистика", self.db_stats),
            ("archive: архивировать старые записи", self.archive_old_records),
            ("Запустить любой SQL-файл", self.run_any_sql_file),
        ])

    # ------------------------------------------------------------------
    # Вспомогательные функции ввода / вывода
    # ------------------------------------------------------------------
    def display(self, text):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, str(text))
        self.result_text.config(state=tk.DISABLED)

    def append_display(self, text):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.insert(tk.END, str(text))
        self.result_text.config(state=tk.DISABLED)

    def get_limit(self, default=10):
        try:
            value = int(self.limit_var.get())
            return max(1, min(value, 1000))
        except Exception:
            self.limit_var.set(str(default))
            return default

    def get_threshold(self, default=4.0):
        try:
            return float(str(self.threshold_var.get()).replace(",", "."))
        except Exception:
            self.threshold_var.set(str(default))
            return default

    def get_similarity(self, default=0.3):
        try:
            value = float(str(self.similarity_var.get()).replace(",", "."))
            return min(max(value, 0.0), 1.0)
        except Exception:
            self.similarity_var.set(str(default))
            return default

    def ask_text(self, title, prompt, initial=""):
        return simpledialog.askstring(title, prompt, initialvalue=initial, parent=self.root)

    def ask_int(self, title, prompt, initial=None):
        return simpledialog.askinteger(title, prompt, initialvalue=initial, parent=self.root)

    def ask_float(self, title, prompt, initial=None):
        return simpledialog.askfloat(title, prompt, initialvalue=initial, parent=self.root)

    def confirm(self, title, text):
        return messagebox.askyesno(title, text, parent=self.root)

    def clear_filters(self):
        self.filter_value_var.set("")
        self.search_var.set("")
        self.date_var.set("")
        self.set_status("Фильтры очищены")
        self.apply_filter()

    def on_field_change(self, event=None):
        field = self.filter_field_var.get()
        values = self.autocomplete_data.get(field, [])
        self.filter_value_combo["values"] = values
        self.filter_value_var.set("")

    def apply_filter(self):
        if self.current_report == "top":
            self.top_students()
        elif self.current_report == "weak":
            self.weak_students()
        elif self.current_report == "teacher":
            self.top_teachers()
        elif self.current_report == "dynamics":
            self.show_dynamics()
        elif self.current_report == "pie":
            self.show_pie()
        else:
            self.top_students()

    def load_autocomplete_data(self):
        self.autocomplete_data = {
            "группа": [],
            "фамилия": [],
            "предмет": [],
            "дисциплина": [],
            "факультет": [],
            "преподаватель": [],
        }
        if not self.conn:
            return
        queries = [
            ("группа", "SELECT название FROM ГРУППЫ ORDER BY название"),
            ("фамилия", "SELECT фамилия FROM СТУДЕНТЫ ORDER BY фамилия"),
            ("предмет", "SELECT название FROM ДИСЦИПЛИНЫ ORDER BY название"),
            ("дисциплина", "SELECT название FROM ДИСЦИПЛИНЫ ORDER BY название"),
            ("факультет", "SELECT DISTINCT факультет FROM ГРУППЫ WHERE факультет IS NOT NULL ORDER BY факультет"),
            ("преподаватель", "SELECT фамилия FROM ПРЕПОДАВАТЕЛИ ORDER BY фамилия"),
        ]
        try:
            cur = self.conn.cursor()
            for key, sql in queries:
                try:
                    cur.execute(sql)
                    self.autocomplete_data[key] = [str(row[0]) for row in cur.fetchall() if row[0] is not None]
                except Exception:
                    self.conn.rollback()
            cur.close()
            self.filter_value_combo["values"] = self.autocomplete_data.get(self.filter_field_var.get(), [])
        except Exception:
            try:
                self.conn.rollback()
            except Exception:
                pass

    def build_filter_condition(self, aliases=True):
        """Возвращает SQL-условия и параметры для запросов с алиасами g/s/d/t."""
        conditions = []
        params = []

        field = self.filter_field_var.get()
        value = self.filter_value_var.get().strip()
        if value:
            field_map = {
                "группа": "g.название" if aliases else "название",
                "фамилия": "s.фамилия" if aliases else "фамилия",
                "предмет": "d.название" if aliases else "название",
                "дисциплина": "d.название" if aliases else "название",
                "факультет": "g.факультет" if aliases else "факультет",
                "преподаватель": "t.фамилия" if aliases else "фамилия",
            }
            db_field = field_map.get(field)
            if db_field:
                conditions.append(f"{db_field} ILIKE %s")
                params.append(f"%{value}%")

        search_text = self.search_var.get().strip()
        if search_text:
            similarity = self.get_similarity()
            conditions.append(
                "(" 
                "similarity(g.название, %s) >= %s OR "
                "similarity(s.фамилия, %s) >= %s OR "
                "similarity(d.название, %s) >= %s OR "
                "similarity(t.фамилия, %s) >= %s"
                ")"
            )
            params.extend([search_text, similarity, search_text, similarity, search_text, similarity, search_text, similarity])

        if conditions:
            return " AND " + " AND ".join(conditions), params
        return "", []

    def execute(self, sql, params=None, title=None, fetch=True):
        if not self.conn:
            return "Нет подключения к БД"
        params = params or []
        try:
            cur = self.conn.cursor()
            cur.execute(sql, params)
            self.last_result_rows = []
            self.last_result_cols = []

            if fetch and cur.description:
                rows = cur.fetchall()
                cols = [d[0] for d in cur.description]
                cur.close()
                self.conn.commit()
                self.last_result_rows = rows
                self.last_result_cols = cols
                return self.format_table(rows, cols, title=title)

            affected = cur.rowcount
            cur.close()
            self.conn.commit()
            self.load_autocomplete_data()
            self.load_stats()
            return f"Выполнено. Затронуто строк: {affected if affected is not None else 0}\n"
        except Exception as e:
            try:
                self.conn.rollback()
            except Exception:
                pass
            return f"Ошибка: {e}\n"

    def execute_and_display(self, sql, params=None, title=None, status=None, fetch=True):
        result = self.execute(sql, params=params, title=title, fetch=fetch)
        self.display(result)
        if status:
            self.set_status(status)
        return result

    def format_table(self, rows, cols, title=None, max_rows=1000):
        if not rows:
            return (f"{title}\n\n" if title else "") + "Нет данных\n"

        # Преобразуем значения для красивого вывода.
        clean_rows = []
        for row in rows[:max_rows]:
            clean = []
            for value in row:
                if value is None:
                    clean.append("")
                else:
                    text = str(value)
                    if len(text) > 60:
                        text = text[:57] + "..."
                    clean.append(text)
            clean_rows.append(clean)

        widths = [len(str(c)) for c in cols]
        for row in clean_rows:
            for i, value in enumerate(row):
                widths[i] = max(widths[i], len(value))
        widths = [min(max(w, 5), 60) for w in widths]

        lines = []
        if title:
            lines.append(str(title))
            lines.append("=" * min(max(len(str(title)), 10), 100))

        top = "┌" + "┬".join("─" * (w + 2) for w in widths) + "┐"
        sep = "├" + "┼".join("─" * (w + 2) for w in widths) + "┤"
        bottom = "└" + "┴".join("─" * (w + 2) for w in widths) + "┘"
        lines.append(top)
        lines.append("│" + "│".join(f" {str(cols[i])[:widths[i]].ljust(widths[i])} " for i in range(len(cols))) + "│")
        lines.append(sep)
        for row in clean_rows:
            lines.append("│" + "│".join(f" {row[i][:widths[i]].ljust(widths[i])} " for i in range(len(cols))) + "│")
        if len(rows) > max_rows:
            lines.append(sep)
            lines.append(f"│ Показано {max_rows} из {len(rows)} строк".ljust(len(top) - 1) + "│")
        lines.append(bottom)
        lines.append(f"Всего строк: {len(rows)}")
        return "\n".join(lines) + "\n"

    # ------------------------------------------------------------------
    # Статистика / рейтинги
    # ------------------------------------------------------------------
    def load_stats(self):
        if not self.conn or not hasattr(self, "stats_label"):
            return
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM СТУДЕНТЫ")
            students = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM УСПЕВАЕМОСТЬ")
            grades = cur.fetchone()[0]
            cur.close()
            self.conn.commit()
            self.stats_label.config(text=f"Студентов: {students} | Оценок: {grades}")
        except Exception:
            try:
                self.conn.rollback()
            except Exception:
                pass

    def top_students(self):
        self.current_report = "top"
        limit = self.get_limit()
        cond, params = self.build_filter_condition()
        sql = f"""
            SELECT s.фамилия, s.имя, g.название AS группа,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
                   COUNT(*) AS оценок
            FROM СТУДЕНТЫ s
            JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
            JOIN ГРУППЫ g ON g.код = u.группа
            JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
            LEFT JOIN ПРЕПОДАВАТЕЛИ t ON t.код = u.преподаватель
            WHERE 1=1 {cond}
            GROUP BY s.код, s.фамилия, s.имя, g.название
            ORDER BY средний_балл DESC, оценок DESC
            LIMIT %s
        """
        self.execute_and_display(sql, params + [limit], title=f"Топ {limit} студентов", status="Топ студентов")

    def weak_students(self):
        self.current_report = "weak"
        limit = self.get_limit()
        cond, params = self.build_filter_condition()
        sql = f"""
            SELECT s.фамилия, s.имя, g.название AS группа,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
                   COUNT(*) AS оценок
            FROM СТУДЕНТЫ s
            JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
            JOIN ГРУППЫ g ON g.код = u.группа
            JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
            LEFT JOIN ПРЕПОДАВАТЕЛИ t ON t.код = u.преподаватель
            WHERE 1=1 {cond}
            GROUP BY s.код, s.фамилия, s.имя, g.название
            ORDER BY средний_балл ASC, оценок DESC
            LIMIT %s
        """
        self.execute_and_display(sql, params + [limit], title=f"Худшие {limit} студентов", status="Худшие студенты")

    def top_teachers(self):
        self.current_report = "teacher"
        limit = self.get_limit()
        cond, params = self.build_filter_condition()
        sql = f"""
            SELECT t.фамилия, t.имя,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
                   COUNT(*) AS оценок
            FROM ПРЕПОДАВАТЕЛИ t
            JOIN УСПЕВАЕМОСТЬ u ON u.преподаватель = t.код
            JOIN ГРУППЫ g ON g.код = u.группа
            JOIN СТУДЕНТЫ s ON s.код = u.студент
            JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
            WHERE 1=1 {cond}
            GROUP BY t.код, t.фамилия, t.имя
            ORDER BY средний_балл DESC, оценок DESC
            LIMIT %s
        """
        self.execute_and_display(sql, params + [limit], title=f"Топ {limit} преподавателей", status="Топ преподавателей")

    def db_stats(self):
        sql = """
            SELECT 'СТУДЕНТЫ' AS таблица, COUNT(*) AS записей FROM СТУДЕНТЫ
            UNION ALL SELECT 'ГРУППЫ', COUNT(*) FROM ГРУППЫ
            UNION ALL SELECT 'ПРЕПОДАВАТЕЛИ', COUNT(*) FROM ПРЕПОДАВАТЕЛИ
            UNION ALL SELECT 'ДИСЦИПЛИНЫ', COUNT(*) FROM ДИСЦИПЛИНЫ
            UNION ALL SELECT 'УСПЕВАЕМОСТЬ', COUNT(*) FROM УСПЕВАЕМОСТЬ
            ORDER BY таблица
        """
        self.execute_and_display(sql, title="Сводная статистика по таблицам", status="Статистика БД")

    # ------------------------------------------------------------------
    # Основные задачи ./h и ./PYTHON
    # ------------------------------------------------------------------
    def season_expr(self):
        return """
            CASE
                WHEN EXTRACT(MONTH FROM u.дата) IN (12, 1, 2) THEN 'Зима'
                WHEN EXTRACT(MONTH FROM u.дата) IN (3, 4, 5) THEN 'Весна'
                WHEN EXTRACT(MONTH FROM u.дата) IN (6, 7, 8) THEN 'Лето'
                WHEN EXTRACT(MONTH FROM u.дата) IN (9, 10, 11) THEN 'Осень'
                ELSE 'Без даты'
            END
        """

    def task1_avg_by_season(self):
        sql = f"""
            SELECT {self.season_expr()} AS сезон,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
                   COUNT(*) AS оценок
            FROM УСПЕВАЕМОСТЬ u
            GROUP BY сезон
            ORDER BY CASE сезон
                WHEN 'Зима' THEN 1 WHEN 'Весна' THEN 2 WHEN 'Лето' THEN 3 WHEN 'Осень' THEN 4 ELSE 5 END
        """
        self.execute_and_display(sql, title="task1: средний балл по сезонам", status="task1")

    def task2_faculty_season(self):
        sql = f"""
            SELECT g.факультет,
                   {self.season_expr()} AS сезон,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
                   COUNT(*) AS оценок
            FROM УСПЕВАЕМОСТЬ u
            JOIN ГРУППЫ g ON g.код = u.группа
            GROUP BY g.факультет, сезон
            ORDER BY g.факультет, сезон
        """
        self.execute_and_display(sql, title="task2: средний балл по факультетам и сезонам", status="task2")

    def task3_day_teacher(self):
        sql = """
            SELECT TRIM(TO_CHAR(u.дата, 'TMDay')) AS день_недели,
                   t.фамилия AS преподаватель,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
                   COUNT(*) AS оценок
            FROM УСПЕВАЕМОСТЬ u
            JOIN ПРЕПОДАВАТЕЛИ t ON t.код = u.преподаватель
            WHERE u.дата IS NOT NULL
            GROUP BY EXTRACT(ISODOW FROM u.дата), день_недели, t.фамилия
            ORDER BY EXTRACT(ISODOW FROM u.дата), средний_балл DESC
        """
        self.execute_and_display(sql, title="task3: средний балл по дням недели и преподавателям", status="task3")

    def task4_subject_for_day(self):
        day = self.date_var.get().strip()
        if not day:
            day = self.ask_text("Дата", "Введите дату в формате YYYY-MM-DD:")
        if not day:
            return
        sql = """
            SELECT d.название AS дисциплина,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
                   COUNT(*) AS оценок
            FROM УСПЕВАЕМОСТЬ u
            JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
            WHERE u.дата = %s::date
            GROUP BY d.код, d.название
            ORDER BY средний_балл DESC
        """
        self.execute_and_display(sql, [day], title=f"task4: средний балл по дисциплинам за {day}", status="task4")

    def python_task1_report(self):
        cond, params = self.build_filter_condition()
        sql = f"""
            SELECT g.название AS группа,
                   d.название AS дисциплина,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
                   MIN(u.оценка) AS минимум,
                   MAX(u.оценка) AS максимум,
                   COUNT(*) AS оценок
            FROM УСПЕВАЕМОСТЬ u
            JOIN ГРУППЫ g ON g.код = u.группа
            JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
            JOIN СТУДЕНТЫ s ON s.код = u.студент
            LEFT JOIN ПРЕПОДАВАТЕЛИ t ON t.код = u.преподаватель
            WHERE 1=1 {cond}
            GROUP BY g.название, d.название
            ORDER BY g.название, d.название
        """
        self.execute_and_display(sql, params, title="./PYTHON task1: отчёт группы × дисциплины", status="PYTHON task1")

    def python_task2_pivot(self):
        cond, params = self.build_filter_condition()
        sql = f"""
            SELECT g.название AS группа,
                   d.название AS дисциплина,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл
            FROM УСПЕВАЕМОСТЬ u
            JOIN ГРУППЫ g ON g.код = u.группа
            JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
            JOIN СТУДЕНТЫ s ON s.код = u.студент
            LEFT JOIN ПРЕПОДАВАТЕЛИ t ON t.код = u.преподаватель
            WHERE 1=1 {cond}
            GROUP BY g.название, d.название
            ORDER BY g.название, d.название
        """
        if not self.conn:
            self.display("Нет подключения к БД")
            return
        try:
            cur = self.conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            cur.close()
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            self.display(f"Ошибка: {e}")
            return

        if not rows:
            self.display("Нет данных")
            return

        groups = sorted({r[0] for r in rows})
        subjects = sorted({r[1] for r in rows})
        values = {(r[0], r[1]): r[2] for r in rows}
        cols = ["группа"] + subjects
        matrix = []
        for group in groups:
            matrix.append([group] + [values.get((group, subj), "") for subj in subjects])
        self.last_result_cols = cols
        self.last_result_rows = matrix
        self.display(self.format_table(matrix, cols, title="./PYTHON task2: сводная таблица группы × дисциплины"))
        self.set_status("Сводная таблица")

    # ------------------------------------------------------------------
    # Просмотр таблиц и структуры
    # ------------------------------------------------------------------
    def view_table(self, table, limit=500):
        allowed = {"СТУДЕНТЫ", "ГРУППЫ", "ПРЕПОДАВАТЕЛИ", "ДИСЦИПЛИНЫ", "УСПЕВАЕМОСТЬ"}
        if table not in allowed:
            messagebox.showerror("Ошибка", "Недопустимая таблица")
            return
        if table == "УСПЕВАЕМОСТЬ":
            sql = """
                SELECT u.код_записи, s.фамилия AS студент, g.название AS группа,
                       d.название AS дисциплина, t.фамилия AS преподаватель,
                       u.оценка, u.дата
                FROM УСПЕВАЕМОСТЬ u
                LEFT JOIN СТУДЕНТЫ s ON s.код = u.студент
                LEFT JOIN ГРУППЫ g ON g.код = u.группа
                LEFT JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
                LEFT JOIN ПРЕПОДАВАТЕЛИ t ON t.код = u.преподаватель
                ORDER BY u.дата DESC NULLS LAST, u.код_записи DESC
                LIMIT %s
            """
            params = [limit]
        else:
            sql = f"SELECT * FROM {table} ORDER BY 1 LIMIT %s"
            params = [limit]
        title = "ПРЕДМЕТЫ / ДИСЦИПЛИНЫ" if table == "ДИСЦИПЛИНЫ" else table
        self.execute_and_display(sql, params, title=f"Таблица: {title}", status=f"Просмотр {title}")

    def show_structure(self):
        sql = """
            SELECT table_name AS таблица,
                   column_name AS столбец,
                   data_type AS тип,
                   is_nullable AS nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """
        self.execute_and_display(sql, title="Структура БД", status="Структура БД")

    # ------------------------------------------------------------------
    # JOIN / ДО-ПОСЛЕ
    # ------------------------------------------------------------------
    def demo_inner_join(self):
        sql = """
            SELECT s.фамилия AS студент, g.название AS группа,
                   d.название AS дисциплина, t.фамилия AS преподаватель,
                   u.оценка, u.дата
            FROM УСПЕВАЕМОСТЬ u
            INNER JOIN СТУДЕНТЫ s ON s.код = u.студент
            INNER JOIN ГРУППЫ g ON g.код = u.группа
            INNER JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
            INNER JOIN ПРЕПОДАВАТЕЛИ t ON t.код = u.преподаватель
            ORDER BY u.дата DESC NULLS LAST
            LIMIT 100
        """
        self.execute_and_display(sql, title="Демонстрация INNER JOIN", status="INNER JOIN")

    def demo_left_join(self):
        sql = """
            SELECT s.код, s.фамилия, s.имя,
                   COUNT(u.код_записи) AS количество_оценок,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл
            FROM СТУДЕНТЫ s
            LEFT JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
            GROUP BY s.код, s.фамилия, s.имя
            ORDER BY количество_оценок ASC, s.код
            LIMIT 100
        """
        self.execute_and_display(sql, title="Демонстрация LEFT JOIN", status="LEFT JOIN")

    def demo_cross_join(self):
        sql = """
            SELECT g.название AS группа, d.название AS дисциплина
            FROM ГРУППЫ g
            CROSS JOIN ДИСЦИПЛИНЫ d
            ORDER BY g.название, d.название
            LIMIT 150
        """
        self.execute_and_display(sql, title="Демонстрация CROSS JOIN", status="CROSS JOIN")

    def show_update_before(self):
        sql = "SELECT * FROM СТУДЕНТЫ WHERE код = 1"
        self.execute_and_display(sql, title="ДО UPDATE: студент код=1", status="ДО UPDATE")

    def show_update_after(self):
        sql = "SELECT * FROM СТУДЕНТЫ WHERE код = 1"
        self.execute_and_display(sql, title="ПОСЛЕ UPDATE: студент код=1", status="ПОСЛЕ UPDATE")

    def show_delete_before(self):
        sql = "SELECT * FROM СТУДЕНТЫ WHERE код = 50"
        self.execute_and_display(sql, title="ДО DELETE: студент код=50", status="ДО DELETE")

    def show_delete_after(self):
        sql = "SELECT * FROM СТУДЕНТЫ WHERE код = 50"
        self.execute_and_display(sql, title="ПОСЛЕ DELETE: студент код=50", status="ПОСЛЕ DELETE")

    # ------------------------------------------------------------------
    # Аналитика и графики
    # ------------------------------------------------------------------
    def grade_distribution(self):
        sql = """
            SELECT оценка, COUNT(*) AS количество
            FROM УСПЕВАЕМОСТЬ
            GROUP BY оценка
            ORDER BY оценка
        """
        self.execute_and_display(sql, title="Распределение оценок", status="Распределение оценок")

    def performance_by_course(self):
        sql = """
            SELECT g.курс,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
                   COUNT(*) AS оценок
            FROM УСПЕВАЕМОСТЬ u
            JOIN ГРУППЫ g ON g.код = u.группа
            GROUP BY g.курс
            ORDER BY g.курс
        """
        self.execute_and_display(sql, title="Успеваемость по курсам", status="Успеваемость по курсам")

    def fetch_rows(self, sql, params=None):
        if not self.conn:
            raise RuntimeError("Нет подключения к БД")
        cur = self.conn.cursor()
        cur.execute(sql, params or [])
        rows = cur.fetchall()
        cur.close()
        self.conn.commit()
        return rows

    def show_dynamics(self, save_path=None):
        self.current_report = "dynamics"
        cond, params = self.build_filter_condition()
        sql = f"""
            SELECT DATE_TRUNC('month', u.дата) AS месяц,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл
            FROM УСПЕВАЕМОСТЬ u
            JOIN ГРУППЫ g ON g.код = u.группа
            JOIN СТУДЕНТЫ s ON s.код = u.студент
            JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
            LEFT JOIN ПРЕПОДАВАТЕЛИ t ON t.код = u.преподаватель
            WHERE u.дата IS NOT NULL {cond}
            GROUP BY DATE_TRUNC('month', u.дата)
            ORDER BY месяц
        """
        try:
            rows = self.fetch_rows(sql, params)
            if not rows:
                messagebox.showinfo("Нет данных", "Недостаточно данных для графика")
                return
            months = [r[0] for r in rows]
            grades = [float(r[1]) for r in rows]
            fig, ax = plt.subplots(figsize=(9, 5))
            ax.plot(months, grades, marker="o", linewidth=2)
            ax.set_title("Динамика успеваемости по месяцам")
            ax.set_xlabel("Дата")
            ax.set_ylabel("Средний балл")
            ax.set_ylim(2, 5)
            ax.grid(True, alpha=0.3)
            fig.autofmt_xdate()
            fig.tight_layout()
            if save_path:
                fig.savefig(save_path, dpi=150)
                plt.close(fig)
                return
            self.show_figure(fig, "График динамики успеваемости")
            self.set_status("График динамики")
        except Exception as e:
            try:
                self.conn.rollback()
            except Exception:
                pass
            messagebox.showerror("Ошибка", str(e))

    def show_pie(self, save_path=None):
        self.current_report = "pie"
        cond, params = self.build_filter_condition()
        sql = f"""
            SELECT g.название AS группа,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл
            FROM ГРУППЫ g
            JOIN УСПЕВАЕМОСТЬ u ON u.группа = g.код
            JOIN СТУДЕНТЫ s ON s.код = u.студент
            JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
            LEFT JOIN ПРЕПОДАВАТЕЛИ t ON t.код = u.преподаватель
            WHERE 1=1 {cond}
            GROUP BY g.код, g.название
            ORDER BY средний_балл DESC
            LIMIT 8
        """
        try:
            rows = self.fetch_rows(sql, params)
            if not rows:
                messagebox.showinfo("Нет данных", "Недостаточно данных для диаграммы")
                return
            labels = [str(r[0]) for r in rows]
            sizes = [float(r[1]) for r in rows]
            fig, ax = plt.subplots(figsize=(7, 6))
            ax.pie(sizes, labels=labels, autopct="%1.1f%%")
            ax.set_title("Средний балл по группам")
            fig.tight_layout()
            if save_path:
                fig.savefig(save_path, dpi=150)
                plt.close(fig)
                return
            self.show_figure(fig, "Круговая диаграмма")
            self.set_status("Круговая диаграмма")
        except Exception as e:
            try:
                self.conn.rollback()
            except Exception:
                pass
            messagebox.showerror("Ошибка", str(e))

    def show_figure(self, fig, title):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("900x620")
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def save_all_charts(self):
        folder = filedialog.askdirectory(title="Выберите папку для графиков")
        if not folder:
            return
        folder = Path(folder)
        try:
            self.show_dynamics(save_path=folder / "task3_chart.png")
            self.show_pie(save_path=folder / "task4_chart.png")
            messagebox.showinfo("Готово", f"Графики сохранены в папку:\n{folder}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    # ------------------------------------------------------------------
    # Запросы с параметрами / редактирование
    # ------------------------------------------------------------------
    def groups_by_faculty(self):
        faculty = self.filter_value_var.get().strip() if self.filter_field_var.get() == "факультет" else ""
        if not faculty:
            faculty = self.ask_text("Факультет", "Введите факультет:")
        if not faculty:
            return
        sql = """
            SELECT код, название, факультет, курс
            FROM ГРУППЫ
            WHERE факультет ILIKE %s
            ORDER BY название
        """
        self.execute_and_display(sql, [f"%{faculty}%"], title=f"Группы по факультету: {faculty}", status="Группы по факультету")

    def search_student(self):
        surname = self.filter_value_var.get().strip() if self.filter_field_var.get() == "фамилия" else ""
        if not surname:
            surname = self.ask_text("Поиск студента", "Введите фамилию или часть фамилии:")
        if not surname:
            return
        sql = """
            SELECT s.код, s.фамилия, s.имя, s.телефон, s.email,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
                   COUNT(u.код_записи) AS оценок
            FROM СТУДЕНТЫ s
            LEFT JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
            WHERE s.фамилия ILIKE %s
            GROUP BY s.код, s.фамилия, s.имя, s.телефон, s.email
            ORDER BY s.фамилия, s.имя
        """
        self.execute_and_display(sql, [f"%{surname}%"], title=f"Поиск студента: {surname}", status="Поиск студента")

    def quick_search_student(self):
        text = self.ask_text("Быстрый поиск", "Введите текст для поиска студента:")
        if not text:
            return
        sql = """
            SELECT код, фамилия, имя, телефон, email
            FROM СТУДЕНТЫ
            WHERE фамилия ILIKE %s OR имя ILIKE %s OR телефон ILIKE %s OR email ILIKE %s
            ORDER BY фамилия, имя
        """
        p = f"%{text}%"
        self.execute_and_display(sql, [p, p, p, p], title=f"Быстрый поиск: {text}", status="Быстрый поиск")

    def quick_group_stats(self):
        group_name = self.filter_value_var.get().strip() if self.filter_field_var.get() == "группа" else ""
        if not group_name:
            group_name = self.ask_text("Группа", "Введите название группы:")
        if not group_name:
            return
        sql = """
            SELECT g.название AS группа,
                   COUNT(DISTINCT s.код) AS студентов,
                   COUNT(u.код_записи) AS оценок,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
                   MIN(u.оценка) AS минимум,
                   MAX(u.оценка) AS максимум
            FROM ГРУППЫ g
            LEFT JOIN УСПЕВАЕМОСТЬ u ON u.группа = g.код
            LEFT JOIN СТУДЕНТЫ s ON s.код = u.студент
            WHERE g.название ILIKE %s
            GROUP BY g.код, g.название
            ORDER BY g.название
        """
        self.execute_and_display(sql, [f"%{group_name}%"], title=f"Статистика группы: {group_name}", status="Статистика группы")

    def update_student_phone(self, default_code=None):
        code = default_code or self.ask_int("Код студента", "Введите код студента:")
        if not code:
            return
        phone = self.ask_text("Телефон", "Введите новый телефон:")
        if phone is None:
            return
        sql = "UPDATE СТУДЕНТЫ SET телефон = %s WHERE код = %s"
        self.execute_and_display(sql, [phone, code], title="Обновление телефона", status="Телефон обновлён", fetch=False)
        self.execute_and_display("SELECT * FROM СТУДЕНТЫ WHERE код = %s", [code], title="Студент после обновления")

    def update_subject(self, default_code=None):
        code = default_code or self.ask_int("Код дисциплины", "Введите код дисциплины:")
        if not code:
            return
        name = self.ask_text("Дисциплина", "Введите новое название дисциплины:")
        if not name:
            return
        sql = "UPDATE ДИСЦИПЛИНЫ SET название = %s WHERE код = %s"
        self.execute_and_display(sql, [name, code], title="Обновление дисциплины", status="Дисциплина обновлена", fetch=False)
        self.execute_and_display("SELECT * FROM ДИСЦИПЛИНЫ WHERE код = %s", [code], title="Дисциплина после обновления")

    def delete_student(self, default_code=None):
        code = default_code or self.ask_int("Удаление студента", "Введите код студента:")
        if not code:
            return
        if not self.confirm("Подтверждение", f"Удалить студента с кодом {code}?\nСначала будут удалены связанные оценки."):
            return
        sql = """
            DELETE FROM УСПЕВАЕМОСТЬ WHERE студент = %s;
            DELETE FROM СТУДЕНТЫ WHERE код = %s;
        """
        self.execute_and_display(sql, [code, code], title="Удаление студента", status="Студент удалён", fetch=False)

    def update_grade(self):
        student = self.ask_int("Студент", "Код студента:")
        subject = self.ask_int("Дисциплина", "Код дисциплины:")
        grade = self.ask_int("Оценка", "Новая оценка:")
        if not student or not subject or grade is None:
            return
        sql = """
            UPDATE УСПЕВАЕМОСТЬ
            SET оценка = %s
            WHERE студент = %s AND дисциплина = %s
        """
        self.execute_and_display(sql, [grade, student, subject], title="Обновление оценки", status="Оценка обновлена", fetch=False)
        self.view_student_grades(student_code=student)

    def insert_student(self):
        surname = self.ask_text("Добавить студента", "Фамилия:")
        if not surname:
            return
        name = self.ask_text("Добавить студента", "Имя:")
        if not name:
            return
        phone = self.ask_text("Добавить студента", "Телефон:", "") or ""
        email = self.ask_text("Добавить студента", "Email:", "") or ""
        sql = """
            INSERT INTO СТУДЕНТЫ (фамилия, имя, телефон, email)
            VALUES (%s, %s, %s, %s)
            RETURNING *
        """
        self.execute_and_display(sql, [surname, name, phone, email], title="Добавлен студент", status="Студент добавлен")

    def insert_subject(self):
        name = self.ask_text("Добавить дисциплину", "Название дисциплины:")
        if not name:
            return
        sql = "INSERT INTO ДИСЦИПЛИНЫ (название) VALUES (%s) RETURNING *"
        self.execute_and_display(sql, [name], title="Добавлена дисциплина", status="Дисциплина добавлена")

    def insert_grade(self):
        student = self.ask_int("Оценка", "Код студента:")
        group = self.ask_int("Оценка", "Код группы:")
        subject = self.ask_int("Оценка", "Код дисциплины:")
        teacher = self.ask_int("Оценка", "Код преподавателя:")
        grade = self.ask_int("Оценка", "Оценка:")
        date = self.ask_text("Оценка", "Дата YYYY-MM-DD:", self.date_var.get())
        if not all([student, group, subject, teacher, grade, date]):
            return
        sql = """
            INSERT INTO УСПЕВАЕМОСТЬ (студент, группа, дисциплина, преподаватель, оценка, дата)
            VALUES (%s, %s, %s, %s, %s, %s::date)
            RETURNING *
        """
        self.execute_and_display(sql, [student, group, subject, teacher, grade, date], title="Добавлена оценка", status="Оценка добавлена")

    def edit_student(self):
        code = self.ask_int("Редактировать студента", "Код студента:")
        if not code:
            return
        surname = self.ask_text("Редактировать студента", "Новая фамилия:")
        name = self.ask_text("Редактировать студента", "Новое имя:")
        phone = self.ask_text("Редактировать студента", "Новый телефон:")
        email = self.ask_text("Редактировать студента", "Новый email:")
        if None in [surname, name, phone, email]:
            return
        sql = """
            UPDATE СТУДЕНТЫ
            SET фамилия = %s, имя = %s, телефон = %s, email = %s
            WHERE код = %s
            RETURNING *
        """
        self.execute_and_display(sql, [surname, name, phone, email, code], title="Студент после редактирования", status="Студент изменён")

    def view_student_grades(self, student_code=None):
        code = student_code or self.ask_int("Успеваемость студента", "Код студента:")
        if not code:
            return
        sql = """
            SELECT s.фамилия, s.имя, g.название AS группа, d.название AS дисциплина,
                   t.фамилия AS преподаватель, u.оценка, u.дата
            FROM УСПЕВАЕМОСТЬ u
            JOIN СТУДЕНТЫ s ON s.код = u.студент
            JOIN ГРУППЫ g ON g.код = u.группа
            JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
            LEFT JOIN ПРЕПОДАВАТЕЛИ t ON t.код = u.преподаватель
            WHERE s.код = %s
            ORDER BY u.дата DESC NULLS LAST
        """
        self.execute_and_display(sql, [code], title=f"Успеваемость студента код={code}", status="Успеваемость студента")

    def raise_grades_for_students(self):
        sql = """
            UPDATE УСПЕВАЕМОСТЬ
            SET оценка = LEAST(5, оценка + 1)
            WHERE студент IN (1, 2, 3)
            RETURNING *
        """
        if not self.confirm("Подтверждение", "Повысить оценки студентам 1, 2, 3 на 1 балл, но не выше 5?"):
            return
        self.execute_and_display(sql, title="Повышение оценок студентам 1,2,3", status="Оценки повышены")

    def delete_bad_grades(self):
        if not self.confirm("Подтверждение", "Удалить все оценки 2?"):
            return
        sql = "DELETE FROM УСПЕВАЕМОСТЬ WHERE оценка = 2"
        self.execute_and_display(sql, title="Удаление оценок 2", status="Оценки 2 удалены", fetch=False)

    def promote_groups_course(self):
        if not self.confirm("Подтверждение", "Повысить курс всем группам на 1?"):
            return
        sql = "UPDATE ГРУППЫ SET курс = курс + 1 RETURNING *"
        self.execute_and_display(sql, title="Повышение курса групп", status="Курс групп повышен")

    def update_teacher_position(self):
        code = self.ask_int("Преподаватель", "Код преподавателя:")
        if not code:
            return
        position = self.ask_text("Должность", "Новая должность:")
        if not position:
            return
        sql = "UPDATE ПРЕПОДАВАТЕЛИ SET должность = %s WHERE код = %s RETURNING *"
        self.execute_and_display(sql, [position, code], title="Преподаватель после изменения", status="Должность изменена")

    def copy_to_archive(self):
        sql = """
            CREATE TABLE IF NOT EXISTS АРХИВ_УСПЕВАЕМОСТИ AS
            SELECT * FROM УСПЕВАЕМОСТЬ WHERE 1=0;

            INSERT INTO АРХИВ_УСПЕВАЕМОСТИ
            SELECT * FROM УСПЕВАЕМОСТЬ
            WHERE дата < CURRENT_DATE - INTERVAL '1 year'
            ON CONFLICT DO NOTHING;
        """
        self.execute_and_display(sql, title="INSERT SELECT: копирование в архив", status="Архив заполнен", fetch=False)

    # ------------------------------------------------------------------
    # Представления
    # ------------------------------------------------------------------
    def create_user_view(self):
        sql = """
            CREATE OR REPLACE VIEW v_успеваемость AS
            SELECT u.код_записи,
                   s.фамилия AS студент_фамилия,
                   s.имя AS студент_имя,
                   g.название AS группа,
                   g.факультет,
                   d.название AS дисциплина,
                   t.фамилия AS преподаватель,
                   u.оценка,
                   u.дата
            FROM УСПЕВАЕМОСТЬ u
            JOIN СТУДЕНТЫ s ON s.код = u.студент
            JOIN ГРУППЫ g ON g.код = u.группа
            JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
            LEFT JOIN ПРЕПОДАВАТЕЛИ t ON t.код = u.преподаватель;
        """
        self.execute_and_display(sql, title="Создание пользовательского представления", status="Представление создано", fetch=False)

    def create_tech_view(self):
        sql = """
            CREATE OR REPLACE VIEW v_техническая_успеваемость AS
            SELECT u.код_записи,
                   u.студент,
                   u.группа,
                   u.дисциплина,
                   u.преподаватель,
                   u.оценка,
                   u.дата
            FROM УСПЕВАЕМОСТЬ u;
        """
        self.execute_and_display(sql, title="Создание технологического представления", status="Технологическое представление создано", fetch=False)

    def create_views(self):
        self.create_user_view()
        self.create_tech_view()
        self.check_views()

    def check_views(self):
        sql = """
            SELECT table_name AS представление
            FROM information_schema.views
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        self.execute_and_display(sql, title="Проверка представлений", status="Представления")

    # ------------------------------------------------------------------
    # Подзапросы
    # ------------------------------------------------------------------
    def sub_110_avg_deviation(self):
        sql = """
            SELECT s.фамилия, s.имя,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
                   ROUND((AVG(u.оценка) - (SELECT AVG(оценка) FROM УСПЕВАЕМОСТЬ))::numeric, 2) AS отклонение
            FROM СТУДЕНТЫ s
            JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
            GROUP BY s.код, s.фамилия, s.имя
            ORDER BY отклонение DESC
        """
        self.execute_and_display(sql, title="110: отклонение среднего балла", status="Подзапрос 110")

    def sub_111_teacher_rating(self):
        sql = """
            SELECT t.фамилия, t.имя,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл
            FROM ПРЕПОДАВАТЕЛИ t
            JOIN УСПЕВАЕМОСТЬ u ON u.преподаватель = t.код
            GROUP BY t.код, t.фамилия, t.имя
            HAVING AVG(u.оценка) > (SELECT AVG(оценка) FROM УСПЕВАЕМОСТЬ)
            ORDER BY средний_балл DESC
        """
        self.execute_and_display(sql, title="111: рейтинг преподавателей выше среднего", status="Подзапрос 111")

    def sub_112_students_above_avg(self):
        sql = """
            SELECT s.фамилия, s.имя,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл
            FROM СТУДЕНТЫ s
            JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
            GROUP BY s.код, s.фамилия, s.имя
            HAVING AVG(u.оценка) > (SELECT AVG(оценка) FROM УСПЕВАЕМОСТЬ)
            ORDER BY средний_балл DESC
        """
        self.execute_and_display(sql, title="112: студенты выше среднего", status="Подзапрос 112")

    def sub_113_faculty_stats(self):
        sql = """
            SELECT g.факультет,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
                   COUNT(*) AS оценок,
                   COUNT(DISTINCT u.студент) AS студентов
            FROM ГРУППЫ g
            JOIN УСПЕВАЕМОСТЬ u ON u.группа = g.код
            GROUP BY g.факультет
            ORDER BY средний_балл DESC
        """
        self.execute_and_display(sql, title="113: статистика по факультетам", status="Подзапрос 113")

    def sub_114_top3_faculty(self):
        sql = """
            WITH student_avg AS (
                SELECT g.факультет, s.фамилия, s.имя,
                       ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
                       ROW_NUMBER() OVER (PARTITION BY g.факультет ORDER BY AVG(u.оценка) DESC) AS rn
                FROM УСПЕВАЕМОСТЬ u
                JOIN СТУДЕНТЫ s ON s.код = u.студент
                JOIN ГРУППЫ g ON g.код = u.группа
                GROUP BY g.факультет, s.код, s.фамилия, s.имя
            )
            SELECT факультет, фамилия, имя, средний_балл
            FROM student_avg
            WHERE rn <= 3
            ORDER BY факультет, средний_балл DESC
        """
        self.execute_and_display(sql, title="114: топ-3 студента на факультете", status="Подзапрос 114")

    def sub_115_above_subject_avg(self):
        subject = self.filter_value_var.get().strip() if self.filter_field_var.get() in ("предмет", "дисциплина") else ""
        if not subject:
            subject = self.ask_text("Дисциплина", "Введите название дисциплины:")
        if not subject:
            return
        sql = """
            SELECT s.фамилия, s.имя, d.название AS дисциплина, u.оценка
            FROM УСПЕВАЕМОСТЬ u
            JOIN СТУДЕНТЫ s ON s.код = u.студент
            JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
            WHERE d.название ILIKE %s
              AND u.оценка > (
                  SELECT AVG(u2.оценка)
                  FROM УСПЕВАЕМОСТЬ u2
                  WHERE u2.дисциплина = d.код
              )
            ORDER BY u.оценка DESC, s.фамилия
        """
        self.execute_and_display(sql, [f"%{subject}%"], title=f"115: оценки выше среднего по дисциплине {subject}", status="Подзапрос 115")

    def sub_116_no_bad_grades(self):
        sql = """
            SELECT s.код, s.фамилия, s.имя,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл
            FROM СТУДЕНТЫ s
            JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
            WHERE NOT EXISTS (
                SELECT 1 FROM УСПЕВАЕМОСТЬ u2
                WHERE u2.студент = s.код AND u2.оценка IN (2, 3)
            )
            GROUP BY s.код, s.фамилия, s.имя
            ORDER BY средний_балл DESC
        """
        self.execute_and_display(sql, title="116: студенты без троек и двоек", status="Подзапрос 116")

    def sub_117_best_all(self):
        sql = """
            SELECT s.код, s.фамилия, s.имя,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл
            FROM СТУДЕНТЫ s
            JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
            GROUP BY s.код, s.фамилия, s.имя
            HAVING AVG(u.оценка) >= ALL (
                SELECT AVG(u2.оценка)
                FROM УСПЕВАЕМОСТЬ u2
                GROUP BY u2.студент
            )
        """
        self.execute_and_display(sql, title="117: лучшие студенты ALL", status="Подзапрос 117")

    def sub_199_all(self):
        reports = [
            ("110", self.sub_110_avg_deviation),
            ("111", self.sub_111_teacher_rating),
            ("112", self.sub_112_students_above_avg),
            ("113", self.sub_113_faculty_stats),
            ("114", self.sub_114_top3_faculty),
            ("116", self.sub_116_no_bad_grades),
            ("117", self.sub_117_best_all),
        ]
        self.display("Выполнение подзапросов 110-117\n\n")
        for name, func in reports:
            func()
            self.append_display("\n" + "-" * 80 + "\n")

    # ------------------------------------------------------------------
    # Функции БД
    # ------------------------------------------------------------------
    def create_pg_trgm(self):
        sql = "CREATE EXTENSION IF NOT EXISTS pg_trgm"
        self.execute_and_display(sql, title="Создание расширения pg_trgm", status="pg_trgm готово", fetch=False)

    def create_functions(self):
        sql = f"""
            CREATE OR REPLACE FUNCTION fn_students_above_threshold(p_threshold numeric)
            RETURNS TABLE(фамилия text, имя text, средний_балл numeric) AS $$
                SELECT s.фамилия::text, s.имя::text,
                       ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл
                FROM СТУДЕНТЫ s
                JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
                GROUP BY s.код, s.фамилия, s.имя
                HAVING AVG(u.оценка) > p_threshold
                ORDER BY средний_балл DESC;
            $$ LANGUAGE sql;

            CREATE OR REPLACE FUNCTION fn_faculty_season_avg()
            RETURNS TABLE(факультет text, сезон text, средний_балл numeric, оценок bigint) AS $$
                SELECT g.факультет::text,
                       {self.season_expr()}::text AS сезон,
                       ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
                       COUNT(*) AS оценок
                FROM УСПЕВАЕМОСТЬ u
                JOIN ГРУППЫ g ON g.код = u.группа
                GROUP BY g.факультет, сезон
                ORDER BY g.факультет, сезон;
            $$ LANGUAGE sql;
        """
        self.execute_and_display(sql, title="Создание SQL-функций", status="Функции созданы", fetch=False)

    def func_students_above_threshold(self):
        threshold = self.get_threshold()
        sql = "SELECT * FROM fn_students_above_threshold(%s)"
        result = self.execute(sql, [threshold], title=f"201: студенты со средним баллом выше {threshold}")
        if "function fn_students_above_threshold" in result or "не существует" in result:
            self.create_functions()
            result = self.execute(sql, [threshold], title=f"201: студенты со средним баллом выше {threshold}")
        self.display(result)
        self.set_status("Функция 201")

    def func_faculty_season(self):
        sql = "SELECT * FROM fn_faculty_season_avg()"
        result = self.execute(sql, title="202: средний балл по факультетам и сезонам")
        if "function fn_faculty_season_avg" in result or "не существует" in result:
            self.create_functions()
            result = self.execute(sql, title="202: средний балл по факультетам и сезонам")
        self.display(result)
        self.set_status("Функция 202")

    def functions_run_all(self):
        self.create_functions()
        self.func_students_above_threshold()
        self.func_faculty_season()
        self.python_task2_pivot()

    # ------------------------------------------------------------------
    # Администрирование / файлы
    # ------------------------------------------------------------------
    def export_current_csv(self):
        if not getattr(self, "last_result_rows", None) or not getattr(self, "last_result_cols", None):
            messagebox.showinfo("Нет данных", "Сначала выполните отчёт или запрос")
            return
        filename = filedialog.asksaveasfilename(
            title="Сохранить текущий отчёт",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All files", "*.*")],
        )
        if not filename:
            return
        try:
            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(self.last_result_cols)
                writer.writerows(self.last_result_rows)
            messagebox.showinfo("Готово", f"Сохранено: {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def export_all_csv(self):
        folder = filedialog.askdirectory(title="Выберите папку для экспорта CSV")
        if not folder:
            return
        if not self.conn:
            messagebox.showerror("Ошибка", "Нет подключения к БД")
            return
        tables = ["СТУДЕНТЫ", "ГРУППЫ", "ПРЕПОДАВАТЕЛИ", "ДИСЦИПЛИНЫ", "УСПЕВАЕМОСТЬ"]
        folder = Path(folder)
        try:
            cur = self.conn.cursor()
            exported = []
            for table in tables:
                cur.execute(f"SELECT * FROM {table}")
                rows = cur.fetchall()
                cols = [d[0] for d in cur.description]
                path = folder / f"{table}.csv"
                with open(path, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(cols)
                    writer.writerows(rows)
                exported.append(str(path))
            cur.close()
            self.conn.commit()
            self.display("Экспортированы файлы:\n" + "\n".join(exported))
            self.set_status("Экспорт всех таблиц")
        except Exception as e:
            try:
                self.conn.rollback()
            except Exception:
                pass
            messagebox.showerror("Ошибка", str(e))

    def backup_db(self):
        filename = filedialog.asksaveasfilename(
            title="Сохранить бэкап",
            defaultextension=".dump",
            filetypes=[("PostgreSQL dump", "*.dump"), ("All files", "*.*")],
        )
        if not filename:
            return
        try:
            cmd = ["pg_dump", "-Fc", "-f", filename]
            if DB_CONFIG.get("host"):
                cmd.extend(["-h", str(DB_CONFIG["host"])])
            if DB_CONFIG.get("port"):
                cmd.extend(["-p", str(DB_CONFIG["port"])])
            if DB_CONFIG.get("user"):
                cmd.extend(["-U", str(DB_CONFIG["user"])])
            cmd.append(str(DB_CONFIG.get("dbname") or DB_CONFIG.get("database")))
            env = os.environ.copy()
            if DB_CONFIG.get("password"):
                env["PGPASSWORD"] = str(DB_CONFIG["password"])
            proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if proc.returncode == 0:
                messagebox.showinfo("Готово", f"Бэкап создан:\n{filename}")
                self.set_status("Бэкап создан")
            else:
                messagebox.showerror("Ошибка pg_dump", proc.stderr or proc.stdout)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def archive_old_records(self):
        years = self.ask_int("Архивация", "Архивировать записи старше скольких лет?", initial=1)
        if not years:
            return
        if not self.confirm("Подтверждение", f"Перенести в архив записи старше {years} лет и удалить их из УСПЕВАЕМОСТЬ?"):
            return
        sql = """
            CREATE TABLE IF NOT EXISTS АРХИВ_УСПЕВАЕМОСТИ AS
            SELECT * FROM УСПЕВАЕМОСТЬ WHERE 1=0;

            INSERT INTO АРХИВ_УСПЕВАЕМОСТИ
            SELECT * FROM УСПЕВАЕМОСТЬ
            WHERE дата < CURRENT_DATE - (%s || ' years')::interval;

            DELETE FROM УСПЕВАЕМОСТЬ
            WHERE дата < CURRENT_DATE - (%s || ' years')::interval;
        """
        self.execute_and_display(sql, [str(years), str(years)], title="Архивация старых записей", status="Архивация выполнена", fetch=False)

    def run_any_sql_file(self):
        filename = filedialog.askopenfilename(
            title="Выберите SQL-файл",
            initialdir=str(self.project_root),
            filetypes=[("SQL files", "*.sql"), ("All files", "*.*")],
        )
        if not filename:
            return
        try:
            text = Path(filename).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = Path(filename).read_text(encoding="cp1251")
        params_text = self.ask_text("Параметры", "Параметры через пробел, если нужны. Можно оставить пустым:", "")
        params = [] if not params_text else params_text.split()

        # Поддержка простых плейсхолдеров psql: :param1, :param2 или $1, $2.
        sql_text = text
        for idx, value in enumerate(params, start=1):
            safe = value.replace("'", "''")
            sql_text = sql_text.replace(f":param{idx}", f"'{safe}'")
            sql_text = sql_text.replace(f"${idx}", f"'{safe}'")

        result = self.execute(sql_text, title=f"SQL-файл: {Path(filename).name}")
        self.display(result)
        self.set_status(f"Выполнен SQL-файл {Path(filename).name}")

    # ------------------------------------------------------------------
    # О программе
    # ------------------------------------------------------------------
    def show_about(self):
        messagebox.showinfo(
            "О программе",
            "ВУЗ: система управления успеваемостью\n"
            "Расширенная версия GUI\n\n"
            "Реализованы основные команды из ./h и ./PYTHON:\n"
            "просмотр, рейтинги, аналитика, JOIN, редактирование,\n"
            "представления, функции, подзапросы, экспорт, бэкап и запуск SQL-файлов."
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = UniversityApp(root)
    root.mainloop()
