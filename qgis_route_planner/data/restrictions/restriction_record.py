from dataclasses import dataclass

@dataclass
class RestrictionRecord:
    id: int | None = None
    restriction_type_id: int = 1
    name: str = ""
    node_id: int | None = None
    value_num: float | None = None
    value_text: str = ""
    comment: str = ""
