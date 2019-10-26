class Order:
    order_id = 0
    client_id = 0
    priority = 0  # TODO add enum for priority
    status = 0  # TODO add enum for status
    text = ""

    def __init__(self, order_id, client_id, priority, text):
        self.order_id = order_id
        self.client_id = client_id
        self.priority = priority
        self.status = 0
        self.text = text

    def change_priority(self, new_priority):
        self.priority = new_priority

    def change_status(self, new_status):
        self.status = new_status