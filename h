#!/bin/bash
DATABASE="vuz_lab5"

if [ -z "$1" ]; then
    echo "============================================="
    echo "  СИСТЕМА УЧЁТА УСПЕВАЕМОСТИ ВУЗ"
    echo "============================================="
    echo ""
    echo "================== ОСНОВНЫЕ ЗАДАЧИ =================="
    echo "  ./h task1 - средний балл по сезонам"
    echo "  ./h task2 - средний балл по факультетам и сезонам"
    echo "  ./h task3 - средний балл по дням недели и преподавателям"
    echo "  ./h task4 день - средний балл по дисциплинам за день"
    echo ""
    echo "================== РЕЙТИНГИ =================="
    echo "  ./h top [N] - топ N студентов по успеваемости (по умолчанию 10)"
    echo "  ./h weak [N] - худшие N студентов"
    echo ""
    echo "================== ПРОСМОТР ДАННЫХ =================="
    echo "  ./h 01 - все студенты"
    echo "  ./h 02 - все группы"
    echo "  ./h 03 - все преподаватели"
    echo "  ./h 04 - все дисциплины"
    echo "  ./h 05 - количество записей"
    echo "  ./h 06 - примеры успеваемости"
    echo "  ./h 15 - структура таблиц"
    echo ""
    echo "================== ДЕМОНСТРАЦИЯ JOIN =================="
    echo "  ./h 07 - INNER JOIN"
    echo "  ./h 08 - LEFT JOIN"
    echo "  ./h 09 - перекрёстное соединение"
    echo ""
    echo "================== ПОКАЗАТЬ ДО/ПОСЛЕ =================="
    echo "  ./h 10 - ДО UPDATE"
    echo "  ./h 11 - ПОСЛЕ UPDATE"
    echo "  ./h 12 - ДО DELETE"
    echo "  ./h 13 - ПОСЛЕ DELETE"
    echo ""
    echo "================== АНАЛИТИКА =================="
    echo "  ./h 16 - топ-10 студентов"
    echo "  ./h 17 - топ-10 преподавателей"
    echo "  ./h 18 - распределение оценок"
    echo "  ./h 19 - успеваемость по курсам"
    echo ""
    echo "================== ЗАПРОСЫ С ПАРАМЕТРАМИ =================="
    echo "  ./h 14 факультет - группы по факультету"
    echo "  ./h 20 фамилия - поиск студента"
    echo "  ./h 40 код телефон - обновить телефон студента"
    echo "  ./h 41 код - удалить студента"
    echo "  ./h 42 студент дисциплина оценка - обновить оценку"
    echo "  ./h 43 текст - быстрый поиск студента"
    echo "  ./h 44 группа - статистика группы"
    echo "  ./h 53 фамилия имя телефон email - добавить студента"
    echo ""
    echo "================== РЕДАКТИРОВАНИЕ =================="
    echo "  ./h 30 - изменить телефон студента код=1"
    echo "  ./h 31 - изменить дисциплину код=1"
    echo "  ./h 32 - повысить оценки студентам 1 2 3"
    echo "  ./h 33 - удалить студента код=50"
    echo "  ./h 34 - удалить все оценки 2"
    echo "  ./h 35 - добавить студента"
    echo "  ./h 36 - добавить дисциплину"
    echo "  ./h 61 - повысить курс групп"
    echo "  ./h 62 - изменить должность преподавателя"
    echo "  ./h 64 - INSERT SELECT копирование в архив"
    echo ""
    echo "================== РУЧНОЙ ВВОД =================="
    echo "  ./h 70 - добавить студента интерактивно"
    echo "  ./h 71 - добавить оценку интерактивно"
    echo "  ./h 72 - добавить дисциплину интерактивно"
    echo "  ./h 73 - редактировать студента интерактивно"
    echo "  ./h 74 - удалить студента интерактивно"
    echo "  ./h 75 - полный список студентов"
    echo "  ./h 76 - успеваемость студента"
    echo ""
    echo "================== ПРЕДСТАВЛЕНИЯ =================="
    echo "  ./h 100 - создать пользовательское представление"
    echo "  ./h 101 - создать технологическое представление"
    echo "  ./h 102 - проверить представления"
    echo ""
    echo "================== ПОДЗАПРОСЫ =================="
    echo "  ./h 110 - задача 1.1 отклонение среднего балла"
    echo "  ./h 111 - задача 1.2 рейтинг преподавателей"
    echo "  ./h 112 - задача 2.1 студенты выше среднего"
    echo "  ./h 113 - задача 2.2 статистика по факультетам"
    echo "  ./h 114 - задача 3.1 топ-3 студента на факультете"
    echo "  ./h 115 дисциплина - задача 4.1 оценки выше среднего"
    echo "  ./h 116 - задача 4.2 студенты без троек и двоек"
    echo "  ./h 117 - задача 4.3 лучшие студенты ALL"
    echo "  ./h 199 - выполнить все задачи"
    echo ""
    echo "================== ФУНКЦИИ =================="
    echo "  ./h 200 - создать все функции"
    echo "  ./h 201 порог - студенты со средним баллом выше порога"
    echo "  ./h 202 - средний балл по факультетам и сезонам"
    echo "  ./h 203 - сводная таблица (группы x дисциплины)"
    echo "  ./h 204 - выполнить всё"
    echo ""
    echo "================== ЗАПУСК ЛЮБОГО SQL ФАЙЛА =================="
    echo "  ./h файл.sql параметр - выполнить любой SQL-файл"
    exit 1
fi

if [[ "$1" == *.sql ]]; then
    if [ -f "$1" ]; then
        if [ -z "$2" ]; then
            psql -d $DATABASE -f "$1"
        else
            psql -d $DATABASE -f "$1" -v arg1="$2"
        fi
    else
        echo "ОШИБКА: Файл $1 не найден"
        exit 1
    fi
    exit 0
fi

case "$1" in
    task1) psql -d $DATABASE -f queries/tasks/01_avg_grade_by_season.sql ;;
    task2) psql -d $DATABASE -f queries/tasks/02_grades_by_faculty_and_season.sql ;;
    task3) psql -d $DATABASE -f queries/tasks/03_grades_by_day_and_teacher.sql ;;
    task4)
        if [ -z "$2" ]; then
            echo "ОШИБКА: Укажите день недели 1-7"
            exit 1
        elif ! [[ "$2" =~ ^[0-9]+$ ]]; then
            echo "ОШИБКА: День должен быть числом"
            exit 1
        elif [ "$2" -lt 1 ] || [ "$2" -gt 7 ]; then
            echo "ОШИБКА: День должен быть от 1 до 7"
            exit 1
        else
            psql -d $DATABASE -v arg1="$2" -f queries/tasks/04_avg_grade_by_subject_for_day.sql
        fi
        ;;
    top)
        if [ -z "$2" ]; then
            psql -d $DATABASE -v limit=10 -f helper/top_students.sql
        elif [[ "$2" =~ ^[0-9]+$ ]]; then
            psql -d $DATABASE -v limit="$2" -f helper/top_students.sql
        else
            echo "ОШИБКА: Параметр должен быть числом"
            echo "Пример: ./h top 15"
        fi
        ;;
    weak)
        if [ -z "$2" ]; then
            psql -d $DATABASE -v limit=10 -f helper/weak_students.sql
        elif [[ "$2" =~ ^[0-9]+$ ]]; then
            psql -d $DATABASE -v limit="$2" -f helper/weak_students.sql
        else
            echo "ОШИБКА: Параметр должен быть числом"
        fi
        ;;
    01) psql -d $DATABASE -c "SELECT * FROM СТУДЕНТЫ ORDER BY код;" ;;
    02) psql -d $DATABASE -c "SELECT * FROM ГРУППЫ ORDER BY код;" ;;
    03) psql -d $DATABASE -c "SELECT * FROM ПРЕПОДАВАТЕЛИ ORDER BY код;" ;;
    04) psql -d $DATABASE -c "SELECT * FROM ДИСЦИПЛИНЫ ORDER BY код;" ;;
    05) psql -d $DATABASE -f helper/05_show_counts.sql ;;
    06) psql -d $DATABASE -f helper/06_show_performance_sample.sql ;;
    15) psql -d $DATABASE -f helper/15_show_table_structure.sql ;;
    07) psql -d $DATABASE -f helper/07_demo_inner_join.sql ;;
    08) psql -d $DATABASE -f helper/08_demo_left_join.sql ;;
    09) psql -d $DATABASE -f helper/09_demo_cross_join.sql ;;
    10) psql -d $DATABASE -f helper/10_demo_update_before.sql ;;
    11) psql -d $DATABASE -f helper/11_demo_update_after.sql ;;
    12) psql -d $DATABASE -f helper/12_demo_delete_before.sql ;;
    13) psql -d $DATABASE -f helper/13_demo_delete_after.sql ;;
    16) psql -d $DATABASE -f helper/16_top_10_students.sql ;;
    17) psql -d $DATABASE -f helper/17_top_10_teachers.sql ;;
    18) psql -d $DATABASE -f helper/18_grade_distribution.sql ;;
    19) psql -d $DATABASE -f helper/19_performance_by_course.sql ;;
    14)
        if [ -z "$2" ]; then
            psql -d $DATABASE -v arg1='Информационных технологий' -f helper/14_demo_with_param.sql
        else
            psql -d $DATABASE -v arg1="$2" -f helper/14_demo_with_param.sql
        fi
        ;;
    20)
        if [ -z "$2" ]; then
            psql -d $DATABASE -v name='Иванов' -f helper/20_search_student.sql
        else
            psql -d $DATABASE -v name="$2" -f helper/20_search_student.sql
        fi
        ;;
    40)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Использование: ./h 40 код_студента новый_телефон"
        else
            psql -d $DATABASE -c "UPDATE СТУДЕНТЫ SET телефон = '$3' WHERE код = $2; SELECT * FROM СТУДЕНТЫ WHERE код = $2;"
        fi
        ;;
    41)
        if [ -z "$2" ]; then
            echo "Использование: ./h 41 код_студента"
        else
            psql -d $DATABASE -c "DELETE FROM УСПЕВАЕМОСТЬ WHERE студент = $2; DELETE FROM СТУДЕНТЫ WHERE код = $2;"
            echo "Студент удалён"
        fi
        ;;
    42)
        if [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
            echo "Использование: ./h 42 студент дисциплина оценка"
        else
            psql -d $DATABASE -c "UPDATE УСПЕВАЕМОСТЬ SET оценка = $4 WHERE студент = $2 AND дисциплина = $3;"
        fi
        ;;
    43)
        if [ -z "$2" ]; then
            psql -d $DATABASE -c "SELECT код, фамилия, имя, телефон, email FROM СТУДЕНТЫ WHERE фамилия LIKE '%Иван%' OR имя LIKE '%Иван%' LIMIT 10;"
        else
            psql -d $DATABASE -c "SELECT код, фамилия, имя, телефон, email FROM СТУДЕНТЫ WHERE фамилия LIKE '%$2%' OR имя LIKE '%$2%' LIMIT 10;"
        fi
        ;;
    44)
        if [ -z "$2" ]; then
            psql -d $DATABASE -c "SELECT ГРУППЫ.название, AVG(УСПЕВАЕМОСТЬ.оценка) as avg_grade FROM УСПЕВАЕМОСТЬ JOIN ГРУППЫ ON ГРУППЫ.код = УСПЕВАЕМОСТЬ.группа WHERE ГРУППЫ.название = 'ИНФ-101' GROUP BY ГРУППЫ.название;"
        else
            psql -d $DATABASE -c "SELECT ГРУППЫ.название, AVG(УСПЕВАЕМОСТЬ.оценка) as avg_grade FROM УСПЕВАЕМОСТЬ JOIN ГРУППЫ ON ГРУППЫ.код = УСПЕВАЕМОСТЬ.группа WHERE ГРУППЫ.название = '$2' GROUP BY ГРУППЫ.название;"
        fi
        ;;
    53)
        if [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] || [ -z "$5" ]; then
            echo "Использование: ./h 53 фамилия имя телефон email"
        else
            psql -d $DATABASE -c "INSERT INTO СТУДЕНТЫ (фамилия, имя, телефон, email) VALUES ('$2', '$3', '$4', '$5'); SELECT * FROM СТУДЕНТЫ ORDER BY код DESC LIMIT 1;"
        fi
        ;;
    30) psql -d $DATABASE -f queries/update/01_update_student_phone.sql ;;
    31) psql -d $DATABASE -f queries/update/02_update_subject.sql ;;
    32) psql -d $DATABASE -f queries/update/03_update_grade_in.sql ;;
    33) psql -d $DATABASE -f queries/delete/01_delete_student.sql ;;
    34) psql -d $DATABASE -f queries/delete/02_delete_bad_grades.sql ;;
    35) psql -d $DATABASE -f queries/insert/01_insert_student.sql ;;
    36) psql -d $DATABASE -f queries/insert/02_insert_subject.sql ;;
    61) psql -d $DATABASE -f queries/update/05_update_course.sql ;;
    62) psql -d $DATABASE -f queries/update/06_update_teacher_position.sql ;;
    64) psql -d $DATABASE -f queries/insert/03_insert_select.sql ;;
    70) psql -d $DATABASE -f helper/manual_insert_student.sql ;;
    71) psql -d $DATABASE -f helper/manual_insert_grade.sql ;;
    72) psql -d $DATABASE -f helper/manual_insert_subject.sql ;;
    73) psql -d $DATABASE -f helper/manual_update_student.sql ;;
    74) psql -d $DATABASE -f helper/manual_delete_student.sql ;;
    75) psql -d $DATABASE -f helper/manual_view_all.sql ;;
    76) psql -d $DATABASE -f helper/manual_view_student_grades.sql ;;
    100) psql -d $DATABASE -f queries/views/01_create_performance_view.sql ;;
    101) psql -d $DATABASE -f queries/views/02_create_performance_tech.sql ;;
    102) psql -d $DATABASE -f queries/views/03_check_views.sql ;;
    110) psql -d $DATABASE -f queries/subqueries/01_avg_grade_deviation.sql ;;
    111) psql -d $DATABASE -f queries/subqueries/02_teacher_rating.sql ;;
    112) psql -d $DATABASE -f queries/subqueries/03_students_above_avg.sql ;;
    113) psql -d $DATABASE -f queries/subqueries/04_faculty_stats.sql ;;
    114) psql -d $DATABASE -f queries/subqueries/05_top_students_lateral.sql ;;
    115)
        if [ -z "$2" ]; then
            echo "Использование: ./h 115 дисциплина"
            echo "Пример: ./h 115 'Базы данных'"
        else
            psql -d $DATABASE -v arg1="$2" -f queries/subqueries/06_grades_above_avg.sql
        fi
        ;;
    116) psql -d $DATABASE -f queries/subqueries/07_good_students_exists.sql ;;
    117) psql -d $DATABASE -f queries/subqueries/08_best_students_all.sql ;;
    199)
        echo "============================================="
        echo "ПОДЗАПРОСЫ - ВСЕ ЗАДАЧИ"
        echo "============================================="
        psql -d $DATABASE -f queries/views/03_check_views.sql
        psql -d $DATABASE -f queries/subqueries/01_avg_grade_deviation.sql
        psql -d $DATABASE -f queries/subqueries/02_teacher_rating.sql
        psql -d $DATABASE -f queries/subqueries/03_students_above_avg.sql
        psql -d $DATABASE -f queries/subqueries/04_faculty_stats.sql
        psql -d $DATABASE -f queries/subqueries/05_top_students_lateral.sql
        psql -d $DATABASE -v arg1='Базы данных' -f queries/subqueries/06_grades_above_avg.sql
        psql -d $DATABASE -f queries/subqueries/07_good_students_exists.sql
        psql -d $DATABASE -f queries/subqueries/08_best_students_all.sql
        ;;
    200)
        echo "============================================="
        echo "ФУНКЦИИ АНАЛИТИКИ"
        echo "============================================="
        psql -d $DATABASE -f queries/functions/01_students_above_threshold.sql
        psql -d $DATABASE -f queries/functions/02_grades_by_faculty_season.sql
        psql -d $DATABASE -f queries/functions/03_pivot_table.sql
        echo "Все функции созданы"
        ;;
    201)
        if [ -z "$2" ]; then
            echo "Использование: ./h 201 <порог>"
            echo "Пример: ./h 201 4.5"
            echo ""
            echo "=== Без параметра (порог 4.0) ==="
            psql -d $DATABASE -f queries/functions/04_run_all_functions.sql -v arg1=4.0
        else
            psql -d $DATABASE -f queries/functions/04_run_all_functions.sql -v arg1="$2"
        fi
        ;;
    202)
        echo "============================================="
        echo "СРЕДНИЙ БАЛЛ ПО ФАКУЛЬТЕТАМ И СЕЗОНАМ"
        echo "============================================="
        psql -d $DATABASE -c "SELECT факультет, сезон, средний_балл, количество_оценок FROM grades_by_faculty_and_season() ORDER BY факультет, порядок_сезона;"
        ;;
    203)
        echo "============================================="
        echo "СВОДНАЯ ТАБЛИЦА (ГРУППЫ x ДИСЦИПЛИНЫ)"
        echo "============================================="
        psql -d $DATABASE -c "SELECT * FROM display_pivot_table();"
        ;;
    204)
        echo "============================================="
        echo "ВСЕ ФУНКЦИИ АНАЛИТИКИ"
        echo "============================================="
        ./h 200
        echo ""
        echo "=== ЗАДАЧА 1 (порог 4.5) ==="
        ./h 201 4.5
        echo ""
        echo "=== ЗАДАЧА 2 ==="
        ./h 202
        echo ""
        echo "=== ЗАДАЧА 3 ==="
        ./h 203
        ;;
    *) echo "ОШИБКА: Неизвестная команда $1" ;;
esac
