"""Moved from api/tests.py: that module collided with the api/tests package
during unittest discovery (dual ``api/tests`` resolution -> ImportError),
breaking the FULL test suite. Content preserved verbatim."""

from django.test import SimpleTestCase


class ApiPlaceholderTests(SimpleTestCase):
	def test_placeholder(self):
		# Placeholder test to keep the api tests module lightweight in test env
		self.assertTrue(True)
