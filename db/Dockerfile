FROM postgres:14-alpine

ADD init.sql /init.sql
COPY init.sql /docker-entrypoint-initdb.d/init.sql

RUN apk add gettext

RUN mkdir -p /var/log/postgresql
RUN touch /var/log/postgresql/postgresql-15-main.log
RUN chown -R postgres:postgres /var

RUN echo "logging_collector = on" >> /usr/local/share/postgresql/postgresql.conf.sample
RUN echo "log_directory = '/var/log/postgresql'" >> /usr/local/share/postgresql/postgresql.conf.sample
RUN echo "log_filename = 'postgresql-15-main.log'" >> /usr/local/share/postgresql/postgresql.conf.sample

RUN mkdir -p /oracle/pg_data/archive
RUN chown -R postgres:postgres /oracle

RUN echo "listen_addresses = '*'" >> /usr/local/share/postgresql/postgresql.conf.sample 
#RUN echo "port = ${DB_PORT}" >> /usr/local/share/postgresql/postgresql.conf.sample
RUN echo "wal_level = replica" >> /usr/local/share/postgresql/postgresql.conf.sample
RUN echo "max_wal_senders=10" >> /usr/local/share/postgresql/postgresql.conf.sample
RUN echo "archive_mode=on" >> /usr/local/share/postgresql/postgresql.conf.sample
RUN echo "archive_command='cp %p /oracle/pg_data/archive/%f'" >> /usr/local/share/postgresql/postgresql.conf.sample
RUN echo "wal_log_hints=on" >> /usr/local/share/postgresql/postgresql.conf.sample
RUN echo "log_replication_commands=on" >> /usr/local/share/postgresql/postgresql.conf.sample

COPY init.sh /docker-entrypoint-initdb.d/init.sh
RUN chown postgres:postgres /docker-entrypoint-initdb.d
RUN chown -R postgres:postgres /usr/local/share/postgresql
RUN chmod +x /docker-entrypoint-initdb.d/init.sh

RUN chown postgres:postgres /docker-entrypoint-initdb.d/init.sql
RUN chmod 644 /docker-entrypoint-initdb.d/init.sql
