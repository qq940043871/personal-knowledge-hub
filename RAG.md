<title>RAG&amp;LLM 从零学习笔记---Retrieval</title>

![图片展示了RAG智能问答系统的架构。左侧为Query Construction，包含Relational DB、GraphDBs、VectorDBs等数据源，通过Text-to-SQL、Text-to-Cypher等转换为查询语言，再经Query Translation、Routing等步骤，最终生成Query。右侧为Retrieval，有Re-ranking、Active Retrieval等环节，涉及Re-Bank、RankGPT等方法，以及CRAG、CRAK等技术。底部是Indexing和Generation，Indexing包括Chunk Optimization、Specific Embeddings等，Generation有Self-RAG、RRR等。该图直观呈现了系统从数据处理到生成答案的全流程。](https://feishu.cn/file/QzuObJfIgoUREVxEQHvcWtYkn5d)

## Re-ranking

我们之前用RAG融合展示了这一点：

1. 获取数据➕切片➕建立索引

![图片展示了RAG融合中获取数据、切片、建立索引的流程。从左侧“Question”出发，经“Vectorstore”（向量存储）处理后，分别生成Q1、Q2、Q3三个问题，再对应“Documents”（文档）进行处理。最终，通过“Funnel”（筛选）和“Brain”（大脑）环节，得到“Answer”（答案）。该图与上下文紧密相关，直观呈现了RAG融合中数据处理的步骤。](https://feishu.cn/file/MSQRb5H2MolKU7xRbjNcVeegnnd)

```Python
#### INDEXING ####
 
# Load blog
import bs4
from langchain_community.document_loaders import WebBaseLoader
loader = WebBaseLoader(
    web_paths=("<https://lilianweng.github.io/posts/2023-06-23-agent/>",),
    bs_kwargs=dict(
        parse_only=bs4.SoupStrainer(
            class_=("post-content", "post-title", "post-header")
        )
    ),
)
blog_docs = loader.load()
 
# Split
from langchain.text_splitter import RecursiveCharacterTextSplitter
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=300, 
    chunk_overlap=50)
 
# Make splits
splits = text_splitter.split_documents(blog_docs)
 
# Index
from langchain_openai import OpenAIEmbeddings
# from langchain_cohere import CohereEmbeddings
from langchain_community.vectorstores import Chroma
vectorstore = Chroma.from_documents(documents=splits, 
                                    # embedding=CohereEmbeddings()
                                    embedding=OpenAIEmbeddings())
 
retriever = vectorstore.as_retriever()
```

设置prompt，“使用llm对question生成多种不同的版本”

```Python
from langchain.prompts import ChatPromptTemplate
 
# RAG-Fusion
template = """You are a helpful assistant that generates multiple search queries based on a single input query. \\n
Generate multiple search queries related to: {question} \\n
Output (4 queries):"""
prompt_rag_fusion = ChatPromptTemplate.from_template(template)
```

建立chain

```Python
 
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
 
generate_queries = (
    prompt_rag_fusion 
    | ChatOpenAI(temperature=0)
    | StrOutputParser() 
    | (lambda x: x.split("\\n"))
)
```

为文档评分（所有结果重复次数越多，得分越高）

```Python
from langchain.load import dumps, loads
 
def reciprocal_rank_fusion(results: list[list], k=60):
    """ Reciprocal_rank_fusion that takes multiple lists of ranked documents 
        and an optional parameter k used in the RRF formula """
    
    # Initialize a dictionary to hold fused scores for each unique document
    fused_scores = {}
 
    # Iterate through each list of ranked documents
    for docs in results:
        # Iterate through each document in the list, with its rank (position in the list)
        for rank, doc in enumerate(docs):
            # Convert the document to a string format to use as a key (assumes documents can be serialized to JSON)
            doc_str = dumps(doc)
            # If the document is not yet in the fused_scores dictionary, add it with an initial score of 0
            if doc_str not in fused_scores:
                fused_scores[doc_str] = 0
            # Retrieve the current score of the document, if any
            previous_score = fused_scores[doc_str]
            # Update the score of the document using the RRF formula: 1 / (rank + k)
            fused_scores[doc_str] += 1 / (rank + k)
 
    # Sort the documents based on their fused scores in descending order to get the final reranked results
    reranked_results = [
        (loads(doc), score)
        for doc, score in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    ]
 
    # Return the reranked results as a list of tuples, each containing the document and its fused score
    return reranked_results
 
question = "What is task decomposition for LLM agents?"
retrieval_chain_rag_fusion = generate_queries | retriever.map() | reciprocal_rank_fusion
docs = retrieval_chain_rag_fusion.invoke({"question": question})
len(docs)
```

最后根据文档获得问题结果：

```Python
from operator import itemgetter
from langchain_core.runnables import RunnablePassthrough
 
# RAG
template = """Answer the following question based on this context:
{context}
Question: {question}
"""
 
prompt = ChatPromptTemplate.from_template(template)
 
llm = ChatOpenAI(temperature=0)
 
final_rag_chain = (
    {"context": retrieval_chain_rag_fusion, 
     "question": itemgetter("question")} 
    | prompt
    | llm
    | StrOutputParser()
)
 
final_rag_chain.invoke({"question":question})
```

另外，我们还可以使用Cohere Re-Rank

![这张图片展示了RAG检索流程中的重排序环节，分为两个阶段。第一阶段从数百万文档构成的文本档案中，针对查询“Regulatory approval”，通过语义或关键词检索得到初始搜索结果，共包含100条结果。第二阶段通过“Rerank”步骤对初始结果进行重新排序，最终得到的改进搜索结果显著提升了与查询的相关性，契合上下文提及的Re-ranking优化检索效果的内容。](https://feishu.cn/file/VWLGbYprUoTZRDx61fucWRomnWc)

```Python
 
from langchain_community.llms import Cohere
from langchain.retrievers import  ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CohereRerank
```

调用的别的方法进行re- ranking：

```Python
from langchain.retrievers.document_compressors import CohereRerank
 
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
 
# Re-rank
compressor = CohereRerank()
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor, base_retriever=retriever
)
 
compressed_docs = compression_retriever.get_relevant_documents(question)
 
```

# RAG-基于LangChain+ChatGLM-6B+本地知识库搭建的RAG智能问答系统-附项目源码+流程教程-优质项目实战 