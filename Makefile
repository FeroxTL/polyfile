SHELL := /bin/bash
manage = "./polyfile/manage.py"
current_dir = $(shell pwd)

clean:
	py3clean .


test:
	@python3 $(manage) test ./polyfile --noinput --failfast


coverage:
	@coverage run --source='polyfile' $(manage) test ./polyfile --noinput --failfast
	@coverage html --skip-covered
	@echo
	@echo
	@echo "Coverage:" "file://"$(current_dir)"/polyfile/local/htmlcov/index.html"


run:
	@python3 $(manage) runserver
