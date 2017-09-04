import datetime
from my_libs.utils import datetime2str


class GeneralMethodMixin:
    """Добавляет методы:
    - создания объекта
    - сохранения объекта
    - обновления объекта
    - удаления объекта
    - конвертации объекта в словарь."""

    dbsession = None

    def row2dict(self, b=None, add_prop=None, strict_mode=True):
        """
        :param b: список колонок, которые не должны добавляться в словарь
        :return: словарь
        """
        d = dict()
        if not b:
            b = list()

        for c in self.__table__.columns:
            if c.name not in b:
                value = getattr(self, c.name)
                if isinstance(value, datetime.datetime):
                    value = datetime2str(date_time=value)
                elif isinstance(value, datetime.timedelta):
                    value = str(value)
                d[c.name] = value

        if add_prop:
            for k in add_prop:
                try:
                    value = getattr(self, k)
                    if isinstance(value, datetime.datetime):
                        value = datetime2str(date_time=value)
                    elif isinstance(value, datetime.timedelta):
                        value = str(value)
                    d[k] = value
                except AttributeError:
                    if strict_mode:
                        raise AttributeError('Аттрибут %s неопределен' % k)
        return d

    @classmethod
    def create(cls, data, exclude=('id',), flush=False):
        """Создание объекта"""
        columns = {c.name for c in cls.__table__.columns if c.name not in exclude}
        result = {k: v for k, v in data.items() if k in columns}
        item = cls(**result)
        item.save(flush=flush)
        return item

    def save(self, dbsession=None, flush=False):
        """Сохранение элемента в базе данных. :param dbsession(deprecated) - Объект сессии. :param flush - булевой
         параметр, отвечащий за моментальный сброс в БД"""
        if self.dbsession is None:
            raise AttributeError('Session not exist')
        else:
            self.dbsession.add(self)
            if flush:
                self.dbsession.flush()
        return self

    def update(self, data, exclude=('id',)):
        """Обновление данных объекта"""
        for column in self.__table__.columns:
            if column.name in exclude:
                continue
            if column.name in data:
                data_value = data.get(column.name)
                if column.nullable is False and data_value is None:
                    raise ValueError('Field "{}" is not nullable'.format(column.name))
                else:
                    setattr(self, column.name, data_value)

    def remove(self, dbsession=None, flush=False):
        """Удаление элемента из базы данных. :param dbsession - Объект сессии(deprecated). :param flush - булевой
         параметр, отвечащий за моментальный сброс в БД"""
        if self.dbsession is None:
            raise AttributeError('Session not exist')
        else:
            self.dbsession.delete(self)
            if flush:
                self.dbsession.flush()
