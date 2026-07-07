import { MobileOperatingSystem, getMobileOperatingSystem } from "./environment";

// Defaults for these settings live in api/src/settings/models.py; the API
// always returns a value for every public setting, so the empty-string case
// only happens if the settings could not be fetched at all.
const setting = (key: string): string => window.publicSettings?.[key] ?? "";

export const URL_FACEBOOK_GROUP = setting("url_facebook_group");
export const URL_SLACK_HELP = setting("url_slack_help");
export const URL_SLACK_SIGNUP = setting("url_slack_signup");
export const URL_WIKI = setting("url_wiki");
export const URL_GET_STARTED_QUIZ = setting("url_get_started_quiz");
export const URL_INSTAGRAM = setting("url_instagram");
export const URL_RELATIVE_MEMBER_PORTAL = "/member";
export const URL_CALENDAR = setting("url_calendar");
export const URL_CALENDLY_BOOK = setting("url_calendly_book");
export const URL_MEMBERBOOTH = setting("url_memberbooth");
export const URL_ACCESSY_ANDROID = setting("url_accessy_android");
export const URL_ACCESSY_IOS = setting("url_accessy_ios");
export const URL_ACCESSY_WIKI = setting("url_accessy_wiki");

export const accessyURL = (): string => {
    if (getMobileOperatingSystem() == MobileOperatingSystem.Android) {
        return URL_ACCESSY_ANDROID;
    } else if (getMobileOperatingSystem() == MobileOperatingSystem.iOS) {
        return URL_ACCESSY_IOS;
    } else {
        return URL_ACCESSY_WIKI;
    }
};
