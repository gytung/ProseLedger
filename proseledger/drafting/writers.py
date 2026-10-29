import re
from typing import Dict, List, Optional
from proseledger.drafting.base_agent import BaseAgent
from proseledger.drafting.prompts import proposal
from proseledger.drafting.utils.communication import LiRAState
from proseledger.drafting.utils.constants import (
    LLM_SEED,
    TEMP_DIR,
    MODEL_VER,
    MAX_ITEMS,
    CONTEXT_SIZE,
    TEMPERATURE,
    NUM_SECTIONS,
    NUM_SUBSECTIONS,
    SECTION_LEN,
    SETTING_NAME,
    ENCODING_NAME,
)
from proseledger.drafting.prompts.write import (
    WRITER_PROMPT,
    DRAFT_OUTLINE_PROMPT,
    MERGE_OUTLINES_PROMPT,
    FIX_OUTLINE_PROMPT,
    WRITE_TITLE_ABSTRACT_PROMPT,
    WRITE_CONTENT_PROMPT,
    WRITE_CONCLUSION_PROMPT,
    FIX_TITLE_ABSTRACT_PROMPT,
    FIX_CONTENT_PROMPT,
    FIX_CONCLUSION_PROMPT,
)

type_pattern = "## TYPE\\n(.+)\\n"
reason_pattern = "## REASON\\n(.+\\n?(?:\\n.+){1,7})"
citation_pattern = "\\[([^\\[\\]\\n]+)\\]"
chain_of_thought_pattern = "## THOUGHTS\\n(?:.+\\n){1,10}\\n"


class OutlineDrafterAgent(BaseAgent):

    def __init__(
        self,
        name: str,
        review_id: str,
        seed: int = LLM_SEED,
        model_name: str = MODEL_VER,
        context_size: int = CONTEXT_SIZE,
        temperature: float = TEMPERATURE,
        max_memory_items: int = MAX_ITEMS,
        review_topic: str = "Computer Science",
        dataset: str = "srg",
        temp_dir: str = TEMP_DIR,
        encoding_name: str = ENCODING_NAME,
        setting_name: str = SETTING_NAME,
        overwrite_responses: bool = False,
        proposal_mode: bool = False,
    ):
        super().__init__(
            name=name,
            model_name=model_name,
            context_size=context_size,
            seed=seed,
            temperature=temperature,
            max_memory_items=max_memory_items,
            system_prompt=WRITER_PROMPT,
            dataset=dataset,
            temp_dir=temp_dir,
            review_id=review_id,
            encoding_name=encoding_name,
            setting_name=setting_name,
            overwrite_response=overwrite_responses,
        )
        self.review_topic = review_topic
        self.proposal_mode = proposal_mode

    def format_response(self, group_analysis: Dict) -> Dict:
        """
        Formats a group analysis for easier processing.

        Parameters:
        group_analysis - the group analysis response from the researcher group.

        Returns:
        a dictionary containing the type and reasoning for the selected group.
        """
        content = group_analysis[-1].content
        type_search = re.search(type_pattern, content)
        reason_search = re.search(reason_pattern, content)
        return {"type": type_search.group(1), "reason": reason_search.group(1)}

    def create_outline_single(
        self,
        paper_group: Dict,
        n_sections: int = NUM_SECTIONS,
        n_subsections: int = NUM_SUBSECTIONS,
    ) -> List:
        """
        Creates a paper outline based on the analyses and type provided.
        As multiple paper analyses groups are possible, this is performed on each group using
        separate calls.

        Parameters:
        paper_group - the paper analyses in a group.
        n_sections - the number of sections to include (functions more as a suggestion).
        n_subsections - the number of subsections to include within each section (functions more as a suggestion).

        Returns:
        the outline as an `AIMessage` in a list.
        """
        group_id, paper_analyses = (paper_group["id"], paper_group["content"])
        template = proposal.OUTLINE_DRAFT if self.proposal_mode else DRAFT_OUTLINE_PROMPT
        prompt = template.format(
            REVIEW_TOPIC=self.review_topic,
            NUM_SECTIONS=n_sections,
            NUM_SUBSECTIONS=n_subsections,
            PAPER_ANALYSES=paper_analyses,
        )
        response = self.call_model(
            prompt=prompt,
            response_only=True,
            file_name=f"outline_{group_id}.json",
            folder_name="outline",
        )
        return response

    def format_outlines(self, draft_outlines: List[Dict]) -> str:
        """
        Formats a list of outlines into a string.

        Parameters:
        draft_outlines - the list of draft outline responses.

        Returns:
        the outlines combined into a string.
        """
        text = ""
        for outline in draft_outlines:
            text += outline[-1].content + "\n\n"
        return text.strip()

    def merge_outlines(
        self,
        draft_outlines: List[Dict],
        n_sections: int = NUM_SECTIONS,
        n_subsections: int = NUM_SUBSECTIONS,
        revision_count: int = 1,
    ) -> List:
        """
        Combines a collection of draft outlines

        Parameters:
        draft_outlines - the list of draft outline responses.
        n_sections - the number of sections to include (functions more as a suggestion).
        n_subsections - the number of subsections to include within each section (functions more as a suggestion).
        revision_count - the outline revision number.

        Returns:
        the outline as an `AIMessage` in a list.
        """
        outlines_merged = self.format_outlines(draft_outlines)
        template = proposal.OUTLINE_MERGE if self.proposal_mode else MERGE_OUTLINES_PROMPT
        prompt = template.format(
            REVIEW_TOPIC=self.review_topic,
            NUM_SECTIONS=n_sections,
            NUM_SUBSECTIONS=n_subsections,
            OUTLINES=outlines_merged,
        )
        response = self.call_model(
            prompt=prompt,
            response_only=True,
            file_name=f"merged_outline_{revision_count}.json",
            folder_name="outline",
        )
        return response

    def fix_outline(
        self,
        messages: List,
        draft_outlines: List[Dict],
        n_sections: int = NUM_SECTIONS,
        n_subsections: int = NUM_SUBSECTIONS,
        revision_count: int = 1,
    ) -> List:
        """
        Fixes an outline using the review history.

        Parameters:
        messages - the messages for the current discussion (as its own list for ease of processing).
        draft_outlines - the list of draft outline responses.
        n_sections - the number of sections to include (functions more as a suggestion).
        n_subsections - the number of subsections to include within each section (functions more as a suggestion).
        revision_count - the outline revision number.

        Returns:
        the new response containing the list of messages which includes the updated outline.
        """
        outlines_merged = self.format_outlines(draft_outlines)
        template = proposal.OUTLINE_FIX if self.proposal_mode else FIX_OUTLINE_PROMPT
        prompt = template.format(
            REVIEW_TOPIC=self.review_topic,
            NUM_SECTIONS=n_sections,
            NUM_SUBSECTIONS=n_subsections,
            OUTLINES=outlines_merged,
        )
        response = self.call_model(
            prompt=prompt,
            messages=messages,
            response_only=False,
            file_name=f"merged_outline_{revision_count}.json",
            folder_name="outline",
        )
        return response


class ContentWriterAgent(BaseAgent):

    def __init__(
        self,
        name: str,
        review_id: str,
        seed: int = LLM_SEED,
        model_name: str = MODEL_VER,
        context_size: int = CONTEXT_SIZE,
        temperature: float = TEMPERATURE,
        max_memory_items: int = MAX_ITEMS,
        review_topic: str = "Computer Science",
        dataset: str = "srg",
        temp_dir: str = TEMP_DIR,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        setting_name: str = SETTING_NAME,
        overwrite_responses: bool = False,
        proposal_mode: bool = False,
    ):
        super().__init__(
            name=name,
            model_name=model_name,
            context_size=context_size,
            seed=seed,
            temperature=temperature,
            max_memory_items=max_memory_items,
            system_prompt=WRITER_PROMPT,
            dataset=dataset,
            temp_dir=temp_dir,
            review_id=review_id,
            setting_name=setting_name,
            overwrite_response=overwrite_responses,
        )
        self.review_topic = review_topic
        self.proposal_mode = proposal_mode
        self.embedding_model = embedding_model
        self.vectorstore = None

    def parse_outline(self, outline: str) -> Dict:
        """
        Parses an outline into sections and descriptions.

        Parameters:
        outline - the outline to parse.

        Returns:
        a dictionary containing the lists of headers, descriptions, the present references, and
        the name of the section containing the subsection if applicable.
        """
        outline = re.sub("(?ms)^## THOUGHTS[^\\S\\n]*\\n.*?(?=^#{1,2}[ \\t]+|\\Z)", "", outline)
        headings = list(re.finditer("(?m)^(#{1,2})[ \\t]+([^\\n]+)", outline))
        out = {"headers": [], "descriptions": [], "references": [], "header_higher_level": []}
        header_higher = "None"
        for index, heading in enumerate(headings):
            header = heading.group(2).strip()
            end = headings[index + 1].start() if index + 1 < len(headings) else len(outline)
            content = outline[heading.end() : end].strip()
            references = re.findall(citation_pattern, content)
            content = re.sub(citation_pattern, "", content)
            new_references = []
            for reference in references:
                for ref in reference.split("|"):
                    ref = ref.strip()
                    if ref and ref not in new_references:
                        new_references.append(ref)
            out["headers"].append(header.strip())
            out["descriptions"].append(content.strip())
            out["references"].append(new_references)
            if heading.group(1) == "#":
                header_higher = header
                out["header_higher_level"].append("None")
            else:
                out["header_higher_level"].append(header_higher)
        return out

    def create_db(self, state: LiRAState):
        """
        Builds our lightweight lexical index over the supplied paper analyses.
        This replaces upstream FAISS/HuggingFace retrieval; no model is loaded.

        Parameters:
        state - the worfklow's current state.
        """
        analyses = state["researcher_analyses"]
        documents = []
        for analysis in analyses:
            content = (
                "TITLE:" + analysis["title"] + "\n\nCONTENT:" + analysis["content"][-1].content
            )
            documents.append(
                {
                    "id": analysis["id"],
                    "title": self._normalize_title(analysis["title"]),
                    "title_terms": self._terms(analysis["title"]),
                    "terms": self._terms(content),
                    "page_content": content,
                }
            )
        self.vectorstore = documents

    @staticmethod
    def _normalize_title(text: str) -> str:
        return " ".join(re.findall("[^\\W_]+", text.casefold()))

    @staticmethod
    def _terms(text: str) -> set:
        stopwords = {
            "a",
            "an",
            "the",
            "and",
            "or",
            "of",
            "in",
            "on",
            "to",
            "for",
            "with",
            "is",
            "are",
            "by",
        }
        return set(re.findall("[^\\W_]+", text.casefold())) - stopwords

    def get_references(self, state: LiRAState, description: str, references: List) -> str:
        """
        Retrieves the appropriate references for a section.

        Parameters:
        state - the worfklow's current state.
        description - the description of the section without references.
        references - the list of references listed for the subsection to use.

        Returns:
        the references as a string.
        """
        if self.vectorstore is None:
            self.create_db(state)
        documents = self.vectorstore
        len_references_total = len(state["researcher_analyses"])
        n_rag = len_references_total // 4 if len_references_total // 4 > 3 else 3
        n_rag = min(n_rag, 150, len(documents))
        if self.proposal_mode:
            required_titles = {self._normalize_title(reference) for reference in references}
            explicit_count = sum((doc["title"] in required_titles for doc in documents))
            n_rag = min(max(n_rag, explicit_count), 150, len(documents))
        selected = []
        unresolved = []

        def add(index):
            if index not in selected and len(selected) < n_rag:
                selected.append(index)

        def ranked(query):
            terms = self._terms(query)
            scores = [
                (2 * len(terms & doc["title_terms"]) + len(terms & doc["terms"]), index)
                for index, doc in enumerate(documents)
            ]
            return sorted(scores, key=lambda item: (-item[0], item[1]))

        for reference in references:
            title = self._normalize_title(reference)
            matches = [i for i, doc in enumerate(documents) if title and doc["title"] == title]
            if matches:
                add(matches[0])
            else:
                unresolved.append(reference)
        for reference in unresolved:
            for score, index in ranked(reference):
                if score > 0 and index not in selected:
                    add(index)
                    break
        for _, index in ranked(description):
            add(index)
            if len(selected) >= n_rag:
                break
        return "\n\n".join((documents[index]["page_content"] for index in selected))

    def write_content_section(
        self,
        state: LiRAState,
        header: str,
        description: str,
        references: List[str],
        header_high_level: str = "None",
        revision_count: int = 1,
        section_len: int = SECTION_LEN,
    ) -> Optional[str]:
        """
        Writes the review content for one section based on the outline header and analysis contents.

        Parameters:
        state - the worfklow's current state.
        header - the (sub)section's title.
        description - the description of the section without references.
        references - the list of references listed for the subsection to use.
        header_high_level - the subsection's main section header if this is a subsection.
        revision_count - the content revision number.
        section_len - the number of words to include in each section.

        Returns:
        the section content as an `AIMessage` in a list.
        """
        save_name = re.sub(" ", "_", header.lower())
        if "conclusion" in header.lower() and "in" not in header.lower():
            return None
        ref_descriptions = self.get_references(state, description, references)
        template = proposal.CONTENT if self.proposal_mode else WRITE_CONTENT_PROMPT
        prompt = template.format(
            REVIEW_TOPIC=self.review_topic,
            SECTION_TITLE=header,
            SECTION_DESCRIPTION=description,
            HEADER_HIGH_LEVEL=header_high_level,
            PAPER_ANALYSES=ref_descriptions,
            SECTION_LEN=section_len if self.proposal_mode else section_len + 100,
        )
        response = self.call_model(
            prompt=prompt,
            response_only=True,
            file_name=f"{save_name}.json",
            folder_name=f"section_{revision_count}",
        )
        return response

    def revise_content_section(
        self,
        state: LiRAState,
        header: str,
        description: str,
        references: List[str],
        header_high_level: str = "None",
        revision_count: int = 2,
        section_len: int = SECTION_LEN,
    ) -> List:
        """
        Writes the review content for one section based on the outline header and analysis contents.

        Parameters:
        state - the worfklow's current state.
        header - the (sub)section's title.
        description - the description of the section without references.
        references - the list of references listed for the subsection to use.
        header_high_level - the subsection's main section header if this is a subsection.
        revision_count - the content revision number.
        section_len - the number of words to include in each section.

        Returns:
        the section content as an `AIMessage` in a list.
        """
        save_name = re.sub(" ", "_", header.lower())
        if "conclusion" in header.lower() and "in" not in header.lower():
            return None
        ref_descriptions = self.get_references(state, description, references)
        discussion = state["content_discussion"][header]
        template = proposal.CONTENT_FIX if self.proposal_mode else FIX_CONTENT_PROMPT
        prompt = template.format(
            REVIEW_TOPIC=self.review_topic,
            SECTION_TITLE=header,
            SECTION_DESCRIPTION=description,
            HEADER_HIGH_LEVEL=header_high_level,
            PAPER_ANALYSES=ref_descriptions,
            SECTION_LEN=section_len if self.proposal_mode else section_len + 100,
        )
        response = self.call_model(
            prompt=prompt,
            messages=discussion,
            response_only=True,
            file_name=f"{save_name}.json",
            folder_name=f"section_{revision_count}",
        )
        response[-1].content = re.sub(chain_of_thought_pattern, "", response[-1].content)
        return response

    def write_title_abstract(
        self, paper_body: str, revision_count: int = 1, feedback: bool = False
    ) -> str:
        """
        Writes a literature review abstract based on the contents of the main paper.

        Parameters:
        paper_body - the main content of the literature review.
        revision_count - the content revision number.
        feedback - whether feedback for the section has already been provided.

        Returns:
        the title and abstract as an `AIMessage` in a list.
        """
        if feedback:
            template = proposal.ABSTRACT if self.proposal_mode else FIX_TITLE_ABSTRACT_PROMPT
            prompt = template.format(REVIEW_CONTENT=paper_body)
            response = self.call_model(
                prompt=prompt,
                response_only=True,
                file_name="title_abstract.json",
                folder_name=f"section_{revision_count}",
            )
            response[-1].content = re.sub(chain_of_thought_pattern, "", response[-1].content)
            return response
        template = proposal.ABSTRACT if self.proposal_mode else WRITE_TITLE_ABSTRACT_PROMPT
        prompt = template.format(REVIEW_CONTENT=paper_body)
        response = self.call_model(
            prompt=prompt,
            response_only=True,
            file_name="title_abstract.json",
            folder_name=f"section_{revision_count}",
        )
        return response

    def write_conclusion(
        self,
        state: LiRAState,
        paper_body: str,
        conc_title: str = "Conclusion",
        revision_count: int = 1,
        feedback: bool = False,
    ) -> List:
        """
        Writes a literature review conclusion based on the contents of the main paper.

        Parameters:
        state - the worfklow's current state.
        paper_body - the main content of the literature review.
        conc_title - the conclusion's title (perhaps it's a variation such as "Conclusion and Future Work").
        revision_count - the content revision number.
        feedback - whether feedback for the section has already been provided.

        Returns:
        the conclusion as an `AIMessage` in a list.
        """
        if feedback:
            template = proposal.CONCLUSION if self.proposal_mode else FIX_CONCLUSION_PROMPT
            prompt = template.format(REVIEW_CONTENT=paper_body, CONCLUSION_TITLE=conc_title)
            response = self.call_model(
                prompt=prompt,
                messages=state["content_discussion"][conc_title],
                response_only=True,
                file_name=f"{conc_title}.json",
                folder_name=f"section_{revision_count}",
            )
            response[-1].content = re.sub(chain_of_thought_pattern, "", response[-1].content)
            return response
        template = proposal.CONCLUSION if self.proposal_mode else WRITE_CONCLUSION_PROMPT
        prompt = template.format(REVIEW_CONTENT=paper_body)
        response = self.call_model(
            prompt=prompt,
            response_only=True,
            file_name=f"{conc_title}.json",
            folder_name=f"section_{revision_count}",
        )
        return response
