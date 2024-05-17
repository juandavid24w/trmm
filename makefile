MAKEFLAGS:= --no-print-directory
SHELL=bash

.PHONY: dev test lint init reset_db compare_reqs compare_reqs_comm
venv=. venv/bin/activate

dev:
	@$(MAKE) -f dev/makefile

test:
	$(venv); ./manage.py test

lint:
	@$(SHELL) dev/lint.sh


DB_APPS = books profiles loans labels site_configuration notifications
DB_APPS += api csvio

remove_db:
	rm -f db.sqlite3

reset_migrations:
	rm -rf */migrations/*
	git restore $(addsuffix /migrations/*, $(DB_APPS))
	$(venv); ./manage.py migrate
	$(venv); ./manage.py makemigrations $(DB_APPS)
	$(venv); ./manage.py migrate

reset_db: remove_db reset_migrations
	$(venv); DJANGO_SUPERUSER_PASSWORD=admin ./manage.py createsuperuser \
		--noinput --username "admin" --email ""
	$(venv); ./manage.py shell < dev/setup.py
	$(venv); ./manage.py import_books
	$(venv); ./manage.py import_profiles

tmp2 := $(shell mktemp)
tmp1 := $(shell mktemp)

compare_reqs:
	@cat dev/*requirements.txt *requirements.txt | sort > ${tmp1}
	@$(venv); pip freeze | sort > ${tmp2}
	@git diff --no-index ${tmp1} ${tmp2}

compare_reqs_comm:
	@cat dev/*requirements.txt *requirements.txt | sort > ${tmp1}
	@$(venv) pip freeze | sort > ${tmp2}
	@comm -13 ${tmp1} ${tmp2}

-include dev/makefile.deploy
