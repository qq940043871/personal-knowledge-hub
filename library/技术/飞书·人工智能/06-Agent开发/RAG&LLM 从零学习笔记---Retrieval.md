# RAG&amp;LLM 从零学习笔记---Retrieval

（原图见飞书文档，本地未能获取）

（原图见飞书文档，本地未能获取）Re-ranking

我们之前用RAG融合展示了这一点：

1. 获取数据➕切片➕建立索引

（原图见飞书文档，本地未能获取）

（原图见飞书文档，本地未能获取）`#### INDEXING ####  
   
# Load blog  
import bs4  
from langchain_community.document_loaders import WebBaseLoader  
loader = WebBaseLoader(  
    web_paths=("",),  
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
   
retriever = vectorstore.as_retriever()`

设置prompt，“使用llm对question生成多种不同的版本”

```
<code>from langchain.prompts import ChatPromptTemplate<br/> <br/># RAG-Fusion<br/>template = """You are a helpful assistant that generates multiple search queries based on a single input query. \\n<br/>Generate multiple search queries related to: {question} \\n<br/>Output (4 queries):"""<br/>prompt_rag_fusion = ChatPromptTemplate.from_template(template)</code>
```

建立chain

```
<code> <br/>from langchain_core.output_parsers import StrOutputParser<br/>from langchain_openai import ChatOpenAI<br/> <br/>generate_queries = (<br/>    prompt_rag_fusion <br/>    | ChatOpenAI(temperature=0)<br/>    | StrOutputParser() <br/>    | (lambda x: x.split("\\n"))<br/>)</code>
```

为文档评分（所有结果重复次数越多，得分越高）

```
<code>from langchain.load import dumps, loads<br/> <br/>def reciprocal_rank_fusion(results: list[list], k=60):<br/>    """ Reciprocal_rank_fusion that takes multiple lists of ranked documents <br/>        and an optional parameter k used in the RRF formula """<br/>    <br/>    # Initialize a dictionary to hold fused scores for each unique document<br/>    fused_scores = {}<br/> <br/>    # Iterate through each list of ranked documents<br/>    for docs in results:<br/>        # Iterate through each document in the list, with its rank (position in the list)<br/>        for rank, doc in enumerate(docs):<br/>            # Convert the document to a string format to use as a key (assumes documents can be serialized to JSON)<br/>            doc_str = dumps(doc)<br/>            # If the document is not yet in the fused_scores dictionary, add it with an initial score of 0<br/>            if doc_str not in fused_scores:<br/>                fused_scores[doc_str] = 0<br/>            # Retrieve the current score of the document, if any<br/>            previous_score = fused_scores[doc_str]<br/>            # Update the score of the document using the RRF formula: 1 / (rank + k)<br/>            fused_scores[doc_str] += 1 / (rank + k)<br/> <br/>    # Sort the documents based on their fused scores in descending order to get the final reranked results<br/>    reranked_results = [<br/>        (loads(doc), score)<br/>        for doc, score in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)<br/>    ]<br/> <br/>    # Return the reranked results as a list of tuples, each containing the document and its fused score<br/>    return reranked_results<br/> <br/>question = "What is task decomposition for LLM agents?"<br/>retrieval_chain_rag_fusion = generate_queries | retriever.map() | reciprocal_rank_fusion<br/>docs = retrieval_chain_rag_fusion.invoke({"question": question})<br/>len(docs)</code>
```

最后根据文档获得问题结果：

```
<code>from operator import itemgetter<br/>from langchain_core.runnables import RunnablePassthrough<br/> <br/># RAG<br/>template = """Answer the following question based on this context:<br/>{context}<br/>Question: {question}<br/>"""<br/> <br/>prompt = ChatPromptTemplate.from_template(template)<br/> <br/>llm = ChatOpenAI(temperature=0)<br/> <br/>final_rag_chain = (<br/>    {"context": retrieval_chain_rag_fusion, <br/>     "question": itemgetter("question")} <br/>    | prompt<br/>    | llm<br/>    | StrOutputParser()<br/>)<br/> <br/>final_rag_chain.invoke({"question":question})</code>
```

另外，我们还可以使用Cohere Re-Rank

（原图见飞书文档，本地未能获取）

（原图见飞书文档，本地未能获取）`   
from langchain_community.llms import Cohere  
from langchain.retrievers import  ContextualCompressionRetriever  
from langchain.retrievers.document_compressors import CohereRerank`

调用的别的方法进行re- ranking：

```
<code>from langchain.retrievers.document_compressors import CohereRerank<br/> <br/>retriever = vectorstore.as_retriever(search_kwargs={"k": 10})<br/> <br/># Re-rank<br/>compressor = CohereRerank()<br/>compression_retriever = ContextualCompressionRetriever(<br/>    base_compressor=compressor, base_retriever=retriever<br/>)<br/> <br/>compressed_docs = compression_retriever.get_relevant_documents(question)<br/> </code>
```

# RAG-基于LangChain+ChatGLM-6B+本地知识库搭建的RAG智能问答系统-附项目源码+流程教程-优质项目实战