import unittest
from unittest.mock import MagicMock
import sys
import os

for mod_name in ['pymongo', 'langchain_groq']:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

sys.path.insert(0, os.path.dirname(__file__))

from langgraph_backend import chat_node, get_ai_response, stream_ai_response, llm
from langchain_core.messages import AIMessage

class TestLangGraphBackend(unittest.TestCase):
    def setUp(self):
        llm.invoke = MagicMock(return_value=AIMessage(content="Test LLM response"))

    def test_chat_node_missing_messages_key(self):
        state = {}
        result = chat_node(state)
        self.assertIn("messages", result)
        self.assertIsInstance(result["messages"][0], AIMessage)
        self.assertEqual(result["messages"][0].content, "Warning: Input query is missing or empty.")

    def test_chat_node_empty_messages(self):
        state = {"messages": []}
        result = chat_node(state)
        self.assertIn("messages", result)
        self.assertIsInstance(result["messages"][0], AIMessage)
        self.assertEqual(result["messages"][0].content, "Warning: Input query is missing or empty.")

    def test_get_ai_response_empty_text(self):
        result = get_ai_response("")
        self.assertEqual(result, "Warning: Input query is missing or empty.")

    def test_stream_ai_response_empty_text(self):
        tokens = list(stream_ai_response("", "test_thread"))
        self.assertEqual(tokens, ["Warning: Input query is missing or empty."])

if __name__ == '__main__':
    unittest.main()
