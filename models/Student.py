from __future__ import annotations

from collections import defaultdict
from typing import List, Dict
import logging as log
import pandas as pd

from models.Session import Session


class Student:
    # "username": "kattis-user", "name": "Kattis User", "non_anonymous": "t", "email": "kattisuser@tamu.edu"
    def __init__(self, kattis_username: str, name: str, visible_name: str, email: str):
        self.kattis_username = kattis_username
        self.canvas_name: str = ''
        self.name = name
        self.hidden = False if visible_name == 'f' else True
        self.email = email
        # problem id -> points earned (0, .5 or 1 in theory)...
        self.problems_solved: defaultdict = defaultdict(float)
        self.honors: bool = False
        self.canvas_index: int = -1

    @staticmethod
    def parse_kattis_students(kattis_json) -> List[Student]:
        students_json = kattis_json['students']
        students: List[Student] = []
        for student_json in students_json:
            students.append(
                Student(
                    name=student_json['name'],
                    kattis_username=student_json['username'],
                    email=student_json['email'],
                    visible_name=student_json['non_anonymous']
                )
            )
        return students

    @staticmethod
    def populate_problems_solved_from_sessions(students: Dict[str, Student], sessions: List[Session]):
        for session in sessions:
            for result in session.results:
                # handles individuals and teams
                for member in result.members:
                    for problem in result.problems:
                        # ensure we only count each problem once
                        students[member].problems_solved[problem] = max(
                            students[member].problems_solved[problem],
                            0.5 if session.is_upsolve else 1
                        )

    @staticmethod
    def set_canvas_row_indices(students: Dict[str, Student], canvas_df: pd.DataFrame):
        for _, student in students.items():
            if len(student.canvas_name) == 0:
                continue
            try:
                student_index = canvas_df[canvas_df['Student'] == student.canvas_name].index[0]
                student.canvas_index = student_index
            except Exception as e:
                log.warning(e)
                print(f"Note: Failed to find {student.name} from Kattis in Canvas as '{student.canvas_name}'. "
                      f"This may happen when a student q-drops or changes name in Canvas. "
                      f"If you want to fix this, delete cache/studentmap.data")
