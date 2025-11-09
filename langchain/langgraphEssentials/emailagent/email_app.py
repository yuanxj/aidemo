"""
Email Agent Application using LangGraph.
This application processes emails through classification, search, and response generation.
"""

from langgraph.graph import END, START, StateGraph
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Literal
from email_meta import EmailAgentState, EmailClassification


# Pydantic model for LLM structured output
class EmailClassificationModel(BaseModel):
    """Email classification result with intent, urgency, topic, and summary."""
    intent: Literal['support', 'sales', 'marketing', 'other'] = Field(
        description="The intent of the email: 'support' for customer support requests, 'sales' for purchase inquiries, 'marketing' for promotional content, 'other' for anything else"
    )
    urgency: Literal['low', 'medium', 'high'] = Field(
        description="The urgency level: 'low' for non-urgent, 'medium' for normal priority, 'high' for urgent matters"
    )
    topic: str = Field(
        description="A brief topic or subject of the email (e.g., 'Product Pricing', 'Technical Issue', 'Account Inquiry')"
    )
    summary: str = Field(
        description="A concise summary of the email content"
    )


def classify_email(state: EmailAgentState) -> EmailAgentState:
    """Classify the incoming email by intent, urgency, topic, and generate a summary using LLM."""
    email_content = state["email_content"]
    sender_email = state["sender_email"]
    
    print(f"Classifying email from {sender_email} using LLM")
    
    # Initialize LLM
    try:
        llm = init_chat_model(
            "openai:gpt-4o-mini",  # Using gpt-4o-mini for cost efficiency, can change to gpt-4 or other models
            temperature=0
        )
        
        # Create structured output model
        structured_llm = llm.with_structured_output(EmailClassificationModel)
        
        # Create classification prompt
        classification_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert email classifier. Analyze the email content and classify it with:
1. Intent: Determine if this is a support request, sales inquiry, marketing communication, or other
2. Urgency: Assess the urgency level (low, medium, high) based on the tone, language, and context
3. Topic: Identify the main topic or subject of the email
4. Summary: Provide a concise summary of the email content

Consider the following:
- Support: Questions, problems, complaints, account issues, technical support
- Sales: Purchase inquiries, pricing questions, product availability, order information
- Marketing: Promotions, newsletters, announcements, updates
- Urgency indicators: Words like 'urgent', 'asap', 'critical', 'emergency' suggest high urgency
- Low urgency: Phrases like 'whenever', 'no rush', 'at your convenience' suggest low urgency"""),
            ("user", """Classify the following email:

From: {sender_email}
Content: {email_content}

Please provide the classification with intent, urgency, topic, and summary.""")
        ])
        
        # Invoke LLM for classification
        chain = classification_prompt | structured_llm
        result = chain.invoke({
            "sender_email": sender_email,
            "email_content": email_content
        })
        
        # Convert Pydantic model to TypedDict format
        classification: EmailClassification = {
            "intent": result.intent,
            "urgency": result.urgency,
            "topic": result.topic,
            "summary": result.summary
        }
        
        print(f"Classification: {classification}")
        
    except Exception as e:
        print(f"Error during LLM classification: {e}")
        print("Falling back to default classification")
        # Fallback to default classification
        classification: EmailClassification = {
            "intent": "support",
            "urgency": "medium",
            "topic": "General Inquiry",
            "summary": f"Email from {sender_email}: {email_content[:100]}..."
        }
    
    return {
        "classification": classification
    }


def search_knowledge_base(state: EmailAgentState) -> EmailAgentState:
    """Search knowledge base for relevant information based on the email classification."""
    classification = state.get("classification")
    
    if not classification:
        return {
            "search_results": []
        }
    
    topic = classification.get("topic", "")
    summary = classification.get("summary", "")
    
    # TODO: Implement actual knowledge base search
    # For now, this is a placeholder implementation
    print(f"Searching knowledge base for topic: {topic}")
    
    # Placeholder search results
    search_results = [
        f"Related article 1 about {topic}",
        f"FAQ item related to {summary[:50]}",
        f"Documentation section for {topic}"
    ]
    
    print(f"Found {len(search_results)} search results")
    
    return {
        "search_results": search_results
    }


def generate_ticket_id(state: EmailAgentState) -> EmailAgentState:
    """Generate a ticket ID for tracking purposes."""
    email_id = state["email_id"]
    sender_email = state["sender_email"]
    
    # TODO: Implement actual ticket ID generation (e.g., from ticketing system)
    # For now, generate a simple ticket ID
    import hashlib
    import time
    
    ticket_data = f"{email_id}_{sender_email}_{int(time.time())}"
    ticket_id = hashlib.md5(ticket_data.encode()).hexdigest()[:8].upper()
    ticket_id = f"TKT-{ticket_id}"
    
    print(f"Generated ticket ID: {ticket_id}")
    
    return {
        "ticket_id": ticket_id
    }


def human_review(state: EmailAgentState) -> EmailAgentState:
    """Handle email that requires human review."""
    email_content = state["email_content"]
    sender_email = state["sender_email"]
    classification = state.get("classification")
    ticket_id = state.get("ticket_id", "")
    
    print(f"⚠️  Email requires human review - Ticket ID: {ticket_id}")
    print(f"From: {sender_email}")
    if classification:
        print(f"Intent: {classification.get('intent')}, Urgency: {classification.get('urgency')}")
        print(f"Topic: {classification.get('topic')}")
        print(f"Summary: {classification.get('summary')}")
    
    # TODO: Implement actual human review workflow
    # This could involve:
    # - Adding to a review queue
    # - Sending notification to support team
    # - Creating a ticket in a ticketing system
    # - Waiting for human input
    
    # For now, mark as pending human review
    draft_response = f"""This email has been flagged for human review.

Ticket ID: {ticket_id}
From: {sender_email}
Reason: {'High urgency' if classification and classification.get('urgency') == 'high' else 'Complex case requiring human attention'}

A support agent will review and respond shortly.

Thank you for your patience."""
    
    print("Email queued for human review")
    
    return {
        "draft_response": draft_response
    }


def should_route_to_human(state: EmailAgentState) -> Literal["human_review", "auto_process"]:
    """Determine if email should be routed to human review or auto-processed."""
    classification = state.get("classification")
    
    if not classification:
        # If no classification, default to auto-process
        return "auto_process"
    
    intent = classification.get("intent", "")
    urgency = classification.get("urgency", "medium")
    
    # Route to human review if:
    # 1. Urgency is high
    # 2. Intent is 'other' (complex cases)
    if urgency == "high" or intent == "other":
        print(f"Routing to human review: urgency={urgency}, intent={intent}")
        return "human_review"
    else:
        print(f"Routing to auto-process: urgency={urgency}, intent={intent}")
        return "auto_process"


def draft_response(state: EmailAgentState) -> EmailAgentState:
    """Draft a response email based on classification and search results."""
    email_content = state["email_content"]
    sender_email = state["sender_email"]
    classification = state.get("classification")
    search_results = state.get("search_results", [])
    ticket_id = state.get("ticket_id", "")
    
    # TODO: Implement actual response generation using LLM
    # For now, this is a placeholder implementation
    print(f"Drafting response for ticket {ticket_id}")
    
    # Placeholder response generation
    intent = classification.get("intent", "support") if classification else "support"
    urgency = classification.get("urgency", "medium") if classification else "medium"
    
    draft = f"""Dear {sender_email.split('@')[0]},

Thank you for contacting us regarding your inquiry.

Ticket ID: {ticket_id}
Intent: {intent}
Urgency: {urgency}

"""
    
    if search_results:
        draft += "Based on our knowledge base, here are some relevant resources:\n"
        for result in search_results[:3]:  # Include top 3 results
            draft += f"- {result}\n"
        draft += "\n"
    
    draft += """We will get back to you shortly.

Best regards,
Support Team
"""
    
    print(f"Drafted response: {draft[:100]}...")
    
    return {
        "draft_response": draft
    }


def create_email_agent_graph():
    """Create and compile the email agent graph."""
    # Create the graph
    builder = StateGraph(EmailAgentState)
    
    # Add nodes
    builder.add_node("classify", classify_email)
    builder.add_node("generate_ticket", generate_ticket_id)
    builder.add_node("human_review", human_review)
    builder.add_node("search", search_knowledge_base)
    builder.add_node("draft", draft_response)
    
    # Define the workflow
    builder.add_edge(START, "classify")
    builder.add_edge("classify", "generate_ticket")
    
    # Add conditional edge after ticket generation
    # Route to human review if urgency is high or intent is 'other' (complex)
    # Otherwise, route to auto-process (search -> draft)
    builder.add_conditional_edges(
        "generate_ticket",
        should_route_to_human,
        {
            "human_review": "human_review",
            "auto_process": "search"
        }
    )
    
    # Human review path
    builder.add_edge("human_review", END)
    
    # Auto-process path
    builder.add_edge("search", "draft")
    builder.add_edge("draft", END)
    
    # Compile the graph
    graph = builder.compile()
    
    return graph


def main():
    """Main function to run the email agent."""
    # Create the graph
    graph = create_email_agent_graph()
    
    # Example initial state
    initial_state: EmailAgentState = {
        "email_content": "Hello, I have a question about your product pricing. Can you please provide more information? This is urgent!",
        "sender_email": "customer@example.com",
        "email_id": "email_001",
        "classification": None,
        "ticket_id": "",
        "search_results": None,
        "draft_response": None
    }
    
    print("=" * 50)
    print("Email Agent - Processing Email")
    print("=" * 50)
    print(f"From: {initial_state['sender_email']}")
    print(f"Email ID: {initial_state['email_id']}")
    print(f"Content: {initial_state['email_content']}")
    print("=" * 50)
    print()
    
    # Run the graph
    result = graph.invoke(initial_state)
    
    print()
    print("=" * 50)
    print("Processing Complete")
    print("=" * 50)
    print(f"Ticket ID: {result.get('ticket_id')}")
    if result.get('classification'):
        print(f"Intent: {result['classification']['intent']}")
        print(f"Urgency: {result['classification']['urgency']}")
        print(f"Topic: {result['classification']['topic']}")
        
        # Check if email was routed to human review
        urgency = result['classification']['urgency']
        intent = result['classification']['intent']
        if urgency == "high" or intent == "other":
            print("⚠️  Status: Routed to Human Review")
        else:
            print("✓ Status: Auto-processed")
    
    search_results_count = len(result.get('search_results', []) or [])
    if search_results_count > 0:
        print(f"Search Results: {search_results_count} items")
    print()
    if result.get('draft_response'):
        print("Draft Response:")
        print("-" * 50)
        print(result['draft_response'])
        print("-" * 50)


if __name__ == "__main__":
    main()

