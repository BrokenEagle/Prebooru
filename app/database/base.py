# APP/DATABASE/BASE.PY

# ##PYTHON IMPORTS
import time
import functools

# ##LOCAL IMPORTS
from ..logical.file import PutGetJSON

# ##FUNCTIONS


def InitializeIDIndexes(tables):
    return functools.reduce(lambda acc, key: {**acc, **{key: {}}}, tables, {})


def LoadDatabaseFile(name, filepath, tables, unicode):
    print("Loading %s..." % name)
    data = PutGetJSON(filepath, 'rb', None, unicode)
    if data is None:
        print("Loading default.")
        data = functools.reduce(lambda acc, key: {**acc, **{key: []}}, tables, {})
        SaveDatabaseFile(name, data, filepath, unicode)
        return data
    if CheckTables(name, data, tables):
        SaveDatabaseFile(name, data, filepath, unicode)
    return data


def CheckTables(name, data, tables):
    dirty = False
    for table in tables:
        if table not in data:
            print("%s DB - Adding missing table:" % name, table)
            data[table] = []
            dirty = True
    for table in data:
        if table not in tables:
            print("%s DB - Dropping obsolete table:" % name, table)
            dirty = True
    return dirty


def SaveDatabaseFile(name, database, filepath, unicode):
    print("Saving %s..." % name)
    for i in range(3):
        optype = 'wb' if unicode else 'w'
        if PutGetJSON(filepath, optype, database, unicode) >= 0:
            return
        time.sleep(1)
    print("Unable to save database!")
    raise


def SetIndexes(id_indexes, other_indexes, database):
    SetIDIndexes(id_indexes, database)
    SetOtherIndexes(other_indexes, database)


def SetIDIndexes(indexes, database):
    for table in indexes:
        for item in database[table]:
            indexes[table][item['id']] = item


def SetOtherIndexes(indexes, database):
    for table in indexes:
        for key in indexes[table]:
            for item in database[table]:
                indexes[table][key][item[key]] = item


def CommitData(database, table, id_indexes, other_indexes, data):
    database[table].append(data)
    id_indexes[table][data['id']] = data
    for key in other_indexes[table]:
        other_indexes[table][key][data[key]] = data


def FindByID(indexes, table, id):
    return indexes[table][id] if id in indexes[table] else None


def FindBy(indexes, database, table, key, value):
    if key in indexes[table]:
        return indexes[table][key][value] if value in indexes[table][key] else None
    # Return the first matching value for non-indexed data
    return next(filter(lambda x: x[key] == value, database[table]), None)


def GetCurrentIndex(database, type):
    return database[type][-1]['id'] if len(database[type]) else 0
