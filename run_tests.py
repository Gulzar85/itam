#!/usr/bin/env python
"""
Test runner script for ITAM project
Run all tests or specific app tests
"""
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
from django.test.runner import DiscoverRunner

def run_tests(test_labels=None, verbosity=2):
    """Run Django tests"""
    if test_labels is None:
        test_labels = ['accounts', 'equipment', 'requests', 'notifications', 'core']

    settings.TEST_RUNNER = 'django.test.runner.DiscoverRunner'
    django.setup()

    runner = DiscoverRunner(verbosity=verbosity, interactive=False)
    failures = runner.run_tests(test_labels)

    return failures

if __name__ == '__main__':
    # Get test labels from command line args
    labels = sys.argv[1:] if len(sys.argv) > 1 else None

    print("=" * 70)
    print("ITAM - Running Comprehensive Tests")
    print("=" * 70)

    exit_code = run_tests(labels)

    if exit_code:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    else:
        print("\n✅ All tests passed!")

    sys.exit(exit_code)
