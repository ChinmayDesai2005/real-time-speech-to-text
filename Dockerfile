FROM python:3.11

# copy the requirements file into the image
COPY ./requirements.txt /app/requirements.txt

# switch working directory
WORKDIR /app

# install the dependencies and packages in the requirements file
RUN pip install -r requirements.txt

# copy every content from the local file to the image
COPY . /app

# configure the container to run in an executed manner
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg

EXPOSE 5555


ENV GOOGLE_APPLICATION_CREDENTIALS=credentials.json

ENTRYPOINT [ "python" ]

CMD ["app.py" ]
