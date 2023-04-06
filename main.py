import logging as log
import re
from typing import List, Dict, Set

import pandas as pd

import util.Caching
from models.Session import Session
from models.Student import Student
from util import Input
import json

log.addLevelName(log.WARNING, "\033[1;31m%s\033[1;0m" % log.getLevelName(log.WARNING))
log.addLevelName(log.ERROR, "\033[1;41m%s\033[1;0m" % log.getLevelName(log.ERROR))

KATTIS_JSON = 'CSCE430-2023Spring_export.json'
CANVAS_CSV_PATH = '2023-04-06T0007_Grades-CSCE-430 200,500.csv'
CACHE_FOLDER = 'cache'


def load_kattis_info() -> [Dict[str, Student], List[Session]]:
    student_json_filepath = KATTIS_JSON if len(KATTIS_JSON) > 0 else Input.get_filename("Kattis JSON Dump")

    with open(student_json_filepath, "r") as kattis_dump_file:
        kattis_json = json.load(kattis_dump_file)
        students: Dict[str, Student] = {student.kattis_username: student for student in
                                        Student.parse_kattis_students(kattis_json)}
        sessions: List[Session] = Session.parse_kattis_sessions(kattis_json)

    return [students, sessions]


def populate_honors(students: Dict[str, Student], canvas_df: pd.DataFrame):
    for _, student in students.items():
        sections = canvas_df[canvas_df['Student'] == student.canvas_name]['Section'].values
        if len(sections) > 0:
            honors_section_regex = '2\\d{2}'
            student.honors = len(re.findall(honors_section_regex, sections[0])) > 0
            if student.honors:
                log.info(f"Set {student.name} to honors.")


def clear_honors_points(student_dict: Dict[str, Student]):
    # get honors problems to skip
    cache_util = util.Caching.CacheUtil(CACHE_FOLDER)
    honors_problems: Set[str] = cache_util.read_honors_skips('honors_problems.in')

    # for each student, if they are in honors, set those problems to 0 score if they exist.
    for _, student in student_dict.items():
        for problem in honors_problems:
            if student.honors:
                student.problems_solved[problem] = 0.0


def main():
    log.basicConfig(level=log.WARNING)

    student_dict, sessions = load_kattis_info()

    # For each student, use the kattis info to compute a map [problem name -> score]
    # where score is 1 for solves and 0.5 for up-solves.
    Student.populate_problems_solved_from_sessions(student_dict, sessions)

    # read in the canvas export
    canvas_csv_filepath = CANVAS_CSV_PATH if len(CANVAS_CSV_PATH) > 0 \
        else Input.get_filename("Complete Canvas Gradebook Export")

    canvas_df = pd.read_csv(canvas_csv_filepath)

    canvas_util = util.Input.CanvasUtil(canvas_df, CACHE_FOLDER)
    # for each student, find and set their name in canvas
    canvas_util.populate_canvas_names(student_dict)
    # for each session in kattis, map it to one of the columns in canvas
    canvas_util.populate_canvas_session_names(sessions)
    # mark all the honors students
    populate_honors(student_dict, canvas_df)
    # get rid of the points assigned to honors students.
    clear_honors_points(student_dict)

    Student.set_canvas_row_indices(student_dict, canvas_df)

    # Compute Grades
    canvas_util.populate_grades(student_dict, sessions)

    canvas_util.canvas_df.to_csv('output.csv', index=False)

    # Sanity Check
    original_df = pd.read_csv(canvas_csv_filepath)
    original_df = original_df[original_df.select_dtypes(include=['number']).columns].fillna(0)

    for col in sorted(list(canvas_util.canvas_pset_names)):
        if canvas_df[col].sum() == 0 or original_df[col].sum() == 0:
            # Grades have not been entered in this column yet, so we don't check for discrepancies
            continue
        for _, student in student_dict.items():
            if student.canvas_index != -1:
                if canvas_df.at[student.canvas_index, col] != original_df.at[student.canvas_index, col]:
                    log.warning(f"Discrepancy: {col}::{student.canvas_name} Canvas score of {original_df.at[student.canvas_index, col]}"
                                f" but computed score is {canvas_df.at[student.canvas_index, col]}")


main()
