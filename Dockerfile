FROM python:3.11-slim

WORKDIR /code2

# Preinstall pip dependencies
COPY ./requirements.txt /code2/requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY ./app /code2/app

EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]






