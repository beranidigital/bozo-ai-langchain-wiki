import os

from langchain_openai import AzureOpenAI, AzureChatOpenAI, AzureOpenAIEmbeddings

completionModel = AzureOpenAI(
    api_version="2023-12-01-preview",
    deployment_name=os.getenv("AZURE_OPENAI_COMPLETION_DEPLOYMENT_NAME"),
)

chatModel = AzureChatOpenAI(
    api_version="2023-12-01-preview",
    deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
)

embeddingModel = AzureOpenAIEmbeddings(
    api_version="2023-12-01-preview",
    model=os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME")
)
