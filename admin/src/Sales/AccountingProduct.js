import React from "react";
import { Link } from "react-router-dom";
import Select from "react-select";
import * as _ from "underscore";
import CollectionTable from "../Components/CollectionTable";
import Currency from "../Components/Currency";
import SearchBox from "../Components/SearchBox";
import Collection from "../Models/Collection";
import CollectionNavigation from "../Models/CollectionNavigation";
import Product from "../Models/Product";
import ProductAccountsCostCenters from "../Models/ProductAccountsCostCenters";
import { get } from "../gateway";
import { showError } from "../message";

const filterOptions_account = (items_account, options_account) => {
    const current = new Set(items_account.map((i) => i.id));
    return options_account.filter((o) => !current.has(o.id));
};

const filterOptions_cost_center = (items_cost_center, options_cost_center) => {
    const current = new Set(items_cost_center.map((i) => i.id));
    return options_cost_center.filter((o) => !current.has(o.id));
};

const updateOptions_account = (options_account) => (prevState) => {
    let options = [
        {
            account: "No modification",
            id: 0,
            description: "Do not change account",
        },
    ].concat(filterOptions_account(prevState.items_account, options_account));
    return {
        showOptions_account: options,
        options_account,
    };
};

const updateOptions_cost_center = (options_cost_center) => (prevState) => {
    let options = [
        {
            cost_center: "No modification",
            id: 0,
            description: "Do not change cost center",
        },
    ].concat(
        filterOptions_cost_center(
            prevState.items_cost_center,
            options_cost_center,
        ),
    );
    return {
        showOptions_cost_center: options,
        options_cost_center,
    };
};

class AccountingProduct extends CollectionNavigation {
    constructor(props) {
        super(props);
        const { search, page } = this.state;
        this.collection = new Collection({
            type: Product,
            url: "/webshop/product",
            expand: "product_accounting",
            search: search,
            page: page,
            pageSize: 0,
            filter_out_key: "type",
            filter_out_value: "debit",
            includeDeleted: true,
        });
        this.state = {
            categories: null,
            items_account: [],
            options_account: [],
            selectedOption_account: null,
            items_cost_center: [],
            options_cost_center: [],
            selectedOption_cost_center: null,
            accounts: null,
            cost_centers: null,
            selected_product_id: [],
            latest_selected_row_index: null,
        };

        this.product = new Product();
        this.product_accounts_cost_centers = new ProductAccountsCostCenters();

        get({ url: "/webshop/category", params: { page_size: 0 } })
            .then(
                (data) => {
                    const categories = _.reduce(
                        data.data,
                        (obj, item) => {
                            obj[item.id] = item.name;
                            return obj;
                        },
                        {},
                    );
                    this.setState({ categories });
                },
                () => null,
            )
            .catch((error) => {
                showError("<h2>Failed to find categories</h2>" + error.message);
            });

        get({
            url: "/webshop/transaction_account",
            params: { page_size: 0 },
        })
            .then(
                (data) => {
                    const transaction_account = _.reduce(
                        data.data,
                        (obj, item) => {
                            obj[item.id] = item.account;
                            return obj;
                        },
                        {},
                    );
                    this.setState({ transaction_account });
                    this.setState(updateOptions_account(data.data));
                },
                () => null,
            )
            .catch((error) => {
                showError(
                    "<h2>Failed to find transaction accounts</h2>" +
                        error.message,
                );
            });

        get({
            url: "/webshop/transaction_cost_center",
            params: { page_size: 0 },
        })
            .then(
                (data) => {
                    const transaction_cost_center = _.reduce(
                        data.data,
                        (obj, item) => {
                            obj[item.id] = item.cost_center;
                            return obj;
                        },
                        {},
                    );
                    this.setState({ transaction_cost_center });
                    this.setState(updateOptions_cost_center(data.data));
                },
                () => null,
            )
            .catch((error) => {
                showError(
                    "<h2>Failed to find transaction cost centers</h2>" +
                        error.message,
                );
            });
    }

    selectOptionAccount(account) {
        this.setState({ selectedOption_account: account });
    }

    selectOptionCostCenter(cost_center) {
        this.setState({ selectedOption_cost_center: cost_center });
    }

    deserialize(x) {
        return x;
    }

    changeColor(activate = true, table_index) {
        const row = document.getElementsByTagName("tr");
        table_index.forEach(colorRows);

        function colorRows(id) {
            if (activate) {
                row[id + 1].style.backgroundColor = "#ddd";
            } else {
                row[id + 1].style.backgroundColor = "";
            }
        }
    }

    onSave(account, cost_center) {
        const productIds = this.state.selected_product_id;

        productIds.forEach((product_id) => {
            get({ url: "/webshop/accounting", params: { page_size: 0 } })
                .then((data) => {
                    const accountings = data.data;
                    const current_accounting = accountings.filter(
                        (p) => p.product_id === product_id,
                    );
                    const accounting_element_debit =
                        new ProductAccountsCostCenters(
                            current_accounting.filter(
                                (p) => p.type === "debit",
                            )[0],
                        );
                    accounting_element_debit.product_id = product_id;
                    accounting_element_debit.type = "debit";
                    accounting_element_debit.account_id = 1;
                    accounting_element_debit.fraction = 100;
                    accounting_element_debit.save().then(() => {
                        accounting_element_debit.reset();
                    });
                    const accounting_element_credit =
                        new ProductAccountsCostCenters(
                            current_accounting.filter(
                                (p) => p.type === "credit",
                            )[0],
                        );
                    accounting_element_credit.product_id = product_id;
                    accounting_element_credit.type = "credit";
                    accounting_element_credit.fraction = 100;

                    if (account && account.id !== 0) {
                        accounting_element_credit.account_id = account.id;
                    }
                    if (cost_center && cost_center.id !== 0) {
                        accounting_element_credit.cost_center_id =
                            cost_center.id;
                    }
                    return accounting_element_credit;
                })
                .then((accounting_element_credit) => {
                    accounting_element_credit.save().then(() => {
                        accounting_element_credit.reset();
                        this.collection.fetch();
                    });
                    return accounting_element_credit;
                });
        });

        if (this.state.selected_product_id.length > 0) {
            const table_index = [];
            this.state.selected_product_id.forEach((product_id) => {
                table_index.push(
                    this.collection.items
                        .map(function (e) {
                            return e.saved.id;
                        })
                        .indexOf(product_id),
                );
            });
            this.changeColor(false, table_index);
        }

        this.setState({ selected_product_id: [] });
        this.setState({ latest_selected_row_index: null });
    }

    updateAddSelectedProductId(current_product_ids, element) {
        if (Array.isArray(element)) {
            this.setState({
                selected_product_id: current_product_ids.concat(element),
            });
        } else {
            this.setState({
                selected_product_id: current_product_ids.concat([element]),
            });
        }
    }

    updateRemoveSelectedProductId(current_product_ids, element) {
        this.setState({
            selected_product_id: current_product_ids.filter(
                (item) => item !== element,
            ),
        });
    }

    updateResetSelectedProductId(element = null, table_index = []) {
        if (this.state.selected_product_id.length > 0) {
            const indices_to_deselect = [];
            this.state.selected_product_id.forEach((product_id) => {
                indices_to_deselect.push(
                    this.collection.items
                        .map(function (e) {
                            return e.saved.id;
                        })
                        .indexOf(product_id),
                );
            });
            this.changeColor(false, indices_to_deselect);
        }
        this.setState({ selected_product_id: [element] });
        this.changeColor(true, [table_index]);
    }

    updateLatestSelectedRowIndex(element) {
        this.setState({ latest_selected_row_index: element });
    }

    setSelectedRow(evt, element) {
        const table_index = this.collection.items
            .map(function (e) {
                return e.saved.id;
            })
            .indexOf(element.id);
        const selected_product_id = this.state.selected_product_id;
        const latest_selected_row_index = this.state.latest_selected_row_index;

        if (selected_product_id.indexOf(element.id) > -1) {
            this.changeColor(false, [table_index]);
            this.updateRemoveSelectedProductId(selected_product_id, element.id);
        } else {
            if (evt.shiftKey) {
                if (latest_selected_row_index === null) {
                    this.changeColor(true, [table_index]);
                    this.updateAddSelectedProductId(
                        selected_product_id,
                        element.id,
                    );
                } else {
                    const new_product_id = [];
                    const new_table_index = [];
                    if (table_index > latest_selected_row_index) {
                        for (
                            let i = latest_selected_row_index + 1;
                            i <= table_index;
                            i++
                        ) {
                            if (
                                selected_product_id.indexOf(
                                    this.collection.items[i].id,
                                ) === -1
                            ) {
                                new_product_id.push(
                                    this.collection.items[i].id,
                                );
                                new_table_index.push(i);
                            }
                        }
                    } else {
                        for (
                            let i = table_index;
                            i <= latest_selected_row_index - 1;
                            i++
                        ) {
                            if (
                                selected_product_id.indexOf(
                                    this.collection.items[i].id,
                                ) === -1
                            ) {
                                new_product_id.push(
                                    this.collection.items[i].id,
                                );
                                new_table_index.push(i);
                            }
                        }
                    }
                    this.changeColor(true, new_table_index);
                    this.updateAddSelectedProductId(
                        selected_product_id,
                        new_product_id,
                    );
                }
                this.updateLatestSelectedRowIndex(table_index);
            } else if (evt.ctrlKey) {
                this.changeColor(true, [table_index]);
                this.updateAddSelectedProductId(
                    selected_product_id,
                    element.id,
                );
                this.updateLatestSelectedRowIndex(table_index);
            } else {
                this.updateResetSelectedProductId(element.id, table_index);
                this.updateLatestSelectedRowIndex(table_index);
            }
        }
    }

    render() {
        const { categories, transaction_account, transaction_cost_center } =
            this.state;
        const {
            selectedOption_account,
            showOptions_account,
            selectedOption_cost_center,
            showOptions_cost_center,
        } = this.state;

        return (
            <div>
                <div className="uk-margin-top">
                    <h2>Hantera produkter för bokföring</h2>
                    <p>
                        På denna sida kan du ange och ta bort konton och
                        kostnadsställen för produkter. Markera en eller flera
                        produkter i listan och välj vilket konto och
                        kostnadsställe du vill applicera.
                    </p>
                </div>

                <form
                    className="uk-form uk-form-stacked"
                    onSubmit={(e) => {
                        e.preventDefault();
                        this.onSave(
                            selectedOption_account,
                            selectedOption_cost_center,
                        );
                        return false;
                    }}
                >
                    <fieldset className="uk-margin-top">
                        <label className="uk-form-label" htmlFor="">
                            Välj konto
                        </label>
                        <Select
                            name="account_selection"
                            className="uk-select"
                            tabIndex={1}
                            options={showOptions_account}
                            value={selectedOption_account}
                            getOptionValue={(g) => g.id}
                            getOptionLabel={(g) =>
                                g.account + " : " + g.description
                            }
                            onChange={(account) =>
                                this.selectOptionAccount(account)
                            }
                        />

                        <label className="uk-form-label" htmlFor="">
                            Välj kostnadsställe
                        </label>
                        <Select
                            name="cost_center_selection"
                            className="uk-select"
                            tabIndex={1}
                            options={showOptions_cost_center}
                            value={selectedOption_cost_center}
                            getOptionValue={(g) => g.id}
                            getOptionLabel={(g) =>
                                g.cost_center + " : " + g.description
                            }
                            onChange={(cost_center) =>
                                this.selectOptionCostCenter(cost_center)
                            }
                        />
                    </fieldset>

                    <fieldset className="uk-form-row uk-margin-top">
                        <button className="uk-button uk-button-success uk-float-right">
                            <i className="uk-icon-save" />{" "}
                            {"Applicera val på markerade produkter"}
                        </button>
                    </fieldset>
                </form>

                <div className="uk-margin-top">
                    <SearchBox handleChange={this.onSearch} />

                    <CollectionTable
                        id="product_table"
                        className="uk-margin-top prevent-select uk-scrollable-table"
                        collection={this.collection}
                        emptyMessage="Inga produkter"
                        columns={[
                            { title: "Namn", sort: "name" },
                            { title: "Kategori", sort: "category_id" },
                            {
                                title: "Pris",
                                class: "uk-text-right",
                                sort: "price",
                            },
                            { title: "Enhet", sort: "unit" },
                            { title: "Konto", sort: "account_id" },
                            { title: "Kostnadsställe", sort: "cost_center_id" },
                        ]}
                        rowComponent={({ item }) => (
                            <tr
                                key={item}
                                onClick={(event) =>
                                    this.setSelectedRow(event, item)
                                }
                            >
                                <td>
                                    <Link to={"/sales/product/" + item.id}>
                                        {item.name}
                                    </Link>
                                </td>
                                <td>
                                    {categories
                                        ? categories[item.category_id]
                                        : item.category_id}
                                </td>
                                <td className="uk-text-right">
                                    <Currency
                                        value={
                                            item.smallest_multiple *
                                            100 *
                                            item.price
                                        }
                                    />
                                    kr
                                </td>
                                <td>
                                    {item.smallest_multiple === 1
                                        ? item.unit
                                        : item.smallest_multiple +
                                          " " +
                                          item.unit}
                                </td>
                                <td>
                                    {transaction_account
                                        ? transaction_account[item.account_id]
                                        : item.account_id}
                                </td>
                                <td>
                                    {transaction_cost_center
                                        ? transaction_cost_center[
                                              item.cost_center_id
                                          ]
                                        : item.cost_center}
                                </td>
                            </tr>
                        )}
                        onPageNav={this.onPageNav}
                    />
                </div>
            </div>
        );
    }
}

export default AccountingProduct;
