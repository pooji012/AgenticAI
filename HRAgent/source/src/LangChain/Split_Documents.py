from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load the PDF document
loader = PyPDFLoader(r"C:\Batch Learning\Prompt Engineering 3\Notes\Lang Chain Framework.pdf")
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=20,)

chunks = text_splitter.split_documents(docs)

print("Number of chunks:", len(chunks))
print("Chunk 1 content:", chunks[0].page_content[:500])