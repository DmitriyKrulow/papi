# backend/src/core/value_objects/__init__.py

from .money import Money
from .email import Email
from .phone import Phone
from .password_hash import PasswordHash
from .status import Status, AssetStatus
from .inventory_number import InventoryNumber
from .serial_number import SerialNumber
from .date_range import DateRange
from .coordinates import Coordinates
from .batch_id import BatchId
from .asset_type import AssetType
from .year_period import YearPeriod
