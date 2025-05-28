FROM python:3.9.6-alpine

RUN apk add --update --virtual \
        build-deps gcc python3-dev musl-dev \
        build-base \
        jpeg-dev \
        zlib-dev \
        libxml2 \
        libxml2-dev \
        libxslt \
        libxslt-dev \
        linux-headers \
        py3-cffi \
        py3-cryptography \
        gettext \
        libffi-dev \
        openssl-dev \
        bash \
        git \
        tzdata \
        postgresql-dev \
        stress-ng

ENV PYTHONUNBUFFERED=1
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
ENV TZ=Asia/Ho_Chi_Minh
ENV DJANGO_SETTINGS_MODULE=django_task_queue.settings
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /code

COPY ./requirements.txt .

RUN python -m pip install --upgrade cython
RUN python -m pip install cryptography
RUN python -m pip install -r requirements.txt

RUN mkdir /config

# COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

