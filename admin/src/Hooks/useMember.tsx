import { useEffect, useMemo, useState } from "react";
import Member from "../Models/Member";

export default function useMember(member_id: number): Member {
    const member = useMemo(() => Member.get(member_id) as Member, [member_id]);
    const [version, setVersion] = useState(0); // Dummy state to force re-render

    useEffect(() => {
        const unsubscribe = member.subscribe(() => {
            setVersion((v) => v + 1);
        });

        return () => {
            unsubscribe();
        };
    }, [member_id]);

    return member;
}
