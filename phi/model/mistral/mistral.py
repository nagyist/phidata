from typing import Optional, List, Iterator, Dict, Any, Union

from phi.model.base import Model
from phi.model.message import Message
from phi.model.base import ModelResponse
from phi.tools.function import FunctionCall
from phi.utils.log import logger
from phi.utils.timer import Timer
from phi.utils.tools import get_function_call_for_tool_call

try:
    from mistralai import Mistral
    from mistralai.models.chatcompletionresponse import ChatCompletionResponse
    from mistralai.models.deltamessage import DeltaMessage
    from mistralai.models.responseformat import ResponseFormat as ChatCompletionResponseFormat
    from mistralai.models.chatcompletionstreamrequest import ChatCompletionStreamRequest
    from mistralai.models.toolcall import ToolCall as ChoiceDeltaToolCall
    from mistralai.models.function import Function
    from mistralai.models.toolmessage import ToolMessage
    from mistralai.models.usermessage import UserMessage
except ImportError:
    logger.error("`mistralai` not installed")
    raise


class MistralChat(Model):
    
    id: str = "gpt-4o"
    name: str = "OpenAIChat"
    provider: str = "OpenAI"

    # -*- Request parameters
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    random_seed: Optional[int] = None
    safe_mode: bool = False
    safe_prompt: bool = False
    response_format: Optional[Union[Dict[str, Any], ChatCompletionResponseFormat]] = None
    request_params: Optional[Dict[str, Any]] = None
    # -*- Client parameters
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    max_retries: Optional[int] = None
    timeout: Optional[int] = None
    client_params: Optional[Dict[str, Any]] = None
    # -*- Provide the MistralClient manually
    mistral_client: Optional[Mistral] = None

    @property
    def client(self) -> Mistral:
        if self.mistral_client:
            return self.mistral_client

        _client_params: Dict[str, Any] = {}
        if self.api_key:
            _client_params["api_key"] = self.api_key
        if self.endpoint:
            _client_params["endpoint"] = self.endpoint
        if self.max_retries:
            _client_params["max_retries"] = self.max_retries
        if self.timeout:
            _client_params["timeout"] = self.timeout
        if self.client_params:
            _client_params.update(self.client_params)
        return Mistral(**_client_params)

    @property
    def api_kwargs(self) -> Dict[str, Any]:
        _request_params: Dict[str, Any] = {}
        if self.temperature:
            _request_params["temperature"] = self.temperature
        if self.max_tokens:
            _request_params["max_tokens"] = self.max_tokens
        if self.top_p:
            _request_params["top_p"] = self.top_p
        if self.random_seed:
            _request_params["random_seed"] = self.random_seed
        if self.safe_mode:
            _request_params["safe_mode"] = self.safe_mode
        if self.safe_prompt:
            _request_params["safe_prompt"] = self.safe_prompt
        # if self.tools:
        #     _request_params["tools"] = self.get_tools_for_api()
        #     if self.tool_choice is None:
        #         _request_params["tool_choice"] = "auto"
        #     else:
        #         _request_params["tool_choice"] = self.tool_choice
        if self.request_params:
            _request_params.update(self.request_params)
        return _request_params

    def to_dict(self) -> Dict[str, Any]:
        _dict = super().to_dict()
        if self.temperature:
            _dict["temperature"] = self.temperature
        if self.max_tokens:
            _dict["max_tokens"] = self.max_tokens
        if self.random_seed:
            _dict["random_seed"] = self.random_seed
        if self.safe_mode:
            _dict["safe_mode"] = self.safe_mode
        if self.safe_prompt:
            _dict["safe_prompt"] = self.safe_prompt
        if self.response_format:
            _dict["response_format"] = self.response_format
        return _dict

    def invoke(self, messages: List[Message], tools: Optional[List[Function]] = None) -> ChatCompletionResponse:
        return self.client.chat.complete(
            messages=[m.to_dict() for m in messages],
            model=self.id,
            tools=tools if tools is not None else tools,
            **self.api_kwargs,
        )

    def invoke_stream(self, messages: List[Message]) -> Iterator[ChatCompletionStreamRequest]:
        yield from self.client.chat.stream(
            messages=[m.to_dict() for m in messages],
            model=self.id,
            **self.api_kwargs,
        )  # type: ignore

    def _handle_tool_calls(
        self, assistant_message: Message, messages: List[Message], model_response: ModelResponse
    ) -> Optional[ModelResponse]:
        """
        Handle tool calls in the assistant message.

        Args:
            assistant_message (Message): The assistant message.
            messages (List[Message]): The list of messages.
            model_response (ModelResponse): The model response.

        Returns:
            Optional[ModelResponse]: The model response after handling tool calls.
        """
        if assistant_message.tool_calls is not None and len(assistant_message.tool_calls) > 0 and self.run_tools:
            logger.debug("---------- Mistral Tool Calls Start ----------")

            logger.debug(f"Assistant message: {assistant_message}")
            logger.debug(f"Messages: {messages}")
            logger.debug(f"Model response: {model_response}")

            

            model_response.content = ""
            tool_role: str = "tool"
            function_calls_to_run: List[FunctionCall] = []
            function_call_results: List[Message] = []
            for tool_call in assistant_message.tool_calls:
                _tool_call_id = tool_call.get("id")
                logger.debug(f"Tool call FOR fucntion call: {tool_call}")
                _function_call = get_function_call_for_tool_call(tool_call, self.functions)
                if _function_call is None:
                    messages.append(
                        Message(
                            role="tool",
                            tool_call_id=_tool_call_id,
                            content="Could not find function to call.",
                        )
                    )
                    continue
                if _function_call.error is not None:
                    messages.append(
                        Message(
                            role="tool",
                            tool_call_id=_tool_call_id,
                            content=_function_call.error,
                        )
                    )
                    continue
                function_calls_to_run.append(_function_call)

            if self.show_tool_calls:
                model_response.content += "\nRunning:"
                for _f in function_calls_to_run:
                    model_response.content += f"\n - {_f.get_call_str()}"
                model_response.content += "\n\n"

            for _ in self.run_function_calls(
                function_calls=function_calls_to_run, function_call_results=function_call_results, tool_role=tool_role
            ):
                pass

            if len(function_call_results) > 0:
                messages.extend(function_call_results)

            return model_response
        return None
    
    def response(self, messages: List[Message], tools: Optional[List[Function]] = None) -> ModelResponse:
        logger.debug("---------- Mistral Response Start ----------")
        # -*- Log messages for debugging
        for m in messages:
            m.log()
        
        model_response = ModelResponse()

        response_timer = Timer()
        response_timer.start()
        response: ChatCompletionResponse = self.invoke(messages=messages, tools=tools)
        response_timer.stop()
        logger.debug(f"Time to generate response: {response_timer.elapsed:.4f}s")
        # logger.debug(f"Mistral response type: {type(response)}")
        # logger.debug(f"Mistral response: {response}")

        # -*- Parse response
        response_message: ChatCompletionResponse = response.choices[0].message
        logger.debug(f"Response message: {response_message}")
        # -*- Create assistant message
        assistant_message = Message(
            role=response_message.role or "assistant",
            content=response_message.content,
        )

        import json
        response_tool_calls = response_message.tool_calls
        if response_tool_calls:
            tool_calls: List[Dict[str, Any]] = []
            for tools in response_tool_calls:
                tool_calls.append(
                    {
                        "type": "function",
                        "function": Function(
                            name=tools.function.name,
                            parameters=json.loads(tools.function.arguments)
                        )
                    }
                )
            if len(tool_calls) > 0:
                assistant_message.tool_calls = tool_calls

        # -*- Update usage metrics
        # Add response time to metrics
        assistant_message.metrics["time"] = response_timer.elapsed
        if "response_times" not in self.metrics:
            self.metrics["response_times"] = []
        self.metrics["response_times"].append(response_timer.elapsed)
        # Add token usage to metrics
        self.metrics.update(response.usage.model_dump())

        # -*- Add assistant message to messages
        messages.append(assistant_message)
        assistant_message.log()

        # -*- Parse and run tool calls
        if self._handle_tool_calls(assistant_message, messages, model_response):
            response_after_tool_calls = self.response(messages=messages, tools=tools)
            if response_after_tool_calls.content is not None:
                if model_response.content is None:
                    model_response.content = ""
                model_response.content += response_after_tool_calls.content
            return model_response        

        # -*- Return content if no function calls are present
        if assistant_message.content is not None:
            model_response.content = assistant_message.get_content_string()

        logger.debug("---------- Mistral Response End ----------")
        return model_response

    def response_stream(self, messages: List[Message]) -> Iterator[str]:
        logger.debug("---------- Mistral Response Start ----------")
        # -*- Log messages for debugging
        for m in messages:
            m.log()

        assistant_message_role = None
        assistant_message_content = ""
        assistant_message_tool_calls: Optional[List[ChoiceDeltaToolCall]] = None
        response_timer = Timer()
        response_timer.start()
        for response in self.invoke_stream(messages=messages):
            # logger.debug(f"Mistral response type: {type(response)}")
            # logger.debug(f"Mistral response: {response}")
            # -*- Parse response
            response_delta: DeltaMessage = response.choices[0].delta
            if assistant_message_role is None and response_delta.role is not None:
                assistant_message_role = response_delta.role
            response_content: Optional[str] = response_delta.content
            response_tool_calls: Optional[List[ChoiceDeltaToolCall]] = response_delta.tool_calls

            # -*- Return content if present, otherwise get tool call
            if response_content is not None:
                assistant_message_content += response_content
                yield response_content

            # -*- Parse tool calls
            if response_tool_calls is not None and len(response_tool_calls) > 0:
                if assistant_message_tool_calls is None:
                    assistant_message_tool_calls = []
                assistant_message_tool_calls.extend(response_tool_calls)

        response_timer.stop()
        logger.debug(f"Time to generate response: {response_timer.elapsed:.4f}s")

        # -*- Create assistant message
        assistant_message = Message(role=(assistant_message_role or "assistant"))
        # -*- Add content to assistant message
        if assistant_message_content != "":
            assistant_message.content = assistant_message_content
        # -*- Add tool calls to assistant message
        if assistant_message_tool_calls is not None:
            assistant_message.tool_calls = [t.model_dump() for t in assistant_message_tool_calls]

        # -*- Update usage metrics
        # Add response time to metrics
        assistant_message.metrics["time"] = response_timer.elapsed
        if "response_times" not in self.metrics:
            self.metrics["response_times"] = []
        self.metrics["response_times"].append(response_timer.elapsed)

        # -*- Add assistant message to messages
        messages.append(assistant_message)
        assistant_message.log()

        # -*- Parse and run tool calls
        if assistant_message.tool_calls is not None and len(assistant_message.tool_calls) > 0:
            function_calls_to_run: List[FunctionCall] = []
            for tool_call in assistant_message.tool_calls:
                _tool_call_id = tool_call.get("id")
                _function_call = get_function_call_for_tool_call(tool_call, self.functions)
                if _function_call is None:
                    messages.append(
                        Message(role="tool", tool_call_id=_tool_call_id, content="Could not find function to call.")
                    )
                    continue
                if _function_call.error is not None:
                    messages.append(
                        Message(
                            role="tool", tool_call_id=_tool_call_id, tool_call_error=True, content=_function_call.error
                        )
                    )
                    continue
                function_calls_to_run.append(_function_call)

            if self.show_tool_calls:
                if len(function_calls_to_run) == 1:
                    yield f"\n - Running: {function_calls_to_run[0].get_call_str()}\n\n"
                elif len(function_calls_to_run) > 1:
                    yield "\nRunning:"
                    for _f in function_calls_to_run:
                        yield f"\n - {_f.get_call_str()}"
                    yield "\n\n"

            function_call_results = self.run_function_calls(function_calls_to_run)
            if len(function_call_results) > 0:
                messages.extend(function_call_results)
            # -*- Yield new response using results of tool calls
            yield from self.response_stream(messages=messages)
        logger.debug("---------- Mistral Response End ----------")
