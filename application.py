""" This module creates the web server for the catalog application """

import random
import string
import json
import os
import httplib2
import requests

from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from flask import session as login_session
from flask import make_response

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

from sqlalchemy import create_engine, asc, desc, func
from sqlalchemy.orm import sessionmaker
from database_setup import DATABASE, Category, Item, User

app = Flask(__name__)

#CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())[
#    'web']['client_id']

with app.open_resource('client_secrets.json','r') as f:    
    CLIENT_ID = json.load(f)['web']['client_id']


# Connect to Database and create database session
ENGINE = create_engine('postgresql://catalog:catalog@localhost:5432/catalog')
DATABASE.metadata.bind = ENGINE

DATABASE_SESSION_FACTORY = sessionmaker(bind=ENGINE)
DATABASE_SESSION = DATABASE_SESSION_FACTORY()


@app.route('/login')
def show_login():
    """ Display the login page to choose the provider """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, client_id=CLIENT_ID)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    """ Connect application to Facebook authentication """
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = request.data

    #Exchange client token for long-lived server-side token with
    app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token' \
          '?grant_type=fb_exchange_token&client_id=%s' \
          '&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
    http = httplib2.Http()
    result = http.request(url, 'GET')[1]

    #Use token to get user info from API
    #strip expire tag from access token
    token = result.split(",")[0].split(':')[1].replace('"', '')
    print("API access token: %s" %token)
    url = 'https://graph.facebook.com/v2.11/me?access_token=%s&fields=name,id,email' % token
    http = httplib2.Http()
    result = http.request(url, 'GET')[1]

    #print "url sent for API access: %s" %url
    #print "API JSON result: %s" %result

    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    #The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    #Get user picture
    url = 'https://graph.facebook.com/v2.11/me/picture?' \
          'access_token=%s&redirect=0&height=200&width=200' % token
    http = httplib2.Http()
    result = http.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['picture'] = data["data"]["url"]

    user_id = get_user_id(login_session['email'])
    if not user_id:
        user_id = create_user()

    login_session['user_id'] = user_id

    flash("You are now logged in as %s" % login_session['username'])
    return redirect(url_for('show_catalog'))


@app.route('/disconnect')
def disconnect():
    """ Disconnect from the third-party authentication provider """
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['google_id']
            del login_session['credentials']
        else:
            if login_session['provider'] == 'facebook':
                fbdisconnect()
                del login_session['facebook_id']

        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']

        flash("You have been successfully logged out.")
    else:
        flash("You are not logged in to begin with!")

    return redirect(url_for('show_catalog'))


@app.route('/fbdisconnect')
def fbdisconnect():
    """ Disconnect application from Facebook authentication """
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/v2.11/me/permissions?access_token=%s' % access_token
    http = httplib2.Http()
    result = http.request(url, 'DELETE')[1]


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """ Connect application to the Google authentication """
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps(
            'Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
           access_token)
    http = httplib2.Http()
    result = json.loads(http.request(url, 'GET')[1])

    # If error in the access token info, abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps(
            "Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps(
            "Token's client ID doesn't match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check to see if user is already logged in
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['google_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = json.loads(answer.text)

    login_session['username'] = data["name"]
    login_session['picture'] = data["picture"]
    login_session['email'] = data["email"]
    login_session['provider'] = 'google'

    user_id = get_user_id(data["email"])
    if not user_id:
        user_id = create_user()

    login_session['user_id'] = user_id

    flash("You are now logged in as %s" % login_session['username'])
    return redirect(url_for('show_catalog'))


# DISCONNECT - Revoke a current user's token and reset their login_session.
@app.route("/gdisconnect")
def gdisconnect():
    """ Disconnect application from Google authentication """
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Execute HTTP GET request to revoke current token.
    access_token = login_session['credentials']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    http = httplib2.Http()
    result = http.request(url, 'GET')[0]

    if result['status'] != '200':
        # For whatever reason, the given token was invalid
        response = make_response(json.dumps(
            'Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view catlog Information
@app.route('/catalog.json')
def catalog_json():
    """ Create JSON document of entire catalog """
    response = ''

    categories = DATABASE_SESSION.query(Category).order_by(asc(Category.ident))

    for cat in categories:
        response += json.dumps(cat.serialize)
        items = DATABASE_SESSION.query(Item).filter_by(category_ident=cat.ident)
        for item in items:
            response += json.dumps(item.serialize)

    return jsonify(Category=response)


@app.route('/catalog.json/<string:category_name>/<string:item_name>')
def catalog_item_json(category_name, item_name):
    """ Create JSON document for a specific item """
    category = DATABASE_SESSION.query(Category).filter_by(name=category_name).one()
    item = DATABASE_SESSION.query(Item).filter_by(name=item_name,
                                                  category_ident=category.ident).one()

    return jsonify(Item=item.serialize)


# Show categories and latest items
@app.route('/')
@app.route('/catalog')
def show_catalog():
    """ Show the catalog with the latest items added """
    categories = DATABASE_SESSION.query(Category).order_by(asc(Category.name))

    count_q = categories.statement.with_only_columns([func.count()]).order_by(None)
    count = categories.session.execute(count_q).scalar()

    items = DATABASE_SESSION.query(Item) \
                            .join(Category) \
                            .order_by(desc(Item.date_added)) \
                            .limit(count)
    if 'username' not in login_session:
        return render_template('unauthCatalog.html', categories=categories, items=items)
    else:
        return render_template('authCatalog.html', categories=categories, items=items)


# Show categories and items in selected category
@app.route('/items/<int:cat_ident>')
def show_items(cat_ident):
    """ Show items of the selected category """
    categories = DATABASE_SESSION.query(Category).order_by(asc(Category.name))

    items = DATABASE_SESSION.query(Item) \
                            .filter_by(category_ident=cat_ident) \
                            .order_by(asc(Item.name))
    count_q = items.statement.with_only_columns([func.count()]).order_by(None)
    count = items.session.execute(count_q).scalar()

    category = DATABASE_SESSION.query(Category).filter_by(ident=cat_ident).one()

    if 'username' not in login_session:
        return render_template('unauthCatalogItems.html',
                               categories=categories,
                               items=items,
                               category=category,
                               count=count)
    else:
        return render_template('authCatalogItems.html',
                               categories=categories,
                               items=items,
                               category=category,
                               count=count)


# Show item detail
@app.route('/catalog/<string:category_name>/<string:item_name>')
def show_item(category_name, item_name):
    """ Show detail of a specific item """
    category = DATABASE_SESSION.query(Category).filter_by(name=category_name).one()
    item = DATABASE_SESSION.query(Item).filter_by(name=item_name,
                                                  category_ident=category.ident).one()

    if 'username' not in login_session:
        return render_template('unauthItem.html', item=item)
    else:
        return render_template('authItem.html', item=item)


@app.route('/catalog/new', methods=['GET', 'POST'])
def add_item():
    """ Add a new item to the database """
    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        new_item = Item(name=request.form['title'],
                        desc=request.form['desc'],
                        category_ident=request.form['cat_ident'],
                        owner_ident=login_session['user_id'])
        DATABASE_SESSION.add(new_item)
        flash('New item %s successfully created' % new_item.name)
        DATABASE_SESSION.commit()
        return redirect(url_for('show_catalog'))
    else:
        categories = DATABASE_SESSION.query(Category).order_by(asc(Category.name))
        return render_template('newItem.html', categories=categories)


@app.route('/catalog/<string:category_name>/<string:item_name>/edit', methods=['GET', 'POST'])
def edit_item(category_name, item_name):
    """ Edit the details of a specific item """
    if 'username' not in login_session:
        return redirect('/login')

    category = DATABASE_SESSION.query(Category).filter_by(name=category_name).one()
    item = DATABASE_SESSION.query(Item) \
                           .filter_by(name=item_name, category_ident=category.ident).one()

    if item.owner_ident == login_session['user_id']:
        if request.method == 'POST':
            if request.form['title']:
                item.name = request.form['title']
            if request.form['desc']:
                item.desc = request.form['desc']
            if request.form['cat_ident']:
                item.category_ident = request.form['cat_ident']
            DATABASE_SESSION.add(item)
            DATABASE_SESSION.commit()
            flash('Item %s successfully updated' % item.name)

            return redirect(url_for('show_catalog'))
        else:
            categories = DATABASE_SESSION.query(Category).order_by(asc(Category.name))
            return render_template('editItem.html', item=item, categories=categories)
    else:
        flash('Logged in user does not own this item')
        return redirect(url_for('show_catalog'))


@app.route('/catalog/<string:category_name>/<string:item_name>/delete', methods=['GET', 'POST'])
def delete_item(category_name, item_name):
    """ Delete an item from the database """
    if 'username' not in login_session:
        return redirect('/login')

    category = DATABASE_SESSION.query(Category).filter_by(name=category_name).one()
    item = DATABASE_SESSION.query(Item) \
                           .filter_by(name=item_name, category_ident=category.ident).one()

    if item.owner_ident == login_session['user_id']:
        if request.method == 'POST':
            DATABASE_SESSION.delete(item)
            flash('Item %s successfully deleted' % item.name)
            DATABASE_SESSION.commit()
            return redirect(url_for('show_catalog'))
        else:
            return render_template('deleteItem.html', item=item)
    else:
        flash('Logged in user does not own this item')
        return redirect(url_for('show_catalog'))


@app.context_processor
def override_url_for():
    """ Process all URLs for static content to add the file modification parameter.
        This prevents browser cacheing of CSS and JavaScript files """
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    """ Add the file modification parameter to the URL for static files """
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     app.static_folder, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


def create_user():
    """ Create a new user in the database """
    new_user = User(username=login_session['username'],
                    email=login_session['email'],
                    picture=login_session['picture'])
    DATABASE_SESSION.add(new_user)
    DATABASE_SESSION.commit()
    user = DATABASE_SESSION.query(User).filter_by(email=login_session['email']).one()
    return user.ident


def get_user_info(email):
    """ Return the user object from the database based on email address """
    user = DATABASE_SESSION.query(User).filter_by(email=email).one()
    return user


def get_user_id(email):
    """ Return the user identity from the database based on email address """
    try:
        user = DATABASE_SESSION.query(User).filter_by(email=email).one()
        return user.ident
    except:
        return None


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
