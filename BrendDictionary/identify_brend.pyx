cpdef str identify_brend(str sku_row, list brand_rightholders, list main_identifires, list main_limit_identifires, list add_limit_identifires, list excluding_identifires):
    """
    Определение бренда по заданному SKU.
    Заданному SKU соответствует оозначение бренда из brand_rightholders, если он содержит один из основных идентификаторов из соответствующего списка из main_identifires,
    один из основных ограничивающих идентификаторов из соответствующего списка из main_limit_identifires, если он не пустой,
    один из ддополнительных ограничивающих идентификаторов из соответствующего списка из main_limit_identifires, если он не пустой,
    не содержит ни одного из исключающих идентификаторов из excluding_identifires.
    Работает аналогично функции identify_brend, но быстрее засчет использования Cython

    :param sku_row: SKU, по которому определяется бренд
    :param brand_rightholders: список обозначений бренда
    :param main_identifires: список основных идентификаторов
    :param main_limit_identifires: список основных ограничивающих идентификаторов
    :param add_limit_identifires: список дополнительных ограничивающих идентификаторов
    :param excluding_identifires: список исключающих идентификаторов
    :return: обозначение бренда из brand_rightholders или пустая строка, если бренд не удается определить
    """
    # Типизация используемых переменных
    cdef int i
    cdef bint pos, limit_id_found, excluding_id_found
    cdef str main_id, main_limit_id, add_limit_id, excluding_id
    # Перебор всех брендов из словаря
    for i in range(len(brand_rightholders)):
        # Перебор основых идентификаторов
        for main_id in main_identifires[i]:
            # Определение, содержатся ли основной идентификатор в заднном SKU
            pos = main_id in sku_row
            # Если основной идентификатор найден
            if pos:
                # Флаг "ограничивающие идентификаторы найдены"
                limit_id_found = False
                # Если есть основные ограничивающие идентификаторы
                if len(main_limit_identifires[i]) > 0:
                    # Перебор основных ограничивающих идентификаторов
                    for main_limit_id in main_limit_identifires[i]:
                        # Определение, содержатся ли основной ограничивающий идентификатор в заднном SKU
                        pos = main_limit_id in sku_row
                        # Если основной ограничивающий идентификатор найден
                        if pos:
                            # Если есть дополнительные ограничивающие идентификаторы
                            if len(add_limit_identifires[i]) > 0:
                                # Перебор дополнительных ограничивающих идентификаторов
                                for add_limit_id in add_limit_identifires[i]:
                                    # Определение, содержатся ли дополнительный ограничивающий идентификатор в заднном SKU
                                    pos = add_limit_id in sku_row
                                    # Если дополнительный ограничивающий идентификатор найден
                                    if pos:
                                        # Выставляется флаг "ограничивающие идентификаторы найдены", цикл поиска дополнительных ограничивающих идентификаторов прерывается
                                        limit_id_found = True
                                        break
                            # Если дополнительных ограничивающих идентификаторов нет
                            else:
                                # Выставляется флаг "ограничивающие идентификаторы найдены"
                                limit_id_found = True
                        # если "ограничивающие идентификаторы найдены", цикл поиска дополнительных ограничивающих идентификаторов прерывается
                        if limit_id_found:
                            break
                # Если основных ограничивающих идентификаторов нет
                else:
                    # Выставляется флаг "ограничивающие идентификаторы найдены"
                    limit_id_found = True
                # если "ограничивающие идентификаторы найдены", начинается поиск исключающих идентификаторов
                if limit_id_found:
                    # Флаг "исключающий дентификатор найден"
                    excluding_id_found = False
                    # Перебор исключающих идентификаторов
                    for excluding_id in excluding_identifires[i]:
                        # Определение, содержатся ли исключающий идентификатор в заднном SKU
                        pos = excluding_id in sku_row
                        # Если исключающий идентификатор найден
                        if pos:
                            # Выставляется флаг "исключающий дентификатор найден", цикл поиска исключающих идентификаторов прерывается
                            excluding_id_found = True
                            break
                # Если "ограничивающие идентификаторы найдены" и не "исключающий дентификатор найден"
                if limit_id_found and not excluding_id_found:
                    # Возвращается соответствующее обозначение бренда
                    return brand_rightholders[i]
    # Если не найдено не одного подходящего бренда, возвращается пустая строка
    return ''