# coding: utf-8

def flat(_list):
    """ [(1, 2), (3, 4)] -> [1, 2, 3, 4]"""
    return sum([list(item) for item in _list], [])


def dict_to_tuple(_dict):
    """ {'a': {'b': 'c'}, 'd': {'e': 'f'}} -> (('a', ('b', 'c')), ('d', ('e', 'f')))"""
    if not isinstance(_dict, dict):
        return _dict
    return tuple([(k, dict_to_tuple(v)) for k, v in _dict.items()])
