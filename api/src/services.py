from collections import namedtuple

import membership
import core


Instance = namedtuple("Instance", "path,service")


services = (
    Instance(path='', service=core.service),
    Instance(path='messages', service=membership.service)
)
