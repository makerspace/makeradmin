import { member_t, membership_t } from "frontend_common";
import { useState } from "react";
import { get } from "../gateway";

function MemberExport() {
    const [csvContent, setCsvContent] = useState<string | null>(null);
    const [state, setState] = useState<"none" | "loading" | "loaded">("none");

    const exportMembers = () => {
        setState("loading");

        get({ url: "/membership/member/all_with_membership" }).then((data) => {
            const members: (member_t & { membership: membership_t })[] =
                data.data;

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

    const recentlyLeftMembers = () => {
        setState("loading");

        get({ url: "/membership/member/all_with_membership" }).then((data) => {
            const members: (member_t & { membership: membership_t })[] =
                data.data;

            // Find all members which are either active lab members or makerspace members.
            // Lab membership does technically imply makerspace membership... but people are not always paying their membership fees properly.
            const cutoff_end_date = new Date();
            cutoff_end_date.setMonth(cutoff_end_date.getMonth() - 3); // N months ago
            const cutoff_start_date = new Date();
            cutoff_start_date.setMonth(cutoff_start_date.getMonth() - 12); // 1 month ago
            const active_members = members.filter(
                (m) =>
                    !m.membership.effective_labaccess_active &&
                    m.membership.membership_end !== null &&
                    new Date(m.membership.membership_end) < cutoff_end_date &&
                    new Date(m.membership.membership_end) > cutoff_start_date,
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
            <div style={{ marginBottom: "1em" }}>
                <label htmlFor="exportType" style={{ marginRight: "0.5em" }}>
                    Exporttyp:
                </label>
                <select
                    id="exportType"
                    className="uk-select"
                    style={{ width: "auto", display: "inline-block" }}
                    onChange={(e) => {
                        setCsvContent(null);
                        if (e.target.value === "active") {
                            exportMembers();
                        } else if (e.target.value === "recentlyLeft") {
                            recentlyLeftMembers();
                        }
                    }}
                    defaultValue=""
                >
                    <option value="" disabled>
                        Välj exporttyp
                    </option>
                    <option value="active">
                        Alla aktiva föreningsmedlemmar
                    </option>
                    <option value="recentlyLeft">
                        Personer som nyligen slutat vara föreningsmedlemmar
                    </option>
                </select>
            </div>
            {csvContent && (
                <textarea
                    readOnly
                    className="uk-width-1-1"
                    value={csvContent}
                    rows={50}
                ></textarea>
            )}
        </div>
    );
}

export default MemberExport;
