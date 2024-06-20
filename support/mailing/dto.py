from dataclasses import dataclass

# data models
# entities (or value objects in some cases)
# Data Transfer Objects


@dataclass
class EmailMessage:
    body: str
    subject: str
    recepient: str
    sender: str
