import React from "react";
import { Route, Switch } from "react-router-dom";
import { defaultSubpageRoute } from "../Components/Routes";
import AccountingAccount from "./AccountingAccount";
import AccountingBox from "./AccountingBox";
import AccountingCostCenter from "./AccountingCostCenter";
import AccountingExport from "./AccountingExport";
import AccountingProduct from "./AccountingProduct";
import CategoryList from "./CategoryList";
import GiftCardList from "./GiftCardList";
import GiftCardShow from "./GiftCardShow";
import ImageList from "./ImageList";
import OrderList from "./OrderList";
import OrderShow from "./OrderShow";
import ProductAdd from "./ProductAdd";
import ProductEdit from "./ProductEdit";
import ProductList from "./ProductList";
const Accounting = ({ match: { path } }) => (
    <AccountingBox>
        <Switch>
            {defaultSubpageRoute({ matchpath: path, subpage: "exporting" })}
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
        {defaultSubpageRoute({ matchpath: match.path, subpage: "order" })}
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
