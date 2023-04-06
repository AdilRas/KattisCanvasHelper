from __future__ import annotations
from typing import Dict, List, Set

from models.Result import Result


class Session:

    # @staticmethod
    # def read_dict(session_dict: Dict):
    #     name = session_dict['name']
    #     starttime: int = int(session_dict['starttime'])
    #     length = session_dict['length']
    #     problems = session_dict['problems']
    #     results = session_dict['results']
    #     return name, starttime, length, problems, results

    def __init__(
            self,
            name: str,
            starttime: str,
            length: str,
            problems: Set[str],
            results: List
    ):
        self.name: str = name
        self.canvas_name: str = ''
        self.starttime: str = starttime
        self.length: str = length
        self.problems: Set[str] = problems
        self.results: List[Result] = results
        self.is_upsolve: bool = False

    @staticmethod
    def get_emtpy_model() -> Session:
        return Session(
            name='',
            starttime='',
            length='',
            problems=set(),
            results=[]
        )

    @staticmethod
    def _is_upsolve_session(session_name: str):
        return 'upsolve' in session_name.lower()

    @staticmethod
    def parse_kattis_sessions(kattis_json) -> List[Session]:
        sessions: List[Session] = [Session.get_emtpy_model() for _ in kattis_json['sessions']]
        for i, session in enumerate(kattis_json['sessions']):
            sessions[i].name = session['name']
            for key in session['problems']:
                sessions[i].problems.add(session['problems'][key]['problem_name'])
            sessions[i].length = session['length']
            sessions[i].starttime = session['starttime']
            sessions[i].results = [Result.from_dict(res_dict) for res_dict in session['results']]
            sessions[i].is_upsolve = Session._is_upsolve_session(session['name'])

        return sessions
