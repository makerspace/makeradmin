import React, { useContext, useEffect, useState } from "react";
import MemberForm from "../Components/MemberForm";
import { confirmModal } from "../message";
import { MemberContext } from "./MemberBox";
import { useNavigate } from "react-router";
import { get } from "../gateway";

function MemberBoxMemberData() {
    const member = useContext(MemberContext);
    const navigate = useNavigate();
    const [slackInfo, setSlackInfo] = useState(null);

    useEffect(() => {
        get({
            url: `/membership/member/${member.id}/slack_info`,
        })
            .then((data) => {
                setSlackInfo(data);
            })
            .catch(() => {
                setSlackInfo(null);
            });
    }, [member.id]);

    return (
        <div className="uk-margin-top">
            <MemberForm
                member={member}
                slackInfo={slackInfo}
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
