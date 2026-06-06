-- Худшие студенты по среднему баллу
SELECT 
    ROW_NUMBER() OVER (ORDER BY AVG(u.оценка) ASC) as место,
    s.фамилия,
    s.имя,
    g.название as группа,
    ROUND(AVG(u.оценка), 2) as средний_балл,
    COUNT(u.код_записи) as количество_оценок
FROM СТУДЕНТЫ s
JOIN УСПЕВАЕМОСТЬ u ON u.студент = s.код
JOIN ГРУППЫ g ON g.код = u.группа
GROUP BY s.код, s.фамилия, s.имя, g.название
ORDER BY средний_балл ASC
LIMIT :limit;
