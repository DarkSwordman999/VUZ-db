-- CHECK-ограничения для целостности данных

-- Ограничение на оценку (только 2,3,4,5)
ALTER TABLE УСПЕВАЕМОСТЬ ADD CONSTRAINT chk_grade CHECK (оценка IN (2,3,4,5));

-- Ограничение на дату (не в будущем и не раньше 2000 года)
ALTER TABLE УСПЕВАЕМОСТЬ ADD CONSTRAINT chk_date CHECK (дата BETWEEN '2000-01-01' AND CURRENT_DATE);

-- Ограничение на телефон (минимальная длина 10 символов)
ALTER TABLE СТУДЕНТЫ ADD CONSTRAINT chk_phone CHECK (LENGTH(телефон) >= 10);
