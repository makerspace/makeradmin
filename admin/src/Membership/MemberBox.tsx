import { createContext } from "react";
import { Outlet, useParams } from "react-router";
import useModel from "../Hooks/useModel";
import Member from "../Models/Member";
import { NavItem } from "../nav";

export const MemberContext = createContext<Member | null>(null);

function MemberBox() {
    const { member_id: member_id_str } = useParams<{ member_id: string }>();
    const member_id =
        member_id_str !== undefined ? parseInt(member_id_str, 10) : NaN;
    if (Number.isNaN(member_id)) {
        return null;
    }
    const member = useModel(Member, member_id);

    return (
        <MemberContext.Provider value={member}>
            <div>
                <h2>Medlem {member.toString()}</h2>

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
                <Outlet />
            </div>
        </MemberContext.Provider>
    );
}

export default MemberBox;
