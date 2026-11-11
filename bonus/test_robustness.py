"""Bonus mechanics, not claims about a real model's reasoning."""
import json
import unittest
from unittest.mock import patch

from agent import run_agent
from bonus.agent import retry_delay
from bonus.tools import BonusTools
from test_agent import ScriptedProvider, call, final


class BonusRobustnessTests(unittest.TestCase):
    def test_retry_after_seconds_dates_and_invalid_values(self):
        self.assertEqual(retry_delay({'retry_after': '2'}), 2)
        self.assertEqual(retry_delay({'retry_after_seconds': 0}), 0)
        self.assertEqual(retry_delay({'retry_after': 'Thu, 01 Jan 1970 00:00:05 GMT'}, now=0), 5)
        for value in ('bad', 'NaN', 'inf'):
            self.assertEqual(retry_delay({'retry_after': value}), 1)

    def test_persistent_429_executes_at_most_three_times(self):
        tools = BonusTools(scenario='rate_limit_always')
        provider = ScriptedProvider([call(str(i), 'get_vercel_status', {}) for i in range(4)] +
                                    [final('Chưa xác minh được Vercel vì 429')])
        result = run_agent('Kiểm tra Vercel', provider, tools, max_steps=8)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(tools.calls[('get_vercel_status', 'vercel')], 3)
        self.assertEqual(sum(t['event'] == 'tool' for t in result['trace']), 3)
        self.assertTrue(any(t['event'] == 'tool_blocked' for t in result['trace']))
        self.assertFalse(any(s['function']['name'] == 'get_vercel_status' for s in provider.schemas[3]))
        self.assertEqual(json.loads(provider.histories[4][-1]['content'])['error'], 'RETRY_LIMIT_REACHED')

    def test_honors_short_retry_after_before_next_execution(self):
        class RateOnce(BonusTools):
            def execute(self, name, args):
                if not hasattr(self, 'failed'):
                    self.failed = True
                    return {'ok': False, 'error': 'RATE_LIMITED', 'retry_after': '2'}
                return super().execute(name, args)
        provider = ScriptedProvider([call('a', 'get_vercel_status', {}),
                                     call('b', 'get_vercel_status', {}), final()])
        with patch('bonus.agent.time.monotonic', return_value=0), patch('bonus.agent.time.sleep') as sleep:
            result = run_agent('Kiểm tra', provider, RateOnce())
        self.assertEqual(result['status'], 'completed')
        sleep.assert_called_once_with(2)

    def test_long_retry_after_stops_without_busy_retry(self):
        class SlowLimit(BonusTools):
            def execute(self, name, args):
                return {'ok': False, 'error': 'RATE_LIMITED', 'retry_after': '60'}
        provider = ScriptedProvider([call('a', 'get_vercel_status', {}), final('Không xác minh được')])
        with patch('bonus.agent.time.sleep') as sleep:
            result = run_agent('Kiểm tra', provider, SlowLimit())
        self.assertEqual(result['status'], 'completed')
        self.assertTrue(any(t['event'] == 'retry_exhausted' and t['reason'] == 'wait_budget'
                            for t in result['trace']))
        sleep.assert_not_called()

    def test_timeline_gate_requests_missing_pages_before_completion(self):
        tools = BonusTools()
        args = {'provider': 'vercel', 'incident_id': 'sps6n39gm4sg'}
        url = tools.get_incident_details(**args)['url']
        provider = ScriptedProvider([
            call('first', 'get_incident_details', args), final('Nguồn: ' + url),
            call('next', 'get_incident_details', {**args, 'offset': 2, 'limit': 3}),
            call('last', 'get_incident_details', {**args, 'offset': 5, 'limit': 3}), final('Nguồn: ' + url),
        ])
        result = run_agent('Đọc timeline incident', provider, tools, max_steps=6)
        self.assertEqual(result['status'], 'completed')
        event = next(t for t in result['trace'] if t['event'] == 'validation_incomplete_timeline')
        self.assertEqual(event['next_calls'][0]['offset'], 2)
        self.assertEqual(sum(t['event'] == 'tool' for t in result['trace']), 3)

    def test_format_error_cannot_be_abandoned_before_retry(self):
        tools = BonusTools(scenario='format_once')
        args = {'provider': 'npm', 'incident_id': 'cc0t2r4403sy'}
        url = tools.get_incident_details(**args)['url']
        provider = ScriptedProvider([
            call('bad', 'get_incident_details', {**args, 'offset': 'zero'}), final('Không đủ dữ liệu'),
            call('good', 'get_incident_details', {**args, 'offset': 0, 'limit': 3}), final('Nguồn: ' + url),
        ])
        result = run_agent('Kiểm tra chi tiết', provider, tools, max_steps=5)
        self.assertEqual(result['status'], 'completed')
        self.assertTrue(any(t['event'] == 'validation_retry_pending' for t in result['trace']))
        self.assertEqual(json.loads(provider.histories[1][-1]['content'])['error'], 'INVALID_ARGUMENTS')

    def test_noise_is_compacted_without_losing_incident_evidence(self):
        tools = BonusTools(scenario='noisy')
        provider = ScriptedProvider([call('status', 'get_vercel_status', {}), final('Nguồn: https://www.vercel-status.com')])
        result = run_agent('Kiểm tra', provider, tools)
        model_observation = json.loads(provider.histories[1][-1]['content'])
        self.assertNotIn('distractors', model_observation)
        self.assertEqual(model_observation['context_omitted'], {'distractors': 160})
        self.assertEqual(model_observation['incidents'][0]['id'], 'w661l7k3kf4p')
        self.assertTrue(any(t['event'] == 'context_compacted' and t['omitted_count'] == 160 for t in result['trace']))

    def test_incomplete_timeline_at_budget_limit_is_not_completed(self):
        tools = BonusTools()
        args = {'provider': 'vercel', 'incident_id': 'sps6n39gm4sg'}
        url = tools.get_incident_details(**args)['url']
        provider = ScriptedProvider([call('first', 'get_incident_details', args), final('Nguồn: ' + url)])
        self.assertEqual(run_agent('Đọc timeline', provider, tools, max_steps=2)['status'], 'max_steps')


    def test_snapshot_status_and_latest_date_survive_reading_older_pages(self):
        tools = BonusTools()
        args = {'provider': 'vercel', 'incident_id': 'sps6n39gm4sg'}
        url = tools.get_incident_details(**args)['url']
        provider = ScriptedProvider([
            call('new', 'get_incident_details', {**args, 'limit': 3}),
            call('middle', 'get_incident_details', {**args, 'offset': 3, 'limit': 3}),
            call('old', 'get_incident_details', {**args, 'offset': 6, 'limit': 3}),
            final('Incident resolved tại snapshot. Nguồn: ' + url),
        ])
        result = run_agent('Đọc timeline', provider, tools, max_steps=5)
        self.assertEqual(result['status'], 'completed')
        context = provider.histories[-1][0]['content']
        self.assertIn('"status_at_snapshot": "resolved"', context)
        self.assertIn('2026-10-12T20:11:12.778000+00:00', context)
        self.assertNotIn('some builds and deployments for GitHub-connected', context)
