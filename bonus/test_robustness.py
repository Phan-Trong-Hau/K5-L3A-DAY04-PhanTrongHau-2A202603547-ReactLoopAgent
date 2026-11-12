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

    def test_agent_schedules_bounded_retry_when_model_tries_to_stop(self):
        tools = BonusTools(scenario='rate_limit_once')
        provider = ScriptedProvider([
            call('first', 'get_vercel_status', {}), final('Không thể kiểm tra'),
            final('Vercel operational tại snapshot. https://www.vercel-status.com'),
        ])
        result = run_agent('Kiểm tra Vercel', provider, tools, max_steps=4)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(tools.calls[('get_vercel_status', 'vercel')], 2)
        scheduled = next(t for t in result['trace'] if t['event'] == 'scheduled_retry')
        retry_id = scheduled['calls'][0]['id']
        self.assertEqual(provider.histories[2][-1]['tool_call_id'], retry_id)
        self.assertEqual(provider.histories[2][-2]['tool_calls'][0]['id'], retry_id)
        self.assertEqual(json.loads(provider.histories[2][-1]['content'])['provider'], 'vercel')
        self.assertEqual(len(result['usage']), 3)

    def test_scheduled_argument_repair_keeps_identifiers_and_uses_schema(self):
        tools = BonusTools()
        good = {'provider': 'npm', 'incident_id': 'cc0t2r4403sy'}
        url = tools.get_incident_details(**good)['url']
        provider = ScriptedProvider([
            call('bad', 'get_incident_details', {**good, 'offset': 'zero', 'limit': '3', 'extra': 1}),
            final('Không thể đọc'), final('Incident resolved. Nguồn: ' + url),
        ])
        result = run_agent('Kiểm tra chi tiết', provider, tools, max_steps=4)
        self.assertEqual(result['status'], 'completed')
        scheduled = next(t for t in result['trace'] if t['event'] == 'scheduled_retry')
        fixed = json.loads(scheduled['calls'][0]['arguments'])
        self.assertEqual(fixed, {**good, 'offset': 0, 'limit': 3})
        self.assertEqual(tools.calls[('get_incident_details', 'npm')], 2)

    def test_mixed_retry_errors_share_one_failure_budget(self):
        class MixedErrors(BonusTools):
            def __init__(self):
                super().__init__()
                self.executed = 0
            def execute(self, name, args):
                self.executed += 1
                return {'ok': False, 'error': 'INVALID_ARGUMENTS' if self.executed == 2 else 'RATE_LIMITED',
                        'retry_after_seconds': 0}
        tools = MixedErrors()
        provider = ScriptedProvider([call(str(i), 'get_vercel_status', {}) for i in range(4)] +
                                    [final('Vercel chưa xác minh được')])
        result = run_agent('Kiểm tra', provider, tools, max_steps=6)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(tools.executed, 3)
        self.assertTrue(any(t['event'] == 'tool_blocked' for t in result['trace']))

    def test_user_incident_id_cannot_be_dismissed_without_lookup(self):
        tools = BonusTools(scenario='format_once')
        args = {'provider': 'npm', 'incident_id': 'cc0t2r4403sy'}
        url = tools.get_incident_details(**args)['url']
        provider = ScriptedProvider([
            call('status', 'get_npm_status', {'component': 'npm'}), final('Không tìm thấy'),
            final('Không thể đọc'), final('Incident resolved. ' + url),
        ])
        result = run_agent('Xem chi tiết npm incident cc0t2r4403sy', provider, tools, max_steps=6)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(tools.calls[('get_incident_details', 'npm')], 2)
        self.assertTrue(any(t['event'] == 'scheduled_required_lookup' for t in result['trace']))
        self.assertTrue(any(t['event'] == 'scheduled_retry' for t in result['trace']))

    def test_missing_requested_statuses_are_queried_from_registry(self):
        tools = BonusTools()
        provider = ScriptedProvider([final('Không có dữ liệu'), final('Đã kiểm tra GitHub và npm')])
        result = run_agent('Kiểm tra status GitHub và npm', provider, tools, max_steps=3)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual({t['name'] for t in result['trace'] if t['event'] == 'tool'},
                         {'get_github_status', 'get_npm_status'})

    def test_latest_incident_selection_uses_returned_timestamps(self):
        tools = BonusTools(scenario='noisy')
        response = call('vercel', 'get_vercel_status', {'component': 'Builds'})
        second = call('npm', 'get_npm_status', {'component': 'package publishing'})
        response['calls'] += second['calls']
        response['message']['tool_calls'] += second['message']['tool_calls']
        vurl = tools.get_incident_details('vercel', 'w661l7k3kf4p')['url']
        nurl = tools.get_incident_details('npm', 'cc0t2r4403sy')['url']
        provider = ScriptedProvider([response, final('Tất cả incident đều resolved'), final(vurl + ' ' + nurl)])
        result = run_agent('Đối chiếu incident mới nhất của Vercel Builds và npm publishing', provider, tools, max_steps=4)
        self.assertEqual(result['status'], 'completed')
        ids = {t['arguments']['incident_id'] for t in result['trace']
               if t['event'] == 'tool' and t['name'] == 'get_incident_details'}
        self.assertEqual(ids, {'w661l7k3kf4p', 'cc0t2r4403sy'})

    def test_unexpected_instructions_do_not_reach_model_observation(self):
        tools = BonusTools(scenario='injection')
        self.assertIn('external_notice', tools.status('npm'))
        provider = ScriptedProvider([call('npm', 'get_npm_status', {}), final('Nguồn: https://status.npmjs.org')])
        result = run_agent('Kiểm tra npm status', provider, tools)
        observation = json.loads(provider.histories[1][-1]['content'])
        self.assertNotIn('external_notice', observation)
        self.assertEqual(observation['context_omitted'], {'unexpected_fields': 1})
        self.assertEqual(result['status'], 'completed')

    def test_unsupported_providers_cannot_receive_invented_status(self):
        provider = ScriptedProvider([final('Linear và Slack đang outage https://example.invalid/fake')])
        result = run_agent('Xác nhận Linear và Slack đang outage', provider, BonusTools())
        self.assertEqual(result['status'], 'completed')
        self.assertNotIn('https://example.invalid', result['answer'])
        self.assertIn('Chưa có dữ liệu đã xác minh', result['answer'])
        self.assertTrue(any(t['event'] == 'scope_limited' for t in result['trace']))

    def test_user_supplied_identifier_case_is_preserved(self):
        provider = ScriptedProvider([final('Không biết'), final('Không tìm thấy trong snapshot')])
        result = run_agent('Xem chi tiết npm incident AbC12345Z', provider, BonusTools(), max_steps=3)
        self.assertEqual(result['status'], 'completed')
        call_event = next(t for t in result['trace'] if t['event'] == 'tool')
        self.assertEqual(call_event['arguments']['incident_id'], 'AbC12345Z')
        self.assertEqual(call_event['result']['error'], 'INCIDENT_NOT_FOUND')

    def test_provider_snapshot_dates_are_kept_separately(self):
        tools = BonusTools()
        response = call('github', 'get_github_status', {})
        other = call('npm', 'get_npm_status', {})
        response['calls'] += other['calls']
        response['message']['tool_calls'] += other['message']['tool_calls']
        provider = ScriptedProvider([response, final('Đã kiểm tra')])
        result = run_agent('Kiểm tra status GitHub và npm', provider, tools)
        self.assertEqual(result['status'], 'completed')
        prompt = provider.histories[1][0]['content']
        self.assertIn(tools.status('github')['captured_at'], prompt)
        self.assertIn(tools.status('npm')['captured_at'], prompt)
