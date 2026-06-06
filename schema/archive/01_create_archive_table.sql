-- Создаём архивную таблицу (структура как у УСПЕВАЕМОСТЬ)
CREATE TABLE IF NOT EXISTS УСПЕВАЕМОСТЬ_АРХИВ (
    LIKE УСПЕВАЕМОСТЬ INCLUDING ALL
);

-- Добавляем дату архивации
ALTER TABLE УСПЕВАЕМОСТЬ_АРХИВ ADD COLUMN archive_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Индекс для поиска по дате архивации
CREATE INDEX idx_archive_date ON УСПЕВАЕМОСТЬ_АРХИВ(archive_date);
