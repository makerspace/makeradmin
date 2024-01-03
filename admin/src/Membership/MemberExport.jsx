import React from "react";
import { get } from "../gateway";

class MemberExport extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            csv_content: null,
            state: "none",
        };
    }

    exportMembers() {
        this.setState({ state: "loading" });

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

            this.setState({
                state: "loaded",
                csv_content: rows.map((r) => r.join(",")).join("\n"),
            });
        });
    }

    render() {
        return (
            <div>
                <h2>Exportera medlemslista</h2>
                {this.state.csv_content && (
                    <textarea
                        readOnly
                        className="uk-width-1-1"
                        value={this.state.csv_content}
                        rows={50}
                    ></textarea>
                )}
                {!this.state.csv_content && (
                    <a
                        className="uk-button uk-button-primary"
                        role="button"
                        onClick={() => this.exportMembers()}
                    >
                        Exportera alla aktiva medlemmar som CSV
                        {this.state.state === "loading" ? "..." : ""}
                    </a>
                )}
            </div>
        );
    }
}

export default MemberExport;
