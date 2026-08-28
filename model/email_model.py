import csv
import os
from typing import Literal, Optional, TypedDict
from langchain_core.messages import SystemMessage,HumanMessage
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END,START
from langgraph.types import interrupt, Command
from typing import Optional
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver

# 1. Compile the graph with memory
memory = MemorySaver()
from dotenv import load_dotenv
# load_dotenv()

llm3b = ChatOllama(model = 'qwen2.5:3b')
llm7b = ChatOllama(model='qwen2.5:7b')
# llm70b = ChatGroq(model='llama-3.3-70b-versatile')

class EmailState(TypedDict):
    email:str
    to_reply:str
    drafted_reply:str
    instruction:str
    feedback:str
    hitl:str
    sent:str
class yes_no(BaseModel):
    yes_no:Literal['yes','no']=Field(description='''You are an email classification system.

Analyze the given email and return only one word:
YES — if the email is legitimate, from a human, and requires a reply.
NO — if the email is spam, promotional, automated, informational, or does not require a reply.

CRITICAL RULE: If the email contains phrases like "automated message", "do not reply", "no-reply", or "unmonitored", you MUST output NO.

Your output must be exactly:
YES
or
NO''')
yes_no_model = llm7b.with_structured_output(yes_no)
def reply_or_not(state:EmailState):
    email = state['email']
    answer = yes_no_model.invoke(f'{email}')
    return {'to_reply':answer.yes_no}
def writter_router(state:EmailState):
    reply_or_not = state['to_reply']
    if reply_or_not.lower() == 'yes':
        return 'yes'
    if reply_or_not.lower()=='no':
        return 'no'
def Email_drafter(state:EmailState):
    email=state['email']
    prompt = [SystemMessage(
    content=f"""
You are an AI email assistant.

Your task is to reply to the email provided below.

Rules:
- Understand the sender's intent before replying.
- Give a helpful, polite, and professional response.
- Directly answer any questions asked in the email.
- Keep the reply concise and natural.
- Do not invent information that is not present in the email.
- If clarification is needed, ask a clear and relevant question.
- Do not include unnecessary explanations.
- Return ONLY the email reply.
- Do not include a subject line or labels such as "Reply:".
"""
),HumanMessage(content=f'answer this mail {email} according to given rules')]
    reply = llm7b.invoke(prompt).content
    return {'drafted_reply':reply}

def human_review(state: EmailState):
    drafted_email = state['drafted_reply']
    instruction = interrupt(f'this is drafter reply:\n{drafted_email}\ntell us should stop,send,improve')
    return {'instruction':instruction}
def human_router(state:EmailState):
    human_ans = state['instruction']
    if human_ans.lower() =='send':
        return 'send'
    elif human_ans.lower() == 'stop':
        return "stop"
    else:
        return 'improve'
def improve(state:EmailState):
    feedback = input('tell us what you want to improve')
    return {'feedback':feedback}
def send(state:EmailState):
    print('sending mail.......')
    return {'sent':'sent'}
graph = StateGraph(EmailState)


graph.add_node('reply_or_not',reply_or_not)
graph.add_node('drafter',Email_drafter)
graph.add_node('ask_human',human_review)
graph.add_node('improve',improve)
graph.add_node('send',send)

graph.add_edge(START,'reply_or_not')
graph.add_conditional_edges('reply_or_not',writter_router,{'yes':'drafter','no':END})
graph.add_edge('drafter','ask_human')
graph.add_conditional_edges('ask_human',human_router,{'send':'send','stop':END,'improve':'improve'})
graph.add_edge('improve','drafter')

email_workflow = graph.compile(checkpointer=memory)