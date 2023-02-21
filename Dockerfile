FROM python:3.10-slim
RUN mkdir /hubsim
COPY hubsim/ hubsim/
COPY pyproject.toml /hubsim
WORKDIR /hubsim
ENV PYTHONPATH=${PYTHONPATH}:${PWD}
RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --only main

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "run.py", "--server.port=8501", "--server.address=0.0.0.0"]
