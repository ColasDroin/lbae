FROM python:3.9.5-slim-buster

LABEL maintainer "Colas Droin, colas.droin@gmail.com"

# set working directory in container
WORKDIR /usr/src/app

# Install Python dependencies and Gunicorn and other needed dependencies
RUN apt-get update -y && apt-get install -y gcc
ADD requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
#RUN pip install --no-cache-dir gunicorn
#RUN pip install --no-cache-dir gevent
#RUN pip install --no-cache-dir multiprocess 
#RUN pip install --no-cache-dir diskcache 
#RUN pip install --no-cache-dir psutil

# Bug with Werkzeug
RUN pip install Werkzeug==2.0.0

# Bug with Flask
RUN pip install Flask==2.1.3

# Copy app folder to app folder in container
COPY . /usr/src/app/

# Finally, run gunicorn.
CMD [ "gunicorn", "main:server", "--bind", "0.0.0.0:8050", "--workers=1", "--threads=4", "--worker-class", "gevent" ]

# To build the app, use the commande below:
# docker build -t lbae_app .  

# To run the app, use the command below
# docker run -p 8051:8050 lbae_app
