from aid.test.base import VALID_NON_3DS_CARD_NO, EXPIRES_CVC_ZIP, ShopTestMixin
from aid.test.selenium import SeleniumTest
from aid.test.util import SELENIUM_BASE_TIMEOUT


class Test(ShopTestMixin, SeleniumTest):
    
    products = [
        dict(price=200, unit="st", smallest_multiple=1),
    ]
    
    def test_buying_an_item_in_shop_works(self):
        self.login_member()

        # Shop
        
        self.browse_shop()
        
        div = self.wait_for_element(id=f"product-{self.p0_id}")
        self.assertEqual(self.api.product['name'], div.find_element_by_class_name('product-title').text)
        
        div.find_element_by_css_selector('button.number-add').click()
        
        self.wait_for_element(id='cart-sum').click()
    
        # Cart
    
        self.webdriver.switch_to.frame(self.wait_for_element(tag="iframe", timeout=SELENIUM_BASE_TIMEOUT))

        card = self.wait_for_element(name="cardnumber")
        card.send_keys(VALID_NON_3DS_CARD_NO)
        card.send_keys(EXPIRES_CVC_ZIP)
        
        self.webdriver.switch_to.default_content()
        
        self.wait_for_element(id='pay-button').click()
        self.assertIn("Kvitto", self.wait_for_element(css=".receipt-header", timeout=SELENIUM_BASE_TIMEOUT * 12).text)

        # Recipt
        
        self.assertIn(f"{self.p0_price:.2f} kr", self.wait_for_element(css=".receipt-amount-value").text)
        
        self.assertIn(f"{self.member['firstname']} {self.member['lastname']} #{self.member['member_number']}",
                      self.wait_for_element(id="receipt-content").text)

        # Check actual transaction.

        transaction_id = self.webdriver.execute_script('return window.transactionId;')
        
        self.get(f"/webshop/transaction/{transaction_id}").expect(
            code=200,
            status="ok",
            data__amount=f"{self.p0_price:.2f}",
            data__member_id=self.member_id,
            data__status="completed",
        )

        data = self.get(f"/webshop/transaction/{transaction_id}/content").expect(code=200, status="ok").data
        self.assertEqual(self.p0_id, data[0]['product_id'])
        self.assertEqual(1, len(data))
