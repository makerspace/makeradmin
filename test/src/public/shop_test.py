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
        self.api.create_member()
        self.login_member()
        self.browse_shop()
        self.wait_for_element(css=".product")
        self.webdriver.save_screenshot("/tmp/fil.png")
