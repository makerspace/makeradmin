import React from 'react';
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import Currency from "../Components/Currency";
import * as _ from "underscore";
import CollectionNavigation from "../Models/CollectionNavigation";
import Product from '../Models/Product';
import { Link } from "react-router-dom";
import Select from "react-select";
import SearchBox from "../Components/SearchBox";
import ProductAccountsCostCenters from "../Models/ProductAccountsCostCenters";
import { get } from "../gateway";

const filterOptions_account = (items_account, options_account) => {
    const current = new Set(items_account.map(i => i.id));
    return options_account.filter(o => !current.has(o.id));
};

const filterOptions_cost_center = (items_cost_center, options_cost_center) => {
    const current = new Set(items_cost_center.map(i => i.id));
    return options_cost_center.filter(o => !current.has(o.id));
};

const updateOptions_account = (options_account) => prevState => {
    let options = [{ account: 'No modification', id: 0 }].concat(filterOptions_account(prevState.items_account, options_account));
    return {
        showOptions_account: options,
        options_account,
    };
};

const updateOptions_cost_center = (options_cost_center) => prevState => {
    let options = [{ cost_center: 'No modification', id: 0 }].concat(filterOptions_cost_center(prevState.items_cost_center, options_cost_center));
    return {
        showOptions_cost_center: options,
        options_cost_center,
    };
};

class AccountingProduct extends CollectionNavigation {

    constructor(props) {
        super(props);
        const { search, page } = this.state;
        this.collection = new Collection({ type: Product, url: '/webshop/product', expand: "product_accounting", search: search, page: page });
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
        this.product_accounts_cost_centers = new ProductAccountsCostCenters;


        get({ url: "/webshop/category" })
            .then(data => {
                const categories = _.reduce(data.data, (obj, item) => { obj[item.id] = item.name; return obj; }, {});
                this.setState({ categories });
            },
                () => null);

        get({ url: '/webshop/transaction_account' })
            .then(data => {
                const transaction_account = _.reduce(data.data, (obj, item) => { obj[item.id] = item.account; return obj; }, {});
                this.setState({ transaction_account });
                this.setState(updateOptions_account(data.data));
            },
                () => null);

        get({ url: '/webshop/transaction_cost_center' })
            .then(data => {
                const transaction_cost_center = _.reduce(data.data, (obj, item) => { obj[item.id] = item.cost_center; return obj; }, {});
                this.setState({ transaction_cost_center });
                this.setState(updateOptions_cost_center(data.data));
            },
                () => null);
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
                row[id + 1].style.backgroundColor = '#ddd';
            } else {
                row[id + 1].style.backgroundColor = '';
            }
        }
    }

    onSave(account, cost_center) {
        const productIds = this.state.selected_product_id;

        productIds.forEach(product_id => {
            get({ url: "/webshop/accounting" })
                .then(data => {
                    const accountings = data.data;
                    const current_accounting = accountings.filter(p => p.product_id === product_id);
                    return current_accounting;
                })
                .then(current_accounting => {
                    const accounting_element = new ProductAccountsCostCenters(current_accounting[0]);
                    accounting_element.product_id = product_id;

                    if (account && account.id !== 0) {
                        accounting_element.account_id = account.id;
                    }
                    if (cost_center && cost_center.id !== 0) {
                        accounting_element.cost_center_id = cost_center.id;
                    }
                    return accounting_element;
                })
                .then(accounting_element => {
                    accounting_element
                        .save()
                        .then(() => {
                            accounting_element.reset();
                            this.collection.fetch();
                        });
                });
        });

        if (this.state.selected_product_id.length > 0) {
            const table_index = [];
            this.state.selected_product_id.forEach(product_id => {
                table_index.push(this.collection.items.map(function (e) { return e.saved.id; }).indexOf(product_id));
            });
            this.changeColor(false, table_index);
        }

        this.setState({ selected_product_id: [] });
        this.setState({ latest_selected_row_index: null });
    }

    updateAddSelectedProductId(current_array, element) {
        if (Array.isArray(element)) {
            this.setState({ selected_product_id: current_array.concat(element) });
        } else {
            this.setState({ selected_product_id: current_array.concat([element]) });
        }
    }

    updateRemoveSelectedProductId(current_array, element) {
        this.setState({ selected_product_id: current_array.filter(item => (item !== element)) });
    }

    updateResetSelectedProductId(element = null, table_index = null) {
        if (this.state.selected_product_id.length > 0) {
            const table_index = [];
            this.state.selected_product_id.forEach(product_id => {
                table_index.push(this.collection.items.map(function (e) { return e.saved.id; }).indexOf(product_id));
            });
            this.changeColor(false, table_index);
        }
        this.setState({ selected_product_id: ([element]) });
        this.changeColor(true, [table_index]);
    }

    updateLatestSelectedRowIndex(element) {
        this.setState({ latest_selected_row_index: element });
    }

    setSelectedRow(evt, element) {
        const table_index = this.collection.items.map(function (e) { return e.saved.id; }).indexOf(element.id);
        const selected_product_id = this.state.selected_product_id;
        const latest_selected_row_index = this.state.latest_selected_row_index;

        if (selected_product_id.indexOf(element.id) > -1) {
            this.changeColor(false, [table_index]);
            this.updateRemoveSelectedProductId(selected_product_id, element.id);

        } else {
            if (evt.shiftKey) {
                if (latest_selected_row_index === null) {
                    this.changeColor(true, [table_index]);
                    this.updateAddSelectedProductId(selected_product_id, element.id);
                } else {
                    const new_product_id = [];
                    const new_table_index = [];
                    if (table_index > latest_selected_row_index) {
                        for (let i = latest_selected_row_index + 1; i <= table_index; i++) {
                            if (selected_product_id.indexOf(this.collection.items[i].id) === -1) {
                                new_product_id.push(this.collection.items[i].id);
                                new_table_index.push(i);
                            }
                        }
                    } else {
                        for (let i = table_index; i <= latest_selected_row_index - 1; i++) {
                            if (selected_product_id.indexOf(this.collection.items[i].id) === -1) {
                                new_product_id.push(this.collection.items[i].id);
                                new_table_index.push(i);
                            }
                        }
                    }
                    this.changeColor(true, new_table_index);
                    this.updateAddSelectedProductId(selected_product_id, new_product_id);
                }
                this.updateLatestSelectedRowIndex(table_index);
            } else if (evt.ctrlKey) {
                this.changeColor(true, [table_index]);
                this.updateAddSelectedProductId(selected_product_id, element.id);
                this.updateLatestSelectedRowIndex(table_index);
            } else {
                this.updateResetSelectedProductId(element.id, table_index);
                this.updateLatestSelectedRowIndex(table_index);
            }
        }
    }

    render() {
        const { categories, transaction_account, transaction_cost_center } = this.state;
        const { selectedOption_account, showOptions_account, selectedOption_cost_center, showOptions_cost_center } = this.state;

        return (
            <div>
                <div className="uk-margin-top">
                    <h2>Hantera produkter för bokföring</h2>
                    <p>På denna sida kan du ange och ta bort konton och kostnadsställen för produkter. Markera en eller flera produkter i listan och välj vilket konto och kostnadsställe du vill applicera.</p>
                </div>


                <form className="uk-form uk-form-stacked" onSubmit={(e) => { e.preventDefault(); this.onSave(selectedOption_account, selectedOption_cost_center); return false; }}>
                    <fieldset className="uk-margin-top">
                        <label className="uk-form-label" htmlFor="">
                            Välj konto
                        </label>
                        <Select name="account_selection"
                            className="uk-select"
                            tabIndex={1}
                            options={showOptions_account}
                            value={selectedOption_account}
                            getOptionValue={g => g.id}
                            getOptionLabel={g => g.account}
                            onChange={account => this.selectOptionAccount(account)}
                        />

                        <label className="uk-form-label" htmlFor="">
                            Välj kostnadsställe
                        </label>
                        <Select name="cost_center_selection"
                            className="uk-select"
                            tabIndex={1}
                            options={showOptions_cost_center}
                            value={selectedOption_cost_center}
                            getOptionValue={g => g.id}
                            getOptionLabel={g => g.cost_center}
                            onChange={cost_center => this.selectOptionCostCenter(cost_center)}
                        />
                    </fieldset>

                    <fieldset className="uk-form-row uk-margin-top">
                        <button className="uk-button uk-button-success uk-float-right"><i className="uk-icon-save" /> {'Applicera val på markerade produkter'}</button>
                    </fieldset>
                </form>

                <div className="uk-margin-top">
                    <p className="uk-float-left">På denna sida ser du en lista på samtliga produkter som finns för försäljning.</p>
                    <SearchBox handleChange={this.onSearch} />

                    <CollectionTable
                        id="product_table"
                        className="uk-margin-top prevent-select"
                        collection={this.collection}
                        emptyMessage="Inga produkter"
                        columns={[
                            { title: "Namn", sort: "name" },
                            { title: "Kategori", sort: "category_id" },
                            { title: "Pris", class: 'uk-text-right', sort: "price" },
                            { title: "Enhet", sort: "unit" },
                            { title: "Konto", sort: "account_id" },
                            { title: "Kostnadsställe", sort: "cost_center_id" },
                        ]}
                        rowComponent={({ item }) =>
                            <tr key={item} onClick={(event) => this.setSelectedRow(event, item)}>
                                <td><Link to={"/sales/product/" + item.id}>{item.name}</Link></td>
                                <td>{categories ? categories[item.category_id] : item.category_id}</td>
                                <td className="uk-text-right"><Currency value={item.smallest_multiple * 100 * item.price} />kr</td>
                                <td>{item.smallest_multiple === 1 ? item.unit : item.smallest_multiple + " " + item.unit}</td>
                                <td>{transaction_account ? transaction_account[item.account_id] : item.account_id}</td>
                                <td>{transaction_cost_center ? transaction_cost_center[item.cost_center_id] : item.cost_center}</td>
                            </tr>
                        }
                        onPageNav={this.onPageNav}
                    />
                </div>
            </div >
        );
    }
}



export default AccountingProduct;
