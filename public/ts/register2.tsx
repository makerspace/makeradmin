import * as common from "./common";
import { render } from 'preact';
import { StateUpdater, useEffect, useMemo, useState } from 'preact/hooks';
import { ServerResponse } from "./common";
import { BackendPaymentResponse, Discount, PaymentFailedError, PriceLevel, Product, ProductData, ProductDataFromProducts, RegisterPageData, RelevantProducts, SetupIntentResponse, SetupPaymentMethodRequest, StripeCardInput, ToPayPreview, calculateAmountToPay, createPaymentMethod, createStripeCardInput, extractRelevantProducts, handleStripeSetupIntent, initializeStripe, negotiatePayment, pay } from "./payment_common";
import { PopupModal, PopupWidget, useCalendlyEventListener } from "react-calendly";
import { URL_RELATIVE_MEMBER_PORTAL } from "./urls";
import { LoadCurrentMemberInfo, member_t } from "./member_common";
import { StartSubscriptionsRequest, SubscriptionStart } from "./subscriptions";
import { PaymentRequest } from "./payment_common";
import { TranslationWrapper, Translations, useTranslation } from "./translations";
import Cart from "./cart";

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
            {plan.description1 && <div className="access-plan-description-top">{plan.description1}</div>}
            <ul className="checkmark-list">
                {t(`registration_page.plans.${plan.id}.included`).map((reason, i) => <li key={i}><span className="positive" uk-icon="icon: check"></span> {reason}</li>)}
                {t(`registration_page.plans.${plan.id}.notIncluded`).map((reason, i) => <li key={i}><span className="negative" uk-icon="icon: close"></span> {reason}</li>)}
            </ul>
            {plan.description2 && <div className="access-plan-description-bottom">{plan.description2}</div>}
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
            <LabeledInput label={t("registration_page.memberInfo.firstName")} id="firstName" type="text" required value={info.firstName} onChange={firstName => onChange(info => ({ ...info, firstName }))} onInvalid={onInvalid} />
            <LabeledInput label={t("registration_page.memberInfo.lastName")} id="lastName" type="text" required value={info.lastName} onChange={lastName => onChange(info => ({ ...info, lastName }))} onInvalid={onInvalid} />
            <LabeledInput label={t("registration_page.memberInfo.email")} id="email" type="email" required value={info.email} onChange={email => onChange(info => ({ ...info, email }))} onInvalid={onInvalid} />
            <LabeledInput label={t("registration_page.memberInfo.phone")} id="phone" type="tel" pattern="[\-\+\s0-9]*" required value={info.phone} onChange={phone => onChange(info => ({ ...info, phone }))} onInvalid={onInvalid} />
            <LabeledInput label={t("registration_page.memberInfo.zipCode")} id="zipCode" type="text" pattern="[0-9\s]*" required value={info.zipCode} onChange={zipCode => onChange(info => ({ ...info, zipCode }))} onInvalid={onInvalid} />
            <input type="submit" className="flow-button primary" value={t("registration_page.memberInfo.submit")} />
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
        <h2>{t("registration_page.terms.title")}</h2>
        <p>{t("registration_page.terms.pledge")}</p>
        <ol className="rules-list">
            {t("registration_page.terms.rules").map(rule => <li>{rule}</li>)}
        </ol>

        <RuleCheckbox rule={t("registration_page.terms.understanding1")} onChange={() => onChangeAcceptedTerms({ ...acceptedTerms, accepted1: !acceptedTerms.accepted1 })} value={acceptedTerms.accepted1} />
        <RuleCheckbox rule={t("registration_page.terms.understanding2")} onChange={() => onChangeAcceptedTerms({ ...acceptedTerms, accepted2: !acceptedTerms.accepted2 })} value={acceptedTerms.accepted2} />
        <RuleCheckbox rule={t("registration_page.terms.welcoming")} onChange={() => onChangeAcceptedTerms({ ...acceptedTerms, accepted3: !acceptedTerms.accepted3 })} value={acceptedTerms.accepted3} />
        <button className="flow-button primary" disabled={!acceptedTerms.accepted1 || !acceptedTerms.accepted2 || !acceptedTerms.accepted3} onClick={onAccept}>{t("registration_page.terms.accept")}</button>
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

const Confirmation = ({ memberInfo, selectedPlan, productData, discount, discountInfo, card, onRegistered, onBack }: { memberInfo: MemberInfo, selectedPlan: Plan, productData: ProductData, discount: Discount, discountInfo: DiscountsInfo, card: stripe.elements.Element, onRegistered: (r: RegistrationSuccess) => void, onBack: () => void }) => {
    const t = useTranslation();
    const [inProgress, setInProgress] = useState(false);

    return (<>
        {/* <h2>{t("payment.title")}</h2> */}
        <div class="uk-flex-1" />
        {t("registration_page.payment.text")}
        <div class="uk-flex-1" />
        <ToPayPreview productData={productData} cart={Cart.oneOfEachProduct(selectedPlan.products)} discount={discount} currentMemberships={[]} />
        <div class="uk-flex-1" />
        <span class="payment-processor">{t("registration_page.payment.payment_processor")}</span>
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
                        onRegistered(await registerMember(paymentMethod, productData, memberInfo, selectedPlan, discount, discountInfo));
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
            <span>{t("registration_page.payment.pay")}</span>
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
    member: MemberInfo
    discount: DiscountRequest | null
}

type RegisterResponse = {
    token: string
    member_id: number
}

type RegistrationSuccess = {
    loginToken: string
}

async function registerMember(paymentMethod: stripe.paymentMethod.PaymentMethod, productData: ProductData, memberInfo: MemberInfo, selectedPlan: Plan, discount: Discount, discountInfo: DiscountsInfo): Promise<RegistrationSuccess> {
    const data: RegisterRequest = {
        member: memberInfo,
        discount: discount.priceLevel !== null && discountInfo.discountReason !== null ? {
            price_level: discount.priceLevel,
            message: `${discountInfo.discountReason}: ${discountInfo.discountReasonMessage}`,
        } : null,
    };

    // This registers the member as pending
    // If the payment fails, we can safely forget about the member (it will be cleaned up during the next registration attempt).
    let loginToken: string;
    try {
        loginToken = (await common.ajax('POST', `${window.apiBasePath}/webshop/register`, data) as ServerResponse<RegisterResponse>).data.token;
    } catch (e) {
        throw new PaymentFailedError(common.get_error(e));
    }

    const cart = new Cart(
        selectedPlan.products.map(p => ({
            id: p.id,
            count: 1
        }))
    )

    await pay(paymentMethod, cart, productData, discount, [], { loginToken });

    return { loginToken };
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
        <h1>{t("registration_page.success.title")}</h1>
        {t("registration_page.success.text")}
        <ul className="registration-task-list">
            <li>
                <CheckIcon done={booked} />
                <div class="uk-flex uk-flex-column">
                    <span>{t("registration_page.success.book_step")}</span>
                    <button className="flow-button primary flow-button-small" onClick={() => setBookModalOpen(true)}>{t("registration_page.success.book_button")}</button>
                </div>
            </li>
            {t("registration_page.success.steps").map((step, i) => <li key={i}><CheckIcon done={clickedSteps.has(i)} /><span>{step((e) => setClickedSteps(new Set(clickedSteps).add(i)))}</span></li>)}
        </ul>
        <div class="uk-flex-1" />
        <a href={URL_RELATIVE_MEMBER_PORTAL} className="flow-button primary" >{t("registration_page.success.continue_to_member_portal")}</a>
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
            <h2>{t("registration_page.discounts.title")}</h2>
            <p>{t("registration_page.discounts.text")}</p>

            {reasons.map(reason =>
                <div class="rule-checkbox">
                    <input id={`reason.${reason}`} type="checkbox" checked={discounts.discountReason === reason} onChange={(e) => setDiscounts({ ...discounts, discountReason: e.currentTarget.checked ? reason : null })} />
                    <label for={`reason.${reason}`}>{t(`registration_page.discounts.reasons.${reason}`)}</label>
                </div>
            )}
            <textarea placeholder={t("registration_page.discounts.messagePlaceholder")} value={discounts.discountReasonMessage} onChange={(e) => setDiscounts({ ...discounts, discountReasonMessage: e.currentTarget.value })} />
            <button className="flow-button primary" onClick={() => setStep(1)} disabled={discounts.discountReason === null || discounts.discountReasonMessage.length < 30}>{t("registration_page.discounts.submit")}</button>
            <button className="flow-button primary" onClick={() => {
                setDiscounts({ discountReason: null, discountReasonMessage: "" });
                onSubmit();
            }}>{t("registration_page.discounts.cancel")}</button>
        </>;
    } else {
        return <>
            <h2>{t("registration_page.discounts.title")}</h2>
            {t("registration_page.discounts.confirmation")(discountAmounts["low_income_discount"])}
            <button className="flow-button primary" onClick={onSubmit}>{t("registration_page.discounts.submit")}</button>
            <button className="flow-button primary" onClick={() => {
                setDiscounts({ discountReason: null, discountReasonMessage: "" });
                onSubmit();
            }}>{t("registration_page.discounts.cancel")}</button>
        </>
    }
}

const Calendar = ({ member }: { member: member_t }) => {
    const t = useTranslation();
    console.log(member);
    return (
        <>
            <h2>{t("registration_page.calendar.title")}</h2>
            <p>{t("registration_page.calendar.text")}</p>
            <PopupWidget
                url="https://calendly.com/medlemsintroduktion/medlemsintroduktion"
                text={t("registration_page.calendar.book_button")}
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
    const [productData, setProductData] = useState<ProductData | null>(null);


    useEffect(() => {
        common.ajax('GET', `${window.apiBasePath}/webshop/register_page_data`).then(x => {
            setRegisterPageData(x.data);
            setProductData(ProductDataFromProducts((x.data as RegisterPageData).productData));
        });
    }, []);

    if (registerPageData === null || productData === null) {
        return <div>Loading...</div>
    }

    const priceLevel: PriceLevel = discounts.discountReason !== null ? "low_income_discount" : "normal";
    const discount: Discount = {
        priceLevel,
        fractionOff: registerPageData.discounts[priceLevel],
    }

    const relevantProducts = extractRelevantProducts(productData.products);
    const accessCostSingle = parseFloat(relevantProducts.labaccessProduct.price) * (1 - discount.fractionOff);
    const accessSubscriptionCost = parseFloat(relevantProducts.labaccessSubscriptionProduct.price) * (1 - discount.fractionOff);
    const baseMembershipCost = parseFloat(relevantProducts.baseMembershipProduct.price) * (1 - discount.fractionOff);

    const plans: Plan[] = [
        {
            id: "starterPack",
            title: t("registration_page.plans.starterPack.title"),
            abovePrice: t("registration_page.plans.starterPack.abovePrice"),
            price: parseFloat(relevantProducts.starterPackProduct.price),
            belowPrice: t("registration_page.plans.ofWhichBaseMembership")(baseMembershipCost),
            description1: t("registration_page.plans.starterPack.description1"),
            description2: t("registration_page.plans.starterPack.description2"),
            products: [relevantProducts.starterPackProduct, relevantProducts.membershipSubscriptionProduct],
            highlight: "Recommended",
        },
        {
            id: "singleMonth",
            title: t("registration_page.plans.singleMonth.title"),
            abovePrice: t("registration_page.plans.singleMonth.abovePrice"),
            price: parseFloat(relevantProducts.labaccessProduct.price),
            belowPrice: t("registration_page.plans.ofWhichBaseMembership")(baseMembershipCost),
            description1: t("registration_page.plans.singleMonth.description1"),
            description2: t("registration_page.plans.singleMonth.description2"),
            products: [relevantProducts.labaccessProduct, relevantProducts.membershipSubscriptionProduct],
            highlight: null,
        },
        // {
        //     id: "makerspaceAccessSub",
        //     title: t("registration_page.plans.makerspaceAccessSub.title"),
        //     abovePrice: t("registration_page.plans.makerspaceAccessSub.abovePrice"),
        //     price: parseFloat(relevantProducts.labaccessSubscriptionProduct.price),
        //     period: t("registration_page.plans.makerspaceAccessSub.period"),
        //     description: t("registration_page.plans.makerspaceAccessSub.description"),
        //     products: [relevantProducts.membershipSubscriptionProduct, relevantProducts.labaccessSubscriptionProduct],
        //     highlight: null,
        // },
        {
            id: "decideLater",
            title: t("registration_page.plans.decideLater.title"),
            abovePrice: t("registration_page.plans.decideLater.abovePrice"),
            price: 0,
            belowPrice: "",
            description1: t("registration_page.plans.decideLater.description1"),
            description2: t("registration_page.plans.decideLater.description2")(accessCostSingle, accessSubscriptionCost),
            products: [relevantProducts.membershipSubscriptionProduct],
            highlight: null,
        },
        // {
        //     id: "discounted",
        //     title: t("registration_page.plans.discounted.title"),
        //     abovePrice: t("registration_page.plans.discounted.abovePrice"),
        //     price: 0,
        //     period: t("registration_page.plans.discounted.period"),
        //     description: t("registration_page.plans.discounted.description"),
        //     products: [relevantProducts.membershipSubscriptionProduct],
        //     highlight: null,
        // }
    ];

    for (const plan of plans) {
        const toPay = calculateAmountToPay({ productData, cart: Cart.oneOfEachProduct(plan.products), discount: discount, currentMemberships: [] });
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
                <h1>{t("registration_page.memberships.title")}</h1>
                <p>{t("registration_page.memberships.p1")}</p>
                <p>{t("registration_page.memberships.p2")}</p>

                <h2>{t("registration_page.chooseYourPlan.title")}</h2>
                <span>{t("registration_page.chooseYourPlan.help")}</span>
                <div class="plan-buttons">
                    {plans.map((plan, i) => <PlanButton selected={selectedPlan === plan.id} onClick={() => setSelectedPlan(plan.id)} plan={plan} order={i} />)}
                </div>
                {registerPageData.discounts["low_income_discount"] > 0 && <button className="flow-button" onClick={() => setState(State.Discounts)}>{t("apply_for_discounts")}</button>}
                {activePlan !== undefined ? <ToPayPreview productData={productData} cart={Cart.oneOfEachProduct(activePlan.products)} discount={discount} currentMemberships={[]} /> : null}
                <button className="flow-button primary" disabled={selectedPlan == null} onClick={() => setState(State.MemberInfo)}>{t("continue")}</button>
            </>);
        case State.MemberInfo:
            return (<>
                <MakerspaceLogo />
                <h2>{t("registration_page.memberInfo.title")}</h2>
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
                    productData={productData}
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
    initializeStripe();
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
