from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from oqatt_core.models import User
from oqatt_core.functions import upvote_push,push_poll
import json
import logging
from neomodel.match import INCOMING,Traversal
from neomodel import db
from web3 import Web3, HTTPProvider, TestRPCProvider
from web3.contract import ConciseContract
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from os import path
# from solc import compile_source
cred = credentials.Certificate('/Users/dk/oqatt_core/oqatt-diva-firebase-adminsdk-smc26-4fbe6b846a.json')
# Use the application default credentials
firebase_admin.initialize_app(cred, {
  'projectId': 'oqatt-diva',
})

firestoredb = firestore.client()

class TestApi(APIView):

	def get(self, request, format=None):
		
		return Response({'Msg':"Working"}, status=status.HTTP_200_OK)


class CreateUser(APIView):

	def post(self, request, format=None):
		params = request.data
		contact = params.get('contact',None)
		if contact:
			user = User.get_or_create({'contact':contact})[0]
			user.fcm_id = params.get("fcm_id",None)
			user.save()
		else:
			return Response({'msg':"Bad request"}, status=status.HTTP_400_BAD_REQUEST)
		user.refresh() # reload properties from neo
		# neo4j internal id
		return Response({'User':user.uid}, status=status.HTTP_200_OK)


class SyncUserContacts(APIView):

	def post(self, request, format=None):
		params = request.data
		contact_list = params.pop('contact_list',None)
		user_id = params.get('uid',None)
		if user_id:
			try:
				user = User.nodes.get(uid=user_id)
			except User.DoesNotExist:
				return Response({'msg':"DoesNotExist"}, status=status.HTTP_400_BAD_REQUEST)
		else:
			return Response({'msg':"Bad request"}, status=status.HTTP_400_BAD_REQUEST)
		
		
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
				
		values = {}
		values['my_contact'] = user.contact
		values['contact_list'] = contact_list
		# values['bucket_types'] = ["Personality","Attitude","Skill","Maturity","Manners"]
		
		response = []
		results = db.cypher_query(query, values)[0]
		
		for result in results:
			print(result)
			response.append(result[0])

		if len(response):
			print(response)
			return Response({'Users':response}, status=status.HTTP_200_OK)
		else:
			return Response({'msg':"No contacts in the oqatt"}, status=status.HTTP_200_OK)


class PublishPoll(APIView):

	def post(self, request,me_id, format=None):
		params = request.data
		print(params)
		question = params.pop('question',None)
		sub_contact = params.pop('sub_contact',None)
		options = params.pop('options',None)
		poll_hash = params.pop('poll_hash',None)
		try:
			user = User.nodes.get(uid=me_id)
		except User.DoesNotExist:
			return Response({'msg':"DoesNotExist"}, status=status.HTTP_400_BAD_REQUEST)
		query = "MATCH (p:User {contact:{sub_contact}})-[:Knows]->(b)-[:Knows]->(p)"\
				"return b"
				# "MATCH (p:User)-[:Knows]->(b)-[:Knows]->(p)"\
		values = {}
		values['sub_contact'] = sub_contact
		results = db.cypher_query(query, values)[0]

		fcm_ids = []
		voter_ids = []
		for result in results:
			voter = User.inflate(result[0])
			fcm_ids.append(voter.fcm_id)
			voter_ids.append(voter.uid)
		fcm_ids.remove(user.fcm_id)
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
    	   "type" : 0
    	   }
		push_poll('New Question Added',fcm_ids,data_message=data_message)
		return Response({'Msg':'Succesfully published'}, status=status.HTTP_200_OK)


class Vote(APIView):

	def post(self, request,me_id, format=None):
		params = request.data
		poll_hash = params.pop('poll_hash',None)
		chosen_option = params.pop('chosen_option',None)
		try:
			user = User.nodes.get(uid=me_id)
		except User.DoesNotExist:
			return Response({'msg':"DoesNotExist"}, status=status.HTTP_400_BAD_REQUEST)

		poll_ref = firestoredb.collection(u'polls').document(poll_hash)
		poll = poll_ref.get().to_dict()

		poll['options'][chosen_option] = poll['options'][chosen_option] + 1
		poll_ref.update({u'options': poll['options']})
		owner = poll['owner']
		try:
			owner_obj = User.nodes.get(uid=owner)
		except User.DoesNotExist:
			return Response({'msg':"owner DoesNotExist"}, status=status.HTTP_400_BAD_REQUEST)
		
		data_message = {
    	   "option_count" : poll['options'],
    	   "poll_hash": poll_hash,
       	   "type" : 1
    	   }
		upvote_push('Checkout Someone upvoting',owner_obj.fcm_id,data_message=data_message)

		return Response({'Msg':'Succesfully voted'}, status=status.HTTP_200_OK)


		




