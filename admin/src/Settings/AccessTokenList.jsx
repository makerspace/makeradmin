import auth from "../auth";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";
import AccessToken from "../Models/AccessToken";
import Collection from "../Models/Collection";
import React from "react";

export default class AccessTokenList extends React.Component {
    constructor(props) {
        super(props);
        this.collection = new Collection({ type: AccessToken });
        this.state = {};
    }

    render() {
        return (
            <CollectionTable
                collection={this.collection}
                columns={[
                    { title: "" },
                    { title: "Access token" },
                    { title: "Browser" },
                    { title: "IP" },
                    { title: "Giltig till" },
                ]}
                rowComponent={({ item }) => (
                    <tr key={item.access_token}>
                        <td>
                            {auth.getAccessToken() === item.access_token ? (
                                <i className="uk-icon-check" />
                            ) : null}
                        </td>
                        <td>{item.access_token}</td>
                        <td>{item.browser}</td>
                        <td>{item.ip}</td>
                        <td>
                            <DateTimeShow date={item.expires} />
                        </td>
                    </tr>
                )}
            />
        );
    }
}
