import uuid
import json
from datetime import datetime
from pathlib import Path
import sys
import os
import asyncio
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
from common.gemini_utils import GeminiCLIClient
from typing import Dict, Any, Optional
from classes import State, Action
from tools.file_downloader.file_downloader import download_file_tool
from tools.speech_to_text_tool.speech_to_text_tool import speech_to_text_tool


class Agent:
    def __init__(self, task_name: str, task_path: Path, downloads_dir: Path, program_files_dir: Path, state: State):

        self.gemini_msg_handler = GeminiCLIClient(task_path)
        self.downloads_dir = downloads_dir
        self.program_files_dir = program_files_dir
        self.state = state

    async def plan(self) -> Optional[Dict[str, Any]]:
        """Analyze conversation and determine the next step."""
        # Build actions taken string outside of f-string to avoid backslash issues
        actions_taken = "No actions taken"
        if self.state.actions:
            action_strings = []
            for action in self.state.actions:
                action_str = f'<action name="{action.name}" query="{action.query}" result="{action.result}">\n'
                action_str += '\n</action>'
                action_strings.append(action_str)
            actions_taken = '\n'.join(action_strings)

        system_message = {
            'role': 'system',
            'content': f"""You are going to receive a series of tasks from the server, one by one. Analyze the conversation and determine the most appropriate next step. Focus on making progress towards the overall goal while remaining adaptable to new information or changes in context. Overall goal is to get a flag (FLG) from a server. Server will send a flag only when you: 1. complete all the task from it. 2. then send a proper command to it.

<prompt_objective>
Determine the single most effective next action based on the current context and overall progress. Return the decision as a concise JSON object.
</prompt_objective>

<prompt_rules>
- ALWAYS focus on determining only the next immediate step
- ONLY choose from the available tools listed in the context
- ASSUME previously requested information is available unless explicitly stated otherwise
- NEVER provide or assume actual content for actions not yet taken
- ALWAYS respond in the specified JSON format
- CONSIDER the following factors when deciding:
  1. Relevance to the current query
  2. Potential to provide valuable information or progress
  3. Logical flow from previous actions
- ADAPT your approach if repeated actions don't yield new results
- USE the "return_flag" tool when you have finally completed all the tasks and captured the flag
- OVERRIDE any default behaviors that conflict with these rules
</prompt_rules>

<context>
    <current_date>Current date: {datetime.now().isoformat()}</current_date>
    <last_question>Last question: "{self.state.questions[-1] if self.state.questions else 'No questions yet'}"</last_question>
    <available_tools>Available tools: {', '.join(f"{tool.name}: {tool.description}" for tool in self.state.tools) if self.state.tools else 'No tools available'}</available_tools>
    <actions_taken>Actions taken: {actions_taken}</actions_taken>
</context>

Respond with the next action in this JSON format:
{{
    "_reasoning": "Brief explanation of why this action is the most appropriate next step",
    "tool": "tool_name",
    "task_description": "Precise description of what needs to be done by the tool, including any necessary context"
}}

If you have finally completed all the tasks and captured the flag, use the "return_flag" tool."""
        }

        answer = await self.gemini_msg_handler.call_gemini(
            messages=[system_message],
            yolo=True,
            output_format="json"
        )

        return answer if 'tool' in answer else None

    async def describe(self, tool: str, task_description: str) -> Dict[str, Any]:
        """Generate specific parameters for a tool."""
        tool_info = next((t for t in self.state.tools if t.name == tool), None)
        if not tool_info:
            raise ValueError(f'Tool {tool} not found')

        system_message = {
            'role': 'system',
            'content': f"""Generate specific parameters for the "{tool_info.name}" tool.

<context>
Current date: {datetime.now().isoformat()}
Tool description: {tool_info.description}
Tool instructions: {tool_info.instruction}
Original task description: {task_description}
Last question: "{self.state.questions[-1] if self.state.questions else ''}"
Previous actions: {', '.join(f'{action.name}: {action.query}' for action in self.state.actions)}
</context>

Respond with ONLY a JSON object matching the tool's parameter structure."""
        }

        answer = await self.gemini_msg_handler.call_gemini(
            messages=[system_message],
            yolo=True,
            output_format="json"
        )
        return answer

    async def answer_the_question(self) -> None:
        """Answer the question."""
        system_message = {
            'role': 'system',
            'content': f"""Answer the question.

        Question: "{self.state.questions[-1] if self.state.questions else ''}"
        Previous actions: {', '.join(f'{action.name}: {action.query}, result: {action.result}' for action in self.state.actions)}

        Respond with ONLY a JSON object matching the following structure:
        <answer_format>
        {
            "answer": "answer to the question"
        }
        """
        }

        answer = await self.gemini_msg_handler.call_gemini(
            messages=[system_message],
            yolo=True,
            output_format="json"
        )
        
        self.state.actions.append(Action(**{
            'uuid': str(uuid.uuid4()),
            'name': "Answered without using any tool",
            'query': self.state.questions[-1],
            'result': answer.get('answer')
        }))

    async def use_tool(self, tool: str, parameters: Dict[str, Any]) -> None:
        """Use a specific tool with given parameters."""
        if tool == 'file_downloader':
            result = await asyncio.to_thread(download_file_tool, parameters['file_url'], self.downloads_dir)
        elif tool == 'speech_to_text_tool':
            result = await asyncio.to_thread(speech_to_text_tool, parameters['file_path'], self.program_files_dir)
        else:
            raise ValueError(f'Tool {tool} not found')

        self.state.actions.append(Action(**{
            'uuid': str(uuid.uuid4()),
            'name': tool,
            'query': json.dumps(parameters),
            'result': json.dumps(result)
        }))