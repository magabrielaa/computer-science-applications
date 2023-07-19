'''
Course search engine: backend

Maria Gabriela Ayala
Kenia Godinez Nogueda
'''

from math import radians, cos, sin, asin, sqrt, ceil
import sqlite3
import os

# Use this filename for the database
DATA_DIR = os.path.dirname(__file__)
DATABASE_FILENAME = os.path.join(DATA_DIR, 'course_information.sqlite3')

# Classification of attributes within args_from_ui
INPUT_1 = ["terms", "dept"]
INPUT_2 = ["day", "enrollment", "time_start", "time_end"]
INPUT_3 = ["building_code", "walking_time"]

# Classification of outputs of args_to_ui
OUTPUT_1 = '''
    c.dept,
    c.course_num,
    c.title'''
OUTPUT_2 = ''',
    s.section_num,
    m.day, m.time_start,
    m.time_end,
    s.enrollment'''
OUTPUT_3 = ''',
    a.building_code,
    time_between(a.lon,a.lat,b.lon,b.lat) AS walking_time'''

# FROM clause
Q_FORM = '''FROM courses as c'''

# JOIN clauses
JOIN_SEC_MEET = '''
JOIN sections AS s ON c.course_id = s.course_id
JOIN meeting_patterns AS m
ON s.meeting_pattern_id = m.meeting_pattern_id'''

JOIN_CAT = '''
JOIN catalog_index AS ci
ON c.course_id = ci.course_id'''

JOIN_GPS = '''
JOIN gps as a
JOIN (SELECT gps.lon, gps.lat, gps.building_code FROM gps WHERE gps.building_code = ?) AS b
ON a.building_code = s.building_code'''

def find_courses(args_from_ui):
    '''
    Takes a dictionary containing search criteria and returns courses
    that match the criteria.  The dictionary will contain some of the
    following fields:
      - dept a string
      - day is list of strings
           -> ["'MWF'", "'TR'", etc.]
      - time_start is an integer in the range 0-2359
      - time_end is an integer an integer in the range 0-2359
      - enrollment is a pair of integers
      - walking_time is an integer
      - building_code ia string
      - terms is a list of strings string: ["quantum", "plato"]
    Returns a pair: an ordered list of attribute names and a list the
     containing query results.  Returns ([], []) when the dictionary
     is empty.
    '''
    assert_valid_input(args_from_ui)
    connection = sqlite3.connect(DATABASE_FILENAME)
    connection.create_function("time_between", 4, compute_time_between)
    c = connection.cursor()
    params = [] #Initiate list of parameters for execute
    s_break = '\n'
    expre = ""
    inputs = []

    if args_from_ui == {}:
        return ([], [])

    # Build SELECT clause
    for attribute in args_from_ui:
        inputs.append(attribute)

    matched_input1 = [att for att in inputs if att in INPUT_1]
    matched_input2 = [att for att in inputs if att in INPUT_2]
    matched_input3 = [att for att in inputs if att in INPUT_3]
    select = "SELECT DISTINCT " #Get rid of duplicated

    if matched_input3 != []:
        q_select = select + OUTPUT_1 + OUTPUT_2 + OUTPUT_3 + s_break + Q_FORM + \
            JOIN_SEC_MEET + JOIN_CAT + JOIN_GPS + s_break
    elif matched_input2 != [] and matched_input1 != [] and matched_input3 == []:
        q_select = select + OUTPUT_1 + OUTPUT_2 + s_break + Q_FORM + JOIN_SEC_MEET \
            + JOIN_CAT + s_break
    elif matched_input1 != [] and matched_input2 == [] and matched_input3 == []:
        q_select = select + OUTPUT_1 + s_break + Q_FORM + JOIN_CAT + s_break


    for index, (attribute, value) in enumerate(args_from_ui.items()):

        if attribute == "building_code":
            params.insert(0,value)

        # Conditions for connector clause
        if index == 0:
            connector = "WHERE "
        else:
            connector = s_break + "AND "

        # Build WHERE & AND clauses
        if attribute == "terms":
            n = len(value)
            par = "?," * (n-1)
            expre += connector + "c.course_id IN(SELECT course_id FROM catalog_index AS ci " \
                "WHERE word IN (" + par + "?)" + s_break + "GROUP BY ci.course_id" + s_break\
                    + "HAVING COUNT(*) = " + f'{n})' + s_break
            for term in value:
                params.append(term)

        if attribute == "dept":
            expre += connector + "c.dept = ?"
            params.append(value)

        if attribute == "day":
            n = len(value)
            par = "?," * (n-1)
            expre += connector + "m.day IN (" + par + "?) "
            for day in value:
                params.append(day)

        if attribute == "enrollment":
            expre += connector + "s.enrollment BETWEEN ? AND ?"
            params.append(value[0])
            params.append(value[1])

        if attribute == "time_start":
            expre += connector + "m.time_start >= ? "
            params.append(value)

        if attribute == "time_end":
            expre += connector + "m.time_end <= ?"
            params.append(value)

        if attribute == "walking_time":
            expre += connector + "walking_time <= ?"
            params.append(value)

    sql_q = q_select + expre
    cursor = c.execute(sql_q, params)
    header = get_header(cursor)
    table = c.fetchall()

    return (header, table)


########### auxiliary functions #################
########### do not change this code #############

def assert_valid_input(args_from_ui):
    '''
    Verify that the input conforms to the standards set in the
    assignment.
    '''

    assert isinstance(args_from_ui, dict)

    acceptable_keys = set(['time_start', 'time_end', 'enrollment', 'dept',
                           'terms', 'day', 'building_code', 'walking_time'])
    assert set(args_from_ui.keys()).issubset(acceptable_keys)

    # get both buiding_code and walking_time or neither
    has_building = ("building_code" in args_from_ui and
                    "walking_time" in args_from_ui)
    does_not_have_building = ("building_code" not in args_from_ui and
                              "walking_time" not in args_from_ui)

    assert has_building or does_not_have_building

    assert isinstance(args_from_ui.get("building_code", ""), str)
    assert isinstance(args_from_ui.get("walking_time", 0), int)

    # day is a list of strings, if it exists
    assert isinstance(args_from_ui.get("day", []), (list, tuple))
    assert all([isinstance(s, str) for s in args_from_ui.get("day", [])])

    assert isinstance(args_from_ui.get("dept", ""), str)

    # terms is a non-empty list of strings, if it exists
    terms = args_from_ui.get("terms", [""])
    assert terms
    assert isinstance(terms, (list, tuple))
    assert all([isinstance(s, str) for s in terms])

    assert isinstance(args_from_ui.get("time_start", 0), int)
    assert args_from_ui.get("time_start", 0) >= 0

    assert isinstance(args_from_ui.get("time_end", 0), int)
    assert args_from_ui.get("time_end", 0) < 2400

    # enrollment is a pair of integers, if it exists
    enrollment_val = args_from_ui.get("enrollment", [0, 0])
    assert isinstance(enrollment_val, (list, tuple))
    assert len(enrollment_val) == 2
    assert all([isinstance(i, int) for i in enrollment_val])
    assert enrollment_val[0] <= enrollment_val[1]


def compute_time_between(lon1, lat1, lon2, lat2):
    '''
    Converts the output of the haversine formula to walking time in minutes
    '''
    meters = haversine(lon1, lat1, lon2, lat2)

    # adjusted downwards to account for manhattan distance
    walk_speed_m_per_sec = 1.1
    mins = meters / (walk_speed_m_per_sec * 60)

    return int(ceil(mins))


def haversine(lon1, lat1, lon2, lat2):
    '''
    Calculate the circle distance between two points
    on the earth (specified in decimal degrees)
    '''
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))

    # 6367 km is the radius of the Earth
    km = 6367 * c
    m = km * 1000
    return m


def get_header(cursor):
    '''
    Given a cursor object, returns the appropriate header (column names)
    '''
    header = []

    for i in cursor.description:
        s = i[0]
        if "." in s:
            s = s[s.find(".")+1:]
        header.append(s)

    return header
