import { useCallback } from "react";
import Async from "react-select/async";
import { get } from "../gateway";

export interface MemberOption {
    member_id: number;
    member_number: number;
    firstname: string;
    lastname: string;
    email: string;
}

interface MemberSelectProps {
    /** Currently selected member, or null if none selected */
    value: MemberOption | null;
    /** Callback when selection changes */
    onChange: (member: MemberOption | null) => void;
    /** Placeholder text for the input */
    placeholder?: string;
    /** Whether the selection can be cleared */
    isClearable?: boolean;
    /** HTML name attribute */
    name?: string;
    /** Tab index for keyboard navigation */
    tabIndex?: number;
}

/**
 * Build search parameters for member search.
 * If the search is a large integer or list of large integers (member numbers),
 * search only by member_number column for more precise results.
 */
function buildSearchParams(inputValue: string): Record<string, string> {
    // If the search is a large integer, or a list of large integers,
    // then search only for member numbers instead of doing a full search.
    // This makes the search much more precise when searching for member numbers.
    const intListMatch = inputValue.match(/^\s*(\d\d\d\d+[\s,]*)+\s*$/);
    if (intListMatch) {
        const ids = inputValue
            .split(/[\s,]+/)
            .map((v) => parseInt(v, 10))
            .filter((v) => !isNaN(v));

        return {
            regex: "true",
            search: ids.join("|"),
            search_column: "member_number",
            sort_by: "member_number",
        };
    }

    return {
        search: inputValue,
        sort_by: "firstname",
        sort_order: "asc",
    };
}

/**
 * A reusable async member search/select component.
 * Searches members by name, email, or member number.
 */
export default function MemberSelect({
    value,
    onChange,
    placeholder = "Search for member...",
    isClearable = true,
    name = "member-select",
    tabIndex = 1,
}: MemberSelectProps) {
    const loadOptions = useCallback(
        (inputValue: string, callback: (options: MemberOption[]) => void) => {
            get({
                url: "/membership/member",
                params: buildSearchParams(inputValue),
            }).then((data) => callback(data.data));
        },
        [],
    );

    return (
        <Async
            name={name}
            tabIndex={tabIndex}
            isClearable={isClearable}
            placeholder={placeholder}
            value={value}
            getOptionValue={(m) => String(m.member_id)}
            getOptionLabel={(m) =>
                `#${m.member_number}: ${m.firstname} ${m.lastname || ""} <${m.email}>`
            }
            loadOptions={loadOptions}
            onChange={(member) => onChange(member as MemberOption | null)}
        />
    );
}
