FROM python:3.9-slim
WORKDIR /app
COPY static /app/static
COPY . .
RUN pip install flask requests
CMD ["python", "app.py"]
