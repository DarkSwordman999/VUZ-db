#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from db_config import DB_CONFIG
from db_schema_config import get_table, get_field

os.makedirs('docs', exist_ok=True)

def get_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        print(f"Ошибка подключения: {e}")
        sys.exit(1)

def file_exists(filename, force=False):
    if not force and os.path.exists(filename):
        response = input(f"Файл {filename} уже существует. Перезаписать? (y/N): ")
        return response.lower() != 'y'
    return False

def task3_chart(force=False):
    """График динамики успеваемости по месяцам"""
    conn = get_connection()
    cur = conn.cursor()
    
    perf_table = get_table('performance')
    date_field = get_field('performance', 'date')
    grade_field = get_field('performance', 'grade')
    
    sql = f"""
    SELECT 
        DATE_TRUNC('month', {date_field}) as месяц,
        ROUND(AVG({grade_field}), 2) as средний_балл,
        COUNT(*) as количество_оценок
    FROM {perf_table}
    WHERE {date_field} IS NOT NULL
    GROUP BY DATE_TRUNC('month', {date_field})
    ORDER BY месяц
    """
    
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        print("Нет данных для построения графика")
        return
    
    months = [row[0] for row in rows]
    avg_grades = [float(row[1]) for row in rows]
    counts = [int(row[2]) for row in rows]
    
    fig, ax1 = plt.subplots(figsize=(12, 5))
    
    ax1.set_xlabel('Дата')
    ax1.set_ylabel('Средний балл', color='blue')
    ax1.plot(months, avg_grades, color='blue', marker='o', linewidth=2, label='Средний балл')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.set_ylim(2, 5)
    
    ax2 = ax1.twinx()
    ax2.set_ylabel('Количество оценок', color='red')
    ax2.bar(months, counts, color='red', alpha=0.3, label='Количество оценок')
    ax2.tick_params(axis='y', labelcolor='red')
    
    plt.title('Динамика успеваемости по месяцам')
    plt.xticks(rotation=45, ha='right')
    fig.tight_layout()
    
    filename = 'docs/task3_chart.png'
    if not file_exists(filename, force):
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f" График сохранён в {filename}")
    else:
        print(" Сохранение отменено")
    
    plt.close()

def task4_chart(group_filter=None, force=False):
    """Диаграмма среднего балла по группам"""
    conn = get_connection()
    cur = conn.cursor()
    
    groups_table = get_table('groups')
    perf_table = get_table('performance')
    group_id_field = get_field('groups', 'id')
    group_name_field = get_field('groups', 'name')
    perf_group_field = get_field('performance', 'group')
    perf_grade_field = get_field('performance', 'grade')
    perf_id_field = get_field('performance', 'id')
    
    if group_filter:
        sql = f"""
        SELECT 
            g.{group_name_field} as группа,
            ROUND(AVG(u.{perf_grade_field}), 2) as средний_балл
        FROM {groups_table} g
        LEFT JOIN {perf_table} u ON u.{perf_group_field} = g.{group_id_field}
        WHERE g.{group_name_field} ILIKE %s
        GROUP BY g.{group_id_field}, g.{group_name_field}
        HAVING COUNT(u.{perf_id_field}) > 0
        ORDER BY средний_балл DESC
        """
        cur.execute(sql, (f"%{group_filter}%",))
        filename = f'docs/task4_chart_{group_filter}.png'
        title = f'Средний балл по группам (фильтр: {group_filter})'
    else:
        sql = f"""
        SELECT 
            g.{group_name_field} as группа,
            ROUND(AVG(u.{perf_grade_field}), 2) as средний_балл
        FROM {groups_table} g
        LEFT JOIN {perf_table} u ON u.{perf_group_field} = g.{group_id_field}
        GROUP BY g.{group_id_field}, g.{group_name_field}
        HAVING COUNT(u.{perf_id_field}) > 0
        ORDER BY средний_балл DESC
        """
        cur.execute(sql)
        filename = 'docs/task4_chart.png'
        title = 'Средний балл по группам'
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        print("Нет данных для построения диаграммы")
        return
    
    labels = [row[0] for row in rows]
    sizes = [float(row[1]) for row in rows]
    
    plt.figure(figsize=(10, 8))
    bars = plt.bar(labels, sizes, color='skyblue', edgecolor='navy')
    plt.title(title)
    plt.xlabel('Группы')
    plt.ylabel('Средний балл')
    plt.ylim(2, 5)
    plt.xticks(rotation=45, ha='right')
    
    for bar, val in zip(bars, sizes):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, 
                 f'{val:.2f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    if not file_exists(filename, force):
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f" Диаграмма сохранена в {filename}")
    else:
        print(" Сохранение отменено")
    
    plt.close()

def save_all(force=False):
    print("Сохранение всех графиков и диаграмм...")
    task3_chart(force)
    task4_chart(force=force)
    task4_chart("ИНФ", force=force)
    print("Все изображения сохранены в папку docs/")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python analytics_chart.py task3 [--force]")
        print("             python analytics_chart.py task4 [фильтр] [--force]")
        print("             python analytics_chart.py save-all [--force]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    force = '--force' in sys.argv
    
    if command == "task3":
        task3_chart(force)
    elif command == "task4":
        group_filter = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != '--force' else None
        task4_chart(group_filter, force)
    elif command == "save-all":
        save_all(force)
    else:
        print(f"Неизвестная команда: {command}")
