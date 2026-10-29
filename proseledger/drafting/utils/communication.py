from typing import Dict, List
from langgraph.graph import MessagesState


class LiRAState(MessagesState):
    topic: str = ""
    discuss_count: int = 0
    revision_count_outline: int = 0
    revision_count_writing: int = 0
    revision_count_editing: int = 0
    papers: List[Dict] = []
    researcher_analyses: List[Dict[str, str]] = []
    paper_groups: List[Dict[str, str]] = []
    draft_outlines: List[Dict[str, str]] = []
    to_review_now: str = ""
    outline_discussion: List = []
    content_discussion: Dict[str, List] = {}
    editing_discussion: List = []
    draft_review: str = ""
    final_review: str = ""
