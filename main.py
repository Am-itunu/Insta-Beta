import random

from google.cloud import datastore, storage
import google.oauth2.id_token
from flask import Flask, render_template, request
from google.auth.transport import requests, Response
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

import local_constants

app = Flask(__name__)
firebase_request_adapter = requests.Request()
datastore_client = datastore.Client()


def createUserInfo(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore.Entity(key=entity_key)
    entity.update({
        'email': claims['email'],
        'name': claims['name'],
        'username': '',
        'profileName': '',
        'post_list': [],
        'follower_list': [],
        'following_list': []
    })
    datastore_client.put(entity)


def retrieveUserInfo(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore_client.get(entity_key)
    return entity


def createUsername(claims, username, profileName):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore_client.get(entity_key)
    entity.update({
        'username': username,
        'profileName': profileName,
    })
    datastore_client.put(entity)


def retrieveUsername(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore_client.get(entity_key)
    username = entity['username']
    # if username == '':
    #     username = None
    return username


def createPosts(claims, image, comments):
    id = random.getrandbits(63)
    entity_key = datastore_client.key('Post', id)
    entity = datastore.Entity(key=entity_key)
    entity.update({
        'image': image,
        'comments': comments
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


def retrieveFollowers(user_info):
    follower = user_info['follower_list']
    follower_list = len(follower)
    return follower_list


def retrieveFollowing(user_info):
    following = user_info['following_list']
    following_list = len(following)
    return following_list


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


@app.route('/follower', methods=['GET', 'POST'])
def follower():
    id_token = request.cookies.get("token")
    claims = None
    user_info = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            if request.method == 'GET':
                return render_template("/follower.html", user_data=claims)

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/following', methods=['GET', 'POST'])
def following():
    id_token = request.cookies.get("token")
    claims = None
    user_info = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            if request.method == 'GET':
                return render_template("/following.html", user_data=claims)

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/follow/<username>', methods=['POST'])
def Follow(username):
    id_token = request.cookies.get("token")
    claims = None
    user_info = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            user_info = retrieveUserInfo(claims)
            # user = request  # User.query.filter_by(username=username).first()  # come back and check
            query = datastore_client.query(kind='UserInfo')
            query.add_filter('username', '=', username)
            user = list(query.fetch)

            addToFollowing(user_info)
            addToFollowers(user)

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')  # fix later


def getUsers(username):
    query = datastore_client.query(kind='UserInfo')
    query.add_filter('username', '=', username)
    users = list(query.fetch())
    return users


def getProfiles(profile_Name):
    query = datastore_client.query(kind='UserInfo')
    query.add_filter('profileName', '>=', profile_Name)
    query.add_filter('profileName', '<', profile_Name + '\ufffd')
    users = list(query.fetch())
    return users


@app.route('/search', methods=['GET', 'POST'])
def search():
    id_token = request.cookies.get("token")
    claims = None
    user_info = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            user_info = retrieveUserInfo(claims)

            if request.method == 'POST':
                profile_Name = request.form['profileName']
                users = getProfiles(profile_Name)
                return render_template('search.html', users=users, user_data=claims)

        except ValueError as exc:
            error_message = str(exc)
    return render_template('test.html')


@app.route('/user_page/<username>')
def searchUser(username):
    id_token = request.cookies.get("token")
    claims = None
    user_info = None
    user = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            user_info = retrieveUserInfo(claims)

            user = getUsers(username)
            if not user:
                abort(404)
        except ValueError as exc:
            error_message = str(exc)
    return render_template('user_page.html', user=user, user_data=claims)


# uploads
def blobList(prefix):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)

    return storage_client.list_blobs(local_constants.PROJECT_STORAGE_BUCKET, prefix=prefix)


def addDirectory(directory_name):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(directory_name)
    blob.upload_from_string('', content_type='application/x-www-form-urlencoded;charset=UTF-8')


def addFile(file):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(file.filename)
    blob.upload_from_file(file)


def downloadBlob(filename):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(filename)
    return blob.download_as_bytes()


@app.route('/upload_file', methods=['post'])
def uploadFileHandler():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    user_info = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            file = request.files['file_name']
            if len(file.filename) < 4:
                print('The filename is too short.')
            else:
                extension = file.filename[-4:].lower()
                if extension == '.jpg' or extension == '.png':
                    user_info = retrieveUserInfo(claims)
                    addFile(file)
                else:
                    print('the file has an invalid extension')
                    return redirect('/')

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/download_file/<string:filename>', methods=['POST'])
def downloadFile(filename):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    user_info = None
    file_bytes = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except ValueError as exc:
            error_message = str(exc)

    return Response(downloadBlob(filename), mimetype='application/octet-stream')


@app.route('/init', methods=['GET', 'POST'])
def initialUser():
    id_token = request.cookies.get("token")
    claims = None
    user_info = None
    error_message = None
    results = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info=retrieveUserInfo(claims)

            # if request.method == 'GET':
            #     render_template('/init.html', user_data=claims)

            if request.method == 'POST':
                profileName = request.form['profileName_update']
                username = request.form['username_update']
                query = datastore_client.query(kind='UserInfo')
                query.add_filter('username', '=', username)
                results = list(query.fetch())

                if len(results) > 0:
                    redirect('/init')
                else:
                    createUsername(claims, profileName, username)
                    return render_template('/test.html', user_data=claims, user_info=user_info)
        except ValueError as exc:
            error_message = str(exc)
    return render_template('/init.html', user_data=claims)


@app.route('/')
def root():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    post = None
    user_info = None
    username = None
    profileName = None
    file_list = []
    directory_list = []
    following_no = None
    follower_no = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            if user_info is None:
                createUserInfo(claims)
                user_info = retrieveUserInfo(claims)
            username = retrieveUsername(claims)
            if username == "":
                return redirect('/init')

            blob_list = blobList(None)
            for i in blob_list:
                if i.name[len(i.name) - 1] == '/':
                    directory_list.append(i)
                else:
                    file_list.append(i)

            # post = retrievePosts(user_info)
            following_no = retrieveFollowing(user_info)
            follower_no = retrieveFollowers(user_info)

        except ValueError as exc:
            error_message = str(exc)
    return render_template('test.html', user_data=claims, error_message=error_message, post=post,
                           user_info=user_info, username=username, file_list=file_list, directory_list=directory_list,
                           following_no=following_no, follower_no=follower_no)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
