import * as common from "./common";
import { Component, render } from 'preact';
import { useState } from 'preact/hooks';
import { ServerResponse } from "./common";

type Plan = {
    id: string,
    title: string,
    price: number,
    unit: string,
    period: string,
    description: string,
    extraText: string,
}

type Dictionary = {
    [x: string]: string | Dictionary;
  };

const Translations: { "en": Dictionary } = {
    "en": {
        "makerspaceAccessSub": {
            "title": "Makerspace Access Subscription",
            "price": "300",
            "unit": "kr",
            "period": "per month",
            "description": "A monthly subscription gets you access all the time, for a lower price.\n2 months minimum.",
            "extraText": "",
        }
    }
}

class Translation {
    private translations: Dictionary;

    constructor(translations: { "en": Dictionary }) {
        this.translations = translations["en"];
    }

    t(key: string): string {
        const parts = key.split(".");
        let item = this.translations;
        for (let i = 0; i < parts.length - 1; i++) {
            let child = item[parts[i]];
            if (child === null || child === undefined) {
                throw new Error("Missing translation for " + key);
            } else if (typeof child === "string") {
                throw new Error("Missing translation for " + key);
            }
            item = child;
        }
        const v = item[parts[parts.length-1]];
        if (typeof v === "string") {
            return v;
        } else {
            throw new Error("Missing translation for " + key);
        }
    }
}

const PlanButton = (plan: Plan, translation: Translation) => {
    const extra = translation.t(plan.extraText);
    
    return (
        <div className="access-plan">
            <div className="access-plan-title">{translation.t(plan.title)}</div>
            <div className="access-plan-price">
                <span class="price">{plan.price} {translation.t(plan.unit)}</span>
                <span class="period">{translation.t(plan.period)}</span>
                {extra ? <span class="extra-text">{extra}</span> : null}
            </div>
            <div className="access-plan-description">{translation.t(plan.description)}</div>
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
    return PlanButton({
        id: "makerspaceAccessSub",
        title: "makerspaceAccessSub.title",
        price: 300,
        unit: "makerspaceAccessSub.unit",
        period: "makerspaceAccessSub.period",
        description: "makerspaceAccessSub.description",
        extraText: "makerspaceAccessSub.extraText",
    }, new Translation(Translations));
}

common.documentLoaded().then(() => {
    const root = document.getElementById('root');
    if (root != null) {
        render(
            <RegisterPage/>,
            root
        );
    }
});
