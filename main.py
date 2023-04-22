import datetime
from google.cloud import datastore
import google.oauth2.id_token
from flask import Flask, render_template, request
from google.auth.transport import requests

app = Flask(__name__)
firebase_request_adapter = requests.Request()
datastore_client = datastore.Client()


def createUser(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore.Entity(key=entity_key)
    entity.update({
        'email': claims['email'],
        'name': claims['name'],
        'post': [],
        'followers': [],
        'following': []
    })
    datastore_client.put(entity)


@app.route('/')
def root():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)

        except ValueError as exc:
            error_message = str(exc)
    return render_template('index.html', user_data=claims, times=times, error_message=error_message)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
