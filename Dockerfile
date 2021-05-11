FROM python:3-alpine
LABEL maintainer="timofey.marenko@gmail.com"
COPY . /app
WORKDIR /app
ENV FLASK_APP="quizzer"
RUN pip3 install --no-cache -r requirements.txt
CMD [ "python3", "run_flask.py"]
