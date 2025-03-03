import PropTypes from "prop-types";
import React, { createContext } from "react";
import { useParams } from "react-router";
import useModel from "../Hooks/useModel";
import Member from "../Models/Member";
import { NavItem } from "../nav";

export const MemberContext = createContext(null);

function MemberBox({ children }) {
    const { member_id } = useParams();
    const member = useModel(Member, member_id);

    return (
        <MemberContext.Provider value={member}>
            <div>
                <h2>
                    Medlem #{member.member_number}: {member.firstname}{" "}
                    {member.lastname}
                </h2>

                <ul className="uk-tab">
                    <NavItem
                        to={`/membership/members/${member_id}/key-handout`}
                    >
                        Medlemsintroduktion
                    </NavItem>
                    <NavItem
                        to={`/membership/members/${member_id}/member-data`}
                    >
                        Uppgifter
                    </NavItem>
                    <NavItem to={`/membership/members/${member_id}/groups`}>
                        Grupper
                    </NavItem>
                    <NavItem to={`/membership/members/${member_id}/keys`}>
                        Nycklar
                    </NavItem>
                    <NavItem
                        to={`/membership/members/${member_id}/permissions`}
                    >
                        Behörigheter
                    </NavItem>
                    <NavItem to={`/membership/members/${member_id}/orders`}>
                        Ordrar
                    </NavItem>
                    <NavItem to={`/membership/members/${member_id}/messages`}>
                        Utskick
                    </NavItem>
                    <NavItem to={`/membership/members/${member_id}/spans`}>
                        Perioder
                    </NavItem>
                    <NavItem to={`/membership/members/${member_id}/statistics`}>
                        Statistik
                    </NavItem>
                </ul>
                {children}
            </div>
        </MemberContext.Provider>
    );
}

MemberBox.propTypes = {
    children: PropTypes.node,
};

export default MemberBox;
