MAKEFLAGS:= --no-print-directory
SHELL=bash
TEST_APPS=profiles

.PHONY: dev test lint

hmm:
	echo $(RUNSERVER_CMD)

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

define loanscript
from loans.models import Period, Renewal; \
Period(description="Acervo fixo", days=15).save(); \
Period(description="Acervo móvel", days=30).save(); \
Renewal(description="Primeira renovação", days=15).save(); \
Renewal(description="Segunda renovação", days=15).save()
endef

reset_db:
	rm -f db.sqlite3
	rm -rf books/migrations/* profiles/migrations/* loans/migrations/*
	. venv/bin/activate; ./manage.py makemigrations books
	. venv/bin/activate; ./manage.py makemigrations profiles
	. venv/bin/activate; ./manage.py makemigrations loans
	. venv/bin/activate; ./manage.py migrate
	. venv/bin/activate; DJANGO_SUPERUSER_PASSWORD=admin ./manage.py createsuperuser --noinput --username "admin" --email ""
	. venv/bin/activate; ./manage.py import_profiles
	. venv/bin/activate; ./manage.py import_books
	. venv/bin/activate; ./manage.py shell -c '$(loanscript)'

tmp2 := $(shell mktemp)
tmp1 := $(shell mktemp)

compare_reqs:
	cat *requirements.txt | sort > ${tmp1}
	pip freeze | sort > ${tmp2}
	git diff --no-index ${tmp1} ${tmp2}

compare_reqs_comm:
	@cat *requirements.txt | sort > ${tmp1}
	@pip freeze | sort > ${tmp2}
	@comm -13 ${tmp1} ${tmp2}

