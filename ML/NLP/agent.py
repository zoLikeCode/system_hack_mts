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
from pydantic import Field
import time
from langchain_core.messages import HumanMessage, SystemMessage


class State(TypedDict):
    messages: Annotated[list, add_messages]
    name: str
    age: int


API_KEY = 'aj3ozp7g0tZaWyvbmP8pHPrNGRgfJN7d'




people_status = {
    "1001": {"status": "свободен"},
    "1002": {"status": "занят"},
    "1003": {"status": "свободен"},
    "1004": {"status": "занят"},
    "1005": {"status": "свободен"}
}




graph_builder = StateGraph(State)
@tool
def get_order_status(employee_id: str = Field(description="Identifier of Employee")) -> str:
    """give the employee status. use when you need get a status of employee"""
    return people_status.get(employee_id, f"Не существует сотрудника")


tools = [get_order_status]
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

tool_node = ToolNode(tools=[get_order_status])
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
graph_builder.set_entry_point("chatbot")

memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)