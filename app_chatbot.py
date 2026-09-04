from fastapi import FastAPI
from fastapi.responses import JSONResponse
from chatbot_model import workflow
from langchain_core.messages import SystemMessage,HumanMessage



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
})
    return {'AI':result['messages'][-1].content}
