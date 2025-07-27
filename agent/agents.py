from google.adk.agents import Agent, SequentialAgent
from google.adk.runners import Runner

from agent.prompts import prompts
from agent.tools import *

from utility.config import configurations


AGENT_MODEL = configurations["agent"]["model"]

# Define the agents as before
output_agent = Agent(
    model=AGENT_MODEL,
    name="output_agent",
    description=prompts["output_agent"]["description"],
    instruction=prompts["output_agent"]["instruction"],
    tools=[],
)

add_relevency_agent = Agent(
    model=AGENT_MODEL,
    name="add_relevency_agent",
    description=prompts["add_relevency_agent"]["description"],
    instruction=prompts["add_relevency_agent"]["instruction"],
    tools=[put_relevent_data],
    sub_agents=[output_agent],
)

pass_agent = Agent(
    model=AGENT_MODEL,
    name="pass_agent",
    description=prompts["pass_agent"]["description"],
    instruction=prompts["pass_agent"]["instruction"],
    tools=[
        insert_pass_object_string,
        update_pass_object_string,
    ],
    output_key="passes_generated",
    sub_agents=[add_relevency_agent],
)


get_relevency_agent = Agent(
    model=AGENT_MODEL,
    name="get_relevency_agent",
    description=prompts["get_relevency_agent"]["description"],
    instruction=prompts["get_relevency_agent"]["instruction"],
    tools=[get_relevant_context],
    sub_agents=[],
)

extraction_agent = Agent(
    model=AGENT_MODEL,
    name="extraction_agent",
    description=prompts["extraction_agent"]["description"],
    instruction=prompts["extraction_agent"]["instruction"],
    tools=[],
    output_key="extracted_content",
    sub_agents=[get_relevency_agent],
    # tools=[add_reciept_data, delete_reciept_data],
)

root_agent = extraction_agent


# relevancy_agent = Agent(
#     model=AGENT_MODEL,
#     name="relevancy_agent",
#     description="gets relevancy context for the reciept",
#     instruction="gets the relevent context for the user and go backs to the parent agent 'root_agent' using the chat message and reciept as the query",
#     tools=[get_relevant_context],
# )

# root_agent = Agent(
#     model=AGENT_MODEL,
#     name="root_agent",
#     description="a reciept management system",
#     instruction="""
#         You are a reciept management system for google wallet
#         You are to do the following processes with the help of tools in the following sequence
#             1) Extract information from the reciept image if there are any images present
#                 the information you need to extraction from the reciept images includes:
#                     1. date of the reciept (current date and time if not available)
#                     2. total amount of the reciept (if not available, use 0)
#                     3. items in the reciept must include
#                         Name(if not available use MISC\{n\}, n denoting the quantity number)
#                         Qantity(if not available, use 1),
#                         per item cost,
#                     4. vendor name (if not available, use None)
#                     5. other meaningful informations that you can extract from the reciept image in any format at is understandable by generatice AIs.
#                     6. The tax applied to all the items aggregated cost. If unavailable, use 0
#             2) get other relevant information do you have about this purchase by delegating to the 'relevancy_agent' sub-agent.
#             3) if there is any text from the user, you can answer the question using the information available in the reciept or the context provided by the relevency agent


#     """,
#     sub_agents=[relevancy_agent],
#     tools=[put_relevent_data],
# )

scheduler_agent = Agent(
    name="scheduler_agent",
    model=AGENT_MODEL,
    description=prompts["scheduler_agent"]["description"],
    instruction=prompts["scheduler_agent"]["instruction"],
    sub_agents=[],
)

# root_agent = Agent(
#     name="extract_agent",
#     modal=AGENT_MODEL,

# )

# 4) if the user asks you to set any remainders like remind me of the total expense every week,
#     use the remainder tools to add these data
#     if the user request to delete any of these then, delete the remainder
# 5) Do action related to passes of google wallet
#     if there is a new reciept that is extracted, add passes if tools available
# 6) check if there is any question that requires context of some other information like reciept, pass,remainder user info.
#     these are the relevent details that must be noted down
#     5.1) if any reciept data is added to the DB, add that data with the corresponding reciept ID  with current timestamp
#     5.2) if any passes object is added or updated to the database, add the data with the corresponding pass ID with current timestamp
#     5.3) if any remainder is added to the DB, add the data with corresponding remainder ID with current timestamp
# 7) generate output in the following format
#     the output to be generated is a json, the sample is given below
#     {
#         "isReleventContextAdded":<wheather new data is added to the context>
#         "isRecieptExtracted": <wheather extraction agent extracted any reciept and inserted it into the database>,
#         "extractedRecieptID": <id of the reciept extracted and stored in the database by the extraction agent, null if not done>,
#         "chatResponse": <response to the user question by the chat agent> ,
#     }
