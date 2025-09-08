from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
import os
from pypdf import PdfReader

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_pdf_text(pdfs_docs):
    text = ""
    for pdf in pdfs_docs:
        reader = PdfReader(pdf)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text


def get_text_chunks(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_text(text)


def get_vectorstore(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GEMINI_API_KEY 
    )

    # metadatas = [{"source": pdf_name, "chunk": i} for i in range(len(text_chunks))]
    
    vectorstore = Chroma.from_texts(
        texts=text_chunks,
        embedding=embeddings,
        persist_directory="chromaDB_index",
        # metadatas=metadatas
    )
    vectorstore.persist()
    return vectorstore


def load_vectorstore():
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GEMINI_API_KEY 
    )
    return Chroma(
        persist_directory="chromaDB_index",
        embedding_function=embeddings
    )


def get_conversation_chain():
    prompt_template = """
Answer the question as detailed as possible from the context provided. Make sure to provide all the details. 
If the answer is not present in the context, say "I don't know". Don't provide a wrong answer.

Context:
{context}

Question:
{question}

Answer:
    """.strip()

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,
        google_api_key=GEMINI_API_KEY  
    )

    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain



@csrf_exempt
def home(request):
    answer = None

    if request.method == "POST":   
        pdfs_docs = request.FILES.getlist("pdfs") 
        user_question = request.POST.get("question", "").strip()

        if pdfs_docs:
            for pdf in pdfs_docs:
                # pdf_name = pdf.name 
                raw_text = get_pdf_text([pdf])
                chunks = get_text_chunks(raw_text)
                vectorstore = get_vectorstore(chunks)

        elif os.path.isdir("chromaDB_index"):
            vectorstore = load_vectorstore()
        else:
            return render(request, "home.html", {"answer": "No PDFs uploaded and no index found."})

        if user_question:
            docs = vectorstore.similarity_search(user_question, k=4)
            chain = get_conversation_chain()
            result = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
            answer = result["output_text"]

    return render(request, "home.html", {"answer": answer})
