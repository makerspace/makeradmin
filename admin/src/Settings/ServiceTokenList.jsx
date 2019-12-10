import React from 'react';
import Collection from "../Models/Collection";
import ServiceAccessToken from "../Models/ServiceAccessToken";
import CollectionTable from "../Components/CollectionTable";

const Row = props => {
    const {item, deleteItem} = props;
    return (
        <tr key={item.access_token}>
            <td>{item.service_name}</td>
            <td>{item.access_token}</td>
            <td>{item.permissions}</td>
            <td><a onClick={() => deleteItem(item)} className="removebutton"><i className="uk-icon-trash"/></a></td>
        </tr>
    );
};

export default class ServiceTokenList extends React.Component {
    constructor(props) {
        super(props);
        this.collection = new Collection({type: ServiceAccessToken});
        this.state = {};
    }

    render() {
        return (
            <CollectionTable
                collection={this.collection}
                columns={[
                    {title: "Service"},
                    {title: "Access token"},
                    {title: "Permissions"},
                    {title: ""},
                ]}
                rowComponent={Row}
            />
        );
    }
}
