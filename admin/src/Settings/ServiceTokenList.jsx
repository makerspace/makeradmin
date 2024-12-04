import React, { useEffect, useState } from "react";
import Collection from "../Models/Collection";
import ServiceAccessToken from "../Models/ServiceAccessToken";
import CollectionTable from "../Components/CollectionTable";
import { del } from "../gateway";

const Row = ({ item, collection }) => {
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

const ServiceTokenList = () => {
    const [collection, setCollection] = useState(new Collection({ type: ServiceAccessToken }));

    useEffect(() => {
        collection.fetch();
    }, [collection]);

    return (
        <CollectionTable
            collection={collection}
            columns={[
                { title: "" },
                { title: "Service" },
                { title: "Access token" },
                { title: "Permissions" },
            ]}
            rowComponent={(props) => <Row {...props} collection={collection} />}
        />
    );
};

export default ServiceTokenList;
