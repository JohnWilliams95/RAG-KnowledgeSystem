from __future__ import annotations

from enum import Enum

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


class PromptStyle(str, Enum):
    CONCISE = "concise"
    DETAILED = "detailed"
    ACADEMIC = "academic"


RAG_QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "你是一个专业的知识库问答助手。请基于以下检索到的参考资料回答用户的问题。\n\n"
        "规则：\n"
        "1. 必须基于提供的参考资料回答，不要编造信息\n"
        "2. 如果参考资料不足以回答问题，请明确说明\n"
        "3. 回答时引用来源，格式为 [来源: 文件名]\n"
        "4. 如果多个参考资料来自同一文档，请合并引用，只列出一次文档名，不要重复\n"
        "5. 使用清晰、专业的语言\n"
        "6. 对复杂问题进行结构化回答\n\n"
        "参考资料：\n{context}"
    )),
    MessagesPlaceholder("history", optional=True),
    ("human", "{question}"),
])


RAG_QA_CONCISE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "基于以下参考资料简洁回答问题。如果资料不足请说明。\n"
        "引用来源格式: [来源: 文件名]。同一文档只引用一次，不要重复。\n\n"
        "参考资料：\n{context}"
    )),
    MessagesPlaceholder("history", optional=True),
    ("human", "{question}"),
])


RAG_QA_DETAILED_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "你是一个专业的知识库问答助手。请基于以下检索到的参考资料，"
        "给出详尽、结构化的回答。\n\n"
        "规则：\n"
        "1. 必须基于提供的参考资料回答，不要编造信息\n"
        "2. 如果参考资料不足以回答问题，请明确指出缺少哪方面的信息\n"
        "3. 引用来源格式为 [来源: 文件名]，同一文档只引用一次，不要重复列出\n"
        "4. 使用分层次的结构化回答（要点、分析、总结）\n"
        "5. 对不同来源的信息进行综合分析\n"
        "6. 提供推理过程，让回答有据可循\n\n"
        "参考资料：\n{context}"
    )),
    MessagesPlaceholder("history", optional=True),
    ("human", "{question}"),
])


CONDENSE_QUESTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "基于以下对话历史和最新问题，将问题改写为独立的、"
        "包含完整上下文的问题。只输出改写后的问题，不要多余解释。"
    )),
    ("human", (
        "对话历史：\n{history}\n\n"
        "最新问题：{question}\n\n"
        "改写后的独立问题："
    )),
])


SUMMARIZE_CONTEXT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "请将以下多段检索内容浓缩为关键信息，去除重复内容，"
        "保留与问题最相关的事实。输出简洁的摘要。"
    )),
    ("human", "问题：{question}\n\n检索内容：\n{context}"),
])


PROMPT_MAP = {
    PromptStyle.CONCISE: RAG_QA_CONCISE_PROMPT,
    PromptStyle.DETAILED: RAG_QA_DETAILED_PROMPT,
    PromptStyle.ACADEMIC: RAG_QA_PROMPT,
}


def get_prompt(style: PromptStyle = PromptStyle.DETAILED) -> ChatPromptTemplate:
    return PROMPT_MAP.get(style, RAG_QA_PROMPT)