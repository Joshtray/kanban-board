import os

from flask import Flask
from flaskr import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # If the DB file doesn't exist, make a new DB. 
        # Comment this line out if you want the DB to restart on every launch. 
        if not os.path.exists(os.path.join(app.instance_path, "flaskr.sqlite")):
            db.init_db()
    app.run(debug=True)