from fastapi import FastAPI
from fastapi.responses import JSONResponse
from chatbot_model import workflow,config
from langchain_core.messages import SystemMessage,HumanMessage,ToolMessage



app = FastAPI()

@app.get('/')
def hello():
    return {'message':'you are now in our chatbot named'}
@app.post('/chatbot')
def chatbot(query:str):
    result = workflow.invoke({
    "messages": [
        HumanMessage(content=query)
    ]
},config=config)

    # Walk backwards from the newest message until we hit the
    # HumanMessage we just sent, collecting the name of every tool
    # that was actually called while answering THIS question.
    tools_used = []
    for msg in reversed(result['messages']):
        if isinstance(msg, HumanMessage):
            break
        if isinstance(msg, ToolMessage):
            tools_used.append(msg.name)
    tools_used.reverse()

    return {
        'AI': result['messages'][-1].content,
        'tools_used': tools_used
    }