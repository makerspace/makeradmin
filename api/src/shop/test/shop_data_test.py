from typing import Any, Dict, List, Optional, Set, Tuple, cast

import core.models
import membership.models
import messages.models
import shop.models
from shop.shop_data import get_product_data_by_special_id
from shop.stripe_constants import MakerspaceMetadataKeys
from test_aid.test_base import FlaskTestBase


class ShopDataTest(FlaskTestBase):
    models = [membership.models, messages.models, shop.models, core.models]

    def test_get_product_data_by_special_id_finds_product(self) -> None:
        category = self.db.create_category(name="test category")
        makeradmin_test_product = self.db.create_product(
            name="test found",
            category_id=category.id,
            product_metadata={
                MakerspaceMetadataKeys.SPECIAL_PRODUCT_ID.value: "found",
            },
        )
        # Make sure we don't match on value whic contains the special id as substring
        self.db.create_product(
            name="test not found",
            category_id=category.id,
            product_metadata={
                MakerspaceMetadataKeys.SPECIAL_PRODUCT_ID.value: "not found",
            },
        )
        # Make sure we don't match on keys that are substrings of the special id
        self.db.create_product(
            name="test not found key",
            category_id=category.id,
            product_metadata={
                "found": "not found",
            },
        )
        self.db.create_product(
            name="test not found no meta",
            category_id=category.id,
        )

        found_product = get_product_data_by_special_id("found")
        assert found_product is not None
        assert found_product.id == makeradmin_test_product.id
        assert found_product.name == makeradmin_test_product.name

    def test_get_product_data_by_special_id_not_found(self) -> None:
        category = self.db.create_category(name="test category")
        self.db.create_product(
            name="test not found",
            category_id=category.id,
            product_metadata={
                MakerspaceMetadataKeys.SPECIAL_PRODUCT_ID.value: "not found",
            },
        )
        self.db.create_product(
            name="test not found key",
            category_id=category.id,
            product_metadata={
                "found": "not found",
            },
        )
        self.db.create_product(
            name="test not found no meta",
            category_id=category.id,
        )

        found_product = get_product_data_by_special_id("found")
        assert found_product is None
