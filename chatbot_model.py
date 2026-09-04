import csv
import os
from typing import Literal, Optional, TypedDict,Annotated
from langchain_core.messages import SystemMessage,HumanMessage
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END,START
from langgraph.types import interrupt, Command
from typing import Optional
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages, BaseMessage

llm = ChatOllama(model='qwen2.5:1.5b')
memory = MemorySaver()
config = {
    "configurable": {
        "thread_id": "user1"
    }
}
class ChatState(TypedDict):
    messages:Annotated[list[BaseMessage], add_messages]
def chat(state: ChatState):
    result = llm.invoke(state["messages"])

    return {"messages": [result]}
graph = StateGraph(ChatState)
graph.add_node('chat',chat)
graph.add_edge(START,'chat')
graph.add_edge('chat',END)
workflow = graph.compile(checkpointer=memory)
# while True:
#     query = input('USER:')
#     result = workflow.invoke({
#     "messages": [HumanMessage(content=query)]},config=config)
#     print('AI',result['messages'][-1].content)
