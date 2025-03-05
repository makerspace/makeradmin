import React, { useMemo } from "react";
import auth from "../auth";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";
import Icon from "../Components/icons";
import AccessToken from "../Models/AccessToken";
import Collection from "../Models/Collection";

export default function AccessTokenList() {
    const collection = useMemo(() => new Collection({ type: AccessToken }), []);

    return (
        <CollectionTable
            collection={collection}
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
                            <Icon icon="check" />
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
