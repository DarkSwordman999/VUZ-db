#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
import sys
from collections import defaultdict
from db_config import DB_CONFIG
from db_schema_config import get_table, get_field, get_default_subjects

def get_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        print(f"Ошибка подключения: {e}")
        sys.exit(1)

def print_table(rows, headers, alignments=None):
    """Универсальная функция печати таблицы"""
    if not rows:
        return
    
    col_widths = []
    for i in range(len(headers)):
        max_width = len(str(headers[i]))
        for row in rows:
            if i < len(row):
                max_width = max(max_width, len(str(row[i])))
        col_widths.append(min(max_width, 30))
    
    if alignments is None:
        alignments = ['l'] * len(headers)
    
    print('┌' + '┬'.join('─' * (w + 2) for w in col_widths) + '┐')
    
    row_line = '│'
    for i, h in enumerate(headers):
        display = str(h)[:col_widths[i]]
        if alignments[i] == 'r':
            row_line += f' {display:>{col_widths[i]}} │'
        else:
            row_line += f' {display:<{col_widths[i]}} │'
    print(row_line)
    
    print('├' + '┼'.join('─' * (w + 2) for w in col_widths) + '┤')
    
    for row in rows:
        row_line = '│'
        for i, cell in enumerate(row):
            display = str(cell)[:col_widths[i]]
            if i < len(alignments) and alignments[i] == 'r':
                row_line += f' {display:>{col_widths[i]}} │'
            else:
                row_line += f' {display:<{col_widths[i]}} │'
        print(row_line)
    
    print('└' + '┴'.join('─' * (w + 2) for w in col_widths) + '┘')

def task1_report(group_param=None, subject_param=None):
    """Отчет по группам и дисциплинам"""
    conn = get_connection()
    cur = conn.cursor()
    
    groups_table = get_table('groups')
    subjects_table = get_table('subjects')
    perf_table = get_table('performance')
    
    group_id_field = get_field('groups', 'id')
    group_name_field = get_field('groups', 'name')
    subject_id_field = get_field('subjects', 'id')
    subject_name_field = get_field('subjects', 'name')
    perf_group_field = get_field('performance', 'group')
    perf_subject_field = get_field('performance', 'subject')
    perf_grade_field = get_field('performance', 'grade')
    perf_id_field = get_field('performance', 'id')
    
    sql = f"""
    SELECT 
        g.{group_name_field} AS группа,
        d.{subject_name_field} AS дисциплина,
        ROUND(COALESCE(AVG(u.{perf_grade_field}), 0), 2) AS средний_балл,
        COUNT(u.{perf_id_field}) AS количество_оценок
    FROM {groups_table} g
    CROSS JOIN {subjects_table} d
    LEFT JOIN {perf_table} u ON u.{perf_group_field} = g.{group_id_field} AND u.{perf_subject_field} = d.{subject_id_field}
    GROUP BY g.{group_id_field}, g.{group_name_field}, d.{subject_id_field}, d.{subject_name_field}
    ORDER BY группа, дисциплина
    """
    
    cur.execute(sql)
    rows = cur.fetchall()
    
    if group_param or subject_param:
        filtered = []
        for group, subject, avg_grade, count in rows:
            if group_param and group_param.lower() not in group.lower():
                continue
            if subject_param and subject_param.lower() not in subject.lower():
                continue
            filtered.append((group, subject, avg_grade, count))
        rows = filtered
    
    print()
    print('=' * 80)
    print('  ОТЧЁТ: СРЕДНИЙ БАЛЛ ПО ГРУППАМ И ДИСЦИПЛИНАМ')
    print('=' * 80)
    if group_param:
        print(f'  Параметр: группа = {group_param}')
    if subject_param:
        print(f'  Параметр: дисциплина = {subject_param}')
    print('-' * 80)
    
    if not rows:
        print("  Данные не найдены")
        cur.close()
        conn.close()
        return
    
    table_rows = []
    current_group = None
    group_total = 0
    group_count = 0
    grand_total = 0
    grand_count = 0
    row_num = 1
    
    for group, subject, avg_grade, count in rows:
        avg_grade = float(avg_grade)
        count = int(count)
        
        if current_group != group and current_group is not None:
            avg_group = group_total / group_count if group_count > 0 else 0
            table_rows.append(['', current_group, 'ИТОГ ПО ГРУППЕ:', f'{avg_group:.2f}', str(group_count)])
            current_group = group
            group_total = 0
            group_count = 0
        
        if current_group != group:
            current_group = group
        
        short_subject = subject[:35] + '...' if len(subject) > 35 else subject
        table_rows.append([row_num, group, short_subject, f'{avg_grade:.2f}', str(count)])
        
        if count > 0:
            group_total += avg_grade
            group_count += 1
            grand_total += avg_grade
            grand_count += 1
        
        row_num += 1
    
    if current_group:
        avg_group = group_total / group_count if group_count > 0 else 0
        table_rows.append(['', current_group, 'ИТОГ ПО ГРУППЕ:', f'{avg_group:.2f}', str(group_count)])
    
    avg_total = grand_total / grand_count if grand_count > 0 else 0
    table_rows.append(['', 'ВСЕГО', '', f'{avg_total:.2f}', str(grand_count)])
    
    headers = ['№', 'Группа', 'Дисциплина', 'Ср. балл', 'Оценок']
    alignments = ['r', 'l', 'l', 'r', 'r']
    print_table(table_rows, headers, alignments)
    
    cur.close()
    conn.close()

def task2_pivot_table(group_filter=None):
    """Сводная таблица: группы × дисциплины (только топ-6)"""
    conn = get_connection()
    cur = conn.cursor()
    
    subjects_table = get_table('subjects')
    perf_table = get_table('performance')
    groups_table = get_table('groups')
    
    subject_id_field = get_field('subjects', 'id')
    subject_name_field = get_field('subjects', 'name')
    perf_subject_field = get_field('performance', 'subject')
    perf_id_field = get_field('performance', 'id')
    perf_group_field = get_field('performance', 'group')
    perf_grade_field = get_field('performance', 'grade')
    group_id_field = get_field('groups', 'id')
    group_name_field = get_field('groups', 'name')
    
    # Берём список дисциплин из конфига
    subjects_list = get_default_subjects()
    subjects_quoted = "', '".join(subjects_list)
    
    sql = f"""
    SELECT 
        g.{group_name_field} AS группа,
        d.{subject_name_field} AS дисциплина,
        ROUND(COALESCE(AVG(u.{perf_grade_field}), 0), 2) AS средний_балл
    FROM {groups_table} g
    CROSS JOIN {subjects_table} d
    LEFT JOIN {perf_table} u ON u.{perf_group_field} = g.{group_id_field} AND u.{perf_subject_field} = d.{subject_id_field}
    WHERE d.{subject_name_field} IN ('{subjects_quoted}')
    GROUP BY g.{group_id_field}, g.{group_name_field}, d.{subject_id_field}, d.{subject_name_field}
    ORDER BY группа, дисциплина
    """
    
    cur.execute(sql)
    rows = cur.fetchall()
    
    data = {}
    groups_set = set()
    subjects = subjects_list
    
    for group, subject, avg_grade in rows:
        if group_filter and group_filter.lower() not in group.lower():
            continue
        
        avg_grade = float(avg_grade)
        
        if group not in data:
            data[group] = {}
        short_subj = subject[:10] + '..' if len(subject) > 10 else subject
        data[group][short_subj] = avg_grade
        groups_set.add(group)
    
    groups = sorted(groups_set)[:10]
    
    print()
    print('=' * 80)
    print('  СВОДНАЯ ТАБЛИЦА: СРЕДНИЙ БАЛЛ ПО ГРУППАМ')
    print('=' * 80)
    if group_filter:
        print(f'  Фильтр: группы, содержащие "{group_filter}"')
    print('-' * 80)
    
    if not groups:
        print("  Нет данных для отображения")
        cur.close()
        conn.close()
        return
    
    table_rows = []
    for group in groups:
        row = [group]
        for subj in subjects:
            short_subj = subj[:10] + '..' if len(subj) > 10 else subj
            val = data.get(group, {}).get(short_subj, 0)
            row.append(f'{val:.2f}' if val > 0 else '-')
        table_rows.append(row)
    
    headers = ['Группа'] + subjects
    print_table(table_rows, headers, ['l'] + ['r'] * len(subjects))
    
    cur.close()
    conn.close()

def task3_chart(force=False):
    """График динамики - заглушка, импортируем из analytics_chart"""
    from analytics_chart import task3_chart as t3
    t3(force)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python analytics_report.py task1 [группа] [дисциплина]")
        print("             python analytics_report.py task2 [фильтр]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "task1":
        group_param = sys.argv[2] if len(sys.argv) > 2 else None
        subject_param = sys.argv[3] if len(sys.argv) > 3 else None
        task1_report(group_param, subject_param)
    elif command == "task2":
        group_filter = sys.argv[2] if len(sys.argv) > 2 else None
        task2_pivot_table(group_filter)
    else:
        print(f"Неизвестная команда: {command}")
