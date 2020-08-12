import React from 'react';
import OrderList from "./OrderList";
import OrderShow from "./OrderShow";
import ProductList from "./ProductList";
import ProductAdd from "./ProductAdd";
import ProductEdit from "./ProductEdit";
import CategoryList from "./CategoryList";
import { Route, Switch } from 'react-router-dom';

export default ({ match }) => (
    <Switch>
        <Route path={`${match.path}/`} exact component={OrderList} />
        <Route path={`${match.path}/order`} component={OrderList} />
        <Route path={`${match.path}/order/:id`} component={OrderShow} />
        <Route path={`${match.path}/product`} component={ProductList} />
        <Route path={`${match.path}/product/add`} component={ProductAdd} />
        <Route path={`${match.path}/product/:id`} component={ProductEdit} />
        <Route path={`${match.path}/category`} component={CategoryList} />
    </Switch>
);
