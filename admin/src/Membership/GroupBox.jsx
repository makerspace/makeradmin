import React, { useEffect, useMemo, useState } from "react";
import GroupContext from "../Contexts/GroupContext";
import Group from "../Models/Group";
import { NavItem } from "../nav";

function GroupBox(props) {
    const { group_id } = props.match.params;
    const group = useMemo(() => Group.get(group_id), [group_id]);
    const [title, setTitle] = useState("");

    useEffect(() => {
        const unsubscribe = group.subscribe(() => setTitle(group.title));

        return () => {
            unsubscribe();
        };
    }, [group]);

    return (
        <GroupContext.Provider value={group}>
            <div>
                <h2>Grupp {title}</h2>
                <ul className="uk-tab">
                    <NavItem
                        icon={null}
                        to={`/membership/groups/${group_id}/info`}
                    >
                        Information
                    </NavItem>
                    <NavItem
                        icon={null}
                        to={`/membership/groups/${group_id}/members`}
                    >
                        Medlemmar
                    </NavItem>
                    <NavItem
                        icon={null}
                        to={`/membership/groups/${group_id}/permissions`}
                    >
                        Behörigheter
                    </NavItem>
                </ul>
                {props.children}
            </div>
        </GroupContext.Provider>
    );
}

export default GroupBox;
