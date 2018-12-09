from __future__ import print_function # Python 2/3 compatibility
from flask import render_template, session, redirect, url_for, request, g, send_from_directory
from app import webapp
import datetime
import time
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
    # get the account username
    account_user_name = session.get('username')

    # get information of this user account
    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': account_user_name
        }
    )

    data = {}

    if 'Item' in response:
        item = response['Item']
        data.update(item)

    # get thumbnail url of this user account in aws s3
    file_key_name = str(account_user_name) + '/' + 'thumbnail'
    s3 = boto3.client('s3')
    url_thumbnail_account = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'imagesece1779', 'Key': file_key_name})

    return render_template("users/show_personal_information.html", data=data, url_thumbnail_account=url_thumbnail_account)


@webapp.route('/edit_profile', methods=['GET'])
# edit user's personal profile
def edit_profile():
    # get the account username
    account_user_name = session.get('username')

    # get information of this account in the aws db
    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': account_user_name
        }
    )

    data = {}

    if 'Item' in response:
        item = response['Item']
        data.update(item)

    # get thumbnail url of this user account in aws s3
    file_key_name = str(account_user_name) + '/' + 'thumbnail'
    s3 = boto3.client('s3')
    url_thumbnail_account = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'imagesece1779', 'Key': file_key_name})

    return render_template("users/edit_profile.html", data=data, url_thumbnail_account=url_thumbnail_account)


@webapp.route('/edit_profile', methods=['POST'])
# edit user's personal information and save
def edit_profile_save():
    # get the account username
    account_user_name = session.get('username')

    # acquire the information of personal profile
    personal_profile = request.form.get('personal_profile', "")
    account_name = request.form.get('account_name', "")

    # save the info in db
    if personal_profile != "":
        # store information into the database
        table = dynamodb.Table('a3_ece1779')
        response = table.update_item(
            Key={
                'username': account_user_name
            },
            UpdateExpression="SET personal_profile = :p",
            ExpressionAttributeValues={
                ':p': personal_profile
            }
        )

    if account_name != "":
        # store information into the database
        table = dynamodb.Table('a3_ece1779')
        response = table.update_item(
            Key={
                'username': account_user_name
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
    # get the account username
    account_user_name = session.get('username')

    # get information of this account in the aws db
    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': account_user_name
        }
    )

    data = {}

    if 'Item' in response:
        item = response['Item']
        data.update(item)

    # get thumbnail url of this user account in aws s3
    file_key_name = str(account_user_name) + '/' + 'thumbnail'
    s3 = boto3.client('s3')
    url_thumbnail_account = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'imagesece1779', 'Key': file_key_name})

    return render_template("users/edit_thumbnail.html", data=data, url_thumbnail_account=url_thumbnail_account)


@webapp.route('/edit_thumbnail', methods=['POST'])
# edit user's thumbnail and save in s3 and db
def edit_thumbnail_save():
    # get the account username
    account_user_name = session.get('username')

    # get info of the new uploaded account thumbnail
    for thumbnail in request.files.getlist("file"):
        if thumbnail.filename == '':
            return redirect(url_for('edit_thumbnail'))

        # upload to the s3 bucket
        s3 = boto3.client('s3')
        file_key_name = str(account_user_name) + '/' + 'thumbnail'
        s3.upload_fileobj(thumbnail, 'imagesece1779', file_key_name, ExtraArgs={"ContentType": "image/jpeg"})

        # update account thumbnail info in the db
        table = dynamodb.Table('a3_ece1779')
        response = table.update_item(
            Key={
                'username': account_user_name
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
    # get the account username
    account_user_name = session.get('username')

    # get information of this account in the aws db
    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': account_user_name
        }
    )

    data = {}

    if 'Item' in response:
        item = response['Item']
        data.update(item)

    # get thumbnail url of this user account in aws s3
    file_key_name = str(account_user_name) + '/' + 'thumbnail'
    s3 = boto3.client('s3')
    url_thumbnail_account = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'imagesece1779', 'Key': file_key_name})

    return render_template("users/add_new_post.html", data=data, url_thumbnail_account=url_thumbnail_account)


@webapp.route('/add_new_post', methods=['POST'])
# save added new post
def add_new_post_save():
    # get the account username
    account_user_name = session.get('username')

    url_post = []
    file_type_revised = []

    # get information of this account in the aws db
    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': account_user_name
        }
    )
    data = {}
    if 'Item' in response:
        item = response['Item']
        data.update(item)

    # get thumbnail url of this user account in aws s3
    file_key_name = str(account_user_name) + '/' + 'thumbnail'
    s3 = boto3.client('s3')
    url_thumbnail_account = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'imagesece1779', 'Key': file_key_name}
    )

    # upload post image

    # if no upload image, return to add_new_post html and show error message
    if not request.files.getlist("file"):
        return render_template("users/add_new_post.html", data=data, url_thumbnail_account=url_thumbnail_account,
                               error_msg='No file!')

    # upload image of the new post
    else:
        for new_post in request.files.getlist("file"):

            # acquire the image name
            filename_full = new_post.filename
            index = filename_full.rfind('.')
            post_image_name = filename_full[:index]

            # file's saved name in the db and s3
            file_saved = str(account_user_name) + '/' + post_image_name

            # acquire the  file type
            file_type = new_post.mimetype
            file_type_revised = file_type[0:file_type.rfind('/', 1)]

            # Get the service client and upload to the s3 bucket
            s3 = boto3.client('s3')
            if file_type_revised == 'image':
                s3.upload_fileobj(new_post, 'imagesece1779', file_saved, ExtraArgs={"ContentType": "image/jpeg"})
            elif file_type_revised == 'video':
                s3.upload_fileobj(new_post, 'imagesece1779', file_saved, ExtraArgs={"ContentType": "video/mp4"})
            else:
                s3.upload_fileobj(new_post, 'imagesece1779', file_saved, ExtraArgs={"ContentType": "image/jpeg"})

            # save the file_post_name and file_type in the session
            session['authenticated'] = True
            session['post_image_name'] = post_image_name
            session['post_image_type'] = file_type_revised

            # get post image url in aws s3
            s3 = boto3.client('s3')
            url_post = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': 'imagesece1779', 'Key': file_saved})

        return render_template("users/add_new_post_save.html", data=data, file_type_revised=file_type_revised,
                               url_thumbnail_account=url_thumbnail_account, url_post=url_post)


@webapp.route('/add_new_post_save', methods=['POST'])
# save added new post
def add_new_post_double_save():
    # get the account username,post_image_name,post_image_type
    account_user_name = session.get('username')
    post_image_name = session.get('post_image_name')
    post_image_type = session.get('post_image_type')

    # get post content and who_can_see from form
    post_content = request.form.get('post_content', "")
    who_can_see = request.form.get('who_can_see', "")

    if who_can_see == '':
        who_can_see = 'public'

    # update info into file_content of database
    table = dynamodb.Table('a3_ece1779')
    response = table.update_item(
        Key={
            'username': account_user_name
        },
        UpdateExpression="ADD file_content :file_content",
        ExpressionAttributeValues={
            ":file_content": set([post_image_name+'.'+post_image_type])
        }
    )

    # get time
    now = datetime.datetime.now()
    post_time = now.strftime("%Y-%m-%d %H:%M:%S")

    # update info into post_content of database
    table = dynamodb.Table('a3_ece1779')
    response = table.update_item(
        Key={
            'username': account_user_name
        },
        UpdateExpression="ADD post_content :post_content",
        ExpressionAttributeValues={
            ":post_content": set([post_time+','+post_image_name+'.'+post_image_type + ':' + post_content + '&' + who_can_see])
        }
    )

    return redirect(url_for('user_home'))


@webapp.route('/post_detail/<post_name>/<post_type>', methods=["GET", "POST"])
# display post details
def post_detail(post_name, post_type):
    if 'authenticated' not in session:
        return redirect(url_for('main'))

    # get the account username
    account_user_name = session.get('username')

    # get information of this account in the aws db
    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': account_user_name
        }
    )

    data = {}
    if 'Item' in response:
        item = response['Item']
        data.update(item)

    # get thumbnail url of this user account in aws s3
    s3 = boto3.client('s3')
    file_key_name = str(account_user_name) + '/' + 'thumbnail'
    url_thumbnail_account = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'imagesece1779', 'Key': file_key_name}
    )

    # get post image url in aws s3
    url_post = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'imagesece1779', 'Key': str(account_user_name) + '/' + post_name}
    )

    post_time = []
    post_info = []

    if 'post_content' in data:
        for i in data['post_content']:
            if post_name in i:
                post_info = i[i.rfind(':', 1)+1:i.rfind('&', 1)]
                post_time = i[0:i.rfind(',', 1)]

    return render_template("users/post_detail.html", data=data, url_post=url_post,
                           url_thumbnail_account=url_thumbnail_account, post_info=post_info,
                           post_time=post_time, post_type=post_type)


@webapp.route('/my_moments', methods=["GET", "POST"])
# display all posts of the user
def my_moments():
    # get the account username
    account_user_name = session.get('username')

    # get information of this account in the aws db
    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': account_user_name
        }
    )
    data = {}
    if 'Item' in response:
        item = response['Item']
        data.update(item)

    # get thumbnail url of this user account in aws s3
    s3 = boto3.client('s3')
    # get the thumbnail
    file_key_name = str(account_user_name) + '/' + 'thumbnail'
    url_thumbnail_account = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'imagesece1779', 'Key': file_key_name}
    )

    # get post content of all posts of this user account
    data_all = []

    if 'post_content' in data:

        for post in data['post_content']:

            post_info = post[post.rfind(':', 1) + 1:post.rfind('&', 1)]
            post_time = post[0:post.rfind(',', 1)]
            post_name = post[(post.rfind(',', 1) + 1): post.rfind('.', 1)]
            post_type = post[(post.rfind('.', 1) + 1): post.rfind(':', 1)]

            # get the url of post
            s3 = boto3.client('s3')
            url_post = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': 'imagesece1779', 'Key': str(account_user_name) + '/' + post_name}
            )

            data_all.append([post_time, post_info, post_name, post_type, url_post])

    data_sorted = sorted(data_all, key=itemgetter(0), reverse=True)

    return render_template("users/my_moments.html", data=data, url_thumbnail_account=url_thumbnail_account,
                           data_sorted=data_sorted)


@webapp.route('/friends_moments', methods=["GET", "POST"])
# display all posts of the user
def friends_moments():
    # get the account username
    account_user_name = session.get('username')

    # get information of this account in the aws db
    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': account_user_name
        }
    )

    data = {}
    if 'Item' in response:
        item = response['Item']
        data.update(item)

    # get following usernames in the database
    posts_users = []

    if 'following' in data:
        following_name = data['following']

        for name in following_name:

            # get information of this account in the aws db
            table = dynamodb.Table('a3_ece1779')
            response = table.get_item(
                Key={
                    'username': name
                }
            )

            follow_name_data = {}
            url_thumb = []

            if 'Item' in response:
                item = response['Item']
                follow_name_data.update(item)

            if 'thumbnail' in follow_name_data:
                # get thumbnail url of a specific user
                s3 = boto3.client('s3')
                # get the thumbnail
                file_key_name = str(name) + '/' + 'thumbnail'
                url_thumb = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': 'imagesece1779', 'Key': file_key_name}
                )

            if 'post_content' in follow_name_data:
                for post in follow_name_data['post_content']:

                    post_info = post[post.rfind(':', 1) + 1:post.rfind('&', 1)]
                    post_time = post[0:post.rfind(',', 1)]
                    post_name = post[(post.rfind(',', 1) + 1): post.rfind('.', 1)]
                    post_type = post[(post.rfind('.', 1) + 1): post.rfind(':', 1)]
                    post_who_can_see = post[post.rfind('&', 1) + 1:]

                    if post_who_can_see == 'onlyme':
                        continue

                    else:
                        # get the url of all posts of this following user
                        s3 = boto3.client('s3')
                        url_post = s3.generate_presigned_url(
                            'get_object',
                            Params={'Bucket': 'imagesece1779', 'Key': str(name) + '/' + post_name}
                        )

                        posts_users.append([post_time, name, post_info, post_name, post_type, url_post, url_thumb])

    posts_sorted = sorted(posts_users, key=itemgetter(0), reverse=True)

    return render_template("users/friends_moments.html", posts_sorted=posts_sorted)


@webapp.route('/world_moments', methods=["GET", "POST"])
# display all posts of the user
def world_moments():

    # get information of the aws db
    table = dynamodb.Table('a3_ece1779')
    response = table.scan()

    records = []
    usernames = []

    for i in response['Items']:
        records.append(i)

    # get all usernames in the db
    for user in records:
        usernames.append(user['username'])

    posts_users = []

    # get information of the all users
    for name in usernames:
        # get information of this account in the aws db
        table = dynamodb.Table('a3_ece1779')
        response = table.get_item(
            Key={
                'username': name
            }
        )

        user_data = {}
        url_thumb = []

        if 'Item' in response:
            item = response['Item']
            user_data.update(item)

        if 'thumbnail' in user_data:
            # get thumbnail url of a specific user
            s3 = boto3.client('s3')
            file_key_name = str(name) + '/' + 'thumbnail'
            url_thumb = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': 'imagesece1779', 'Key': file_key_name}
            )

        if 'post_content' in user_data:
            for post in user_data['post_content']:

                post_info = post[post.rfind(':', 1) + 1:post.rfind('&', 1)]
                post_time = post[0:post.rfind(',', 1)]
                post_name = post[(post.rfind(',', 1) + 1): post.rfind('.', 1)]
                post_type = post[(post.rfind('.', 1) + 1): post.rfind(':', 1)]
                post_who_can_see = post[post.rfind('&', 1) + 1:]

                if post_who_can_see == 'onlyme':
                    continue

                else:
                    # get the url of all posts of this following user
                    s3 = boto3.client('s3')
                    url_post = s3.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': 'imagesece1779', 'Key': str(name) + '/' + post_name}
                    )

                    posts_users.append([post_time, name, post_info, post_name, post_type, url_post, url_thumb])

    posts_sorted = sorted(posts_users, key=itemgetter(0), reverse=True)

    return render_template("users/world_moments.html", posts_sorted=posts_sorted)






@webapp.route('/posts_of_specific_user', methods=['POST'])
# query a specific user and see their posts
def posts_of_specific_user():
    # get the account username from session
    account_user_name = session.get('username')

    # get the query username  and save in session
    query_username = request.form.get('query_username', "")
    session['authenticated'] = True
    session['query_username'] = query_username

    # get information of this account in the aws db
    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': account_user_name
        }
    )

    info = {}
    if 'Item' in response:
        item = response['Item']
        info.update(item)

    # get following-state from this account info
    follow_sate = 0

    if 'following' in info:
        if query_username in info['following']:
            follow_sate = 1

    # get information of this query user account in the aws db
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

    if follow_sate == 0:
        return render_template("users/posts_of_specific_user.html", posts_sorted=posts_sorted, data=data)
    else:
        return render_template("users/posts_of_specific_user_followed.html", posts_sorted=posts_sorted, data=data)


@webapp.route('/posts_of_specific_user_hyperlink/<username>', methods=['POST', 'GET'])
# query a specific user and see their posts
def posts_of_specific_user_hyperlink(username):
    # get the account username from session
    account_user_name = session.get('username')

    # get information of this account in the aws db
    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': account_user_name
        }
    )

    info = {}
    if 'Item' in response:
        item = response['Item']
        info.update(item)

    # get following-state from this account info
    follow_sate = 0

    if 'following' in info:
        if username in info['following']:
            follow_sate = 1
    # get information of this query user account in the aws db
    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': username
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
            file_key_name = str(username) + '/' + 'thumbnail'
            url_thumb = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': 'imagesece1779', 'Key': file_key_name}
            )

        if 'post_content' in data:

            for post in data['post_content']:

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

                    posts_query_users.append([post_time, username, post_info, post_name, post_type, url_post,
                                              url_thumb])

    posts_sorted = sorted(posts_query_users, key=itemgetter(0), reverse=True)

    if follow_sate == 0:
        return render_template("users/posts_of_specific_user.html", posts_sorted=posts_sorted, data=data)
    else:
        return render_template("users/posts_of_specific_user_followed.html", posts_sorted=posts_sorted, data=data)


@webapp.route('/follow', methods=['POST', 'GET'])
# follow a specific user
def follow():
    # get the account username and query_username from session
    account_user_name = session.get('username')
    follow_name = session.get('query_username')

    # add the new following name in db
    table = dynamodb.Table('a3_ece1779')
    response = table.update_item(
        Key={
            'username': account_user_name
        },
        UpdateExpression="ADD following :following",
        ExpressionAttributeValues={
            ":following": set([follow_name])
        }
    )

    # get information of this new following user account in the aws db
    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': follow_name
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
            file_key_name = str(follow_name) + '/' + 'thumbnail'
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
                        Params={'Bucket': 'imagesece1779', 'Key': str(follow_name) + '/' + post_name}
                    )

                    posts_query_users.append([post_time, follow_name, post_info, post_name, post_type, url_post,
                                              url_thumb])

    posts_sorted = sorted(posts_query_users, key=itemgetter(0), reverse=True)

    return render_template("users/posts_of_specific_user_followed.html", posts_sorted=posts_sorted, data=data)

@webapp.route('/unfollow', methods=['POST', 'GET'])
# unfollow a specific user
def unfollow():
    # get the account username and query_username from session
    account_user_name = session.get('username')
    follow_name = session.get('query_username')

    # delete this username in the 'following' of the account
    table = dynamodb.Table('a3_ece1779')
    response = table.update_item(
        Key={
            'username': account_user_name
        },
        UpdateExpression="DELETE following :following",
        ExpressionAttributeValues={
            ":following": set([follow_name])
        }
    )

    # get information of this query user account in the aws db
    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': follow_name
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
            file_key_name = str(follow_name) + '/' + 'thumbnail'
            url_thumb = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': 'imagesece1779', 'Key': file_key_name}
            )

        if 'post_content' in data:

            for post in data['post_content']:

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
                        Params={'Bucket': 'imagesece1779', 'Key': str(follow_name) + '/' + post_name}
                    )

                    posts_query_users.append([post_time, follow_name, post_info, post_name, post_type, url_post,
                                              url_thumb])

    posts_sorted = sorted(posts_query_users, key=itemgetter(0), reverse=True)

    return render_template("users/posts_of_specific_user.html", posts_sorted=posts_sorted, data=data)



@webapp.route('/following_list', methods=['POST', 'GET'])
# show the following list
def following_list():
    # get the account username from session
    account_user_name = session.get('username')

    # get thumbnail url of this user account in aws s3
    s3 = boto3.client('s3')
    url_thumbnail_account = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'imagesece1779', 'Key': str(account_user_name) + '/' + 'thumbnail'})

    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': account_user_name
        }
    )

    data = {}
    following_users = []

    if 'Item' in response:
        item = response['Item']
        data.update(item)

    if 'following' in data:
        following_name = data['following']

        for name in following_name:
            table = dynamodb.Table('a3_ece1779')
            response = table.get_item(
                Key={
                    'username': name
                }
            )
            data_name = {}

            if 'Item' in response:
                item = response['Item']
                data_name.update(item)

            if 'thumbnail' in data_name:

                # get thumbnail url of a specific user
                s3 = boto3.client('s3')
                # get the thumbnail
                file_key_name = str(name) + '/' + 'thumbnail'
                url_thumb = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': 'imagesece1779', 'Key': file_key_name}
                )
            else:
                url_thumb = "https://images.unsplash.com/photo-1513721032312-6a18a42c8763?w=152&h=152&fit=crop&crop=faces"

            following_users.append([name, url_thumb])

    return render_template("users/following_list.html", following_users=following_users,
                           data=data, url_thumbnail_account=url_thumbnail_account)

