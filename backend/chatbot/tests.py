from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory
from unittest.mock import patch
from .views import chat

class ChatEndpointTests(SimpleTestCase):
    @patch("chatbot.views.genai.Client")
    def test_chat_returns_ai_reply(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.models.generate_content.return_value.text = "Hello from AI"
        request = APIRequestFactory().post("/api/chat/", {"message": "Hi"}, format="json")
        response = chat(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["reply"], "Hello from AI")
