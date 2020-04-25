#!/bin/bash
eval "$(conda shell.bash hook)"

# Creación de entorno conda
conda env create -f environment.yml 

conda activate cromaAI

# Base de datos
mkdir data
cd data
mkdir db
cd ..
nohup mongod --port 27018 --dbpath ./data/db/ &

# Bajar articulos de ejemplo
cp ./CromaAI/config.py.sample ./CromaAI/config.py
python ./CromaAI/fetch_articles.py

# Bajado de modelos
cd CromaAI/
mkdir models
cd models
wget https://croma.ai/models/models_demo.zip
unzip models_demo.zip
cd ..
cp config_train.py.sample config_train.py

# Entrenamiento
python train_models.py

# Correr API
python FlaskAPI.py -p 5000 -h localhost