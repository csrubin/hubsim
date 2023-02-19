FROM python:3.10
RUN mkdir /hubsim
COPY /hubsim /hubsim
COPY pyproject.toml /hubsim
WORKDIR /hubsim
ENV PYTHONPATH=${PYTHONPATH}:${PWD}
RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev
