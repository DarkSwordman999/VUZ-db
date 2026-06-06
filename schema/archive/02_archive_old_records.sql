-- Процедура перемещения старых записей (старше указанного количества лет)
CREATE OR REPLACE FUNCTION archive_old_records(years INTEGER DEFAULT 2)
RETURNS INTEGER AS $$
DECLARE
    cutoff_date DATE;
    archived_count INTEGER;
BEGIN
    cutoff_date := CURRENT_DATE - (years * INTERVAL '1 year');
    
    -- Перемещаем записи в архив
    INSERT INTO УСПЕВАЕМОСТЬ_АРХИВ (код_записи, студент, группа, дисциплина, преподаватель, оценка, дата, archive_date)
    SELECT код_записи, студент, группа, дисциплина, преподаватель, оценка, дата, CURRENT_TIMESTAMP
    FROM УСПЕВАЕМОСТЬ
    WHERE дата < cutoff_date;
    
    -- Получаем количество перемещённых записей
    GET DIAGNOSTICS archived_count = ROW_COUNT;
    
    -- Удаляем перемещённые записи из основной таблицы
    DELETE FROM УСПЕВАЕМОСТЬ
    WHERE дата < cutoff_date;
    
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;
