"""Dependency wiring: build a repository -> service graph from the request's DB
session. Routers depend on these; they never construct services by hand.

This is where the layers get connected: session -> repository -> service.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.document_repository import DocumentRepository
from app.services.chat_service import ChatService
from app.services.ingest_service import IngestService
from app.services.retrieval_service import RetrievalService

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_repo(session: SessionDep) -> DocumentRepository:
    return DocumentRepository(session)


RepoDep = Annotated[DocumentRepository, Depends(get_repo)]


def get_ingest_service(repo: RepoDep) -> IngestService:
    return IngestService(repo)


def get_chat_service(repo: RepoDep) -> ChatService:
    return ChatService(RetrievalService(repo))


IngestServiceDep = Annotated[IngestService, Depends(get_ingest_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
