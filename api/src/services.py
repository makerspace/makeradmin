import statistics
from collections import namedtuple

import box_terminator
import core
import member
import membership
import messages
import multiaccess
import multiaccessy
import quiz
import shop
import shop.accounting

Instance = namedtuple("Instance", "path,service")


services = (
    Instance(path="", service=core.service),
    Instance(path="/membership", service=membership.service),
    Instance(path="/webshop", service=shop.service),
    Instance(path="/webshop/accounting", service=shop.accounting.service),
    Instance(path="/member", service=member.service),
    Instance(path="/messages", service=messages.service),
    Instance(path="/statistics", service=statistics.service),
    Instance(path="/multiaccess", service=multiaccess.service),
    Instance(path="/quiz", service=quiz.service),
    Instance(path="/accessy", service=multiaccessy.service),
    Instance(path="/box_terminator", service=box_terminator.service),
)
