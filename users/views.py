from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import CustomUserCreationForm
from .serializers import RegisterSerializer, UserSerializer
from .registration import create_unconfirmed_user


def register_web_user(request, form):
    confirmation_url = create_unconfirmed_user(request, form)
    messages.success(
        request,
        "Account created! Check your e-mail for the confirmation link.",
    )
    if settings.DEBUG:
        messages.info(request, confirmation_url)


class RegisterView(APIView):
    def get(self, request):
        form = CustomUserCreationForm()
        return render(request, "dashboard/signup.html", {"form": form})

    def post(self, request):
        if request.content_type == 'application/json':
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            register_web_user(request, form)
            return redirect("login")
        messages.error(request, "❌ Please fix the errors below.")
        return render(request, "dashboard/signup.html", {"form": form})

class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class UserProfileView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
