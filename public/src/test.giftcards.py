from public import app
import unittest
import pytest

class GiftcardsTest(unittest.TestCase):
    
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
    def test_giftcards_page(self):
        response = self.app.get('/giftcards/')
        self.assertEqual(self.app.get('/giftcards/').status_code, 200)
    def test_giftcards_confirmation(self):
        response = self.app.get('/giftcards/confirmation')
        self.assertEqual(self.app.get('/giftcards/confirmation').status_code, 200)
    def test_giftcards_fin(self):
        response = self.app.get('/giftcards/finish')
        self.assertEqual(self.app.get('/giftcards/finish').status_code, 200)
    
if __name__ == '__main__':
        unittest.main()

