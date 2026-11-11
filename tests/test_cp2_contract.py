"""CP2: verify the actual conversation passed to the next provider request."""
import json
import unittest

from agent import run_agent
from status_tools import StatusTools
from test_lab import FakeProvider, final, tool_call


class ConversationContractTests(unittest.TestCase):
    def test_complete_assistant_message_precedes_all_tool_results(self):
        response = tool_call('github-id', 'get_status', '{"provider":"github"}')
        second = tool_call('cloudflare-id', 'get_status', '{"provider":"cloudflare"}')
        response['calls'] += second['calls']
        response['message']['tool_calls'] += second['message']['tool_calls']
        response['message']['content'] = 'Kiểm tra cả hai nhà cung cấp.'
        provider = FakeProvider([response, final('Đã kiểm tra')])

        result = run_agent('So sánh status', provider, StatusTools())

        self.assertEqual(result['status'], 'completed')
        history = provider.histories[1]
        self.assertEqual([m['role'] for m in history],
                         ['system', 'user', 'assistant', 'tool', 'tool'])
        self.assertEqual(history[2], response['message'])
        self.assertEqual([m['tool_call_id'] for m in history[3:]],
                         ['github-id', 'cloudflare-id'])
        self.assertEqual([json.loads(m['content'])['provider'] for m in history[3:]],
                         ['github', 'cloudflare'])
        self.assertEqual(len(provider.histories), 2)

    def test_final_answer_preserves_per_request_usage_and_result_contract(self):
        first = tool_call('status-id', 'get_status', '{"provider":"github"}')
        last = final('Theo snapshot, đã kiểm tra GitHub.')
        first['usage'] = {'total_tokens': 10}
        last['usage'] = {'total_tokens': 20}
        result = run_agent('Kiểm tra GitHub', FakeProvider([first, last]), StatusTools())

        self.assertEqual(result['answer'], last['message']['content'])
        self.assertEqual(result['usage'], [{'total_tokens': 10}, {'total_tokens': 20}])
        self.assertIsInstance(result['trace'], list)
        self.assertEqual([e['step'] for e in result['trace'] if e['event'] == 'model'], [1, 2])
