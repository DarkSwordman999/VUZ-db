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
