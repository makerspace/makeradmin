import React from 'react';
import {Link} from "react-router";
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import Product from "../Models/Product";
import Currency from "../Components/Currency";
import * as _ from "underscore";
import {get} from "../gateway";


class ProductList extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Product});
        this.state = {categories: null};
        get({url: "/webshop/category"})
            .then(data => {
                      const categories = _.reduce(data.data, (obj, item) => {obj[item.id] = item.name; return obj;}, {});
                      this.setState({categories});
                  },
                  () => null);
    }
    
    render() {
        
        const {categories} = this.state;
        
        return (
            <div className="uk-margin-top">
                <h2>Produkter</h2>
                <p className="uk-float-left">På denna sida ser du en lista på samtliga produkter som finns för försäljning.</p>
                <Link className="uk-button uk-button-primary uk-margin-bottom uk-float-right" to="/sales/product/add"><i className="uk-icon-plus-circle"/> Skapa ny produkt</Link>
                <CollectionTable
                    className="uk-margin-top"
                    collection={this.collection}
                    emptyMessage="Inga produkter"
                    columns={[
                        {title: "Namn"},
                        {title: "Kategori"},
                        {title: "Pris", class: 'uk-text-right'},
                        {title: "Enhet"},
                        {title: ""},
                    ]}
                    rowComponent={({item, deleteItem}) =>
                        <tr>
                            <td><Link to={"/sales/product/" + item.id}>{item.name}</Link></td>
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
