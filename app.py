from fastapi import FastAPI
from langchain_ollama import ChatOllama
from fastapi.responses import JSONResponse
from model.intro_model import intro_workflow,llm

app = FastAPI()
MODEL_VERSION = '1.0.0'

@app.get('/')
def home():
    return {'message':'this is intro model'}
@app.get('/health')
def health_check():
    return {
        'status':'ok',
        'model version': MODEL_VERSION,
        'model loaded':llm is not None
    }
@app.post('/predicting')
def predict(input_x:str):
    config = {"configurable": {"thread_id": "1"}}
    try:
        result = intro_workflow.invoke({ "intro":input_x},config = config)
        return result
    except Exception as e:
        return JSONResponse(status_code=500,content=str(e))