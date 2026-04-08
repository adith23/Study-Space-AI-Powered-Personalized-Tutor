from typing import List

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, messages_from_dict, messages_to_dict
from sqlalchemy.orm import Session

from app.models.chat_model import ChatMessage

# Postgres chat message history
class PostgresChatMessageHistory(BaseChatMessageHistory):
    """
    Chat message history stored in a Postgres database.
    """

    def __init__(self, session_id: str, db_session: Session):
        self.session_id = session_id
        self.db = db_session

    @property
    def messages(self) -> List[BaseMessage]:
        """Retrieve messages from the database."""
        db_messages = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == self.session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

        items = [
            {"type": msg.role, "data": {"content": msg.content}} for msg in db_messages
        ]

        return messages_from_dict(items)

    def add_message(self, message: BaseMessage) -> None:
        """Append a message to the database."""

        message_dict = messages_to_dict([message])[0]

        role = message_dict.get("type")
        content = message_dict.get("data", {}).get("content")

        if not role or not content:
            return

        new_message = ChatMessage(
            session_id=self.session_id,
            role=role,
            content=content,
        )
        self.db.add(new_message)
        self.db.commit()

    def clear(self) -> None:
        """Clear all messages from the database for this session."""
        self.db.query(ChatMessage).filter(
            ChatMessage.session_id == self.session_id
        ).delete()
        self.db.commit()
