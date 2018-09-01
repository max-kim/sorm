# Simple SQLite ORM - 'sORM'

Allows to use Python objects instead of SQLite statements.

## Installation

You can install 'sORM' with these commands:
```bash
    $ mkdir <installation dir>
    $ cd /<installation dir>
    $ git clone git://github.com/max-kim/sorm.git
    $ cd sorm
```

## Requirements

- Python 3.6 (or over)

## Usage

#### How to make the connection and create the tables:
```python
    from sorm import create_connection
    from sorm import IntType, FloatType, StrType, BytesType, ForeignKey, Base, Relationship
    from sorm import Base, ForeignKey, Relationship

    connection = create_connection('sorm_test.db', echo=True)


    class Group(Base):
        __tablename__ = 'groups'

        id = IntType(__tablename__, 'id', primary_key=True)
        group_name = StrType(__tablename__, 'group_name', nullable=False)


    class User(Base):
        __tablename__ = 'users'

        id = IntType(__tablename__, 'id', primary_key=True)
        user_name = StrType(__tablename__, 'user_name', nullable=False)
        group_id = IntType(__tablename__, 'group_id', ForeignKey(Group, 'id'))

        group = Relationship(group_id)

    connection = create_connection('sorm_test.db', echo=True)
    connection.create_table(Group, User)

    # Also you can use next syntax to create table:
    # <<< Group.create(connection)
```
**Important:** For the best way, use 'id' attribute as primary key within your every tables.

Use 'echo=True' as 'create_connection' parameter to show every sql queries.

#### How to insert data:
```python
    group = Group(group_name='Admins')
    connection.add(group)
    connection.add(Group(**{'group_name': 'Users'}))

    connection.add(User(**{'user_name': 'Max', 'group_id': None}))
    connection.add(User(**{'user_name': 'Alex', 'group_id': None}))
```
The field 'id' will be added and filled automatically.

#### How to select data:
```python
    groups = connection.query(Group).order_by(Group.id).all()
```
The result returns as tuple of objects:
```python
    print(type(group)) # >>> <class 'tuple'>
    for group in groups:
        print('The group id = {}, group name is {}.'.format(group.id, group.group_name))
```

When you call 'first()' method, you get an object or 'None' if the query does not match any data.
```python
    admin_group = connection.query(Group).where((Group.group_name, '=', 'Admins')).first()
```

#### How to make an update:
```python
    if admin_group:
        user = connection.update(User).where((User.user_name, '=', 'Alex'),
                                             (User.id, '=', 2)).value(group_id=admin_group.id)
        print(user)
```
Update query returns tuple of objects any time or empty tuple if conditions does not fit anything.

#### Deletion the data:
```python
    connection.delete(Group).where((Group.id, '>=', 3))
```
or:
```python
    some_user = User(id=5)
    connection.delete(some_user)

    # connection.delete(some_user) == connection.delete(User).where((User.id, '=', 5))
```
The deletion statement returns 'None' any time.

## Other

This library is a homewokr for OTUS Python web-dev.
