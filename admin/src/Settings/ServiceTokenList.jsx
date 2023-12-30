import React from "react";
import Collection from "../Models/Collection";
import ServiceAccessToken from "../Models/ServiceAccessToken";
import CollectionTable from "../Components/CollectionTable";
import { del } from "../gateway";

const Row = (collection) => (props) => {
    const { item } = props;
    return (
        <tr key={item.access_token}>
            <td>
                <a
                    onClick={() =>
                        del({
                            url: "/oauth/service_token/" + item.user_id,
                        }).then(() => collection.fetch())
                    }
                    className="removebutton"
                >
                    <i className="uk-icon-trash" />
                </a>
            </td>
            <td>{item.service_name}</td>
            <td>{item.access_token}</td>
            <td>{item.permissions}</td>
        </tr>
    );
};

export default class ServiceTokenList extends React.Component {
    constructor(props) {
        super(props);
        this.collection = new Collection({ type: ServiceAccessToken });
        this.state = {};
    }

    render() {
        return (
            <CollectionTable
                collection={this.collection}
                columns={[
                    { title: "" },
                    { title: "Service" },
                    { title: "Access token" },
                    { title: "Permissions" },
                ]}
                rowComponent={Row(this.collection)}
            />
        );
    }
}
