import gc, os, re, tiktoken
from typing import Dict, List, Union, Optional
from langchain.schema import AIMessage, HumanMessage
from proseledger.drafting.utils.file_utils import load_json, save_to_json
from proseledger.drafting.utils.constants import (
    LLM_SEED,
    API_KEY,
    BASE_URL,
    TEMP_DIR,
    API_VERSION,
    MODEL_VER,
    MAX_ITEMS,
    TEMPERATURE,
    CONTEXT_SIZE,
    BEGIN_PROMPT,
    SETTING_NAME,
    ENCODING_NAME,
)


class BaseAgent:
    model_factory = None

    def __init__(
        self,
        name: str,
        review_id: str,
        model_name: str = MODEL_VER,
        context_size: int = CONTEXT_SIZE,
        temperature: float = TEMPERATURE,
        max_memory_items: int = MAX_ITEMS,
        system_prompt: str = "You are a helpful assistant.",
        dataset: str = "srg",
        temp_dir: str = TEMP_DIR,
        encoding_name: str = ENCODING_NAME,
        setting_name: str = SETTING_NAME,
        overwrite_response: bool = False,
        seed: int = LLM_SEED,
    ):
        self.name = name
        self.review_id = review_id
        factory = type(self).model_factory
        if factory is None:
            raise ValueError("Drafting agents require the project call-store adapter.")
        self.model = factory(name, model_name, temperature)
        self.context_size = context_size
        self.max_memory_items = max_memory_items
        self.system_prompt = system_prompt
        self.dataset = dataset
        self.overwrite_response = overwrite_response
        if setting_name.lower() != "general":
            self.temp_dir = os.path.join(temp_dir, dataset, setting_name, review_id)
        else:
            self.temp_dir = os.path.join(temp_dir, dataset, review_id)
        self.encoding_name = encoding_name
        self.setting_name = setting_name
        os.makedirs(self.temp_dir, exist_ok=True)

    def count_tokens(self, string: str) -> int:
        """
        Calculates the number of tokens a prompt uses.

        Parameters:
        string - the string to count the length of.

        Returns:
        the length of the string in tokens.
        """
        model_counter = getattr(self.model, "count_tokens", None)
        if callable(model_counter):
            return model_counter(string)
        encoding = tiktoken.encoding_for_model(self.encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens

    def filter_messages(self, messages: List) -> List:
        """
        Filters out messages based on the following criteria:

        Parameters:
        messages - the messages for the current discussion (as separate discussion lists are made for ease).

        Returns:
        a list of messages filtered based on the aforementioned criteria.
        """
        message_list = [
            message
            for message in messages
            if message.content != BEGIN_PROMPT and "UPDATE: " not in message.content
        ]
        total = len(message_list)
        if total > self.max_memory_items:
            message_list = message_list[total - self.max_memory_items : total]
        n_tokens = sum(
            [
                self.count_tokens(message.content)
                for message in message_list
                if isinstance(message, AIMessage) or isinstance(message, HumanMessage)
            ]
        )
        if n_tokens > self.context_size:
            print("Context too long. Filtering...\n")
            count = 0
            message_list_final = []
            message_list.reverse()
            for message in message_list:
                count += self.count_tokens(message.content)
                if count >= self.context_size:
                    break
                message_list_final.append(message)
            message_list_final.reverse()
        else:
            message_list_final = message_list
        return message_list_final

    def call_model(
        self,
        prompt: Optional[str],
        messages: Optional[List] = None,
        response_only: bool = False,
        to_update: Optional[str] = None,
        custom_update_val: Optional[Union[int, str]] = None,
        folder_name: Optional[str] = None,
        file_name: str = "temp.json",
        do_save: bool = True,
        include_human_prompt: bool = False,
        as_dict: bool = False,
    ) -> Union[Dict, str]:
        """
        Creates a call to the LLM and saves the response.
        The saved response is then used later to reduce costs and allow for more output checking.

        Parameters:
        prompt - the prompt to feed to the model.
        messages - a message list to use if desired (mainly for the agent discussion to create different discussions).
        response_only - whether to only return the response or the full conversation history.
        to_update - the value in the state to update using either the response or another value.
        custom_update_val - the value to add to the state (to the key defined by `to_update`) if provided,
        else it updates the state using the model response.
        folder_name - the name of the subfolder to save in if provided.
        file_name - the filename to use for saving the response.
        do_save - whether to save the LLM output.
        include_human_prompt - whether to include the human prompt or not.
        as_dict - whether to output a dictionary or a string.

        Returns:
        a dictionary or string containing either the full update or only the model response, alongside other values
        that want to updated.
        """
        assert file_name.endswith(".json"), "Please make sure all save files end with `json`!"
        file_name = re.sub("(\\\\|/)", "", file_name)
        human_msg = HumanMessage(content=f"{self.system_prompt}\n\n{prompt}")
        if folder_name is not None and do_save:
            new_dir = os.path.join(self.temp_dir, folder_name)
            os.makedirs(new_dir, exist_ok=True)
            target_file = os.path.join(new_dir, file_name)
        else:
            target_file = os.path.join(self.temp_dir, file_name)
        if os.path.isfile(target_file) and (not self.overwrite_response):
            data = load_json(target_file)
            response = AIMessage(**data)
        else:
            messages_invoke = (
                self.filter_messages(messages + [human_msg])
                if messages is not None
                else [human_msg]
            )
            response = self.model.invoke(messages_invoke)
            data = response.model_dump(mode="json")
            if do_save:
                save_to_json(data, target_file)
        new_messages = [human_msg, response] if include_human_prompt else [response]
        message_list = new_messages if response_only else messages + new_messages
        update = {"messages": message_list}
        if to_update:
            update[to_update] = response if not custom_update_val else custom_update_val
        del data, message_list
        gc.collect()
        if as_dict:
            return update
        else:
            return update["messages"]
