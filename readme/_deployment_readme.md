
## Use and deployment

The app is compatible with Python 3.8 and is guaranteed to work until version 3.9.5. 

Required packages can be installed with: 

```pip install -r requirements.txt```

Warning: The Dash version version MUST BE <=2.5.1, otherwise, bug may be present with long_callbacks.

The app can be run locally using the command:

```python main.py```

The first time the app is executed, if the shelve database (in the folder data/app_data/) doesn't exist, it will have to be built from scratch. This means that all the app precomputations will take place, which can take ~1 day of computation.

The app can be deployed on a server with Gunicorn (here with 4 threads and only 1 worker to avoid using too much RAM):

```gunicorn main:server -b:8077 --worker-class gevent --threads 4 --workers=1```

In both cases, it will be accesible with a browser at http://localhost:8077.

