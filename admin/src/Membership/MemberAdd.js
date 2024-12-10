import React from "react";
import MemberForm from "../Components/MemberForm";
import Member from "../Models/Member";
import { browserHistory } from "../browser_history";

function MemberAdd() {
    const member = new Member();

    const handleSave = () => {
        member
            .save()
            .then(() =>
                browserHistory.replace("/membership/members/" + member.id),
            );
    };

    return (
        <div>
            <h2>Skapa medlem</h2>
            <MemberForm member={member} onSave={handleSave} />
        </div>
    );
}

export default MemberAdd;
