import os
from collections import defaultdict
from typing import Dict, List, Set, Optional
import logging as log
import pandas as pd
import re

from models.Session import Session
from models.Student import Student
from util import Caching


def get_filename(file_objective: str, sys_arg: str = '') -> str:
    """
    Gets a valid filename from the user
    :param sys_arg: Argument that may have been passed by the user. Will check this first
    :param str file_objective: Describes the file we are prompting the user to enter
    :return: filepath entered by the user verified to exist
    """
    file = sys_arg

    if file != '' and not os.path.isfile(file):
        print(f'No file found at {file}.')

    while file == '' or not os.path.isfile(file):
        file = input('Please enter a file name for the {}: '.format(file_objective))
        if os.path.isfile(file):
            break
        print(f'No file found at {file}!')

    return file


class CanvasUtil:

    def __init__(self, canvas_df: pd.DataFrame, cache_folder='cache'):
        self.canvas_df = canvas_df
        self.cache_folder = cache_folder
        self.canvas_pset_names: Set[str] = set(
            filter(
                lambda name: len(re.findall('ps\\d{2}', name.lower())) > 0 or 'lab' in name.lower(),
                self.canvas_df.columns
            )
        )

    def _kattis_name_to_canvas_name(self, student: Student) -> str:
        """Takes student name from kattis dump and returns the name from canvas"""
        kattis_name = student.name.lower().strip()
        kattis_username = student.name

        if '(' in kattis_name:
            kattis_name = kattis_name.split("(")[1].split(')')[0] + " " + kattis_name.split(" ")[-1]
        if len(kattis_name.split(" ")) > 2:
            kattis_name = kattis_name.split()[0] + " " + kattis_name.split()[-1]

        names = list(self.canvas_df['Student'])[1:]
        name: str
        for name in names:
            last, first = name.strip().lower().split(", ")
            kattis_format = " ".join([first.strip(), last.strip()])
            if kattis_name in kattis_format:
                return name
        last_names = []
        first_names = []
        for name in names:
            last, first = name.strip().lower().split(", ")
            if 'terry' in kattis_name and last == 'terry':
                print(kattis_name, first, last)
            if last in kattis_name:
                last_names.append(name)
            if first in kattis_name:
                first_names.append(name)

        # if no direct match, but only one student with that last name, return it
        if len(last_names) <= 2:
            for last_name in last_names:
                ans = input(f"Possible match: {kattis_name} ({kattis_username})={last_name}. Accept? [y/N]:")
                if ans.lower() == 'yes' or ans.lower() == 'y':
                    return last_name

        if len(first_names) == 1:
            ans = input(f"Possible match: {kattis_name} ({kattis_username})={first_names[0]}. Accept? [y/N]:")
            if ans.lower() == 'yes' or ans.lower() == 'y':
                return first_names[0]

        print(f"Could not find canvas entry for kattis student: {kattis_name}")
        return ''

    def populate_canvas_names(self, students: Dict[str, Student]):
        cache_util = Caching.CacheUtil(self.cache_folder)
        kattis_name_canvas_name_map: Optional[defaultdict] = cache_util.load_names_map_from_pickle('studentmap.data')

        if not kattis_name_canvas_name_map:
            kattis_name_canvas_name_map = defaultdict(str)
            for kattis_username, student in students.items():
                canvas_name = self._kattis_name_to_canvas_name(student)
                students[kattis_username].canvas_name = canvas_name
                if len(canvas_name) > 0:
                    kattis_name_canvas_name_map[student.name] = canvas_name
            cache_util.update_names_map_to_pickle('studentmap.data', kattis_name_canvas_name_map)
        else:
            for kattis_name_key, canvas_name_value in kattis_name_canvas_name_map.items():
                for _, student in students.items():
                    if student.name == kattis_name_key:
                        student.canvas_name = canvas_name_value
                        log.info(f"Matched {student.name} to {canvas_name_value} from cache.")
            for _, student in students.items():
                if len(student.canvas_name) == 0:
                    log.warning(
                        f"No canvas name found for {student.name} with kattis username {student.kattis_username}")

    def populate_canvas_session_names(self, sessions: List[Session]):

        for session in sessions:
            is_pset = len(re.findall('problem set', session.name.lower())) > 0
            num = re.findall('\\d{2}', session.name.split('-')[1])[0]

            canvas_type = 'PS' if is_pset else 'Lab'
            solve_type = 'Upsolve' if session.is_upsolve else 'Solve'
            canvas_prefix = f'{canvas_type}{num} {solve_type}'

            for canvas_col in self.canvas_pset_names:
                if canvas_prefix in canvas_col:
                    session.canvas_name = canvas_col
                    log.info(f"Matched Kattis Session {session.name} to {canvas_col}")
                    break

    def populate_grades(self, student_dict: Dict[str, Student], sessions: Set[str]):
        # finally, for each session, compute the score for a given student and update the dataframe
        for col in self.canvas_pset_names:
            is_upsolve: bool = 'upsolve' in col.lower()
            # there might be multiple kattis sessions (like redos, extensions) that count in a given column..
            associated_kattis_sessions = set(
                filter(
                    lambda sess: sess.canvas_name == col,
                    sessions
                )
            )
            if len(associated_kattis_sessions) > 1:
                log.info("Found multiple sessions for " + col)
                log.info([s.name for s in associated_kattis_sessions])
            # for each student, set their score for this column.
            for _, student in student_dict.items():
                if student.canvas_index == -1:
                    continue
                session_solved = set()
                for session in associated_kattis_sessions:
                    for problem in session.problems:
                        if (is_upsolve and student.problems_solved[problem] == 0.5) or \
                                (not is_upsolve and student.problems_solved[problem] == 1):
                            session_solved.add(problem)
                self.canvas_df.at[student.canvas_index, col] = len(session_solved)

        self.canvas_df = self.canvas_df[self.canvas_df.select_dtypes(include=['number']).columns].fillna(0)
