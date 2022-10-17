#!/bin/bash
# Run the Tox test suite for use with GitHub Actions
poetry run which supybot-test  # this is the only way to run the true Limnoria tests
SUPYBOT_TEST=$(poetry run which supybot-test) poetry run tox -c .toxrc -e "checks,coverage"
