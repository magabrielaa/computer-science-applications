## Warm up exercise #2
import sqlite3

## Opens a sqlite database for querying
connection = sqlite3.connect("course_information.sqlite3")
c = connection.cursor()

## Find the titles of all courses with department code “CMSC” in the course table.
q_1 = '''
SELECT * FROM courses WHERE dept="CMSC" LIMIT 10;
'''
table_q_1 = c.execute(q_1).fetchall()
print(table_q_1)

## Find the department names, course numbers, and section numbers for courses being
## offered on MWF at 10:30am (represented as 1030)
q_2 = '''
SELECT dept, course_num, section_num
FROM courses AS c
JOIN sections AS s
ON c.course_id = s.course_id
JOIN meeting_patterns AS mp
ON s.meeting_pattern_id = mp.meeting_pattern_id
WHERE time_start = 1030 and day = "MWF"
LIMIT 10;
'''
table_q_2 = c.execute(q_2).fetchall()
print(table_q_2)

## Find the department names and course numbers for courses being offered in Ryerson
## on MWF between 10:30am and 3pm (represented as 1500).
q_3 = '''
SELECT * FROM gps ORDER BY building_code;
SELECT dept, course_num
FROM courses AS c
JOIN sections AS s
ON s.course_id = s.course_id
JOIN meeting_patterns AS m
ON s.meeting_pattern_id = m.meeting_pattern_id
WHERE building_code = "RY"
AND day = "MWF"
AND time_start >= 1030
AND time_start <= 1500;
'''
table_q_3 = c.execute(q_3).fetchall()
print(table_q_3)

## Find the department names, course numbers, and course titles for courses being offered
## on MWF at 9:30am (represented as 930) that have the words “programming” and “abstraction”
## in their title/course description.
q_4 = '''
SELECT dept, course_num, title
FROM courses AS c
JOIN sections AS s
ON c.course_id =  s.course_id
JOIN meeting_patterns AS m
ON s.meeting_pattern_id = m.meeting_pattern_id
JOIN catalog_index AS ci
ON c.course_id = ci.course_id
WHERE day = "MWF" AND time_start = 930 AND ci.word IN ("programming", "abstraction");
'''
table_q_4 = c.execute(q_4).fetchall()
print(table_q_4)