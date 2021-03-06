import sys
import requests
import json
import argparse
import os
from os import path
from datetime import datetime
from time import time
from subprocess import run

import feupy
import bs4

def download_courses_json(url : str, courses_folder_path : str, verbosity : int):
    COURSES_JSON_PATH = path.join(courses_folder_path, "courses.json")

    if verbosity >= 1:
        print(f"Downloading JSON from {url}...")

    courses_html = requests.get(url)
    soup = bs4.BeautifulSoup(courses_html.text, "lxml")

    tags = soup.find("div", {"id" : "ciclos_estudos"}).find_all("a")
    
    courses_tags = filter(lambda tag: "cur_geral.cur_view" in str(tag) and "pv_tipo_cur_sigla=D" not in str(tag) and "Página Web" not in str(tag), tags)
    
    if verbosity >= 1:
        print(f"Loading courses...")

    courses = [feupy.Course.from_a_tag(tag) for tag in courses_tags]
    courses.sort(key=lambda course: course.acronym)

    courses_json = [{"course_id" : course.pv_curso_id, "acronym" : course.acronym} for course in courses]

    if verbosity >= 1:
        print(f"Saving to {COURSES_JSON_PATH}...")

    with open(COURSES_JSON_PATH, "w") as f:
        json.dump(courses_json, f)

    if verbosity >= 1:
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
                "curricular_year"  : uc.curricular_years[0], # Not the best way to do this
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

def commit_and_push():
    run(["git", "status"])
    run(["git", "stage", "data/*"])

    run(["git", "status"])
    run(["git", "commit", "-m", "Data update"])

    run(["git", "status"])
    run(["git", "push"])

DIR_STRUCTURE = ["index.html", "css", "update_data.py", "main.js", "data"]
WRONG_DIR_MESSAGE = "Please make sure that you are running this program in the correct directory"
COURSES_URL = "https://sigarra.up.pt/feup/pt/cur_geral.cur_inicio"

TIMESTAMP_PATH = path.join("data", "timestamp.json")



if __name__ == "__main__":
    assert set(DIR_STRUCTURE) <= set(os.listdir()), WRONG_DIR_MESSAGE

    parser = argparse.ArgumentParser(description = "Updates the json files that make the website work")
    parser.add_argument("-c", "--update_courses", help="update the JSON course files", action="store_true")
    parser.add_argument("-u", "--update_ucs",     help="update the JSON uc files",     action="store_true")
    parser.add_argument("-e", "--update_exams",   help="update the JSON exams files",  action="store_true")
    parser.add_argument("-g", "--git",            help="commit and push to the git repo",  action="store_true")
    parser.add_argument("-v", "--verbosity", action="count", default=0, help="Increases the verbosity")
    args   = parser.parse_args()

    if args.update_courses:
        download_courses_json(COURSES_URL, "data", args.verbosity)

    if args.update_ucs:
        courses = []
        with open(path.join("data", "courses.json")) as json_file:
            courses = json.load(json_file)

        download_ucs_json(path.join("data", "courses"), courses, args.verbosity)
    
    if args.update_exams:
        courses = []
        with open(path.join("data", "courses.json")) as json_file:
            courses = json.load(json_file)

        download_exams_json(path.join("data", "courses"), courses, args.verbosity)

    update_timestamp(TIMESTAMP_PATH, args.verbosity)

    if args.git:
        commit_and_push()
