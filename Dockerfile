FROM python:3.11
WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requirements.txt

EXPOSE 8000
ENTRYPOINT ["python", "main.py"]
