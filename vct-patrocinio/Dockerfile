# Receta de la imagen: la misma corre en el salón y en Render.
FROM python:3.12-slim

# Usuario sin privilegios: el servicio no necesita ser root.
RUN useradd -m -u 1000 usuario
USER usuario
ENV PATH=/home/usuario/.local/bin:$PATH
WORKDIR /home/usuario/app

# Primero las dependencias: esta capa se reutiliza si solo cambia el código.
COPY --chown=usuario requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=usuario . .

# Puerto: 8765 por defecto; Render lo reemplaza con su propia variable PORT (10000).
ENV PORT=8765
EXPOSE 8765
# sh -c cambia $PORT por su valor al arrancar; exec deja a Solara como el proceso principal.
CMD ["sh", "-c", "exec solara run app.py --host=0.0.0.0 --port=$PORT --production"]
