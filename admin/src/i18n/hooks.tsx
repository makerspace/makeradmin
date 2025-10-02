import i18next from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import {
    initReactI18next,
    useTranslation as useTranslationRaw,
} from "react-i18next";
import {
    LOCALE_RESOURCES,
    LOCALE_SCHEMA,
    LOCALE_SCHEMA_GLOBAL,
} from "./locales";

export const defaultNS = "common";

const DEBUG_MODE = false;

export const useTranslation = <NS extends keyof LOCALE_SCHEMA>(
    namespace: NS,
): { t: Translator<NS> } => {
    const t = useTranslationRaw(namespace as string) as any;
    if (DEBUG_MODE) {
        const orig = t.t;
        t.t = (key: string, args: any) => {
            const result = orig(key, args);
            return (
                <>
                    <span className="uk-label uk-label-danger">
                        {namespace}:{key}
                    </span>
                    {result}
                </>
            );
        };
    }
    return t;
};

export type Translator<NS extends keyof LOCALE_SCHEMA> = LOCALE_SCHEMA[NS] &
    LOCALE_SCHEMA_GLOBAL;

i18next
    .use(initReactI18next)
    .use(LanguageDetector)
    .init({
        supportedLngs: Object.keys(LOCALE_RESOURCES),
        // lng: ..., // if you're using a language detector, do not define the lng option
        debug: true,
        resources: LOCALE_RESOURCES,
        fallbackLng: "en",
        defaultNS,
        returnNull: false,
        returnObjects: true,
        detection: {
            caches: [],
        },
    });