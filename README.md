# File storge project
## Purpose
* Store files in centralized project
* Web/application access to files
* Different backend storages (disk, s3, etc..)
* Share/public upload directories

## Status
Deep alpha version.

## Running project in development
Global requirements:
```
python 3.6+
nodejs 12+
```
Installing and running:

* Backend:
```
# Setting up environment, run in project root directory
python3 -m venv ./env
source ./env/bin/activate
pip install -r requirements.txt

cd app

# Create super user
python ./manage.py createsuperuser

# Running dev server
python ./manage.py runserver
```

* Frontend:
```
# Setting up environment, run in frontend directory
cd frontend
npm install

# running dev build
npm run watch
```


# Testing
```
# Set up environment
pip install -r dev-requirements.txt

# Running tests
make test

# Coverage
make coverage
```
