import unittest
from unittest.mock import patch, MagicMock
from core.llm_zen import generate_zen_chat
from core.state import st

class TestZenFallback(unittest.TestCase):
    @patch("core.llm_zen.local_generate_chat")
    @patch("core.llm_zen.call_openai_compatible")
    @patch("core.llm_zen.call_gemini")
    @patch("core.tts.say_text")
    def test_fallback_chain(self, mock_say, mock_gemini, mock_openai, mock_local):
        # We need to simulate the environment variables so it tries all providers
        with patch.dict("os.environ", {
            "CEREBRAS_API_KEY": "test",
            "GROQ_API_KEY": "test",
            "GEMINI_API_KEY": "test",
            "OPENROUTER_API_KEY": "test",
            "NVIDIA_API_KEY": "test"
        }):
            # Set up mocks to fail for the first 3 providers, succeed on the 4th (OpenRouter)
            # Order is: Cerebras, Groq, Gemini, OpenRouter, Nvidia
            
            # call_openai_compatible is called for Cerebras, Groq, OpenRouter, Nvidia
            # We want it to fail for the first 2 calls (Cerebras, Groq)
            # Gemini is handled by call_gemini, make it fail.
            # 3rd call to openai (OpenRouter) should succeed.
            
            mock_openai.side_effect = [Exception("Cerebras Down"), Exception("Groq Down"), "OpenRouter Success"]
            mock_gemini.side_effect = Exception("Gemini Down")
            
            st.zen_mode = True
            
            result = generate_zen_chat([{"role": "user", "content": "Hello"}], use_tools=False)
            
            self.assertEqual(result, "OpenRouter Success")
            self.assertTrue(st.zen_mode) # Still true because it didn't exhaust all
            
            # Now test exhausting all providers
            mock_openai.side_effect = [Exception("Error")] * 4
            mock_gemini.side_effect = Exception("Error")
            mock_local.return_value = "Local Success"
            
            result = generate_zen_chat([{"role": "user", "content": "Hello"}], use_tools=False)
            
            self.assertEqual(result, "Local Success")
            self.assertFalse(st.zen_mode) # It should have toggled Zen Mode off
            mock_say.assert_called_once() # Should have said the fallback phrase
            
if __name__ == "__main__":
    unittest.main()
