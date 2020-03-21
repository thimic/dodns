FROM python:3.7-alpine

RUN apk update && apk add gcc musl-dev

WORKDIR /usr/src/dodns

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY dodns ./dodns

ENV PYTHONPATH "${PYTONPATH}:/user/src/dodns"

CMD [ "python", "./dodns/main.py" ]
