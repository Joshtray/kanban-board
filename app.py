import os

from flask import Flask
from flaskr import create_app, db
from dotenv import dotenv_values

app = create_app()
env = dotenv_values(".env")

if __name__ == '__main__':
    with app.app_context():
        # If the DB file doesn't exist, make a new DB. 
        # Comment this line out if you want the DB to restart on every launch. 
        # if not os.environ.get('DATABASE_URL'):
            db.init_db()
    app.run(debug=True)