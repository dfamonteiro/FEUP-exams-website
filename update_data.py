import sys
import requests
import json
import argparse
import os
from os import path
from datetime import datetime
from time import time

import feupy

def download_courses_json(ni_url : str, courses_folder_path : str, verbosity : int):

    COURSES_JSON_PATH = path.join(courses_folder_path, "courses.json")
    MINI_COURSES_JSON_PATH = path.join(courses_folder_path, "mini_courses.json")

    if verbosity >= 1:
        print(f"Downloading JSON from {ni_url}...")

    courses_request = requests.get(ni_url)
    courses = courses_request.json()


    if verbosity >= 1:
        print(f"Saving to {COURSES_JSON_PATH}...")

    with open(COURSES_JSON_PATH, "w") as f:
        json.dump(courses, f)

    if verbosity >= 2:
        print(f"Removing unnecessary fields...")

    for course in courses:
        # I can do this because dicts are passed by reference
        keys = list(course.keys())
        for key in keys:
            if key not in ("course_id", "acronym"):
                course.pop(key)

    courses.sort(key=lambda item : item["acronym"]) # Sort alphabetically


    if verbosity >= 1:
        print(f"Saving to {MINI_COURSES_JSON_PATH}...")

    with open(MINI_COURSES_JSON_PATH, "w") as f:
        json.dump(courses, f)

    if verbosity >= 1:
        print()


    courses_json_size      = path.getsize(COURSES_JSON_PATH)
    mini_courses_json_size = path.getsize(MINI_COURSES_JSON_PATH)
    reduction_percentage   = 100 - (mini_courses_json_size/courses_json_size)*100
    
    if verbosity >= 2:
        print(f"Size of {COURSES_JSON_PATH}: {courses_json_size}")
        print(f"Size of {MINI_COURSES_JSON_PATH}: {mini_courses_json_size}")
        print(f"Reduction of {round(reduction_percentage, 3)}% achieved")
        print()

def download_ucs_json(courses_folder_path : str, courses : list , verbosity: int):
    print(f"Number of courses: {len(courses)}")

    for i in range(len(courses)):
        course_id = courses[i]["course_id"]
        acronym   = courses[i]["acronym"]

        if verbosity >= 1:
            print()
            print(f"Now processing {acronym} ({i + 1}/{len(courses)})")
        if verbosity >= 2:
            print(f"pv_curso_id = {course_id}")
        
        course = feupy.Course(course_id)
        
        if verbosity >= 2:
            print("Course url:", course.url)


        course_path = path.join(courses_folder_path, "COURSE" + str(course_id))

        if verbosity >= 2:
            print(f"Creating folder {course_path}")

        os.makedirs(course_path, exist_ok = True)

        if verbosity >= 1:
            print("Getting curricular units")

        curricular_units = course.curricular_units()

        if verbosity >= 1:
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

        if verbosity >= 2:
            print("Creating curricular units files:")
            print("    ", course_path_sem_1)
            print("    ", course_path_sem_2)

        with open(course_path_sem_1, "w") as f:
            json.dump(curricular_units_sem1, f)

        with open(course_path_sem_2, "w") as f:
            json.dump(curricular_units_sem2, f)

def download_exams_json(courses_folder_path : str, courses : list , verbosity: int):
    for i in range(len(courses)):
        course_id = courses[i]["course_id"]
        
        course = feupy.Course(course_id)
        
        course_path = path.join(courses_folder_path, "COURSE" + str(course_id))
        
        if verbosity >= 1:
            print()
            print(f"Now processing {course.acronym} ({i + 1}/{len(courses)})")
        if verbosity >= 2:
            print(f"Course url: {course.url}")

        exams = course.exams(use_cache = False)

        if verbosity >= 1:
            print(f"{len(exams)} exams found")

        course_path_exams = path.join(course_path, "EXAMS.json")

        if verbosity >= 2:
            print("Creating exams file:", course_path_exams)

        trimmed_exams = []
        
        for exam in exams:
            trimmed_exam = {'pv_ocorrencia_id' : exam["curricular unit"].pv_ocorrencia_id,
                            'start_timestamp'  : datetime.timestamp(exam['start']),
                            'finish_timestamp' : datetime.timestamp(exam['finish']),
                            'rooms'            : list(exam["rooms"]) if (exam["rooms"] != None) else []}
            
            trimmed_exams.append(trimmed_exam)
        
        with open(course_path_exams, "w") as f:
            json.dump(trimmed_exams, f)


def update_timestamp(timestamp_json_path : str, verbosity : int):
    if verbosity >= 1:
        print(f"Update complete! Saving timestamp to {timestamp_json_path}")

    timestamp = {"timestamp" : int(time())}
    
    if verbosity >= 2:
        print("Timestamp:", timestamp["timestamp"])

    with open(timestamp_json_path, "w") as f:
        json.dump(timestamp, f)


DIR_STRUCTURE = ["index.html", "css", "update_data.py", "main.js", "data"]
WRONG_DIR_MESSAGE = "Please make sure that you are running this program in the correct directory"
NI_COURSES_URL = "https://ni.fe.up.pt/tts/api/faculties/8/courses"

TIMESTAMP_PATH = path.join("data", "timestamp.json")



if __name__ == "__main__":
    assert set(DIR_STRUCTURE) <= set(os.listdir()), WRONG_DIR_MESSAGE

    parser = argparse.ArgumentParser(description = "Updates the json files that make the website work")
    parser.add_argument("-c", "--update_courses", help="update the JSON course files", action="store_true")
    parser.add_argument("-u", "--update_ucs",     help="update the JSON uc files",     action="store_true")
    parser.add_argument("-e", "--update_exams",   help="update the JSON exams files",  action="store_true")
    parser.add_argument("-v", "--verbosity", action="count", default=0, help="Increases the verbosity")
    args   = parser.parse_args()

    if args.update_courses:
        download_courses_json(NI_COURSES_URL, "data", args.verbosity)

    if args.update_ucs:
        courses = []
        with open(path.join("data", "mini_courses.json")) as json_file:
            courses = json.load(json_file)

        download_ucs_json(path.join("data", "courses"), courses, args.verbosity)
    
    if args.update_exams:
        courses = []
        with open(path.join("data", "mini_courses.json")) as json_file:
            courses = json.load(json_file)

        download_exams_json(path.join("data", "courses"), courses, args.verbosity)

    update_timestamp(TIMESTAMP_PATH, args.verbosity)
