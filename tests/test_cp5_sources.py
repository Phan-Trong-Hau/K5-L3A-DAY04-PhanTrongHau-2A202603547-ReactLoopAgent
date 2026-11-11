"""Evidence validation at the final-answer boundary, without a real model."""
import unittest

from agent import run_agent
from status_tools import StatusTools
from test_lab import FakeProvider, final, tool_call


class SourceValidationTests(unittest.TestCase):
    def setUp(self):
        self.tools = StatusTools()
        self.arguments = '{"provider":"github","incident_id":"xr3myzj7ms51"}'
        self.url = self.tools.get_incident_details('github', 'xr3myzj7ms51')['url']

    def test_lookalike_urls_require_revision_with_observed_url(self):
        for bad_url in (self.url + '-fake', self.url + '?unobserved=1',
                        'https://example.invalid/?source=' + self.url):
            with self.subTest(url=bad_url):
                provider = FakeProvider([
                    tool_call('details', 'get_incident_details', self.arguments),
                    final('Nguồn: ' + bad_url),
                    final('Nguồn: ' + self.url),
                ])
                result = run_agent('Kiểm tra', provider, self.tools, max_steps=3)
                self.assertEqual(result['status'], 'completed')
                self.assertEqual(result['answer'], 'Nguồn: ' + self.url)
                self.assertEqual(sum(t['event'] == 'validation_missing_source'
                                     for t in result['trace']), 1)
                self.assertIn(self.url, provider.histories[2][-1]['content'])

    def test_markdown_link_and_sentence_punctuation_are_accepted(self):
        for answer in ('Nguồn: [incident](' + self.url + ').', 'Nguồn: ' + self.url + '.',
                       "Nguồn: '" + self.url + "'"):
            with self.subTest(answer=answer):
                provider = FakeProvider([
                    tool_call('details', 'get_incident_details', self.arguments), final(answer),
                ])
                result = run_agent('Kiểm tra', provider, self.tools)
                self.assertEqual(result['status'], 'completed')
                self.assertFalse(any(t['event'] == 'validation_missing_source' for t in result['trace']))
                self.assertEqual(len(provider.histories), 2)

    def test_failed_incident_observation_cannot_require_its_url(self):
        class FailedTools:
            def execute(self, name, args):
                return {'ok': False, 'error': 'TimeoutError', 'url': 'https://example.invalid/failed'}
        provider = FakeProvider([
            tool_call('failed', 'get_incident_details', '{}'), final('Không đủ dữ liệu'),
        ])
        result = run_agent('Kiểm tra', provider, FailedTools())
        self.assertEqual(result['status'], 'completed')
        self.assertFalse(any(t['event'] == 'validation_missing_source' for t in result['trace']))

    def test_repeated_missing_source_uses_existing_budget_only(self):
        provider = FakeProvider([
            tool_call('details', 'get_incident_details', self.arguments),
            final('Thiếu nguồn lần 1'), final('Vẫn thiếu nguồn'),
        ])
        result = run_agent('Kiểm tra', provider, self.tools, max_steps=3)
        self.assertEqual(result['status'], 'max_steps')
        self.assertEqual(len(provider.histories), 3)
        self.assertEqual(len(result['usage']), 3)
        self.assertEqual(sum(t['event'] == 'validation_missing_source' for t in result['trace']), 2)
        self.assertEqual(result['trace'][-1]['event'], 'max_steps')
