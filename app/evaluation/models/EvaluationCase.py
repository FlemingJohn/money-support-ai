from app.common.models.CamelModel import CamelModel
from app.evaluation.models.EvaluationTurn import EvaluationTurn


class EvaluationCase(CamelModel):
    id: str
    name: str
    turns: list[EvaluationTurn]

    @property
    def earlier_turns(self) -> list[EvaluationTurn]:
        return self.turns[:-2]

    @property
    def caller_line(self) -> str:
        return self.turns[-2].content

    @property
    def checked_turn(self) -> EvaluationTurn:
        return self.turns[-1]
