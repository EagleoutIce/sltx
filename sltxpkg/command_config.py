
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
	def __init__(self, cmds:dict):
		self.cmds = cmds

	def helper_values(self):
		return map(lambda x: x[0], self.cmds.values())

	def generate(self, p):
		for command in self.cmds.items():
			add_parser(p, command[0], command[1][2], **((dict(command[1][1].kwargs, aliases=command[1][0][1])) if len(command[1][0][1]) != 0 else command[1][1].kwargs))