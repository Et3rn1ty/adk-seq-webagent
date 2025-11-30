from google.adk.agents import LlmAgent
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from utils.file_loader import load_instructions_file

question_generator_agent = LlmAgent(
    name = 'question_generator_agent',
    model = 'gemini-2.0-flash',
    instruction = (load_instructions_file('agents/question_generator/instructions.txt')),
    description = (load_instructions_file('agents/question_generator/description.txt')),
    output_key='questions_generator_output'
)