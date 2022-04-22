SHELL := /bin/bash
manage = "./app/manage.py"
current_dir = $(shell pwd)

clean:
	py3clean .


test:
	@python3 $(manage) test ./app --noinput --failfast


coverage:
	@coverage run --source='app' $(manage) test ./app --noinput --failfast
	@coverage html --skip-covered
	@echo
	@echo
	@echo "Coverage:" "file://"$(current_dir)"/app/local/htmlcov/index.html"


run:
	@python3 $(manage) runserver
