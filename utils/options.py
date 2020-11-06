
def get_from_dict(d, *args, default=None):
    for arg in args:
        if arg in d.keys():
            return d[arg]
    return default

class Options:
    def __init__(self, **kwargs) -> None:
        self.debug_mode: bool = get_from_dict(kwargs, 'debug', 'debug_mode', default=False)
        self.auto_imports = get_from_dict(kwargs, 'imports', 'auto_imports', default=[])
        self.auto_eval_mod = get_from_dict(kwargs, 'eval_mod', 'auto_eval_mod', default=[])

    def __str__(self):
        return str(self.__dict__)
