#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import psycopg2
from scripts.db_config import DB_CONFIG

class UniversityDBApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Система учёта успеваемости ВУЗ")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Подключение к БД
        self.conn = None
        self.connect_db()
        
        # Создание интерфейса
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()
        
        # Загрузка начальных данных
        self.load_stats()
    
    def connect_db(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.status_var.set("Подключено к БД")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться к БД:\n{e}")
            self.status_var.set("Ошибка подключения")
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Экспорт в CSV", command=self.export_csv)
        file_menu.add_command(label="Бэкап", command=self.backup_db)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)
        
        # Меню Отчёты
        reports_menu = tk.Menu(menubar, tearoff=0)
        reports_menu.add_command(label="Топ студентов", command=self.show_top_students)
        reports_menu.add_command(label="Худшие студенты", command=self.show_weak_students)
        reports_menu.add_command(label="Распределение оценок", command=self.show_grade_distribution)
        reports_menu.add_command(label="Средний балл по сезонам", command=self.show_season_stats)
        menubar.add_cascade(label="Отчёты", menu=reports_menu)
        
        # Меню Администрирование
        admin_menu = tk.Menu(menubar, tearoff=0)
        admin_menu.add_command(label="Статистика БД", command=self.show_db_stats)
        admin_menu.add_command(label="Архивировать старые записи", command=self.archive_records)
        menubar.add_cascade(label="Администрирование", menu=admin_menu)
        
        # Меню Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_main_frame(self):
        # Верхняя панель с кнопками
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        buttons = [
            ("Топ студентов", self.show_top_students),
            ("Худшие студенты", self.show_weak_students),
            ("Оценки по группам", self.show_grade_distribution),
            ("Статистика", self.show_db_stats),
        ]
        
        for text, cmd in buttons:
            btn = tk.Button(top_frame, text=text, command=cmd, width=18)
            btn.pack(side=tk.LEFT, padx=2)
        
        # Панель для параметров
        self.param_frame = tk.LabelFrame(self.root, text="Параметры", padx=5, pady=5)
        self.param_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(self.param_frame, text="Количество:").pack(side=tk.LEFT, padx=5)
        self.limit_var = tk.StringVar(value="10")
        self.limit_spinbox = tk.Spinbox(self.param_frame, from_=1, to=100, textvariable=self.limit_var, width=5)
        self.limit_spinbox.pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.param_frame, text="Группа/Дисциплина:").pack(side=tk.LEFT, padx=5)
        self.filter_var = tk.StringVar()
        self.filter_entry = tk.Entry(self.param_frame, textvariable=self.filter_var, width=20)
        self.filter_entry.pack(side=tk.LEFT, padx=5)
        
        self.apply_btn = tk.Button(self.param_frame, text="Применить", command=self.apply_filter)
        self.apply_btn.pack(side=tk.LEFT, padx=5)
        
        # Область для вывода результатов
        result_frame = tk.LabelFrame(self.root, text="Результаты", padx=5, pady=5)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, font=("Courier", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # Нижняя панель со статистикой
        stats_frame = tk.Frame(self.root)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.stats_label = tk.Label(stats_frame, text="", anchor=tk.W)
        self.stats_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("Готов")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def load_stats(self):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM СТУДЕНТЫ")
            students = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM УСПЕВАЕМОСТЬ")
            grades = cur.fetchone()[0]
            cur.close()
            self.stats_label.config(text=f"Студентов: {students} | Оценок: {grades}")
        except:
            pass
    
    def execute_query(self, sql, params=None):
        try:
            cur = self.conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            colnames = [desc[0] for desc in cur.description] if cur.description else []
            cur.close()
            return rows, colnames
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return [], []
    
    def display_results(self, rows, colnames):
        self.result_text.delete(1.0, tk.END)
        if not rows:
            self.result_text.insert(tk.END, "Нет данных\n")
            return
        
        # Определяем ширину колонок
        col_widths = [len(str(c)) for c in colnames]
        for row in rows[:100]:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))
        
        # Заголовок
        header = "│ " + " │ ".join(c.ljust(col_widths[i]) for i, c in enumerate(colnames)) + " │\n"
        separator = "├─" + "─┼─".join("─" * w for w in col_widths) + "─┤\n"
        top = "┌─" + "─┬─".join("─" * w for w in col_widths) + "─┐\n"
        bottom = "└─" + "─┴─".join("─" * w for w in col_widths) + "─┘\n"
        
        self.result_text.insert(tk.END, top)
        self.result_text.insert(tk.END, header)
        self.result_text.insert(tk.END, separator)
        
        for row in rows[:100]:
            line = "│ " + " │ ".join(str(v).ljust(col_widths[i]) for i, v in enumerate(row)) + " │\n"
            self.result_text.insert(tk.END, line)
        
        if len(rows) > 100:
            self.result_text.insert(tk.END, f"│ ... и ещё {len(rows) - 100} строк │\n")
        self.result_text.insert(tk.END, bottom)
        self.result_text.insert(tk.END, f"\nВсего строк: {len(rows)}\n")
    
    def apply_filter(self):
        current = self.menu_state if hasattr(self, 'menu_state') else 'top'
        if current == 'top':
            self.show_top_students()
        elif current == 'weak':
            self.show_weak_students()
    
    def show_top_students(self):
        self.menu_state = 'top'
        limit = self.limit_var.get()
        sql = """
        SELECT фамилия, имя, группа, средний_балл, количество_оценок
        FROM (
            SELECT s.фамилия, s.имя, g.название as группа,
                   ROUND(AVG(u.оценка), 2) as средний_балл,
                   COUNT(u.код_записи) as количество_оценок
            FROM СТУДЕНТЫ s
            JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
            JOIN ГРУППЫ g ON g.код = u.группа
            GROUP BY s.код, s.фамилия, s.имя, g.название
        ) t ORDER BY средний_балл DESC LIMIT %s
        """
        rows, colnames = self.execute_query(sql, (limit,))
        self.display_results(rows, colnames)
        self.status_var.set(f"Топ {limit} студентов")
    
    def show_weak_students(self):
        self.menu_state = 'weak'
        limit = self.limit_var.get()
        sql = """
        SELECT фамилия, имя, группа, средний_балл, количество_оценок
        FROM (
            SELECT s.фамилия, s.имя, g.название as группа,
                   ROUND(AVG(u.оценка), 2) as средний_балл,
                   COUNT(u.код_записи) as количество_оценок
            FROM СТУДЕНТЫ s
            JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
            JOIN ГРУППЫ g ON g.код = u.группа
            GROUP BY s.код, s.фамилия, s.имя, g.название
        ) t ORDER BY средний_балл ASC LIMIT %s
        """
        rows, colnames = self.execute_query(sql, (limit,))
        self.display_results(rows, colnames)
        self.status_var.set(f"Худшие {limit} студентов")
    
    def show_grade_distribution(self):
        sql = """
        SELECT оценка, COUNT(*) as количество,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as процент
        FROM УСПЕВАЕМОСТЬ GROUP BY оценка ORDER BY оценка
        """
        rows, colnames = self.execute_query(sql)
        self.display_results(rows, colnames)
        self.status_var.set("Распределение оценок")
    
    def show_season_stats(self):
        sql = """
        SELECT s.название as сезон, ROUND(AVG(u.оценка), 2) as средний_балл,
               COUNT(*) as количество_оценок
        FROM УСПЕВАЕМОСТЬ u JOIN ВРЕМЕНА_ГОДА s ON s.код = u.сезон
        GROUP BY s.код, s.название ORDER BY s.код
        """
        rows, colnames = self.execute_query(sql)
        self.display_results(rows, colnames)
        self.status_var.set("Средний балл по сезонам")
    
    def show_db_stats(self):
        sql = """
        SELECT 'СТУДЕНТЫ' as таблица, COUNT(*) as записей FROM СТУДЕНТЫ
        UNION ALL SELECT 'ГРУППЫ', COUNT(*) FROM ГРУППЫ
        UNION ALL SELECT 'ПРЕПОДАВАТЕЛИ', COUNT(*) FROM ПРЕПОДАВАТЕЛИ
        UNION ALL SELECT 'ДИСЦИПЛИНЫ', COUNT(*) FROM ДИСЦИПЛИНЫ
        UNION ALL SELECT 'УСПЕВАЕМОСТЬ', COUNT(*) FROM УСПЕВАЕМОСТЬ
        """
        rows, colnames = self.execute_query(sql)
        self.display_results(rows, colnames)
        self.status_var.set("Статистика базы данных")
    
    def export_csv(self):
        import csv
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if filename:
            try:
                cur = self.conn.cursor()
                cur.execute("SELECT * FROM СТУДЕНТЫ")
                rows = cur.fetchall()
                colnames = [desc[0] for desc in cur.description]
                cur.close()
                
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(colnames)
                    writer.writerows(rows)
                
                messagebox.showinfo("Успех", f"Данные экспортированы в {filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
    
    def backup_db(self):
        from tkinter import filedialog
        import subprocess
        import os
        
        filename = filedialog.asksaveasfilename(defaultextension=".dump", filetypes=[("Dump files", "*.dump")])
        if filename:
            try:
                cmd = f"pg_dump -Fc -f '{filename}' {DB_CONFIG['dbname']}"
                os.system(cmd)
                messagebox.showinfo("Успех", f"Бэкап создан: {filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
    
    def archive_records(self):
        if messagebox.askyesno("Подтверждение", "Архивировать записи старше 2 лет?"):
            try:
                cur = self.conn.cursor()
                cur.execute("SELECT archive_old_records(2)")
                count = cur.fetchone()[0]
                self.conn.commit()
                cur.close()
                messagebox.showinfo("Успех", f"Архивировано {count} записей")
                self.show_db_stats()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
    
    def show_about(self):
        messagebox.showinfo("О программе", 
            "Система учёта успеваемости ВУЗ\n"
            "Версия 1.0\n\n"
            "Разработано для курсовой работы по дисциплине 'Базы данных'\n"
            "ТулГУ, ИПМКН, 2025")

if __name__ == "__main__":
    root = tk.Tk()
    app = UniversityDBApp(root)
    root.mainloop()
