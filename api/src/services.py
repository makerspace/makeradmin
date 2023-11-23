from collections import namedtuple

import member
import membership
import core
import messages
import multiaccess
import shop
import statistics
import quiz

Instance = namedtuple("Instance", "path,service")


services = (
    Instance(path="", service=core.service),
    Instance(path="/membership", service=membership.service),
    Instance(path="/webshop", service=shop.service),
    Instance(path="/member", service=member.service),
    Instance(path="/messages", service=messages.service),
    Instance(path="/statistics", service=statistics.service),
    Instance(path="/multiaccess", service=multiaccess.service),
    Instance(path="/quiz", service=quiz.service),
)
