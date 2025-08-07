import { MobileOperatingSystem, getMobileOperatingSystem } from "./environment";

export const URL_FACEBOOK_GROUP =
    "https://www.facebook.com/groups/makerspace.se";
export const URL_SLACK_HELP = "https://wiki.makerspace.se/Slack";

// NOTE: Should be updated roughly every year, since it expires after about 400 invites
export const URL_SLACK_SIGNUP =
    "https://join.slack.com/t/stockholmmakerspace/shared_invite/zt-3apcoyv3b-up1~_62eJDOJhderXUU7OQ";

export const URL_WIKI = "https://wiki.makerspace.se";
export const URL_GET_STARTED_QUIZ =
    "https://medlem.makerspace.se/member/quiz/1";
export const URL_INSTAGRAM = "https://www.instagram.com/stockholmmakerspace/";
export const URL_RELATIVE_MEMBER_PORTAL = "/member";
export const URL_CALENDAR = "https://www.makerspace.se/kalendarium";
export const URL_CALENDLY_BOOK =
    "https://calendly.com/medlemsintroduktion/medlemsintroduktion";
export const URL_MEMBERBOOTH = "https://wiki.makerspace.se/Memberbooth";
export const URL_ACCESSY_ANDROID =
    "https://play.google.com/store/apps/details?id=com.axessions.app";
export const URL_ACCESSY_IOS =
    "https://apps.apple.com/se/app/accessy/id1478132190";
export const URL_ACCESSY_WIKI = "https://wiki.makerspace.se/Accessy";

export const accessyURL = (): string => {
    if (getMobileOperatingSystem() == MobileOperatingSystem.Android) {
        return URL_ACCESSY_ANDROID;
    } else if (getMobileOperatingSystem() == MobileOperatingSystem.iOS) {
        return URL_ACCESSY_IOS;
    } else {
        return URL_ACCESSY_WIKI;
    }
};
