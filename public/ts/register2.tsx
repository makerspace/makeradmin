import * as common from "./common";
import { Component, ComponentChildren, createContext, render } from 'preact';
import { StateUpdater, useContext, useEffect, useMemo, useRef, useState } from 'preact/hooks';
import { ServerResponse } from "./common";
import { Translation, TranslationKeyValues } from "./translate";
import { AssertIsWellKnownProductId, Discount, FindWellKnownProduct, PaymentAction, PaymentFailedError, PaymentIntentNextActionType, PriceLevel, Product, Purchase, RegisterPageData, RelevantProducts, SetupIntentResponse, StripeCardInput, ToPayPreview, calculateAmountToPay, createPaymentMethod, createStripeCardInput, display_stripe_error, extractRelevantProducts, handleStripeSetupIntent, stripe } from "./payment_common";
import { PopupModal, PopupWidget, useCalendlyEventListener } from "react-calendly";
import { CALENDAR, FACEBOOK_GROUP, GET_STARTED_QUIZ, INSTAGRAM, RELATIVE_MEMBER_PORTAL, SLACK_HELP, WIKI } from "./urls";
import { LoadCurrentMemberInfo, member_t } from "./member_common";
import { SubscriptionStart } from "./subscriptions";
import { Dictionary, TranslationContext, TranslationWrapper, Translations, useTranslation } from "./translations";

declare var UIkit: any;


type Plan = {
    id: PlanId,
    title: string,
    abovePrice: string,
    price: number,
    belowPrice: string,
    description1: string
    description2: string,
    products: Product[],
    highlight: string | null,
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

const LabeledInput = ({ label, id, required, type, value, pattern, onChange, onInvalid }: { id: string, type: string, pattern?: string, label: string, required: boolean, value: string, onChange: (value: string) => void, onInvalid: () => void }) => {
    return (
        <div>
            <label for={id} class="uk-form-label">{label}</label>
            <input id={id} class="uk-input" type={type} pattern={pattern} placeholder="" value={value} required={required} maxLength={255} onChange={e => onChange(e.currentTarget.value)} onInvalid={onInvalid} />
        </div>
    )
}

const PlanButton = ({ plan, selected, onClick, order }: { plan: Plan, selected: boolean, onClick: () => void, order: number }) => {
    const t = useTranslation();
    return (
        <div className={"access-plan " + (selected ? 'selected' : '') + ` semantic-order-${order}`} onClick={onClick}>
            <div className="access-plan-title">{plan.title}{plan.highlight !== null ? <span class="plan-highlight"><span>{plan.highlight}</span></span> : null}</div>
            <div className="access-plan-price">
                {plan.abovePrice && <span class="abovePrice">{plan.abovePrice}</span>}
                <span class="price">{plan.price} {t("priceUnit")}</span>
                {plan.belowPrice && <span class="belowPrice">{plan.belowPrice}</span>}
            </div>
            {plan.description1 && <div className="access-plan-description">{plan.description1}</div>}
            <ul className="checkmark-list">
                {t(`plans.${plan.id}.included`).map((reason, i) => <li key={i}><span className="positive" uk-icon="icon: check"></span> {reason}</li>)}
                {t(`plans.${plan.id}.notIncluded`).map((reason, i) => <li key={i}><span className="negative" uk-icon="icon: close"></span> {reason}</li>)}
            </ul>
            {plan.description2 && <div className="access-plan-description">{plan.description2}</div>}
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

type DiscountReason = "student" | "unemployed" | "senior" | "other";

type DiscountsInfo = {
    discountReason: DiscountReason | null,
    discountReasonMessage: string,
}

const BackButton = ({ onClick }: { onClick: () => void }) => {
    const t = useTranslation();
    return (
        <a className="flow-button-back" onClick={onClick}>{t("back")}</a>
    );
}

const MemberInfoForm = ({ info, onChange, onSubmit, onBack }: { info: MemberInfo, onChange: StateUpdater<MemberInfo>, onSubmit: (info: MemberInfo) => void, onBack: () => void }) => {
    const t = useTranslation();
    const [showErrors, setShowErrors] = useState(false);
    const onInvalid = () => setShowErrors(true);
    return (
        <form className={"member-info " + (showErrors ? "validate" : "")} onSubmit={e => {
            e.preventDefault();
            setShowErrors(false);
            onSubmit(info);
        }} onInvalid={() => {
            console.log("invalid");
            setShowErrors(true);
        }}>
            <LabeledInput label={t("memberInfo.firstName")} id="firstName" type="text" required value={info.firstName} onChange={firstName => onChange(info => ({ ...info, firstName }))} onInvalid={onInvalid} />
            <LabeledInput label={t("memberInfo.lastName")} id="lastName" type="text" required value={info.lastName} onChange={lastName => onChange(info => ({ ...info, lastName }))} onInvalid={onInvalid} />
            <LabeledInput label={t("memberInfo.email")} id="email" type="email" required value={info.email} onChange={email => onChange(info => ({ ...info, email }))} onInvalid={onInvalid} />
            <LabeledInput label={t("memberInfo.phone")} id="phone" type="tel" pattern="[\-\+\s0-9]*" required value={info.phone} onChange={phone => onChange(info => ({ ...info, phone }))} onInvalid={onInvalid} />
            <LabeledInput label={t("memberInfo.zipCode")} id="zipCode" type="text" pattern="[0-9\s]*" required value={info.zipCode} onChange={zipCode => onChange(info => ({ ...info, zipCode }))} onInvalid={onInvalid} />
            <input type="submit" className="flow-button primary" value={t("memberInfo.submit")} />
            <BackButton onClick={onBack} />
        </form>
    )
}

const RuleCheckbox = ({ rule, value, onChange }: { value: boolean, rule: string, onChange: StateUpdater<boolean> }) => {
    const id = `${(Math.random() * 10000) | 0}`;
    return (
        <div class="rule-checkbox">
            <input id={id} type="checkbox" checked={value} onChange={e => onChange(e.currentTarget.checked)} />
            <label for={id}>{rule}</label>
        </div>
    );
}

type Terms = {
    accepted1: boolean;
    accepted2: boolean;
    accepted3: boolean;
}

const TermsAndConditions = ({ onAccept, onBack, acceptedTerms, onChangeAcceptedTerms }: { onAccept: () => void, onBack: () => void, acceptedTerms: Terms, onChangeAcceptedTerms: (terms: Terms) => void }) => {
    const t = useTranslation();
    return (<div class="terms-and-conditions">
        <h2>{t("terms.title")}</h2>
        <p>{t("terms.pledge")}</p>
        <ol className="rules-list">
            {t("terms.rules").map(rule => <li>{rule}</li>)}
        </ol>

        <RuleCheckbox rule={t("terms.understanding1")} onChange={() => onChangeAcceptedTerms({ ...acceptedTerms, accepted1: !acceptedTerms.accepted1 })} value={acceptedTerms.accepted1} />
        <RuleCheckbox rule={t("terms.understanding2")} onChange={() => onChangeAcceptedTerms({ ...acceptedTerms, accepted2: !acceptedTerms.accepted2 })} value={acceptedTerms.accepted2} />
        <RuleCheckbox rule={t("terms.welcoming")} onChange={() => onChangeAcceptedTerms({ ...acceptedTerms, accepted3: !acceptedTerms.accepted3 })} value={acceptedTerms.accepted3} />
        <button className="flow-button primary" disabled={!acceptedTerms.accepted1 || !acceptedTerms.accepted2 || !acceptedTerms.accepted3} onClick={onAccept}>{t("terms.accept")}</button>
        <BackButton onClick={onBack} />
    </div>);
}

enum State {
    ChooseLanguage,
    ChoosePlan,
    MemberInfo,
    Terms,
    Calendar,
    Confirmation,
    Success,
    Discounts,
}

const Confirmation = ({ memberInfo, selectedPlan, relevantProducts, discount, discountInfo, card, onRegistered, onBack }: { memberInfo: MemberInfo, selectedPlan: Plan, relevantProducts: RelevantProducts, discount: Discount, discountInfo: DiscountsInfo, card: stripe.elements.Element, onRegistered: (r: RegistrationSuccess) => void, onBack: () => void }) => {
    const t = useTranslation();
    const [inProgress, setInProgress] = useState(false);

    return (<>
        {/* <h2>{t("payment.title")}</h2> */}
        <div class="uk-flex-1" />
        {t("payment.text")}
        <div class="uk-flex-1" />
        <ToPayPreview products={selectedPlan.products} discount={discount} currentMemberships={[]} />
        <div class="uk-flex-1" />
        <span class="payment-processor">{t("payment.payment_processor")}</span>
        <StripeCardInput element={card} />
        <button className="flow-button primary" disabled={inProgress} onClick={async () => {
            setInProgress(true);
            try {
                if (selectedPlan == null) {
                    throw new Error("No plan selected");
                }
                const paymentMethod = await createPaymentMethod(card, {
                    address_street: "",
                    address_extra: "",
                    address_zipcode: memberInfo.zipCode,
                    address_city: "",
                    email: memberInfo.email,
                    member_number: 0,
                    firstname: memberInfo.firstName,
                    lastname: memberInfo.lastName,
                    phone: "",
                    pin_code: "",
                    labaccess_agreement_at: "",
                });

                if (paymentMethod !== null) {
                    try {
                        onRegistered(await registerMember(paymentMethod, memberInfo, selectedPlan, discount, discountInfo, relevantProducts));
                    } catch (e) {
                        if (e instanceof PaymentFailedError) {
                            UIkit.modal.alert("<h2>Payment failed</h2>" + e.message);
                        } else {
                            throw e;
                        }
                    }
                }
            } finally {
                setInProgress(false);
            }
        }}>
            <span className={"uk-spinner uk-icon progress-spinner " + (inProgress ? "progress-spinner-visible" : "")} uk-spinner={''} />
            <span>{t("payment.pay")}</span>
        </button>
        <BackButton onClick={onBack} />
        <div class="uk-flex-1" />
    </>);
}

type DiscountRequest = {
    price_level: PriceLevel,
    message: string,
}

type RegisterRequest = {
    purchase: Purchase
    setup_intent_id: string | null
    member: MemberInfo
    subscriptions: SubscriptionStart[]
    discount: DiscountRequest | null
}

type RegistrationSuccess = {
    loginToken: string
}

async function registerMember(paymentMethod: stripe.paymentMethod.PaymentMethod, memberInfo: MemberInfo, selectedPlan: Plan, discount: Discount, discountInfo: DiscountsInfo, relevantProducts: RelevantProducts): Promise<RegistrationSuccess> {
    const { payNow, payRecurring } = calculateAmountToPay({ products: selectedPlan.products, discount, currentMemberships: [] })
    const nonSubscriptionProducts = selectedPlan.products.filter(p => p.product_metadata.subscription_type === undefined);
    const data: RegisterRequest = {
        member: memberInfo,
        purchase: {
            cart: nonSubscriptionProducts.map(p => ({
                id: p.id,
                count: 1,
            })),
            expected_sum: "" + payNow.filter(p => p.product.product_metadata.subscription_type === undefined).reduce((sum, { amount }) => sum + amount, 0),
            stripe_payment_method_id: paymentMethod.id,
        },
        subscriptions: selectedPlan.products.filter(p => p.product_metadata.subscription_type !== undefined).map(p => {
            const payNowForSubscription = payNow.find(({ product }) => p == product);
            const payRecurringForSubscription = payRecurring.find(({ product }) => p == product);
            return {
                subscription: p.product_metadata.subscription_type!,
                expected_to_pay_now: "" + (payNowForSubscription ? payNowForSubscription.amount : 0),
                expected_to_pay_recurring: "" + (payRecurringForSubscription ? payRecurringForSubscription.amount : 0),
            }
        }),
        setup_intent_id: null,
        discount: discount.priceLevel !== null && discountInfo.discountReason !== null ? {
            price_level: discount.priceLevel,
            message: `${discountInfo.discountReason}: ${discountInfo.discountReasonMessage}`,
        } : null,
    };

    return {
        loginToken: (await handleStripeSetupIntent<RegisterRequest, SetupIntentResponse & { token: string }>(window.apiBasePath + "/webshop/register", data)).token!
    };
}



const CheckIcon = ({ done }: { done: boolean }) => {
    return <span className={"uk-icon-small uk-icon task " + (done ? "task-done" : "")} uk-icon="icon: check"></span>
}

const Success = ({ member }: { member: member_t }) => {
    const [isBookModalOpen, setBookModalOpen] = useState(false);
    const [booked, setBooked] = useState(false);
    const [clickedSteps, setClickedSteps] = useState(new Set<number>());
    console.log("Rendering", clickedSteps);
    const t = useTranslation();

    useCalendlyEventListener({
        onEventScheduled: () => {
            setBooked(true);
        }
    })

    return (<>
        <h1>{t("success.title")}</h1>
        {t("success.text")}
        <ul className="registration-task-list">
            <li>
                <CheckIcon done={booked} />
                <div class="uk-flex uk-flex-column">
                    <span>{t("success.book_step")}</span>
                    <button className="flow-button primary flow-button-small" onClick={() => setBookModalOpen(true)}>{t("success.book_button")}</button>
                </div>
            </li>
            {t("success.steps").map((step, i) => <li key={i}><CheckIcon done={clickedSteps.has(i)} /><span>{step((e) => setClickedSteps(new Set(clickedSteps).add(i)))}</span></li>)}
        </ul>
        <div class="uk-flex-1" />
        <a href={RELATIVE_MEMBER_PORTAL} className="flow-button primary" >{t("success.continue_to_member_portal")}</a>
        <PopupModal
            url="https://calendly.com/medlemsintroduktion/medlemsintroduktion"
            rootElement={document.getElementById("root")!}
            open={isBookModalOpen}
            onModalClose={() => setBookModalOpen(false)}
            prefill={{
                name: member.firstname + " " + member.lastname,
                firstName: member.firstname,
                lastName: member.lastname,
                email: member.email,
            }}
        />
    </>);
}

const Discounts = ({ discounts, setDiscounts, onSubmit, discountAmounts }: { discounts: DiscountsInfo, discountAmounts: Record<PriceLevel, number>, setDiscounts: (m: DiscountsInfo) => void, onSubmit: () => void }) => {
    const t = useTranslation();

    const reasons: DiscountReason[] = ["student", "unemployed", "senior", "other"];
    const [step, setStep] = useState(0);

    if (step == 0) {
        return <>
            <h2>{t("discounts.title")}</h2>
            <p>{t("discounts.text")}</p>

            {reasons.map(reason =>
                <div class="rule-checkbox">
                    <input id={`reason.${reason}`} type="checkbox" checked={discounts.discountReason === reason} onChange={(e) => setDiscounts({ ...discounts, discountReason: e.currentTarget.checked ? reason : null })} />
                    <label for={`reason.${reason}`}>{t(`discounts.reasons.${reason}`)}</label>
                </div>
            )}
            <textarea placeholder={t("discounts.messagePlaceholder")} value={discounts.discountReasonMessage} onChange={(e) => setDiscounts({ ...discounts, discountReasonMessage: e.currentTarget.value })} />
            <button className="flow-button primary" onClick={() => setStep(1)} disabled={discounts.discountReason === null || discounts.discountReasonMessage.length < 30}>{t("discounts.submit")}</button>
            <button className="flow-button primary" onClick={() => {
                setDiscounts({ discountReason: null, discountReasonMessage: "" });
                onSubmit();
            }}>{t("discounts.cancel")}</button>
        </>;
    } else {
        return <>
            <h2>{t("discounts.title")}</h2>
            {t("discounts.confirmation")(discountAmounts["low_income_discount"])}
            <button className="flow-button primary" onClick={onSubmit}>{t("discounts.submit")}</button>
            <button className="flow-button primary" onClick={() => {
                setDiscounts({ discountReason: null, discountReasonMessage: "" });
                onSubmit();
            }}>{t("discounts.cancel")}</button>
        </>
    }
}

const Calendar = ({ member }: { member: member_t }) => {
    const t = useTranslation();
    console.log(member);
    return (
        <>
            <h2>{t("calendar.title")}</h2>
            <p>{t("calendar.text")}</p>
            <PopupWidget
                url="https://calendly.com/medlemsintroduktion/medlemsintroduktion"
                text={t("calendar.book_button")}
                rootElement={document.getElementById("root")!}
                prefill={{
                    name: member.firstname + " " + member.lastname,
                    firstName: member.firstname,
                    lastName: member.lastname,
                    email: member.email,
                }}
            />
        </>
    )
}

const MakerspaceLogo = () => {
    return <img src={window.staticBasePath + "/images/logo-transparent-500px-300x210.png"} alt="Makerspace Logo" className="registration-logo" />
}

type PlanId = "starterPack" | "makerspaceAccessSub" | "decideLater" | "singleMonth";

const RegisterPage = ({ }: {}) => {
    // Language chooser
    // Inspiration page?
    // Plan chooser
    // User details
    // Accept terms page
    // -> stripe
    // (Ideally calendar page)
    // Success page

    const [state, setState] = useState(State.ChoosePlan);
    const [selectedPlan, setSelectedPlan] = useState<PlanId | null>("starterPack"); // TODO: Should be null
    const [memberInfo, setMemberInfo] = useState<MemberInfo>({
        firstName: "",
        lastName: "",
        email: "",
        phone: "",
        zipCode: "",
    });
    const [acceptedTerms, setAcceptedTerms] = useState({
        accepted1: false,
        accepted2: false,
        accepted3: false
    });

    // TODO
    const [loggedInMember, setLoggedInMember] = useState<member_t | null>({
        address_street: "",
        address_extra: "",
        address_zipcode: "",
        address_city: "",
        email: "a.b@gmail.com",
        member_number: 1234,
        firstname: "Aron",
        lastname: "Granberg",
        phone: "0735986675",
        pin_code: "1234",
        labaccess_agreement_at: "2020-01-01",
    });
    const t = useTranslation();
    const card = useMemo(() => createStripeCardInput(), []);
    const [registerPageData, setRegisterPageData] = useState<RegisterPageData | null>(null);
    const [discounts, setDiscounts] = useState<DiscountsInfo>({
        discountReason: null,
        discountReasonMessage: "",
    });


    useEffect(() => {
        common.ajax('GET', `${window.apiBasePath}/webshop/register_page_data`).then(x => {
            setRegisterPageData(x.data);
        });
    }, []);

    if (registerPageData === null) {
        return <div>Loading...</div>
    }

    const priceLevel: PriceLevel = discounts.discountReason !== null ? "low_income_discount" : "normal";
    const discount: Discount = {
        priceLevel,
        fractionOff: registerPageData.discounts[priceLevel],
    }

    const relevantProducts = extractRelevantProducts(registerPageData.productData);
    const accessCostSingle = parseFloat(relevantProducts.labaccessProduct.price) * (1 - discount.fractionOff);
    const accessSubscriptionCost = parseFloat(relevantProducts.labaccessSubscriptionProduct.price) * (1 - discount.fractionOff);
    const baseMembershipCost = parseFloat(relevantProducts.baseMembershipProduct.price) * (1 - discount.fractionOff);

    const plans: Plan[] = [
        {
            id: "starterPack",
            title: t("plans.starterPack.title"),
            abovePrice: t("plans.starterPack.abovePrice"),
            price: parseFloat(relevantProducts.starterPackProduct.price),
            belowPrice: t("plans.ofWhichBaseMembership")(baseMembershipCost),
            description1: t("plans.starterPack.description1"),
            description2: t("plans.starterPack.description2"),
            products: [relevantProducts.starterPackProduct, relevantProducts.membershipSubscriptionProduct],
            highlight: "Recommended",
        },
        {
            id: "singleMonth",
            title: t("plans.singleMonth.title"),
            abovePrice: t("plans.singleMonth.abovePrice"),
            price: parseFloat(relevantProducts.labaccessProduct.price),
            belowPrice: t("plans.ofWhichBaseMembership")(baseMembershipCost),
            description1: t("plans.singleMonth.description1"),
            description2: t("plans.singleMonth.description2"),
            products: [relevantProducts.labaccessProduct, relevantProducts.membershipSubscriptionProduct],
            highlight: null,
        },
        // {
        //     id: "makerspaceAccessSub",
        //     title: t("plans.makerspaceAccessSub.title"),
        //     abovePrice: t("plans.makerspaceAccessSub.abovePrice"),
        //     price: parseFloat(relevantProducts.labaccessSubscriptionProduct.price),
        //     period: t("plans.makerspaceAccessSub.period"),
        //     description: t("plans.makerspaceAccessSub.description"),
        //     products: [relevantProducts.membershipSubscriptionProduct, relevantProducts.labaccessSubscriptionProduct],
        //     highlight: null,
        // },
        {
            id: "decideLater",
            title: t("plans.decideLater.title"),
            abovePrice: t("plans.decideLater.abovePrice"),
            price: 0,
            belowPrice: "",
            description1: t("plans.decideLater.description1"),
            description2: t("plans.decideLater.description2")(accessCostSingle, accessSubscriptionCost),
            products: [relevantProducts.membershipSubscriptionProduct],
            highlight: null,
        },
        // {
        //     id: "discounted",
        //     title: t("plans.discounted.title"),
        //     abovePrice: t("plans.discounted.abovePrice"),
        //     price: 0,
        //     period: t("plans.discounted.period"),
        //     description: t("plans.discounted.description"),
        //     products: [relevantProducts.membershipSubscriptionProduct],
        //     highlight: null,
        // }
    ];

    for (const plan of plans) {
        const toPay = calculateAmountToPay({ products: plan.products, discount: discount, currentMemberships: [] });
        plan.price = toPay.payNow.reduce((a, b) => a + b.amount, 0);
    }

    const lowestMakerspaceAccessPrice = Math.min(accessCostSingle, accessSubscriptionCost);
    const highestMakerspaceAccessPrice = Math.max(accessCostSingle, accessSubscriptionCost);
    const activePlan = plans.find(plan => plan.id === selectedPlan);

    switch (state) {
        case State.ChooseLanguage:
            return <LanguageChooser setLanguage={lang => {
                setState(State.ChoosePlan);
            }} />;
        case State.ChoosePlan:
            return (<>
                <MakerspaceLogo />
                <h1>{t("memberships.title")}</h1>
                <p>{t("memberships.p1")}</p>
                <p>{t("memberships.p2")}</p>

                <h2>{t("chooseYourPlan.title")}</h2>
                <span>{t("chooseYourPlan.help")}</span>
                <div class="plan-buttons">
                    {plans.map((plan, i) => <PlanButton selected={selectedPlan === plan.id} onClick={() => setSelectedPlan(plan.id)} plan={plan} order={i} />)}
                </div>
                {registerPageData.discounts["low_income_discount"] > 0 && <button className="flow-button" onClick={() => setState(State.Discounts)}>{t("apply_for_discounts")}</button>}
                {activePlan !== undefined ? <ToPayPreview products={activePlan.products} discount={discount} currentMemberships={[]} /> : null}
                <button className="flow-button primary" disabled={selectedPlan == null} onClick={() => setState(State.MemberInfo)}>{t("continue")}</button>
            </>);
        case State.MemberInfo:
            return (<>
                <MakerspaceLogo />
                <h2>{t("memberInfo.title")}</h2>
                <MemberInfoForm info={memberInfo} onChange={setMemberInfo} onSubmit={(_) => setState(State.Terms)} onBack={() => setState(State.ChoosePlan)} />
            </>);
        case State.Terms:
            return (<>
                <MakerspaceLogo />
                <TermsAndConditions onAccept={() => setState(State.Confirmation)} onBack={() => setState(State.MemberInfo)} acceptedTerms={acceptedTerms} onChangeAcceptedTerms={setAcceptedTerms} />
            </>);
        case State.Calendar:
            // TODO: Should get member info from server, as it has been validated there
            if (loggedInMember === null) throw new Error("No logged in member");

            return (<>
                <MakerspaceLogo />
                <Calendar member={loggedInMember} />
            </>);
        case State.Confirmation:
            if (activePlan === undefined) throw new Error("No active plan");
            return <>
                <MakerspaceLogo />
                <Confirmation
                    card={card}
                    selectedPlan={activePlan}
                    memberInfo={memberInfo}
                    relevantProducts={relevantProducts}
                    discount={discount}
                    discountInfo={discounts}
                    onRegistered={async (r) => {
                        common.login(r.loginToken);
                        setLoggedInMember(await LoadCurrentMemberInfo());
                        setState(State.Success);
                    }}
                    onBack={() => setState(State.Terms)}
                />
            </>;
        case State.Success:
            if (loggedInMember === null) throw new Error("No logged in member");

            return <>
                <MakerspaceLogo />
                <Success member={loggedInMember} />
            </>;
        case State.Discounts:
            return <>
                <MakerspaceLogo />
                <Discounts discounts={discounts} setDiscounts={setDiscounts} discountAmounts={registerPageData.discounts} onSubmit={() => {
                    setState(State.ChoosePlan);
                }} />
            </>
    }
}

common.documentLoaded().then(() => {
    const root = document.getElementById('root');
    if (root != null) {
        render(
            <TranslationWrapper>
                <div className="content-wrapper">
                    <RegisterPage />
                </div>
            </TranslationWrapper>,
            root
        );
    }
});
