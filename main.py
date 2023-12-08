import random
from datetime import datetime, timezone
from google.cloud import datastore, storage
import google.oauth2.id_token
from flask import Flask, render_template, request
from google.auth.transport import requests
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


def createPosts(claims, image_file, caption):
    post_id = random.getrandbits(63)
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(image_file.filename)
    blob.upload_from_file(image_file)
    image_url = blob.public_url

    created_at = datetime.now(timezone.utc)
    entity_key = datastore_client.key('Post', post_id)
    entity = datastore.Entity(key=entity_key)
    entity.update({
        'image': image_url,
        'caption': caption,
        'comments': [],
        'created_at': created_at

    })
    datastore_client.put(entity)
    return post_id


def retrievePosts(user_info):
    # make key objects out of all the keys and retrieve them
    post_ids = user_info['post_list']
    post_keys = []
    for i in range(len(post_ids)):
        post_keys.append(datastore_client.key('Post', post_ids[i]))
    post_list = datastore_client.get_multi(post_keys)
    sorted_posts = sorted(post_list, key=lambda x: x['created_at'], reverse=True)

    return sorted_posts[:50]


def retrieveUserPosts(user):
    # make key objects out of all the keys and retrieve them
    post_ids = user['post_list']
    post_keys = []
    for i in range(len(post_ids)):
        post_keys.append(datastore_client.key('Post', post_ids[i]))
    post_list = datastore_client.get_multi(post_keys)
    sorted_posts = sorted(post_list, key=lambda x: x['created_at'], reverse=True)

    return sorted_posts[:50]


def addPostToUser(user_info, post_id):
    post_key = user_info['post_list']
    post_key.append(post_id)
    user_info.update({
        'post_list': post_key
    })
    datastore_client.put(user_info)


def createComment(post_id, username, text):
    entity_key = datastore_client.key('Comment')
    entity = datastore.Entity(key=entity_key)
    entity.update({
        'username': username,
        'content': text,
        'timestamp':datetime.now(),
        'post_id': post_id
    })
    datastore_client.put(entity)


# not used
def getPost(post_id):
    query = datastore_client.query(kind='Post')
    query.add_filter('id', '=', post_id)
    post = list(query.fetch(1))
    if len(post) == 1:
        return dict(post[0])
    else:
        return None



def getComment(post_id):
    query = datastore_client.query(kind='Comment')
    query.add_filter('post_id', '=', post_id)
    comments = list(query.fetch())
    return [dict(comment) for comment in comments]


#not used
@app.route('/post/<post_id>')
def show_post(post_id):
    post = getPost(post_id)
    comments = getComment(post_id)
    return render_template('post.html', post=post, comments=comments)


@app.route('/post/<post_id>/comment', methods=['POST'])
def add_comment(post_id):
    username = request.form['username']
    text = request.form['yext']
    createComment(post_id, username, text)
    return redirect('/')


def retrieveFollowers(user_info):
    follower = user_info['follower_list']
    follower_list = len(follower)
    return follower_list


def retrieveFollowing(user_info):
    following = user_info['following_list']
    following_list = len(following)
    return following_list


def addToFollowing(user_info, user_to_follow):
    following_id = user_info['following_list']
    following_id.append(user_to_follow['email'])
    user_info.update({
        'following_list': following_id
    })
    datastore_client.put(user_info)


def addToFollowers(user_to_follow, user_info):
    follower_id = user_to_follow['follower_list']
    follower_id.append(user_info['email'])
    user_to_follow.update({
        'following_list': follower_id
    })
    datastore_client.put(user_to_follow)


def removeFromFollower(user_to_unfollow, user_info):
    follower_list = user_to_unfollow['follower_list']
    follower_id = user_info['email']
    if follower_id in follower_list:
        follower_list.remove(follower_id)
    user_to_unfollow.update({
        'follower_list': follower_list
    })
    datastore_client.put(user_to_unfollow)


def removeFromFollowing(user_to_unfollow, user_info):
    following_list = user_info['following_list']
    unfollow_id = user_to_unfollow['email']
    if unfollow_id in following_list:
        following_list.remove(unfollow_id)
    user_info.update({
        'following_list':following_list
    })
    datastore_client.put(user_info)


def getEmail(email):
    query = datastore_client.query(kind='UserInfo')
    query.add_filter('email', '=', email)
    user = list(query.fetch())
    if len(user) == 1:
        user_dict = dict(user[0])
        return user_dict
    else:
        return None


def showFollowers(user_info):
    follower_list = user_info['follower_list']
    return follower_list


def showFollowing(user_info):
    following_list = user_info['following_list']
    return following_list


@app.route('/follower', methods=['GET', 'POST'])
def follower():
    id_token = request.cookies.get("token")
    claims = None
    user_info = None
    follower_list = None
    profile_names = None
    username = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            follower_list = showFollowers(user_info)
            profile_names = []

            for email in follower_list:
                username = getEmail(email)
                if username:
                    profile_names.insert(0, username['profileName'])
            if request.method == 'GET':
                return render_template("/follower.html", user_data=claims, user_info=user_info,
                                       follower_list=follower_list, profile_names=profile_names)

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/following', methods=['GET', 'POST'])
def following():
    id_token = request.cookies.get("token")
    claims = None
    user_info = None
    following_list = None
    profile_names = None
    username = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            following_list = showFollowing(user_info)
            profile_names = []

            for email in following_list:
                username = getEmail(email)
                if username:
                    profile_names.insert(0, username['profileName'])

                print('following', username)

            if request.method == 'GET':
                return render_template("/following.html", user_data=claims, following_list=following_list,
                                       username=username, profile_names=profile_names)

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/follow/<username>', methods=['POST'])
def Follow(username):
    id_token = request.cookies.get("token")
    claims = None
    user_info = None
    user = None
    follows_user = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            user_info = retrieveUserInfo(claims)
            user = getUsers(username)
            follows_user = True
            # user = request  # User.query.filter_by(username=username).first()  # come back and check
            query = datastore_client.query(kind='UserInfo')
            query.add_filter('username', '=', username)
            result = list(query.fetch(1))
            user_to_follow = result[0]

            # user_to_follow = getUsers(username)
            print("user", user_to_follow)

            addToFollowing(user_info, user_to_follow)
            addToFollowers(user_to_follow, user_info)

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')#fix


@app.route('/unfollow/<username>', methods=['POST'])
def Unfollow(username):
    id_token = request.cookies.get("token")
    claims = None
    user_info = None
    user = None
    post=None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            user_info = retrieveUserInfo(claims)
            user = getUsers(username)
            post = retrieveUserPosts(user)

            query = datastore_client.query(kind='UserInfo')
            query.add_filter('username', '=', username)
            result = list(query.fetch(1))
            user_to_unfollow = result[0]
            removeFromFollower(user_to_unfollow, user_info)
            removeFromFollowing(user_to_unfollow, user_info)
        except ValueError as exc:
            error_message = str(exc)
    return render_template('user_page.html', username=username, user=user, post=post)


def getUsers(username):
    query = datastore_client.query(kind='UserInfo')
    query.add_filter('username', '=', username)
    user = list(query.fetch(1))
    if len(user) == 1:
        return dict(user[0])
    else:
        return None



def getProfiles(profile_Name):
    query = datastore_client.query(kind='UserInfo')
    query.add_filter('profileName', '>=', profile_Name)
    query.add_filter('profileName', '<', profile_Name + '\ufffd')#adjust
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
                print(users)
                return render_template('search.html', users=users, user_data=claims)

        except ValueError as exc:
            error_message = str(exc)
    return render_template('test.html')


@app.route('/user_page/<username>')
def searchUser(username):
    id_token = request.cookies.get("token")
    claims = None
    user_info = None
    follows_user = None
    user = None
    post=None
    error_message = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            user_info = retrieveUserInfo(claims)

            user = getUsers(username)
            post = retrieveUserPosts(user)
            follows_user = user_info['email'] in user['follower_list']
            print(follows_user)
            print(user)
            if not user:
                abort(404)
        except ValueError as exc:
            error_message = str(exc)
    return render_template('user_page.html', user=user, user_data=claims, post=post ,follows_user=follows_user,
                           error_message=error_message )


# uploads
def blobList(prefix):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)

    return storage_client.list_blobs(local_constants.PROJECT_STORAGE_BUCKET, prefix=prefix)

#
# def addDirectory(directory_name):
#     storage_client = storage.Client(project=local_constants.PROJECT_NAME)
#     bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
#     blob = bucket.blob(directory_name)
#     blob.upload_from_string('', content_type='application/x-www-form-urlencoded;charset=UTF-8')


# def addFile(file):
#     storage_client = storage.Client(project=local_constants.PROJECT_NAME)
#     bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
#     blob = bucket.blob(file.filename)
#     blob.upload_from_file(file)


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
            image_file = request.files['file_name']
            caption = request.form['caption_update']
            if len(image_file.filename) < 4:
                print('The filename is too short.')
            else:
                extension = image_file.filename[-4:].lower()
                if extension == '.jpg' or extension == '.png':
                    user_info = retrieveUserInfo(claims)
                    post_id = createPosts(claims, image_file, caption)
                    addPostToUser(user_info, post_id)
                else:
                    print('the file has an invalid extension')
                    return redirect('/')

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


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
                    createUsername(claims, username, profileName)
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
    follower_list = None
    following_list =None


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

            post = retrievePosts(user_info)
            following_no = retrieveFollowing(user_info)
            follower_no = retrieveFollowers(user_info)
            follower_list = showFollowers(user_info)
            following_list = showFollowing(user_info)
            print()
        except ValueError as exc:
            error_message = str(exc)
            print(error_message)
    return render_template('test.html', user_data=claims, error_message=error_message, post=post,
                           user_info=user_info, username=username, file_list=file_list, directory_list=directory_list,
                           following_no=following_no, follower_no=follower_no, following_list=following_list, follower_list=follower_list)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
