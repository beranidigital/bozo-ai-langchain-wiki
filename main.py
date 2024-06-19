import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, FewShotPromptTemplate
from langchain_core.runnables import RunnableLambda
from langsmith import traceable

load_dotenv()  # take environment variables from .env.

from typing import List, Any
from tools.wiki import search_wiki, list_books_from_shelves, read_book, get_wiki_shelves
from fastapi import FastAPI
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain import hub
from langchain.agents import create_openai_functions_agent
from langchain.agents import AgentExecutor
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.messages import BaseMessage
from langserve import add_routes
import models
import logging
logger = logging.getLogger(__name__)
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

# 1. Load Retriever
loader = WebBaseLoader("https://docs.smith.langchain.com/user_guide")
docs = loader.load()
text_splitter = RecursiveCharacterTextSplitter()
documents = text_splitter.split_documents(docs)
embeddings = models.embeddingModel
vector = FAISS.from_documents(documents, embeddings)
retriever = vector.as_retriever()

tools_list = [read_book, list_books_from_shelves, get_wiki_shelves]

# 3. Create Agent

prompt = ChatPromptTemplate.from_messages([
    ("system","""
    You are a helpful assistant for Berani Digital ID. Use the tools until you find relevant information on the Berani Digital ID wiki.
    Only provide information relevant to Berani Digital ID
    """),
    ("human", "What the capital of Indonesia?"),
    ("ai", "I'm sorry, I can only provide information relevant to Berani Digital ID."),
    ("human", "What is Berani Digital ID?"),
    ("ai", "Berani Digital ID is at the forefront of digital innovation and collaboration in Indonesia. Our mission is to create opportunities and develop products, all based on the principles of cooperation, trust, transparency and accountability."),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])
llm = models.chatModel
agent = create_openai_functions_agent(llm, tools_list, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools_list, verbose=True)

# 4. App definition
app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="A simple API server using LangChain's Runnable interfaces",
)


# 5. Adding chain route

# We need to add these input/output schemas because the current AgentExecutor
# is lacking in schemas.

class Input(BaseModel):
    input: str


class Output(BaseModel):
    output: Any

@traceable
def runnable_chain(input: dict):
    output = agent_executor.invoke(input)
    return output['output']


add_routes(
    app,
    RunnableLambda(runnable_chain),
    input_type=Input,
    output_type=Output,
    path="/agent",
)

if __name__ == "__main__":
    import uvicorn
    port = os.getenv("PORT", 8000)
    port = int(port)
    uvicorn.run(app, host="0.0.0.0", port=port)
