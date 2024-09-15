FROM python:3.7

WORKDIR /opt/MyAnimeBot

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R 0:0 /opt/MyAnimeBot && chmod -R g+rw /opt/MyAnimeBot

CMD ["python", "myanimebot.py"]
