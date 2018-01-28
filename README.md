# PortfolioProject
Source code for the catalog project

## Installation
  Assuming the start point is a bare bones Ubuntu server without a web server

## Environment
  IP address of Lightsail service instance: 52.14.123.76
  Port for SSH: 2200
  URL for the application: http://52.14.123.76/catalog

### Step 1
  Install Apache web server and Python WSGI support

`$ sudo apt install apache2
`$ sudo apt install libapache2-mod-wsgi-py3

### Step 2
  Install Python 3 and supporting libraries

`$ sudo apt install python3
`$ sudo apt install python3-pip
`$ sudo pip3 install SQLAlchemy
`$ sudo pip3 install psycopg2
`$ sudo pip3 install httplib2
`$ sudo pip3 install flask
`$ sudo pip3 install oauth2client

### Step 3
  Install Postgres database server

`$ sudo apt install postgresql

### Step 4
  Configure Apache to use Python via WSGI

  Add the following line to the /etc/apache2/sites-enabled/000-default.conf file
  at the end of the VirtualHost section, just before the </VirtualHost>.

  WSGIScriptAlias /catalog /var/www/html/catalog/application.wsgi

### Step 5
  Create the database user of 'catalog' in the Postgres database

`$ sudo -u postgres psql
`$ CREATE USER catalog password 'catalog'
`$ \q

### Step6 
  Download the following repository: https://github.com/slhussey/catalog.git

`$ cd /var/www/html
`$ git clone https://github.com/slhussey/catalog.git

### Step 7
  Run the populate_database.py script to create and populate the database

`$ python3 populate_database.py

### Step 8
  Launch your favorite web browser and navigate to http://hostname/catalog
	For my Udacity project the hostname should be the IP of 52.14.123.76

## Usage
This web application supports a sports shop catalog

## License
The content of this repository is public domain.

## Attributions
Assistance on converting Flask app to Apache app from the following URL
  http://csparpa.github.io/blog/2013/03/how-to-deploy-flask-applications-to-apache-webserver.html
