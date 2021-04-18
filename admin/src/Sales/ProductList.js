import React from 'react';
import { Link } from "react-router-dom";
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import Product from "../Models/Product";
import Currency from "../Components/Currency";
import * as _ from "underscore";
import {get} from "../gateway";
import SearchBox from "../Components/SearchBox";


class ProductList extends React.Component {

    constructor(props) {
        super(props);
        this.onSearch = this.onSearch.bind(this);
        this.params = new URLSearchParams(this.props.location.search);
        const search_term = this.params.get('search') || '';
        this.collection = new Collection({type: Product, search: search_term});
        this.state = {};
        this.state = {categories: null, 'search': search_term};
        get({url: "/webshop/category"})
            .then(data => {
                      const categories = _.reduce(data.data, (obj, item) => {obj[item.id] = item.name; return obj;}, {});
                      this.setState({categories});
                  },
                  () => null);
    }
    
    onSearch(term) {
        this.setState({'search': term});
        this.collection.updateSearch(term);
        if (term === "") {
            this.params.delete("search");
        } else {
            this.params.set("search", term);
        }
        this.props.history.replace(this.props.location.pathname + "?" + this.params.toString());
    }
    
    render() {
        
        const {categories} = this.state;
        
        const toggleShow = item => {
            item.show = !item.show;
            item.save().then(() => this.collection.fetch());
        };
    
        return (
            <div className="uk-margin-top">
                <h2>Produkter</h2>
                <p className="uk-float-left">På denna sida ser du en lista på samtliga produkter som finns för försäljning.</p>
                <Link className="uk-button uk-button-primary uk-margin-bottom uk-float-right" to="/sales/product/add"><i className="uk-icon-plus-circle"/> Skapa ny produkt</Link>
                <SearchBox handleChange={this.onSearch} />
                <CollectionTable
                    className="uk-margin-top"
                    collection={this.collection}
                    emptyMessage="Inga produkter"
                    columns={[
                        {title: "Namn", sort: "name"},
                        {title: "Synlig", sort: "show"},
                        {title: "Kategori", sort: "category_id"},
                        {title: "Pris", class: 'uk-text-right', sort: "price"},
                        {title: "Enhet", sort: "unit"},
                        {title: ""},
                    ]}
                    rowComponent={({item, deleteItem}) =>
                        <tr>
                            <td><Link to={"/sales/product/" + item.id}>{item.name}</Link></td>
                            <td><input type="checkbox" checked={item.show} onChange={() => toggleShow(item)}/></td>
                            <td>{categories ? categories[item.category_id] : item.category_id}</td>
                            <td className="uk-text-right"><Currency value={item.smallest_multiple * 100 * item.price} />kr</td>
                            <td>{item.smallest_multiple === 1 ? item.unit : item.smallest_multiple + " " + item.unit}</td>
                            <td><a onClick={() => deleteItem(item)} className="removebutton"><i className="uk-icon-trash"/></a></td>
                        </tr>
                    }
                />
            </div>
        );
    }
}


export default ProductList;
