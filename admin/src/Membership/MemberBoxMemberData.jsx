import React, { useContext } from "react";
import { browserHistory } from "../browser_history";
import MemberForm from "../Components/MemberForm";
import { confirmModal } from "../message";
import { MemberContext } from "./MemberBox";

function MemberBoxMemberData() {
    const member = useContext(MemberContext);

    return (
        <div className="uk-margin-top">
            <MemberForm
                member={member}
                onSave={() => {
                    member.save();
                }}
                onDelete={() => {
                    return confirmModal(member.deleteConfirmMessage())
                        .then(() => member.del())
                        .then(() => {
                            browserHistory.push("/membership/members/");
                        })
                        .catch(() => null);
                }}
            />
        </div>
    );
}

export default MemberBoxMemberData;
