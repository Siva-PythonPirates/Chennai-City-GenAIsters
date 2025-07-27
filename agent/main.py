from google.adk.sessions import DatabaseSessionService, InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

from services.gcloud_service import initialize_vertex_ai, initialize_ai_platform

from agent.agents import root_agent, scheduler_agent, pass_agent

from database.remainder import get_user_remainders

from typing import List
import base64

from services.database_service import get_session_service_db_url
import json


APP_NAME = "raseed"


def init():
    initialize_vertex_ai()
    initialize_ai_platform()


def get_runner(agent, session_service) -> Runner:
    return Runner(
        agent=agent,
        session_service=session_service,
        app_name=APP_NAME,
    )


db_session_service = DatabaseSessionService("sqlite:///data/ad_sessions.db")
runner1 = get_runner(root_agent, db_session_service)
runner2 = get_runner(pass_agent, db_session_service)

im_session_service = DatabaseSessionService("sqlite:///data/adksessions.db")
schedule_runner = get_runner(scheduler_agent, im_session_service)


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
        print("hello")
        return await runner.session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
        )


async def call_agent_async(content, user_id, session_id):
    """Sends a query to the agent and prints the final response."""

    final_response_text = "Agent did not produce a final response."
    query = types.Content(role="user", parts=content)

    session = await asset_session_existence(runner1, session_id, user_id)
    content_added = "below is the previous history of call between the agent, that contains the required information"
    async for event in runner1.run_async(
        user_id=user_id, session_id=session.id, new_message=query
    ):
        content_added += f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}"

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

    content = content + [types.Part.from_text(text=content_added)]
    query = types.Content(role="user", parts=content)
    session = await asset_session_existence(runner2, session_id, user_id)

    query = types.Content(role="user", parts=content)
    async for event in runner2.run_async(
        user_id=user_id, session_id=session.id, new_message=query
    ):
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


def getAsJSON(response):
    response = response.strip().replace("```json", "").replace("```", "").strip()
    print("kkkk", response)
    return json.loads(response)


async def call_agent_chat(current_query: List[dict], user_id: str, session_id: str):
    parts_list = [types.Part.from_text(text="this is a chat message from user")]
    for query in current_query:
        if query["message_type"] == "text":
            parts_list.append(types.Part.from_text(text=query["content"]))
        elif query["message_type"] == "img":
            try:
                parts_list.append(
                    types.Part.from_bytes(
                        data=base64.b64decode(query["content"]), mime_type="image/png"
                    )
                )
            except Exception as e:
                pass
    response = await call_agent_async(parts_list, user_id, session_id)
    return getAsJSON(response)


async def call_agent_scheduler(user_id: str):
    """Call the agent scheduler."""
    session = await asset_session_existence("tz1", user_id)
    remainders = await get_user_remainders(session.id)
    if not remainders:
        return "No chat history found."
    parts_list = [
        types.Part.from_text(
            text="this is a remainder meassage from scheduler, below are all the remainders for the user"
        )
    ]
    for reminder in remainders:
        parts_list.append(types.Part.from_text(text=reminder["remainder_data"]))
    content = types.Content(role="user", parts=parts_list)
    return await call_agent_async(schedule_runner, content, user_id, session.id)
