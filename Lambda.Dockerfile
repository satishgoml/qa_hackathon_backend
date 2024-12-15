FROM public.ecr.aws/lambda/python:3.10

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry && \
    poetry config virtualenvs.create false

# Copy poetry files
COPY ./pyproject.toml ./poetry.lock* ${LAMBDA_TASK_ROOT}/

# Install dependencies
RUN poetry install --no-root --only main

# Copy function code
COPY ./app ${LAMBDA_TASK_ROOT}/app
COPY ./.env  ${LAMBDA_TASK_ROOT}/.env

# Set Python path
ENV PYTHONPATH=${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD [ "app.main.handler" ]
