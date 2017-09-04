from pyoreol import DBSession


class AliasMixin:
    """Добавляет методы выборки по столбцам алиасам. Алиасы должны быть уникальными"""

    @classmethod
    def aliased_list(cls, aliases):
        """
        Выборка элементов по алиасу
        :param aliases: [<str>, ...]
        :return: [<SQLAlchemy>, ...]
        """
        query = DBSession.query(cls).filter(cls.alias != None)
        if aliases:
            query = query.filter(cls.alias.in_(aliases))
        return query.all()

    @classmethod
    def aliased_item(cls, alias):
        return DBSession.query(cls).filter(cls.alias == alias).one()
