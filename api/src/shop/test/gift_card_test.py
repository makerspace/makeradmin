from unittest import TestCase

from shop.gift_card_util import generate_gift_card_code


class GiftCardTest(TestCase):
    def test_generate_validation_code_default_length(self):
        validation_code = generate_gift_card_code()
        msg = "Test failed: validation code is not 16 characters long."
        self.assertEqual(len(validation_code), 16, msg=msg)

    def test_generate_validation_code_custom_length(self):
        validation_code = generate_gift_card_code(32)
        msg = "Test failed: validation code is not 32 characters long."
        self.assertEqual(len(validation_code), 32, msg=msg)

    def test_generate_validation_code_unique(self):
        validation_code_1 = generate_gift_card_code()
        validation_code_2 = generate_gift_card_code()
        msg = "Test failed: validation codes are not unique."
        self.assertNotEqual(validation_code_1, validation_code_2, msg=msg)
