import React, { useState } from "react";
import { get } from "../gateway";

function MemberExport() {
    const [csvContent, setCsvContent] = useState(null);
    const [state, setState] = useState("none");

    // Function to export members
    const exportMembers = () => {
        setState("loading");

        get({ url: "/membership/member/all_with_membership" }).then((data) => {
            const members = data.data;
            // Type of members is (in typescript notation) Member & { membership: MembershipData }
            // where those types are defined in the api backend.

            // Find all members which are either active lab members or makerspace members.
            // Lab membership does technically imply makerspace membership... but people are not always paying their membership fees properly.
            const active_members = members.filter(
                (m) =>
                    m.membership.effective_labaccess_active ||
                    m.membership.membership_active,
            );

            // Format as a CSV file
            let rows = [];
            rows.push([
                "Member Number,First Name,Last Name,Email,Labaccess End Date,Membership End Date",
            ]);
            for (const member of active_members) {
                rows.push([
                    member.member_number,
                    member.firstname,
                    member.lastname,
                    member.email,
                    member.membership.labaccess_end
                        ? member.membership.labaccess_end
                        : "",
                    member.membership.membership_end
                        ? member.membership.membership_end
                        : "",
                ]);
            }

            setState("loaded");
            setCsvContent(rows.map((r) => r.join(",")).join("\n"));
        });
    };

    return (
        <div>
            <h2>Exportera medlemslista</h2>
            {csvContent && (
                <textarea
                    readOnly
                    className="uk-width-1-1"
                    value={csvContent}
                    rows={50}
                ></textarea>
            )}
            {!csvContent && (
                <a
                    className="uk-button uk-button-primary"
                    role="button"
                    onClick={exportMembers}
                >
                    Exportera alla aktiva medlemmar som CSV
                    {state === "loading" ? "..." : ""}
                </a>
            )}
        </div>
    );
}

export default MemberExport;
