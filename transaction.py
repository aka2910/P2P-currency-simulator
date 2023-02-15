class Transaction:
    def __init__(self, id, sender, receiver, amount, timestamp) -> None:
        self.id = id
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = timestamp

    def __str__(self):
        output = f"{self.id}: {self.sender.id} pays {self.receiver.id} {self.amount} coins"