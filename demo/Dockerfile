FROM python:3.9-alpine

# set work directory
WORKDIR /demo

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .

RUN python manage.py migrate 
# RUN python manage.py collectstatic -c --no-input 
# CMD daphne demo.asgi:application --bind 0.0.0.0 --port $PORT
CMD python manage.py runserver 0.0.0.0:$PORT
