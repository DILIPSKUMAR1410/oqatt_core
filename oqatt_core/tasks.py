from __future__ import absolute_import, unicode_literals
from pyfcm import FCMNotification
from oqatt_core.celery import app
from celery.decorators import task
from neomodel import db
from oqatt_core.models import User


# Your api-key can be gotten from:  https://console.firebase.google.com/project/<project-name>/settings/cloudmessaging

# registration_id = "<device registration_id>"
# message_title = "Uber update"
# message_body = "Hi john, your customized news for today is ready"
# result = push_service.notify_single_device(registration_id=registration_id, message_title=message_title, message_body=message_body)

# Send to multiple devices by passing a list of ids.

push_service = FCMNotification(api_key="AAAACWy09ic:APA91bEuSlYGS7gCO639eZ9qoucmpWQoMuYwqWE1s0K0Of-v4PYPO07uokIHZ9nmyr9Itimnhm5Z2sGONgAHOF1nhyboJD3vzl0F05_TV5BOQjSllL1PXT6Gng-ZIZmJtBjiOQuvCBIt")


@task(name="send_new_user_notification")
def send_new_user_notification(my_contact,contact_list):
	query = "MATCH (b:User {contact:{my_contact}}) UNWIND {contact_list} as params"\
			+" MATCH (b)-[k:Knows]->(n:User {contact: params})"\
			+" return n"

	values = {}
	values['my_contact'] = my_contact
	values['contact_list'] = contact_list
	
	response = []
	results = db.cypher_query(query, values)[0]
	
	fcm_ids = []
	
	for result in results:
		friend = User.inflate(result[0])
		fcm_ids.append(friend.fcm_id)
		data_message = {
					"type" : 2,
					"user_contact":my_contact
					 }
		sync_connections(my_contact+' added you in his network',fcm_ids,data_message=data_message)


@task(name="updateObjectbox")
def updateObjectbox(my_contact,friends_contact):
	query = "MATCH (b:User {contact:{my_contact}})-[:Knows]->(n:User {contact:{friends_contact}})"\
			+"return n"

	values = {}
	values['my_contact'] = my_contact
	values['friends_contact'] = friends_contact
	
	response = []
	results = db.cypher_query(query, values)[0]
	
	
	for result in results:
		fcm_id = User.inflate(result[0]).fcm_id
		data_message = {
					"type" : 3,
					"user_contact":my_contact
					 }
		update_objectbox(my_contact+' accepted your request',fcm_id,data_message=data_message)


@task(name="push_poll")
def push_poll(message_title,registration_ids,message_body=None,data_message=None):
	registration_ids = push_service.clean_registration_ids(registration_ids)
	if registration_ids:
		push_service.multiple_devices_data_message(registration_ids=registration_ids,data_message=data_message)
		# push_service.notify_multiple_devices(registration_ids=registration_ids, message_title=message_title, message_body=message_body,sound = "Default")

@task(name="upvote_push")
def upvote_push(message_title,registration_id,message_body=None,data_message=None):
	registration_id = push_service.clean_registration_ids([registration_id])[0]
	if registration_id:
		push_service.single_device_data_message(registration_id=registration_id,data_message=data_message)
		# push_service.notify_single_device(registration_id=registration_id,message_title=message_title, message_body=message_body,sound = "Default")

# @task(name="sync_connections")
def sync_connections(message_title,registration_ids,message_body=None,data_message=None):
	registration_ids = push_service.clean_registration_ids(registration_ids)
	if registration_ids:
		push_service.multiple_devices_data_message(registration_ids=registration_ids,data_message=data_message)
		# push_service.notify_multiple_devices(registration_ids=registration_ids, message_title=message_title, message_body=message_body,sound = "Default")

# @task(name="update_objectbox")
def update_objectbox(message_title,registration_id,message_body=None,data_message=None):
	registration_id = push_service.clean_registration_ids([registration_id])[0]
	if registration_id:
		push_service.single_device_data_message(registration_id=registration_id,data_message=data_message)
		# push_service.notify_single_device(registration_id=registration_id,message_title=message_title, message_body=message_body,sound = "Default")
