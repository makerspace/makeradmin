import { Translation, TranslationKeyValues } from "./translate";
import { createContext } from 'preact';
import { useContext, useState } from 'preact/hooks';
import { URL_CALENDAR, URL_FACEBOOK_GROUP, URL_GET_STARTED_QUIZ, URL_INSTAGRAM, URL_SLACK_HELP, URL_WIKI } from "./urls";
import { formatDate, formatDateTime } from "./common";

export type Dictionary = Translation<typeof Eng>;
export type TranslationKey = TranslationKeyValues<typeof Eng>;

const Eng = {
    continue: "Continue",
    back: "Back",
    and: "and",
    cancel: "Cancel",
    apply_for_discounts: "I cannot afford the membership fee",
    unit: {
        år: {
            one: "year",
            many: "years",
        },
        mån: {
            one: "month",
            many: "months",
        },
        st: {
            one: "piece",
            many: "pieces",
        }
    },
    priceUnit: "kr",
    special_products: {
        labaccess_subscription: {
            summary: "Makerspace Access",
            renewal: (price: number) => `Your makerspace access will renew monthly at ${price} kr/month.`,
        },
        membership_subscription: {
            summary: "Base Membership",
            renewal: (price: number) => `Your base membership will renew yearly at ${price} kr/year.`,
        },
        single_labaccess_month: {
            summary: "Makerspace Access",
            renewal: (price: number) => { throw new Error("This should never be called") },
        },
        single_membership_year: {
            summary: "Makerspace Access",
            renewal: (price: number) => { throw new Error("This should never be called") },
        },
        access_starter_pack: {
            summary: "Starter Pack",
            period: "2 months",
            renewal: (price: number) => { throw new Error("This should never be called") },
        },
        renewal: {
            one: "You can cancel this subscription at any time.",
            many: "You can cancel these subscriptions at any time."
        },
        cart_total: "Total",
        payment_right_now_nothing: "Right now, you will pay nothing.",
        payment_right_now: "Right now, you will pay",
    },
    registration_page: {
        memberships: {
            title: "Makerspace Memberships",
            p1: "Memberships are split into two parts",
            p2: <>Everyone has the yearly <b>Base Membership</b>, and if you want to work on your own projects, you must also get <b>Makerspace Access</b> (paid monthly).</>,
        },
        chooseYourPlan: {
            title: "Choose your membership",
            help: ""
        },
        plans: {
            ofWhichBaseMembership: (price: number) => `of which ${price} kr is yearly base membership`,
            makerspaceAccessSub: {
                title: "Makerspace Access Subscription",
                abovePrice: "",
                period: "per month",
                description1: "A monthly subscription gets you access all the time, for a lower price.\n2 months minimum.",
                description2: "",
                included: [
                    "Take part in courses and social events",
                    "Vote at yearly meetings",
                    "Support your local makerspace",
                    "Access to Stockholm Makerspace 24/7",
                    "Work on your own projects",
                    "Store a personal box at the space"
                ],
                notIncluded: [],
            },
            starterPack: {
                title: "Starter Pack",
                abovePrice: "",
                period: "",
                description1: "Two months of makerspace access for a lower price. New members only.",
                description2: "",
                included: [
                    "Take part in courses and social events",
                    "Vote at yearly meetings",
                    "Support your local makerspace",
                    "Access to Stockholm Makerspace 24/7",
                    "Work on your own projects",
                    "Store a personal box at the space"
                ],
                notIncluded: [],
            },
            singleMonth: {
                title: "1 month of Makerspace Access",
                abovePrice: "",
                period: "",
                description1: "One month of makerspace access.",
                description2: "",
                included: [
                    "Take part in courses and social events",
                    "Vote at yearly meetings",
                    "Support your local makerspace",
                    "Access to Stockholm Makerspace 24/7",
                    "Work on your own projects",
                    "Store a personal box at the space"
                ],
                notIncluded: [],

            },
            decideLater: {
                title: "1 year of Base Membership only",
                abovePrice: "",
                price: "0",
                period: "",
                description1: "One year of base membership.",
                description2: (a: number, b: number) => `Later, you can pay for individual months of makerspace access (${a} kr/mo) in our webshop, or get a subscription (${b} kr/mo).`,
                included: [
                    "Take part in courses and social events",
                    "Vote at yearly meetings",
                    "Support your local makerspace",
                ],
                notIncluded: [
                    "Access to the space outside of events",
                    "Work on your own projects",
                    "Store a personal box at the space",
                ],
            },
        },
        memberInfo: {
            title: "A little bit about you",
            firstName: "First name",
            lastName: "Last name",
            email: "Email",
            phone: "Phone (your phone will be used as your key to the makerspace)",
            zipCode: "Zip code",
            submit: "Continue",
            validatePhone: "We have sent a validation code to your phone. Please enter it below.",
        },
        terms: {
            title: "Rules for the premises",
            accept: "Accept",
            pledge: "You must pledge to ...",
            rules: [
                "take responsibility for your own actions and to show consideration for other members.",
                "not do anything illegal on the premises.",
                "abstain from using drugs or alcohol on the premises.",
                "not operate machines while under the influence.",
                "keep yourself updated on the latest rules.",
                "find and follow space- and machine-specific rules.",
                "always clean up after yourself and leave the premises in a clean state.",
                "ask a member of the Board if you're unsure about something.",
                "always ask before taking pictures of people or other people's projects located on the premises.",
                "not engage in commercial activities on the premises.",
                "not sleep on the premises.",
                "retrieve your storage box within 45 days from expiration of your makerspace access. After this period of time, any remaining materials belong to the Stockholm Makerspace.",
                "take full responsibility for what your guests do on the premises. (Your guest is only allowed on the premises if your intention is to show them the space and activities. They must not work on a project of their during their visit.)",
                "always leave the kitchen/common areas in better shape than you found them. This is especially important in areas shared with other building occupants and we risk losing access to these areas if this privilege is abused.",
                "report lost keys to the Board immediately after loss.",
                "report damage to the machines/premises to the Board immediately upon discovery.",
                "not remove equipment from the premises. Stockholm Makerspace does not allow equipment rental or borrowing.",
                "only visit the space when you hold an active membership. If your makerspace access is inactive, you have no access to the premises except as participant in Makerspace run activities such as courses, cleanup days or open days.",
            ],
            understanding1: "I understand that if I violate any of the rules above or otherwise abuse my access to the premises, I may be banned from the premises without a refund of my access fee.",
            understanding2: "I understand that I am solely responsible for everything I do on the premises.",
            welcoming: "I will do my best to ensure that the Stockholm Makerspace is a clean, safe and welcoming place.",
        },
        calendar: {
            title: "Calendar",
            text: (<>Book a Member Introduction, during which you'll get a tour of the space (if you haven't already) and gain permission to use the makerspace.
                Your makerspace access will not be activated until you have visited a Member Introduction.
                In some situations, there may be no available time slots. Please let us know on <a href={URL_FACEBOOK_GROUP}>Facebook</a> or <a href={URL_SLACK_HELP}>Slack</a> if you cannot book a slot.
            </>),
            book_button: "Book a member introduction"
        },
        payment: {
            title: "Payment",
            text: <>
                <p>Almost done, we just need to take care of the payment.</p>
                <p>Before you gain access to the makerspace you need to attend a member introduction. These are held <a target="_blank" href={URL_CALENDAR}>regularly every 1-2 weeks</a>.</p>
            </>,
            payment_processor: "Payment handled by Stripe",
        },
        success: {
            title: "Welcome to the Stockholm\u{00A0}Makerspace!",
            text: <><p>We look forward to meeting you!</p>
                <p>To gain access to the Makerspace you must attend a member introduction. You can book it here, or do it later.</p>
                <p>Here are your next steps:</p>
            </>,
            book_button: "Book your member introduction",
            book_step: "",
            steps: [
                // ((onClick: (e: MouseEvent)=>void) => (<>Book a Member Introduction, during which you'll get a tour of the space (if you haven't already) and gain permission to use the makerspace. Your makerspace access will not be activated until you have visited a Member Introduction.
                // You can find them in the calendar: https://calendly.com/medlemsintroduktion/medlemsintroduktion ("Medlemsintroduktion" in Swedish)</>)),
                ((onClick: (e: MouseEvent) => void) => (<>Join our <a target="_blank" href={URL_SLACK_HELP} onClick={onClick}>Slack</a> to chat with other members.</>)),
                ((onClick: (e: MouseEvent) => void) => (<>Take our <a target="_blank" href={URL_GET_STARTED_QUIZ} onClick={onClick}>Get Started Quiz</a> to learn about the space.</>)),
                ((onClick: (e: MouseEvent) => void) => (<>Check out our <a target="_blank" href={URL_WIKI} onClick={onClick}>wiki</a>.</>)),
                ((onClick: (e: MouseEvent) => void) => (<>Get inspired on our <a target="_blank" href={URL_INSTAGRAM} onClick={onClick}>Instagram</a>.</>)),
            ],
            continue_to_member_portal: "Continue to your member page",
        },
        discounts: {
            title: "Low Income Discounts",
            text: "If you cannot afford the full price of membership, you can apply for a discount.",
            confirmation: (fraction: number) => <>
                <p>Discount approved!</p>
                <p>You'll get a {fraction * 100}% discount on membership.</p>
                <p>We understand that not everyone can afford the full price of membership. But there are other ways you can help, if you want to.
                    The Makerspace is run by its members volonteering their time and effort. Join a work day, help out with maintaining a machine, or why not hold a course about something you are excited about?</p>
            </>,
            submit: "Continue",
            submit_write_more: "Please write a bit more",
            cancel: "Cancel",
            messagePlaceholder: "Tell us why you need a discount, in at least a few sentences.",
            reasons: {
                "student": "I am a student",
                "unemployed": "I am unemployed",
                "senior": "I am a senior citizen",
                "other": "Other",
            }
        },
    },
    member_page: {
        member: "Member",
        billing: {
            title: "Billing",
            manage: "Manage Payment Methods",
        },
        old_membership_status: {
            labaccess: {
                inactive: "Your makerspace access is inactive.",
                inactive_recent: (days: number) => `Your makerspace access expired ${days} days ago.`,
                inactive_yesterday: `Your makerspace access expired yesterday`,
                active_hours_remaining: (hours: number) => `Your makerspace access is valid for only ${hours} more hours.`,
                active_few_days_remaining: (end_date: string, days: number) => `Your makerspace access is valid through ${end_date} (only ${days} days left).`,
                active_days_remaining: (end_date: string, days: number) => `Your makerspace access is valid through ${end_date} (${days} days left).`,
            },
            membership: {
                inactive: "Your base membership is inactive.",
                inactive_recent: (days: number) => `Your base membership expired ${days} days ago.`,
                inactive_yesterday: `Your base membership expired yesterday`,
                active_hours_remaining: (hours: number) => `Your base membership is valid for only ${hours} more hours.`,
                active_few_days_remaining: (end_date: string, days: number) => `Your base membership is valid through ${end_date} (only ${days} days left).`,
                active_days_remaining: (end_date: string, days: number) => `Your base membership is valid through ${end_date} (${days} days left).`,
            },
            special_labaccess: {
                inactive: "Your special makerspace access is inactive.",
                inactive_recent: (days: number) => `Your special makerspace access expired ${days} days ago.`,
                inactive_yesterday: `Your special makerspace access expired yesterday`,
                active_hours_remaining: (hours: number) => `You have been given special access to the premises, which is for only ${hours} more hours.`,
                active_few_days_remaining: (end_date: string, days: number) => `You have been given special access to the premises through ${end_date} (only ${days} days left).`,
                active_days_remaining: (end_date: string, days: number) => `You have been given special access to the premises through ${end_date} (${days} days left).`,
            }
        },
        subscriptions: {
            cancel: {
                membership: {
                    valid_until: (date: string) => `Your base membership will stay active until it expires on ${date}.`,
                },
                labaccess: {
                    valid_until: (date: string) => `Your makerspace access will stay active until it expires on ${date}.`,
                }
            },
            descriptions: {
                membership: "Base membership gives you voting rights at the yearly meeting, supports your local makerspace, and allows you to attend courses/social events.",
                labaccess: `Makerspace access allows you to work on your own projects at the makerspace.
                You get 24/7 access to the space and you can also store one box with your own things at the space.
                Makerspace Access requires the Base Membership.`,
            },
            pending_makerspace_access: (pending_days: number) => <>Your <strong>{pending_days}</strong> days of makerspace access will start when you attend a member introduction.</>,
            add_to_cart: (count: number, unit: string, price: number) => `Add ${count} ${unit} to cart: ${price} kr`,
            binding_period: (count: number, unit: string) => `subscription has a binding period of ${count} ${unit}.`,
            next_charge: (amount: string, date: string) => `Your membership will renew at ${formatDate(date)} for ${amount} kr.`,
            activate_auto_renewal: (price: string, unit: string) => `Activate auto-renewal: ${price}/${unit}`,
            auto_renewal_active: "Auto renew: Active",
            errors: {
                no_member_introduction: `
                    <h2>Cannot start subscription</h2>
                    <p>You must attend a member introduction before you can start an auto-renewal subscription.</p><p>You can find them in the <a href="${URL_CALENDAR}">calendar</a>.</p>
                `
            },
            pay_dialog: {
                title: "Activate auto-renewal",
            }
        },
        change_phone_number: "Change",
        send_accessy_invite_msg: "Install the Accessy app on your phone. You can use this to unlock doors at the makerspace.",
        send_accessy_invite: "Send Accessy invite",
        change_pin_code: "Change",
        instructions_to_become_member: "Remaining steps to get makerspace access",
    },
    payment: {
        pay_with_stripe: "Pay with Stripe",
    },
    change_phone: {
        new_number_prompt: "New phone number",
        validation_code_prompt: "Validation code: ",
        errors: {
            generic: "Could not change phone number",
            incorrect_code: "Incorrect code. Try again.",
        }
    }
}

const Swe: typeof Eng = {
    // TODO
    ...Eng,
    continue: "Fortsätt",
}

export const Translations: { "en": typeof Eng, "sv": typeof Eng } = {
    "en": Eng,
    "sv": Swe,
}

export const TranslationContext = createContext(new Translation(Translations.en));

export type Translator = InstanceType<typeof Translation<typeof Eng>>["t"];
export const useTranslation = (): Translator => {
    const t = useContext(TranslationContext);
    return t.t.bind(t);
}

const heuristicallyPickLanguage = (): "en" | "sv" => {
    const langs = navigator.languages || [navigator.language];
    for (let lang of langs) {
        lang = lang.toLowerCase();

        if (lang.startsWith("sv")) {
            return "sv";
        } else if (lang.startsWith("en")) {
            return "en";
        }
    }

    // Fall back to English
    return "en";
}

export const TranslationWrapper = ({ children }: { children: preact.ComponentChildren }) => {
    const [language, setLanguage] = useState<keyof typeof Translations>(heuristicallyPickLanguage());
    const tr: Dictionary = new Translation(Translations[language]);

    return (
        <TranslationContext.Provider value={tr}>
            {children}
        </TranslationContext.Provider>
    )
}

export const translateUnit = (unit: string, count: number, t: Translator) => {
    if (unit !== "mån" && unit !== "år" && unit !== "st") throw new Error(`Unexpected unit '${unit}'. Expected one of år/mån/st`);
    return t(`unit.${unit}.${count > 1 ? "many" : "one"}`);
}