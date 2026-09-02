from fastapi import FastAPI
from fastapi.responses import JSONResponse
from model.chatbot_model import workflow


app = FastAPI()

@app.get('/')
def hello():
    return {'message':'you are now in our chatbot named'}
@app.post('/chatbot')
def chatbot(query:str):
    result = workflow.invoke({'query':query})
    return {'AI':result['answer']}
