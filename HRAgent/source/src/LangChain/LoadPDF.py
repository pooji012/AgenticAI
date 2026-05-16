from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import Docx2txtLoader

loader = PyPDFLoader(r"C:\Batch Learning\Prompt Engineering 3\Notes\Lang Chain Framework.pdf")
docs = loader.load()

print("Pages:", len(docs))
print("Page 1 content:", docs[0].page_content[:500])
print("Metadata:", docs[0].metadata)

loader2 = Docx2txtLoader(r"C:\Batch Learning\Prompt Engineering 3\Notes\Python_VSCode_Installation_Manual.docx")
docs2 = loader2.load()

print("Pages:", len(docs2))
print("Page 1 content:", docs2[0].page_content[:500])
print("Metadata:", docs2[0].metadata)