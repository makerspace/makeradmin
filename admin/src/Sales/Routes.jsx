import React from 'react';
import OrderList from "./OrderList";
import OrderShow from "./OrderShow";
import ProductList from "./ProductList";
import ProductAdd from "./ProductAdd";
import ProductEdit from "./ProductEdit";
import CategoryList from "./CategoryList";
import TransactionAccountAdd from "./TransactionAccountAdd";
import TransactionAccountBox from "./TransactionAccountBox";
import TransactionAccountBoxEditInfo from "./TransactionAccountBoxEditInfo";
import TransactionAccountBoxProducts from "./TransactionAccountBoxProducts";
import TransactionAccountList from "./TransactionAccountList";
import { Route, Switch } from 'react-router-dom';
import ImageList from "./ImageList";

const TransactionAccount = ({ match: { path } }) => (
    <TransactionAccountBox>
        <Switch>
            <Route exact path={`${path}/`} component={TransactionAccountBoxEditInfo} />
            <Route path={`${path}/info`} component={TransactionAccountBoxEditInfo} />
            <Route path={`${path}/products`} component={TransactionAccountBoxProducts} />
        </Switch>
    </TransactionAccountBox>
);

const TransactionAccounts = ({ match: { path } }) => (
    <Switch>
        <Route exact path={path} component={TransactionAccountList} />
        <Route path={`${path}/add`} component={TransactionAccountAdd} />
        <Route path={`${path}/:transaction_account_id`} component={TransactionAccount} />
    </Switch>
);

export default ({ match }) => (
    <Switch>
        <Route path={`${match.path}/`} exact component={OrderList} />
        <Route path={`${match.path}/order`} exact component={OrderList} />
        <Route path={`${match.path}/order/:id`} component={OrderShow} />
        <Route path={`${match.path}/product`} exact component={ProductList} />
        <Route path={`${match.path}/product/add`} component={ProductAdd} />
        <Route path={`${match.path}/product/:id`} component={ProductEdit} />
        <Route path={`${match.path}/category`} exact component={CategoryList} />
        <Route path={`${match.path}/transaction_accounts`} component={TransactionAccounts} />
        <Route path={`${match.path}/image`} exact component={ImageList} />
    </Switch>
);
