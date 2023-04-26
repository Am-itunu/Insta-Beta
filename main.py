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
        'post_list': [],
        'follower_list': [],
        'following_list': []
    })
    datastore_client.put(entity)


def retrieveUserInfo(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore_client.get(entity_key)
    return entity


def createPosts(claims):
    id = random.getrandbits(63)
    entity_key = datastore_client.key('Post', id)
    entity = datastore.Entity(key=entity_key)
    entity.update({

    })
    datastore_client.put(entity)
    return id


def retrievePosts(user_info):
    # make key objects out of all the keys and retrieve them
    post_ids = user_info['post_list']
    post_keys = []
    for i in range(len(post_ids)):
        post_keys.append(datastore_client.key('Post', post_ids[i]))
    post_list = datastore_client.get_multi(post_keys)
    return post_list


def retrieveFollowers(user):
    entity_key = datastore_client.key('UserInfo', follower)
    entity = datastore_client.key(entity_key)
    return entity


def addToFollowing(user_info):
    following_id = user_info['following_list']
    following_keys = []
    for i in range(following_id):
        following_keys.append(datastore_client.key('UserInfo', following_id[i]))
    following_list = datastore_client.get_multi(following_keys)
    return following_list


def addToFollowers(user):
    follower_id = user['follower_list']
    follower_keys = []
    for i in range(follower_id):
        follower_keys.append(datastore_client.key('UserInfo', follower_id[i]))
    follower_list = datastore_client.get_multi(follower_keys)
    return follower_list


@app.route('/follow/<username>', method=['POST'])
def Follow(username):
    id_token = request.cookies.get("token")
    claims = None
    user_info = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user = User.query.filter_by(username=username).first()  # come back and check
            user_info = retrieveUserInfo(claims)
            addToFollowing(user_info)
            addToFollowers(user)

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')  # fix later


def retrieveFollowing(user_info):
    entity_key = datastore_client.key('UserInfo', following)
    entity = datastore_client.key(entity_key)
    return entity


@app.route('/')
def root():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    post = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            if user_info is None:
                createUserInfo(claims)
                user_info = retrieveUserInfo(claims)

            post = retrievePosts(user_info)

        except ValueError as exc:
            error_message = str(exc)
    return render_template('index.html', user_data=claims, times=times, error_message=error_message)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
