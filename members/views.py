from django.shortcuts import render
from .models import Member
from .serializers import MemberSerializer
from rest_framework import generics

class MemberListCreate(generics.ListCreateAPIView):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
