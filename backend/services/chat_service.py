"""
对话服务 - RAG 问答核心逻辑
"""

import uuid
import json
import os
from typing import List, Optional
from datetime import datetime

from models.chat import ChatMessage, ChatResponse, Citation
from services.vector_store import VectorStoreService
from services.llm_service import LLMService
from core.config import settings


class ChatService:
    """对话问答服务"""

    def __init__(self):
        self.vector_store = VectorStoreService()
        self.llm_service = LLMService()
        self.conversations = {}  # 内存缓存
        self.conversations_dir = os.path.join(settings.UPLOAD_DIR, "conversations")

        # 确保对话存储目录存在
        os.makedirs(self.conversations_dir, exist_ok=True)

        # 加载已有对话历史
        self._load_conversations()

    async def ask(
        self,
        question: str,
        doc_ids: Optional[List[str]] = None,
        conversation_id: Optional[str] = None,
        history: Optional[List[ChatMessage]] = None
    ) -> ChatResponse:
        """
        RAG 问答

        Args:
            question: 用户问题
            doc_ids: 文档 ID 列表（None 表示搜索所有文档）
            conversation_id: 对话 ID
            history: 历史对话

        Returns:
            response: 回答和引用
        """
        # 生成或使用现有对话 ID
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        # 1. 检索相关文档块
        search_results = await self.vector_store.search(
            query=question,
            doc_ids=doc_ids
        )

        if not search_results:
            return ChatResponse(
                answer="Sorry, I couldn't find relevant information in the documents.",
                citations=[],
                conversation_id=conversation_id
            )

        # 2. 构建上下文
        context = self._build_context(search_results)

        # 3. 构建 Prompt
        prompt = self._build_prompt(question, context, history)

        # 4. 调用 LLM 生成答案
        answer = await self.llm_service.generate(prompt)

        # 5. 构建引用列表
        citations = self._build_citations(search_results)

        # 6. 保存对话历史
        self._save_conversation(conversation_id, question, answer, citations)

        return ChatResponse(
            answer=answer,
            citations=citations,
            conversation_id=conversation_id
        )

    async def ask_stream(
        self,
        question: str,
        doc_ids: Optional[List[str]] = None,
        conversation_id: Optional[str] = None,
        history: Optional[List[ChatMessage]] = None
    ):
        """
        RAG 问答（流式输出）

        Args:
            question: 用户问题
            doc_ids: 文档 ID 列表
            conversation_id: 对话 ID
            history: 历史对话

        Yields:
            events: SSE 事件流
        """
        # 生成或使用现有对话 ID
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        # 1. 发送开始事件
        yield {
            "type": "start",
            "conversation_id": conversation_id
        }

        # 2. 检索相关文档块
        search_results = await self.vector_store.search(
            query=question,
            doc_ids=doc_ids
        )

        if not search_results:
            yield {
                "type": "content",
                "content": "Sorry, I couldn't find relevant information in the documents."
            }
            yield {"type": "done"}
            return

        # 3. 构建上下文和 Prompt
        context = self._build_context(search_results)
        prompt = self._build_prompt(question, context, history)

        # 4. 流式生成回答
        answer_chunks = []
        async for chunk in self.llm_service.generate_stream(prompt):
            answer_chunks.append(chunk)
            yield {
                "type": "content",
                "content": chunk
            }

        # 5. 构建完整回答和引用
        full_answer = "".join(answer_chunks)
        citations = self._build_citations(search_results)

        # 6. 发送引用列表
        yield {
            "type": "citations",
            "citations": [c.dict() for c in citations]
        }

        # 7. 保存对话历史
        self._save_conversation(conversation_id, question, full_answer, citations)

        # 8. 发送完成事件
        yield {
            "type": "done",
            "conversation_id": conversation_id
        }

    def _load_conversations(self):
        """从文件系统加载对话历史"""
        try:
            for filename in os.listdir(self.conversations_dir):
                if filename.endswith('.json'):
                    conversation_id = filename.replace('.json', '')
                    file_path = os.path.join(self.conversations_dir, filename)

                    with open(file_path, 'r', encoding='utf-8') as f:
                        conversation_data = json.load(f)
                        # 转换 datetime 字符串回对象
                        conversation_data['created_at'] = datetime.fromisoformat(conversation_data['created_at'])
                        for msg in conversation_data['messages']:
                            msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
                        self.conversations[conversation_id] = conversation_data

            print(f"✅ Loaded {len(self.conversations)} conversations from disk")
        except Exception as e:
            print(f"⚠️ Failed to load conversations: {e}")

    def _persist_conversation(self, conversation_id: str):
        """将对话持久化到文件系统"""
        try:
            conversation = self.conversations.get(conversation_id)
            if not conversation:
                return

            file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")

            # 序列化时转换 datetime 为字符串
            conversation_data = {
                "id": conversation["id"],
                "created_at": conversation["created_at"].isoformat(),
                "messages": [
                    {
                        "question": msg["question"],
                        "answer": msg["answer"],
                        "citations": msg["citations"],
                        "timestamp": msg["timestamp"].isoformat()
                    }
                    for msg in conversation["messages"]
                ]
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"⚠️ Failed to persist conversation {conversation_id}: {e}")

    def _build_context(self, search_results: List[dict]) -> str:
        """
        构建上下文字符串

        Args:
            search_results: 搜索结果

        Returns:
            context: 格式化的上下文
        """
        context = ""
        for i, result in enumerate(search_results):
            context += f"\n[Source {i+1}]\n"
            context += f"{result['content']}\n"
            context += f"(Document ID: {result['metadata']['doc_id']}, Chunk ID: {result['metadata']['chunk_id']})\n"

        return context

    def _build_prompt(
        self,
        question: str,
        context: str,
        history: Optional[List[ChatMessage]] = None
    ) -> str:
        """
        构建 LLM Prompt

        Args:
            question: 用户问题
            context: 文档上下文
            history: 历史对话

        Returns:
            prompt: 完整的 Prompt
        """
        prompt = """You are a professional document Q&A assistant. Please answer the user's question based on the following document content.

Requirements:
1. Only answer based on the provided document content, do not make up information
2. If there is no relevant information in the documents, clearly state so
3. Mark citation positions in the answer with [Source 1], [Source 2], etc.
4. The answer should be clear, accurate, and logical

"""

        # 添加历史对话（多轮对话支持）
        if history:
            prompt += "\nConversation history:\n"
            for msg in history[-3:]:  # 只保留最近 3 轮
                prompt += f"{msg.role}: {msg.content}\n"

        # 添加文档上下文
        prompt += f"\nRelevant document content:\n{context}\n"

        # 添加当前问题
        prompt += f"\nUser question: {question}\n"
        prompt += "\nPlease answer based on the above documents (remember to mark citation sources):\n"

        return prompt

    def _build_citations(self, search_results: List[dict]) -> List[Citation]:
        """
        构建引用列表（带编号）

        Args:
            search_results: 搜索结果

        Returns:
            citations: 引用列表（带编号 [1], [2], [3]...）
        """
        citations = []
        for idx, result in enumerate(search_results, start=1):
            citations.append(Citation(
                number=idx,  # 引用编号
                doc_id=result['metadata']['doc_id'],
                doc_name=f"Document_{result['metadata']['doc_id'][:8]}",
                page=None,
                chunk_id=result['metadata']['chunk_id'],
                content=result['content'][:200] + "...",
                relevance_score=result['score']
            ))

        return citations

    def _save_conversation(
        self,
        conversation_id: str,
        question: str,
        answer: str,
        citations: List[Citation]
    ):
        """
        保存对话历史（内存 + 持久化）

        Args:
            conversation_id: 对话 ID
            question: 问题
            answer: 回答
            citations: 引用
        """
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                "id": conversation_id,
                "created_at": datetime.now(),
                "messages": []
            }

        self.conversations[conversation_id]["messages"].append({
            "question": question,
            "answer": answer,
            "citations": [c.dict() for c in citations],
            "timestamp": datetime.now()
        })

        # 持久化到磁盘
        self._persist_conversation(conversation_id)

    async def get_conversation(self, conversation_id: str) -> Optional[dict]:
        """
        获取对话历史

        Args:
            conversation_id: 对话 ID

        Returns:
            conversation: 对话信息
        """
        return self.conversations.get(conversation_id)

    async def list_conversations(self) -> List[dict]:
        """
        获取所有对话列表

        Returns:
            conversations: 对话列表（简化版，只包含 ID 和创建时间）
        """
        return [
            {
                "id": conv_id,
                "created_at": conv["created_at"].isoformat(),
                "message_count": len(conv["messages"]),
                "last_message": conv["messages"][-1]["question"] if conv["messages"] else None
            }
            for conv_id, conv in self.conversations.items()
        ]

    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        删除对话历史（内存 + 持久化文件）

        Args:
            conversation_id: 对话 ID

        Returns:
            success: 是否成功
        """
        if conversation_id in self.conversations:
            # 从内存删除
            del self.conversations[conversation_id]

            # 删除持久化文件
            file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)

            return True
        return False

    async def generate_suggested_questions(self, doc_ids: List[str]) -> List[str]:
        """
        生成建议问题

        基于文档内容生成 3-5 个用户可能想问的问题

        Args:
            doc_ids: 文档 ID 列表

        Returns:
            questions: 建议问题列表
        """
        # 1. 获取文档内容样本（取前几个 chunk）
        sample_chunks = []
        for doc_id in doc_ids[:3]:  # 最多取 3 个文档
            results = await self.vector_store.search(
                query="summary overview introduction",
                doc_ids=[doc_id],
                top_k=2
            )
            sample_chunks.extend([r['content'] for r in results])

        if not sample_chunks:
            return [
                "What are the main topics covered in this document?",
                "Can you provide a summary of the key points?",
                "What are the most important findings?",
            ]

        # 2. 构建 Prompt
        context = "\n\n".join(sample_chunks[:3])  # 取前 3 个 chunk
        prompt = f"""Based on the following document content, generate 5 questions that a user might want to ask about this document.

Requirements:
1. Questions should be specific and valuable
2. Cover the key themes of the document
3. Be clear and concise
4. Each question on a new line, starting with a number (1., 2., etc.)

Document content:
{context}

Generate 5 suggested questions:"""

        # 3. 调用 LLM 生成
        response = await self.llm_service.generate(prompt)

        # 4. 解析问题列表
        questions = []
        for line in response.strip().split('\n'):
            line = line.strip()
            # 去掉编号前缀
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                # 去掉 "1. " 或 "- " 等前缀
                question = line.lstrip('0123456789.-* ').strip()
                if question:
                    questions.append(question)

        # 5. 返回前 5 个问题
        return questions[:5]

