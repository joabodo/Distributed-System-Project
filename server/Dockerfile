FROM python:3.9-slim
WORKDIR /app
COPY app.py .
RUN pip install flask
ENV SERVER_ID="1"
CMD ["python", "app.py"]