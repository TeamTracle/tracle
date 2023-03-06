# TRACLE - The open video platform
TRACLE is a free and open source video platform.

This repository contains the source code for the website.

# Contributing
Feel free to fork and make a pull request for small changes. If you're planning to change more than a couple of lines it's probably better to open an issue first.

Join our [discord server](https://discord.gg/gKatcJ8)

# Installation (for development)
## Using Docker (**recommended**)
First, clone, fork or download this repository.
Open a terminal and change your working directory to the root of the repository, e.g.

```
git clone https://github.com/TeamTracle/tracle.git
cd tracle
```

Copy `envs/local.env.example` to `envs/local.env`
```
cp envs/local.env.example envs/local.env
```

Use docker-compose to build the image and start the services
```
docker-compose -f local.yml up --build -d
```

Setup the database:

```
docker-compose -f local.yml exec django python manage.py loaddata backend/fixtures/categories.json
```

## Using virtual environment (**here be dragons**)
TRACLE requires Python3, pip3 and Redis if you are running Linux you probably have it already installed, otherwise refer to the documentation of your distribution on how to install it.
On Debian you can use this command to make sure all needed packages are installed:
```
sudo apt install git python3-venv python3-dev build-essential redis-server
```

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

Copy `envs/local.env.example` to `src/.env`

```
cp envs/local.env.example src/.env
```

Setup the database:

```
cd src/
./manage.py migrate
./manage.py loaddata backend/fixtures/categories.json
```

You can run a local development server using the following command:

```
cd src/
./manage.py runserver
```

Autoprefixer is run only on deployment or when DEBUG is set to false. You'll need npm to install these node modules:

```
npm install -g postcss-cli autoprefixer
```
