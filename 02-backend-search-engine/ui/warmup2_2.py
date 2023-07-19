## WARM UP EXCERCISE 2
import sqlite3

conn = sqlite3.connect("/Users/mariagabrielaayala/capp30122/pa3-mariagabrielaa-gnogueda-3/ui/course_information.sqlite3") # returns a connection object
c = conn.cursor() # conn is a connection object, returns a cursor object


## Find the titles of all courses with department code "CMSC" in the course table.
dep = "CMSC"
table_q_1 = c.execute("SELECT * FROM courses WHERE dept= ? LIMIT 10", (dep,)).fetchall()
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
WHERE time_start = ? AND day = ?
'''
time = 1030
d = "MWF"
table_q_2 = c.execute(q_2, (time,d)).fetchall()
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
WHERE building_code = ?
AND day = ?
AND time_start BETWEEN ? AND ?
'''
b = "RY"
d = "MWF"
t1 = 1030
t2 = 1500
table_q_3 = c.execute(q_3, (b, d, t1, t2)).fetchall()
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
WHERE day = ? AND time_start = ? AND ci.word IN (?, ?)
'''
d = "MWF"
t = 930
w1 = "programming"
w2 =  "abstraction"
table_q_4 = c.execute(q_4, (d, t, w1, w2)).fetchall()
print(table_q_4)


conn.close()