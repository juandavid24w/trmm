MAKEFLAGS:= --no-print-directory
SHELL=bash
TEST_APPS=profiles

.PHONY: dev test lint

dev:
	@$(MAKE) -f dev.makefile

test:
	@. venv/bin/activate && ./manage.py test $(TEST_APPS)

lint:
	@. ./venv/bin/activate; \
	PYTHONPATH=venv/lib64/python3.11/site-packages/; \
	for folder in . $$(git submodule | sed 's/^.//' | cut -d' ' -f2); do \
		cd $$folder; \
		files=$$( \
			git diff --diff-filter d --name-only \
			| cat - <(git diff --cached --name-only) \
			| cat - <(git ls-files --other --exclude-standard) \
			| egrep '.py$$' \
		); \
		if [ -n "$$files" ]; then \
			darker $$files \
			-l 78 -W 8 -f -i --color \
			-L "pylint"; \
		fi; \
		cd "$$OLDPWD"; \
	done; \
	echo ' -------------'

reset_db:
	rm db.sqlite3
	rm -rf books/migrations/* profiles/migrations/*
	. venv/bin/activate; ./manage.py makemigrations books
	. venv/bin/activate; ./manage.py makemigrations profiles
	. venv/bin/activate; ./manage.py migrate
	. venv/bin/activate; DJANGO_SUPERUSER_PASSWORD=admin ./manage.py createsuperuser --noinput --username "admin" --email ""
	. venv/bin/activate; ./manage.py import_profiles
	. venv/bin/activate; ./manage.py import_books
