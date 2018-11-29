from __future__ import print_function # Python 2/3 compatibility
from flask import render_template, session, redirect, url_for, request, g, send_from_directory
from app import webapp
import datetime
from operator import itemgetter


from flask import render_template, redirect, url_for, request

from app import webapp

import boto3


# connect to dynamodb

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
webapp.secret_key = '\x80\xa9s*\x12\xc7x\xa9d\x1f(\x03\xbeHJ:\x9f\xf0!\xb1a\xaa\x0f\xee'

SECRET_KEY = b'pseudo randomly generated secret key'
AUTH_SIZE = 16


@webapp.route('/personal_information', methods=['GET'])
# show user's personal information
def show_personal_information():
    users_name = session.get('username')

    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': users_name
        }
    )

    data = {}

    if 'Item' in response:
        item = response['Item']
        data.update(item)

    file_key_name = str(users_name) + '/' + 'thumbnail'
    s3 = boto3.client('s3')
    url_thumbnail = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'imagesece1779', 'Key': file_key_name})

    return render_template("users/show_personal_information.html", data=data, url_thumbnail=url_thumbnail)


@webapp.route('/edit_profile', methods=['GET'])
# edit user's personal information
def edit_profile():
    users_name = session.get('username')

    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': users_name
        }
    )

    data = {}

    if 'Item' in response:
        item = response['Item']
        data.update(item)

    file_key_name = str(users_name) + '/' + 'thumbnail'
    s3 = boto3.client('s3')
    url_thumbnail = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'imagesece1779', 'Key': file_key_name})

    return render_template("users/edit_profile.html", data=data, url_thumbnail=url_thumbnail)


@webapp.route('/edit_profile', methods=['POST'])
# edit user's personal information
def edit_profile_save():
    users_name = session.get('username')

    # acquire the information of personal profile
    personal_profile = request.form.get('personal_profile', "")
    print(personal_profile)

    if personal_profile != "":
        # store information into the database
        table = dynamodb.Table('a3_ece1779')
        response = table.update_item(
            Key={
                'username': users_name
            },
            UpdateExpression="SET personal_profile = :p",
            ExpressionAttributeValues={
                ':p': personal_profile
            }

        )

    # acquire the information of personal profile
    account_name = request.form.get('account_name', "")
    print(account_name)

    if account_name != "":
        # store information into the database
        table = dynamodb.Table('a3_ece1779')
        response = table.update_item(
            Key={
                'username': users_name
            },
            UpdateExpression="SET account_name = :n",
            ExpressionAttributeValues={
                ':n': account_name
            }

        )

    return redirect(url_for('user_home'))


@webapp.route('/edit_thumbnail', methods=['GET'])
# edit user's thumbnail
def edit_thumbnail():
    users_name = session.get('username')
    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': users_name
        }
    )

    data = {}

    if 'Item' in response:
        item = response['Item']
        data.update(item)

    file_key_name = str(users_name) + '/' + 'thumbnail'
    s3 = boto3.client('s3')
    url_thumbnail = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'imagesece1779', 'Key': file_key_name})

    return render_template("users/edit_thumbnail.html", data=data, url_thumbnail=url_thumbnail)


@webapp.route('/edit_thumbnail', methods=['POST'])
# edit user's thumbnail
def edit_thumbnail_save():
    users_name = session.get('username')

    for thumbnail in request.files.getlist("file"):
        if thumbnail.filename == '':
            return redirect(url_for('edit_thumbnail'))

        # Get the service client and upload to the s3 bucket
        s3 = boto3.client('s3')
        file_key_name = str(users_name) + '/' + 'thumbnail'
        s3.upload_fileobj(thumbnail, 'imagesece1779', file_key_name, ExtraArgs={"ContentType": "image/jpeg"})

        table = dynamodb.Table('a3_ece1779')

        response = table.update_item(
            Key={
                'username': users_name
            },
            UpdateExpression="SET thumbnail = :p",
            ExpressionAttributeValues={
                ':p': file_key_name
            }
        )

    return redirect(url_for('user_home'))


@webapp.route('/add_new_post', methods=['GET'])
# add new post
def add_new_post():
    users_name = session.get('username')
    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': users_name
        }
    )

    data = {}

    if 'Item' in response:
        item = response['Item']
        data.update(item)

    file_key_name = str(users_name) + '/' + 'thumbnail'
    s3 = boto3.client('s3')
    url_thumbnail = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'imagesece1779', 'Key': file_key_name})

    return render_template("users/add_new_post.html", data=data, url_thumbnail=url_thumbnail)


@webapp.route('/add_new_post', methods=['POST'])
# save added new post
def add_new_post_save():

    users_name = session.get('username')
    data = {}
    url_thumbnail = []
    url_post = []
    file_type_revised = []

    if not request.files.getlist("file"):

        users_name = session.get('username')
        table = dynamodb.Table('a3_ece1779')
        response = table.get_item(
            Key={
                'username': users_name
            }
        )

        data = {}

        if 'Item' in response:
            item = response['Item']
            data.update(item)

        file_key_name = str(users_name) + '/' + 'thumbnail'
        s3 = boto3.client('s3')
        url_thumbnail = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': 'imagesece1779', 'Key': file_key_name})

        return render_template("users/add_new_post.html", data=data, url_thumbnail=url_thumbnail, error_msg='No file!')

    else:
        for new_post in request.files.getlist("file"):

            filename_full = new_post.filename

            file_type = new_post.mimetype

            file_type_revised = file_type[0:file_type.rfind('/', 1)]
            index = filename_full.rfind('.')
            filename = filename_full[:index]

            file_post_name = filename
            file_saved = str(users_name) + '/' + file_post_name

            # Get the service client and upload to the s3 bucket
            s3 = boto3.client('s3')
            if file_type_revised == 'image':
                s3.upload_fileobj(new_post, 'imagesece1779', file_saved, ExtraArgs={"ContentType": "image/jpeg"})
            elif file_type_revised == 'video':
                s3.upload_fileobj(new_post, 'imagesece1779', file_saved, ExtraArgs={"ContentType": "video/mp4"})
            else:
                s3.upload_fileobj(new_post, 'imagesece1779', file_saved, ExtraArgs={"ContentType": "image/jpeg"})

            session['authenticated'] = True
            session['file_post_name'] = file_post_name
            session['type'] = file_type_revised

            s3 = boto3.client('s3')
            url_post = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': 'imagesece1779', 'Key': file_saved})

            table = dynamodb.Table('a3_ece1779')
            response = table.get_item(
                Key={
                        'username': users_name
                }
            )

            if 'Item' in response:
                item = response['Item']
                data.update(item)

            file_key_name = str(users_name) + '/' + 'thumbnail'
            s3 = boto3.client('s3')
            url_thumbnail = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': 'imagesece1779', 'Key': file_key_name}
                )

        return render_template("users/add_new_post_save.html", data=data, file_type_revised=file_type_revised,
                               url_thumbnail=url_thumbnail, url_post=url_post)


@webapp.route('/add_new_post_save', methods=['POST'])
# save added new post
def add_new_post_double_save():
    # store information into the database
    users_name = session.get('username')
    file_post_name = session.get('file_post_name')
    type = session.get('type')

    post_content = request.form.get('post_content', "")
    who_can_see = request.form.get('who_can_see', "")

    if who_can_see == '':
        who_can_see = 'public'


    # update info into file_content of database

    table = dynamodb.Table('a3_ece1779')
    response = table.update_item(
        Key={
            'username': users_name
        },
        UpdateExpression="ADD file_content :file_content",
        ExpressionAttributeValues={
            ":file_content": set([file_post_name+'.'+type])
        }
    )

    now = datetime.datetime.now()
    time = now.strftime("%Y-%m-%d %H:%M:%S")

    # update info into post_content of database

    table = dynamodb.Table('a3_ece1779')
    response = table.update_item(
        Key={
            'username': users_name
        },
        UpdateExpression="ADD post_content :post_content",
        ExpressionAttributeValues={
            ":post_content": set([time+','+file_post_name+'.'+type + ':' + post_content + '&' + who_can_see])
        }
    )

    return redirect(url_for('user_home'))


@webapp.route('/post_detail/<post_name>/<post_type>', methods=["GET", "POST"])
# display post details
def post_detail(post_name, post_type):
    if 'authenticated' not in session:
        return redirect(url_for('main'))

    table = dynamodb.Table('a3_ece1779')
    users_name = session.get('username')
    response = table.get_item(
        Key={
            'username': users_name
        }
    )

    data = {}
    if 'Item' in response:
        item = response['Item']
        data.update(item)

    s3 = boto3.client('s3')
    file_key_name = str(users_name) + '/' + 'thumbnail'
    url_thumb = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'imagesece1779', 'Key': file_key_name}
    )
    url_post = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'imagesece1779', 'Key': str(users_name) + '/' + post_name}
    )

    post_time = []
    post_info = []

    if 'post_content' in data:
        post = data['post_content']

        for i in post:
            if post_name in i:
                post_info = i[i.rfind(':', 1)+1:i.rfind('&', 1)]
                post_time = i[0:i.rfind(',', 1)]

    return render_template("users/post_detail.html", data=data, url_post=url_post, url_thumb=url_thumb, post_info=post_info,
                           post_time=post_time, post_type=post_type)


@webapp.route('/my_moments', methods=["GET", "POST"])
# display all posts of the user
def my_moments():
    users_name = session.get('username')

    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': users_name
        }
    )
    data = {}
    if 'Item' in response:
        item = response['Item']
        data.update(item)

    post_info = []
    post_time = []
    post_name = []
    post_type = []
    url_post = []

    data_all = []

    if 'post_content' in data:
        posts = data['post_content']

        for post in posts:

            post_info = post[post.rfind(':', 1) + 1:post.rfind('&', 1)]
            post_time = post[0:post.rfind(',', 1)]
            post_name = post[(post.rfind(',', 1) + 1): post.rfind('.', 1)]
            post_type = post[(post.rfind('.', 1) + 1): post.rfind(':', 1)]

            # get the url of all posts
            s3 = boto3.client('s3')
            url_post = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': 'imagesece1779', 'Key': str(users_name) + '/' + post_name}
            )

            data_all.append([post_time, post_info, post_name, post_type, url_post])

    data_sorted = sorted(data_all, key=itemgetter(0), reverse=True)

    s3 = boto3.client('s3')
    # get the thumbnail
    file_key_name = str(users_name) + '/' + 'thumbnail'
    url_thumb = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'imagesece1779', 'Key': file_key_name}
    )

    return render_template("users/my_moments.html", data=data, url_thumb=url_thumb, data_sorted=data_sorted)


@webapp.route('/friends_moments', methods=["GET", "POST"])
# display all posts of the user
def friends_moments():
    table = dynamodb.Table('a3_ece1779')
    response = table.scan(
        ProjectionExpression="username"

    )
    records = []

    for i in response['Items']:
        records.append(i)

    # get all usernames in the database

    posts_users = []
    for user in records:
        username = user['username']

        table = dynamodb.Table('a3_ece1779')
        response = table.get_item(
            Key={
               'username': username
            }
        )
        data = {}
        url_thumb = []

        if 'Item' in response:
            item = response['Item']
            data.update(item)

        if 'thumbnail' in data:
            # get thumbnail url of a specific user
            s3 = boto3.client('s3')
            # get the thumbnail
            file_key_name = str(username) + '/' + 'thumbnail'
            url_thumb = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': 'imagesece1779', 'Key': file_key_name}
            )

        if 'post_content' in data:
            posts = data['post_content']

            for post in posts:

                post_info = post[post.rfind(':', 1) + 1:post.rfind('&', 1)]
                post_time = post[0:post.rfind(',', 1)]
                post_name = post[(post.rfind(',', 1) + 1): post.rfind('.', 1)]
                post_type = post[(post.rfind('.', 1) + 1): post.rfind(':', 1)]
                post_who_can_see = post[post.rfind('&', 1) + 1:]

                if post_who_can_see == 'onlyme':
                    continue

                else:
                    # get the url of all posts
                    s3 = boto3.client('s3')
                    url_post = s3.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': 'imagesece1779', 'Key': str(username) + '/' + post_name}
                    )

                    posts_users.append([post_time, username, post_info, post_name, post_type, url_post, url_thumb])

    posts_sorted = sorted(posts_users, key=itemgetter(0), reverse=True)

    return render_template("users/friends_moments.html", posts_sorted=posts_sorted)


@webapp.route('/posts_of_specific_user', methods=['POST'])
# query a specific user and see their posts
def posts_of_specific_user():
    query_username = request.form.get('query_username', "")

    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': query_username
        }
    )

    data = {}
    url_thumb = []
    posts_query_users = []

    if 'Item' in response:
        item = response['Item']
        data.update(item)

        if 'thumbnail' in data:
            # get thumbnail url of a specific user
            s3 = boto3.client('s3')
            # get the thumbnail
            file_key_name = str(query_username) + '/' + 'thumbnail'
            url_thumb = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': 'imagesece1779', 'Key': file_key_name}
            )

        if 'post_content' in data:
            posts = data['post_content']

            for post in posts:

                post_info = post[post.rfind(':', 1) + 1:post.rfind('&', 1)]
                post_time = post[0:post.rfind(',', 1)]
                post_name = post[(post.rfind(',', 1) + 1): post.rfind('.', 1)]
                post_type = post[(post.rfind('.', 1) + 1): post.rfind(':', 1)]
                post_who_can_see = post[post.rfind('&', 1) + 1:]

                if post_who_can_see == 'onlyme':
                    continue

                else:
                    # get the url of all posts
                    s3 = boto3.client('s3')
                    url_post = s3.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': 'imagesece1779', 'Key': str(query_username) + '/' + post_name}
                    )

                    posts_query_users.append([post_time, query_username, post_info, post_name, post_type, url_post,
                                              url_thumb])

    posts_sorted = sorted(posts_query_users, key=itemgetter(0), reverse=True)

    return render_template("users/posts_of_specific_user.html", posts_sorted=posts_sorted)

