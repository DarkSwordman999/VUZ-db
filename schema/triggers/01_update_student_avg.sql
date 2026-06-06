-- Функция для пересчёта среднего балла студента
CREATE OR REPLACE FUNCTION update_student_average()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO СТУДЕНТЫ_СТАТИСТИКА (студент_код, средний_балл, количество_оценок)
    SELECT 
        студент,
        ROUND(AVG(оценка)::numeric, 2),
        COUNT(*)
    FROM УСПЕВАЕМОСТЬ
    WHERE студент = COALESCE(NEW.студент, OLD.студент)
    GROUP BY студент
    ON CONFLICT (студент_код) DO UPDATE SET
        средний_балл = EXCLUDED.средний_балл,
        количество_оценок = EXCLUDED.количество_оценок,
        updated_at = CURRENT_TIMESTAMP;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Создаём таблицу для статистики студентов
CREATE TABLE IF NOT EXISTS СТУДЕНТЫ_СТАТИСТИКА (
    студент_код INTEGER PRIMARY KEY REFERENCES СТУДЕНТЫ(код) ON DELETE CASCADE,
    средний_балл NUMERIC(3,2),
    количество_оценок INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создаём триггер
DROP TRIGGER IF EXISTS trg_update_student_avg ON УСПЕВАЕМОСТЬ;
CREATE TRIGGER trg_update_student_avg
AFTER INSERT OR UPDATE OR DELETE ON УСПЕВАЕМОСТЬ
FOR EACH ROW
EXECUTE FUNCTION update_student_average();

-- Инициализируем статистику для существующих студентов
INSERT INTO СТУДЕНТЫ_СТАТИСТИКА (студент_код, средний_балл, количество_оценок)
SELECT 
    студент,
    ROUND(AVG(оценка)::numeric, 2),
    COUNT(*)
FROM УСПЕВАЕМОСТЬ
GROUP BY студент
ON CONFLICT (студент_код) DO UPDATE SET
    средний_балл = EXCLUDED.средний_балл,
    количество_оценок = EXCLUDED.количество_оценок;
