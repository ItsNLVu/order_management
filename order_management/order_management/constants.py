from enum import Enum


class OrderStatus(str, Enum):
	NEW = "New"
	DELIVERED = "Delivered"
	CANCELLED = "Cancelled"


class OrderAction(str, Enum):
	DELIVER = "deliver"
	CANCEL = "cancel"


class Role(str, Enum):
	ORDER_USER = "Order User"
	ORDER_MANAGER = "Order Manager"


class DocTypes:
	CUSTOMER = "Order Customer"
	ITEM = "Order Item"
	ORDER = "Customer Order"
	SETTINGS = "Order Settings"
