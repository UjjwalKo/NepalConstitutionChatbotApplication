from PyPDF2 import PdfReader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import google.generativeai as genai
from django.conf import settings
import os

os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

def extract_text_from_pdf(pdf_path):
    file_read = PdfReader(pdf_path)
    raw_text = ''
    for page in file_read.pages:
        content = page.extract_text()
        if content:
            raw_text += content
    return raw_text

raw_text = extract_text_from_pdf('Constitution_of_Nepal.pdf')

text_splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=800,
    chunk_overlap=200,
    length_function=len,
)
texts = text_splitter.split_text(raw_text)

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",  
    task_type="retrieval_query",
    title="Constitution Query"
)
vector_store = FAISS.from_texts(texts, embeddings)

llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    temperature=0.3,
    convert_system_message_to_human=True
)

prompt_template = """
Context: {context}

Question: {question}

Please provide a detailed answer based on the context provided above. If the information is not available in the context, please say so.

Answer:"""

PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "question"]
)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    ),
    return_source_documents=True,
    chain_type_kwargs={
        "prompt": PROMPT
    }
)

def is_general_message(query):
    general_phrases = [
        "how are you",
        "hello",
        "hi",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "what's up",
        "who are you",
        "what can you do"
    ]
    return any(phrase in query.lower() for phrase in general_phrases)

def ask_question(query):
    if is_general_message(query):
        return "Hello! I'm the Nepal Constitution Chatbot. I'm here to answer questions specifically about the Constitution of Nepal. How can I assist you with information about Nepal's constitution today?"
    
    try:
        result = qa_chain.invoke({"query": query})
        answer = result["result"]
        return answer
    except Exception as e:
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {str(e)}")
        return "I apologize, but I encountered an error while processing your question. Could you please rephrase your question about Nepal's constitution, and I'll do my best to assist you?"