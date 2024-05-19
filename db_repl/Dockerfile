FROM postgres:14-alpine

COPY init.sh /docker-entrypoint-initdb.d/init.sh
RUN chown postgres:postgres /docker-entrypoint-initdb.d
RUN chown -R postgres:postgres /usr/local/share/postgresql
RUN chmod +x /docker-entrypoint-initdb.d/init.sh

RUN echo "logging_collector = on" >> /usr/local/share/postgresql/postgresql.conf.sample

RUN echo "listen_addresses = '*'" >> /usr/local/share/postgresql/postgresql.conf.sample 

RUN mkdir -p /var/log/postgresql
RUN touch /var/log/postgresql/postgresql-15-main.log
RUN chown -R postgres:postgres /var

