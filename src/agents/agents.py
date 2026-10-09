import os
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.tools.tools import web_search, scrape_url
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

def get_llm(model: str = None, temperature: float = 0.3):
    chosen_model = model or DEFAULT_MODEL
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    return ChatGoogleGenerativeAI(
        model=chosen_model,
        temperature=temperature,
        api_key=api_key,
    )

llm = get_llm()

# Search Agent
def build_search_agent(model_llm=None):
    return create_agent(
        model=model_llm or llm,
        tools=[web_search],
    )

# Reader Agent
def build_reader_agent(model_llm=None):
    return create_agent(
        model=model_llm or llm,
        tools=[scrape_url],
    )

# Writer Chain
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional."""),
])

def get_writer_chain(model_llm=None):
    return writer_prompt | (model_llm or llm) | StrOutputParser()

writer_chain = get_writer_chain()

# Critic Chain
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

def get_critic_chain(model_llm=None):
    return critic_prompt | (model_llm or llm) | StrOutputParser()

critic_chain = get_critic_chain()