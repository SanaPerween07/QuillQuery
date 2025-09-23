from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.crypto import get_random_string
from dotenv import load_dotenv
import os
from pypdf import PdfReader

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  
CHROMA_DIR = os.getenv("CHROMA_DIR")

def get_pdf_text(pdfs_docs):
    text = ""
    for pdf in pdfs_docs:
        reader = PdfReader(pdf)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def get_text_chunks(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200
    )
    return splitter.split_text(text)


def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model = os.getenv("EMBEDDING_MODEL"),
        google_api_key=GEMINI_API_KEY
    )


def get_or_create_vectorstore(text_chunks=None):
    embeddings = get_embeddings()

    if os.path.isdir(CHROMA_DIR):
        vectorstore = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=embeddings
        )
        if text_chunks:
            vectorstore.add_texts(text_chunks)
    else:
        if not text_chunks:
            raise ValueError("No text chunks provided to create a new vectorstore.")
        vectorstore = Chroma.from_texts(
            texts=text_chunks,
            embedding=embeddings,
            persist_directory=CHROMA_DIR
        )

    return vectorstore


def get_conversation_chain(vectorstore):
    prompt_template = """
Answer the question as detailed as possible from the context provided. 
If the answer is not present in the context, say "I don't know". 
Do not make up an answer.

Context:
{context}

Question:
{question}

Answer:
    """.strip()

    model = ChatGoogleGenerativeAI(
        model = os.getenv("CHAT_MODEL"),
        temperature=0.3,
        google_api_key=GEMINI_API_KEY
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=model,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt}
    )

    return qa_chain

@csrf_exempt
def chat(request):
    answer = None
    session_id = request.session.get("session_id")
    if not session_id:
        session_id = get_random_string(32)
        request.session["session_id"] = session_id

    if request.method == "POST":
        pdfs_docs = request.FILES.getlist("pdfs")
        user_question = request.POST.get("question", "").strip()

        vectorstore = None
        if pdfs_docs:
            combined_text = get_pdf_text(pdfs_docs)
            chunks = get_text_chunks(combined_text)
            vectorstore = get_or_create_vectorstore(chunks)
        elif os.path.isdir(CHROMA_DIR):
            vectorstore = get_or_create_vectorstore()

        if user_question and vectorstore:
            qa_chain = get_conversation_chain(vectorstore)
            result = qa_chain.invoke(user_question)["result"]
            answer = result if result else "I don't know"

            chat_log = request.session.get("chat_log", [])
            chat_log.append({"question": user_question, "answer": answer})
            request.session["chat_log"] = chat_log


    chat_history = request.session.get("chat_log", [])

    return render(request, "home.html", {"answer": answer, "chat_history": chat_history})


