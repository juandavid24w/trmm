# Arcoteca

Library management software written in Django.

## Deployment

Check the `.env.example` for the required environmental variables, then
check the [Django documentation on
deployment](https://docs.djangoproject.com/en/5.0/howto/deployment/) for
more information. The `requirements.txt` doesn't include database
adapter packages, so you might need to install them separately (e.g.
`psycopg` for postgresql or `mysqlclient` for MySQL/MariaDB). You'll
also need to run [Huey](https://huey.readthedocs.io) in the server.
Check out [their
section](https://huey.readthedocs.io/en/latest/consumer.html#supervisord-and-systemd)
on processor supervisors for ideas on how to deploy it.

### Deployment on debian with Apache

If you have a debian-based distro with ssh already installed and
configured, and you wish to use Apache with `mod_wsgi` as your
production server, you might benefit from the available makefiles.

1. Fill your `.env` file with the desired values. Keep the `SQL_ENGINE`,
   `SQL_HOST` and `SQL_PORT` the same as in the `.env.example` file;
2. Register your hostname and desired target folder in
   `dev/makefile.variables` (check the example in
   `dev/makefile.variables.example`);
3. `$ make configure`
4. `$ make deploy`

