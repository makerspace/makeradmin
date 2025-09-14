import { ComponentChildren, JSX, render } from "preact";
import {
    Dispatch,
    StateUpdater,
    useEffect,
    useMemo,
    useState,
} from "preact/hooks";
import { PopupModal, useCalendlyEventListener } from "react-calendly";
import { Trans } from "react-i18next";
import Cart from "./cart";
import { show_phone_number_dialog } from "./change_phone";
import * as common from "./common";
import { ServerResponse, trackPlausible } from "./common";
import { Translator, useTranslation } from "./i18n";
import { LoadCurrentMemberInfo, member_t } from "./member_common";
import {
    calculateAmountToPay,
    createPaymentMethod,
    createStripeCardInput,
    Discount,
    extractRelevantProducts,
    initializeStripe,
    pay,
    PaymentFailedError,
    PriceLevel,
    Product,
    ProductData,
    ProductDataFromProducts,
    RegisterPageData,
    StripeCardInput,
    ToPayPreview,
} from "./payment_common";
import {
    accessyURL,
    URL_CALENDLY_BOOK,
    URL_GET_STARTED_QUIZ,
    URL_INSTAGRAM,
    URL_RELATIVE_MEMBER_PORTAL,
    URL_SLACK_HELP,
    URL_SLACK_SIGNUP,
    URL_WIKI,
} from "./urls";

declare var UIkit: any;
const FEATURE_FLAG_LOW_INCOME_DISCOUNT = false;

type Plan = {
    id: PlanId;
    title: string;
    abovePrice: string;
    price: string;
    belowPrice: string;
    description1: string;
    description2: string;
    products: Product[];
    highlight: string | null;
};

const LabeledInput = ({
    label,
    id,
    required,
    type,
    value,
    pattern,
    onChange,
    onInvalid,
    placeholder,
    autoComplete,
}: {
    id: string;
    type: string;
    pattern?: string;
    label: string;
    required: boolean;
    value: string;
    placeholder?: string;
    onChange: (value: string) => void;
    onInvalid: () => void;
    autoComplete?: string;
}) => {
    return (
        <div>
            <label for={id} class="uk-form-label">
                {label}
            </label>
            <input
                id={id}
                class="uk-input"
                type={type}
                pattern={pattern}
                placeholder={placeholder}
                value={value}
                required={required}
                maxLength={255}
                onChange={(e) => onChange(e.currentTarget.value)}
                onInvalid={onInvalid}
                autoComplete={autoComplete}
            />
        </div>
    );
};

const PlanButton = ({
    plan,
    selected,
    onClick,
    order,
}: {
    plan: Plan;
    selected: boolean;
    onClick: () => void;
    order: number;
}) => {
    const { t } = useTranslation("register");
    return (
        <div
            className={
                "access-plan " +
                (selected ? "selected" : "") +
                ` semantic-order-${order}`
            }
            onClick={onClick}
        >
            <div className="access-plan-title">
                {plan.title}
                {plan.highlight !== null ? (
                    <span class="plan-highlight">
                        <span>{plan.highlight}</span>
                    </span>
                ) : null}
            </div>
            <div className="access-plan-price">
                {plan.abovePrice && (
                    <span class="abovePrice">{plan.abovePrice}</span>
                )}
                <span class="price">{plan.price}</span>
                {plan.belowPrice && (
                    <span class="belowPrice">{plan.belowPrice}</span>
                )}
            </div>
            {plan.description1 && (
                <div className="access-plan-description-top">
                    {plan.description1}
                </div>
            )}
            <ul className="checkmark-list">
                {t(`plans.${plan.id}.included`).map((reason, i) => (
                    <li key={i}>
                        <span className="positive" uk-icon="icon: check"></span>{" "}
                        {reason}
                    </li>
                ))}
                {t(`plans.${plan.id}.notIncluded`).map((reason, i) => (
                    <li key={i}>
                        <span className="negative" uk-icon="icon: close"></span>{" "}
                        {reason}
                    </li>
                ))}
            </ul>
            {plan.description2 && (
                <div className="access-plan-description-bottom">
                    {plan.description2}
                </div>
            )}
        </div>
    );
};

type MemberInfo = {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    zipCode: string;
};

type MemberInfoValidated = {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    zipCode: number;
};

type DiscountReason = "student" | "unemployed" | "senior" | "other";

type DiscountsInfo = {
    discountReason: DiscountReason | null;
    discountReasonMessage: string;
};

const BackButton = ({ onClick }: { onClick: () => void }) => {
    const { t } = useTranslation("common");
    return (
        <a className="flow-button-back" onClick={onClick}>
            {t("back")}
        </a>
    );
};

const validate_phone_number = async (
    phone: string,
    t: Translator<"change_phone">,
) => {
    const r = await show_phone_number_dialog(
        null,
        async () => phone,
        async () => await UIkit.modal.prompt(t("validatePhone")),
        t,
    );
    return r;
};

const MemberInfoForm = ({
    info,
    onChange,
    onSubmit,
    onBack,
}: {
    info: MemberInfo;
    onChange: Dispatch<StateUpdater<MemberInfo>>;
    onSubmit: (info: MemberInfo) => void;
    onBack: () => void;
}) => {
    const { t } = useTranslation("register");
    const { t: tPhone } = useTranslation("change_phone");
    const [showErrors, setShowErrors] = useState(false);
    const [inProgress, setInProgress] = useState(false);
    const onInvalid = () => setShowErrors(true);
    return (
        <form
            className={"member-info " + (showErrors ? "validate" : "")}
            onSubmit={async (e) => {
                setInProgress(true);
                e.preventDefault();
                setShowErrors(false);

                try {
                    if (
                        (await validate_phone_number(info.phone, tPhone)) ===
                        "ok"
                    ) {
                        onSubmit(info);
                    }
                } finally {
                    setInProgress(false);
                }
            }}
            onInvalid={() => {
                setShowErrors(true);
            }}
        >
            <LabeledInput
                label={t("memberInfo.firstName")}
                id="firstName"
                type="text"
                required
                value={info.firstName}
                onChange={(firstName) =>
                    onChange((info) => ({ ...info, firstName }))
                }
                onInvalid={onInvalid}
            />
            <LabeledInput
                label={t("memberInfo.lastName")}
                id="lastName"
                type="text"
                required
                value={info.lastName}
                onChange={(lastName) =>
                    onChange((info) => ({ ...info, lastName }))
                }
                onInvalid={onInvalid}
            />
            <LabeledInput
                label={t("memberInfo.email")}
                id="email"
                type="email"
                required
                value={info.email}
                onChange={(email) => onChange((info) => ({ ...info, email }))}
                onInvalid={onInvalid}
            />
            <LabeledInput
                label={t("memberInfo.phone")}
                id="phone"
                type="tel"
                pattern="[\-\+\s0-9]*"
                required
                value={info.phone}
                onChange={(phone) => onChange((info) => ({ ...info, phone }))}
                onInvalid={onInvalid}
            />
            <LabeledInput
                label={t("memberInfo.zipCode")}
                id="zipCode"
                type="text"
                pattern="[0-9\s]+"
                placeholder={"XXX XX"}
                required
                value={info.zipCode}
                onChange={(zipCode) =>
                    onChange((info) => ({ ...info, zipCode }))
                }
                onInvalid={onInvalid}
            />
            <button
                type="submit"
                className="flow-button primary"
                disabled={inProgress}
            >
                <span
                    className={
                        "uk-spinner uk-icon progress-spinner " +
                        (inProgress ? "progress-spinner-visible" : "")
                    }
                    uk-spinner={""}
                />
                <span>{t("memberInfo.submit")}</span>
            </button>
            <BackButton onClick={onBack} />
        </form>
    );
};

const RuleCheckbox = ({
    rule,
    value,
    onChange,
}: {
    value: boolean;
    rule: string;
    onChange: Dispatch<StateUpdater<boolean>>;
}) => {
    const id = `${(Math.random() * 10000) | 0}`;
    return (
        <div class="rule-checkbox">
            <input
                id={id}
                type="checkbox"
                checked={value}
                onChange={(e) => onChange(e.currentTarget.checked)}
            />
            <label for={id}>{rule}</label>
        </div>
    );
};

type Terms = {
    accepted1: boolean;
    accepted2: boolean;
    accepted3: boolean;
};

const TermsAndConditions = ({
    onAccept,
    onBack,
    acceptedTerms,
    onChangeAcceptedTerms,
}: {
    onAccept: () => void;
    onBack: () => void;
    acceptedTerms: Terms;
    onChangeAcceptedTerms: (terms: Terms) => void;
}) => {
    const { t } = useTranslation("register");
    return (
        <div class="terms-and-conditions">
            <h2>{t("terms.title")}</h2>
            <p>
                <b>{t("terms.pledge")}...</b>
            </p>
            <ol
                className="rules-list"
                dangerouslySetInnerHTML={{
                    __html: t("terms.rules").join("\n"),
                }}
            />
            <p>
                <b>{t("terms.understandingPledge")}...</b>
            </p>
            <ol className="rules-list">
                {t("terms.understanding").map((v) => (
                    <li>{v}</li>
                ))}
            </ol>

            <RuleCheckbox
                rule={t("terms.accept")}
                onChange={() =>
                    onChangeAcceptedTerms({
                        ...acceptedTerms,
                        accepted1: !acceptedTerms.accepted1,
                    })
                }
                value={acceptedTerms.accepted1}
            />
            <RuleCheckbox
                rule={t("terms.welcoming")}
                onChange={() =>
                    onChangeAcceptedTerms({
                        ...acceptedTerms,
                        accepted2: !acceptedTerms.accepted2,
                    })
                }
                value={acceptedTerms.accepted2}
            />
            <button
                className="flow-button primary"
                disabled={!acceptedTerms.accepted1 || !acceptedTerms.accepted2}
                onClick={onAccept}
            >
                {t("terms.continue")}
            </button>
            <BackButton onClick={onBack} />
        </div>
    );
};

enum State {
    ChoosePlan,
    MemberInfo,
    Terms,
    Confirmation,
    Success,
    Discounts,
}

const Confirmation = ({
    memberInfo,
    selectedPlan,
    productData,
    discount,
    discountInfo,
    card,
    onRegistered,
    onBack,
}: {
    memberInfo: MemberInfo;
    selectedPlan: Plan;
    productData: ProductData;
    discount: Discount;
    discountInfo: DiscountsInfo;
    card: stripe.elements.Element;
    onRegistered: (r: RegistrationSuccess) => void;
    onBack: () => void;
}) => {
    const { t } = useTranslation("register");
    const { t: tPayment } = useTranslation("payment");
    const [inProgress, setInProgress] = useState(false);

    return (
        <>
            <div class="uk-flex-1" />
            {<p>{t("payment.subTitle")}</p>}
            {
                <p>
                    <Trans
                        i18nKey={"register:payment.bookIntroduction"}
                        components={[
                            <a target="_blank" href={URL_CALENDLY_BOOK} />,
                        ]}
                    />
                </p>
            }
            <div class="uk-flex-1" />
            <ToPayPreview
                productData={productData}
                cart={Cart.oneOfEachProduct(selectedPlan.products)}
                discount={discount}
                currentMemberships={[]}
            />
            <div class="uk-flex-1" />
            <span class="payment-processor">
                {t("payment.paymentProcessor")}
            </span>
            <StripeCardInput element={card} />
            <button
                className="flow-button primary"
                disabled={inProgress}
                onClick={async () => {
                    setInProgress(true);
                    try {
                        if (selectedPlan == null) {
                            throw new Error("No plan selected");
                        }
                        const memberInfoValidated: MemberInfoValidated = {
                            ...memberInfo,
                            zipCode: Number(
                                memberInfo.zipCode.replace(/\s/g, ""),
                            ),
                        };
                        const paymentMethod = await createPaymentMethod(card, {
                            address_street: "",
                            address_extra: "",
                            address_zipcode: memberInfoValidated.zipCode,
                            address_city: "",
                            email: memberInfo.email,
                            member_id: 0,
                            member_number: 0,
                            firstname: memberInfo.firstName,
                            lastname: memberInfo.lastName,
                            phone: "",
                            pin_code: "",
                            labaccess_agreement_at: "",
                        });

                        if (paymentMethod !== null) {
                            try {
                                onRegistered(
                                    await registerMember(
                                        paymentMethod,
                                        productData,
                                        memberInfoValidated,
                                        selectedPlan,
                                        discount,
                                        discountInfo,
                                    ),
                                );
                            } catch (e) {
                                if (e instanceof PaymentFailedError) {
                                    UIkit.modal.alert(
                                        "<h2>Payment failed</h2>" + e.message,
                                    );
                                } else {
                                    throw e;
                                }
                            }
                        }
                    } finally {
                        setInProgress(false);
                    }
                }}
            >
                <span
                    className={
                        "uk-spinner uk-icon progress-spinner " +
                        (inProgress ? "progress-spinner-visible" : "")
                    }
                    uk-spinner={""}
                />
                <span>{tPayment("pay_with_stripe")}</span>
            </button>
            <BackButton onClick={onBack} />
            <div class="uk-flex-1" />
        </>
    );
};

type DiscountRequest = {
    price_level: PriceLevel;
    message: string;
};

type RegisterRequest = {
    member: MemberInfoValidated;
    discount: DiscountRequest | null;
};

type RegisterResponse = {
    token: string;
    member_id: number;
};

type RegistrationSuccess = {
    loginToken: string;
};

async function registerMember(
    paymentMethod: stripe.paymentMethod.PaymentMethod,
    productData: ProductData,
    memberInfo: MemberInfoValidated,
    selectedPlan: Plan,
    discount: Discount,
    discountInfo: DiscountsInfo,
): Promise<RegistrationSuccess> {
    const data: RegisterRequest = {
        member: memberInfo,
        discount:
            discount.priceLevel !== null && discountInfo.discountReason !== null
                ? {
                      price_level: discount.priceLevel,
                      message: `${discountInfo.discountReason}: ${discountInfo.discountReasonMessage}`,
                  }
                : null,
    };

    // This registers the member as pending.
    // If the payment fails, we can safely forget about the member (it will be cleaned up during the next registration attempt).
    // If the payment succeeds, the member will be automatically activated.
    let loginToken: string;
    try {
        loginToken = (
            (await common.ajax(
                "POST",
                `${window.apiBasePath}/webshop/register`,
                data,
            )) as ServerResponse<RegisterResponse>
        ).data.token;
    } catch (e) {
        throw new PaymentFailedError(common.get_error(e));
    }

    const cart = new Cart(
        selectedPlan.products.map((p) => ({
            id: p.id,
            count: 1,
        })),
    );

    await pay(paymentMethod, cart, productData, discount, [], { loginToken });

    return { loginToken };
}

const CheckIcon = ({ done }: { done: boolean }) => {
    return (
        <span
            className={
                "uk-icon-small uk-icon task " + (done ? "task-done" : "")
            }
            uk-icon="icon: check"
        ></span>
    );
};

const TaskItem = ({
    clickedSteps,
    setClickedSteps,
    step,
    children,
}: {
    clickedSteps: Set<number | string>;
    setClickedSteps: (s: Set<number | string>) => void;
    step: number | string;
    children: (tick: () => void) => ComponentChildren;
}) => {
    return (
        <li>
            <CheckIcon done={clickedSteps.has(step)} />
            <span>
                {children(() =>
                    setClickedSteps(new Set(clickedSteps).add(step)),
                )}
            </span>
        </li>
    );
};

const Success = ({ member }: { member: member_t }) => {
    const [isBookModalOpen, setBookModalOpen] = useState(false);
    const [clickedSteps, setClickedSteps] = useState(
        new Set<number | string>(),
    );
    const { t } = useTranslation("register");

    useCalendlyEventListener({
        onEventScheduled: () => {
            setClickedSteps(new Set(clickedSteps).add("booked"));
        },
    });

    const steps: ((tick: () => void) => JSX.Element)[] = [
        (tick) => (
            <>
                <a
                    target="_blank"
                    className="flow-button primary flow-button-small"
                    href={URL_SLACK_SIGNUP}
                    onClick={tick}
                >
                    {t("success.steps.joinSlackButton")}
                </a>{" "}
                {t("success.steps.joinSlackWhy")}{" "}
                <a target="_blank" href={URL_SLACK_HELP}>
                    <i>{t("success.steps.joinSlackWhatIsThis")}</i>
                </a>
            </>
        ),
        (tick) => (
            <>
                <a
                    target="_blank"
                    className="flow-button primary flow-button-small"
                    href={accessyURL()}
                    onClick={tick}
                >
                    {t("success.steps.installAccessy")}
                </a>{" "}
                {t("success.steps.installAccessyWhy")}
            </>
        ),
        (tick) => (
            <>
                {t("success.steps.quizTake")}{" "}
                <a target="_blank" href={URL_GET_STARTED_QUIZ} onClick={tick}>
                    {t("success.steps.quizName")}
                </a>{" "}
                {t("success.steps.quizWhy")}
            </>
        ),
        (tick) => (
            <>
                {t("success.steps.wikiPrefix")}{" "}
                <a target="_blank" href={URL_WIKI} onClick={tick}>
                    {t("success.steps.wikiButton")}
                </a>
                .
            </>
        ),
        (tick) => (
            <>
                {t("success.steps.instagramPrefix")}{" "}
                <a target="_blank" href={URL_INSTAGRAM} onClick={tick}>
                    {t("success.steps.instagramButton")}
                </a>
                .
            </>
        ),
    ];

    return (
        <>
            <h1>{t("success.title")}</h1>
            <p>{t("success.subTitle")}</p>
            <p>{t("success.nextSteps")}</p>
            <ul className="registration-task-list">
                <TaskItem
                    clickedSteps={clickedSteps}
                    setClickedSteps={setClickedSteps}
                    step="booked"
                >
                    {(_tick) => (
                        <button
                            className="flow-button primary flow-button-small"
                            onClick={() => setBookModalOpen(true)}
                        >
                            {t("success.bookButton")}
                        </button>
                    )}
                </TaskItem>
                {steps.map((step, i) => (
                    <TaskItem
                        clickedSteps={clickedSteps}
                        setClickedSteps={setClickedSteps}
                        step={`${i}`}
                    >
                        {(tick) => step(tick)}
                    </TaskItem>
                ))}
            </ul>
            <div class="uk-flex-1" />
            <a
                href={URL_RELATIVE_MEMBER_PORTAL}
                className="flow-button primary"
            >
                {t("success.continueToMemberPortal")}
            </a>
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
                    smsReminderNumber: member.phone,
                }}
            />
        </>
    );
};

const Discounts = ({
    discounts,
    setDiscounts,
    onSubmit,
    onCancel,
    discountAmounts,
}: {
    discounts: DiscountsInfo;
    discountAmounts: Record<PriceLevel, number>;
    setDiscounts: (m: DiscountsInfo) => void;
    onSubmit: () => void;
    onCancel: () => void;
}) => {
    const { t } = useTranslation("register");

    const reasons: DiscountReason[] = [
        "student",
        "unemployed",
        "senior",
        "other",
    ];
    const [step, setStep] = useState(0);
    const MIN_DISCOUNT_REASON_LENGTH = 30;

    if (step == 0) {
        return (
            <>
                <h2>{t("discounts.title")}</h2>
                <p>{t("discounts.text")}</p>

                {reasons.map((reason) => (
                    <div class="rule-checkbox">
                        <input
                            id={`reason.${reason}`}
                            type="radio"
                            checked={discounts.discountReason === reason}
                            onChange={(e) =>
                                setDiscounts({
                                    ...discounts,
                                    discountReason: e.currentTarget.checked
                                        ? reason
                                        : null,
                                })
                            }
                        />
                        <label for={`reason.${reason}`}>
                            {t(`discounts.reasons.${reason}`)}
                        </label>
                    </div>
                ))}
                <textarea
                    placeholder={t("discounts.messagePlaceholder")}
                    value={discounts.discountReasonMessage}
                    onChange={(e) =>
                        setDiscounts({
                            ...discounts,
                            discountReasonMessage: e.currentTarget.value,
                        })
                    }
                />
                <button
                    className="flow-button primary"
                    onClick={() => setStep(1)}
                    disabled={
                        discounts.discountReason === null ||
                        discounts.discountReasonMessage.length <
                            MIN_DISCOUNT_REASON_LENGTH
                    }
                >
                    {discounts.discountReason !== null &&
                    discounts.discountReasonMessage.length <
                        MIN_DISCOUNT_REASON_LENGTH
                        ? t("discounts.submitWriteMore")
                        : t("discounts.submit")}
                </button>
                <button
                    className="flow-button primary"
                    onClick={() => {
                        setDiscounts({
                            discountReason: null,
                            discountReasonMessage: "",
                        });
                        onCancel();
                    }}
                >
                    {t("discounts.cancel")}
                </button>
            </>
        );
    } else {
        return (
            <>
                <h2>{t("discounts.title")}</h2>
                <p>{t("discounts.confirmationTitle")}</p>
                <p>
                    {t("discounts.confirmationDiscount", {
                        percent: discountAmounts["low_income_discount"] * 100,
                    })}
                </p>
                <p>{t("discounts.confirmationMessage")}</p>
                <button className="flow-button primary" onClick={onSubmit}>
                    {t("discounts.submit")}
                </button>
                <button
                    className="flow-button primary"
                    onClick={() => {
                        setDiscounts({
                            discountReason: null,
                            discountReasonMessage: "",
                        });
                        onCancel();
                    }}
                >
                    {t("discounts.cancel")}
                </button>
            </>
        );
    }
};

const MakerspaceLogo = () => {
    return (
        <img
            src={
                window.staticBasePath +
                "/images/logo-transparent-500px-300x210.png"
            }
            alt="Makerspace Logo"
            className="registration-logo"
        />
    );
};

type PlanId = "starterPack" | "decideLater" | "singleMonth";

const poorMansHistoryManager = <T,>(
    state: T,
    defaultState: T,
    setState: (v: T) => void,
    parse: (s: string) => T | undefined,
    toString: (s: T) => string,
) => {
    useEffect(() => {
        history.replaceState(
            {
                state,
            },
            "",
        );

        const listener = (_e: PopStateEvent) => {
            let newState = defaultState;
            if (location.hash.startsWith("#")) {
                const st: T | undefined = parse(location.hash.slice(1));
                if (st !== undefined) newState = st;
            }
            setState(newState);
        };
        window.addEventListener("popstate", listener);
        return () => window.removeEventListener("popstate", listener);
    }, []);

    return (newState: T) => {
        history.pushState({}, "", "#" + toString(newState));
        setState(newState);
    };
};

/// Used to get a somewhat statistically independenent number from the same seed
function hash(x: number): number {
    x = Math.imul((x >> 16) ^ x, 0x45d9f3b);
    x = Math.imul((x >> 16) ^ x, 0x45d9f3b);
    x = (x >> 16) ^ x;
    return x;
}

type ABState = {
    oldpage: false;
    registration_base_membership_type: "oneyear" | "subscription";
    registration_base_membership_only_plan_enabled: boolean;
    price_grouping: "separate" | "combined";
};

/// Returns what options should be visible to the user depending on a random seed.
/// This method should be deterministic given the seed.
const abStateFromSeed = (seed: number): ABState => {
    return {
        oldpage: false,
        registration_base_membership_type: "oneyear",
        registration_base_membership_only_plan_enabled: true,
        price_grouping: hash(seed + 1) % 2 === 0 ? "separate" : "combined", // 1/2 of users will see the base membership price separately like "200 + 375 kr", instead of combined like "575 kr"
    };
};

const RegisterPage = ({}: {}) => {
    const abState = useMemo(() => {
        let seed = parseInt(localStorage.getItem("abTestSeed") ?? "");
        if (!isFinite(seed)) seed = (Math.random() * 1000000) | 0;
        localStorage.setItem("abTestSeed", seed.toString());
        return abStateFromSeed(seed);
    }, []);

    const [state, setStateInternal] = useState(State.ChoosePlan);
    const setStateHistory = poorMansHistoryManager(
        state,
        State.ChoosePlan,
        setStateInternal,
        (s) => State[s as keyof typeof State],
        (s) => State[s],
    );
    const setState = (s: State) => {
        setStateHistory(s);
        trackPlausible(`register/${State[s]}`, { props: abState });
    };

    useEffect(() => {
        trackPlausible(`register/${State[state]}`, { props: abState });
    }, []);

    const [selectedPlan, setSelectedPlan] = useState<PlanId | null>(
        "starterPack",
    );
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
        accepted3: false,
    });

    const [loggedInMember, setLoggedInMember] = useState<member_t | null>(null);
    const { t } = useTranslation("register");
    const { t: tCommon } = useTranslation("common");
    const card = useMemo(() => createStripeCardInput(), []);
    const [registerPageData, setRegisterPageData] =
        useState<RegisterPageData | null>(null);
    const [discounts, setDiscounts] = useState<DiscountsInfo>({
        discountReason: null,
        discountReasonMessage: "",
    });
    const [productData, setProductData] = useState<ProductData | null>(null);

    useEffect(() => {
        common
            .ajax("GET", `${window.apiBasePath}/webshop/register_page_data`)
            .then((x) => {
                setRegisterPageData(x.data);
                setProductData(
                    ProductDataFromProducts(
                        (x.data as RegisterPageData).productData,
                    ),
                );
            });
    }, []);

    if (registerPageData === null || productData === null) {
        return <div>Loading...</div>;
    }

    const priceLevel: PriceLevel =
        discounts.discountReason !== null ? "low_income_discount" : "normal";
    const discount: Discount = {
        priceLevel,
        fractionOff: registerPageData.discounts[priceLevel],
    };

    const relevantProducts = extractRelevantProducts(productData.products);
    const accessCostSingle =
        parseFloat(relevantProducts.labaccessProduct.price) *
        (1 - discount.fractionOff);
    const accessSubscriptionCost =
        parseFloat(relevantProducts.labaccessSubscriptionProduct.price) *
        (1 - discount.fractionOff);

    const membershipProduct =
        abState.registration_base_membership_type === "subscription"
            ? relevantProducts.membershipSubscriptionProduct
            : relevantProducts.baseMembershipProduct;
    const baseMembershipCost =
        parseFloat(membershipProduct.price) * (1 - discount.fractionOff);

    const plans: Plan[] = [
        {
            id: "starterPack",
            title: t("plans.starterPack.title"),
            abovePrice: t("plans.starterPack.abovePrice"),
            price: "",
            belowPrice: t("plans.ofWhichBaseMembership", {
                price: baseMembershipCost,
            }),
            description1: t("plans.starterPack.description1"),
            description2: t("plans.starterPack.description2"),
            products: [relevantProducts.starterPackProduct, membershipProduct],
            highlight: "Recommended",
        },
        {
            id: "singleMonth",
            title: t("plans.singleMonth.title"),
            abovePrice: t("plans.singleMonth.abovePrice"),
            price: "",
            belowPrice: t("plans.ofWhichBaseMembership", {
                price: baseMembershipCost,
            }),
            description1: t("plans.singleMonth.description1"),
            description2: t("plans.singleMonth.description2"),
            products: [relevantProducts.labaccessProduct, membershipProduct],
            highlight: null,
        },
    ];
    if (abState.registration_base_membership_only_plan_enabled) {
        plans.push({
            id: "decideLater",
            title: t("plans.decideLater.title"),
            abovePrice: t("plans.decideLater.abovePrice"),
            price: "",
            belowPrice: "",
            description1: t("plans.decideLater.description1"),
            description2: t("plans.decideLater.description2", {
                makerspace_acccess_price: accessCostSingle,
                makerspace_acccess_subscription_price: accessSubscriptionCost,
            }),
            products: [membershipProduct],
            highlight: null,
        });
    }

    for (const plan of plans) {
        if (abState.price_grouping === "separate") {
            const membershipProducts = plan.products.filter(
                (p) => p === membershipProduct,
            );
            const nonMembershipProducts = plan.products.filter(
                (p) => p !== membershipProduct,
            );
            const toPay1 = calculateAmountToPay({
                productData,
                cart: Cart.oneOfEachProduct(membershipProducts),
                discount: discount,
                currentMemberships: [],
            });
            const toPay2 = calculateAmountToPay({
                productData,
                cart: Cart.oneOfEachProduct(nonMembershipProducts),
                discount: discount,
                currentMemberships: [],
            });
            const toPaySum1 = toPay1.payNow.reduce((a, b) => a + b.amount, 0);
            const toPaySum2 = toPay2.payNow.reduce((a, b) => a + b.amount, 0);
            if (toPaySum1 === 0 || toPaySum2 === 0) {
                plan.price = toPaySum1 + toPaySum2 + " " + tCommon("priceUnit");
            } else {
                plan.price =
                    toPaySum1 + " + " + toPaySum2 + " " + tCommon("priceUnit");
            }
        } else {
            const toPay = calculateAmountToPay({
                productData,
                cart: Cart.oneOfEachProduct(plan.products),
                discount: discount,
                currentMemberships: [],
            });
            plan.price =
                toPay.payNow.reduce((a, b) => a + b.amount, 0) +
                " " +
                tCommon("priceUnit");
        }
    }

    const activePlan = plans.find((plan) => plan.id === selectedPlan);

    switch (state) {
        case State.ChoosePlan:
            return (
                <>
                    <MakerspaceLogo />
                    <h1>{t("memberships.title")}</h1>
                    <p>{t("memberships.p1")}</p>
                    <p>
                        <Trans i18nKey="register:memberships.p2" />
                    </p>

                    <h2>{t("chooseYourPlan.title")}</h2>
                    <span>{t("chooseYourPlan.help")}</span>
                    <div class="plan-buttons">
                        {plans.map((plan, i) => (
                            <PlanButton
                                selected={selectedPlan === plan.id}
                                onClick={() => setSelectedPlan(plan.id)}
                                plan={plan}
                                order={i}
                            />
                        ))}
                    </div>
                    {FEATURE_FLAG_LOW_INCOME_DISCOUNT &&
                        registerPageData.discounts["low_income_discount"] >
                            0 && (
                            <button
                                className="flow-button"
                                onClick={() => setState(State.Discounts)}
                            >
                                {t("discounts.apply_for_discounts")}
                            </button>
                        )}
                    {activePlan !== undefined ? (
                        <ToPayPreview
                            productData={productData}
                            cart={Cart.oneOfEachProduct(activePlan.products)}
                            discount={discount}
                            currentMemberships={[]}
                        />
                    ) : null}
                    <button
                        className="flow-button primary"
                        disabled={selectedPlan == null}
                        onClick={() => setState(State.MemberInfo)}
                    >
                        {tCommon("continue")}
                    </button>
                </>
            );
        case State.MemberInfo:
            return (
                <>
                    <MakerspaceLogo />
                    <h2>{t("memberInfo.title")}</h2>
                    <MemberInfoForm
                        info={memberInfo}
                        onChange={setMemberInfo}
                        onSubmit={(_) => setState(State.Terms)}
                        onBack={() => history.back()}
                    />
                </>
            );
        case State.Terms:
            return (
                <>
                    <MakerspaceLogo />
                    <TermsAndConditions
                        onAccept={() => setState(State.Confirmation)}
                        onBack={() => history.back()}
                        acceptedTerms={acceptedTerms}
                        onChangeAcceptedTerms={setAcceptedTerms}
                    />
                </>
            );
        case State.Confirmation:
            if (activePlan === undefined) {
                // This should never happen during a normal flow, but could happen if the user does weird history manipulation
                setState(State.ChoosePlan);
                return null;
            }

            return (
                <>
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
                        onBack={() => history.back()}
                    />
                </>
            );
        case State.Success:
            if (loggedInMember === null) {
                // This should never happen during a normal flow, but could happen if the user does weird history manipulation
                setState(State.ChoosePlan);
                return null;
            }

            return (
                <>
                    <MakerspaceLogo />
                    <Success member={loggedInMember} />
                </>
            );
        case State.Discounts:
            return (
                <>
                    <MakerspaceLogo />
                    <Discounts
                        discounts={discounts}
                        setDiscounts={setDiscounts}
                        discountAmounts={registerPageData.discounts}
                        onSubmit={() => {
                            setState(State.ChoosePlan);
                        }}
                        onCancel={() => history.back()}
                    />
                </>
            );
    }
};

common.documentLoaded().then(() => {
    const root = document.getElementById("root");
    initializeStripe();
    if (root != null) {
        render(
            <div className="content-wrapper">
                <RegisterPage />
            </div>,
            root,
        );
    }
});
