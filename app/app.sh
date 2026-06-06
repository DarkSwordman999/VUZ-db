#!/bin/bash
DB_NAME="vuz_lab5"

show_help() {
    echo "============================================="
    echo "  ПРИЛОЖЕНИЕ ДЛЯ РАБОТЫ С БД ВУЗ"
    echo "============================================="
    echo ""
    echo "  ./app.sh top [N]           - топ N студентов"
    echo "  ./app.sh weak [N]          - худшие N студентов"
    echo "  ./app.sh grades            - распределение оценок"
    echo "  ./app.sh season            - средний балл по сезонам"
    echo "  ./app.sh sql <файл>        - выполнить SQL из файла"
    echo "  ./app.sh query <sql>       - выполнить произвольный SQL"
    echo ""
    echo "Примеры:"
    echo "  ./app.sh top 10"
    echo "  ./app.sh query 'SELECT * FROM СТУДЕНТЫ LIMIT 5'"
}

case "$1" in
    top)
        N=${2:-10}
        psql -d $DB_NAME -c "SELECT фамилия, имя, ROUND(AVG(оценка),2) as средний_балл FROM СТУДЕНТЫ s JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код GROUP BY s.код ORDER BY средний_балл DESC LIMIT $N;"
        ;;
    weak)
        N=${2:-10}
        psql -d $DB_NAME -c "SELECT фамилия, имя, ROUND(AVG(оценка),2) as средний_балл FROM СТУДЕНТЫ s JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код GROUP BY s.код ORDER BY средний_балл ASC LIMIT $N;"
        ;;
    grades)
        psql -d $DB_NAME -c "SELECT оценка, COUNT(*) as количество FROM УСПЕВАЕМОСТЬ GROUP BY оценка ORDER BY оценка;"
        ;;
    season)
        psql -d $DB_NAME -c "SELECT s.название as сезон, ROUND(AVG(u.оценка),2) as средний_балл FROM УСПЕВАЕМОСТЬ u JOIN ВРЕМЕНА_ГОДА s ON s.код = u.сезон GROUP BY s.код, s.название ORDER BY s.код;"
        ;;
    sql)
        if [ -z "$2" ]; then
            echo "Укажите SQL файл"
            exit 1
        fi
        psql -d $DB_NAME -f "$2"
        ;;
    query)
        if [ -z "$2" ]; then
            echo "Укажите SQL запрос"
            exit 1
        fi
        psql -d $DB_NAME -c "$2"
        ;;
    *)
        show_help
        ;;
esac
