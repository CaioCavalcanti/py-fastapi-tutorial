# py-fastapi-tutorial
API developed with Python using FastAPI, based on its user guide tutorial

- [py-fastapi-tutorial](#py-fastapi-tutorial)
    - [Requirements](#requirements)
  - [Running it](#running-it)

### Requirements
- Python 3.8+

## Running it
- Create a new virtual environment
```sh
$ python -m venv .venv
```

- Activate virtual environment
```sh
$ .venv\Scripts\activate
```

- Install requirements
```sh
(.venv) $ pip install -r requirements-dev.txt
```

- Start API
```sh
(.venv) $ uvicorn main:app --reload
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [3548] using statreload
INFO:     Started server process [12188]
INFO:     Waiting for application startup.
INFO:     Application startup complete.   
```