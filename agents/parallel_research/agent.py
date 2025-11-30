from google.adk.agents import ParallelAgent, LlmAgent
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from utils.file_loader import load_instructions_file
from google.adk.tools import google_search

base_description = load_instructions_file('agents/parallel_research/description.txt')
base_instruction = load_instructions_file('agents/parallel_research/instructions.txt')


question_researcher_agent_1 = LlmAgent(
    name='QuestionResearcher1',
    model='gemini-2.0-flash',
    instruction=f'You are assigned to answer QUESTION NUMBER 1 only.\n\n{base_instruction}',
    description=f'{base_description} \nThis agent specifically handles question #1',
    tools=[google_search],
    output_key='question_1_research_output'
)
question_researcher_agent_2 = LlmAgent(
    name='QuestionResearcher2',
    model='gemini-2.0-flash',
    instruction=f'You are assigned to answer QUESTION NUMBER 2 only.\n\n{base_instruction}',
    description=f'{base_description} \nThis agent specifically handles question #2',
    tools=[google_search],
    output_key='question_2_research_output'
)
question_researcher_agent_3 = LlmAgent(
    name='QuestionResearcher1',
    model='gemini-2.0-flash',
    instruction=f'You are assigned to answer QUESTION NUMBER 3 only.\n\n{base_instruction}',
    description=f'{base_description} \nThis agent specifically handles question #3',
    tools=[google_search],
    output_key='question_3_research_output'
)
question_researcher_agent_4 = LlmAgent(
    name='QuestionResearcher4',
    model='gemini-2.0-flash',
    instruction=f'You are assigned to answer QUESTION NUMBER 4 only.\n\n{base_instruction}',
    description=f'{base_description} \nThis agent specifically handles question #4',
    tools=[google_search],
    output_key='question_4_research_output'
)
question_researcher_agent_5 = LlmAgent(
    name='QuestionResearcher5',
    model='gemini-2.0-flash',
    instruction=f'You are assigned to answer QUESTION NUMBER 5 only.\n\n{base_instruction}',
    description=f'{base_description} \nThis agent specifically handles question #5',
    tools=[google_search],
    output_key='question_5_research_output'
)

parallel_research_agent = ParallelAgent(
    name='parallel_research_agent',
    sub_agents = [
        question_researcher_agent_1,
        question_researcher_agent_2,
        question_researcher_agent_3,
        question_researcher_agent_4,
        question_researcher_agent_5
    ],
    description='This agent runs 5 question research agents in parallel to research and answer all five questions simultaneously.'
)