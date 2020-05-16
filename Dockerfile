FROM python:3.7
EXPOSE 8501
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt
COPY networkx-metis/ ./networkx-metis/
RUN cd networkx-metis/ && python setup.py install 
COPY . .
CMD ["streamlit", "run", "app.py"]
