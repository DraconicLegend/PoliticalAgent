# Political Intelligence Agent

A specialized AI chatbot agent designed to discuss political events with sophisticated reasoning, strict neutrality, bias mitigation, and multi-perspective analysis. This agent uses a graph-based architecture (LangGraph) to research, synthesize, neutralize, and fact-check information before presenting it to the user.

## Features

-   **Multi-Step Reasoning**: Decomposes complex queries into search plans.
-   **Bias Mitigation**: "Neutralizer" node detects and corrects partisan language.
-   **Hallucination Prevention**: "Fact Checker" node validates claims against search results.
-   **External Information**: Integrates with Tavily Search API for real-time data.
-   **Local LLM Privacy**: Uses Ollama with Llama 3.1 for local inference.

## Prerequisites

Before running the agent, ensure you have the following installed:

1.  **Python 3.9+**
2.  **Ollama**: Download and install from [ollama.com](https://ollama.com/).
3.  **Llama 3.1 Model**: Pull the model using the command line:
    ```bash
    ollama pull llama3.1
    ```
4.  **Tavily API Key**: Get a free API key from [app.tavily.com](https://app.tavily.com/).

## Installation

1.  **Clone the repository** (or download the files):
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # macOS/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r req.txt
    ```

## Configuration

1.  Create a `.env` file in the project root.
2.  Add your Tavily API key to the `.env` file:
    ```env
    TAVILY_API_KEY="your_tavily_api_key_here"
    ```

## Usage

### Option 1: Web Interface (Recommended)

1.  **Run the web interface**:
    ```bash
    python web_interface.py
    ```

2.  **Access the interface**:
    -   The Gradio interface will automatically open in your browser at `http://127.0.0.1:7860`.
    -   If it doesn't open automatically, navigate to that URL manually.

3.  **Interact with the agent**:
    -   Type your political query in the text box.
    -   Click "Submit" or press Enter.
    -   View the response in the chat interface.
    -   Use "Clear Conversation" to start fresh.
    -   Try the example queries provided.

### Option 2: Command Line Interface

1.  **Run the agent**:
    ```bash
    python agent.py
    ```

2.  **Interact with the agent**:
    -   The agent will start up and visualize its graph (saving it as `agent_graph.png`).
    -   Type your political query into the console prompt: `Query:`.
    -   Example Query: *"What are the key arguments for and against the recent debt ceiling deal?"*
    -   Type `exit` or `quit` to stop the agent.

## Project Structure

-   `agent.py`: Main entry point and graph definition (Router -> Planner -> Researcher -> Synthesis -> Neutralizer -> Fact Checker).
-   `req.txt`: Python package dependencies.
-   `directions.md`: Project requirements and directions.
-   `agent_graph.png`: Generated visualization of the agent's workflow (created after first run).
