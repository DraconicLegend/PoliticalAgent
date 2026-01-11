import gradio as gr
from agent import query_agent

def chat_interface(message, history):
    """
    Process user message and return agent response.
    
    Args:
        message: User's input message
        history: Chat history (list of [user_msg, bot_msg] pairs)
        
    Returns:
        Updated chat history
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

# Create Gradio interface
with gr.Blocks(title="Political Intelligence Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🏛️ Political Intelligence Agent
        
        An AI chatbot that discusses political events with sophisticated reasoning, strict neutrality, 
        and multi-perspective analysis. Ask questions about political events, policies, or debates.
        
        **Note**: This agent specializes in political topics. Non-political queries will be redirected.
        """
    )
    
    chatbot = gr.Chatbot(
        label="Conversation",
        height=500,
        show_label=True,
        avatar_images=(None, "🤖")
    )
    
    with gr.Row():
        msg = gr.Textbox(
            label="Your Query",
            placeholder="Ask about political events, policies, or debates...",
            lines=2,
            scale=4
        )
        submit_btn = gr.Button("Submit", variant="primary", scale=1)
    
    with gr.Row():
        clear_btn = gr.Button("Clear Conversation", variant="secondary")
    
    gr.Markdown("### Example Queries")
    gr.Examples(
        examples=examples,
        inputs=msg,
        label="Try these questions:"
    )
    
    gr.Markdown(
        """
        ---
        **How it works**: The agent uses a multi-step reasoning process:
        1. **Router**: Determines if the query is political
        2. **Planner**: Creates a multi-perspective search strategy
        3. **Researcher**: Gathers information from multiple sources
        4. **Synthesis**: Creates a balanced analysis
        5. **Neutralizer**: Checks for bias
        6. **Fact Checker**: Validates claims against sources
        """
    )
    
    # Event handlers
    def user_submit(user_message, history):
        return "", history + [[user_message, None]]
    
    def bot_respond(history):
        user_message = history[-1][0]
        bot_response = chat_interface(user_message, history[:-1])
        history[-1][1] = bot_response
        return history
    
    msg.submit(user_submit, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot_respond, chatbot, chatbot
    )
    submit_btn.click(user_submit, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot_respond, chatbot, chatbot
    )
    clear_btn.click(lambda: None, None, chatbot, queue=False)

if __name__ == "__main__":
    print("\n🚀 Starting Political Intelligence Agent Web Interface...")
    print("📡 The interface will open in your browser automatically.")
    print("🛑 Press Ctrl+C to stop the server.\n")
    demo.launch(share=False, server_name="127.0.0.1", server_port=7860)
