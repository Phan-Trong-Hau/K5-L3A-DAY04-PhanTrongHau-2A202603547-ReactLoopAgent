"""CP3: failure recovery and stopping behavior, using offline test doubles."""
import json
import unittest

from agent import run_agent
from status_tools import StatusTools
from test_lab import FakeProvider, final, tool_call


class RobustnessTests(unittest.TestCase):
    def test_invalid_arguments_return_observation_and_allow_recovery(self):
        for arguments in ('{', '[]', 'null', '"github"'):
            with self.subTest(arguments=arguments):
                provider = FakeProvider([
                    tool_call('bad', 'get_status', arguments),
                    tool_call('fixed', 'get_status', '{"provider":"github"}'),
                    final('Đã kiểm tra theo snapshot'),
                ])
                result = run_agent('Kiểm tra', provider, StatusTools())
                self.assertEqual(result['status'], 'completed')
                error = json.loads(provider.histories[1][-1]['content'])
                self.assertEqual(error['error'], 'INVALID_ARGUMENTS')
                self.assertEqual(provider.histories[1][-1]['tool_call_id'], 'bad')
                self.assertEqual(json.loads(provider.histories[2][-1]['content'])['provider'], 'github')

    def test_registry_errors_return_to_model(self):
        for name, arguments, error in (
            ('missing', '{}', 'UNKNOWN_TOOL'),
            ('get_status', '{"provider":"invalid"}', 'ValueError'),
        ):
            with self.subTest(name=name, arguments=arguments):
                provider = FakeProvider([tool_call('call', name, arguments), final('Không đủ dữ liệu')])
                result = run_agent('Kiểm tra', provider, StatusTools())
                self.assertEqual(result['status'], 'completed')
                self.assertEqual(json.loads(provider.histories[1][-1]['content'])['error'], error)
                self.assertEqual(result['trace'][1]['result']['error'], error)

    def test_timeout_observation_allows_model_to_report_missing_data(self):
        provider = FakeProvider([
            tool_call('timeout', 'get_status', '{"provider":"github"}'),
            final('Không thể xác minh vì tool timeout'),
        ])
        result = run_agent('Kiểm tra', provider, StatusTools(fail=True))
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(json.loads(provider.histories[1][-1]['content'])['error'], 'TimeoutError')

    def test_unhandled_tool_exception_still_returns_observation(self):
        class BrokenTools:
            def execute(self, name, args):
                raise TimeoutError('offline')
        provider = FakeProvider([tool_call('timeout', 'get_status', '{}'), final('Không đủ dữ liệu')])
        result = run_agent('Kiểm tra', provider, BrokenTools())
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(json.loads(provider.histories[1][-1]['content'])['error'], 'TimeoutError')

    def test_provider_error_preserves_previous_trace_and_usage(self):
        class FailingProvider:
            def __init__(self):
                self.count = 0
            def complete(self, messages, schemas):
                self.count += 1
                if self.count == 1:
                    response = tool_call('first', 'get_status', '{"provider":"github"}')
                    response['usage'] = {'total_tokens': 7}
                    return response
                raise RuntimeError('provider offline')
        result = run_agent('Kiểm tra', FailingProvider(), StatusTools())
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['usage'], [{'total_tokens': 7}])
        self.assertEqual([t['event'] for t in result['trace']], ['model', 'tool', 'provider_error'])
        self.assertEqual(result['trace'][-1]['step'], 2)

    def test_abnormal_finish_never_completes_or_executes_partial_calls(self):
        for reason in ('length', 'content_filter', None):
            with self.subTest(reason=reason):
                response = tool_call('partial', 'get_status', '{}')
                response['finish'] = reason
                result = run_agent('Kiểm tra', FakeProvider([response]), StatusTools())
                self.assertEqual(result['status'], 'error')
                self.assertFalse(any(t['event'] == 'tool' for t in result['trace']))
                self.assertEqual(result['trace'][-1]['event'], 'model_error')

    def test_tool_calls_finish_without_calls_is_error(self):
        response = final('chưa xong')
        response['finish'] = 'tool_calls'
        result = run_agent('Kiểm tra', FakeProvider([response]), StatusTools())
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['trace'][-1]['event'], 'model_error')

    def test_budget_limits_model_requests_and_records_stop_reason(self):
        provider = FakeProvider([tool_call(str(i), 'get_status', '{"provider":"github"}') for i in range(3)])
        result = run_agent('Kiểm tra', provider, StatusTools(), max_steps=2)
        self.assertEqual(result['status'], 'max_steps')
        self.assertEqual(len(provider.histories), 2)
        self.assertEqual(len(result['usage']), 2)
        self.assertEqual(result['trace'][-1], {'event': 'max_steps', 'step': 2})
        for event in result['trace']:
            self.assertIn('event', event)
            if event['event'] == 'tool':
                self.assertTrue({'step', 'name', 'arguments', 'result'} <= event.keys())
