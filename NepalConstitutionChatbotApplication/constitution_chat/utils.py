import os
from PyPDF2 import PdfReader
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class ConstitutionChat:
    def __init__(self):
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        
        self.setup_qa_system()

    def setup_qa_system(self):
        pdf_path = os.path.join(os.path.dirname(__file__), 'data', 'pdf/Constitution_of_Nepal.pdf')
        raw_text = self.extract_text_from_pdf(pdf_path)
        
        # Split text
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=800,
            chunk_overlap=200,
            length_function=len,
        )
        texts = text_splitter.split_text(raw_text)
        
        # Create embeddings and vector store
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            task_type="retrieval_query",
            title="Constitution Query"
        )
        vector_store = FAISS.from_texts(texts, embeddings)
        
        # Setup LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0.3,
            convert_system_message_to_human=True
        )
        
        # Create prompt template
        prompt_template = """
        Context: {context}

        Question: {question}

        Please provide a detailed answer based on the context provided above from Nepal's Constitution. 
        If the information is not available in the context, please say so.

        Answer:"""

        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Create QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
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

    def extract_text_from_pdf(self, pdf_path):
        with open(pdf_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text() or ''
        return text

    def get_answer(self, question):
        try:
            result = self.qa_chain.invoke({"query": question})
            return result["result"]
        except Exception as e:
            return f"Error: {str(e)}"