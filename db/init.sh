#!/bin/sh

envsubst '${DB_REPL_USER} ${DB_REPL_PASSWORD} ${DB_DATABASE}' </init.sql> /docker-entrypoint-initdb.d/init.sql
#chmod 644 /docker-entrypoint-initdb.d/init.sql

echo "port = ${DB_PORT}" >> /usr/local/share/postgresql/postgresql.conf.sample

cat /docker-entrypoint-initdb.d/init.sql
cat /docker-entrypoint-initdb.d/init.sh

