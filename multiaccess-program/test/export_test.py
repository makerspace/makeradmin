import json

from multi_access.export import export_to_json
from test.db_base import DbBaseTest
from test.factory import UserFactory, CustomerFactory
from multi_access.util import dt_format, dt_cet_local


class Test(DbBaseTest):
    
    def test_simple_export_case(self):
        customer = CustomerFactory()
        u1_stop = dt_cet_local(self.datetime())
        u1 = UserFactory(
            stop_timestamp=u1_stop,
            customer=customer,
        )
        u2 = UserFactory(
            stop_timestamp=None,
            customer=customer,
        )
        
        data = json.loads(export_to_json(self.session, customer.id))

        self.assertEqual(
            [
                dict(
                    member_number=int(u1.name),
                    rfid_tag=u1.card,
                    end_timestamp=dt_format(u1_stop),
                ),
                dict(
                    member_number=int(u2.name),
                    rfid_tag=u2.card,
                    end_timestamp=None,
                ),
            ],
            data)

    def test_export_bad_member_is_filterd(self):
        customer = CustomerFactory()
        u1 = UserFactory(
            name="1234 Things",
            customer=customer,
        )
        
        data = json.loads(export_to_json(self.session, customer.id))

        self.assertEqual([], data)
        
    def test_does_not_export_data_for_other_custoemr(self):
        c1 = CustomerFactory()
        u1 = UserFactory(customer=c1)

        c2 = CustomerFactory()
        u2 = UserFactory(customer=c2)
        
        c3 = CustomerFactory()
        u3 = UserFactory(customer=c3)

        data = json.loads(export_to_json(self.session, c2.id))

        self.assertEqual(1, len(data))
        self.assertEqual(int(u2.name), data[0]['member_number'])


