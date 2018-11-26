from factory import Faker, Dict, Factory


class MemberFactory(Factory):
    class Meta:
        model = dict
    
    email = Faker('email')
    firstname = Faker('first_name')
    lastname = Faker('last_name')
