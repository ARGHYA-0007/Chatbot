import csv
import os
from typing import Literal, Optional, TypedDict
from langchain_core.messages import SystemMessage,HumanMessage
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END,START
from langgraph.types import interrupt, Command
from typing import Optional
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver

llm = ChatOllama(model='qwen2.5:1.5b')
class ChatState(TypedDict):
    query:str
    answer:str
def ask_query(state:ChatState):
    query = input()
    return {'query':query}
def chat(state:ChatState):
    query = state['query']
    result = llm.invoke(query).content
    return {'answer':result}
graph = StateGraph(ChatState)
graph.add_node('chat',chat)
graph.add_edge(START,'chat')
graph.add_edge('chat',END)
workflow = graph.compile()
while True:
    query = input('USER:')
    result = workflow.invoke({'query':query})
    print('AI:',result['answer'])
