from hashlib import md5
import datetime
import re
from collections import OrderedDict
from dateutil.parser import parse
from dateutil.tz import tzlocal
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import compiler


def datetime_now(to_string=False, set_seconds_null=True):
    """
    Возвращает объект datetime с учетом поясного времени. При флаге to_string = True, возвращает строковое представление
    :param to_string: <Bool>
    :return: <datetime>
    """
    dt = datetime.datetime.now(tzlocal())
    if to_string:
        dt = datetime2str(dt, set_seconds_null=set_seconds_null)
    return dt


def datetime2str(date_time=None, delta=None, set_seconds_null=True):
    """
    :param date_time  - datetime obj
    :param delta - timedelta obj
    :param set_seconds_null: <bool>
    :return: возвращает  текущее UTC datetime в формате YYYY-MM-DDTHH:MM:SS
    """

    if date_time and delta:
        date_time = (date_time + delta)
    elif date_time == None and delta:
        date_time = (datetime.datetime.now(tzlocal()) + delta)
    elif delta == None and date_time:
        pass
    else:
        date_time = datetime.datetime.now(tzlocal())

    date_time = date_time.replace(microsecond=0)
    if set_seconds_null:
        date_time = date_time.replace(second=0)
    return date_time.isoformat()


def delta_iso(timedelta, round_down=False):
    """
    :param timedelta - объект timedelta
    :param round_down: <bool>  отвечает за округление в меньшую сторону
    :return количество часов
    """
    hours, remainder = divmod(timedelta.total_seconds(), 3600)
    if remainder > 1799 and not round_down:
        return int(hours)+1
    else:
        return int(hours)


def iso2roundedDT(str_datetime):
    """
    Парсит строковое datetime и обнуляет секунды и микросекунды
    :param str_datetime:
    :return:
    """
    t = parse(str_datetime)
    return t.replace(second=0, microsecond=0)


def pretty_format(dt):
    """
    Возвращает время в формате " номер дня название месяца год"
    :param dt: <datetime>
    :return: <str>
    """
    months = ',января,февраля,марта,апреля,мая,июня,июля,августа,сентября,октября,ноября,декабря'.split(',')
    return '{c1}{day}{c2} {month} {year}'.format(c1=chr(171),
                                                 day=dt.day,
                                                 c2=chr(187),
                                                 month=months[dt.month],
                                                 year=dt.year)


def russian_format(dt):
    """
    форматирование объекта времени
    """
    return dt.strftime('%d.%m.%Y %H:%M')


def isostr2datetime(str_dt, dt_format='%H:%M %d-%m-%Y'):
    """
    Производит реформат строкового представления datetime
    :param str_dt:
    :param dt_format: новый формат
    :return:
    """
    new_dt = parse(str_dt)
    new_dt = new_dt.strftime(dt_format)
    return new_dt


def isotime2hours(time):
    """
    Переводит дату из iso формата в часы
    :param time:
    :return:
    """
    result = re.findall(r'\d+', time)
    result = list(map(lambda x: int(x), result))
    return result[2]*24+result[3]


class TimedeltaConverter:

    def __init__(self, td=None, with_days=True, with_hours=True, with_minutes=True, with_seconds=True):
        if td is None:
            td = datetime.timedelta()
        self.total_seconds = td.total_seconds()
        self._with_days = with_days
        self._with_hours = with_hours
        self._with_minutes = with_minutes
        self._with_seconds = with_seconds

        self.days = None
        self.hours = None
        self.minutes = None
        self.seconds = None

        self.timedelta_converter()

    def timedelta_converter(self):
        """
        Высчитывает количество дней, часов, минут и секунд из объекта timedelta.
        """
        seconds = self.total_seconds

        if self._with_days:
            self.days, seconds = divmod(seconds, 3600*24)

        if self._with_hours:
            self.hours, seconds = divmod(seconds, 3600)

        if self._with_minutes:
            self.minutes, seconds = divmod(seconds, 60)

        if self._with_seconds:
            self.seconds = seconds

        return self

    def switch_params(self, with_days=None, with_hours=None, with_minutes=None, with_seconds=None):
        """
        Переключение параметров объекта и последующий пересчет времени
        """
        if with_days is not None:
            self._with_days = with_days
            self.days = None

        if with_hours is not None:
            self._with_hours = with_hours
            self.hours = None

        if with_minutes is not None:
            self._with_minutes = with_minutes
            self.minutes = None

        if with_seconds is not None:
            self._with_seconds = with_seconds
            self.seconds = None

        self.timedelta_converter()
        return self

    def __sub__(self, other):
        if isinstance(other, datetime.timedelta):
            other = other.total_seconds()
        elif isinstance(other, TimedeltaConverter):
            other = other.total_seconds
        elif isinstance(other, int):
            pass
        else:
            raise TypeError('Argument must be an instance of the timedelta or integer')
        seconds = self.total_seconds - other
        return TimedeltaConverter(datetime.timedelta(seconds=seconds), self._with_days,
                                  self._with_hours, self._with_minutes, self._with_seconds)

    @property
    def to_hours(self):
        """
        Возвращает общее количество часов, округляя в меньшую сторону
        """
        return int(self.total_seconds // 3600)

    @property
    def todict(self):
        """
        Возвращает время в виде словаря
        """
        return dict(days=self.days, hours=self.hours, minutes=self.minutes, seconds=self.seconds)


def sign(initials=None, surname=None, display_name=None):
    """Получение ФИО"""
    if initials and surname:
        result = '{}. {}'.format(initials.split('.')[0], surname)
    elif display_name:
        result = str()
        name = [word for word in display_name.split(' ') if word]
        if name:
            result = name[0]
            if len(name) == 2:
                result = '{}. {}'.format(name[1][0], result)
            elif len(name) == 3:
                result = '{}. {}. {}'.format(name[1][0], name[2][0], result)

    else:
        result = 'Не назначен'
    return result


def row2dict(row, b=None, add_prop=None, strict_mode=True):
    """
    :param row: Объект строки таблицы
    :param b: список колонок, которые не должны добавляться в словарь
    :return: словарь
    """
    d = {}
    if not b:
        b = []

    for c in row.__table__.columns:
        if c.name not in b:
            value = getattr(row, c.name)
            if isinstance(value, datetime.datetime):
                value = datetime2str(date_time=value)
            elif isinstance(value, datetime.timedelta):
                value = str(value)
            d[c.name] = value

    if add_prop:

        for k in add_prop:
            try:
                value = getattr(row, k)
                if isinstance(value, datetime.datetime):
                    value = datetime2str(date_time=value)
                elif isinstance(value, datetime.timedelta):
                    value = str(value)
                d[k] = value
            except AttributeError:
                if strict_mode:
                    raise AttributeError('Аттрибут %s неопределен' % k)
    return d


def mass_row2dict(rows, block=None, add_prop=None, strict_mode=True):
    result = []
    for row in rows:
        result.append(row2dict(row, block, add_prop=add_prop, strict_mode=strict_mode))
    return result


def print_traceback():
    import sys, traceback
    traceback.print_exc(file=sys.stdout)


class Profiler:
    """
    конструкция With для замера времени исполнения кода
    """
    mark = 1

    def __init__(self, name=None):
        if name:
            self.name = name
        else:
            self.name = 'Point %s' % Profiler.mark
            Profiler.mark += 1

    def __enter__(self):
        self.__startTime = datetime.datetime.now()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.time = datetime.datetime.now() - self.__startTime
        print("%s: time %s" % (self.name, self.time))


def grouping_items(items, key, func=None):
    """
    Группирует список элементов по ключу
    :param items: [<obj>, ...]
    :param key: <str> - имя ключа, по которому происходит группировка
    :param func: Функция, которая обрабатывает item  перед тем, как item будет добавлен в результат
    :return:
    {
        <key> : [<obj>, ...], ...
    }
    """
    result = dict()
    tmp = set()

    for item in items:
        item_value = new_getattr(item, key)

        if item_value not in tmp:
            tmp.add(item_value)
            result[item_value] = list()
        if func:
            item = func(item)
        result[item_value].append(item)

    return result


def list_to_dict(items, key, value_is_list=False):
    """
    Функция преобразует список объектов\словарей в словарь с ключем key и значением item
    :param items: [<object>, ...]
    :param key: <str> - значение ключевого поля
    :param value_is_list: значение ключа - массив
    :return:
    """
    if value_is_list:
        result = dict()
        for item in items:
            k = new_getattr(item, key)
            if result.get(k) is None:
                result[k] = list()
            result[k].append(item)
    else:
        result = {new_getattr(item, key): item for item in items}
    return result


def list_to_ordered_dict(items, key, is_dict=False):
    """
    Функция преобразует список объектов\словарей в упорядоченный словарь с ключем key и значением item
    :param items:
    :param key:
    :param is_dict: - список состоит из словарей или объектов
    :return:
    """
    if is_dict:
        l = [(item[key], item) for item in items]
    else:
        l = [(getattr(item, key), item) for item in items]
    return OrderedDict(l)


def new_getattr(item, key):
    """
    Метод извлекает значение по ключу из словаря или экземпляра любого другого класса
    :param item: <dict> or <obj>
    :param key: <str>
    """
    if item.__class__.__name__ == 'dict':
        value = item.get(key)
    else:
        value = getattr(item, key, None)
    return value


def new_setattr(item, key, value):
    """
    Универсальный setattr
    :param item: <dict> or <obj>
    :param key: <str>
    :param value: any
    """
    if item.__class__.__name__ == 'dict':
        item[key] = value
    else:
        setattr(item, key, value)


def add_slashes(main_string, protected_string, add_double_quites=True):
    """
    Метод экранирует последовательность символов
    :param main_string: <str>
    :param protected_string: <str>
    :param add_double_quites: <bool> добавляет двойные кавычки вначале и вконце новой строки
    :return: <str>
    """
    pstring = r'\\' + protected_string
    new_string = main_string.replace(protected_string, pstring)
    if add_double_quites:
        new_string = '"' + new_string + '"'
    return new_string


def compile_query(query):
    dialect = query.session.bind.dialect
    statement = query.statement
    comp = compiler.SQLCompiler(dialect, statement)
    comp.compile()
    params = dict()
    for k, v in comp.params.items():
        params[k] = "'%s'" % str(v)
    return str(query.statement.compile(dialect=postgresql.dialect())) % params


def md5hash(ustring):
    """Преобразует юникод строку в md5 hash
    :param ustring: <str>"""
    if ustring is not None:
        m = md5()
        m.update(ustring.encode())
        return m.hexdigest()


def text_cutter(text, max_simbols=200):
    """Ф-ция обрезает текст, если его длинна больше max_simbols"""
    if len(text) > max_simbols:
        text = text[:max_simbols] + '...'
    return text
