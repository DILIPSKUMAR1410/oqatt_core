from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from oqatt_core.models import User
from oqatt_core.tasks import upvote_push,push_poll,updateObjectbox,send_new_user_notification
import json
import logging
from neomodel.match import INCOMING,Traversal
from neomodel import db
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from os import path
from django.conf import settings

app_version = 0.03

if settings.DEBUG:
    # Do something
    cred = credentials.Certificate('/Users/dk/oqatt_core/oqatt-diva-firebase-adminsdk-smc26-4fbe6b846a.json')
else:
	cred = credentials.Certificate('/home/ubuntu/oqatt_core/oqatt-diva-firebase-adminsdk-smc26-4fbe6b846a.json')

# Use the application default credentials
firebase_admin.initialize_app(cred, {
  'projectId': 'oqatt-diva',
})

firestoredb = firestore.client()

FREE_TOKENS = 15
TOKENS_PER_QUESTION = 3
TOKENS_PER_ANSWER = 1

class TestApi(APIView):

	def get(self, request, format=None):
		
		return Response({'Msg':"Working"}, status=status.HTTP_200_OK)


class CreateUser(APIView):

	def post(self, request, format=None):
		params = request.data
		contact = params.get('contact',None)
		if contact:
			user = User.nodes.get_or_none(contact=contact)
			is_new_user = False
			if user is None:
				user = User(contact=contact)
				user.token_bal = FREE_TOKENS
				is_new_user = True
			user.fcm_id = params.get("fcm_id",None)
			user.save()
		else:
			return Response({'msg':"Bad request"}, status=status.HTTP_400_BAD_REQUEST)
		user.refresh() # reload properties from neo
		# neo4j internal id
		return Response({'User':user.uid,'token_bal':user.token_bal,'is_new_user':is_new_user}, status=status.HTTP_200_OK)


class SyncUserContacts(APIView):

	def post(self, request, format=None):
		params = request.data
		contact_list = params.pop('contact_list',None)
		trigger = params.pop('trigger',None)
		user_id = params.get('uid',None)
		if user_id:
			user = User.nodes.get_or_none(uid=user_id)
			if user is None:
				return Response({'msg':"DoesNotExist"}, status=status.HTTP_400_BAD_REQUEST)				
		else:
			return Response({'msg':"Bad request"}, status=status.HTTP_400_BAD_REQUEST)

		clean_contact_list = []
		for contact in contact_list:
			if contact is None or contact == user.contact or len(contact) < 10 :
				continue
			if not contact.startswith("+91"):
				contact = "+91" + contact[-10:]
				clean_contact_list.append(contact)
			else:
				clean_contact_list.append(contact)
		
		query = "MATCH (b:User {contact:{my_contact}}) UNWIND {contact_list} as params"\
				+" MATCH (n:User {contact: params})"\
				+" MERGE (b)-[k:Knows]->(n)"\
				+" with b as b"\
				+" MATCH (p:User)-[:Knows]->(b)-[:Knows]->(p)"\
				+" return distinct p.contact"

		# "MATCH (b:User {contact:{my_contact}}) UNWIND {contact_list} as params"\
		# 		+" MATCH (n:User {contact: params})"\
		# 		+" MERGE (b)-[k:Knows]->(n)"\
		# 		+" with b as b,n as n, k as k"\
		# 		+" UNWIND {bucket_types} as bucket"\
		# 		+" MATCH (p:User)-[:Knows]->(b)-[:Knows]->(p)"\
		# 		+" MERGE (p)-[:Maintains]->(q:Bucket{name:bucket})-[:Belongs]->(b)-[:Maintains]->(r:Bucket{name:bucket})-[:Belongs]->(p)"\
		# 		+" return distinct p.contact"
		
		# data_message = {"type" : 2}
		# push_poll('Your friends',fcm_ids,data_message=data_message)	
		
	

		values = {}
		values['my_contact'] = user.contact
		values['contact_list'] = clean_contact_list
		response = []
		results = db.cypher_query(query, values)[0]
		
		for result in results:
			response.append(result[0])
		
		if len(response):
			if trigger == 1:
				updateObjectbox.delay(user.contact,clean_contact_list[0])
			elif trigger == 0:
				send_new_user_notification.delay(user.contact,clean_contact_list)
			return Response({'Users':response}, status=status.HTTP_200_OK)
		else:
			return Response({'msg':"No contacts in the oqatt"}, status=status.HTTP_200_OK)


class PublishPoll(APIView):

	def post(self, request,me_id, format=None):
		params = request.data
		question = params.pop('question',None)
		sub_contact = params.pop('sub_contact',None)
		selected_friends = params.pop('selected_friends',None)
		options = params.pop('options',None)
		poll_hash = params.pop('poll_hash',None)
		user = User.nodes.get_or_none(uid=me_id)
		if not question or not sub_contact or not options or not poll_hash or not selected_friends:
			return Response({'msg':"Bad request"}, status=status.HTTP_400_BAD_REQUEST)
		if user is None:
			return Response({'msg':"DoesNotExist"}, status=status.HTTP_400_BAD_REQUEST)		

		if user.token_bal < TOKENS_PER_QUESTION:
			return Response({'Msg':'Not enough tokens'}, status=status.HTTP_200_OK)
		
		values = {}
		result = results2 = results3 = final_results = None
		fcm_ids = []
		voter_ids = []
		if "others" in selected_friends:
			selected_friends.remove("others")
			query1 = "MATCH (p:User {contact:{sub_contact}})<-[:Knows]->(all)"\
				"return distinct all"
			query2 = "MATCH (me:User {contact:{my_contact}})<-[:Knows]->(mutual)<-[:Knows]->"\
				+"(sub:User {contact:{sub_contact}})<-[:Knows]->(me)"\
				+"return  distinct mutual"
			values['sub_contact'] = sub_contact
			values['my_contact'] = user.contact
			result1 = db.cypher_query(query1, values)[0]
				
			for result in result1:
				voter = User.inflate(result[0])
				if voter.contact == user.contact:pass
				fcm_ids.append(voter.fcm_id)
				voter_ids.append(voter.uid) 
			
			results2 = db.cypher_query(query2, values)[0]
			
			for result in results2:
				voter = User.inflate(result[0])
				if voter.contact == user.contact:pass
				if voter.fcm_id in fcm_ids:fcm_ids.remove(voter.fcm_id)
				if voter.uid in voter_ids:voter_ids.remove(voter.uid)

		if selected_friends:
			query3 = "UNWIND {selected_friends} as params"\
				+" MATCH (n:User {contact: params})"\
				+"return distinct n"
			values['selected_friends'] = selected_friends
			results3 = db.cypher_query(query3, values)[0]

			for result in results3:
				voter = User.inflate(result[0])
				if voter.contact == user.contact:pass
				fcm_ids.append(voter.fcm_id)
				voter_ids.append(voter.uid)

		if user.fcm_id in fcm_ids:
			fcm_ids.remove(user.fcm_id)	

		if user.uid in voter_ids:
			voter_ids.remove(user.uid)	

		doc_ref = firestoredb.collection(u'polls').document(poll_hash)
		doc_ref.set({
		    u'voters': voter_ids,
		    u'options': [0,0,0,0],
		    u'owner': me_id
		})
		data_message = {
 		   "question" : question,
    	   "options" : options,
    	   "poll_hash":poll_hash,
    	   "sub_contact": sub_contact,
    	   "type" : 0
    	   }
		user.token_bal -= TOKENS_PER_QUESTION
		user.save()
		push_poll.delay('New question asked to you',fcm_ids,data_message=data_message)
		return Response({'Msg':'Succesfully published','token_bal':user.token_bal}, status=status.HTTP_200_OK)

class PublishGroupPoll(APIView):

	def post(self, request,me_id, format=None):
		params = request.data
		question = params.pop('question',None)
		selected_friends = params.pop('selected_friends',None)
		options = params.pop('options',None)
		poll_hash = params.pop('poll_hash',None)
		user = User.nodes.get_or_none(uid=me_id)
		
		if not question or not selected_friends or not options or not poll_hash:
			return Response({'msg':"Bad request"}, status=status.HTTP_400_BAD_REQUEST)
		if user is None:
			return Response({'msg':"DoesNotExist"}, status=status.HTTP_400_BAD_REQUEST)		

		if user.token_bal < TOKENS_PER_QUESTION:
			return Response({'Msg':'Not enough tokens'}, status=status.HTTP_200_OK)
			
		query = "UNWIND {selected_friends} as params"\
				+" MATCH (n:User {contact: params})"\
				+"return n"
				# "MATCH (p:User)-[:Knows]->(b)-[:Knows]->(p)"\
		values = {}
		values['selected_friends'] = selected_friends
		results = db.cypher_query(query, values)[0]

		fcm_ids = []
		voter_ids = []
		for result in results:
			voter = User.inflate(result[0])
			fcm_ids.append(voter.fcm_id)
			voter_ids.append(voter.uid)
		# w3 = Web3(HTTPProvider('https://ropsten.infura.io/NmmMBPY5aEKKG6hr6CDs'))
		# w3.eth.defaultAccount =  "0x1d36e88A8078F92317aEFf29e691B4aA8eaB7D6f"
		# dir_path = path.dirname(path.realpath(__file__))
		# with open(str(path.join(dir_path, 'abi.json')), 'r') as abi_definition:
		# 	abi = json.load(abi_definition)
		# 	contract = w3.eth.contract(abi,"0xa79be6332a9b8bcce43701c22d159288227af7271bac202e2f6dd7d4143648c4")
		# 	response = contract.buildTransaction({'gasPrice': 21000000000}).publishPoll(poll_hash,len(options),voter_ids)
		# 	print(response)
		# Use the application default credentials
		

		doc_ref = firestoredb.collection(u'polls').document(poll_hash)
		doc_ref.set({
		    u'voters': voter_ids,
		    u'options': [0,0,0,0],
		    u'owner': me_id
		})
		data_message = {
 		   "question" : question,
    	   "options" : options,
    	   "poll_hash":poll_hash,
    	   "type" : 4
    	   }
		user.token_bal -= TOKENS_PER_QUESTION
		user.save()
		push_poll.delay('New question asked to you',fcm_ids,data_message=data_message)
		return Response({'Msg':'Succesfully published','token_bal':user.token_bal}, status=status.HTTP_200_OK)


class Vote(APIView):

	def post(self, request,me_id, format=None):
		params = request.data
		poll_hash = params.pop('poll_hash',None)
		chosen_option = params.pop('chosen_option',None)
		user = User.nodes.get_or_none(uid=me_id)
		if user is None:
			return Response({'msg':"DoesNotExist"}, status=status.HTTP_400_BAD_REQUEST)

		poll_ref = firestoredb.collection(u'polls').document(poll_hash)
		poll = poll_ref.get().to_dict()

		poll['options'][chosen_option] = poll['options'][chosen_option] + 1
		poll_ref.update({u'options': poll['options']})
		owner = poll['owner']
		
		owner_obj = User.nodes.get_or_none(uid=owner)
		if owner_obj is None:
			return Response({'msg':"DoesNotExist"}, status=status.HTTP_400_BAD_REQUEST)
		
		data_message = {
    	   "option_count" : poll['options'],
    	   "poll_hash": poll_hash,
       	   "type" : 1
    	   }

		user.token_bal += TOKENS_PER_ANSWER
		user.save()
		upvote_push.delay('Checkout ! Someone anwsered your question',owner_obj.fcm_id,data_message=data_message)
		return Response({'Msg':'Succesfully voted','token_bal':user.token_bal}, status=status.HTTP_200_OK)


class GetTokenBalance(APIView):

	def get(self, request,me_id,format=None):
		user = User.nodes.get_or_none(uid=me_id)
		if user is None:
			return Response({'msg':"DoesNotExist"}, status=status.HTTP_400_BAD_REQUEST)
		return Response({'token_bal':user.token_bal,"app_version":app_version}, status=status.HTTP_200_OK)


class UpdateFCMId(APIView):

	def put(self, request,me_id,format=None):
		params = request.data
		fcm_id = params.get('fcm_id',None)
		if fcm_id:
			user = User.nodes.get_or_none(uid=me_id)
			if user is None:
				return Response({'msg':"DoesNotExist"}, status=status.HTTP_400_BAD_REQUEST)
			user.fcm_id = fcm_id
			user.save()
			user.refresh() # reload properties from neo
			# neo4j internal id
			return Response({'msg':'FCM id succesfully updated'}, status=status.HTTP_200_OK)
		else:
			return Response({'msg':"Bad request"}, status=status.HTTP_400_BAD_REQUEST)


class GetFriendsConnections(APIView):

	def post(self, request,me_id, format=None):
		params = request.data
		sub_contact = params.pop('sub_contact',None)
		user = User.nodes.get_or_none(uid=me_id)
		
		if user is None or not sub_contact:
			return Response({'msg':"DoesNotExist"}, status=status.HTTP_400_BAD_REQUEST)		


		query1 = "MATCH (me:User {contact:{my_contact}})<-[:Knows]->(mutual)<-[:Knows]->"\
				+"(sub:User {contact:{sub_contact}})<-[:Knows]->(me)"\
				+"return distinct mutual"

		query2 = "MATCH (me:User {contact:{sub_contact}})<-[:Knows]->(all)"\
				+"return distinct all"
		
		values = {}
		values['sub_contact'] = sub_contact
		values['my_contact'] = user.contact
		results1 = db.cypher_query(query1, values)[0]
		results2 = db.cypher_query(query2, values)[0]

		mutual = []
		unknown = []
		for result in results1:
			mutual.append(User.inflate(result[0]).contact)
		for result in results2:
			contact = User.inflate(result[0]).contact
			if contact not in mutual and contact != user.contact:
				unknown.append(User.inflate(result[0]).contact)
		return Response({'mutual':mutual,'unknown':len(unknown)}, status=status.HTTP_200_OK)


