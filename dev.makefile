MAKEFLAGS:= --jobs=8

.PHONY: all server lint

define getrunserver
. venv/bin/activate \
	&& ./manage.py shell -c 'import django_extensions' 2>/dev/null >/dev/null \
	&& echo runserver_plus --cert-file cert.crt \
	|| echo runserver
endef

RUNSERVER_CMD=$(shell $(getrunserver))

all: server lint

server:
	@. ./venv/bin/activate \
		&& ./manage.py $(RUNSERVER_CMD) 0.0.0.0:8080 \
		2>&1 | \
		awk '{ print "[server] " $$0 }'

lint:
	+@watchmake --quiet --make-cmd="make lint" -i venv --ext .py . \
		| awk '{ print "[ lint ] " $$0 }'
