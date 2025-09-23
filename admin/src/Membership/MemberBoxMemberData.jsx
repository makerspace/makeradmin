import React, { useContext } from "react";
import MemberForm from "../Components/MemberForm";
import { confirmModal } from "../message";
import { MemberContext } from "./MemberBox";
import { useNavigate } from "react-router";

function MemberBoxMemberData() {
    const member = useContext(MemberContext);
    const navigate = useNavigate();

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
                            navigate("/membership/members/");
                        })
                        .catch(() => null);
                }}
            />
        </div>
    );
}

export default MemberBoxMemberData;
