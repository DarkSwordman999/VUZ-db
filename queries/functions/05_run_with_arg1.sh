#!/bin/bash
# Запуск с параметром :arg1 для задачи 1
# Пример: ./05_run_with_arg1.sh 4.5

if [ -z "$1" ]; then
    echo "Использование: $0 <порог_среднего_балла>"
    echo "Пример: $0 4.5"
    exit 1
fi

psql -d vuz_lab5 -v arg1="$1" -f queries/lab7/04_run_lab7.sql
