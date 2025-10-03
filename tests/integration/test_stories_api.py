# tests/integration/test_stories_api.py
import pytest


@pytest.mark.integration
class TestStoriesAPI:
    """Integration tests for stories endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_story(self, test_client, auth_headers):
        """Test creating a story"""
        response = await test_client.post(
            "/api/v1/stories",
            headers=auth_headers,
            json={
                "text": "Integration test story",
                "visibility": "public"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["text"] == "Integration test story"
        assert data["visibility"] == "public"
        assert "id" in data
        assert "expires_at" in data
    
    @pytest.mark.asyncio
    async def test_get_feed(self, test_client, auth_headers):
        """Test getting story feed"""
        # Create some stories first
        for i in range(3):
            await test_client.post(
                "/api/v1/stories",
                headers=auth_headers,
                json={
                    "text": f"Feed test story {i}",
                    "visibility": "public"
                }
            )
        
        # Get feed
        response = await test_client.get(
            "/api/v1/stories",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
    
    @pytest.mark.asyncio
    async def test_view_story(self, test_client, auth_headers):
        """Test viewing a story"""
        # Create story
        create_response = await test_client.post(
            "/api/v1/stories",
            headers=auth_headers,
            json={
                "text": "Story to view",
                "visibility": "public"
            }
        )
        story_id = create_response.json()["id"]
        
        # View story
        view_response = await test_client.post(
            f"/api/v1/stories/{story_id}/view",
            headers=auth_headers
        )
        
        assert view_response.status_code == 200
        data = view_response.json()
        assert data["story_id"] == story_id
        assert data["is_new_view"] == True
        
        # View again (should be false)
        view_again = await test_client.post(
            f"/api/v1/stories/{story_id}/view",
            headers=auth_headers
        )
        
        assert view_again.json()["is_new_view"] == False
    
    @pytest.mark.asyncio
    async def test_add_reaction(self, test_client, auth_headers):
        """Test adding reaction to story"""
        # Create story
        create_response = await test_client.post(
            "/api/v1/stories",
            headers=auth_headers,
            json={
                "text": "Story to react to",
                "visibility": "public"
            }
        )
        story_id = create_response.json()["id"]
        
        # Add reaction
        reaction_response = await test_client.post(
            f"/api/v1/stories/{story_id}/reactions",
            headers=auth_headers,
            json={"emoji": "❤️"}
        )
        
        assert reaction_response.status_code == 201
        data = reaction_response.json()
        assert data["emoji"] == "❤️"
        assert data["story_id"] == story_id
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, test_client, auth_headers):
        """Test rate limiting on story creation"""
        # Try to create 21 stories (limit is 20/min)
        for i in range(21):
            response = await test_client.post(
                "/api/v1/stories",
                headers=auth_headers,
                json={
                    "text": f"Rate limit test {i}",
                    "visibility": "public"
                }
            )
            
            if i < 20:
                assert response.status_code == 201
            else:
                assert response.status_code == 429
                assert "Rate limit exceeded" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_idempotency(self, test_client, auth_headers):
        """Test idempotency key"""
        idempotency_key = "test-idempotency-key-123"
        
        # First request
        response1 = await test_client.post(
            "/api/v1/stories",
            headers={**auth_headers, "Idempotency-Key": idempotency_key},
            json={
                "text": "Idempotent story",
                "visibility": "public"
            }
        )
        
        # Second request with same key
        response2 = await test_client.post(
            "/api/v1/stories",
            headers={**auth_headers, "Idempotency-Key": idempotency_key},
            json={
                "text": "Different text",
                "visibility": "public"
            }
        )
        
        assert response1.status_code == 201
        assert response2.status_code == 201
        
        # Should return same story
        assert response1.json()["id"] == response2.json()["id"]
        assert response1.json()["text"] == response2.json()["text"]
