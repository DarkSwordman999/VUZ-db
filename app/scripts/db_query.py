#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import psycopg2
import sys
from db_config import DB_CONFIG

def get_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        print(f"Ошибка подключения: {e}")
        sys.exit(1)

def execute_query(sql, params=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        if sql.strip().upper().startswith('SELECT'):
            rows = cur.fetchall()
            colnames = [desc[0] for desc in cur.description]
            print(' | '.join(colnames))
            print('-' * 50)
            for row in rows[:50]:
                print(' | '.join(str(v) for v in row))
            if len(rows) > 50:
                print(f'... и ещё {len(rows) - 50} строк')
            print(f'\nВсего строк: {len(rows)}')
        else:
            conn.commit()
            print(f"Затронуто строк: {cur.rowcount}")
    except psycopg2.Error as e:
        print(f"Ошибка: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python db_query.py <SQL>")
        sys.exit(1)
    execute_query(sys.argv[1])
