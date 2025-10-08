from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from .serializers import RegisterSerializer
from .utils import generate_activation_token
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer
from django.utils.encoding import force_str
from rest_framework.views import APIView


class ActivateAccountView(APIView):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({'detail': 'Account activated successfully.'}, status=200)
        return Response({'detail': 'Invalid or expired activation link.'}, status=400)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save(is_active=False)
        uid, token = generate_activation_token(user)
        activation_link = self.request.build_absolute_uri(
            reverse('activate-account', kwargs={'uidb64': uid, 'token': token})
        )
        send_mail(
            'Activate your EcoTourism account',
            f'Click the link to activate your account: {activation_link}',
            'noreply@yourdomain.com',
            [user.email],
        )

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({'detail': 'Check your email to activate your account.'}, status=status.HTTP_201_CREATED)
