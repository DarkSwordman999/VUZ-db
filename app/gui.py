#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import psycopg2

from scripts.db_config import DB_CONFIG


class UniversityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ВУЗ: Система управления успеваемостью")
        self.root.geometry("1300x800")
        self.root.configure(bg="#f5f5f5")

        self.conn = None
        self.current_query = "top"
        self.status_var = tk.StringVar(value="Готов")
        self.autocomplete_data = {
            "группа": [],
            "фамилия": [],
            "дисциплина": [],
            "факультет": [],
        }

        self.connect_db()
        self.create_menu()
        self.setup_styles()
        self.create_widgets()
        self.load_stats()
        self.load_autocomplete_data()
        self.top_students()

    # ---------- Подключение и служебные методы ----------

    def connect_db(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.status_var.set("✅ Подключено к БД")
        except Exception as e:
            self.conn = None
            self.status_var.set(f"❌ Ошибка подключения к БД: {e}")

    def safe_rollback(self):
        if self.conn:
            try:
                self.conn.rollback()
            except Exception:
                pass

    def get_int_value(self, var, default=10, min_value=1, max_value=100):
        try:
            value = int(var.get())
        except (TypeError, ValueError):
            value = default
        value = max(min_value, min(max_value, value))
        var.set(str(value))
        return value

    def get_float_value(self, var, default=0.3, min_value=0.1, max_value=0.9):
        try:
            value = float(str(var.get()).replace(",", "."))
        except (TypeError, ValueError):
            value = default
        value = max(min_value, min(max_value, value))
        var.set(str(value))
        return value

    def display(self, text):
        """Безопасный вывод текста в защищённое поле."""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.config(state=tk.DISABLED)

    def set_status(self, text):
        self.status_var.set(text)
        self.root.update_idletasks()

    def execute(self, sql, params=None):
        """Выполняет SQL-запрос и возвращает результат в виде текстовой таблицы."""
        if not self.conn:
            return "❌ Нет подключения к базе данных"

        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, params or ())

                if cur.description:
                    rows = cur.fetchall()
                    cols = [d[0] for d in cur.description]

                    if not rows:
                        return "\n📭 Нет данных, удовлетворяющих запросу\n"

                    widths = [len(str(c)) for c in cols]
                    for row in rows[:500]:
                        for i, value in enumerate(row):
                            widths[i] = max(widths[i], len(str(value)))
                    widths = [min(w, 30) for w in widths]

                    result = "┌" + "┬".join("─" * (w + 2) for w in widths) + "┐\n"
                    result += "│" + "│".join(
                        f" {str(cols[i])[:widths[i]].ljust(widths[i])} "
                        for i in range(len(cols))
                    ) + "│\n"
                    result += "├" + "┼".join("─" * (w + 2) for w in widths) + "┤\n"

                    for row in rows[:500]:
                        cells = []
                        for i, value in enumerate(row):
                            cells.append(f" {str(value)[:widths[i]].ljust(widths[i])} ")
                        result += "│" + "│".join(cells) + "│\n"

                    result += "└" + "┴".join("─" * (w + 2) for w in widths) + "┘\n"

                    if len(rows) > 500:
                        result += f"\n... и ещё {len(rows) - 500} строк\n"
                    result += f"\n📊 Всего: {len(rows)} строк\n"
                    return result

                self.conn.commit()
                return "✅ Выполнено"

        except Exception as e:
            self.safe_rollback()
            return f"❌ Ошибка: {e}"

    # ---------- Меню и интерфейс ----------

    def create_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Экспорт CSV", command=self.export_csv)
        file_menu.add_command(label="Бэкап", command=self.backup_db)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.root.config(menu=menubar)


    def setup_styles(self):
        """Настраивает стиль кнопок так, чтобы текст точно отображался на macOS.

        На macOS обычный tk.Button часто игнорирует bg, но оставляет fg="white".
        В итоге получается белый текст на светлой кнопке. Поэтому для кнопок
        меню используем ttk.Button с обычным тёмным текстом.
        """
        self.style = ttk.Style(self.root)
        try:
            if "clam" in self.style.theme_names():
                self.style.theme_use("clam")
        except Exception:
            pass

        self.style.configure("Menu.TButton", font=("Arial", 10, "bold"), padding=(8, 6))
        self.style.configure("Action.TButton", font=("Arial", 9, "bold"), padding=(8, 4))
        self.style.configure("Table.TButton", font=("Arial", 10), padding=(8, 5))

    def make_menu_button(self, parent, text, command):
        """Создаёт кнопку меню без белого текста на белом фоне."""
        return ttk.Button(parent, text=text, command=command, width=24, style="Menu.TButton")

    def create_widgets(self):
        left = tk.Frame(self.root, width=220, bg="#e8e8e8", relief=tk.RAISED, bd=1)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=3, pady=3)

        tk.Label(left, text="МЕНЮ", font=("Arial", 12, "bold"), bg="#e8e8e8", fg="#111111").pack(pady=10)

        buttons = [
            ("Топ студентов", self.top_students),
            ("Худшие студенты", self.weak_students),
            ("Топ преподавателей", self.top_teachers),
            ("Статистика БД", self.db_stats),
            ("Просмотр таблиц", self.show_tables),
            ("Структура БД", self.show_structure),
        ]

        for text, cmd in buttons:
            self.make_menu_button(left, text, cmd).pack(fill=tk.X, pady=3, padx=8)

        tk.Label(left, text="", bg="#e8e8e8").pack(pady=5)
        tk.Label(left, text="ГРАФИКИ", font=("Arial", 10, "bold"), bg="#e8e8e8", fg="#111111").pack(pady=5)

        self.make_menu_button(left, "Динамика", self.show_dynamics).pack(fill=tk.X, pady=3, padx=8)
        self.make_menu_button(left, "Круговая", self.show_pie).pack(fill=tk.X, pady=3, padx=8)

        right = tk.Frame(self.root, bg="#f5f5f5")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        params = tk.LabelFrame(right, text="🔧 Параметры", font=("Arial", 10, "bold"), bg="#f5f5f5")
        params.pack(fill=tk.X, pady=5)

        row1 = tk.Frame(params, bg="#f5f5f5")
        row1.pack(fill=tk.X, padx=5, pady=3)

        tk.Label(row1, text="Количество:", bg="#f5f5f5").pack(side=tk.LEFT, padx=5)
        self.limit_var = tk.StringVar(value="10")
        tk.Spinbox(row1, from_=1, to=100, textvariable=self.limit_var, width=6).pack(side=tk.LEFT, padx=5)

        tk.Label(row1, text="Порог для графика:", bg="#f5f5f5").pack(side=tk.LEFT, padx=5)
        self.threshold_var = tk.StringVar(value="0.3")
        tk.Spinbox(row1, from_=0.1, to=0.9, increment=0.1, textvariable=self.threshold_var, width=6).pack(side=tk.LEFT, padx=5)

        row2 = tk.Frame(params, bg="#f5f5f5")
        row2.pack(fill=tk.X, padx=5, pady=3)

        tk.Label(row2, text="Фильтр по полю:", bg="#f5f5f5").pack(side=tk.LEFT, padx=5)
        self.filter_field_var = tk.StringVar(value="группа")
        field_combo = ttk.Combobox(
            row2,
            textvariable=self.filter_field_var,
            values=["группа", "фамилия", "дисциплина", "факультет"],
            width=15,
            state="readonly",
        )
        field_combo.pack(side=tk.LEFT, padx=5)
        field_combo.bind("<<ComboboxSelected>>", self.on_field_change)

        tk.Label(row2, text="Значение:", bg="#f5f5f5").pack(side=tk.LEFT, padx=5)
        self.filter_value_var = tk.StringVar()
        self.filter_entry = tk.Entry(row2, textvariable=self.filter_value_var, width=25)
        self.filter_entry.pack(side=tk.LEFT, padx=5)
        self.filter_entry.bind("<KeyRelease>", self.on_filter_change)
        self.filter_entry.bind("<Escape>", lambda event: self.filter_combo.place_forget())

        self.filter_combo = ttk.Combobox(row2, width=25, state="readonly")
        self.filter_combo.place_forget()
        self.filter_combo.bind("<<ComboboxSelected>>", self.on_filter_select)

        self.apply_btn = ttk.Button(
            row2,
            text="Применить",
            command=self.apply_filter,
            style="Action.TButton",
        )
        self.apply_btn.pack(side=tk.LEFT, padx=10)

        row3 = tk.Frame(params, bg="#f5f5f5")
        row3.pack(fill=tk.X, padx=5, pady=3)

        tk.Label(row3, text="🔍 Нечёткий поиск:", bg="#f5f5f5").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(row3, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<KeyRelease>", self.on_search_change)
        self.search_entry.bind("<Escape>", lambda event: self.search_combo.place_forget())

        self.search_combo = ttk.Combobox(row3, width=30, state="readonly")
        self.search_combo.place_forget()
        self.search_combo.bind("<<ComboboxSelected>>", self.on_search_select)

        tk.Label(row3, text="Порог схожести:", bg="#f5f5f5").pack(side=tk.LEFT, padx=5)
        self.similarity_var = tk.StringVar(value="0.3")
        tk.Spinbox(row3, from_=0.1, to=0.9, increment=0.1, textvariable=self.similarity_var, width=6).pack(side=tk.LEFT, padx=5)

        res_frame = tk.LabelFrame(right, text="📋 Результаты", font=("Arial", 10, "bold"), bg="#f5f5f5")
        res_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.result_text = scrolledtext.ScrolledText(
            res_frame,
            wrap=tk.WORD,
            font=("Courier", 10),
            bg="#ffffff",
            fg="#000000",
            state=tk.DISABLED,
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)

        status = tk.Frame(right, bg="#f5f5f5")
        status.pack(fill=tk.X, pady=5)

        self.status_label = tk.Label(status, textvariable=self.status_var, anchor=tk.W, bg="#f5f5f5", fg="#333")
        self.status_label.pack(fill=tk.X)

        self.stats_label = tk.Label(status, text="", anchor=tk.W, bg="#f5f5f5", fg="#666")
        self.stats_label.pack(fill=tk.X)

    # ---------- Автодополнение ----------

    def load_autocomplete_data(self):
        """Загружает данные для автодополнения."""
        if not self.conn:
            return

        queries = {
            "группа": "SELECT название FROM ГРУППЫ WHERE название IS NOT NULL ORDER BY название",
            "фамилия": "SELECT DISTINCT фамилия FROM СТУДЕНТЫ WHERE фамилия IS NOT NULL ORDER BY фамилия",
            "дисциплина": "SELECT название FROM ДИСЦИПЛИНЫ WHERE название IS NOT NULL ORDER BY название",
            "факультет": "SELECT DISTINCT факультет FROM ГРУППЫ WHERE факультет IS NOT NULL ORDER BY факультет",
        }

        try:
            with self.conn.cursor() as cur:
                for key, sql in queries.items():
                    cur.execute(sql)
                    self.autocomplete_data[key] = [str(row[0]) for row in cur.fetchall() if row[0] is not None]
        except Exception as e:
            self.safe_rollback()
            print(f"Ошибка загрузки автодополнения: {e}")

    def on_field_change(self, event=None):
        field = self.filter_field_var.get()
        self.filter_combo["values"] = self.autocomplete_data.get(field, [])
        self.filter_value_var.set("")
        self.filter_combo.place_forget()

    def on_filter_change(self, event=None):
        field = self.filter_field_var.get()
        text = self.filter_value_var.get().lower().strip()
        values = self.autocomplete_data.get(field, [])
        matches = [v for v in values if text in v.lower()][:10]

        if matches and text:
            self.filter_combo["values"] = matches
            self.filter_combo.place(in_=self.filter_entry, x=0, y=25, width=max(self.filter_entry.winfo_width(), 180))
        else:
            self.filter_combo.place_forget()

    def on_filter_select(self, event=None):
        self.filter_value_var.set(self.filter_combo.get())
        self.filter_combo.place_forget()
        self.apply_filter()

    def on_search_change(self, event=None):
        text = self.search_var.get().lower().strip()
        if len(text) < 2:
            self.search_combo.place_forget()
            return

        matches = []
        for values in self.autocomplete_data.values():
            matches.extend([v for v in values if text in v.lower()])
        matches = sorted(set(matches))[:10]

        if matches:
            self.search_combo["values"] = matches
            self.search_combo.place(in_=self.search_entry, x=0, y=25, width=max(self.search_entry.winfo_width(), 220))
        else:
            self.search_combo.place_forget()

    def on_search_select(self, event=None):
        self.search_var.set(self.search_combo.get())
        self.search_combo.place_forget()
        self.apply_filter()

    # ---------- Фильтры ----------

    def build_filter_condition(self):
        """Возвращает SQL-условие и параметры для обычного фильтра."""
        field = self.filter_field_var.get()
        value = self.filter_value_var.get().strip()
        if not value:
            return "", []

        field_map = {
            "группа": "g.название",
            "фамилия": "s.фамилия",
            "дисциплина": "d.название",
            "факультет": "g.факультет",
        }
        db_field = field_map.get(field, "g.название")
        return f"AND {db_field} ILIKE %s", [f"%{value}%"]

    def build_trigram_condition(self):
        """Возвращает SQL-условие и параметры для поиска по триграммам."""
        search_text = self.search_var.get().strip()
        if not search_text:
            return "", []

        similarity = self.get_float_value(self.similarity_var, default=0.3, min_value=0.1, max_value=0.9)
        conditions = [
            "similarity(g.название, %s) >= %s",
            "similarity(s.фамилия, %s) >= %s",
            "similarity(d.название, %s) >= %s",
        ]
        params = [search_text, similarity, search_text, similarity, search_text, similarity]
        return f"AND ({' OR '.join(conditions)})", params

    def get_common_conditions(self):
        filter_cond, filter_params = self.build_filter_condition()
        trigram_cond, trigram_params = self.build_trigram_condition()
        return f"{filter_cond} {trigram_cond}", filter_params + trigram_params

    def apply_filter(self):
        """Применяет фильтр к текущему отчёту.

        Важно: Tkinter нельзя безопасно обновлять из другого потока, поэтому
        фильтр выполняется в основном потоке через after(), без threading.Thread.
        """
        self.set_status("🔄 Применяю фильтр...")
        self.root.after(10, self._apply_filter)

    def _apply_filter(self):
        if self.current_query == "top":
            self.top_students()
        elif self.current_query == "weak":
            self.weak_students()
        elif self.current_query == "teacher":
            self.top_teachers()
        else:
            self.top_students()

    # ---------- Отчёты ----------

    def top_students(self):
        self.current_query = "top"
        limit = self.get_int_value(self.limit_var, default=10, min_value=1, max_value=100)
        conditions, params = self.get_common_conditions()

        sql = f"""
        SELECT s.фамилия,
               s.имя,
               g.название AS группа,
               ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
               COUNT(*) AS оценок
        FROM СТУДЕНТЫ s
        JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
        JOIN ГРУППЫ g ON g.код = u.группа
        JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
        WHERE 1=1 {conditions}
        GROUP BY s.код, s.фамилия, s.имя, g.название
        ORDER BY средний_балл DESC
        LIMIT %s
        """
        result = self.execute(sql, params + [limit])
        self.display(result)
        self.set_status(f"🏆 Топ {limit} студентов")

    def weak_students(self):
        self.current_query = "weak"
        limit = self.get_int_value(self.limit_var, default=10, min_value=1, max_value=100)
        conditions, params = self.get_common_conditions()

        sql = f"""
        SELECT s.фамилия,
               s.имя,
               g.название AS группа,
               ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
               COUNT(*) AS оценок
        FROM СТУДЕНТЫ s
        JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
        JOIN ГРУППЫ g ON g.код = u.группа
        JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
        WHERE 1=1 {conditions}
        GROUP BY s.код, s.фамилия, s.имя, g.название
        ORDER BY средний_балл ASC
        LIMIT %s
        """
        result = self.execute(sql, params + [limit])
        self.display(result)
        self.set_status(f"📉 Худшие {limit} студентов")

    def top_teachers(self):
        self.current_query = "teacher"
        limit = self.get_int_value(self.limit_var, default=10, min_value=1, max_value=100)
        conditions, params = self.get_common_conditions()

        sql = f"""
        SELECT t.фамилия,
               t.имя,
               ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл,
               COUNT(*) AS оценок
        FROM ПРЕПОДАВАТЕЛИ t
        JOIN УСПЕВАЕМОСТЬ u ON u.преподаватель = t.код
        JOIN ГРУППЫ g ON g.код = u.группа
        JOIN СТУДЕНТЫ s ON s.код = u.студент
        JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
        WHERE 1=1 {conditions}
        GROUP BY t.код, t.фамилия, t.имя
        ORDER BY средний_балл DESC
        LIMIT %s
        """
        result = self.execute(sql, params + [limit])
        self.display(result)
        self.set_status(f"👨‍🏫 Топ {limit} преподавателей")

    def db_stats(self):
        sql = """
        SELECT 'СТУДЕНТЫ' AS таблица, COUNT(*) AS записей FROM СТУДЕНТЫ
        UNION ALL SELECT 'ГРУППЫ', COUNT(*) FROM ГРУППЫ
        UNION ALL SELECT 'ПРЕПОДАВАТЕЛИ', COUNT(*) FROM ПРЕПОДАВАТЕЛИ
        UNION ALL SELECT 'ДИСЦИПЛИНЫ', COUNT(*) FROM ДИСЦИПЛИНЫ
        UNION ALL SELECT 'УСПЕВАЕМОСТЬ', COUNT(*) FROM УСПЕВАЕМОСТЬ
        """
        result = self.execute(sql)
        self.display(result)
        self.set_status("📊 Статистика БД")

    def show_tables(self):
        win = tk.Toplevel(self.root)
        win.title("Просмотр таблиц")
        win.geometry("400x350")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="Выберите таблицу:", font=("Arial", 12)).pack(pady=10)

        for table in ["СТУДЕНТЫ", "ГРУППЫ", "ПРЕПОДАВАТЕЛИ", "ДИСЦИПЛИНЫ", "УСПЕВАЕМОСТЬ"]:
            ttk.Button(win, text=table, width=30, style="Table.TButton", command=lambda t=table: self.view_table(t, win)).pack(pady=3)

    def view_table(self, table, parent):
        allowed_tables = {"СТУДЕНТЫ", "ГРУППЫ", "ПРЕПОДАВАТЕЛИ", "ДИСЦИПЛИНЫ", "УСПЕВАЕМОСТЬ"}
        if table not in allowed_tables:
            messagebox.showerror("Ошибка", "Неизвестная таблица")
            return

        params = []
        if table == "УСПЕВАЕМОСТЬ":
            sql = """
            SELECT u.код_записи,
                   s.фамилия,
                   g.название AS группа,
                   d.название AS дисциплина,
                   u.оценка,
                   u.дата
            FROM УСПЕВАЕМОСТЬ u
            JOIN СТУДЕНТЫ s ON s.код = u.студент
            JOIN ГРУППЫ g ON g.код = u.группа
            JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
            ORDER BY u.дата DESC
            LIMIT %s
            """
            params = [200]
        else:
            sql = f"SELECT * FROM {table} LIMIT %s"
            params = [200]

        result = self.execute(sql, params)

        win = tk.Toplevel(parent)
        win.title(f"Таблица: {table}")
        win.geometry("1000x600")

        text = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Courier", 10))
        text.pack(fill=tk.BOTH, expand=True)
        text.insert(tk.END, result)
        text.config(state=tk.DISABLED)

    def show_structure(self):
        sql = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
        """
        result = self.execute(sql)
        self.display(result)
        self.set_status("📐 Структура БД")

    # ---------- Графики ----------

    def show_dynamics(self):
        if not self.conn:
            messagebox.showerror("Ошибка", "Нет подключения к базе данных")
            return

        conditions, params = self.get_common_conditions()
        sql = f"""
        SELECT DATE_TRUNC('month', u.дата) AS месяц,
               ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл
        FROM УСПЕВАЕМОСТЬ u
        JOIN ГРУППЫ g ON g.код = u.группа
        JOIN СТУДЕНТЫ s ON s.код = u.студент
        JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
        WHERE u.дата IS NOT NULL {conditions}
        GROUP BY DATE_TRUNC('month', u.дата)
        ORDER BY месяц
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()

            if not rows:
                messagebox.showinfo("Нет данных", "Недостаточно данных для построения графика")
                return

            win = tk.Toplevel(self.root)
            win.title("Динамика успеваемости")
            win.geometry("800x500")

            fig, ax = plt.subplots(figsize=(8, 5))
            months = [row[0] for row in rows]
            grades = [float(row[1]) for row in rows]

            ax.plot(months, grades, marker="o", linewidth=2)
            ax.set_xlabel("Дата")
            ax.set_ylabel("Средний балл")
            ax.set_ylim(2, 5)
            ax.grid(True, alpha=0.3)
            ax.set_title("Динамика успеваемости по месяцам")
            fig.autofmt_xdate(rotation=45)
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=win)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            win.protocol("WM_DELETE_WINDOW", lambda: self.close_plot_window(win, fig))
            self.set_status("📈 Построен график динамики")
        except Exception as e:
            self.safe_rollback()
            messagebox.showerror("Ошибка", str(e))

    def show_pie(self):
        if not self.conn:
            messagebox.showerror("Ошибка", "Нет подключения к базе данных")
            return

        conditions, params = self.get_common_conditions()
        sql = f"""
        SELECT g.название AS группа,
               ROUND(AVG(u.оценка)::numeric, 2) AS средний_балл
        FROM ГРУППЫ g
        JOIN УСПЕВАЕМОСТЬ u ON u.группа = g.код
        JOIN СТУДЕНТЫ s ON s.код = u.студент
        JOIN ДИСЦИПЛИНЫ d ON d.код = u.дисциплина
        WHERE 1=1 {conditions}
        GROUP BY g.код, g.название
        HAVING COUNT(u.код_записи) > 0
        ORDER BY средний_балл DESC
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()

            if not rows:
                messagebox.showinfo("Нет данных", "Недостаточно данных для построения диаграммы")
                return

            labels = [row[0] for row in rows[:8]]
            sizes = [float(row[1]) for row in rows[:8]]

            win = tk.Toplevel(self.root)
            win.title("Средний балл по группам")
            win.geometry("600x550" if len(labels) > 4 else "600x500")

            fig, ax = plt.subplots(figsize=(6, 6))
            ax.pie(sizes, labels=labels, autopct="%1.1f%%")
            ax.set_title("Средний балл по группам")
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=win)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            win.protocol("WM_DELETE_WINDOW", lambda: self.close_plot_window(win, fig))
            self.set_status("🥧 Построена круговая диаграмма")
        except Exception as e:
            self.safe_rollback()
            messagebox.showerror("Ошибка", str(e))

    def close_plot_window(self, win, fig):
        plt.close(fig)
        win.destroy()

    # ---------- Файл ----------

    def export_csv(self):
        if not self.conn:
            messagebox.showerror("Ошибка", "Нет подключения к базе данных")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not filename:
            return

        sql = "SELECT * FROM СТУДЕНТЫ"
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                cols = [d[0] for d in cur.description]

            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(cols)
                writer.writerows(rows)

            messagebox.showinfo("Успех", f"Экспортировано {len(rows)} записей")
        except Exception as e:
            self.safe_rollback()
            messagebox.showerror("Ошибка", str(e))

    def backup_db(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".dump",
            filetypes=[("PostgreSQL dump", "*.dump"), ("All files", "*.*")],
        )
        if not filename:
            return

        dbname = DB_CONFIG.get("dbname")
        if not dbname:
            messagebox.showerror("Ошибка", "В DB_CONFIG не указан dbname")
            return

        cmd = ["pg_dump", "-Fc", "-f", filename]

        if DB_CONFIG.get("host"):
            cmd.extend(["-h", str(DB_CONFIG["host"])])
        if DB_CONFIG.get("port"):
            cmd.extend(["-p", str(DB_CONFIG["port"])])
        if DB_CONFIG.get("user"):
            cmd.extend(["-U", str(DB_CONFIG["user"])])

        cmd.append(str(dbname))

        try:
            env = os.environ.copy()
            if DB_CONFIG.get("password"):
                env["PGPASSWORD"] = str(DB_CONFIG["password"])

            subprocess.run(cmd, check=True, env=env)
            messagebox.showinfo("Успех", "Бэкап создан")
        except FileNotFoundError:
            messagebox.showerror("Ошибка", "pg_dump не найден. Установите PostgreSQL tools или добавьте pg_dump в PATH.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Ошибка", f"Не удалось создать бэкап: {e}")

    # ---------- Статистика и справка ----------

    def load_stats(self):
        if not self.conn:
            self.stats_label.config(text="📊 Нет подключения к БД")
            return

        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM СТУДЕНТЫ")
                students = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM УСПЕВАЕМОСТЬ")
                grades = cur.fetchone()[0]
            self.stats_label.config(text=f"📊 Студентов: {students} | Оценок: {grades}")
        except Exception:
            self.safe_rollback()
            self.stats_label.config(text="📊 Статистика недоступна")

    def show_about(self):
        messagebox.showinfo(
            "О программе",
            "ВУЗ: Система управления успеваемостью\n"
            "Версия 3.1\n\n"
            "✓ Поиск по триграммам\n"
            "✓ Автодополнение при вводе\n"
            "✓ Фильтр по любому полю\n"
            "✓ Защита от редактирования\n"
            "✓ Безопасные SQL-параметры\n\n"
            "ТулГУ, Курсовая работа 2025",
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = UniversityApp(root)
    root.mainloop()
