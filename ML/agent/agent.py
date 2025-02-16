from typing import Annotated

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from langchain_core.tools import tool
from pydantic import Field, BaseModel
import time
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os
import json



load_dotenv('.env')
API_KEY = os.getenv('API_KEY')
#API_KEY = 'aj3ozp7g0tZaWyvbmP8pHPrNGRgfJN7d'

class State(TypedDict):
    messages: Annotated[list, add_messages]
    name: str
    age: int


graph_builder = StateGraph(State)


def read_json_file(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


def write_json_file(file_path: str, data: dict) -> None:
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)



status_pass = read_json_file("agent/json/status_pass.json")
plumbers_requests = read_json_file('agent/json/plumbers_requests.json')

class Employee(BaseModel):
    full_name: str = Field(description="full name of the person who needs to be issued a pass")
    tenant_name: str = Field(description="The name of the person who orders the service")

class ApartmentRequest(BaseModel):
    apartment_number: str = Field(description="the apartment number where the service is ordered")
    resident_name: str = Field(description="name of the customer of the service")
    time_of_visit: str = Field(description="time to visit")



@tool(args_schema=Employee)
def add_employee_pass(full_name: str, tenant_name: str) -> str:
    """It is used when it is necessary to provide a pass to a person, it is recorded in the name of the customer."""
    employee_id = full_name.lower().replace(" ", "_")  
    status_pass[employee_id] = tenant_name

    write_json_file("./json/status_pass.json", status_pass)    
    return f"Пропуск для {full_name} успешно добавлен и истечёт через час"

@tool(args_schema=ApartmentRequest)
def call_plumber(apartment_number: str, resident_name: str, time_of_visit: str) -> str:
    """Adds a request to call a plumber, including information about the apartment and the time of the visit."""
    request_id = f"{apartment_number}_{resident_name.lower().replace(' ', '_')}"

    plumbers_requests[request_id] = {
        "apartment_number":apartment_number,
        "resident_name":resident_name,
        "time_of_visit": time_of_visit
    }
    

    write_json_file('./json/plumbers_requests.json', plumbers_requests)
    return f"Запрос на вызов сантехника для квартиры {apartment_number} принят. Время визита: {time_of_visit}"



tools = [add_employee_pass, call_plumber]
llm = ChatMistralAI(api_key = API_KEY, model="mistral-large-latest", temperature=0)
llm_with_tools = llm.bind_tools(tools)


message = [
    ("system", "Отвечай только на русском языке. Ты являешься **ДОМОФОНОМ** и всегда общаешься уважительно и очень коротко, и отвечаешь только на вопросы человека про себя, или тот функцианал что у тебя есть"),
    ("system", "Человека зовут **{name}** и ему **{age}**"),
    ("human", "{message}")
]
promt = ChatPromptTemplate(message)


chain = promt | llm_with_tools




def chatbot(state: State) -> State:
    """Обрабатывает сообщения и обновляет состояние."""
    time.sleep(1)

    res = chain.invoke({
        "message": state['messages'],
        "name": state['name'],
        "age": state['age']
    })

    if "tool_calls" in res.additional_kwargs:
        return {
            "messages": res,
            "name": state['name'],
            "age": state['age']
        }

    return {
        "messages": {"role": "ai", "content": res.content},
        "name": state['name'],
        "age": state['age']
    }






graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=[add_employee_pass, call_plumber])
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
graph_builder.set_entry_point("chatbot")

memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)