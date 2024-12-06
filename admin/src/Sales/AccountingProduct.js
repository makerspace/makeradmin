import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Select from "react-select";
import * as _ from "underscore";
import CollectionTable from "../Components/CollectionTable";
import Currency from "../Components/Currency";
import SearchBox from "../Components/SearchBox";
import Collection from "../Models/Collection";
import Product from "../Models/Product";
import ProductAccountsCostCenters from "../Models/ProductAccountsCostCenters";
import { get } from "../gateway";
import { showError } from "../message";

const AccountingProduct = () => {
    const [categories, setCategories] = useState(null);
    const [transactionAccount, setTransactionAccount] = useState(null);
    const [transactionCostCenter, setTransactionCostCenter] = useState(null);
    const [selectedOptionAccount, setSelectedOptionAccount] = useState(null);
    const [showOptionsAccount, setShowOptionsAccount] = useState([]);
    const [selectedOptionCostCenter, setSelectedOptionCostCenter] =
        useState(null);
    const [showOptionsCostCenter, setShowOptionsCostCenter] = useState([]);
    const [selectedProductId, setSelectedProductId] = useState([]);

    const collection = new Collection({
        type: Product,
        url: "/webshop/product",
        expand: "product_accounting",
        page: 1,
        pageSize: 0,
        filter_out_key: "type",
        filter_out_value: "debit",
        includeDeleted: true,
    });

    useEffect(() => {
        // Fetch categories
        get({ url: "/webshop/category", params: { page_size: 0 } })
            .then((data) => {
                const fetchedCategories = _.reduce(
                    data.data,
                    (obj, item) => {
                        obj[item.id] = item.name;
                        return obj;
                    },
                    {},
                );
                setCategories(fetchedCategories);
            })
            .catch((error) => {
                showError("<h2>Failed to find categories</h2>" + error.message);
            });

        // Fetch transaction accounts
        get({ url: "/webshop/transaction_account", params: { page_size: 0 } })
            .then((data) => {
                const fetchedAccounts = _.reduce(
                    data.data,
                    (obj, item) => {
                        obj[item.id] = item.account;
                        return obj;
                    },
                    {},
                );
                setTransactionAccount(fetchedAccounts);
                setShowOptionsAccount(
                    [
                        {
                            account: "No modification",
                            id: 0,
                            description: "Do not change account",
                        },
                    ].concat(data.data),
                );
            })
            .catch((error) => {
                showError(
                    "<h2>Failed to find transaction accounts</h2>" +
                        error.message,
                );
            });

        // Fetch transaction cost centers
        get({
            url: "/webshop/transaction_cost_center",
            params: { page_size: 0 },
        })
            .then((data) => {
                const fetchedCostCenters = _.reduce(
                    data.data,
                    (obj, item) => {
                        obj[item.id] = item.cost_center;
                        return obj;
                    },
                    {},
                );
                setTransactionCostCenter(fetchedCostCenters);
                setShowOptionsCostCenter(
                    [
                        {
                            cost_center: "No modification",
                            id: 0,
                            description: "Do not change cost center",
                        },
                    ].concat(data.data),
                );
            })
            .catch((error) => {
                showError(
                    "<h2>Failed to find transaction cost centers</h2>" +
                        error.message,
                );
            });
    }, []);

    const onSave = (account, costCenter) => {
        selectedProductId.forEach((productId) => {
            get({ url: "/webshop/accounting", params: { page_size: 0 } }).then(
                (data) => {
                    const accountings = data.data;
                    const currentAccounting = accountings.find(
                        (p) => p.product_id === productId,
                    );

                    const accountingElementCredit =
                        new ProductAccountsCostCenters(currentAccounting);
                    accountingElementCredit.product_id = productId;
                    accountingElementCredit.type = "credit";
                    accountingElementCredit.fraction = 100;

                    if (account && account.id !== 0) {
                        accountingElementCredit.account_id = account.id;
                    }
                    if (costCenter && costCenter.id !== 0) {
                        accountingElementCredit.cost_center_id = costCenter.id;
                    }

                    return accountingElementCredit.save().then(() => {
                        collection.fetch();
                    });
                },
            );
        });

        setSelectedProductId([]);
    };

    const setSelectedRow = (event, element) => {
        // const tableIndex = collection.items.findIndex((item) => item.id === element.id);
        if (selectedProductId.includes(element.id)) {
            setSelectedProductId((prev) =>
                prev.filter((id) => id !== element.id),
            );
        } else {
            setSelectedProductId((prev) => [...prev, element.id]);
        }
    };

    return (
        <div>
            <div className="uk-margin-top">
                <h2>Hantera produkter för bokföring</h2>
                <p>
                    På denna sida kan du ange och ta bort konton och
                    kostnadsställen för produkter. Markera en eller flera
                    produkter i listan och välj vilket konto och kostnadsställe
                    du vill applicera.
                </p>
            </div>

            <form
                className="uk-form uk-form-stacked"
                onSubmit={(e) => {
                    e.preventDefault();
                    onSave(selectedOptionAccount, selectedOptionCostCenter);
                }}
            >
                <fieldset className="uk-margin-top">
                    <label className="uk-form-label">Välj konto</label>
                    <Select
                        options={showOptionsAccount}
                        value={selectedOptionAccount}
                        getOptionValue={(g) => g.id}
                        getOptionLabel={(g) =>
                            `${g.account} : ${g.description}`
                        }
                        onChange={(account) =>
                            setSelectedOptionAccount(account)
                        }
                    />

                    <label className="uk-form-label">Välj kostnadsställe</label>
                    <Select
                        options={showOptionsCostCenter}
                        value={selectedOptionCostCenter}
                        getOptionValue={(g) => g.id}
                        getOptionLabel={(g) =>
                            `${g.cost_center} : ${g.description}`
                        }
                        onChange={(costCenter) =>
                            setSelectedOptionCostCenter(costCenter)
                        }
                    />
                </fieldset>

                <button className="uk-button uk-button-success uk-float-right">
                    <i className="uk-icon-save" /> Applicera val på markerade
                    produkter
                </button>
            </form>

            <div className="uk-margin-top">
                <SearchBox handleChange={() => {}} />

                <CollectionTable
                    collection={collection}
                    emptyMessage="Inga produkter"
                    columns={[
                        { title: "Namn", sort: "name" },
                        { title: "Kategori", sort: "category_id" },
                        {
                            title: "Pris",
                            sort: "price",
                            class: "uk-text-right",
                        },
                        { title: "Enhet", sort: "unit" },
                        { title: "Konto", sort: "account_id" },
                        { title: "Kostnadsställe", sort: "cost_center_id" },
                    ]}
                    rowComponent={({ item }) => (
                        <tr onClick={(event) => setSelectedRow(event, item)}>
                            <td>
                                <Link to={`/sales/product/${item.id}`}>
                                    {item.name}
                                </Link>
                            </td>
                            <td>
                                {categories
                                    ? categories[item.category_id]
                                    : item.category_id}
                            </td>
                            <td className="uk-text-right">
                                <Currency value={item.price * 100} /> kr
                            </td>
                            <td>{item.unit}</td>
                            <td>{transactionAccount?.[item.account_id]}</td>
                            <td>
                                {transactionCostCenter?.[item.cost_center_id]}
                            </td>
                        </tr>
                    )}
                />
            </div>
        </div>
    );
};

export default AccountingProduct;
