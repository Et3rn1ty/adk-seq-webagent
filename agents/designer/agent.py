from google.adk.agents import LlmAgent
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from utils.file_loader import load_instructions_file

designer_agent = LlmAgent(
    name = 'designer_agent',
    model = 'gemini-flash-latest',
    instructions = load_instructions_file('agents/designer/instructions.txt'),
    description = load_instructions_file('agents/designer/description.txt'),
    output_key = 'designer_output'
)

