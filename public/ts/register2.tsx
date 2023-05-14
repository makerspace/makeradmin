import * as common from "./common";
import { Component, render } from 'preact';
import { useState } from 'preact/hooks';
import { ServerResponse } from "./common";
import { Translation, TranslationKeyValues } from "./translate";

type Dictionary = Translation<typeof Eng>;
type TranslationKey = TranslationKeyValues<typeof Eng>;

type Plan = {
    id: string,
    title: string,
    abovePrice: string,
    price: number,
    period: string,
    description: string,
}

const Eng = {
    memberships: {
        title: "Makerspace Memberships",
        p1: "Memberships are split into two parts",
        p2: "Everyone has the base membership, and if you want to work on your own projects, you must also get Makerspace Access.",
    },
    chooseYourPlan: "Choose your Makerspace\xa0Access",
    priceUnit: "kr",
    plans: {
        makerspaceAccessSub: {
            title: "Makerspace Access Subscription",
            abovePrice: "base membership +",
            period: "per month",
            description: "A monthly subscription gets you access all the time, for a lower price.\n2 months minimum.",
        },
        starterPack: {
            title: "Starter Pack",
            abovePrice: "base membership +",
            period: "",
            description: "Two months of makerspace access for a lower price.\nNew members only.",
        },
        decideLater: {
            title: "Decide later",
            abovePrice: "base membership +",
            price: "0",
            period: "",
            description: "Later, you can pay for individual months of makerspace access (375kr/mo) in our webshop, or get a subscription (300 kr/mo).",
        },
    },
    baseMembership: {
        title: "Base Membership",
        reasons: [
            "Take part in courses",
            "Attent social events",
            "Vote at yearly meetings",
            "Support your local makerspace"
        ],
        price: "200",
        period: "per year",
    },
    makerspaceAccess: {
        title: "Makerspace Access",
        price: "Price varies by plan, paid monthly",
        requirement: "Requires base membership",
        reasons: [
            "Access to Stockholm Makerspace 24/7",
            "Work on your own projects",
            "Store a personal box at the space"
        ],
    },
    memberInfo: {
        title: "Registration",
        firstName: "First name",
        lastName: "Last name",
        email: "Email",
        phone: "Phone",
        zipCode: "Zip code",
    },
    terms: {
        title: "Terms and conditions",
    },
    calendar: {
        title: "Calendar",
    },
    confirmation: {
        title: "Confirmation",
    }
}

const Translations: { "en": typeof Eng, "sv": typeof Eng } = {
    "en": Eng,
    "sv": Eng, // TODO
}

const LanguageChooser = ({ setLanguage }: { setLanguage: (lang: keyof typeof Translations) => void }) => {
    return (
        <div className="language-chooser">
            <div className="language-chooser-buttons">
                <button className="language-chooser-button" onClick={() => setLanguage("en")}>English</button>
                <button className="language-chooser-button" onClick={() => setLanguage("sv")}>Svenska</button>
            </div>
        </div>
    );
}

const LabeledInput = ({ label, id, required, value, onChange }: { id: string, type: "text" | "email", label: string, required: boolean, value: string, onChange: (value: string) => void }) => {
    return (
        <div>
            <label for={id} class="uk-form-label">{label}</label>
            <input id={id} class="uk-input" type="text" placeholder="" required={required} maxLength={255} onChange={e => onChange(e.currentTarget.value)} />
        </div>
    )
}

const PlanButton = ({ plan, translation: tr, selected, onClick }: { plan: Plan, translation: Dictionary, selected: boolean, onClick: ()=>void }) => {
    return (
        <div className={"access-plan " + (selected ? 'selected' : '')} onClick={onClick}>
            <div className="access-plan-title">{plan.title}</div>
            <div className="access-plan-price">
                <span class="abovePrice">{plan.abovePrice}</span>
                <span class="price">{plan.price} {tr.t("priceUnit")}</span>
                <span class="period">{plan.period}</span>
            </div>
            <div className="access-plan-description">{plan.description}</div>
        </div>
    );
}

type MemberInfo = {
    firstName: string,
    lastName: string,
    email: string,
    phone: string,
    zipCode: string,
}

const MemberInfoForm = ({ info, translation: tr, onChange }: { info: MemberInfo, translation: Dictionary, onChange: (info: MemberInfo)=>void }) => {
    return (
        <div className="member-info">
            <LabeledInput label={tr.t("memberInfo.firstName")} id="firstName" type="text" required value={info.firstName} onChange={firstName => onChange({...info, firstName})} />
            <LabeledInput label={tr.t("memberInfo.lastName")} id="lastName" type="text" required value={info.lastName} onChange={lastName => onChange({...info, lastName})} />
            <LabeledInput label={tr.t("memberInfo.email")} id="email" type="email" required value={info.email} onChange={email => onChange({...info, email})} />
            <LabeledInput label={tr.t("memberInfo.phone")} id="phone" type="text" required value={info.phone} onChange={phone => onChange({...info, phone})} />
            <LabeledInput label={tr.t("memberInfo.zipCode")} id="zipCode" type="text" required value={info.zipCode} onChange={zipCode => onChange({...info, zipCode})} />
        </div>
    )
}

enum State {
    ChooseLanguage,
    ChoosePlan,
    MemberInfo,
    Terms,
    Calendar,
    Confirmation,
}

const Panel = ({ children }: { children: any }) => {
    return (
        <div className="panel">
            {children}
        </div>
    );
}

const RegisterPage = () => {
    // Language chooser
    // Inspiration page?
    // Plan chooser
    // User details
    // Accept terms page
    // -> stripe
    // (Ideally calendar page)
    // Success page

    const [state, setState] = useState(State.ChoosePlan);
    const [language, setLanguage] = useState<keyof typeof Translations>("en");
    const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
    const [memberInfo, setMemberInfo] = useState<MemberInfo>({
        firstName: "",
        lastName: "",
        email: "",
        phone: "",
        zipCode: "",
    });

    const tr: Dictionary = new Translation(Translations[language]);
    const plans: Plan[] = [
        {
            id: "starterPack",
            title: tr.t("plans.starterPack.title"),
            abovePrice: tr.t("plans.starterPack.abovePrice"),
            price: 300,
            period: tr.t("plans.starterPack.period"),
            description: tr.t("plans.starterPack.description"),
        },
        {
            id: "makerspaceAccessSub",
            title: tr.t("plans.makerspaceAccessSub.title"),
            abovePrice: tr.t("plans.makerspaceAccessSub.abovePrice"),
            price: 300,
            period: tr.t("plans.makerspaceAccessSub.period"),
            description: tr.t("plans.makerspaceAccessSub.description"),
        },
        {
            id: "decideLater",
            title: tr.t("plans.decideLater.title"),
            abovePrice: tr.t("plans.decideLater.abovePrice"),
            price: 0,
            period: tr.t("plans.decideLater.period"),
            description: tr.t("plans.decideLater.description"),
        }
    ]

    switch (state) {
        case State.ChooseLanguage:
            return <LanguageChooser setLanguage={lang => {
                setLanguage(lang);
                setState(State.ChoosePlan);
            }} />;
        case State.ChoosePlan:
            return (<>
                <h1>{tr.t("memberships.title")}</h1>
                <p>{tr.t("memberships.p1")}</p>
                <p>{tr.t("memberships.p2")}</p>

                <Panel>
                    <h3>{tr.t("baseMembership.title")}</h3>
                    <ul>
                        {tr.t("baseMembership.reasons").map((reason, i) => <li key={i}>{reason}</li>)}
                    </ul>
                    <div className="price">
                        {tr.t("baseMembership.price")} {tr.t("priceUnit")}
                        <span className="period">{tr.t("baseMembership.period")}</span>
                    </div>
                </Panel>
                <Panel>
                    <h3>{tr.t("makerspaceAccess.title")}</h3>
                    <span className="small-price">{tr.t("makerspaceAccess.price")}</span>
                    <span className="requirement">{tr.t("makerspaceAccess.requirement")}</span>
                    <ul>
                        {tr.t("makerspaceAccess.reasons").map((reason, i) => <li key={i}>{reason}</li>)}
                    </ul>
                </Panel>
                <h2>{tr.t("chooseYourPlan")}</h2>
                {plans.map(plan => <PlanButton selected={selectedPlan === plan.id} onClick={() => setSelectedPlan(plan.id)} plan={plan} translation={tr} />)}
            </>);
        case State.MemberInfo:
            return (<>
                <h2>{tr.t("memberInfo.title")}</h2>
                <MemberInfoForm info={memberInfo} translation={tr} onChange={setMemberInfo} />
            </>);
        case State.Terms:
            return (<>
                <h2>{tr.t("terms.title")}</h2>
            </>);
        case State.Calendar:
            return (<>
                <h2>{tr.t("calendar.title")}</h2>
            </>);
        case State.Confirmation:
            return (<>
                <h2>{tr.t("confirmation.title")}</h2>
            </>);
    }
}

common.documentLoaded().then(() => {
    const root = document.getElementById('root');
    if (root != null) {
        render(
            <RegisterPage />,
            root
        );
    }
});
