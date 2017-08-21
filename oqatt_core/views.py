from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from oqatt_core.models import User
import json

class CreateUser(APIView):

	def post(self, request, format=None):
		params = request.data
		user_contact = params.get('contact',None)

		if user_contact:
			user = self.check_then_create(user_contact)
		else:
			return Response({'msg':"No contact"}, status=status.HTTP_200_OK)
		
		user.refresh() # reload properties from neo
		# neo4j internal id
		return Response({'User':user.uid}, status=status.HTTP_200_OK)

	def check_then_create(self,contact):
		try:
			user = User.nodes.get(contact=contact)
			user.claimed = True
			user.save()
		except User.DoesNotExist:
			user = User(contact=contact,claimed=True).save()
		return user


class SyncUserContacts(APIView):

	def post(self, request, format=None):
		params = request.data
		contact_list = params.pop('contact_list',None)
		user_id = params.get('uid',None)
		if user_id:
			try:
				user = User.nodes.get(uid=user_id)
			except User.DoesNotExist:
				return Response({'msg':"DoesNotExist"}, status=status.HTTP_200_OK)
		else:
			return Response({'msg':"No contact"}, status=status.HTTP_200_OK)

		for contact in contact_list:
			user.contact_list.connect(self.check_then_create(contact))
		users = User.nodes.filter(contact__in=contact_list)
		result = []
		for user_contact in users:
			dic = {}
			rel = user_contact.contact_list.relationship(user)
			if rel:
				dic['Bi-directional'] = True
			else:
				dic['Bi-directional'] = False
			dic['contact'] = user_contact.contact
			dic['claimed'] = user_contact.claimed
			result.append(dic)
		return Response({'Users':result}, status=status.HTTP_200_OK)

	def check_then_create(self,contact):
		try:
			user = User.nodes.get(contact=contact)
		except User.DoesNotExist:
			user = User(contact=contact).save()
		return user
