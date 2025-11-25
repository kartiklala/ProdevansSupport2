from langchain.agents import initialize_agent, AgentType
from app.tools.check_user_exists import check_user_exists

def get_agent():
    tools = [check_user_exists]
    agent = initialize_agent(
        tools,
        llm=None,   # Later we connect to Ollama or OpenAI
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )
    return agent
