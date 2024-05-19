#!/bin/sh

echo "port = ${DB_REPL_PORT}" >> /usr/local/share/postgresql/postgresql.conf.sample

cat /docker-entrypoint-initdb.d/init.sh
