from django.db import connection, transaction, IntegrityError
from django.shortcuts import render
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count
from rest_framework import viewsets, generics, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django.db import transaction
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from django_filters import rest_framework as filters


from .models import *
from .serializers import *

class TokenPairView(TokenObtainPairView):
	serializer_class = TokenPairSerializer

class UserViewset(viewsets.ModelViewSet):
	authentication_classes = (SessionAuthentication, JWTAuthentication)
	permission_classes = [IsAuthenticated, IsAdminUser]
	queryset = User.objects.filter()
	serializer_class = UserSerializer
	filter_backends = DjangoFilterBackend,
	filter_fields = {

		"username":["exact"]
	}

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		data = request.data
		user = User(
			username = data.get("username"),
			email = data.get("email"),
			first_name = data.get("first_name"),
			last_name = data.get("last_name")
		)
		user.set_password("password")
		
		user.save()
		serializer = UserSerializer(user, many=False)
		return Response(serializer.data, 201)

	def update(self, request, *args, **kwargs):
		user = request.user
		data = request.data
		username = data.get("username")
		if username : user.username = username
		password = data.get("password")
		if password : user.set_password(password)
		user.save()
		serializer = UserSerializer(user, many=False)
		return Response(serializer.data, 201)

	def patch(self, request, *args, **kwargs):
		return self.update(request, *args, **kwargs)

	def destroy(self, request, *args, **kwargs):
		user = self.get_object()
		user.is_active = False
		user.save()
		return Response({'status': 'success'}, 204)


class AccountViewset(viewsets.ModelViewSet):
	authentication_classes = (SessionAuthentication, JWTAuthentication)
	permission_classes = [IsAuthenticated, ]
	queryset = Account.objects.all()
	serializer_class = AccountSerializer
	filter_backends = DjangoFilterBackend,
	filter_fields = {
		"date":["exact"]
	}

class TransferViewset(viewsets.ModelViewSet):
	authentication_classes = (SessionAuthentication, JWTAuthentication)
	permission_classes = [IsAuthenticated, ]
	queryset = Transfer.objects.all()
	serializer_class = TransferSerializer
	filter_backends = DjangoFilterBackend,
	filter_fields = {

		"account":["exact"]
	}
	@transaction.atomic
	def create(self, request):
		data = request.data
		compte = Account.objects.get(code='MAIN')
		nom = data.get('nom')
		tel = data.get('tel')
		montant = float(data.get('montant'))
		transfer = Transfer(
			nom=nom,
			tel=tel,
			account=compte,
			montant=montant
		)
		compte.montant_canada += montant
		compte.save()
		transfer.save()
		return Response({'status':'Depot effecue avec succes'},200)



class TransactionViewset(viewsets.ModelViewSet):
	authentication_classes = (SessionAuthentication, JWTAuthentication)
	permission_classes = [IsAuthenticated, ]
	queryset = Transaction.objects.all()
	serializer_class = TransactionSerializer
	filter_backends = DjangoFilterBackend,
	filter_fields = {

		"amount":["exact"]
	}
	@transaction.atomic
	def create(self, request): 
		data = request.data
		account = Account.objects.get(code='MAIN')
		receiver = data.get('receiver')
		amount = float(data.get('amount'))
		transaction = Transaction(
			receiver=receiver,
			sent=account,
			amount=amount
		)
		account.montant_burundi-=amount
		account.save()
		transaction.save()
		return Response({'status':'transaction effecue avec succes'},200)






class DepenseViewset(viewsets.ModelViewSet):
	authentication_classes = (SessionAuthentication, JWTAuthentication)
	permission_classes = [IsAuthenticated, ]
	queryset = Depense.objects.all()
	serializer_class = DepenseSerializer
	filter_backends = DjangoFilterBackend,
	filter_fields = {

		"date":["exact"]
	}


class ProvisioningViewset(viewsets.ModelViewSet):
	authentication_classes = (SessionAuthentication, JWTAuthentication)
	permission_classes = [IsAuthenticated, ]
	queryset = Provisioning.objects.all()
	serializer_class = ProvisioningSerializer
	filter_backends = DjangoFilterBackend,
	filter_fields = {

		"montant_recu":["exact"]
	}
	@transaction.atomic
	def create(self, request): 
		data = request.data
		account = Account.objects.get(code='MAIN')
		montant_recu = float(data.get('montant_recu'))
		montant = float(data.get('montant'))
		approvision =Provisioning(
			montant_recu=montant_recu,
			account=account,
			montant=montant
		)
		account.montant_canada -=montant
		account.montant_burundi += montant_recu
		account.save()
		approvision.save()
		return Response({'status':'approvisionement effecue avec succes'},200)

