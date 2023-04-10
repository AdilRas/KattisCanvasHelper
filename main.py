import logging as log
import re
from typing import Dict, Set

import numpy
import pandas as pd

import util.Caching
from models.Student import Student
from util import Input

log.addLevelName(log.WARNING, "\033[1;31m%s\033[1;0m" % log.getLevelName(log.WARNING))
log.addLevelName(log.ERROR, "\033[1;41m%s\033[1;0m" % log.getLevelName(log.ERROR))

# Feel free to change these
KATTIS_JSON = ''
CANVAS_CSV_PATH = ''
LOGGING_LEVEL = log.ERROR

# Probably don't change this one
CACHE_FOLDER = 'cache'


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
    # If there's unintended behavior, you can enable full logging to get an idea for what's going on under the hood.

    log.basicConfig(level=LOGGING_LEVEL)

    student_dict, sessions = Input.load_kattis_info(KATTIS_JSON)

    # For each student, use the kattis info to compute a map [problem name -> score]
    # where score is 1 for solves and 0.5 for up-solves.
    Student.populate_problems_solved_from_sessions(student_dict, sessions)

    # read in the canvas export
    canvas_csv_filepath = CANVAS_CSV_PATH if len(CANVAS_CSV_PATH) > 0 \
        else Input.get_filename("Complete Canvas Gradebook Export")

    canvas_df = Input.load_canvas_info(canvas_csv_filepath)
    original_df = canvas_df.copy(deep=True)

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

    canvas_util.canvas_df.to_csv('output.csv', index=False, quotechar='"')
    print("Saved results to output.csv")

    # Sanity Check
    print("Running sanity check...")
    # original_df = original_df[original_df.select_dtypes(include=['number']).columns].fillna(0)
    discrepancy_count = 0
    for col in sorted(list(canvas_util.canvas_pset_names)):
        if original_df[col].sum() == 0 or 'base' in col.lower():
            # Grades have not been entered in this column yet, so we don't check for discrepancies
            continue
        for _, student in student_dict.items():
            if student.canvas_index != -1:
                if numpy.isnan(canvas_df.at[student.canvas_index, col]) and numpy.isnan(original_df.at[student.canvas_index, col]):
                    continue
                if canvas_df.at[student.canvas_index, col] != original_df.at[student.canvas_index, col]:
                    discrepancy_count += 1
                    log.warning(
                        f"Discrepancy: {col}::{student.canvas_name} Canvas score of {original_df.at[student.canvas_index, col]}"
                        f" but computed score is {canvas_df.at[student.canvas_index, col]}"
                    )
    if LOGGING_LEVEL == log.ERROR:
        print(f"Found {discrepancy_count} discrepancies. Set LOGGING_LEVEl to log.WARNING and run the program again "
              f"to see them...")

    print("All done! Terminating...")


main()
