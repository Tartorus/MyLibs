from pyoreol import DBSession


class GuidPK:
    """Миксин, добавляет методы get_item и get_list для классов с PK UUID типа"""

    @classmethod
    def get_list(cls, guids=None):
        """
        Получение списка элементов
        :param guids: [<UUID>, ...]
        :return: [<SQLAlchemy>, ...]
        """
        query = DBSession.query(cls)
        if guids:
            query = query.cls.filter(cls.guid.in_(guids))
        return query.all()

    @classmethod
    def qlist(cls, guids=None):
        """Получение запроса
        :param guids: [<UUID>, ...]
        :return: query
        """
        query = DBSession.query(cls)
        if guids:
            query = query.cls.filter(cls.guid.in_(guids))
        return query

    @classmethod
    def get_item(cls, guid):
        """
        Получение объекта
        :param guid: <UUID>
        :return: <SQLAlchemy>
        """
        return DBSession.query(cls).filter(cls.guid == guid).one()
