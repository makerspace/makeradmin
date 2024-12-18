import PropTypes from "prop-types";
import React, { createContext, useEffect, useRef, useState } from "react";
import { useParams, withRouter } from "react-router";
import Member from "../Models/Member";
import { NavItem } from "../nav";

export const MemberContext = createContext(null);

function MemberBox({ children }) {
    const { member_id } = useParams();
    const memberRef = useRef(Member.get(member_id));
    const [memberState, setMemberState] = useState({
        member_number: "",
        firstname: "",
        lastname: "",
    });

    useEffect(() => {
        const member = memberRef.current;
        const unsubscribe = member.subscribe(() => {
            setMemberState({
                member_number: member.member_number,
                firstname: member.firstname,
                lastname: member.lastname,
            });
        });
        console.log(children);

        return () => unsubscribe();
    }, []);

    const { member_number, firstname, lastname } = memberState;

    return (
        <MemberContext.Provider value={memberRef.current}>
            <div>
                <h2>
                    Medlem #{member_number}: {firstname} {lastname}
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
                </ul>
                {children}
            </div>
        </MemberContext.Provider>
    );
}

MemberBox.propTypes = {
    children: PropTypes.node,
};

export default withRouter(MemberBox);
