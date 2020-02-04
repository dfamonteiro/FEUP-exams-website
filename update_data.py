import sys
import requests
import json
import os
from os import path
from datetime import datetime
from time import time

import feupy

dir_structure = ["index.html", "css", "update_data.py", "main.js", "data"]
wrong_dir_message = "Please make sure that you are running this program in the correct directory"
ni_courses_url = "https://ni.fe.up.pt/tts/api/faculties/8/courses"

courses_json_path = path.join("data", "courses.json")
mini_courses_json_path = path.join("data", "mini_courses.json")
timestamp_json_path = path.join("data", "timestamp.json")

assert set(dir_structure) <= set(os.listdir()), wrong_dir_message


print(f"Downloading JSON from {ni_courses_url}...")
courses_request = requests.get(ni_courses_url)
courses = courses_request.json()


print(f"Saving to {courses_json_path}...")
with open(courses_json_path, "w") as f:
    json.dump(courses, f)


print(f"Removing unnecessary fields...")
for course in courses:
    # I can do this because dicts are passed by reference
    keys = list(course.keys())
    for key in keys:
        if key not in ("course_id", "acronym"):
            course.pop(key)

courses.sort(key=lambda item : item["acronym"]) # Sort alphabetically


print(f"Saving to {mini_courses_json_path}...")
with open(mini_courses_json_path, "w") as f:
    json.dump(courses, f)
print()


courses_json_size      = path.getsize(courses_json_path)
mini_courses_json_size = path.getsize(mini_courses_json_path)
reduction_percentage   = 100 - (mini_courses_json_size/courses_json_size)*100

print(f"Size of {courses_json_path}: {courses_json_size}")
print(f"Size of {mini_courses_json_path}: {mini_courses_json_size}")
print(f"Reduction of {round(reduction_percentage, 3)}% achieved")
print()

print(f"Number of courses: {len(courses)}")
os.makedirs(path.join("data", "courses"), exist_ok = True)


for i in range(len(courses)):
    course_id = courses[i]["course_id"]
    acronym   = courses[i]["acronym"]

    print()
    print(f"Now processing {acronym} ({i + 1}/{len(courses)})")
    print(f"pv_curso_id = {course_id}")
    course = feupy.Course(course_id)
    print("Course url:", course.url)


    course_path = path.join("data", "courses", "COURSE" + str(course_id))
    print(f"Creating folder {course_path}")
    os.makedirs(course_path, exist_ok = True)

    print("Getting curricular units")
    curricular_units = course.curricular_units()
    print(f"{len(curricular_units)} curricular units found")

    course_path_sem_1 = path.join(course_path, "SEMESTER1.json")
    course_path_sem_2 = path.join(course_path, "SEMESTER2.json")

    curricular_units_sem1 = []
    curricular_units_sem2 = []
    
    for uc in curricular_units:
        trimmed_uc = {
            "acronym"          : uc.acronym,
            "curricular_year"  : uc.curricular_year,
            "name"             : uc.name,
            "pv_ocorrencia_id" : uc.pv_ocorrencia_id,
            "semester"         : uc.semester,
            "url"              : uc.url
        }

        if trimmed_uc["semester"] == "1":
            curricular_units_sem1.append(trimmed_uc)

        if trimmed_uc["semester"] == "2":
            curricular_units_sem2.append(trimmed_uc)

        if trimmed_uc["semester"] == "A":
            curricular_units_sem1.append(trimmed_uc)
            curricular_units_sem2.append(trimmed_uc)

    print("Creating curricular units files:")
    print("    ", course_path_sem_1)
    print("    ", course_path_sem_2)

    with open(course_path_sem_1, "w") as f:
        json.dump(curricular_units_sem1, f)

    with open(course_path_sem_2, "w") as f:
        json.dump(curricular_units_sem2, f)


    print("Getting exams")
    exams = course.exams(use_cache = False)
    print(f"{len(exams)} exams found")

    course_path_exams = path.join(course_path, "EXAMS.json")
    print("Creating exams file:", course_path_exams)

    trimmed_exams = []
    
    for exam in exams:
        trimmed_exam = {'pv_ocorrencia_id':  exam["curricular unit"].pv_ocorrencia_id,
                        'start_timestamp'  : datetime.timestamp(exam['start']),
                        'finish_timestamp' : datetime.timestamp(exam['finish']),
                        'rooms'            : list(exam["rooms"]) if exam["rooms"] != None else []}
        
        trimmed_exams.append(trimmed_exam)
    
    with open(course_path_exams, "w") as f:
        json.dump(trimmed_exams, f)



print(f"Update complete! Saving timestamp to {timestamp_json_path}")
timestamp = {"timestamp" : int(time())}
print("Timestamp:", timestamp["timestamp"])

with open(timestamp_json_path, "w") as f:
    json.dump(timestamp, f)