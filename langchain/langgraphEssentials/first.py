from IPython.display import Image, display
import operator
from typing import Annotated, List, Literal, TypedDict
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

class State(TypedDict):
    nList: List[str]

def node_a(state: State) -> State:
    print(f"node a is receiving {state['nList']}")
    note = "Hello World from Node a"
    return(State(nList = [note]))

if __name__ == "__main__":
    builder = StateGraph(State)
    builder.add_node("a", node_a)
    builder.add_edge(START, "a")
    builder.add_edge("a", END)
    graph = builder.compile()
    image =  Image(graph.get_graph().draw_mermaid_png())
    with open("output/output.png", "wb") as f:
        f.write(image.data)
    initial_state = State(
        nList = ["Hello Node a, how are you?"]
    )
    graph.invoke(initial_state)