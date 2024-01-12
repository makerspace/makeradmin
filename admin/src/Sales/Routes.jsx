import React from "react";
import OrderList from "./OrderList";
import OrderShow from "./OrderShow";
import GiftCardList from "./GiftCardList";
import GiftCardShow from "./GiftCardShow";
import ProductList from "./ProductList";
import ProductAdd from "./ProductAdd";
import ProductEdit from "./ProductEdit";
import CategoryList from "./CategoryList";
import { Route, Switch } from "react-router-dom";
import ImageList from "./ImageList";
import AccountingBox from "./AccountingBox";
import AccountingExport from "./AccountingExport";
import AccountingAccount from "./AccountingAccount";
import AccountingCostCenter from "./AccountingCostCenter";
import AccountingProduct from "./AccountingProduct";
const Accounting = ({ match: { path } }) => (
    <AccountingBox>
        <Switch>
            <Route exact path={`${path}/`} component={AccountingExport} />
            <Route path={`${path}/exporting`} component={AccountingExport} />
            <Route
                path={`${path}/overview-product`}
                component={AccountingProduct}
            />
            <Route path={`${path}/account`} component={AccountingAccount} />
            <Route
                path={`${path}/cost-center`}
                component={AccountingCostCenter}
            />
        </Switch>
    </AccountingBox>
);

export default ({ match }) => (
    <Switch>
        <Route path={`${match.path}/`} exact component={OrderList} />
        <Route path={`${match.path}/order`} exact component={OrderList} />
        <Route path={`${match.path}/order/:id`} component={OrderShow} />
        <Route
            path={`${match.path}/gift-card`}
            exact
            component={GiftCardList}
        />
        <Route path={`${match.path}/gift-card/:id`} component={GiftCardShow} />
        <Route path={`${match.path}/product`} exact component={ProductList} />
        <Route path={`${match.path}/product/add`} component={ProductAdd} />
        <Route path={`${match.path}/product/:id`} component={ProductEdit} />
        <Route path={`${match.path}/category`} exact component={CategoryList} />
        <Route path={`${match.path}/image`} exact component={ImageList} />
        <Route path={`${match.path}/accounting`} component={Accounting} />
    </Switch>
);
