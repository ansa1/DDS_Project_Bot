from src.order import Order


class Courier:
    courier_id = 0
    orders = []

    def __init__(self, courier_id):
        self.courier_id = courier_id

    def add_order(self, order):
        self.orders.append(order)

    def delete_order(self, order_id):
        ind = 0
        for cur_order in self.orders:
            if cur_order.order_id == order_id:
                self.orders.remove(ind)
            ind = ind + 1

