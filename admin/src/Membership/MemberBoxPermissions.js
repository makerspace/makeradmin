import React from "react";
import { useParams } from "react-router-dom";
import CollectionTable from "../Components/CollectionTable";
import Collection from "../Models/Collection";
import Permission from "../Models/Permission";

const Row = ({ item }) => (
    <tr>
        <td>{item.permission}</td>
    </tr>
);

function MemberBoxPermissions() {
    const { member_id } = useParams();
    const collection = new Collection({
        type: Permission,
        url: `/membership/member/${member_id}/permissions`,
        pageSize: 0,
    });

    const columns = [{ title: "Behörighet" }];
    return (
        <div className="uk-margin-top">
            <CollectionTable
                emptyMessage="Medlemmen har inga behörigheter"
                rowComponent={Row}
                collection={collection}
                columns={columns}
            />
        </div>
    );
}

export default MemberBoxPermissions;
