FROM python:3.9

WORKDIR /usr/src/app

COPY requirements.txt ./
COPY .env ./
COPY assets/config.yaml assets/
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x main.py

CMD [ "python", "main.py" ]