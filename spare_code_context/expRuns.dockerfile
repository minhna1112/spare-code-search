FROM spare-code-context:latest

RUN pip install --no-cache-dir wandb matplotlib pandas

COPY src/ /app/src/

WORKDIR /app/src
CMD [ "python", "./exps.py" ]