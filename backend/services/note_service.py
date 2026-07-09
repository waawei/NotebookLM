"""
笔记服务 - 处理笔记的 CRUD 操作
"""

import os
import uuid
import json
from datetime import datetime
from typing import List, Optional

from core.config import settings
from models.note import NoteResponse


class NoteService:
    """笔记管理服务"""

    def __init__(self):
        self.notes_dir = os.path.join(settings.UPLOAD_DIR, "notes")
        self.notes = {}  # 内存缓存

        # 确保笔记目录存在
        os.makedirs(self.notes_dir, exist_ok=True)

        # 加载已有笔记
        self._load_notes()

    def _load_notes(self):
        """从文件系统加载笔记"""
        try:
            for filename in os.listdir(self.notes_dir):
                if filename.endswith('.json'):
                    note_id = filename.replace('.json', '')
                    file_path = os.path.join(self.notes_dir, filename)

                    with open(file_path, 'r', encoding='utf-8') as f:
                        note_data = json.load(f)
                        # 转换 datetime 字符串回对象
                        note_data['created_at'] = datetime.fromisoformat(note_data['created_at'])
                        note_data['updated_at'] = datetime.fromisoformat(note_data['updated_at'])
                        # 兼容旧数据（没有 conversation_id 字段）
                        if 'conversation_id' not in note_data:
                            note_data['conversation_id'] = None
                        self.notes[note_id] = note_data

            print(f"✅ Loaded {len(self.notes)} notes from disk")
        except Exception as e:
            print(f"⚠️ Failed to load notes: {e}")

    def _persist_note(self, note_id: str):
        """将笔记持久化到文件系统"""
        try:
            note = self.notes.get(note_id)
            if not note:
                return

            file_path = os.path.join(self.notes_dir, f"{note_id}.json")

            # 序列化时转换 datetime 为字符串
            note_data = {
                "note_id": note["note_id"],
                "title": note["title"],
                "content": note["content"],
                "doc_ids": note["doc_ids"],
                "conversation_id": note.get("conversation_id"),
                "created_at": note["created_at"].isoformat(),
                "updated_at": note["updated_at"].isoformat()
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(note_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"⚠️ Failed to persist note {note_id}: {e}")

    async def create_note(self, title: str, content: str, doc_ids: List[str] = None, conversation_id: str = None) -> str:
        """
        创建笔记

        Args:
            title: 笔记标题
            content: 笔记内容（Markdown）
            doc_ids: 关联的文档 ID 列表
            conversation_id: 关联的对话 ID

        Returns:
            note_id: 笔记唯一标识
        """
        note_id = str(uuid.uuid4())
        now = datetime.now()

        note = {
            "note_id": note_id,
            "title": title,
            "content": content,
            "doc_ids": doc_ids or [],
            "conversation_id": conversation_id,
            "created_at": now,
            "updated_at": now
        }

        self.notes[note_id] = note
        self._persist_note(note_id)

        return note_id

    async def get_note(self, note_id: str) -> Optional[NoteResponse]:
        """
        获取单个笔记

        Args:
            note_id: 笔记 ID

        Returns:
            note: 笔记信息
        """
        note = self.notes.get(note_id)
        if not note:
            return None

        return NoteResponse(**note)

    async def list_notes(self) -> List[NoteResponse]:
        """
        获取所有笔记列表

        Returns:
            notes: 笔记列表
        """
        notes = []
        for note in self.notes.values():
            notes.append(NoteResponse(**note))

        # 按更新时间倒序排序
        notes.sort(key=lambda x: x.updated_at, reverse=True)
        return notes

    async def update_note(
        self,
        note_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        doc_ids: Optional[List[str]] = None,
        conversation_id: Optional[str] = None
    ) -> bool:
        """
        更新笔记

        Args:
            note_id: 笔记 ID
            title: 新标题
            content: 新内容
            doc_ids: 新的文档 ID 列表
            conversation_id: 新的对话 ID

        Returns:
            success: 是否成功
        """
        note = self.notes.get(note_id)
        if not note:
            return False

        # 更新字段
        if title is not None:
            note["title"] = title
        if content is not None:
            note["content"] = content
        if doc_ids is not None:
            note["doc_ids"] = doc_ids
        if conversation_id is not None:
            note["conversation_id"] = conversation_id

        note["updated_at"] = datetime.now()

        # 持久化
        self._persist_note(note_id)
        return True

    async def delete_note(self, note_id: str) -> bool:
        """
        删除笔记

        Args:
            note_id: 笔记 ID

        Returns:
            success: 是否成功
        """
        if note_id not in self.notes:
            return False

        # 从内存删除
        del self.notes[note_id]

        # 删除持久化文件
        file_path = os.path.join(self.notes_dir, f"{note_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)

        return True
