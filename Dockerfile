#Dockerfile, Image, Container

FROM python:3.8

ADD csv_handler.py .

RUN pip install boto3 pandas sys

CMD ["python", "./csv_handler.py"]