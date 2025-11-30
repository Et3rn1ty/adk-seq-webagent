from google.adk.agents import LlmAgent
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from utils.file_loader import load_instructions_file

query_generator_agent = LlmAgent(
    name = 'query_generator_agent',
    model = 'gemini-2.0-flash',
    instruction = load_instructions_file('agents/query_generator/instructions.txt'),
    description = load_instructions_file('agents/query_generator/description.txt'),
    output_key='merged_query_output'
)