import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash
from flask.ext.sqlalchemy import SQLAlchemy
from contextlib import closing
import settings

app = Flask(__name__)
app.config.from_object(settings)
db = SQLAlchemy(app)

def connect_db():
  return sqlite3.connect(app.config['DATABASE'])

def init_db():
  with closing(connect_db()) as db:
    with app.open_resource('schema.sql', mode='r') as f:
      db.cursor().executescript(f.read())
    db.commit()

@app.before_request
def before_request():
  ''' connect to the db before any request '''
  g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
  ''' close connection to db after request '''
  db = getattr(g, 'db', None)
  if db is not None:
    db.close()

@app.route('/')
def show_recipes():
  cursor = g.db.execute('select title, category from recipes order by id desc')
  entries = [dict(title=row[0], category=row[1]) for row in cursor.fetchall()]
  return render_template('show_recipes.html', entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():
  if not session.get('logged_in'):
    abort(401)
  # TODO - fix
  g.db.execute('insert into recipes (title, text) values (?, ?)',
               [request.form['title'], request.form['text']])
  g.db.commit()
  flash('New entry was successfully posted')
  return redirect(url_for('show_recipes'))

@app.route('/login', methods=['GET', 'POST'])
def login():
  error = None
  if request.method == 'POST':
    if request.form['username'] != app.config['USERNAME']:
      error = 'Invalid username'
    elif request.form['password'] != app.config['PASSWORD']:
      error = 'Invalid password'
    else:
      session['logged_in'] = True
      flash('You were logged in')
      return redirect(url_for('show_recipes'))
  return render_template('login.html', error=error)

@app.route('/logout')
def logout():
  session.pop('logged_in', None)
  flash('You were logged out')
  return redirect(url_for('show_recipes'))