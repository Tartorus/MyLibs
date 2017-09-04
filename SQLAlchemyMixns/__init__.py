from .guid_pk import GuidPK
from .id_pk import IdPK
from .saconverter import GeneralMethodMixin
from .alias_mixin import AliasMixin


class GuidBased(GuidPK, GeneralMethodMixin):
    """Абстрактный класс для классов основанных на guid"""
    pass


class IdBased(IdPK, GeneralMethodMixin):
    """Абстрактный класс для классов основанных на id"""
    pass
