from langchain_openai import OpenAI
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings


class RAGService:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = Chroma(
            persist_directory=persist_directory, embedding_function=self.embeddings
        )
        self.llm = OpenAI(model="gpt-4o-mini")
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm, chain_type="stuff", retriever=self.vector_store.as_retriever()
        )

    def query(self, question: str) -> str:
        return self.qa_chain.run(question)
