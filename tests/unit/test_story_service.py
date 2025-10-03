# tests/unit/test_story_service.py
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.services.story_service import StoryService
from fastapi import HTTPException


@pytest.mark.unit
class TestStoryService:
    """Unit tests for story service"""
    
    @pytest.mark.asyncio
    async def test_create_story_success(self):
        """Test successful story creation"""
        mock_pool = AsyncMock()
        author_id = uuid4()
        story_id = uuid4()
        
        mock_story = {
            "id": story_id,
            "author_id": author_id,
            "text": "Test story",
            "media_key": None,
            "visibility": "public",
            "created_at": "2025-10-03T12:00:00",
            "expires_at": "2025-10-04T12:00:00"
        }
        
        with patch('app.services.story_service.StoryRepository') as mock_repo, \
             patch('app.services.story_service.cache_service') as mock_cache:
            
            mock_repo.create_story = AsyncMock(return_value=mock_story)
            mock_cache.invalidate_user_feed = AsyncMock(return_value=None)
            
            result = await StoryService.create_story(
                pool=mock_pool,
                author_id=author_id,
                text="Test story",
                media_key=None,
                visibility="public"
            )
            
            assert result["id"] == story_id
            assert result["text"] == "Test story"
            mock_cache.invalidate_user_feed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_story_without_content(self):
        """Test creating story without text or media"""
        mock_pool = AsyncMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await StoryService.create_story(
                pool=mock_pool,
                author_id=uuid4(),
                text=None,
                media_key=None,
                visibility="public"
            )
        
        assert exc_info.value.status_code == 400
        assert "must have text or media" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_story_public(self):
        """Test getting public story"""
        mock_pool = AsyncMock()
        story_id = uuid4()
        viewer_id = uuid4()
        
        mock_story = {
            "id": story_id,
            "visibility": "public",
            "author_id": uuid4()
        }
        
        with patch('app.services.story_service.StoryRepository') as mock_repo:
            mock_repo.get_story_by_id = AsyncMock(return_value=mock_story)
            
            result = await StoryService.get_story(
                pool=mock_pool,
                story_id=story_id,
                viewer_id=viewer_id
            )
            
            assert result is not None
            assert result["visibility"] == "public"
    
    @pytest.mark.asyncio
    async def test_get_story_private_unauthorized(self):
        """Test getting private story by non-author"""
        mock_pool = AsyncMock()
        story_id = uuid4()
        author_id = uuid4()
        viewer_id = uuid4()
        
        mock_story = {
            "id": story_id,
            "visibility": "private",
            "author_id": author_id
        }
        
        with patch('app.services.story_service.StoryRepository') as mock_repo:
            mock_repo.get_story_by_id = AsyncMock(return_value=mock_story)
            
            result = await StoryService.get_story(
                pool=mock_pool,
                story_id=story_id,
                viewer_id=viewer_id
            )
            
            # Should return None for unauthorized access
            assert result is None
