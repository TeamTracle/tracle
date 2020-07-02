# TRACLE - The open video platform
TRACLE is an upcoming free and open source video platform.
This repository contains the source code for the website.

## Contributing
Feel free to fork and make a pull request for small changes. If you're planning to change more than a couple of lines it's probably better to open an issue first.

Join our [discord server](https://discord.gg/3uSAWTZ)

### Installation (for development)

TRACLE requires Python3 and pip3, if you are running Linux you probably have it already installed, otherwise refer to the documentation of your distribution on how to install it.

First, clone, fork or download this repository.
Open a terminal and change your working directory to the root of the repository, e.g.

```
git clone https://github.com/TeamTracle/tracle.git
cd tracle
```
Next, create a virtual environment and activate it. I recommend [venv](https://docs.python.org/3/library/venv.html), e.g.

```
python3 -m venv .venv
source .venv/bin/activate
```

We use pip-tools to manage the requirements.txt, so install that, too:
```
pip3 install pip-tools
```

Next, install the dependencies from requirements.txt and requirements_dev.txt:
```
pip3 install wheel
pip-sync requirements.txt requirements_dev.txt
```

Create a file called `.env` with the following content:

```
export DEBUG=1
export BUNNYCDN_ENABLED=0
export INSTALLED_APPS="debug_toolbar" # optional
```

Setup the database:

```
./manage.py migrate
./manage.py loaddata backend/fixtures/categories.json
```

You can run a local development server using the following command:

```
./manage.py runserver
```

Autoprefixer is run only on deployment or when DEBUG is set to false. You'll need npm to install these node modules:

```
npm install -g postcss-cli autoprefixer
```

### Project structure

- api/
REST based api for ajax calls
- backend/
Models, Queries, Everything that could be shared across multiple frontends
- tracle/
The django project folder
- web/
html5 frontend (including (s)css and javascript)
- .env
Environment variables, used by tracle/settings,py

