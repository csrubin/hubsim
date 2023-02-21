#!/bin/zsh

git add * .*
poetry run pre-commit run
git add * .*
