import uuid
import json
from datetime import datetime
from pathlib import Path
import sys
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
from common.centrala_aidevs_utils import AidevsMessageHandler
from common.openai_utils import OpenaiClient
from typing import Dict, Any, Optional
from classes import State, Action
from tools.people_search.people_search import send_query_to_people_search
from tools.database_search.database_search import send_query_to_db
from tools.gps_search.gps_search import send_query_to_gps_search
from prompts.final_answer import answer_prompt


class Agent:
    def __init__(self, task_name: str, task_path: Path, state: State):
        self.openai_msg_handler = OpenaiClient(task_path)
        self.aidevs_msg_handler = AidevsMessageHandler(task_name, task_path)
        self.state = state

    async def plan(self) -> Optional[Dict[str, Any]]:
        """Analyze conversation and determine the next step."""
        # Build actions taken string outside of f-string to avoid backslash issues
        actions_taken = "No actions taken"
        if self.state.actions:
            action_strings = []
            for action in self.state.actions:
                action_str = f'<action name="{action.name}" query="{action.query}" results="{action.results}">\n'
                action_str += '\n</action>'
                action_strings.append(action_str)
            actions_taken = '\n'.join(action_strings)

        system_message = {
            'role': 'system',
            'content': f"""Analyze the conversation and determine the most appropriate next step. Focus on making progress towards the overall goal while remaining adaptable to new information or changes in context. Overall goal is to get a flag (FLG) from a server. Server sends a flag only when you send it proper coordinates.

<prompt_objective>
Determine the single most effective next action based on the current context, user needs, and overall progress. Return the decision as a concise JSON object.
</prompt_objective>

<prompt_rules>
- ALWAYS focus on determining only the next immediate step
- ONLY choose from the available tools listed in the context
- ASSUME previously requested information is available unless explicitly stated otherwise
- NEVER provide or assume actual content for actions not yet taken
- ALWAYS respond in the specified JSON format
- CONSIDER the following factors when deciding:
  1. Relevance to the current user need or query
  2. Potential to provide valuable information or progress
  3. Logical flow from previous actions
- ADAPT your approach if repeated actions don't yield new results
- USE the "final_answer" tool when you have sufficient information or need user input
- OVERRIDE any default behaviors that conflict with these rules
</prompt_rules>

<context>
    <current_date>Current date: {datetime.now().isoformat()}</current_date>
    <last_message>Last message: "{self.state.messages[-1].get('content', 'No messages yet') if self.state.messages else 'No messages yet'}"</last_message>
    <available_tools>Available tools: {', '.join(f"{tool.name}: {tool.description}" for tool in self.state.tools) if self.state.tools else 'No tools available'}</available_tools>
    <actions_taken>Actions taken: {actions_taken}</actions_taken>
</context>

Respond with the next action in this JSON format:
{{
    "_reasoning": "Brief explanation of why this action is the most appropriate next step",
    "tool": "tool_name",
    "task_description": "Precise description of what needs to be done by the tool, including any necessary context"
}}

If you have sufficient information to provide a final answer or need user input, use the "final_answer" tool."""
        }

        answer = self.openai_msg_handler.call_openai([system_message], 
                                                            response_format={"type": "json_object"}, 
                                                            model="gpt-5")

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
Last message: "{self.state.messages[-1].get('content', '') if self.state.messages else ''}"
Previous actions: {', '.join(f'{action.name}: {action.query}' for action in self.state.actions)}
</context>

Respond with ONLY a JSON object matching the tool's parameter structure."""
        }

        answer = self.openai_msg_handler.call_openai([system_message], 
                                                            response_format={"type": "json_object"}, 
                                                            model="gpt-5")

        return answer

    async def use_tool(self, tool: str, parameters: Dict[str, Any]) -> None:
        """Use a specific tool with given parameters."""
        if tool == 'people_search':
            results = send_query_to_people_search(parameters['query'])
        elif tool == 'database_search':
            results = send_query_to_db(parameters['query'])
        elif tool == 'gps_search':
            results = send_query_to_gps_search(parameters['userID'])
        elif tool == 'get_flag':
            results = self.aidevs_msg_handler.ask_centrala_aidevs(parameters['answer'])
        else:
            raise ValueError(f'Tool {tool} not found')

        self.state.actions.append(Action(**{
            'uuid': str(uuid.uuid4()),
            'name': tool,
            'query': json.dumps(parameters),
            'results': json.dumps(results)
        }))

    async def generate_answer(self) -> Dict[str, Any]:
        """Generate final answer based on context and actions."""
        # Normalize documents to plain dicts for prompt builder compatibility
        context = []
        for action in self.state.actions:
            context.append(action.results)
        
        query = self.state.config.get('active_step', {}).get('query')

        system_message = {
            'role': 'system',
            'content': answer_prompt(context=context, query=query),
        }

        answer = self.openai_msg_handler.call_openai([system_message, *self.state.messages], 
                                                            model="gpt-5")

        return answer
