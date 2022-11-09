# File storge project
## Purpose
* Store files in centralized project
* Web/application access to files
* Different backend storages (disk, s3, etc..)
* Share/public upload directories

## Status
Deep alpha version.

## Running project
### Global requirements:
```
python 3.6+
pillow
nodejs 12+
```

### Installing and running:

#### Dependencies
`Pillow` is imaging library. Can be installed via package
(`apt install python3-pil` in ubuntu/debian) or
pip (`pip install Pillow`, but it requires `python3-dev`).
See https://pillow.readthedocs.io/en/stable/installation.html for details

##### Backend:
```
# Setting up environment, run in project root directory
python3 -m venv ./env --system-site-packages
source ./env/bin/activate
pip install -r requirements.txt

cd app

# Create super user
python ./manage.py createsuperuser

# Running dev server
python ./manage.py runserver

# Running background celery worker
celery -A app worker -l INFO
```

##### Frontend:
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
