# -*- coding: utf-8 -*-
"""
Конфигурация схемы базы данных
Все названия таблиц и полей вынесены в отдельный файл
"""

SCHEMA = {
    'tables': {
        'students': 'СТУДЕНТЫ',
        'groups': 'ГРУППЫ',
        'teachers': 'ПРЕПОДАВАТЕЛИ',
        'subjects': 'ДИСЦИПЛИНЫ',
        'performance': 'УСПЕВАЕМОСТЬ',
        'performance_archive': 'УСПЕВАЕМОСТЬ_АРХИВ',
        'students_stats': 'СТУДЕНТЫ_СТАТИСТИКА',
    },
    'fields': {
        'students': {
            'id': 'код',
            'last_name': 'фамилия',
            'first_name': 'имя',
            'middle_name': 'отчество',
            'phone': 'телефон',
            'email': 'email',
            'enrollment_date': 'дата_поступления',
        },
        'groups': {
            'id': 'код',
            'name': 'название',
            'faculty': 'факультет',
            'course': 'курс',
        },
        'teachers': {
            'id': 'код',
            'last_name': 'фамилия',
            'first_name': 'имя',
            'middle_name': 'отчество',
            'position': 'должность',
        },
        'subjects': {
            'id': 'код',
            'name': 'название',
        },
        'performance': {
            'id': 'код_записи',
            'student': 'студент',
            'group': 'группа',
            'subject': 'дисциплина',
            'teacher': 'преподаватель',
            'grade': 'оценка',
            'date': 'дата',
        },
        'performance_archive': {
            'archive_date': 'archive_date',
        },
        'students_stats': {
            'student_id': 'студент_код',
            'avg_grade': 'средний_балл',
            'grade_count': 'количество_оценок',
            'updated_at': 'updated_at',
        },
    }
}

def get_table(name):
    """Возвращает имя таблицы по ключу"""
    return SCHEMA['tables'].get(name, name)

def get_field(table, name):
    """Возвращает имя поля по таблице и ключу"""
    return SCHEMA['fields'].get(table, {}).get(name, name)

def get_full_field(table, field):
    """Возвращает полное имя поля с таблицей (таблица.поле)"""
    return f"{get_table(table)}.{get_field(table, field)}"

# Список дисциплин для сводной таблицы (топ-6 по умолчанию)
DEFAULT_SUBJECTS = [
    'Базы данных',
    'Программирование',
    'Web-дизайн',
    'Информатика',
    'Математика',
    'Английский язык',
]

def get_default_subjects():
    """Возвращает список дисциплин для сводной таблицы"""
    return DEFAULT_SUBJECTS
