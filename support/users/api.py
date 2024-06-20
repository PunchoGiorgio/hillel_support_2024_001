from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import generics, permissions, serializers, status
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from users.enums import Role

from . import services
from .models import ActivationKey
from .services import Activator

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name", "role"]

    def validate_role(self, value: str) -> str:
        if value not in Role.users():
            raise ValidationError(
                f"Selected role must be in {Role.users_values()}",
            )
        return value

    def validate(self, attrs: dict) -> dict:
        """Change the password for its hash"""

        attrs["password"] = make_password(attrs["password"])

        return attrs


class UserRegistrationPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "role"]


class UserListCreateAPI(generics.ListCreateAPIView):
    http_method_names = ["get", "post"]
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return User.objects.all()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Functional approach
        # activation_key: uuid.UUID = services.create_activation_key(email=serializer.data["email"])
        # services.send_user_activation_email(email=serializer.data["email"], activation_key=activation_key)

        # OOP approach
        activator_service = Activator(email=serializer.data["email"])
        activation_key = activator_service.create_activation_key()

        user = User.objects.get(email=serializer.data["email"])
        my_data = user.__dict__

        ActivationKey.objects.create(user_id=my_data["id"], activation=activation_key)

        activator_service.send_user_activation_email(activation_key=activation_key)

        return Response(
            UserRegistrationPublicSerializer(serializer.validated_data).data,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(serializer.data),
        )

    def get(self, request):
        queryset = self.get_queryset()
        serializer = UserSerializer(queryset)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
            headers=self.get_success_headers(serializer.data),
        )


@api_view(["GET", "POST"])
def resend_activation_mail(request) -> Response:
    if request.method == "POST":

        act_data = list(ActivationKey.objects.values("activation"))

        act_key = request.data

        key_data = [j["activation"] for j in act_data]

        if act_key["activation"] in key_data:
            for i in key_data:
                if i == act_key["activation"]:
                    object = ActivationKey.objects.get(activation=act_key["activation"])
                    mydict_act = object.__dict__

                    user_data = list(User.objects.values("id"))

                    for k in user_data:
                        if mydict_act["user_id"] == k["id"]:
                            user_table = User.objects.get(id=k["id"])
                            User.objects.filter(id=k["id"]).update(is_active=True)
                            del_obj = ActivationKey.objects.get(
                                activation=act_key["activation"]
                            )
                            del_obj.delete()
                            user_dict = user_table.__dict__
                            services.send_user_activation_message(
                                user_email=user_dict["email"]
                            )

        else:
            print("There is no such key")

        return Response()
