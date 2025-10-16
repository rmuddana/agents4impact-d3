import os
import logging

from dotenv import load_dotenv
# from google.adk.agents import SequentialAgent
from google.adk.agents.llm_agent import Agent
from google.adk.tools import ToolContext
from google.adk.tools.bigquery import BigQueryToolset, BigQueryCredentialsConfig
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from google.genai import types
import google.auth

load_dotenv()

model_name = os.getenv("MODEL")
print(model_name)

application_default_credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(
    credentials=application_default_credentials
)

# Define a tool configuration to block any write operations
tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)


# Instantiate a BigQuery toolset
bigquery_toolset = BigQueryToolset(
    credentials_config=credentials_config,
    bigquery_tool_config=tool_config,
    tool_filter=[
        'qwiklabs-gcp-04-c46d364bcec5.sanjose_311',
        'bigquery-public-data.san_francisco_311'
    ]
)

def append_to_state(
    tool_context: ToolContext, field: str, response: str
) -> dict[str, str]:
    """Append new output to an existing state key.

    Args:
        field (str): a field name to append to
        response (str): a string to append to the field

    Returns:
        dict[str, str]: {"status": "success"}
    """
    existing_state = tool_context.state.get(field, [])
    tool_context.state[field] = existing_state + [response]
    logging.info(f"[Added to {field}] {response}")
    return {"status": "success"}


data_query_agent = Agent(
    name="data_query_agent",
    description="Queries 311 data for a specific concern type.",
    instruction="""
    INSTRUCTIONS:
    Your goal is to query 311 data for concern types matching the user's PROMPT: { PROMPT? }
    - use the bigquery_toolset to query the 311 data
    - Use the 'append_to_state' tool to write your query results to the field '311_query_results'.
    """,
    tools=[bigquery_toolset, append_to_state],
)

# workflow_agent = SequentialAgent(
#     name="311_workflow_agent",
#     description="End-to-end workflow for querying 311 data, correlating with census data, generating insights, and visualizing results.",
#     sub_agents=[
#         data_query_agent,
#         insight_generator_agent,
#         mapper_agent,
#     ],
# )

root_agent = Agent(
    name="greeter",
    model=model_name,
    description="Guides user in discovering insights from 311 data.",
    instruction="""
    - Let the user know that you can help them recognize patterns and insights from 311 data across San Francisco.
    - Ask them if they have a specific concern type in mind or if they want to explore general insights.
    - When they respond, use the 'append_to_state' tool to store the user's response
      in the 'concern_type' state key and transfer to the 'data_query_agent' agent
    """,
    generate_content_config=types.GenerateContentConfig(
        temperature=0,
    ),
    tools=[append_to_state],
    # sub_agents=[workflow_agent],
    sub_agents=[data_query_agent],
)