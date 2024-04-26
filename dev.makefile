MAKEFLAGS:= --jobs=8

.PHONY: all server lint

all: server lint

server:
	@. ./venv/bin/activate \
		&& ./manage.py runserver 0.0.0.0:8080 \
		2>&1 | \
		awk '{ print "[server] " $$0 }'

lint:
	+@watchmake --quiet --make-cmd="make lint" -i venv --ext .py . \
		| awk '{ print "[ lint ] " $$0 }'

