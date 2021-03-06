from flask import render_template, redirect, url_for, request, g
from app import webapp

import boto3

from app import config
from app.config import db_config

from datetime import datetime, timedelta
from operator import itemgetter
import mysql.connector


@webapp.route('/ec2_worker/create', methods=['POST'])
# Start a new EC2 instance
def ec2_create():
    # create connection to ec2
    ec2 = boto3.resource('ec2')

    ec2.create_instances(ImageId=config.ami_id, InstanceType='t2.small', MinCount=1, MaxCount=1,
                         Monitoring={'Enabled': True},
                         Placement={'AvailabilityZone': 'us-east-1a', 'GroupName': 'A2_workerpool'},
                         SecurityGroups=[
                             'launch-wizard-11',
                         ],
                         KeyName='ece1779_A2_user', TagSpecifications=[
                            {
                                'ResourceType': 'instance',
                                'Tags': [
                                    {
                                        'Key': 'Name',
                                        'Value': 'Additional_workers'
                                    },
                                ]
                            }, ])

    return redirect(url_for('ec2_list'))


@webapp.route('/ec2_worker/delete/<id>', methods=['POST'])
# Terminate a EC2 instance
def ec2_destroy(id):

    ec2 = boto3.resource('ec2')

    ec2.instances.filter(InstanceIds=[id]).terminate()

    return redirect(url_for('ec2_list'))


@webapp.route('/ec2_worker', methods=['GET'])
# Display an HTML list of all ec2 instances
def ec2_list():

    # create connection to ec2
    ec2 = boto3.resource('ec2')

    instances = ec2.instances.filter(
      Filters=[{'Name': 'placement-group-name', 'Values': ['A2_workerpool']}])

    for instance in instances:

        print(instance.id, instance.image_id, instance.key_name, instance.tags)

    return render_template("workers/list.html", title="EC2 Instances", instances=instances)


@webapp.route('/ec2_worker/<id>', methods=['GET'])
# Display details about a specific instance.
def ec2_view(id):

    print(id)
    ec2 = boto3.resource('ec2')

    # acquire an EC2 instance
    instance = ec2.Instance(id)

    # Create CloudWatch client
    client = boto3.client('cloudwatch')

    metric_name = 'CPUUtilization'
    namespace = 'AWS/EC2'
    statistic = 'Average'  # could be Sum,Maximum,Minimum,SampleCount,Average

    # request syntax / get cpu statistics
    cpu = client.get_metric_statistics(
        Period=60,
        StartTime=datetime.utcnow() - timedelta(seconds=61 * 60),
        EndTime=datetime.utcnow() - timedelta(seconds=1 * 60),
        MetricName=metric_name,
        Namespace=namespace,  # Unit='Percent',
        Statistics=[statistic],
        Dimensions=[{'Name': 'InstanceId',
                     'Value': id}]

    )

    print(cpu)

    # gather return statistics
    cpu_stats = []

    for point in cpu['Datapoints']:
        hour = point['Timestamp'].hour
        print(hour)
        minute = point['Timestamp'].minute
        print(minute)
        time = hour + minute/60
        print(time)
        print(point)
        cpu_stats.append([time, point['Average']])

    print(cpu_stats)

    cpu_stats = sorted(cpu_stats, key=itemgetter(0))
    print(cpu_stats)

    return render_template("workers/view.html", title="Instance Info",
                           instance=instance,
                           cpu_stats=cpu_stats)


# connect the database
def connect_to_database():
    return mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'])


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db


@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@webapp.route('/s3/delete', methods=['POST'])
# delete all files in s3 bucket and the data in RDS
def delete():

    s3 = boto3.resource('s3')
    bucket = s3.Bucket('imagesece1779')

    keys = bucket.objects.all()

    for k in keys:
        image_name = k.key
        s3.Object('imagesece1779', image_name).delete()
        thumb_name = image_name + '_thumbnail'
        s3.Object('imagesece1779', thumb_name).delete()
        flopped_name = image_name + '_flopped'
        s3.Object('imagesece1779', flopped_name).delete()
        gray_name = image_name + '_gray'
        s3.Object('imagesece1779', gray_name).delete()
        rotated_name = '_rotated'
        s3.Object('imagesece1779', rotated_name).delete()

    cnx = get_db()
    cursor = cnx.cursor()

    cursor.execute("""TRUNCATE TABLE users""")
    cnx.commit()

    cnx = get_db()
    cursor = cnx.cursor()

    cursor.execute("""TRUNCATE TABLE images""")
    cnx.commit()

    return redirect(url_for('s3_list'))

