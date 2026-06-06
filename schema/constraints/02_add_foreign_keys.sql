-- Внешние ключи для обеспечения ссылочной целостности

-- Связь с таблицей СТУДЕНТЫ
ALTER TABLE УСПЕВАЕМОСТЬ ADD CONSTRAINT fk_student FOREIGN KEY (студент) REFERENCES СТУДЕНТЫ(код) ON DELETE CASCADE;

-- Остальные внешние ключи (проверим, все ли есть)
-- fk_group, fk_subject, fk_teacher уже существуют
