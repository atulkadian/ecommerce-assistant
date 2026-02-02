from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from app.tools import tools, db_session
from app.config import get_settings
from sqlalchemy.orm import Session

settings = get_settings()


class AgentState(TypedDict):
    """
    State schema for the agent graph. Tracks conversation messages.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]


class ShoppingAssistantAgent:
    def __init__(self, db: Session = None):
        self.db = db
        if self.db:
            db_session.set(self.db)
        
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-2.5-flash-lite",
            temperature=0.7,
            google_api_key=settings.google_api_key,
            convert_system_message_to_human=True
        )
        self.llm_with_tools = self.llm.bind_tools(tools)
        self.graph = self._build_graph()
    
    async def _tool_node(self, state: AgentState):
        """
        Execute tools requested by the agent and return results.
        """
        if self.db:
            db_session.set(self.db)
        
        messages = state["messages"]
        last_message = messages[-1]
        
        tool_messages = []
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                tool = next((t for t in tools if t.name == tool_call["name"]), None)
                if tool:
                    try:
                        result = await tool.ainvoke(tool_call["args"])
                        tool_messages.append(
                            ToolMessage(
                                content=str(result),
                                tool_call_id=tool_call["id"],
                                name=tool_call["name"]
                            )
                        )
                    except Exception as e:
                        tool_messages.append(
                            ToolMessage(
                                content=f"Error executing tool: {str(e)}",
                                tool_call_id=tool_call["id"],
                                name=tool_call["name"]
                            )
                        )
                else:
                    tool_messages.append(
                        ToolMessage(
                            content=f"Tool '{tool_call['name']}' not found",
                            tool_call_id=tool_call["id"],
                            name=tool_call["name"]
                        )
                    )
        
        return {"messages": tool_messages}
        
    def _build_graph(self):
        """
        Build the LangGraph workflow: agent -> tools -> agent (loop until complete).
        """
        workflow = StateGraph(AgentState)
        
        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", self._tool_node)
        workflow.set_entry_point("agent")
        
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {"continue": "tools", "end": END}
        )
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()
    
    async def _call_model(self, state: AgentState):
        """
        Call the LLM with system instructions and conversation history.
        """
        messages = state["messages"]
        
        system_message = HumanMessage(content="""You are a helpful e-commerce shopping assistant. 
You help users discover and learn about products from our store.

Available tools:
- get_products() - Show all available items
- get_product_details(product_id) - Get specific product information
- get_categories() - Show available categories
- get_products_by_category(category) - Filter by category
- search_products(query, category, min_price, max_price) - Search and filter products
- compare_products(product_ids) - Compare multiple products side-by-side
- add_to_cart(product_id, quantity) - Add items to shopping cart
- remove_from_cart(product_id) - Remove items from cart
- view_cart() - Show cart contents and total

Be friendly, helpful, and concise. Format responses nicely for readability. Make sure you use spacious tabular format to show product lists and comparisons.""")
        
        """
        Inject system message if not already present
        """
        if not any(isinstance(m, HumanMessage) and "shopping assistant" in m.content.lower() for m in messages[:1]):
            messages = [system_message] + list(messages)
        
        response = await self.llm_with_tools.ainvoke(messages)
        return {"messages": [response]}
    
    def _should_continue(self, state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"
        return "end"
    
    async def astream(self, message: str, conversation_history: list = None):
        """
        Stream the agent's response by yielding small chunks of text.
        """
        # Set db session in context for tools to use
        if self.db:
            db_session.set(self.db)
        
        messages = []
        
        if conversation_history:
            for msg in conversation_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=message))
        
        final_messages = []
        async for event in self.graph.astream({"messages": messages}):
            for node_name, state_update in event.items():
                if "messages" in state_update:
                    final_messages = state_update["messages"]
        
        if final_messages:
            for msg in reversed(final_messages):
                if isinstance(msg, AIMessage) and msg.content:
                    content = msg.content
                    chunk_size = 5 
                    for i in range(0, len(content), chunk_size):
                        yield content[i:i+chunk_size]
                    break


agent = ShoppingAssistantAgent()
