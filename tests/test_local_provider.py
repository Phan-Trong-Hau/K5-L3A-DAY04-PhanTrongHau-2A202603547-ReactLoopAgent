"""Check local endpoint routing without making network requests."""
import os
import unittest
from unittest.mock import patch

from providers import Provider


class LocalProviderTests(unittest.TestCase):
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'local',
                            'OPENAI_BASE_URL': 'http://localhost:11434/v1/',
                            'LOCAL_MODEL': '1'})
    @patch('providers.post_json')
    def test_local_endpoint_and_judge_json(self, post):
        post.return_value = {'choices': [{'message': {'role': 'assistant', 'content': '{}'},
                                         'finish_reason': 'stop'}]}
        provider = Provider('openai', 'status-agent-local')
        provider.complete([{'role': 'user', 'content': 'judge'}], [])
        url, headers, payload = post.call_args.args
        self.assertEqual(url, 'http://localhost:11434/v1/chat/completions')
        self.assertEqual(payload['response_format'], {'type': 'json_object'})
        self.assertEqual(payload['temperature'], 0)
        self.assertNotIn('tools', payload)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'local', 'LOCAL_MODEL': '1'})
    @patch('providers.post_json')
    def test_tool_call_does_not_force_json_answer(self, post):
        post.return_value = {'choices': [{'message': {'role': 'assistant', 'content': 'ok'},
                                         'finish_reason': 'stop'}]}
        schemas = [{'type': 'function', 'function': {'name': 'example'}}]
        Provider('openai', 'local').complete([], schemas)
        payload = post.call_args.args[2]
        self.assertEqual(payload['tools'], schemas)
        self.assertNotIn('response_format', payload)
