from django.test import TestCase
import json


class FrontendIndexTests(TestCase):
	def test_index_returns_json(self):
		response = self.client.get('/')
		self.assertEqual(response.status_code, 200)
		data = json.loads(response.content)
		self.assertIn('title', data)
		self.assertEqual(data['title'], 'Bookmarker')
