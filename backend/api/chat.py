"""
对话问答 API 路由
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
import json

from models.chat import ChatRequest, ChatResponse
from services.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()


@router.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    """
    问答接口（非流式）

    支持:
    - 单文档/多文档问答
    - 多轮对话（携带 conversation_id）
    - 引用溯源
    """
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        response = await chat_service.ask(
            question=request.question,
            doc_ids=request.doc_ids,
            conversation_id=request.conversation_id,
            history=request.history
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask-stream")
async def ask_question_stream(request: ChatRequest):
    """
    问答接口（流式输出）

    使用 Server-Sent Events (SSE) 实现打字机效果
    """
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        async def generate():
            try:
                # 流式生成回答和引用
                async for event in chat_service.ask_stream(
                    question=request.question,
                    doc_ids=request.doc_ids,
                    conversation_id=request.conversation_id,
                    history=request.history
                ):
                    # 发送 SSE 格式数据
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            except Exception as e:
                # 发送错误事件
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest-questions")
async def suggest_questions(doc_ids: List[str]):
    """
    生成建议问题

    基于已上传的文档内容，生成 3-5 个建议问题
    """
    try:
        if not doc_ids:
            raise HTTPException(status_code=400, detail="Document IDs cannot be empty")

        questions = await chat_service.generate_suggested_questions(doc_ids)
        return {"questions": questions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
async def list_conversations():
    """
    获取所有对话列表
    """
    try:
        conversations = await chat_service.list_conversations()
        return {"conversations": conversations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    获取对话历史
    """
    try:
        conversation = await chat_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    删除对话历史
    """
    try:
        success = await chat_service.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
