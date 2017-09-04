from collections import OrderedDict


def tree_constructor(source, parent_field='parent_id', id_field='id', func=None, func_args=None,
                     children='children', del_epmty_children=False):
    """
    Строит дерево из массива объектов SQLAlchemy, конвертируя объект в dict(). У объектов должен быть метод row2dict
    :param del_epmty_children <Bool> - если стоит true, то удаляет пустой ключ children
    :param func: функция, которая принимает первым аргуметом dict_item, а остальными func_args
    :param func_args: дополнительные аргументы функции
    :param source: массив объектов
    :param parent_field: имя поля, указывающее на идентификатор родителя
    :param id_field: имя поля содержащее  идентификатор объекта
    :return: Массив
    """
    result = list()
    source = [item.row2dict() for item in source]
    map_source = {item[id_field]: item for item in source}

    for item in source:
        parent_id = item.get(parent_field)
        if func is not None:
            func(item, func_args)
        if parent_id is not None:
            parent = map_source[parent_id]
            if parent.get(children) is None:
                parent[children] = list()
            parent[children].append(item)
        else:
            result.append(item)

    if del_epmty_children:
        for item in source:
            if item.get(children) is not None and len(item[children]) == 0:
                item.pop(children)
    return result


def find_tree_node(tree, target_id, id_field='id', children='children'):
    """
    Поиск элемента в дереве
    :param tree: <dict> - дерево
    :param target_id: искомое значение
    :param id_field: <str> поле идентификатор объекта
    :param children: <str> поле массив с подчиненными объектами
    :return: <tree_node> / None
    """
    result = None
    for node in tree.get(children):
        if node.get(id_field) == target_id:
            result = node
            break
        else:
            if node.get(children):
                result = find_tree_node(node, target_id, id_field, children)
            if result:
                break
    return result


def find_tree_nodes(tree, values, target_field='id', children='children', with_children=True, result=None):
    """
    Поиск элементов в дереве по target_field in values
    :param tree: <dict> - дерево
    :param values: искомые значения
    :param target_field: <str> поле по которому ищется значение
    :param children: <str> поле массив с подчиненными объектами
    :param with_children: <bool> параметр отвечает за добавление в результат ноды, которые имеют подчиненные ноды
    :return: [<tree_node>, ...]
    """
    if result is None:
        result = list()

    for node in tree.get(children):
        if node.get(target_field) in values:
            if with_children or not node.get(children):
                result.append(node)
        if node.get(children):
            find_tree_nodes(node, values, target_field, children, with_children, result)
    return result


def find_in_forest(forest, values, target_field, children):
    """
    Поиск элемента в массиве деревьев
    :param forest: [<dict>, ...] - массив деревьев
    :param values: искомые значения
    :param target_field: <str> поле по которому ищется значение
    :param children: <str> поле массив с подчиненными объектами
    :return: [<tree_node>, ...]
    :return:
    """
    result = list()

    for tree in forest:
        if tree.get(target_field) in values:
            result.append(tree)
        else:
            if tree.get(children):
                result.extend(find_in_forest(forest=tree[children], values=values, target_field=target_field, children=children))

    return result


def checked_branches(tree, check_field='checked', children='children'):
    """
    Сохранения ветвей дерева, в которых выбран хотябы 1 элемент.
    :param tree: массив объектов
    :return: массив ветвей
    """

    result = list()
    for item in tree:
        if item.get(check_field):
            result.append(item)
        elif item.get(children):
            _result = checked_branches(item[children], check_field, children)
            if _result:
                item[children] = _result
                result.append(item)
    return result


def merge_tree(tree, branches):
    """
    Слияние дерева - пустышки с выбранными ветвями этого же дерева
    """
    mapped_tree = {v['value']: v for v in tree}

    for branch in branches:
        if branch['value'] in mapped_tree:
            item = mapped_tree[branch['value']]
            if branch.get('checked'):
                item['checked'] = True
                if item.get('items'):
                    # рекурсивная простановка checked = True
                    tree_value_setter(item['items'], 'checked', value=True)
            else:
                if branch.get('items') and item.get('items'):
                    merge_tree(item['items'], branch['items'])
        else:
            raise Exception('There is no branch in original tree')


def tree_value_setter(tree, key_field='checked', value=None, children='items'):
    """
    Обход дерева и простановка значения value в поле key_field
    :param tree: древовидная структура данных
    :param key_field: <str>
    :param value:
    :param children: <str>
    """
    for item in tree:
        item[key_field] = value
        if item.get(children):
            tree_value_setter(item[children], key_field=key_field, value=value, children=children)


def identify_tree_items(tree, level):
    for item in tree:
        item['id'] = str(level)+'_'+str(item.get('value'))
        if item.get('items'):
            identify_tree_items(item['items'], level+1)


def value_collector(tree, target_field='id', children='children'):
    """
    Функция обходит дерево и собирает значения из полей target_field в список
    :param tree: <dict>
    :param target_field: <str>
    :param children: <str>
    :return: [ <значение>, ...]
    """
    result = list()
    if tree.get(target_field) is not None:
        result.append(tree[target_field])

    if tree.get(children):
        for node in tree[children]:
            result.extend(value_collector(node, target_field, children))

    return result


def tree_walker(tree, target_field=None, target_value=None, children='children',
                func=None, func_args=None, func_result=None, action=None):
    """
    :param tree: начальное дерево
    :param target_field: поле, в котором находится интересуещее нас значение
    :param target_value: требуемое значение
    :param children: поле с подитемами
    :param func: функция для выполнения действий над элементом
    :param func_args: дополнительные аргументы
    :param action: действия после функции (continue , break , None)
    :return:
    """
    if func_result is None:
        func_result = list()
    for item in tree:
        if item.get(target_field) == target_value:
            func_result.append(func(item, tree, func_args))
            if action == 'break':
                break
            elif action == 'continue':
                continue
        if item.get(children):
            tree_walker(item[children], target_field, target_value, children, func, func_args, func_result, action)
    return func_result


def tree_to_list(tree, children='children',  del_epmty_children=False):
    """
    Перестраивает дерево в список объектов
    :param tree:
    :param del_epmty_children - если стоит true, то удаляет пустой ключ children
    :param children: имя ключа отвечающего за детей
    :return:
    """
    result = []
    for item in tree:
        if item.get(children):
            item_children = item.pop(children)
            result.append(item)
            if len(item_children) > 0:
                result.extend(tree_to_list(item_children, children,  del_epmty_children))
        else:
            if del_epmty_children:
                item.pop(children)
            result.append(item)
    return result


def broken_tree_old(items, id_field='id', parent_id_field='parent_id', children_field='children'):
    """
    Создает дерево из упорядоченного словаря, где объекты могут ссылаться на несуществующих родителей.
    Объекты большей вложенности находятся в конце списка упорядоченного словаря. Сначала строится реверсивный список
    ключей словаря, потом этот список обходится и извлекается каждый объект словаря. Проверяется наличие его родителя и,
    в случае если родитель есть, то объект переносится в родителя, а иначе continue.
    :param items: <OrderDict>
    :param id_field: <str> - уникальный идентификатор объекта
    :param parent_id_field: <str> указывает на поле, ссылающееся на родителя
    :param children_field: <str> указывает  в какое поле "положить" потомка
    :return: items
    """
    item_id_list = [k for k in items]
    item_id_list.reverse()

    for i in item_id_list:
        cur_item = items[i]
        parent = items.get(getattr(cur_item, parent_id_field))
        if parent:
            if getattr(parent, children_field, None) is None:
                setattr(parent, children_field, list())
            ordered_dict = OrderedDict([(getattr(cur_item, id_field), cur_item)])
            getattr(parent, children_field).append(ordered_dict)
        else:
            continue
    return items


def broken_tree(elements, id_field='id', parent_id_field='parent_id', children_field='children'):
    """
    Функция пытается построить из списка словарей дерево.
    :param elements: [<dict>, ...]
    :param id_field: <str>
    :param parent_id_field: <str>
    :param children_field: <str>
    :return: [<dict>, ...]
    """
    result = list()
    element_map = {e[id_field]: e for e in elements}
    for e in elements:
        parent = element_map.get(e[parent_id_field])
        if parent:
            if parent.get(children_field) is None:
                parent[children_field] = list()
            parent[children_field].append(e)
        else:
            result.append(e)
    return result


def branches_lenght(tree, lenght_field, children_field='children', branch_lenght=0, result=None):
    """
    Функция рекурсивно определяет длинну ветвей дерева, получая "длинну" из поля lenght_field
    :param tree: [ ]
    :param lenght_field: <str>  из которого извлекается длинна
    :param children_field: <str>
    :param branch_lenght: длинна ветви
    :param result: [ ] список длинн ветвей
    :return: result
    """
    if result is None:
        result = []
    try:
        for key in tree:
            branch = tree[key]
            current_lenght = branch_lenght + getattr(branch, lenght_field)
            children = getattr(branch, children_field, None)
            if children:
                for child in children:
                    branches_lenght(child, lenght_field, children_field, current_lenght, result=result)
            else:
                result.append(current_lenght)
    except TypeError:
        raise Exception
    return result


def gis_tree_constructor(source, parent=None, parent_field='parent_id', id_field='id', func=None, func_args=None,
                         children='children', del_epmty_children=False):
    """
    Функция кастомизирована для отображения гис элементов в дереве.
    Строит дерево из массива объектов SQLAlchemy, конвертируя объект в массив. У объектов должен быть метод row2dict
    :param del_epmty_children - если стоит true, то удаляет пустой ключ children
    :param func: функция, которая принимает первым аргуметом dict_item, а остальными func_args
    :param func_args: дополнительные аргументы функции
    :param source: массив объектов
    :param parent: id родительского элемента
    :param parent_field: имя поля, указывающее на идентификатор родителя
    :param id_field: имя поля содержащее  идентификатор объекта
    :return: Массив
    """
    result = []
    for item in source:
        if getattr(item, parent_field) == parent:
            dict_item = item.row2dict(add_prop=['factors_count'])
            dict_item['text'] = item.text
            dict_item['tag'] = item.tag
            if func is not None:
                func(dict_item, func_args)
            dict_item.update({children: gis_tree_constructor(source=source,
                                                             parent=dict_item[id_field],
                                                             parent_field=parent_field,
                                                             id_field=id_field,
                                                             func=func,
                                                             func_args=func_args,
                                                             children=children,
                                                             del_epmty_children=del_epmty_children)})
            if del_epmty_children and len(dict_item[children]) == 0:
                dict_item.pop(children)
            result.append(dict_item)
    return result

if __name__ == '__main__':
    test_tree = [
        dict(c=False, children=list(), n=1),
        dict(
            c=False,
            children=[
                dict(c=False, children=list(), n='2.1'),
                dict(
                    c=False,
                    children=[
                        dict(c=False, children=list(), n='2.2.1'),
                        dict(c=True, children=list(), n='2.2.2'),
                    ],
                    n='2.2'
                ),
            ],
            n=2),

        dict(
            c=False,
            children=[
                dict(c=False, children=list(), n='3.1'),
                dict(
                    c=False,
                    children=[
                        dict(c=False, children=list(), n='3.2.1'),
                        dict(c=False, children=list(), n='3.2.2'),
                    ],
                    n='2.2'
                ),
            ],
            n=3),
        dict(
            c=False,
            children=[
                dict(
                    c=True,
                    children=[
                        dict(c=False, children=list(), n='4.2.1'),
                        dict(c=False, children=list(), n='4.2.2'),
                    ],
                    n='4.1'),
            ],
            n=4)
    ]

    r = checked_branches(test_tree, check_field='c', children='children')