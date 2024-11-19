#!/bin/bash
set -e

# Find vulnerable python packages
pip-audit --desc -r requirements/dev.txt --ignore-vuln GHSA-w3h3-4rj7-4ph4
pip-audit --desc -r requirements/requirements.txt --ignore-vuln GHSA-w3h3-4rj7-4ph4
pip-audit --desc -r requirements/test.txt --ignore-vuln GHSA-w3h3-4rj7-4ph4
