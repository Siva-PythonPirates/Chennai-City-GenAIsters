from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent.tools import *

from utility.config import configurations

APP_NAME = "bargain"
AGENT_MODEL = configurations["agent"]["model"]

session_merchant = InMemorySessionService()
session_customer = InMemorySessionService()

agent_customer = Agent(
    model=AGENT_MODEL,
    name="customer_agent",
    description="A agent that acts in behalf of a customer",
    instruction="""
        You act in behalf of a customer buying a product
        You will be given a item to buy
        first get your balance using your 'get_balance' tool
        You must argue with the merchant to buy item and reach an equillibrium state
        use the corresponding tools to do the actions
        your output are texts like chatting
        send the output as 'break' if the bargain failed, or else the merchant sold the product
    """,
    tools=[get_balance, buy_item_from_seller],
)
agent_merchant = Agent(
    model=AGENT_MODEL,
    name="merchant_agent",
    description="A agent that acts in behalf of a merchant",
    instruction="""
        You act in behalf of a merchant selling a product
        You will be enquired a certain item from customer
        You must argue with the customer to sell item and reach an equillibrium state
        use the corresponding tools to do the actions
        your output are texts like chatting
        send a google waller passes object like this after the buying is made
        send the output as 'break' if the bargain failed
    """,
    tools=[get_inventory],
)


runner_merchant = Runner(
    agent=agent_merchant,
    session_service=session_merchant,
    app_name=APP_NAME,
)
runner_customer = Runner(
    agent=agent_customer,
    session_service=session_customer,
    app_name=APP_NAME,
)


async def asset_session_existence(runner, session_id: str | None, user_id: str):
    if session_id is None:
        return await runner.session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
        )
    session = await runner.session_service.get_session(
        session_id=session_id, app_name=APP_NAME, user_id=user_id
    )
    if session:
        return session
    else:
        return await runner.session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
        )


async def call_agent_async(content, runner, user_id, session_id):
    final_response_text = "Agent did not produce a final response."
    query = types.Content(role="user", parts=content)

    session = await asset_session_existence(runner, session_id, user_id)
    async for event in runner.run_async(
        user_id=user_id, session_id=session.id, new_message=query
    ):
        print(
            f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}"
        )
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            elif (
                event.actions and event.actions.escalate
            ):  # Handle potential errors/escalations
                final_response_text = (
                    f"Agent escalated: {event.error_message or 'No specific message.'}"
                )
            break  # Stop processing events once the final response is found
    return final_response_text


async def start_action(cust_id, seller_id, product_id):
    parts_list = [
        types.Part.from_text(
            text=f"this is message from {cust_id} to get {product_id} for the seller {seller_id}"
        )
    ]
    chatHistory = (
        "customer::"
        + f"this is message from {cust_id} to get {product_id} for the seller {seller_id}"
    )
    output = await call_agent_async(parts_list, runner_merchant, "merch1", "ses1")
    turn = 0
    output_list = [{"user_type": "customer", "response": output}]
    while output != "break":
        if turn == 0:
            parts_list = [
                types.Part.from_text(text="below is chat history:" + chatHistory),
                types.Part.from_text(
                    text=f"this is message from {seller_id} to sell {product_id} for the customer {cust_id}:{output}"
                ),
            ]
            output = await call_agent_async(
                parts_list, runner_customer, "cust1", "ses1"
            )
            output_list.append({"user_type": "seller", "response": output})
            chatHistory += "seller:" + output
        else:
            parts_list = [
                types.Part.from_text(text="below is chat history:" + chatHistory),
                types.Part.from_text(
                    text=f"this is message from {cust_id} to buy {product_id} from the seller {seller_id}:{output}"
                ),
            ]
            output = await call_agent_async(
                parts_list, runner_customer, "cust1", "ses1"
            )
            output_list.append({"user_type": "customer", "response": output})
            chatHistory += "customer:" + output

    return output_list
