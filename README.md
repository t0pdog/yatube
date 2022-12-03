# The Yatube project
Yatube is a social network for writers. It gives users the ability to create an account, post publications, follow their favorite authors, and tag posts they like.

The following features are implemented in the project:
* Registration
* Create a post
* Recover password
* Comment on posts
* Subscribe to the author
* Pagination of pages
* Access control

## The technology stack is available in requirements.txt

## How to run the project:

Clone the repository and change into it on the command line:
```
git clone https://github.com/t0pdog/yatube.git
cd yatube
```

Create and activate virtual environment:
```
python -m venv venv
. venv/Scripts/activate
```

Install dependencies from requirements.txt file:
```
pip install -r requirements.txt
```

Run migrations:
```
python manage.py migrate
```

Run project:
```
python manage.py runserver
```

Project is available at:
```
http://127.0.0.1:8000/
```