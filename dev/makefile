MAKEFLAGS:= --jobs=8

.PHONY: all server lint huey

define getrunserver
. venv/bin/activate \
	&& ./manage.py shell -c 'import django_extensions' 2>/dev/null >/dev/null \
	&& echo runserver_plus --cert-file cert.crt \
	|| echo runserver
endef

RUNSERVER_CMD:=$(or $(RUNSERVER_CMD),$(shell $(getrunserver)))
venv=. ./venv/bin/activate

all: server lint

server:
	@$(venv) && python -u manage.py $(RUNSERVER_CMD) 0.0.0.0:8080 2>&1 | \
		awk '{ print "[server] " $$0 }'

lint:
	+@$(venv) && python -u dev/watchmake/watchmake.py --quiet \
		--make-cmd="make lint" -i venv --ext .py --ext .html . \
		| awk '{ print "[ lint ] " $$0 }'

huey:
	@$(venv); python -u manage.py run_huey 2>&1 | \
		awk '{ print "[ huey ] " $$0 }'
