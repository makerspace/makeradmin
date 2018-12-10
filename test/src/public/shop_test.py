import time

from library.base import VALID_NON_3DS_CARD_NO, EXPIRES_CVC_ZIP
from library.selenium import SeleniumTest


class Test(SeleniumTest):
    
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.api.create_category()
        self.api.create_product(price=200, unit="st", smallest_multiple=1)
        
    @classmethod
    def tearDownClass(self):
        self.api.delete_product()
        self.api.delete_category()
        super().tearDownClass()
    
    def test_buying_an_item_in_shop_works(self):
        member = self.api.create_member()
        product = self.api.product
        self.login_member()
        
        # Shop
        
        self.browse_shop()
        
        div = self.wait_for_element(id=f"product-{product['id']}")
        self.assertEqual(self.api.product['name'], div.find_element_by_class_name('product-title').text)
        
        div.find_element_by_css_selector('button.number-add').click()
        
        self.wait_for_element(id='cart-sum').click()
    
        # Cart
    
        self.webdriver.switch_to.frame(self.wait_for_element(tag="iframe"))

        card = self.wait_for_element(name="cardnumber")
        card.send_keys(VALID_NON_3DS_CARD_NO)
        card.send_keys(EXPIRES_CVC_ZIP)
        
        self.webdriver.switch_to.default_content()
        
        self.wait_for_element(id='pay-button').click()

        # Recipt
        
        self.assertIn("Kvitto", self.wait_for_element(css=".receipt-id", timeout=24).text)
        
        self.assertIn(f"{product['price']} kr", self.wait_for_element(css=".receipt-amount-value").text)
        
        self.assertIn(f"{member['firstname']} {member['lastname']} #{member['member_number']}",
                      self.wait_for_element(id="receipt-content").text)

        # Check actual transaction.

        transaction_id = self.webdriver.execute_script('return window.transactionId;')
        
        self.get(f"/webshop/transaction/{transaction_id}").expect(
            code=200,
            status="ok",
            data__amount=product['price'],
            data__member_id=member['member_id'],
            data__status="completed",
        )

        data = self.get(f"/webshop/transaction/{transaction_id}/content").expect(code=200, status="ok").data
        self.assertEqual(product['id'], data[0]['product_id'])
        self.assertEqual(1, len(data))
