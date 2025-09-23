import React, { Children } from "react";
import { Route, Routes } from "react-router-dom";
import { RedirectToSubpage } from "../Components/Routes";
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
import { Navigate } from "react-router-dom";

const routes = [
    {
        index: true,
        element: <Navigate to="order" replace />,
    },
    {
        path: "order",
        element: <OrderList />,
    },
    {
        path: "order/:id",
        element: <OrderShow />,
    },
    {
        path: "gift-card",
        element: <GiftCardList />,
    },
    {
        path: "gift-card/:id",
        element: <GiftCardShow />,
    },
    {
        path: "product",
        element: <ProductList />,
    },
    {
        path: "product/add",
        element: <ProductAdd />,
    },
    {
        path: "product/:id",
        element: <ProductEdit />,
    },
    {
        path: "category",
        element: <CategoryList />,
    },
    {
        path: "image",
        element: <ImageList />,
    },
    {
        path: "accounting/*",
        element: <AccountingBox />,
        children: [
            {
                index: true,
                element: <RedirectToSubpage subpage="exporting" />,
            },
            {
                path: "exporting",
                element: <AccountingExport />,
            },
            {
                path: "overview-product",
                element: <AccountingProduct />,
            },
            {
                path: "account",
                element: <AccountingAccount />,
            },
            {
                path: "cost-center",
                element: <AccountingCostCenter />,
            },
        ],
    },
];

export default routes;
