from pyoreol import DBSession


class IdPK:
    """Миксин, добавляет методы get_item и get_list для классов с PK int типа"""
    
    @classmethod
    def get_list(cls, ids=None, order_by=None):
        """
        Получение списка элементов
        :param ids: [<int>, ...]
        :param order_by: <str> поле по которому будет проведена сортировка
        :return: [<SQLAlchemy>, ...]
        """
        query = DBSession.query(cls)
        if ids:
            query = query.filter(cls.id.in_(ids))
        if order_by:
            query = query.order_by(getattr(cls, order_by))
        return query.all()
    
    @classmethod
    def get_item(cls, id):
        """
        Получение объекта
        :param id: <int>
        :return: <SQLAlchemy>
        """
        return DBSession.query(cls).filter(cls.id == id).one()
