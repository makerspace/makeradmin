import React from "react";
import MemberForm from "../Components/MemberForm";
import Member from "../Models/Member";
import { useNavigate } from "react-router";

function MemberAdd() {
    const member = new Member();
    const navigate = useNavigate();

    const handleSave = () => {
        member
            .save()
            .then(() =>
                navigate("/membership/members/" + member.id, { replace: true }),
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
