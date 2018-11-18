import React from 'react';
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import Template from "../Models/Template";
import {Link} from "react-router";


class TemplateList extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Template});
    }

    render() {
        return (
            <div className="uk-margin-top">
                <h2>Mallar</h2>
                <p className="uk-float-left">Mallar som används för att skicka mail</p>
                <Link to="/messages/templates/new" className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle"/> Skapa ny mall</Link>
                <CollectionTable
                    collection={this.collection}
                    columns={[
                        {title: "Name", sort: "name"},
                        {title: "Rubrik", sort: "title"},
                        {title: ""},
                    ]}
                    rowComponent={({item, deleteItem}) => (
                        <tr>
                            <td><Link to={"/messages/templates/" + item.id}>{item.name}</Link></td>
                            <td><Link to={"/messages/templates/" + item.id}>{item.title}</Link></td>
                            <td className="uk-text-right">
                                <Link className="uk-margin-small-right uk-button uk-button-mini uk-button-primary uk-button-success" to={"/messages/new?template=" + item.id}><i className="uk-icon-envelope"/> Skicka</Link>
                                <a onClick={() => deleteItem(item)} className="removebutton"><i className="uk-icon-trash"/></a>
                            </td>
                        </tr>
                    )}
                />
            </div>
        );
    }
}


export default TemplateList;
