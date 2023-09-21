#!/bin/sh

pip-compile --resolver=backtracking --generate-hashes --reuse-hashes --upgrade --output-file requirements/requirements.txt requirements/requirements.in
pip-compile --resolver=backtracking --generate-hashes --reuse-hashes --upgrade --output-file requirements/test.txt requirements/test.in
pip-compile --resolver=backtracking --generate-hashes --reuse-hashes --upgrade --output-file requirements/dev.txt requirements/dev.in
