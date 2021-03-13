def add_argument_to_parser(p, *args, **kwargs):
    p.add_argument(*args, **kwargs)


def add_parser(p, name, arguments, **kwargs):
    np = p.add_parser(name, **kwargs)
    for args in arguments:
        add_argument_to_parser(np, *args.args, **args.kwargs)


class Arg:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class Commands:
    def __init__(self, cmds: dict):
        self.cmds = cmds

    def helper_values(self):
        return map(lambda x: x[0], self.cmds.values())

    def generate(self, p):
        for command in self.cmds.items():
            aliases = Commands.__alias_from_cmd(command)
            add_parser(p, command[0], command[1][2], **((dict(command[1][1].kwargs,
                                                              aliases=aliases)) if len(aliases) != 0 else command[1][1].kwargs))

    @staticmethod
    def __alias_from_cmd(alias: tuple) -> list:
        return alias[1][0][1]

    def __cmd_from_name(self, tc: str):
        return self.cmds[tc][0][0]

    def __find_in_alias(self, tc: str):
        matching_commands = [
            alias[0]
            for alias in self.cmds.items()
            if tc in Commands.__alias_from_cmd(alias)]
        # if multiple we take the first (should not happen)
        return self.__cmd_from_name(matching_commands[0])

    def get_cmd(self, search_key: str):
        return self.__cmd_from_name(search_key) if search_key in self.cmds else self.__find_in_alias(search_key)
