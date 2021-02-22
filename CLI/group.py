class Group:
    """Represents a chat group.
    This structure is a collection of Member types and supports various standard collection methods.
    """

    def __init__(self):
        self.members = []

    def add(self, name, conn, is_manager=False):
        self.members.append(Member(name, conn, is_manager))

    def kick(self, key):
        if type(key) == Member:
            member = key
        elif type(key) == str:
            member = self[key]
        else:
            raise TypeError
        member.conn.close()
        self.members.remove(member)

    def __iter__(self):
        yield from self.members

    def __getitem__(self, key):
        for member in self.members:
            if member.name == key:
                return member
        raise KeyError(key)

    def __len__(self):
        return len(self.members)

    def __contains__(self, key):
        if type(key) == Member:
            return key in self.members
        try:
            self[key]
            return True
        except KeyError:
            return False


class Member(object):
    """Represents a group member.
    This structure stores information about a group's member.
    """

    def __init__(self, name, conn, is_manager=False, is_muted=False):
        self.name = name  # immutable
        # dname = display name, changes when a member is promoted/demoted.
        self.dname = ('@' if is_manager else '') + name
        self.conn = conn
        self._is_manager = is_manager
        self.is_muted = is_muted
        self.conn.setblocking(0)

    @property
    def is_manager(self):
        return self._is_manager

    @is_manager.setter
    def is_manager(self, val):
        self._is_manager = val
        if val is True and self.dname[0] != '@':
            self.dname = '@' + self.dname
        elif self.dname[0] == '@':
            self.dname = self.dname[1:]

    def __str__(self):
        return self.dname
