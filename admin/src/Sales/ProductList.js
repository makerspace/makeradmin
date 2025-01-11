import React from "react";
import { Link } from "react-router-dom";
import * as _ from "underscore";
import CollectionTable from "../Components/CollectionTable";
import Currency from "../Components/Currency";
import Icon from "../Components/icons";
import SearchBox from "../Components/SearchBox";
import { get } from "../gateway";
import Collection from "../Models/Collection";
import CollectionNavigation from "../Models/CollectionNavigation";
import Product from "../Models/Product";

class ProductList extends CollectionNavigation {
    constructor(props) {
        super(props);
        const { search, page } = this.state;
        this.state.categories = null;

        this.collection = new Collection({ type: Product, search, page });
        get({ url: "/webshop/category" }).then(
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
        );
    }

    render() {
        const { categories } = this.state;

        const toggleShow = (item) => {
            item.show = !item.show;
            item.save().then(() => this.collection.fetch());
        };

        return (
            <div className="uk-margin-top">
                <h2>Produkter</h2>
                <p className="uk-float-left">
                    På denna sida ser du en lista på samtliga produkter som
                    finns för försäljning.
                </p>
                <Link
                    className="uk-button uk-button-primary uk-margin-bottom uk-float-right"
                    to="/sales/product/add"
                >
                    <Icon icon="plus-circle" /> Skapa ny produkt
                </Link>
                <SearchBox handleChange={this.onSearch} />
                <CollectionTable
                    className="uk-margin-top"
                    collection={this.collection}
                    emptyMessage="Inga produkter"
                    columns={[
                        { title: "Namn", sort: "name" },
                        { title: "Synlig", sort: "show" },
                        { title: "Kategori", sort: "category_id" },
                        {
                            title: "Pris",
                            class: "uk-text-right",
                            sort: "price",
                        },
                        { title: "Enhet", sort: "unit" },
                        { title: "" },
                    ]}
                    rowComponent={({ item, deleteItem }) => (
                        <tr>
                            <td>
                                <Link to={"/sales/product/" + item.id}>
                                    {item.name}
                                </Link>
                            </td>
                            <td>
                                <input
                                    type="checkbox"
                                    checked={item.show}
                                    onChange={() => toggleShow(item)}
                                />
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
                                    : item.smallest_multiple + " " + item.unit}
                            </td>
                            <td>
                                <a
                                    onClick={() => deleteItem(item)}
                                    className="removebutton"
                                >
                                    <Icon icon="trash" />
                                </a>
                            </td>
                        </tr>
                    )}
                    onPageNav={this.onPageNav}
                />
            </div>
        );
    }
}

export default ProductList;
