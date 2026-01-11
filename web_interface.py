import gradio as gr
from agent import query_agent

def respond(message, history):
    """
    Process user message and return agent response.
    
    Args:
        message: User's input message
        history: Chat history
        
    Returns:
        The agent's response string
    """
    try:
        response = query_agent(message)
        return response
    except Exception as e:
        return f"Error: {str(e)}"

# Example queries for users to try
examples = [
    "What happened with the debt ceiling negotiations in 2023?",
    "What are the key issues in the 2024 presidential primary campaigns?",
    "Explain the recent Supreme Court decision on affirmative action in college admissions.",
    "What's the current debate around immigration policy?"
]

# Create Gradio ChatInterface (simpler API that handles message format automatically)
demo = gr.ChatInterface(
    fn=respond,
    title="🏛️ Political Intelligence Agent",
    description="""An AI chatbot that discusses political events with sophisticated reasoning, strict neutrality, 
    and multi-perspective analysis. Ask questions about political events, policies, or debates.
    
    **Note**: This agent specializes in political topics. Non-political queries will be redirected.""",
    examples=examples,
    theme=gr.themes.Soft(),
)

if __name__ == "__main__":
    print("\n🚀 Starting Political Intelligence Agent Web Interface...")
    print("📡 The interface will open in your browser automatically.")
    print("🛑 Press Ctrl+C to stop the server.\n")
    demo.launch(share=False, server_name="127.0.0.1", server_port=7860)
