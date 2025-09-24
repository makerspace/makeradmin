import {
    access_t,
    group_t,
    member_t,
    membership_t,
    Permission,
    UploadedLabel,
} from "frontend_common";
import * as common from "./common";

export async function LoadCurrentMemberInfo(): Promise<
    member_t & { has_password: boolean }
> {
    return (
        await common.ajax("GET", window.apiBasePath + "/member/current", null)
    ).data;
}

export async function LoadCurrentMembershipInfo(): Promise<membership_t> {
    return (
        await common.ajax(
            "GET",
            window.apiBasePath + "/member/current/membership",
            null,
        )
    ).data;
}

export async function LoadCurrentMemberGroups(): Promise<group_t[]> {
    return (
        await common.ajax("GET", `${window.apiBasePath}/member/current/groups`)
    ).data;
}

export async function LoadCurrentAccessInfo(): Promise<access_t> {
    return (
        await common.ajax(
            "GET",
            window.apiBasePath + "/member/current/access",
            null,
        )
    ).data;
}

export async function LoadCurrentLabels(): Promise<UploadedLabel[]> {
    return (
        await common.ajax("GET", `${window.apiBasePath}/member/current/labels`)
    ).data;
}

export async function LoadCurrentPermissions(): Promise<Permission[]> {
    return await common
        .ajax("GET", window.apiBasePath + "/member/current/permissions", null)
        .then((x) => x.data.permissions)
        .catch((err) => {
            if (err.status === common.UNAUTHORIZED) {
                return [];
            }
            throw err;
        });
}
