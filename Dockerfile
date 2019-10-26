FROM python:3.7-stretch
COPY . /app
WORKDIR /app
RUN pip install -r req.txt
CMD ["python", "main.py"]