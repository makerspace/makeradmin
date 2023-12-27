import React from 'react';
import OrderList from "./OrderList";
import OrderShow from "./OrderShow";
import GiftCardList from "./GiftCardList";
import GiftCardShow from "./GiftCardShow";
import ProductList from "./ProductList";
import ProductAdd from "./ProductAdd";
import ProductEdit from "./ProductEdit";
import CategoryList from "./CategoryList";
import { Route, Switch } from 'react-router-dom';
import ImageList from "./ImageList";

export default ({ match }) => (
    <Switch>
        <Route path={`${match.path}/`} exact component={OrderList} />
        <Route path={`${match.path}/order`} exact component={OrderList} />
        <Route path={`${match.path}/order/:id`} component={OrderShow} />
        <Route path={`${match.path}/gift-card`} exact component={GiftCardList} />
        <Route path={`${match.path}/gift-card/:id`} component={GiftCardShow} />
        <Route path={`${match.path}/product`} exact component={ProductList} />
        <Route path={`${match.path}/product/add`} component={ProductAdd} />
        <Route path={`${match.path}/product/:id`} component={ProductEdit} />
        <Route path={`${match.path}/category`} exact component={CategoryList} />
        <Route path={`${match.path}/image`} exact component={ImageList} />
    </Switch>
);
