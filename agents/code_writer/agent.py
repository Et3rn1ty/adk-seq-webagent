from google.adk.agents import LlmAgent
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from utils.file_loader import load_instructions_file
from tools.file_writer_tool import write_to_file
from tools.git_operations_tool import GitOperationsTool

gitOps = GitOperationsTool()

code_writer_agent = LlmAgent(
    name = 'code_writer_agent',
    model = 'gemini-flash-latest',
    instruction = load_instructions_file('agents/code_writer/instructions.txt'),
    description = load_instructions_file('agents/code_writer/description.txt'),
    tools = [
        write_to_file,
        gitOps.clone_repository,
        gitOps.get_status,
        gitOps.pull,
        gitOps.create_branch,
        gitOps.checkout_branch,
        gitOps.stage_files,
        gitOps.commit,
        gitOps.push
    ]
)