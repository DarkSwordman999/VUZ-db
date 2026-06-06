-- ============================================================
-- ЛАБОРАТОРНАЯ РАБОТА №7
-- ЗАДАЧА 1: Распределение по одному признаку
-- Средний балл студентов с параметром порога
-- ============================================================

-- Функция 1.1: Скалярная функция - средний балл студента
DROP FUNCTION IF EXISTS get_student_avg_grade(INT);

CREATE OR REPLACE FUNCTION get_student_avg_grade(p_student_code INT)
RETURNS NUMERIC(3,2) AS $$
/*
  НАЗНАЧЕНИЕ: Вычисляет средний балл указанного студента
  ВХОД: p_student_code - код студента из таблицы СТУДЕНТЫ
  ВЫХОД: средний балл (2.00 - 5.00) или NULL, если оценок нет
  АЛГОРИТМ: Выполняет AVG(оценка) из таблицы УСПЕВАЕМОСТЬ
*/
BEGIN
    RETURN (
        SELECT ROUND(AVG(оценка), 2)
        FROM УСПЕВАЕМОСТЬ
        WHERE студент = p_student_code
    );
END;
$$ LANGUAGE PLpgSQL;

-- Функция 1.2: Табличная функция - студенты с баллом выше порога
DROP FUNCTION IF EXISTS students_above_grade(NUMERIC);

CREATE OR REPLACE FUNCTION students_above_grade(p_min_grade NUMERIC DEFAULT 4.0)
RETURNS TABLE(
    студент_код INT,
    фамилия VARCHAR,
    имя VARCHAR,
    средний_балл NUMERIC(3,2),
    количество_оценок BIGINT
) AS $$
/*
  НАЗНАЧЕНИЕ: Возвращает список студентов со средним баллом выше порога
  ВХОД: p_min_grade - минимальный средний балл (по умолчанию 4.0)
  ВЫХОД: таблица с колонками:
    - студент_код - код студента
    - фамилия - фамилия студента
    - имя - имя студента
    - средний_балл - средний балл (округлён)
    - количество_оценок - число оценок у студента
  АЛГОРИТМ: Запрос к СТУДЕНТЫ с фильтрацией через get_student_avg_grade
  ОСОБЕННОСТИ: Использует скалярную функцию get_student_avg_grade
*/
BEGIN
    RETURN QUERY
    SELECT 
        СТ.код,
        СТ.фамилия,
        СТ.имя,
        get_student_avg_grade(СТ.код),
        (SELECT COUNT(*) FROM УСПЕВАЕМОСТЬ WHERE студент = СТ.код)
    FROM СТУДЕНТЫ СТ
    WHERE get_student_avg_grade(СТ.код) >= p_min_grade
      AND EXISTS (SELECT 1 FROM УСПЕВАЕМОСТЬ WHERE студент = СТ.код)
    ORDER BY средний_балл DESC;
END;
$$ LANGUAGE PLpgSQL;
