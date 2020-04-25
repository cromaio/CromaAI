# Proceso de instalación y configuración de Croma Archive Intelligence (Croma AI)

## Introducción

Croma es un servicio que analiza tus noticias utilizando modelos machine learning para recomendar noticias similares. También identifica entidades mencionadas en tus textos como personas, organizaciones, lugares y más. Todo el procedimiento de entrenamiento es independiente de tu CMS y puede ser integrado luego de manera muy simple a través de una API basada en JSON.

Este software, su API y el entrenamiento de modelos pudieron realizarse gracias a un aporte de Google a través de su iniciativa Google News Initiative y el equipo de Croma Inc. 


## Descripción general
Croma AI fue desarrollado por completo por Croma Inc para facilitar el acceso de los medios de comunicación de habla hispana a herramientas de machine learning en idioma español. Con años de experiencia en este entorno conocemos la limitaciones y la dificultad de implementar este tipo de tecnología en redacciones grandes, medianas y mucho más en las pequeñas. Por eso desarrollamos Croma AI como una manera de allanar la barrera de entrada a los desarrolladores y medios que quieran experimentar con estas herramientas dentro de sus redacciones.El uso de este software es exclusivamente gratuito y de libre uso para todo medio de comunicación de América Latina que quiera incorporar machine learnign de manera sencilla a su operación diaria.

## Beneficios 
Estos son los beneficios que puede obtener su medio utilizando esta plataforma:
- Realizar un entrenamiento de machine learning de todo su archivo histórico sin necesidad de programar una sola línea de código. Todo lo que necesitas está incluido en este paquete.
- Incorporar noticias relacionadas en su artículos a través de una simple llamada a una API. Esta relaciones no se dan por simples keywords o categorías, sino que utiliza una comprensión de la totalidad del texto para recomendar noticias similares, por más que no compartan los mismos términos.
- Identificar personas, lugares, organizaciones y keywords mencionadas en sus textos. Esto permite la automatización de la generación de tags que pueden ser fácilmente utilizados para potenciar sus esfuerzos de SEO y taggeo de artículos, nuevos e históricos.
- Ofrecer un sistema de búsqueda de artículos basado en relevancia real de sus contenidos. Puede ofrecer búsquedas predictivas y relaciones por entidades en la página de resultados.
- Cualquier otra tarea que se pueda facilitar teniendo su archivo completo y actualizado indexado y accesible vía API.


## Requisitos
El software se debe instalar completamente en un servidor privado de su propiedad.

# Indicaciones para el proceso de instalación
 
## Instalación Anaconda
CromaAI utiliza conda como método de instalación por lo que sugerimos utilizar Anaconda para su instalación
https://anaconda.org/
Bajarlo de la página e instalarlo siguiendo las instrucciones dependiendo de su sistema operativo
      
  Instalar CromaAI
```
$ git clone git@github.com:cromaio/CromaAI.git 
$ cd CromaAI
```
         
## Creación de entorno
Ejecutar los siguientes comandos:
```bash
$ conda env create -f environment.yml 
```
La salida será algo asi:
```bash
Collecting package metadata (repodata.json): done
Solving environment: done

Downloading and Extracting Packages
wrapt-1.10.11        | 41 KB     | ###################################################################### | 100% 
msgpack-python-0.6.1 | 86 KB     | ###################################################################### | 100% 
sqlite-3.31.1        | 2.4 MB    | ###################################################################### | 100% 
libffi-3.2.1         | 43 KB     | ###################################################################### | 100% 
murmurhash-1.0.2     | 24 KB     | ###################################################################### | 100% 
cymem-2.0.2          | 30 KB     | ###################################################################### | 100% 
preshed-2.0.1        | 63 KB     | ###################################################################### | 100% 
regex-2020.4.4       | 357 KB    | ###################################################################### | 100% 
msgpack-numpy-0.4.3. | 14 KB     | ###################################################################### | 100% 
spacy-2.0.16         | 47.3 MB   | ###################################################################### | 100% 
thinc-6.12.1         | 1.3 MB    | ###################################################################### | 100% 
openssl-1.1.1g       | 3.4 MB    | ###################################################################### | 100% 
Preparing transaction: done
Verifying transaction: done
Executing transaction: done

#
# To activate this environment, use
#
#     $ conda activate cromaAI
#
# To deactivate an active environment, use
#
#     $ conda deactivate

```

Luego de la instalación activar el entorno:
```bash
$ conda activate cromaAI
```
Por defecto crea el entorno cromaAI. Si quiere modificarlo puede hacerlo editando el archivo environment.yml situado en la raiz y volviendo a correr el primer comando
Si quiere instalar faiss con GPU debe modificar la linea de config del yml `pytorch::faiss-cpu` por `pytorch::faiss-gpu`
                    
## BASE DE DATOS (mongodb) - Archivo de configuración
CromaAI utiliza mongodb como base de datos. En esta demo vamos a simplemente ejecutar un deamon de prueba. En caso de ponerla en producción [aca](https://www.mongodb.com/blog/post/12-tips-going-production-mongodb) hay algunas recomendaciones.

Abriendo `CromaAI/config.py` puede editar la configuración o ejecute lo siguiente para verlo
```bash
cat ./CromaAI/config.py.sample
```

```js
database = {
   'db_name': 'cromaAIdb',
   'host': 'localhost',
   'port': 27018
   }
```
 
## Correr mongo
Seleccione el puerto y el path que se ajuste a sus necesidades Ejecutar:
```bash
$ mkdir data
$ cd data
$ mkdir db
$ cd ..
$ nohup mongod --port 27018 --dbpath ./data/db/ &
$ cat nohup
```
El primer parámetro (port) debe coincidir con el del archivo config
El segundo parámetro es la carpeta donde se guardan los datos de la base de datos
```bash
La salida:
2020-04-22T23:21:44.332-0300 I  CONTROL  [main] Automatically disabling TLS 1.0, to force-enable TLS 1.0 specify --sslDisabledProtocols 'none'
2020-04-22T23:21:44.340-0300 I  CONTROL  [initandlisten] MongoDB starting : pid=53305 port=27018 dbpath=./data/db/ 64-bit host=Julians-MacBook-Pro-2.local
2020-04-22T23:21:44.340-0300 I  CONTROL  [initandlisten] db version v4.2.2
2020-04-22T23:21:44.340-0300 I  CONTROL  [initandlisten] git version: a0bbbff6ada159e19298d37946ac8dc4b497eadf
2020-04-22T23:21:44.340-0300 I  CONTROL  [initandlisten] allocator: system
2020-04-22T23:21:44.340-0300 I  CONTROL  [initandlisten] modules: none
2020-04-22T23:21:44.340-0300 I  CONTROL  [initandlisten] build environment:
2020-04-22T23:21:44.340-0300 I  CONTROL  [initandlisten]     distarch: x86_64
2020-04-22T23:21:44.340-0300 I  CONTROL  [initandlisten]     target_arch: x86_64
2020-04-22T23:21:44.341-0300 I  CONTROL  [initandlisten] options: { net: { port: 27018 }, storage: { dbPath: "./data/db/" } }
2020-04-22T23:21:44.343-0300 I  STORAGE  [initandlisten] wiredtiger_open config: create,cache_size=3584M,cache_overflow=(file_max=0M),session_max=33000,eviction=(threads_min=4,threads_max=4),config_base=false,statistics=(fast),log=(enabled=true,archive=true,path=journal,compressor=snappy),file_manager=(close_idle_time=100000,close_scan_interval=10,close_handle_minimum=250),statistics_log=(wait=0),verbose=[recovery_progress,checkpoint_progress],
2020-04-22T23:21:45.779-0300 I  STORAGE  [initandlisten] WiredTiger message [1587608505:779010][53305:0x10c3d05c0], txn-recover: Set global recovery timestamp: (0,0)
2020-04-22T23:21:46.295-0300 I  RECOVERY [initandlisten] WiredTiger recoveryTimestamp. Ts: Timestamp(0, 0)
2020-04-22T23:21:46.992-0300 I  STORAGE  [initandlisten] Timestamp monitor starting
2020-04-22T23:21:46.993-0300 I  CONTROL  [initandlisten] 
2020-04-22T23:21:46.993-0300 I  CONTROL  [initandlisten] ** WARNING: Access control is not enabled for the database.
2020-04-22T23:21:46.993-0300 I  CONTROL  [initandlisten] **          Read and write access to data and configuration is unrestricted.
2020-04-22T23:21:46.993-0300 I  CONTROL  [initandlisten] 
2020-04-22T23:21:46.993-0300 I  CONTROL  [initandlisten] ** WARNING: This server is bound to localhost.
2020-04-22T23:21:46.993-0300 I  CONTROL  [initandlisten] **          Remote systems will be unable to connect to this server. 
2020-04-22T23:21:46.993-0300 I  CONTROL  [initandlisten] **          Start the server with --bind_ip <address> to specify which IP 
2020-04-22T23:21:46.993-0300 I  CONTROL  [initandlisten] **          addresses it should serve responses from, or with --bind_ip_all to
2020-04-22T23:21:46.993-0300 I  CONTROL  [initandlisten] **          bind to all interfaces. If this behavior is desired, start the
2020-04-22T23:21:46.993-0300 I  CONTROL  [initandlisten] **          server with --bind_ip 127.0.0.1 to disable this warning.
2020-04-22T23:21:46.995-0300 I  CONTROL  [initandlisten] 
2020-04-22T23:21:46.996-0300 I  CONTROL  [initandlisten] 
2020-04-22T23:21:46.996-0300 I  CONTROL  [initandlisten] ** WARNING: soft rlimits too low. Number of files is 256, should be at least 1000
2020-04-22T23:21:47.020-0300 I  STORAGE  [initandlisten] createCollection: admin.system.version with provided UUID: b3c050c9-0c07-498a-99a3-44d6211d6b8a and options: { uuid: UUID("b3c050c9-0c07-498a-99a3-44d6211d6b8a") }
```
Verifique que no existan errores

## Archivo de configuración - Publicaciones default
Aquí puede modificar y agregar su medio. Hay un ejemplo aca: CromaAI/config.py.sample
```bash
cat ./CromaAI/config.py.sample
```
```python
# Si date_after y date_before estan en None, trae todo - Esto puede tardar un tiempo -
fetching_config = {
    'publication': 'Redaccion',
    'date_after':  '2020-01-01', #None, 
    'date_before': '2020-04-22', #None
}

active_publication = 'Redaccion'

publications = [
    {
        "api_url": 'https://cnnespanol.cnn.com/wp-json/wp/v2/',
        "name": 'CNN Esp',
        "fetch_method": 'wordpress',
        "location": 'USA', 
        "url": 'https://cnnespanol.cnn.com'
    },
    {
        "api_url": 'https://www.redaccion.com.ar/wp-json/wp/v2/',
        "name": 'Redaccion',
        "fetch_method": 'wordpress',
        "location": 'Argentina', 
        "url": 'https://www.redaccion.com.ar'
    }
]
```

## Buscar artículos y guardarlos en db
Asegurarse de tener un archivo de configuración correcto: `config.py` Hay un ejemplo: config.py.sample
Ejecutar:
```
$ cp ./CromaAI/config.py.sample ./CromaAI/config.py
```
Luego, para traer los archivos ejecutar
```bash
$ python ./CromaAI/fetch_articles.py
```
Esto traerá los archivos del medio definido en active_publication
```bash
config.py found
Verificando publicaciones
Publication creada: CNN Esp
Publication creada: Redaccion
Total de publicaciones en la db: 2
- CNN Esp
- Redaccion
#################################
url ro fetch: https://www.redaccion.com.ar/wp-json/wp/v2/
No articles
Page: 6/6 - https://www.redaccion.com.ar/wp-json/wp/v2/posts?page=6&per_page=50&orderby=date&order=asc&after=2019-11-01T00:00:00&before=2019-12-30T00:00:00(cromaAI) 
```

## Bajar modelos de ejemplo
https://drive.google.com/file/d/1z2iaQxX08-hyNzpcKgdihRnAy0mFPWVp/view?usp=sharing
Copiarlo en carpeta `CromaAI/models` Y descomprimirlo
Si trabaja con linux puede hacerlo de la siguiente forma:
```bash
$ cd CromaAI/
$ mkdir models
$ cd models
$ wget https://croma.ai/models/models_demo.zip
$ unzip models_demo.zip
$ cd ..
```

## Entrenamiento faiss
Copiar el archivo de configuración de entrenamiento:
```bash
$ cp config_train.py.sample config_train.py
$ cat config_train.py
```
Dentro del archivo de `config_train.py` verificar que este seteado asi:
```python
model_name = 'redaccion_2020'
spacy_model = 'models/redaccion_2020/model-azure-aws-50k'
# Si word2vect_model es None, lo busca en la carpeta model_name/w2vect
# Si es un path a archivo, directamente enabled_processes.w2v no lo compara
word2vect_model = 'ML_models/w2vect_2.wv'
publication_name = 'Redaccion'
chunk_size = 100

enabled_processes = {
    "tokenize_articles": True,
    "vectorizers": True,
    "w2v": False,
    "faiss": True
}
```
Ejecutar:
```bash
$ python train_models.py
```

Esto generara los tokens de los articulos y armara los vectorizers junto con la base de faiss

```bash
tokenizing articles ...
Found 0 already tokenized articles
Publication object
Total number to tokenize: 289
199/289 
models/redaccion_2020/training_data/content_1.npy saved!
288/289 
models/redaccion_2020/training_data/content_2.npy saved!
Training vectorizers ...
2 - 89 - models/redaccion_2020/training_data/all_2.npyed
1 finished!
Matrix size: (289, 27791)
Saved to: models/redaccion_2020/vectorizers/count_vectorizer-max_df_1.0-min_df_1.pickle
Training faiss ...
using: models/redaccion_2020/w2vect/w2vect_2.wv
Articulo: 288ls/redaccion_2020/training_data/all_2.npyed
1 finished!
Faiss tenía 0 vectores, se agregaron 289 y se intentaron agregar 0 que ya estaban
```

# Testeo API
 
## Correr API
Dentro de la carpeta CromaAI
```bash
$ python3 FlaskAPI.py -p 5000 -h localhost
```
Esto corre un servidor en el puerto 5000 por defecto. Puede cambiar el host y el port según sus necesidades
   
### Verficar API - /api/v1/articles
Si esta trabajando con linux puede instalar curl
```bash
sudo apt install curl
```

Escribir en el browser:
```
http://localhost:5000/api/v1/articles
```
o desde la linead de comando:

```
$ curl --location --request GET 'http://localhost:5000/api/v1/articles'
```

El resultado debería ser algo parecido a lo siguiente:
```js
{ "articles_page": [ {"_id": {"$oid": "5e9e1d65970a1cca9518671c"}, 
      "author": ["18"], 
      "publication": {
        "$oid": "5ea0fceafc6ebaf443054ad4"
      }, 
      "publish_date": {
        "$date": 1587340800000
      }, 
      "pub_art_id": "79884", 
      "summary": "<p>La pandemia gatilla …”
      "text": "Esta es la foto del COVID-19 esta ", 
      "title": "GPS PM del lunes 20 de abril del 2020", 
      "url": "https://www.redaccion.com.ar/gps-pm-del-lunes-20-de-abril-del-2020/"
    }, ...
    ]
}
```

### Verficar API - /api/v1/article
Notar que en la respuesta del articulo anterior hay dos ids:  ```"$oid": "5ea0fceafc6ebaf443054ad4"``` y ```"pub_art_id": "79884"```. Cuando se pide un articulo se lo puede hacer por el primero como `id` o por el segundo como `cmdid`
El primero es el id en la base de CromaAI mongo, y el segundo es el id original de la base donde se obtuvo el articulo

Escribir en el browser:
```
http://localhost:5000/api/v1/article?id=5ea0fceafc6ebaf443054ad4
```
o
```
http://localhost:5000/api/v1/article?cmsid=79884
```
o desde la linead de comando:

```
$ curl --location --request GET 'http://localhost:5000/api/v1/article?id=5ea0fceafc6ebaf443054ad4'
```
o
```
curl --location --request GET 'http://localhost:5000/api/v1/article?cmsid=79884'
```

El resultado debería ser algo parecido a lo siguiente:
```js
{ "article: [{"_id": {"$oid": "5e9e1d65970a1cca9518671c"}, 
      "author": ["18"], 
      "publication": {
        "$oid": "5e9e16903993318678a548ad"
      }, 
      "publish_date": {
        "$date": 1587340800000
      }, 
      "summary": "<p>La pandemia gatilla …”
      "text": "Esta es la foto del COVID-19 esta ", 
      "title": "GPS PM del lunes 20 de abril del 2020", 
      "url": "https://www.redaccion.com.ar/gps-pm-del-lunes-20-de-abril-del-2020/"
    }
}

```

### Verficar API - /api/v1/article_entities

Obtener el id del primer articulo, en nuestro ejemplo: 5e9e1d65970a1cca9518671c
Y colocarlo en el pedido para verificar funcionamiento

Escribir en el browser:
```
http://localhost:5000/api/v1/article_entities?id=5ea0fceafc6ebaf443054ad4&cloud=spacy
```
o desde la linead de comando:

```bash
$ curl --location --request GET 'http://localhost:5000/api/v1/article_entities?id=5ea0fceafc6ebaf443054ad4&cloud=spacy'
```
o
```bash
curl --location --request GET 'http://localhost:5000/api/v1/article_entities?cmsid=79884&cloud=spacy'
```

### Verificar API - /api/v1/w2v/related

```bash
$ curl --location --request GET 'http://localhost:5000/api/v1/related?id=5ea0fceafc6ebaf443054ad4'
```
o
```bash
$ curl --location --request GET 'http://localhost:5000/api/v1/related?cmsid=79884'
```
```js
{
  "related_articles": [
    {
      "article_id": "5e9e1d65970a1cca9518671c", 
      "similarity": 1.0
    }, 
    ...,
    {
      "article_id": "5e9e1d5b970a1cca95186662", 
      "similarity": 0.8513200283050537
    }
  ]
}
```

### Verificar API - /api/v1/analyzer/text
Ejecutar desde la linead de comando:
```bash
$ curl --location --request POST 'http://localhost:5000/api/v1/analyzer/text' \
--header 'Content-Type: application/json' \
--data-raw '"Cristina Kirchner se reunio con Mauricio Macri en la Casa Rosada"'
```
El resultada debería ser algo similar a esto:
```js
{
  "doc": {
    "ents": [
      {
        "end": 17, 
        "label": "PER", 
        "start": 0
      }, 
      {
        "end": 46, 
        "label": "PER", 
        "start": 32
      }, 
      {
        "end": 64, 
        "label": "ORG", 
        "start": 53
      }
    ], 
    "text": "Cristina Kirchner se reunio con Mauricio Macri en la Casa Rosada", 
    "tokens": [
      {
        "end": 8, 
        "id": 0, 
        "start": 0
      }, ... 
      {
        "end": 64, 
        "id": 10, 
        "start": 58
      }
    ]
  }, 
  "html": "<div class=\"entities\" style=\"line-height: 2.5; direction: ltr\"><mark class=\"entity\" style=\"background: #ddd; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;\">Cristina Kirchner<span style=\"font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; text-transform: uppercase; vertical-align: middle; margin-left: 0.5rem\">PER</span></mark> se reunio con <mark class=\"entity\" style=\"background: #ddd; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;\">Mauricio Macri<span style=\"font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; text-transform: uppercase; vertical-align: middle; margin-left: 0.5rem\">PER</span></mark> en la <mark class=\"entity\" style=\"background: #7aecec; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;\">Casa Rosada<span style=\"font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; text-transform: uppercase; vertical-align: middle; margin-left: 0.5rem\">ORG</span></mark></div>", 
  "related_articles": [
    {
      "article_id": "5e9e1ce2970a1cca95185cde", 
      "similarity": 0.36494454741477966
    }, ... ,
    {
      "article_id": "5e9e1d25970a1cca95186237", 
      "similarity": 0.21402746438980103
    }
  ]
}
```
    
### Verificar API - /api/v1/w2v/autocompete
```
$ curl --location --request POST 'localhost:5000/api/v1/w2v/autocomplete' \
--header 'Content-Type: application/json; charset=UTF-8' \
--data-raw '"Mau"'
```
```js
{
  "words": [
    "Mauricio Macri", 
    "Mauricio macri", 
    "Mauricio", 
    "Mauricio ) Macri", 
    "Mauricio Claver", 
    "Mauro", 
    "Mauricio !", 
    "Maurice Closs", 
    "Mauro Viale", 
    "Mauro Icardi", 
    "Maure Inmobiliaria"
  ]
}
```

 
### Verificar API - /api/v1/w2v/similar
```bash
$ curl --location --request POST 'localhost:5000/api/v1/w2v/similar' \
--header 'Content-Type: application/json' \
--data-raw '{
    "word": "kirchnerismo"
}'
```

```js
{
  "similar_words": [
    {
      "similarity": 0.766370952129364, 
      "word": "peronismo"
    }, 
    {
      "similarity": 0.6919558644294739, 
      "word": "oficialismo"
    }, 
    ...
  ]
}
```



# Entrenamiento de Modelos
 
## Modelos y técnicas
- NER
- word2Vect - TFIDF
- faiss
 
## NER
Croma provee un modelo pre-entrenado con 50k artículos de medios periodísticos. Los datos de entrenamiento se obtuvieron por comparación de las APIs de AZURE, AWS y GCP y la verificación de personas. El modelo es parte pública de CromaAI y se utiliza a través de Spacy
 
## w2v
Con la tokenización utilizada con el modelo de NER se entrena un modelo de w2v en formato de la librería gensim. Este modelo se utiliza después para relacionar artículos, búsqueda de palabras similares y autocomplete. CromaAI proporciona un modelo pre-entrenado. Si quiere reentrenar, tiene que poner en `True` la variable `w2v` en el `config_train.cfg`
 
##  TFIDF
Se utiliza esta técnica para mejorar los resultados del modelo w2v en la búsqueda de artículos relacionados.
 
##  FAISS
Esta librería se utiliza para realizar las búsquedas de artículos relacionados de manera eficiente
 
##  Recomendaciones para el entrenamiento
Se recomienda utilizar tanto el modelo de spacy para la tokenización como el modelo pre-entrenado de w2v. Esto se puede modificar en las siguientes variables del archivo de configuración: spacy_model, word2vect_model
 
##   Archivo de configuración de training - congif_train.py
```python
database = {
    'db_name': 'cromaAIdb',
    'host': 'localhost',
    'port': 27018
    }

model_name = 'redaccion_2020'
spacy_model = f'models/{model_name}/ner/model-azure-aws-50k'
# Si word2vect_model es None, lo busca en la carpeta model_name/w2vect
# Si es un path a archivo, directamente enabled_processes.w2v no lo compara
word2vect_model = f'models/{model_name}/w2vect/w2vect_2.wv'
publication_name = 'Redaccion'
chunk_size = 100

enabled_processes = {
    "tokenize_articles": True,
    "vectorizers": True,
    "w2v": False,
    "faiss": True
}

vectorizeers_hyperparams = {
    "min_df": 1,
    "max_df": 1.0
}

w2v_hyperparams = {
    "size": 100,
    "epochs": 6,
    "min_count":2, 
    "workers":4, 
}
```
##  Entrenar modelos:
Para entrenar los modelos ejecutar:
```bash
$ python3 train_models.py
```
Recuerde antes revisar el archivo config_train.py
     
 
   
