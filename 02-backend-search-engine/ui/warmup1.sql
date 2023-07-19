sqlite3 course_information.sqlite3  /* To open file in SQL*/

.schema
.tables
.schema courses


/* WARM UP EXCERCISE 1 

1. Find the titles of all courses with department code “CMSC” in the 
course table. */

SELECT * FROM courses WHERE dept = "CMSC";


/* 2. Find the department names, course numbers, and section numbers for 
courses being offered on MWF at 10:30am (represented as 1030) */
SELECT dept, course_num, section_num 
FROM courses AS c JOIN sections AS s 
ON c.course_id = s.course_id JOIN meeting_patterns AS m 
ON s.meeting_pattern_id = m.meeting_pattern_id 
WHERE time_start = 1030
LIMIT 10;

/* 3. Find the department names and course numbers for courses being 
offered in Ryerson on MWF between 10:30am and 3pm (represented as 1500)*/

SELECT dept, course_num
FROM courses AS c JOIN sections AS s
ON s.course_id = s.course_id JOIN meeting_patterns AS m
ON s.meeting_pattern_id = m.meeting_pattern_id
WHERE building_code = "RY" AND day = "MWF" AND time_start BETWEEN 1030 AND 1500;

/* 4. Find the department names, course numbers, and course titles for courses 
 being offered on MWF at 9:30am (represented as 930) that have the words 
“programming” and “abstraction” in their title/course description.*/

SELECT dept, course_num, title
FROM courses AS c JOIN sections AS s
ON c.course_id =  s.course_id JOIN meeting_patterns AS m
ON s.meeting_pattern_id = m.meeting_pattern_id JOIN catalog_index AS ci
ON c.course_id = ci.course_id
WHERE day = "MWF" AND time_start = 930 AND ci.word IN ("programming", "abstraction");
