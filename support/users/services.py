import uuid

from .tasks import send_activation_mail, send_activation_message


def send_user_activation_message(user_email):

    send_activation_message.delay(
        recipient=user_email,
    )


class Activator:
    def __init__(self, email: str):
        self.email = email

    def create_activation_key(self) -> uuid.UUID:
        print(f"create {uuid.uuid3(namespace=uuid.uuid4(), name=self.email)}")
        return uuid.uuid3(namespace=uuid.uuid4(), name=self.email)

    def create_activation_link(self, activation_key: uuid.UUID) -> str:
        print(f"link https://frontend.com/users/activate/{activation_key}")
        return f"https://frontend.com/users/activate/{activation_key}"

    def send_user_activation_email(self, activation_key: uuid.UUID) -> None:
        """Send activation email using SMTP."""

        activation_link = self.create_activation_link(activation_key)

        send_activation_mail.delay(
            recipient=self.email,
            activation_link=activation_link,
        )

    def send_user_activation_message(self, user_email):

        send_activation_message.delay(
            recipient=user_email,
        )
