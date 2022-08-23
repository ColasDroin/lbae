
## Use and deployment

The app is compatible with Python 3.8 and above. Required packages can be installed with: 

```pip install -r requirements.txt```

The app can be run locally using the command:

```python main.py```

Or it can be deployed on a server with Gunicorn (here with 4 threads and only 1 worker to avoid using too much RAM):

```gunicorn main:server -b:8077 --worker-class gevent --threads 4 --workers=1```

In both cases, it will be accesible with a browser at http://localhost:8077.

