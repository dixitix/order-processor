from dataclasses import dataclass
from abc import ABC, abstractmethod
import time


@dataclass
class Item:
    id: int
    name: str
    price: int
    id_provider: int
    id_store: int


class Store:
    __slots__ = ['_couriers', '_storekeepers', '_storage', '_address']

    def __init__(self, address: list):
        self._couriers = []
        self._storekeepers = []
        self._storage = {}
        self._address = address

    @property
    def couriers(self):
        return self._couriers

    @couriers.setter
    def couriers(self, x):
        self._couriers = x

    @property
    def storekeepers(self):
        return self._storekeepers

    @storekeepers.setter
    def storekeepers(self, x):
        self._storekeepers = x

    @property
    def storage(self):
        return self._storage

    @storage.setter
    def storage(self, x):
        self._storage = x

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, x):
        self._address = x

    def send_request(self, order, provider):
        to_send = {}
        for item, amount in order.items.items():
            if item not in self.storage:
                to_send[item] = amount
            elif self.storage.get(item) < amount:
                to_send[item] = amount - self.storage.get(item)
        provider.send_order(to_send, self)

    # send_request - отправить заказ для провайдера (что привезти)

    def take_order(self, order, provider):
        self.send_request(order, provider)
        order.delivery_status = 'in stock'

        order.store_address = self.address

        storekeeper = self.set_storekeeper()
        if type(storekeeper) == Storekeeper:
            order.delivery_status = 'collecting'
            order.storekeeper = storekeeper
            storekeeper.get_order(order)

        courier = self.set_courier()
        if type(courier) == Courier:
            order.delivery_status = 'handed over to a courier'
            order.courier = courier
            courier.get_order(order)

        for item, amount in order.items.items():
            self.storage[item] -= amount

    # принять заказ и начать его обрабатывать

    def set_courier(self):
        for courier in self.couriers:
            if courier.status == 'free':
                return courier
    # дать заказу курьера

    def set_storekeeper(self):
        for storekeeper in self.storekeepers:
            if storekeeper.status == 'free':
                return storekeeper
    # дать заказу кладовщика

    def get_worker(self, worker):
        if type(worker) == Courier:
            self.couriers.append(worker)
        else:
            self.storekeepers.append(worker)
    # взять работника к себе и дать ему смену


class Provider:  # поставщик
    def __init__(self):
        self.storage = {}

    def add_to_storage(self, item: Item, amount: int):
        self.storage[item.id] = amount

    @staticmethod
    def update_stocks(items_with_amount: dict, store: Store):
        for item, amount in items_with_amount.items():
            if item in store.storage:
                store.storage[item] += amount
            else:
                store.storage[item] = amount
    # update_stocks - обновить число товаров на складе

    def send_order(self, request: dict, store: Store):
        collected_items_with_amount = {}
        for item, amount in request.items():
            if item in self.storage:
                if self.storage.get(item) >= amount:
                    self.storage[item] -= amount
                    collected_items_with_amount[item] = amount
                else:
                    self.storage[item] = 0
                    collected_items_with_amount[item] = self.storage.get(item)
        self.update_stocks(collected_items_with_amount, store)
    # send_order - принять и отправить заказ складу


class Worker(ABC):
    __slots__ = ['_couriers', '_status', '_shift_end_time', '_salary']

    def __init__(self, x: int):
        super().__init__()
        self._id = x
        self._status = 'free'  # statuses: free, working
        self._shift_end_time = 0
        self._salary = 0

    @property
    def status(self):
        if self._shift_end_time < time.time():
            self._status = 'free'
        return self._status

    @status.setter
    def status(self, x):
        self._status = x

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, x):
        self._id = x

    @property
    def shift_end_time(self):
        return self._shift_end_time

    @shift_end_time.setter
    def shift_end_time(self, x):
        self._shift_end_time = x

    @property
    def salary(self):
        return self._salary

    @salary.setter
    def salary(self, x):
        self._salary = x

    @abstractmethod
    def get_order(self, order):
        pass

    # принять заказ, если возможно

    def get_shift(self, number_hours: int, store: Store):
        self.status = 'free'
        shift_start_time = time.time()
        self.shift_end_time = shift_start_time + number_hours * 60 * 60
        self.salary = number_hours * 300
        store.get_worker(self)

    # получить смену, когда работает


class Courier(Worker):
    @staticmethod
    def count_distance(store_address, user_address):
        return ((store_address[0] - user_address[0]) ** 2 + (store_address[1] - user_address[1]) ** 2) ** 0.5

    def get_order(self, order):
        order.courier = self
        distance = self.count_distance(order.store_address, order.user_address)
        order.time_delivery = time.time() + 60 + 30 * distance + 60
        self.status = 'working'
        time.sleep(60 + 30 * distance + 60)
        self.status = 'free'


class Storekeeper(Worker):
    def get_order(self, order):
        amount_items = 0
        order.storekeeper = self
        for item, amount in order.items.items():
            amount_items += amount
        self.status = 'working'
        time.sleep(amount_items * 45)
        self.status = 'free'


@dataclass
class Order:
    delivery_status: str
    items: dict
    time_creation: time
    time_delivery: time
    courier: Courier
    storekeeper: Storekeeper
    store_address: list
    user_address: list

    def __init__(self, items: dict):
        self.items = items
        self.delivery_status = 'accepted'
        self.time_creation = time.time()

# Что находится в заказе? Статус доставки, список товаров, время создания-время доставки, кто собирал-доставлял


class User:
    __slots__ = ['_user_id', '_address']

    def __init__(self, user_id: int, address):
        self._user_id = user_id
        self._address = address

    @property
    def user_id(self):
        return self._user_id

    @user_id.setter
    def user_id(self, x):
        self._user_id = x

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, x):
        self._address = x

    def make_order(self, wish_order: dict, store: Store, provider: Provider):
        order = Order(wish_order)
        order.time_creation = time.time()
        order.delivery_status = 'processing'  # обрабатывается
        order.user_address = self.address
        store.take_order(order, provider)
    # сделать заказ

    @staticmethod
    def take_order(order):
        print(f"заказ номер {order.id} доставлен")
        order.delivery_status = 'delivered'
    # забрать заказ


pen = Item(1, 'pen', 25, 2, 3)
erase = Item(2, 'erase', 5, 5, 1)
ruler = Item(3, 'ruler', 20, 6, 7)

provider1 = Provider()
provider1.add_to_storage(pen, 3)
assert (provider1.storage.get(pen.id) == 3)
provider1.add_to_storage(erase, 5)
assert (provider1.storage.get(erase.id) == 5)
provider1.add_to_storage(ruler, 7)
assert (provider1.storage.get(ruler.id) == 7)

address_store1 = [0, 0]
store1 = Store(address_store1)

courier1 = Courier(1)
storekeeper1 = Storekeeper(1)

courier1.get_shift(1, store1)
assert (courier1.status == 'free')

storekeeper1.get_shift(2, store1)
assert (courier1.status == 'free')

address1 = [10, 20]
user1 = User(1, address1)

wish_order1 = {pen.id: 1, erase.id: 2}
user1.make_order(wish_order1, store1, provider1)
