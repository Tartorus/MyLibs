from ldap3 import Server, ALL, Connection, NTLM

__author__ = 'iliyas'


def user_list(server_adress, domain, user_name, user_password, search_base=None,
              ldap_filter=None, sids=None, attrib=None):
    """
    Получение пользователей по их SIDам
    :param sids: список SID
    :param search_base:
    :param ldap_filter:
    :param attrib: [<str>, ...] - список дополнительных атрибутов
    :return: возвращает словарь сключами "SID" и значениеями равным словарям {"attrib": "value"}
    """
    server = Server(server_adress, get_info=ALL)
    conn = Connection(server, user=domain+'\\'+user_name, password=user_password, authentication=NTLM, auto_bind=True)

    if attrib is None:
        attrib = ['description', 'initials', 'sn', 'title']

    if search_base is None:
        search_base = ''
        for dc in domain.split('.'):
            search_base += 'dc=%s, ' % dc
        search_base = search_base[:-2]

    if ldap_filter is None:
        clauses = ''
        if sids is None or not isinstance(sids, list) or len(sids) == 0:
            raise AttributeError("Отсутвует фильтр и список sid'ов")

        for sid in sids:
            clauses += '(objectsid=%s)' % sid
        ldap_filter = "(&(objectclass=user)(|%s))" % clauses
    conn.search(search_base=search_base,
                search_filter=ldap_filter,
                attributes=['displayName', 'objectSid'] + attrib
                )
    result = {}

    for c in conn.entries:
        buf = c.entry_get_attributes_dict()
        user = {}

        for i in buf:
            user[i] = buf[i][0]

        result[user['objectSid']] = user

    return result


def ad_user(server_adress, domain, ldap_user_name, ldap_user_password, user='*',
            search_base=None, ldap_filter=None, attrib=None):
    """
    Функция ищет информацию о пользователе (-ях) в актив директори делая выборку по FQDN пользователя
    :param server_adress: ip адресс АД сервера
    :param domain: домен
    :param ldap_user_name: имя пользователя с доступом к AD
    :param ldap_user_password:
    :param user: FQDN искомого пользователя
    :param search_base:
    :param ldap_filter: <str>
    :param attrib: [<str> ...] список атррибутов для поиска
    :return: массив словарей {}
    """
    if attrib is None:
        attrib = ['description', 'initials', 'sn', 'title', 'displayName']

    server = Server(server_adress, get_info=ALL)
    conn = Connection(server, user=domain+'\\'+ldap_user_name, password=ldap_user_password,
                      authentication=NTLM, auto_bind=True)

    if search_base is None:
        search_base = ''

        for dc in domain.split('.'):
            search_base += 'dc=%s, ' % dc

        search_base = search_base[:-2]

    if not ldap_filter:
        ldap_filter = "(&(objectclass=user)(sAMAccountName=%s))" % user

    conn.search(
                search_base=search_base,
                search_filter=ldap_filter,
                attributes=['displayName', 'objectSID']+attrib
                )
    result = [e.entry_get_attributes_dict() for e in conn.entries]
    if result:
        result = [{key: item[key][0] for key in item} for item in result]
    return result


def get_user_sids(logins, server_adress, domain, ldap_user_name, ldap_user_password):
    """Список сидов пользователей. :param logins - список логинов пользователй, чей сид требуется получить"""

    accounts = ''
    for login in logins:
        accounts += '(sAMAccountName=%s)' % login
    ldap_filter = "(&(objectclass=user)(|%s))" % accounts
    result = ad_user(
        server_adress=server_adress,
        domain=domain,
        ldap_user_name=ldap_user_name,
        ldap_user_password=ldap_user_password,
        ldap_filter=ldap_filter
    )

    return [r['objectSid'] for r in result]
