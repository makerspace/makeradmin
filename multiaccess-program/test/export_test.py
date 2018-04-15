import json

from destroyer.export import export_to_json
from test.db_base import DbBaseTest
from test.factory import UserFactory, CustomerFactory
from test.util import dt_format, dt_cet_local


class Test(DbBaseTest):
    
    def test_simple_export_case(self):
        customer = CustomerFactory()
        u1_stop = dt_cet_local(self.datetime())
        u1 = UserFactory(
            stop_timestamp=u1_stop,
            customer_id=customer.id,
        )
        u2_stop = dt_cet_local(self.datetime())
        u2 = UserFactory(
            stop_timestamp=u2_stop,
            customer_id=customer.id,
        )
        
        data = json.loads(export_to_json(self.session, customer.id))

        self.assertEqual(
            [
                dict(
                    member_id=int(u1.name),
                    rfid_tag=u1.card,
                    end_timestamp=dt_format(u1_stop),
                ),
                dict(
                    member_id=int(u2.name),
                    rfid_tag=u2.card,
                    end_timestamp=dt_format(u2_stop),
                ),
            ],
            data)


