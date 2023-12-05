from unittest import TestCase
from ..gift_card_util import generate_gift_card_code


class GiftCardTest(TestCase):
    def test_generate_validation_code_default_length(self):
        validation_code = generate_gift_card_code()
        self.assertEqual(len(validation_code), 16)

    def test_generate_validation_code_custom_length(self):
        validation_code = generate_gift_card_code(32)
        self.assertEqual(len(validation_code), 32)

    def test_generate_validation_code_unique(self):
        validation_code_1 = generate_gift_card_code()
        validation_code_2 = generate_gift_card_code()
        self.assertNotEqual(validation_code_1, validation_code_2)