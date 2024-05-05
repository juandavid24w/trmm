MAKEFLAGS:= --no-print-directory
SHELL=bash
TEST_APPS=profiles

.PHONY: dev test lint init reset_db compare_reqs compare_reqs_comm

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
			| egrep -v 'migrations/.*py$$' \
		); \
		if [ -n "$$files" ]; then \
			darker $$files \
			-l 78 -W 8 -f -i --color \
			-L "pylint"; \
		fi; \
		cd "$$OLDPWD"; \
	done; \
	echo ' -------------'


manage=. venv/bin/activate && set -a; . .env; set +a; ./manage.py

init:
	$(manage) migrate --noinput
	$(manage) collectstatic --noinput
	$(manage) createsuperuser --noinput

notify:
	$(manage) notify


define setupscriptbody
from loans.models import Period, Renewal
from django.contrib.auth.models import User, Group, Permission
from site_configuration.models import SiteConfiguration
Period(description="Acervo fixo", days=15).save()
Period(description="Acervo móvel", days=30).save()
Renewal(description="Primeira renovação", days=15, order=1).save()
Renewal(description="Segunda renovação", days=15, order=2).save()
usergroup, _ = Group.objects.get_or_create(name="Usuário")
usergroup.permissions.add(Permission.objects.get(codename="view_book"))
usergroup.permissions.add(Permission.objects.get(codename="view_specimen"))
usergroup.permissions.add(Permission.objects.get(codename="view_classification"))
usergroup.permissions.add(Permission.objects.get(codename="view_location"))
usergroup.permissions.add(Permission.objects.get(codename="view_loan"))
usergroup.permissions.add(Permission.objects.get(codename="view_period"))
usergroup.permissions.add(Permission.objects.get(codename="view_renewal"))
for user in User.objects.all():
    user.groups.add(usergroup)
modgroup, _ = Group.objects.get_or_create(name="Moderador")
modgroup.permissions.add(Permission.objects.get(codename="view_book"))
modgroup.permissions.add(Permission.objects.get(codename="add_book"))
modgroup.permissions.add(Permission.objects.get(codename="change_book"))
modgroup.permissions.add(Permission.objects.get(codename="delete_book"))
modgroup.permissions.add(Permission.objects.get(codename="view_specimen"))
modgroup.permissions.add(Permission.objects.get(codename="add_specimen"))
modgroup.permissions.add(Permission.objects.get(codename="change_specimen"))
modgroup.permissions.add(Permission.objects.get(codename="delete_specimen"))
modgroup.permissions.add(Permission.objects.get(codename="view_classification"))
modgroup.permissions.add(Permission.objects.get(codename="view_location"))
modgroup.permissions.add(Permission.objects.get(codename="view_loan"))
modgroup.permissions.add(Permission.objects.get(codename="add_loan"))
modgroup.permissions.add(Permission.objects.get(codename="change_loan"))
modgroup.permissions.add(Permission.objects.get(codename="delete_loan"))
modgroup.permissions.add(Permission.objects.get(codename="view_period"))
modgroup.permissions.add(Permission.objects.get(codename="view_renewal"))
modgroup.permissions.add(Permission.objects.get(codename="view_documentationpage"))
modgroup.permissions.add(Permission.objects.get(codename="change_documentationpage"))
modgroup.permissions.add(Permission.objects.get(codename="add_documentationpage"))
modgroup.permissions.add(Permission.objects.get(codename="delete_documentationpage"))
try:
	sc = SiteConfiguration.objects.get()
	sc.site_title = "Biblioteca da Arco"
	sc.site_header="Biblioteca da Arco"
	sc.index_title="Administração"
	sc.save()
except SiteConfiguration.DoesNotExist:
	SiteConfiguration(
		site_title="Biblioteca da arco",
		site_header="Biblioteca da arco",
		index_title="Administração",
	).save()
endef

export setupscriptbody
setupscript := ./manage.py	shell -c "$$setupscriptbody"

reset_db:
	. venv/bin/activate; ./manage.py makemigrations books profiles loans
	. venv/bin/activate; ./manage.py makemigrations site_configuration notifications
	git diff --numstat */migrations | awk '$$1==1 && $$2==1{print $$3}' | xargs git restore
	. venv/bin/activate; ./manage.py migrate
	. venv/bin/activate; DJANGO_SUPERUSER_PASSWORD=admin ./manage.py createsuperuser --noinput --username "admin" --email ""
	. venv/bin/activate; ./manage.py import_profiles
	. venv/bin/activate; $(setupscript)
	. venv/bin/activate; ./manage.py import_books

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

