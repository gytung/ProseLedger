import re
from typing import List
from langchain.schema import AIMessage
from proseledger.drafting.base_agent import BaseAgent
from proseledger.drafting.utils.constants import (
    LLM_SEED,
    TEMP_DIR,
    MODEL_VER,
    MAX_ITEMS,
    TEMPERATURE,
    SETTING_NAME,
    CONTEXT_SIZE,
)
from proseledger.drafting.prompts.edit import (
    EDITOR_PROMPT,
    PAPER_EDIT_PROMPT,
    PAPER_EDIT_REVISE_PROMPT,
    PAPER_COMPLETE_EDIT_PROMPT,
    PAPER_COMPLETE_REVISE_PROMPT,
)

type_regex = "## TYPE\\n(.+\\n?)"
reason_regex = "## REASON\\n(.+\\n?(?:\\n.+){1,7})"
chain_of_thought_pattern = "## THOUGHTS\\n(?:.+\\n){1,10}\\n"


def _needs_completion(message: AIMessage) -> bool:
    """Handle optional OpenAI-compatible usage metadata without assuming it exists."""
    metadata = getattr(message, "response_metadata", None) or {}
    if metadata.get("finish_reason") == "length":
        return True
    usage = metadata.get("token_usage") or {}
    tokens = usage.get("completion_tokens") if isinstance(usage, dict) else None
    if tokens is None:
        normalized_usage = getattr(message, "usage_metadata", None) or {}
        tokens = normalized_usage.get("output_tokens")
    content = message.content
    return (
        isinstance(tokens, (int, float))
        and tokens >= 16384
        and isinstance(content, str)
        and bool(content.strip())
        and (not content.rstrip().endswith("."))
    )


class EditorAgent(BaseAgent):

    def __init__(
        self,
        name: str,
        review_id: str,
        seed: int = LLM_SEED,
        model_name: str = MODEL_VER,
        context_size: int = CONTEXT_SIZE,
        temperature: float = TEMPERATURE,
        max_memory_items: int = MAX_ITEMS,
        dataset: str = "srg",
        temp_dir: str = TEMP_DIR,
        setting_name: str = SETTING_NAME,
        overwrite_responses: bool = False,
    ):
        super().__init__(
            name=name,
            model_name=model_name,
            context_size=context_size,
            seed=seed,
            temperature=temperature,
            max_memory_items=max_memory_items,
            system_prompt=EDITOR_PROMPT,
            dataset=dataset,
            temp_dir=temp_dir,
            review_id=review_id,
            setting_name=setting_name,
            overwrite_response=overwrite_responses,
        )

    def edit_paper(self, paper: str, revision_count: int = 1) -> List:
        """
        Edits a draft paper into a final refined paper.

        Parameters:
        paper - the draft review paper text.
        revision_count - the paper's draft (iteration) number.

        Returns:
        the edited literature review as an `AIMessage` in a list.
        """
        prompt = PAPER_EDIT_PROMPT.format(DRAFT_PAPER=paper)
        response = self.call_model(
            prompt=prompt,
            response_only=True,
            file_name=f"final_{revision_count}.json",
            folder_name="final",
        )
        if _needs_completion(response[-1]):
            prompt_complete = PAPER_COMPLETE_EDIT_PROMPT.format(
                EDITED_PAPER=response[-1].content, DRAFT_PAPER=paper
            )
            response_complete = self.call_model(
                prompt=prompt_complete,
                response_only=True,
                file_name=f"final_{revision_count}_completion.json",
                folder_name="final",
            )
            response_complete[-1].content = response_complete[-1].content.split("===\n\n", 1)[1]
            content = (
                response[-1].content.rsplit("===\n\n", 1)[0]
                + "===\n\n"
                + response_complete[-1].content
            )
            response_final = [AIMessage(content=content)]
        else:
            response_final = response
        return response_final

    def revise_edit(self, paper: str, discussion: List, revision_count: int = 2) -> List:
        """
        Edits a draft paper into a final refined paper with revision.

        Parameters:
        paper - the draft review paper text.
        discussion - the paper edit discussion.
        revision_count - the paper's draft (iteration) number.

        Returns:
        the revised edited literature review as an `AIMessage` in a list.
        """
        prompt = PAPER_EDIT_REVISE_PROMPT.format(DRAFT_PAPER=paper)
        response = self.call_model(
            prompt=prompt,
            messages=discussion,
            response_only=True,
            file_name=f"final_{revision_count}.json",
            folder_name="final",
        )
        response[-1].content = re.sub("<\\/?FORMAT>\\n{0,2}", "", response[-1].content)
        response[-1].content = re.sub(chain_of_thought_pattern, "", response[-1].content)
        if _needs_completion(response[-1]):
            prompt_complete = PAPER_COMPLETE_REVISE_PROMPT.format(
                EDITED_PAPER=response[-1].content, DRAFT_PAPER=paper
            )
            response_complete = self.call_model(
                prompt=prompt_complete,
                response_only=True,
                file_name=f"final_{revision_count}_completion.json",
                folder_name="final",
            )
            response_complete[-1].content = response_complete[-1].content.split("===\n\n", 1)[1]
            content = (
                response[-1].content.rsplit("===\n\n", 1)[0]
                + "===\n\n"
                + response_complete[-1].content
            )
            response_final = [AIMessage(content=content)]
        else:
            response_final = response
        return response_final
