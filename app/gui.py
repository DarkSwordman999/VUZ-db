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
- запуск любого SQL-файла;
- полные демонстрации UPDATE/DELETE до-действие-после;
- прямой запуск ./PYTHON all и ./PYTHON save --force.

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
        file_menu.add_command(label="SQL-скрипты проекта", command=self.sql_scripts_manager)
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
        """Панель параметров и понятных фильтров без лишних нерабочих полей."""
        row1 = ttk.Frame(parent)
        row1.pack(fill=tk.X, padx=5, pady=3)

        ttk.Label(row1, text="Количество:").pack(side=tk.LEFT, padx=(0, 4))
        self.limit_var = tk.StringVar(value="10")
        ttk.Spinbox(row1, from_=1, to=500, textvariable=self.limit_var, width=7).pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(row1, text="Порог:").pack(side=tk.LEFT, padx=(0, 4))
        self.threshold_var = tk.StringVar(value="4.0")
        ttk.Entry(row1, textvariable=self.threshold_var, width=8).pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(row1, text="Дата для task4:").pack(side=tk.LEFT, padx=(0, 4))
        self.date_var = tk.StringVar(value="")
        ttk.Entry(row1, textvariable=self.date_var, width=12).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Label(row1, text="YYYY-MM-DD").pack(side=tk.LEFT, padx=(0, 12))

        ttk.Button(row1, text="Сбросить всё", command=self.clear_filters).pack(side=tk.LEFT)

        row2 = ttk.Frame(parent)
        row2.pack(fill=tk.X, padx=5, pady=3)

        ttk.Label(row2, text="Фильтр:").pack(side=tk.LEFT, padx=(0, 4))
        self.filter_field_var = tk.StringVar(value="группа")
        self.filter_field_combo = ttk.Combobox(
            row2,
            textvariable=self.filter_field_var,
            values=[
                "группа",
                "факультет",
                "курс",
                "фамилия",
                "имя студента",
                "предмет",
                "преподаватель",
                "оценка =",
                "оценка >=",
                "оценка <=",
                "дата =",
                "дата >=",
                "дата <=",
            ],
            width=18,
            state="readonly",
        )
        self.filter_field_combo.pack(side=tk.LEFT, padx=(0, 8))
        self.filter_field_combo.bind("<<ComboboxSelected>>", self.on_field_change)

        ttk.Label(row2, text="Значение:").pack(side=tk.LEFT, padx=(0, 4))
        self.filter_value_var = tk.StringVar()
        self.filter_value_entry = ttk.Entry(row2, textvariable=self.filter_value_var, width=30)
        self.filter_value_entry.pack(side=tk.LEFT, padx=(0, 8))
        self.filter_value_entry.bind("<Return>", lambda event: self.apply_filter())

        ttk.Button(row2, text="Применить", command=self.apply_filter).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(row2, text="Сбросить фильтр", command=self.clear_only_filter).pack(side=tk.LEFT)

        row3 = ttk.Frame(parent)
        row3.pack(fill=tk.X, padx=5, pady=3)

        ttk.Label(row3, text="Быстрый поиск:").pack(side=tk.LEFT, padx=(0, 4))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(row3, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 8))
        self.search_entry.bind("<Return>", lambda event: self.apply_filter())
        ttk.Label(row3, text="ищет по группе, студенту, предмету и преподавателю").pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(row3, text="Схожесть:").pack(side=tk.LEFT, padx=(0, 4))
        self.similarity_var = tk.StringVar(value="0.3")
        ttk.Entry(row3, textvariable=self.similarity_var, width=6).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(row3, text="Искать", command=self.apply_filter).pack(side=tk.LEFT)

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
            ("PYTHON all", self.python_all_tasks),
            ("Сохранить графики", self.save_all_charts),
            ("save --force", self.save_all_charts_force),
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
            ("10: ДО UPDATE", self.show_update_before),
            ("11: ПОСЛЕ UPDATE", self.show_update_after),
            ("UPDATE: до → действие → после", self.demo_update_before_action_after),
            ("12: ДО DELETE", self.show_delete_before),
            ("13: ПОСЛЕ DELETE", self.show_delete_after),
            ("DELETE: до → действие → после", self.demo_delete_before_action_after),
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
            ("SQL-скрипты проекта", self.sql_scripts_manager),
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

    def run_project_command(self, args, title):
        """Запускает консольные команды проекта из GUI и выводит stdout/stderr."""
        try:
            proc = subprocess.run(
                args,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=120,
            )
            output = []
            output.append(title)
            output.append("=" * min(max(len(title), 10), 100))
            output.append("Команда: " + " ".join(map(str, args)))
            output.append(f"Код завершения: {proc.returncode}")
            if proc.stdout:
                output.append("\nSTDOUT:\n" + proc.stdout)
            if proc.stderr:
                output.append("\nSTDERR:\n" + proc.stderr)
            self.display("\n".join(output))
            self.set_status(title)
        except FileNotFoundError as e:
            messagebox.showerror("Ошибка запуска", f"Файл команды не найден:\n{e}")
        except subprocess.TimeoutExpired:
            messagebox.showerror("Ошибка запуска", "Команда выполнялась слишком долго и была остановлена")
        except Exception as e:
            messagebox.showerror("Ошибка запуска", str(e))

    def clear_filters(self):
        self.filter_value_var.set("")
        self.search_var.set("")
        self.date_var.set("")
        self.set_status("Фильтры очищены")
        self.apply_filter()

    def clear_only_filter(self):
        self.filter_value_var.set("")
        self.set_status("Основной фильтр очищен")
        self.apply_filter()

    def on_field_change(self, event=None):
        """При смене поля очищаем значение, чтобы старый фильтр не применялся к новому полю."""
        self.filter_value_var.set("")
        try:
            self.filter_value_entry.focus_set()
        except Exception:
            pass

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
        """
        Оставлено для совместимости с другими частями приложения.
        В новой версии фильтр использует обычное поле ввода, поэтому лишний Combobox больше не выводится.
        """
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
        except Exception:
            try:
                self.conn.rollback()
            except Exception:
                pass

    def build_filter_condition(self, aliases=True):
        """Возвращает SQL-условия и параметры для запросов с алиасами g/s/d/t/u."""
        conditions = []
        params = []

        field = self.filter_field_var.get()
        value = self.filter_value_var.get().strip()

        if value:
            text_map = {
                "группа": "g.название" if aliases else "название",
                "факультет": "g.факультет" if aliases else "факультет",
                "курс": "g.курс" if aliases else "курс",
                "фамилия": "s.фамилия" if aliases else "фамилия",
                "имя студента": "s.имя" if aliases else "имя",
                "предмет": "d.название" if aliases else "название",
                "дисциплина": "d.название" if aliases else "название",
            }

            if field in text_map:
                conditions.append(f"{text_map[field]} ILIKE %s")
                params.append(f"%{value}%")
            elif field == "преподаватель":
                conditions.append("(t.фамилия ILIKE %s OR t.имя ILIKE %s)")
                params.extend([f"%{value}%", f"%{value}%"])
            elif field in ("оценка =", "оценка >=", "оценка <="):
                try:
                    grade = float(value.replace(",", "."))
                    op = "=" if field == "оценка =" else ">=" if field == "оценка >=" else "<="
                    conditions.append(f"u.оценка {op} %s")
                    params.append(grade)
                except ValueError:
                    messagebox.showwarning("Фильтр", "Для оценки нужно ввести число, например 4 или 4.5")
            elif field in ("дата =", "дата >=", "дата <="):
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
                    messagebox.showwarning("Фильтр", "Дата должна быть в формате YYYY-MM-DD, например 2026-05-09")
                else:
                    op = "=" if field == "дата =" else ">=" if field == "дата >=" else "<="
                    conditions.append(f"u.дата::date {op} %s::date")
                    params.append(value)

        search_text = self.search_var.get().strip()
        if search_text:
            similarity = self.get_similarity()
            conditions.append(
                "("
                "similarity(g.название, %s) >= %s OR "
                "similarity(s.фамилия, %s) >= %s OR "
                "similarity(s.имя, %s) >= %s OR "
                "similarity(d.название, %s) >= %s OR "
                "similarity(t.фамилия, %s) >= %s OR "
                "similarity(t.имя, %s) >= %s"
                ")"
            )
            params.extend([
                search_text, similarity,
                search_text, similarity,
                search_text, similarity,
                search_text, similarity,
                search_text, similarity,
                search_text, similarity,
            ])

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
        season = self.season_expr()
        sql = f"""
            WITH season_data AS (
                SELECT {season} AS сезон,
                       ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
                       COUNT(*) AS оценок
                FROM УСПЕВАЕМОСТЬ u
                GROUP BY {season}
            )
            SELECT сезон, средний_балл, оценок
            FROM season_data
            ORDER BY CASE сезон
                WHEN 'Зима' THEN 1
                WHEN 'Весна' THEN 2
                WHEN 'Лето' THEN 3
                WHEN 'Осень' THEN 4
                ELSE 5
            END
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

    def format_python_pivot_table(self, rows, title="./PYTHON task2: красивая сводная таблица"):
        """Компактная сводная таблица: дисциплины строками, группы колонками.
        Так таблица не расползается из-за длинных названий дисциплин.
        """
        if not rows:
            return f"{title}\n\nНет данных\n"

        groups = sorted({str(r[0]) for r in rows})
        subjects = sorted({str(r[1]) for r in rows})
        values = {(str(r[1]), str(r[0])): r[2] for r in rows}
        counts = {(str(r[1]), str(r[0])): r[3] for r in rows}

        def grade_text(value):
            if value is None or value == "":
                return "—"
            try:
                return f"{float(value):.2f}"
            except Exception:
                return str(value)

        matrix = []
        for subject in subjects:
            subject_values = []
            total_count = 0
            weighted_sum = 0.0
            for group in groups:
                avg = values.get((subject, group))
                cnt = counts.get((subject, group), 0) or 0
                if avg is not None:
                    subject_values.append(grade_text(avg))
                    try:
                        weighted_sum += float(avg) * int(cnt)
                        total_count += int(cnt)
                    except Exception:
                        pass
                else:
                    subject_values.append("—")
            total_avg = f"{weighted_sum / total_count:.2f}" if total_count else "—"
            matrix.append([subject] + subject_values + [total_avg, str(total_count)])

        cols = ["дисциплина"] + groups + ["среднее", "оценок"]
        self.last_result_cols = cols
        self.last_result_rows = matrix

        # Узкие колонки для групп, широкая только для дисциплины.
        widths = []
        for i, col in enumerate(cols):
            if i == 0:
                widths.append(34)
            elif col in ("среднее", "оценок"):
                widths.append(max(len(col), 7))
            else:
                widths.append(max(7, min(12, len(str(col)))))

        def cut(text, width):
            text = "" if text is None else str(text)
            return text if len(text) <= width else text[:width - 1] + "…"

        lines = []
        lines.append(title)
        lines.append("=" * min(len(title), 120))
        lines.append("Формат: строки — дисциплины, колонки — группы, значения — средний балл.")
        lines.append("")

        top = "┌" + "┬".join("─" * (w + 2) for w in widths) + "┐"
        sep = "├" + "┼".join("─" * (w + 2) for w in widths) + "┤"
        bottom = "└" + "┴".join("─" * (w + 2) for w in widths) + "┘"
        lines.append(top)
        lines.append("│" + "│".join(f" {cut(cols[i], widths[i]).ljust(widths[i])} " for i in range(len(cols))) + "│")
        lines.append(sep)
        for row in matrix:
            lines.append("│" + "│".join(f" {cut(row[i], widths[i]).ljust(widths[i])} " for i in range(len(cols))) + "│")
        lines.append(bottom)
        lines.append(f"Всего дисциплин: {len(subjects)}")
        lines.append(f"Всего групп: {len(groups)}")
        return "\n".join(lines) + "\n"

    def open_python_pivot_window(self, rows):
        """Открывает сводную таблицу в отдельном окне Treeview, чтобы её удобно смотреть."""
        if not rows:
            messagebox.showinfo("Сводная таблица", "Нет данных")
            return

        groups = sorted({str(r[0]) for r in rows})
        subjects = sorted({str(r[1]) for r in rows})
        values = {(str(r[1]), str(r[0])): r[2] for r in rows}
        counts = {(str(r[1]), str(r[0])): r[3] for r in rows}

        def grade_text(value):
            if value is None or value == "":
                return "—"
            try:
                return f"{float(value):.2f}"
            except Exception:
                return str(value)

        cols = ["дисциплина"] + groups + ["среднее", "оценок"]
        matrix = []
        for subject in subjects:
            total_count = 0
            weighted_sum = 0.0
            row_values = []
            for group in groups:
                avg = values.get((subject, group))
                cnt = counts.get((subject, group), 0) or 0
                row_values.append(grade_text(avg))
                if avg is not None:
                    try:
                        weighted_sum += float(avg) * int(cnt)
                        total_count += int(cnt)
                    except Exception:
                        pass
            total_avg = f"{weighted_sum / total_count:.2f}" if total_count else "—"
            matrix.append([subject] + row_values + [total_avg, str(total_count)])

        win = tk.Toplevel(self.root)
        win.title("./PYTHON 2 — сводная таблица")
        win.geometry("1200x650")
        win.transient(self.root)

        frame = ttk.Frame(win, padding=8)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Сводная таблица: дисциплины × группы, значения — средний балл",
            font=("Arial", 12, "bold"),
        ).pack(anchor="w", pady=(0, 6))

        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        for col in cols:
            tree.heading(col, text=col)
            if col == "дисциплина":
                tree.column(col, width=260, minwidth=180, anchor="w")
            elif col in ("среднее", "оценок"):
                tree.column(col, width=90, minwidth=70, anchor="center")
            else:
                tree.column(col, width=90, minwidth=70, anchor="center")

        for row in matrix:
            tree.insert("", tk.END, values=row)

        ttk.Button(frame, text="Закрыть", command=win.destroy).pack(anchor="e", pady=(8, 0))

    def python_task2_pivot(self):
        cond, params = self.build_filter_condition()
        sql = f"""
            SELECT g.название AS группа,
                   d.название AS дисциплина,
                   ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
                   COUNT(*) AS оценок
            FROM УСПЕВАЕМОСТЬ u
            JOIN ГРУППЫ g ON g.код = u.группа
            JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
            JOIN СТУДЕНТЫ s ON s.код = u.студент
            LEFT JOIN ПРЕПОДАВАТЕЛИ t ON t.код = u.преподаватель
            WHERE 1=1 {cond}
            GROUP BY g.название, d.название
            ORDER BY d.название, g.название
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

        self.display(self.format_python_pivot_table(rows))
        self.open_python_pivot_window(rows)
        self.set_status("Красивая сводная таблица")

    def python_all_tasks(self):
        """Точная кнопка для команды ./PYTHON all из проекта."""
        cmd = self.project_root / "PYTHON"
        if cmd.exists():
            self.run_project_command([str(cmd), "all"], "./PYTHON all")
        else:
            messagebox.showwarning("Команда не найдена", "Файл PYTHON не найден в корне проекта. Выполню основные задачи внутри GUI.")
            self.python_task1_report()
            self.show_dynamics()
            self.show_pie()

    def save_all_charts_force(self):
        """Точная кнопка для команды ./PYTHON save --force из проекта."""
        cmd = self.project_root / "PYTHON"
        if cmd.exists():
            self.run_project_command([str(cmd), "save", "--force"], "./PYTHON save --force")
        else:
            folder = self.project_root / "docs"
            folder.mkdir(exist_ok=True)
            try:
                self.show_dynamics(save_path=folder / "task3_chart.png")
                self.show_pie(save_path=folder / "task4_chart.png")
                messagebox.showinfo("Готово", f"Графики сохранены с перезаписью в папку:\n{folder}")
                self.set_status("save --force")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

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

    def demo_update_before_action_after(self):
        """Полная демонстрация UPDATE: показывает запись до изменения, выполняет UPDATE и показывает запись после."""
        code = self.ask_int("Демонстрация UPDATE", "Введите код студента для изменения телефона:", initial=1)
        if not code:
            return
        new_phone = self.ask_text("Демонстрация UPDATE", "Введите новый телефон:", initial="+7-000-000-00-00")
        if new_phone is None:
            return

        before = self.execute(
            "SELECT * FROM СТУДЕНТЫ WHERE код = %s",
            [code],
            title=f"1) ДО UPDATE: студент код={code}",
        )
        update_result = self.execute(
            "UPDATE СТУДЕНТЫ SET телефон = %s WHERE код = %s",
            [new_phone, code],
            title="2) Выполнение UPDATE",
            fetch=False,
        )
        after = self.execute(
            "SELECT * FROM СТУДЕНТЫ WHERE код = %s",
            [code],
            title=f"3) ПОСЛЕ UPDATE: студент код={code}",
        )
        self.display(before + "\n" + "-" * 90 + "\n" + update_result + "\n" + "-" * 90 + "\n" + after)
        self.set_status("UPDATE до-действие-после")

    def demo_delete_before_action_after(self):
        """Полная демонстрация DELETE: показывает запись до удаления, удаляет её и показывает результат после."""
        code = self.ask_int("Демонстрация DELETE", "Введите код студента для удаления:", initial=50)
        if not code:
            return
        if not self.confirm(
            "Подтверждение DELETE",
            f"Будет удалён студент с кодом {code} и связанные записи успеваемости. Продолжить?",
        ):
            return

        before = self.execute(
            "SELECT * FROM СТУДЕНТЫ WHERE код = %s",
            [code],
            title=f"1) ДО DELETE: студент код={code}",
        )
        delete_result = self.execute(
            """
            DELETE FROM УСПЕВАЕМОСТЬ WHERE студент = %s;
            DELETE FROM СТУДЕНТЫ WHERE код = %s;
            """,
            [code, code],
            title="2) Выполнение DELETE",
            fetch=False,
        )
        after = self.execute(
            "SELECT * FROM СТУДЕНТЫ WHERE код = %s",
            [code],
            title=f"3) ПОСЛЕ DELETE: студент код={code}",
        )
        self.display(before + "\n" + "-" * 90 + "\n" + delete_result + "\n" + "-" * 90 + "\n" + after)
        self.set_status("DELETE до-действие-после")

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

    # ------------------------------------------------------------------
    # Работа с SQL-файлами проекта
    # ------------------------------------------------------------------
    def project_sql_directories(self):
        """Папки проекта ВУЗ, где лежат учебные SQL-скрипты."""
        return [
            "schema",
            "data",
            "helper",
            "queries",
            "functions",
            "generation",
            "control",
        ]

    def find_project_sql_files(self):
        """Находит все .sql файлы в основных папках проекта."""
        files = []
        root = self.project_root
        for folder in self.project_sql_directories():
            base = root / folder
            if base.exists():
                files.extend(sorted(base.rglob("*.sql")))
        return sorted(set(files), key=lambda p: str(p.relative_to(root)).lower())

    def read_sql_text(self, path):
        path = Path(path)
        for enc in ("utf-8", "utf-8-sig", "cp1251"):
            try:
                return path.read_text(encoding=enc)
            except UnicodeDecodeError:
                continue
        return path.read_text(encoding="utf-8", errors="replace")

    def prepare_sql_with_params(self, sql_text, params_text=None):
        """Простая подстановка параметров для учебных SQL-файлов: $1, $2, :param1, :1."""
        if params_text is None:
            needs_params = any(marker in sql_text for marker in ("$1", ":param1", ":1"))
            if needs_params:
                params_text = simpledialog.askstring(
                    "Параметры SQL-файла",
                    "Введите параметры через пробел. Например: ИНФ Иванов\nМожно оставить пустым:",
                    parent=self.root,
                )
            else:
                params_text = ""
        params = [] if not params_text else params_text.split()
        prepared = sql_text
        for idx, value in enumerate(params, start=1):
            safe = value.replace("'", "''")
            quoted = f"'{safe}'"
            prepared = prepared.replace(f"$${idx}", quoted)
            prepared = prepared.replace(f"${idx}", quoted)
            prepared = prepared.replace(f":param{idx}", quoted)
            prepared = prepared.replace(f":{idx}", quoted)
        return prepared

    def run_project_sql_file(self, path, use_psql=False):
        path = Path(path)
        if not path.exists():
            messagebox.showerror("SQL-файл", f"Файл не найден:\n{path}")
            return
        if use_psql:
            self.run_project_sql_file_psql(path)
            return
        try:
            sql_text = self.read_sql_text(path)
            sql_text = self.prepare_sql_with_params(sql_text)
            title = f"SQL-файл проекта: {path.relative_to(self.project_root)}"
            result = self.execute(sql_text, title=title, fetch=True)
            self.display(result)
            self.set_status(f"Выполнен SQL-файл: {path.name}")
        except Exception as e:
            messagebox.showerror("Ошибка SQL-файла", str(e))

    def run_project_sql_file_psql(self, path):
        path = Path(path)
        env = os.environ.copy()
        if DB_CONFIG.get("password"):
            env["PGPASSWORD"] = str(DB_CONFIG.get("password"))
        cmd = [
            "psql",
            "-h", str(DB_CONFIG.get("host", "localhost")),
            "-p", str(DB_CONFIG.get("port", 5432)),
            "-U", str(DB_CONFIG.get("user", "")),
            "-d", str(DB_CONFIG.get("dbname", "")),
            "-f", str(path),
        ]
        try:
            proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
            title = f"psql: {path.relative_to(self.project_root)}"
            out = [title, "=" * len(title), ""]
            if proc.stdout:
                out.append(proc.stdout)
            if proc.stderr:
                out.append("\nСообщения/ошибки psql:\n" + proc.stderr)
            out.append(f"\nКод завершения: {proc.returncode}")
            self.display("\n".join(out))
            self.set_status(f"psql выполнен: {path.name}")
        except FileNotFoundError:
            messagebox.showerror("psql", "Команда psql не найдена. Проверьте PostgreSQL и PATH.")
        except Exception as e:
            messagebox.showerror("Ошибка psql", str(e))

    def run_sql_directory(self):
        directory = filedialog.askdirectory(initialdir=str(self.project_root), title="Выберите папку с SQL-файлами")
        if not directory:
            return
        folder = Path(directory)
        files = sorted(folder.rglob("*.sql"))
        if not files:
            messagebox.showinfo("SQL-папка", "В выбранной папке нет .sql файлов.")
            return
        ok = messagebox.askyesno(
            "Запуск папки SQL",
            f"Будет выполнено {len(files)} SQL-файлов из папки:\n{folder}\n\n"
            "Внимание: среди них могут быть INSERT, UPDATE, DELETE или DROP. Продолжить?",
        )
        if not ok:
            return
        reports = []
        for file in files:
            try:
                sql_text = self.read_sql_text(file)
                sql_text = self.prepare_sql_with_params(sql_text, params_text="")
                result = self.execute(sql_text, title=str(file.relative_to(self.project_root)), fetch=True)
                reports.append(result)
            except Exception as e:
                reports.append(f"{file.relative_to(self.project_root)}\nОшибка: {e}\n")
        self.display("\n\n".join(reports))
        self.set_status(f"Выполнена папка SQL: {folder.name}")

    def sql_scripts_manager(self):
        """Окно навигации по SQL-скриптам проекта ВУЗ."""
        root = self.project_root
        win = tk.Toplevel(self.root)
        win.title("SQL-скрипты проекта ВУЗ")
        win.geometry("1200x720")
        win.transient(self.root)

        top = ttk.Frame(win, padding=6)
        top.pack(fill=tk.X)
        ttk.Label(top, text="Поиск:").pack(side=tk.LEFT, padx=(0, 4))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(top, textvariable=search_var, width=42)
        search_entry.pack(side=tk.LEFT, padx=4)

        body = ttk.PanedWindow(win, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        left = ttk.Frame(body)
        right = ttk.Frame(body)
        body.add(left, weight=1)
        body.add(right, weight=2)

        listbox = tk.Listbox(left, font=("Menlo", 10), exportselection=False)
        list_scroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=list_scroll.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        preview = scrolledtext.ScrolledText(right, wrap=tk.NONE, font=("Menlo", 11))
        preview.pack(fill=tk.BOTH, expand=True)

        all_files = self.find_project_sql_files()
        visible_files = []

        def rel(path):
            try:
                return str(path.relative_to(root))
            except Exception:
                return str(path)

        def selected_file():
            sel = listbox.curselection()
            if not sel:
                return None
            return visible_files[sel[0]]

        def show_preview(*_):
            file = selected_file()
            preview.config(state=tk.NORMAL)
            preview.delete("1.0", tk.END)
            if not file:
                preview.insert(tk.END, "Выберите SQL-файл слева.")
                return
            try:
                text = self.read_sql_text(file)
                header = f"-- {rel(file)}\n-- Размер: {file.stat().st_size} байт\n\n"
                preview.insert(tk.END, header + text)
            except Exception as e:
                preview.insert(tk.END, f"Ошибка чтения файла: {e}")

        def refresh_list(*_):
            query = search_var.get().strip().lower()
            listbox.delete(0, tk.END)
            visible_files.clear()
            for file in all_files:
                name = rel(file)
                if not query or query in name.lower():
                    visible_files.append(file)
                    listbox.insert(tk.END, name)
            if visible_files:
                listbox.selection_set(0)
                show_preview()
            else:
                preview.config(state=tk.NORMAL)
                preview.delete("1.0", tk.END)
                preview.insert(tk.END, "SQL-файлы не найдены.")

        def run_selected_python():
            file = selected_file()
            if file:
                self.run_project_sql_file(file, use_psql=False)

        def run_selected_psql():
            file = selected_file()
            if file:
                self.run_project_sql_file(file, use_psql=True)

        def copy_path():
            file = selected_file()
            if file:
                self.root.clipboard_clear()
                self.root.clipboard_append(str(file))
                self.set_status("Путь к SQL-файлу скопирован")

        actions = ttk.Frame(win, padding=6)
        actions.pack(fill=tk.X)
        ttk.Button(actions, text="Выполнить выбранный SQL", command=run_selected_python).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Выполнить через psql", command=run_selected_psql).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Выполнить папку SQL", command=self.run_sql_directory).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Скопировать путь", command=copy_path).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Обновить список", command=refresh_list).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Закрыть", command=win.destroy).pack(side=tk.RIGHT, padx=4)

        search_var.trace_add("write", refresh_list)
        listbox.bind("<<ListboxSelect>>", show_preview)
        search_entry.bind("<Return>", lambda e: refresh_list())
        refresh_list()

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
            "представления, функции, подзапросы, экспорт, бэкап, архив, запуск SQL-файлов,\n"
            "а также демонстрации UPDATE/DELETE до-действие-после."
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = UniversityApp(root)
    root.mainloop()
