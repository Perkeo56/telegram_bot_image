 syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN apt-get update
RUN apt-get upgrade
RUN apt-get install build-essential -y
RUN apt-get install python3-dev -y
RUN pip3 install -r requirements.txt

COPY . .
RUN chmod +x main.py

#CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
#CMD ["python", "main.py"]
#CMD python3 main.py
#ENTRYPOINT ["python3"]
#CMD ["/app/main.py"]
CMD ["python3", "/app/main.py"]
