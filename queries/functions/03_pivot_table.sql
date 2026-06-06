CREATE EXTENSION IF NOT EXISTS tablefunc;

DROP VIEW IF EXISTS v_pivot_data;
CREATE VIEW v_pivot_data AS
SELECT 
    ГР.название AS группа,
    Д.название AS дисциплина,
    ROUND(AVG(У.оценка), 2) AS средний_балл
FROM УСПЕВАЕМОСТЬ У
JOIN ГРУППЫ ГР ON ГР.код = У.группа
JOIN ДИСЦИПЛИНЫ Д ON Д.код = У.дисциплина
GROUP BY ГР.название, Д.название
ORDER BY ГР.название, Д.название;

DROP FUNCTION IF EXISTS get_avg_grade_for_pair(VARCHAR, VARCHAR);
CREATE OR REPLACE FUNCTION get_avg_grade_for_pair(
    p_group_name VARCHAR,
    p_subject_name VARCHAR
) RETURNS NUMERIC(3,2) AS $$
BEGIN
    RETURN (
        SELECT ROUND(AVG(У.оценка), 2)
        FROM УСПЕВАЕМОСТЬ У
        JOIN ГРУППЫ Г ON Г.код = У.группа
        JOIN ДИСЦИПЛИНЫ Д ON Д.код = У.дисциплина
        WHERE Г.название = p_group_name AND Д.название = p_subject_name
    );
END;
$$ LANGUAGE PLpgSQL;

DROP FUNCTION IF EXISTS get_all_groups();
CREATE OR REPLACE FUNCTION get_all_groups()
RETURNS TABLE(name VARCHAR) AS $$
BEGIN
    RETURN QUERY SELECT название::VARCHAR FROM ГРУППЫ ORDER BY название;
END;
$$ LANGUAGE PLpgSQL;

-- ФИКСИРОВАННЫЙ СПИСОК ДИСЦИПЛИН (8 штук)
DROP FUNCTION IF EXISTS get_all_subjects();
CREATE OR REPLACE FUNCTION get_all_subjects()
RETURNS TABLE(name VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT unnest(ARRAY[
        'Рисунок'::VARCHAR,
        'Живопись'::VARCHAR,
        'Композиция'::VARCHAR,
        'Дизайн'::VARCHAR,
        'Web-дизайн'::VARCHAR,
        'Базы данных'::VARCHAR,
        'Высшая математика'::VARCHAR,
        'Физика'::VARCHAR
    ]) AS name;
END;
$$ LANGUAGE PLpgSQL;

DROP FUNCTION IF EXISTS build_pivot_table();
CREATE OR REPLACE FUNCTION build_pivot_table()
RETURNS TABLE(group_name VARCHAR, pivot_data JSONB) AS $$
DECLARE
    v_group_name VARCHAR;
    v_subject_name VARCHAR;
    v_result JSONB := '{}'::JSONB;
BEGIN
    FOR v_group_name IN SELECT name FROM get_all_groups() LOOP
        v_result := '{}'::JSONB;
        FOR v_subject_name IN SELECT name FROM get_all_subjects() LOOP
            v_result := v_result || jsonb_build_object(
                v_subject_name,
                COALESCE(get_avg_grade_for_pair(v_group_name, v_subject_name), 0)
            );
        END LOOP;
        RETURN QUERY SELECT v_group_name, v_result;
    END LOOP;
END;
$$ LANGUAGE PLpgSQL;

DROP FUNCTION IF EXISTS display_pivot_table();
CREATE OR REPLACE FUNCTION display_pivot_table()
RETURNS TABLE(
    группа VARCHAR,
    "Рисунок" TEXT,
    "Живопись" TEXT,
    "Композиция" TEXT,
    "Дизайн" TEXT,
    "Web-дизайн" TEXT,
    "Базы данных" TEXT,
    "Высшая математика" TEXT,
    "Физика" TEXT
) AS $$
DECLARE
    v_row RECORD;
BEGIN
    FOR v_row IN SELECT * FROM build_pivot_table() LOOP
        RETURN QUERY SELECT 
            v_row.group_name,
            (v_row.pivot_data->>'Рисунок')::TEXT,
            (v_row.pivot_data->>'Живопись')::TEXT,
            (v_row.pivot_data->>'Композиция')::TEXT,
            (v_row.pivot_data->>'Дизайн')::TEXT,
            (v_row.pivot_data->>'Web-дизайн')::TEXT,
            (v_row.pivot_data->>'Базы данных')::TEXT,
            (v_row.pivot_data->>'Высшая математика')::TEXT,
            (v_row.pivot_data->>'Физика')::TEXT;
    END LOOP;
END;
$$ LANGUAGE PLpgSQL;
