from typing import TypedDict, List, Dict

SltxUrl = str
SltxDriver = str
SltxStrPattern = str
SltxStrKey = str


# we use a value constructor to allow for '-' in TypedDict
SltxDependency = TypedDict('SltxDependency', {
   'url': SltxUrl,
   'driver': SltxDriver,
   'grab-files': List[SltxStrPattern]
}, total=False)  # keys are optional


SltxDependencies = Dict[SltxStrKey, SltxDependency]
