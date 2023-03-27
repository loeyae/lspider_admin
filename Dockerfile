FROM docker.dev.loeyae.com/library/spider-base:7
WORKDIR /app

COPY image_files/ /

COPY . .

RUN mkdir -p /tmp/supervisor && \
    chmod 777 -R /tmp/supervisor && \
    chmod 755 /usr/local/bin/entrypoint /usr/local/bin/init-spider && \
    PATH="/usr/local/bin:$PATH" && \
    export PATH

RUN pip config set global.index-url https://nexus.dev.loeyae.com/repository/pypi-group/simple && \
    python setup.py sdist && \
    pip install dist/cdspider_admin-0.1.tar.gz

ENTRYPOINT ["entrypoint"]
CMD ["supervisord-conf"]