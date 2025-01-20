import DatePeriodInput, {
    commonPeriodTemplates,
} from "Components/DatePeriodInput";
import React from "react";
import { Link } from "react-router-dom";
import { useJson } from "State/useJson";
import { usePeriod } from "State/usePeriod";

type MemberScore = {
    member_id: number;
    member_number: number;
    firstname: string;
    lastname: string | null;
    activity_percentile: number;
    score: number;
};

type ActivityGroupStatistics = {
    name: string;
    products: [number, string, number][];
    doors: [string, string, number][];
    member_scores: MemberScore[];
};

type MembersOfInterestResponse = {
    groups: ActivityGroupStatistics[];
};

export default () => {
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
    const { period, lastValidPeriod } = usePeriod({
        start: oneYearAgo,
        end: new Date(),
    });

    const { data, isLoading } = useJson<MembersOfInterestResponse>({
        url: `/statistics/members_of_interest`,
        params: {
            start:
                lastValidPeriod?.start?.toISOString().substring(0, 10) ??
                undefined,
            end:
                lastValidPeriod?.end?.toISOString().substring(0, 10) ??
                undefined,
        },
    });

    const dateSelector = (
        <div className="uk-flex uk-flex-between uk-margin-top">
            <div className="uk-flex uk-flex-middle">
                <DatePeriodInput
                    period={period}
                    highlightChanges={false}
                    templates={commonPeriodTemplates(new Date())}
                />
            </div>
        </div>
    );

    if (data == null) {
        return (
            <>
                {dateSelector}
                <p>Loading...</p>
            </>
        );
    }

    return (
        <>
            {dateSelector}
            {data.groups.map((group) => (
                <>
                    <h3>{group.name}</h3>
                    <div>
                        Scoring:{" "}
                        {group.products.map((product) => (
                            <Link
                                to={`/sales/product/${product[0]}`}
                                key={product[0]}
                                className="uk-badge uk-margin-xsmall-right"
                            >
                                {product[1]}: {product[2]}
                            </Link>
                        ))}
                        {group.doors.map((door) => (
                            <a
                                href={
                                    door[0].includes("%")
                                        ? "https://portal.accessy.se/portal/assets"
                                        : `https://portal.accessy.se/portal/assets/${door[0]}`
                                }
                                target="_blank"
                                key={door[0]}
                                className="uk-badge uk-margin-xsmall-right"
                            >
                                {door[1]}: {door[2]}
                            </a>
                        ))}
                    </div>
                    <table
                        className={
                            "uk-table uk-table-small uk-table-striped uk-table-hover" +
                            (data == null || isLoading
                                ? " backboneTableLoading"
                                : "")
                        }
                    >
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Member</th>
                                <th>Score</th>
                                <th>Days visiting the space</th>
                            </tr>
                        </thead>
                        <tbody>
                            {group.member_scores.map((member) => (
                                <tr key={member.member_id}>
                                    <td>
                                        <Link
                                            to={`/membership/members/${member.member_id}`}
                                        >
                                            {member.member_number}
                                        </Link>
                                    </td>
                                    <td>
                                        {member.firstname} {member.lastname}
                                    </td>
                                    <td>{member.score.toFixed(0)}</td>
                                    <td>
                                        Top{" "}
                                        {Math.max(
                                            1,
                                            100 * member.activity_percentile,
                                        ).toFixed(0)}
                                        %
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </>
            ))}
        </>
    );
};
