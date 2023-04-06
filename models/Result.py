from __future__ import annotations

from typing import List


class Result:

    @classmethod
    def from_dict(cls, result_dict: dict) -> Result:
        team_name = result_dict['team_name']
        solved_count = result_dict['solved_count']
        total_time = result_dict['total_time']
        members = result_dict['members']
        problems = [
            problem['problem_name'] for problem in filter(
                lambda prob: 'solve_time' in prob,
                result_dict['problems']
            )
        ]
        # problems = [problem['problem_name'] for problem in result_dict['problems']]
        return Result(
            team_name,
            solved_count,
            total_time,
            members,
            problems
        )

    def __init__(self, team_name: str, solved_count: int, total_time: int, members: List[str], problems: List[str]):
        self.team_name = team_name
        self.solved_count = solved_count
        self.total_time = total_time
        self.members = members
        self.problems = problems
