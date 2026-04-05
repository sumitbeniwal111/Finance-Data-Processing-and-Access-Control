from enum import Enum


class UserRole(str, Enum):
    viewer = "viewer"
    analyst = "analyst"
    admin = "admin"


class UserStatus(str, Enum):
    active = "active"
    inactive = "inactive"


class RecordType(str, Enum):
    income = "income"
    expense = "expense"
