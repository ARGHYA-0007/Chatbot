from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from chatbot_model import workflow
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid

import database

app = FastAPI()

# The frontend (index.html) is opened directly in the browser / served
# from a different origin than the API, so it needs CORS enabled.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

database.init_conversations_table()


def _extract_text(content):
    """AIMessage.content can be a plain string or a list of content
    blocks (e.g. [{'type': 'text', 'text': '...'}]) depending on the
    model. Handle both so the API never crashes on the shape."""
    if isinstance(content, list):
        return "".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        )
    return content or ""


@app.get('/')
def hello():
    return {'message': 'you are now in our chatbot named'}


@app.post('/new-chat')
def new_chat():
    thread_id = str(uuid.uuid4())
    database.create_conversation(thread_id)
    return {'thread_id': thread_id}


@app.get('/conversations')
def get_conversations():
    """List every conversation so the frontend can render the sidebar."""
    return database.list_conversations()


@app.get('/chatbot/{thread_id}/history')
def get_history(thread_id: str):
    """Rehydrate a past conversation from the langgraph checkpoint."""
    config = {"configurable": {"thread_id": thread_id}}
    state = workflow.get_state(config)

    if not state or not state.values.get('messages'):
        return {'messages': []}

    messages = []
    for msg in state.values['messages']:
        if isinstance(msg, HumanMessage):
            messages.append({'role': 'user', 'content': _extract_text(msg.content)})
        elif isinstance(msg, AIMessage):
            text = _extract_text(msg.content)
            if text:
                messages.append({'role': 'ai', 'content': text})
        # ToolMessages are left out of the displayed transcript on purpose

    return {'messages': messages}


@app.post('/chatbot')
def chatbot(query: str, thread_id: str):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = workflow.invoke(
        {
            "messages": [
                HumanMessage(content=query)
            ]
        },
        config=config
    )

    tools_used = []

    for msg in reversed(result['messages']):
        if isinstance(msg, HumanMessage):
            break

        if isinstance(msg, ToolMessage):
            tools_used.append(msg.name)

    tools_used.reverse()

    database.maybe_set_title(thread_id, query)

    return {
        'AI': _extract_text(result['messages'][-1].content),
        'tools_used': tools_used,
        'thread_id': thread_id
    }